"""Leitura de credenciais no Google Secret Manager.

Regra da cláusula 8.5: credencial não entra em código, `.env` versionado,
log ou mensagem de erro. Só chega ao processo por aqui.

## O cofre local, e por que ele existe

O projeto GCP ainda não existe (pendência A3), e credenciais já chegaram —
o token do TempoOK em 14/09. Sem um lugar para guardá-las, elas ficariam num
`.env` do repositório, que é exatamente o que a cláusula proíbe.

O cofre local resolve isso e é desenhado para **não conseguir** virar porta
aberta em produção:

1. **é opt-in explícito** (`ALUPDATA_SECRETS_LOCAIS=1`), nunca fallback
   silencioso — fallback deixaria um token local antigo mascarar o de produção,
   e o erro só apareceria no dado;
2. **recusa rodar dentro do Cloud Run**, onde a credencial vem do Secret
   Manager e ponto;
3. **recusa arquivo dentro do repositório**, que é o único jeito de ele ser
   commitado por acidente.

Quando A3 chegar, `scripts/migrar_segredos.py` sobe o cofre inteiro para o
Secret Manager e o cofre é apagado. O formato do arquivo usa o **nome canônico
do secret como chave** justamente para que essa migração seja mecânica.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from src.core.config import get_settings

PADRAO_NOME = "alupdata-{fonte}-{campo}"

RAIZ_REPO = Path(__file__).resolve().parents[2]
COFRE_PADRAO = Path.home() / ".alupdata" / "segredos.env"

# Variáveis que o Cloud Run define sozinho. Se alguma existe, é produção.
_MARCAS_CLOUD_RUN = ("K_SERVICE", "CLOUD_RUN_JOB")


def nome_secret(fonte: str, campo: str) -> str:
    """Nome canônico do secret de uma fonte."""
    return PADRAO_NOME.format(fonte=fonte, campo=campo)


def _usando_cofre_local() -> bool:
    return os.getenv("ALUPDATA_SECRETS_LOCAIS", "").strip().lower() in {"1", "true", "sim"}


def caminho_do_cofre() -> Path:
    """Onde o cofre local vive, já validado."""
    caminho = Path(os.getenv("ALUPDATA_SECRETS_ARQUIVO") or COFRE_PADRAO).expanduser()
    if caminho.resolve().is_relative_to(RAIZ_REPO):
        raise ValueError(
            f"o cofre local não pode ficar dentro do repositório ({caminho}); "
            f"use um caminho fora dele, como {COFRE_PADRAO}"
        )
    return caminho


def ler_cofre() -> dict[str, str]:
    """Pares `nome-do-secret=valor` do cofre local.

    Linha vazia e comentário são ignorados. O valor é usado com espaços em
    volta removidos: colar um token com espaço sobrando é o erro mais fácil de
    cometer, e o mais chato de diagnosticar depois.
    """
    caminho = caminho_do_cofre()
    if not caminho.exists():
        raise FileNotFoundError(
            f"cofre local não encontrado em {caminho}. "
            "Crie-o com uma linha por credencial, no formato alupdata-<fonte>-<campo>=<valor>"
        )

    segredos: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        texto = linha.strip()
        if not texto or texto.startswith("#") or "=" not in texto:
            continue
        chave, _, valor = texto.partition("=")
        segredos[chave.strip()] = valor.strip()
    return segredos


@lru_cache
def ler_secret(fonte: str, campo: str, versao: str = "latest") -> str:
    """Valor do secret. Memoizado — não relê a cada requisição do conector."""
    nome = nome_secret(fonte, campo)

    if _usando_cofre_local():
        if presente := [m for m in _MARCAS_CLOUD_RUN if os.getenv(m)]:
            raise RuntimeError(
                f"ALUPDATA_SECRETS_LOCAIS está ligado dentro do Cloud Run ({presente[0]}). "
                "Em produção a credencial vem do Secret Manager; desligue a variável."
            )
        cofre = ler_cofre()
        if nome not in cofre:
            # A mensagem diz o que falta e onde, nunca o que existe: mensagem de
            # erro é lugar por onde credencial vaza (cláusula 8.5).
            raise KeyError(f"{nome} não está no cofre local ({caminho_do_cofre()})")
        return cofre[nome]

    from google.cloud import secretmanager  # import tardio: conector público não precisa

    cfg = get_settings()
    cliente = secretmanager.SecretManagerServiceClient()
    caminho = f"projects/{cfg.gcp_project_id}/secrets/{nome}/versions/{versao}"
    resposta = cliente.access_secret_version(request={"name": caminho})
    return resposta.payload.data.decode("utf-8")
