"""Gravação do dado bruto no Cloud Storage, antes de qualquer parsing.

Se o parser tiver bug, reprocessa-se do GCS sem bater de novo na fonte —
algumas APIs do projeto têm rate limit ou retenção curta.
"""

from __future__ import annotations

import gzip
import json
import logging
from typing import TYPE_CHECKING, Any

from src.core.config import get_settings

if TYPE_CHECKING:
    from src.core.execucao import Execucao

logger = logging.getLogger(__name__)


def caminho_raw(execucao: Execucao) -> str:
    """Objeto de destino no bucket raw, particionado por data de referência."""
    dt = execucao.janela.inicio.isoformat()
    return f"{execucao.fonte}/{execucao.entidade}/dt={dt}/{execucao.ingestao_id}.json.gz"


def gravar_raw(execucao: Execucao, registros: list[dict[str, Any]]) -> str | None:
    """Grava os registros brutos como JSONL comprimido. Devolve o URI gs://."""
    cfg = get_settings()
    caminho = caminho_raw(execucao)
    uri = f"gs://{cfg.bucket_raw}/{caminho}"

    if cfg.dry_run:
        logger.info("dry-run: %d registros não gravados em %s", len(registros), uri)
        return None

    from google.cloud import storage  # import tardio: teste unitário não precisa do SDK

    corpo = "\n".join(json.dumps(r, ensure_ascii=False, default=str) for r in registros)
    blob = storage.Client(project=cfg.gcp_project_id).bucket(cfg.bucket_raw).blob(caminho)
    blob.content_encoding = "gzip"
    blob.upload_from_string(gzip.compress(corpo.encode("utf-8")), content_type="application/json")
    logger.info("raw gravado: %s (%d registros)", uri, len(registros))
    return uri
