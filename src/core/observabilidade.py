"""Log estruturado e correlação por execução.

O Cloud Logging lê JSON em stdout nativamente: `severity` vira o nível de
verdade (dá para filtrar por ERROR), e os demais campos viram `jsonPayload`
consultável. Texto corrido vira `textPayload` — um blob sem severidade e sem
filtro por fonte, que só serve para leitura humana.

Toda linha emitida durante uma ingestão carrega `ingestao_id`, `fonte` e
`entidade`. É o que costura o log ao registro de `bronze._execucoes`: da linha
"falhou" no painel até as 40 linhas daquela execução é um filtro, não uma caçada
por horário aproximado.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from copy import copy
from typing import TYPE_CHECKING, Any

from src.core.seguranca import sanitizar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Execucao

_contexto: ContextVar[dict[str, str] | None] = ContextVar("contexto_log", default=None)

# Os níveis do logging já são os nomes que o Cloud Logging espera; nível
# customizado, fora desta lista, cai em DEFAULT.
_SEVERIDADES = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})

FORMATO_TEXTO = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"


class FormatadorJson(logging.Formatter):
    """Uma linha JSON por registro, no formato que o Cloud Logging entende."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "severity": record.levelname if record.levelname in _SEVERIDADES else "DEFAULT",
            "message": sanitizar(record.getMessage()),
            "logger": record.name,
            **(_contexto.get() or {}),
        }
        if record.exc_info:
            # O Error Reporting agrupa por assinatura quando encontra este campo.
            payload["stack_trace"] = sanitizar(self.formatException(record.exc_info), limite=12000)
        return json.dumps(payload, ensure_ascii=False, default=str)


class FormatadorTexto(logging.Formatter):
    """Formato humano com a mesma redação aplicada ao JSON de produção."""

    def format(self, record: logging.LogRecord) -> str:
        seguro = copy(record)
        seguro.msg = sanitizar(record.getMessage())
        seguro.args = ()
        if record.exc_info:
            seguro.exc_text = sanitizar(self.formatException(record.exc_info), limite=12000)
        return super().format(seguro)


def _formato_padrao() -> str:
    """JSON quando roda no Cloud Run; texto no laptop, que é onde alguém lê."""
    if formato := os.getenv("LOG_FORMATO"):
        return formato.lower()
    return "json" if os.getenv("K_SERVICE") or os.getenv("CLOUD_RUN_JOB") else "texto"


def configurar_logging() -> None:
    """Configura o log do processo. Chamado uma vez, no entrypoint."""
    manipulador = logging.StreamHandler(sys.stdout)
    if _formato_padrao() == "json":
        manipulador.setFormatter(FormatadorJson())
    else:
        manipulador.setFormatter(FormatadorTexto(FORMATO_TEXTO, datefmt="%Y-%m-%d %H:%M:%S"))

    raiz = logging.getLogger()
    raiz.handlers = [manipulador]
    raiz.setLevel(logging.INFO)


@contextmanager
def contexto_execucao(execucao: Execucao) -> Iterator[None]:
    """Marca toda linha logada dentro do bloco com a identidade da execução."""
    token = _contexto.set(
        {
            "ingestao_id": execucao.ingestao_id,
            "fonte": execucao.fonte,
            "entidade": execucao.entidade,
            "janela": str(execucao.janela),
        }
    )
    try:
        yield
    finally:
        _contexto.reset(token)
