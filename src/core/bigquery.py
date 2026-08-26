"""Carga no BigQuery.

O Bronze é append-only: reprocessar a mesma janela insere de novo, e a
deduplicação é responsabilidade da view Silver. Isso mantém a auditoria do
que a fonte devolveu em cada execução.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.core.config import get_settings

if TYPE_CHECKING:
    from src.core.execucao import Execucao

logger = logging.getLogger(__name__)

TABELA_EXECUCOES = "_execucoes"


def _cliente():
    from google.cloud import bigquery  # import tardio

    return bigquery.Client(project=get_settings().gcp_project_id)


def carregar_bronze(execucao: Execucao, linhas: list[dict[str, Any]]) -> int:
    """Insere as linhas na tabela Bronze da entidade. Devolve o total carregado."""
    cfg = get_settings()
    tabela = cfg.tabela_bronze(execucao.fonte, execucao.entidade)

    if cfg.dry_run:
        logger.info("dry-run: %d linhas não carregadas em %s", len(linhas), tabela)
        return 0
    if not linhas:
        logger.info("nada a carregar em %s", tabela)
        return 0

    from google.cloud import bigquery

    job = _cliente().load_table_from_json(
        linhas,
        tabela,
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        ),
    )
    job.result()
    logger.info("carregadas %d linhas em %s", len(linhas), tabela)
    return len(linhas)


def registrar_execucao(execucao: Execucao) -> None:
    """Grava a linha de controle em `bronze._execucoes`.

    Falha aqui é logada, não propagada: perder o log de controle não pode
    derrubar uma ingestão que deu certo.
    """
    cfg = get_settings()
    if cfg.dry_run:
        logger.info("dry-run: execução não registrada (%s)", execucao.status)
        return

    tabela = f"{cfg.gcp_project_id}.{cfg.bq_dataset_bronze}.{TABELA_EXECUCOES}"
    try:
        erros = _cliente().insert_rows_json(tabela, [execucao.to_row()])
        if erros:
            logger.error("falha ao registrar execução em %s: %s", tabela, erros)
    except Exception as exc:  # noqa: BLE001 — log de controle nunca derruba a ingestão
        logger.error("falha ao registrar execução em %s: %s", tabela, exc)
