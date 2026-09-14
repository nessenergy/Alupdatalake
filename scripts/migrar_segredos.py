"""Sobe o cofre local para o Secret Manager, quando o projeto GCP existir (A3).

O cofre local (`src/core/secrets.py`) é a ponte enquanto não há ambiente. Este
script é a travessia: lê cada `alupdata-<fonte>-<campo>=<valor>` e grava uma
versão nova do secret correspondente.

Por que um script em vez de `gcloud secrets versions add` na mão:

- **o token não passa pelo histórico do terminal.** Digitar o valor na linha de
  comando o deixa no `.bash_history`, no log do terminal e na lista de
  processos enquanto o comando roda;
- os secrets já estão declarados em `infra/modules/secrets` — o script confere
  que o nome existe antes de gravar, em vez de criar um secret órfão por erro
  de digitação.

Uso:

    ALUPDATA_SECRETS_LOCAIS=1 uv run python -m scripts.migrar_segredos --projeto alupdata-dev
    ALUPDATA_SECRETS_LOCAIS=1 uv run python -m scripts.migrar_segredos --projeto alupdata-dev --aplicar

Sem `--aplicar` é simulação: lista o que faria, sem gravar nada e sem imprimir
valor nenhum.

Depois de migrar, **apague o cofre local** e rotacione o que trafegou por
e-mail — o script lembra disso no fim.
"""

from __future__ import annotations

import argparse
import sys

from src.core.secrets import caminho_do_cofre, ler_cofre


def _resumo(valor: str) -> str:
    """Prova de que o valor certo foi lido, sem imprimir o valor.

    Só o tamanho e as pontas. É o suficiente para conferir contra o que o
    fornecedor informou, e insuficiente para reconstruir a credencial.
    """
    if len(valor) < 12:
        return f"{len(valor)} caracteres (curto demais — confira)"
    return f"{len(valor)} caracteres, {valor[:3]}…{valor[-3:]}"


def migrar(projeto: str, *, aplicar: bool) -> int:
    segredos = ler_cofre()
    if not segredos:
        print(f"cofre vazio em {caminho_do_cofre()}; nada a migrar")
        return 0

    print(f"cofre: {caminho_do_cofre()}")
    print(f"projeto: {projeto}")
    print(f"modo: {'APLICAR' if aplicar else 'simulação (use --aplicar para gravar)'}\n")

    if aplicar:
        from google.cloud import secretmanager

        cliente = secretmanager.SecretManagerServiceClient()

    falhas = 0
    for nome in sorted(segredos):
        valor = segredos[nome]
        if not valor:
            print(f"  [PULADO]   {nome} — valor vazio no cofre")
            falhas += 1
            continue

        if not aplicar:
            print(f"  [simularia] {nome} — {_resumo(valor)}")
            continue

        try:
            cliente.add_secret_version(
                request={
                    "parent": f"projects/{projeto}/secrets/{nome}",
                    "payload": {"data": valor.encode("utf-8")},
                }
            )
        except Exception as exc:  # noqa: BLE001 — um secret que falha não impede os outros
            # O nome da exceção basta; o corpo pode ecoar o payload enviado.
            print(f"  [FALHOU]   {nome} — {type(exc).__name__}. O secret existe em infra/modules/secrets?")
            falhas += 1
            continue
        print(f"  [gravado]  {nome} — {_resumo(valor)}")

    if aplicar and falhas == 0:
        print(
            f"\nMigração concluída. Agora:\n"
            f"  1. apague o cofre local:  rm {caminho_do_cofre()}\n"
            f"  2. desligue ALUPDATA_SECRETS_LOCAIS\n"
            f"  3. rotacione junto ao fornecedor toda credencial que trafegou por e-mail"
        )
    return 1 if falhas else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sobe o cofre local para o Secret Manager")
    parser.add_argument("--projeto", required=True, help="ID do projeto GCP de destino")
    parser.add_argument("--aplicar", action="store_true", help="grava de verdade; sem isso, apenas simula")
    args = parser.parse_args(argv)
    return migrar(args.projeto, aplicar=args.aplicar)


if __name__ == "__main__":
    sys.exit(main())
