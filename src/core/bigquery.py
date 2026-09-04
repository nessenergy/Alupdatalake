"""Carga no BigQuery.

O Bronze é append-only: reprocessar a mesma janela insere de novo, e a
deduplicação é responsabilidade da view Silver. Isso mantém a auditoria do
que a fonte devolveu em cada execução.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

from src.core.config import get_settings
from src.core.seguranca import sanitizar

if TYPE_CHECKING:
    from src.core.execucao import Execucao

logger = logging.getLogger(__name__)

TABELA_EXECUCOES = "_execucoes"

# Rótulo do BigQuery aceita minúscula, dígito, sublinhado e hífen, até 63
# caracteres. Valor fora disso faz o job inteiro ser recusado, então o que não
# encaixa vira hífen em vez de quebrar a carga.
_FORA_DO_ROTULO = re.compile(r"[^a-z0-9_-]")


def _sanear(valor: str) -> str:
    return _FORA_DO_ROTULO.sub("-", valor.lower())[:63]


def rotulos(execucao: Execucao, camada: str = "bronze") -> dict[str, str]:
    """Rótulos do job — é o que atribui custo de varredura por fonte.

    Rótulo de *recurso* é fixo por recurso, e existe um único Cloud Run Job
    para as 13 fontes: por isso o compute sai correto no total e não se separa
    por fonte. O que se separa é byte varrido no BigQuery, e isso se resolve
    rotulando o **job**, que o cliente monta em tempo de execução — a saída 3
    de `docs/arquitetura/portal-finops.md` §4.

    Precisa existir desde o primeiro `apply`: custo já gasto não se rateia
    depois, porque o rateio se apoia no rótulo aplicado no momento do consumo.
    """
    return {
        "projeto": "alupdata",
        "fonte": _sanear(execucao.fonte),
        "entidade": _sanear(execucao.entidade),
        "camada": _sanear(camada),
        "modo": _sanear(execucao.modo),
        "ingestao_id": _sanear(execucao.ingestao_id),
    }


class RegistroExecucaoError(RuntimeError):
    """Carga pode ter ocorrido, mas sua evidência operacional não foi gravada."""


def cliente():
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

    job = cliente().load_table_from_json(
        linhas,
        tabela,
        job_config=bigquery.LoadJobConfig(
            write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
            labels=rotulos(execucao),
        ),
    )
    job.result()
    logger.info("carregadas %d linhas em %s", len(linhas), tabela)
    return len(linhas)


def registrar_execucao(execucao: Execucao) -> None:
    """Grava a linha de controle em `bronze._execucoes`.

    Falha aqui é propagada: uma carga sem evidência operacional não pode ser
    declarada como sucesso completo nem homologada.
    """
    cfg = get_settings()
    if cfg.dry_run:
        logger.info("dry-run: execução não registrada (%s)", execucao.status)
        return

    tabela = f"{cfg.gcp_project_id}.{cfg.bq_dataset_bronze}.{TABELA_EXECUCOES}"
    try:
        erros = cliente().insert_rows_json(tabela, [execucao.to_row()])
        if erros:
            raise RegistroExecucaoError(sanitizar(f"BigQuery recusou o registro operacional: {erros}"))
    except RegistroExecucaoError:
        raise
    except Exception as exc:
        raise RegistroExecucaoError(sanitizar(f"falha ao registrar execução em {tabela}: {exc}")) from exc
