"""Sessão HTTP padrão dos conectores: timeout explícito e retry com backoff.

Requisição sem timeout pendura a task no orquestrador até o limite do
ambiente — por isso o timeout não é opcional aqui.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.core.config import get_settings

_METODOS_IDEMPOTENTES = frozenset({"GET", "HEAD", "OPTIONS"})


def criar_sessao(max_tentativas: int | None = None) -> requests.Session:
    """Sessão com retry em 429/5xx e backoff exponencial."""
    cfg = get_settings()
    tentativas = max_tentativas or cfg.http_max_tentativas
    retry = Retry(
        total=tentativas,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=_METODOS_IDEMPOTENTES,
        raise_on_status=False,
    )
    sessao = requests.Session()
    adaptador = HTTPAdapter(max_retries=retry)
    sessao.mount("https://", adaptador)
    sessao.mount("http://", adaptador)
    return sessao


def get_json(sessao: requests.Session, url: str, params: dict[str, Any] | None = None) -> Any:
    """GET com timeout da configuração; levanta em status de erro."""
    cfg = get_settings()
    resposta = sessao.get(url, params=params, timeout=cfg.http_timeout)
    resposta.raise_for_status()
    return resposta.json()
