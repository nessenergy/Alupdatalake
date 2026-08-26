"""De onde o Portal lê o que mostra.

Duas implementações do mesmo contrato: BigQuery, para quando o ambiente GCP
existir (pendência A3), e um provedor simulado que permite construir e testar a
tela antes disso. A troca é a variável `portal_provedor`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Protocol

from src.core.config import get_settings


@dataclass(frozen=True)
class Painel:
    """O que a tela precisa: uma tabela e quando ela foi alimentada."""

    view: str
    colunas: list[str]
    linhas: list[dict[str, Any]]
    ultima_ingestao: datetime | None
    fonte_ultima_ingestao: str | None


class ProvedorDados(Protocol):
    def painel(self, view: str) -> Painel: ...


class ProvedorSimulado:
    """Dados de exemplo, para desenvolver a tela sem ambiente GCP.

    Os números são inventados e rotulados como tal na interface — nunca são
    dado de cliente. Some no dia em que `portal_provedor=bigquery` for ligado.
    """

    def painel(self, view: str) -> Painel:
        return Painel(
            view=view,
            colunas=["periodo_apuracao", "cambio_medio", "cambio_fechamento", "dias_uteis"],
            linhas=[
                {
                    "periodo_apuracao": "2026-06",
                    "cambio_medio": Decimal("5.4210"),
                    "cambio_fechamento": Decimal("5.3980"),
                    "dias_uteis": 20,
                },
                {
                    "periodo_apuracao": "2026-07",
                    "cambio_medio": Decimal("5.3875"),
                    "cambio_fechamento": Decimal("5.4120"),
                    "dias_uteis": 23,
                },
                {
                    "periodo_apuracao": "2026-08",
                    "cambio_medio": Decimal("5.4501"),
                    "cambio_fechamento": Decimal("5.4655"),
                    "dias_uteis": 21,
                },
            ],
            ultima_ingestao=datetime(2026, 8, 26, 9, 0, tzinfo=UTC),
            fonte_ultima_ingestao="bcb_cambio_ptax",
        )


NOME_VALIDO = re.compile(r"[a-z][a-z0-9_]{2,62}")


class ProvedorBigQuery:
    """Lê a view Gold e o log de ingestão do BigQuery."""

    def painel(self, view: str) -> Painel:
        # O nome da view vem da configuração, não do request — mas identificador
        # não é parametrizável em SQL, então ele é conferido antes de entrar na
        # query, e não depois.
        if not NOME_VALIDO.fullmatch(view):
            raise ValueError(f"nome de view inválido: {view!r}")

        from google.cloud import bigquery  # import tardio

        cfg = get_settings()
        cliente = bigquery.Client(project=cfg.gcp_project_id)

        resultado = cliente.query(
            f"SELECT * FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.{view}` LIMIT @limite",  # noqa: S608
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("limite", "INT64", cfg.portal_limite_linhas)]
            ),
        ).result()
        colunas = [campo.name for campo in resultado.schema]
        linhas = [dict(linha) for linha in resultado]

        execucao = next(
            iter(
                cliente.query(
                    f"SELECT fonte, encerrada_em FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_bronze}._execucoes` "  # noqa: S608
                    "WHERE status = 'SUCESSO' ORDER BY encerrada_em DESC LIMIT 1"
                ).result()
            ),
            None,
        )

        return Painel(
            view=view,
            colunas=colunas,
            linhas=linhas,
            ultima_ingestao=execucao.encerrada_em if execucao else None,
            fonte_ultima_ingestao=execucao.fonte if execucao else None,
        )


def obter_provedor() -> ProvedorDados:
    """Provedor conforme a configuração. `simulado` enquanto A3 não chega."""
    return ProvedorBigQuery() if get_settings().portal_provedor == "bigquery" else ProvedorSimulado()
