"""Sessão HTTP padrão dos conectores: timeout explícito, retry com backoff e
identificação do coletor.

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

# Quem está consumindo, e a quem recorrer. Não é credencial: é o cartão de
# visita do coletor, e por isso vive no código e não no Secret Manager.
#
# A CCEE respondia 403 a cliente não identificado, e foi esse cabeçalho que
# destravou a Onda 1 (ADR 018). Ele fica aqui, e não no conector da CCEE, por
# dois motivos: identificar-se é a conduta correta com qualquer origem, e
# qualquer outra fonte pública pode ligar o mesmo filtro amanhã.
USER_AGENT = "Alupar-DataCollector/1.0 (+https://alupar.com.br; contato: comercializacao@alupar.com.br)"


def criar_sessao(*, retry_post: bool = False) -> requests.Session:
    """Sessão com retry em 429/5xx e backoff exponencial.

    POST fica desligado por padrão. Conectores podem habilitá-lo somente para
    endpoints de consulta cuja repetição não produz efeito na origem.
    """
    cfg = get_settings()
    metodos = _METODOS_IDEMPOTENTES | ({"POST"} if retry_post else set())
    retry = Retry(
        total=cfg.http_max_tentativas,
        backoff_factor=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=metodos,
        raise_on_status=False,
    )
    sessao = requests.Session()
    sessao.headers["User-Agent"] = USER_AGENT
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
