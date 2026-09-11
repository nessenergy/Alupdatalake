"""Compila a release `main` do Dataform e executa o workflow, esperando o fim.

Roda no deploy logo depois do `terraform apply` (ADR 012): as tabelas Bronze
precisam existir, particionadas, antes da primeira ingestão — a carga nunca as
cria (`CREATE_NEVER`).

    uv run python -m scripts.executar_dataform --service-account <email>
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from typing import Any

from src.core.config import get_settings
from src.core.observabilidade import configurar_logging
from src.core.seguranca import sanitizar

configurar_logging()
logger = logging.getLogger("executar-dataform")

API = "https://dataform.googleapis.com/v1"
TERMINAIS = {"SUCCEEDED", "FAILED", "CANCELLED"}


def repositorio(projeto: str, regiao: str, nome: str = "alupdata") -> str:
    """Nome completo do repositório Dataform criado pelo Terraform."""
    return f"projects/{projeto}/locations/{regiao}/repositories/{nome}"


def erros_de_compilacao(resultado: dict[str, Any]) -> list[str]:
    """Erros de compilação no formato `arquivo: mensagem`."""
    return [f"{e.get('path', '?')}: {e.get('message', '')}" for e in resultado.get("compilationErrors", [])]


def _verificar(resposta: Any) -> None:
    """Propaga erro HTTP, registrando antes o corpo da resposta (nunca a credencial, regra 2)."""
    try:
        resposta.raise_for_status()
    except Exception:
        logger.error("Dataform respondeu com erro: %s", sanitizar(str(getattr(resposta, "text", ""))))
        raise


def executar(sessao: Any, repo: str, service_account: str, intervalo: float = 10.0, limite: float = 1800.0) -> str:
    """Compila a release `main`, executa tudo e devolve o estado terminal."""
    compilacao = sessao.post(f"{API}/{repo}/compilationResults", json={"releaseConfig": f"{repo}/releaseConfigs/main"})
    _verificar(compilacao)
    resultado = compilacao.json()
    if erros := erros_de_compilacao(resultado):
        raise RuntimeError("compilação do Dataform falhou:\n" + "\n".join(erros))

    invocacao = sessao.post(
        f"{API}/{repo}/workflowInvocations",
        json={"compilationResult": resultado["name"], "invocationConfig": {"serviceAccount": service_account}},
    )
    _verificar(invocacao)
    nome = invocacao.json()["name"]
    logger.info("execução do Dataform iniciada: %s", nome)

    inicio = time.monotonic()
    while True:
        resposta = sessao.get(f"{API}/{nome}")
        _verificar(resposta)
        estado = resposta.json().get("state", "STATE_UNSPECIFIED")
        if estado in TERMINAIS:
            return estado
        if time.monotonic() - inicio >= limite:
            raise TimeoutError(f"execução do Dataform sem fim após {limite:.0f}s: {nome}")
        time.sleep(intervalo)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Executa o Dataform a partir da release main")
    parser.add_argument("--service-account", required=True, help="SA que executa o Dataform (strict act-as)")
    parser.add_argument("--repositorio", default="alupdata", help="Nome do repositório Dataform criado pelo Terraform")
    args = parser.parse_args(argv)

    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credenciais, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    cfg = get_settings()
    repo = repositorio(cfg.gcp_project_id, cfg.gcp_region, args.repositorio)
    estado = executar(AuthorizedSession(credenciais), repo, args.service_account)
    logger.info("Dataform terminou em %s", estado)
    return 0 if estado == "SUCCEEDED" else 1


if __name__ == "__main__":
    sys.exit(main())
