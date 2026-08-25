"""Leitura de credenciais no Google Secret Manager.

Regra da cláusula 8.5: credencial não entra em código, `.env` versionado,
log ou mensagem de erro. Só chega ao processo por aqui.
"""

from __future__ import annotations

from functools import lru_cache

from src.core.config import get_settings

PADRAO_NOME = "alupdata-{fonte}-{campo}"


def nome_secret(fonte: str, campo: str) -> str:
    """Nome canônico do secret de uma fonte."""
    return PADRAO_NOME.format(fonte=fonte, campo=campo)


@lru_cache
def ler_secret(fonte: str, campo: str, versao: str = "latest") -> str:
    """Valor do secret. Memoizado — não relê a cada requisição do conector."""
    from google.cloud import secretmanager  # import tardio: conector público não precisa

    cfg = get_settings()
    cliente = secretmanager.SecretManagerServiceClient()
    caminho = f"projects/{cfg.gcp_project_id}/secrets/{nome_secret(fonte, campo)}/versions/{versao}"
    resposta = cliente.access_secret_version(request={"name": caminho})
    return resposta.payload.data.decode("utf-8")
