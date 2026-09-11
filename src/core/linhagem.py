"""Linhagem da origem até o Bronze (ADR 013).

O Knowledge Catalog registra sozinho a linhagem de BigQuery e Dataform, mas
não vê o que acontece antes do Bronze. O executor emite um evento OpenLineage
por ingestão, com a origem em namespace `custom` e o destino na tabela Bronze.

Falha ao emitir não falha a ingestão: linhagem é metadado, e o dado já está no
Bronze. Vira aviso no log.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.core.config import get_settings
from src.core.seguranca import sanitizar

if TYPE_CHECKING:
    from src.core.execucao import Execucao

logger = logging.getLogger(__name__)

API = "https://datalineage.googleapis.com/v1"
PRODUTOR = "https://github.com/nessenergy/Alupdatalake"
ESQUEMA = "https://openlineage.io/spec/1-0-5/OpenLineage.json#/$defs/RunEvent"


def evento(execucao: Execucao, origem: str, tabela_bronze: str) -> dict[str, Any]:
    """Evento OpenLineage de uma ingestão: origem externa → tabela Bronze."""
    return {
        "eventType": "COMPLETE" if execucao.status == "SUCESSO" else "FAIL",
        "eventTime": (execucao.encerrada_em or datetime.now(UTC)).isoformat(),
        "producer": PRODUTOR,
        "schemaURL": ESQUEMA,
        # O ingestao_id é um UUID sem hífens; o OpenLineage espera o formato canônico.
        "run": {"runId": str(uuid.UUID(execucao.ingestao_id))},
        "job": {"namespace": "alupdata", "name": f"ingestao.{execucao.fonte}_{execucao.entidade}"},
        "inputs": [{"namespace": "custom", "name": origem}],
        "outputs": [{"namespace": "bigquery", "name": tabela_bronze}],
    }


def _sessao() -> Any:
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    credenciais, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(credenciais)


def emitir(execucao: Execucao, origem: str, sessao: Any | None = None) -> None:
    """Envia o evento ao Data Lineage. Nunca levanta exceção."""
    cfg = get_settings()
    if cfg.dry_run:
        logger.info("dry-run: linhagem não emitida (%s)", execucao.ingestao_id)
        return

    try:
        corpo = evento(execucao, origem, cfg.tabela_bronze(execucao.fonte, execucao.entidade))
        url = f"{API}/projects/{cfg.gcp_project_id}/locations/{cfg.gcp_region}:processOpenLineageRunEvent"
        resposta = (sessao or _sessao()).post(url, json=corpo, timeout=cfg.http_timeout)
        resposta.raise_for_status()
    except Exception as exc:  # noqa: BLE001 — linhagem é metadado; não derruba a ingestão
        detalhe = sanitizar(str(exc))
        corpo_resposta = getattr(exc, "response", None)
        texto_resposta = getattr(corpo_resposta, "text", None)
        if texto_resposta:
            detalhe = f"{detalhe} | resposta da API: {sanitizar(texto_resposta, limite=500)}"
        logger.warning("linhagem não registrada para %s: %s", execucao.ingestao_id, detalhe)
