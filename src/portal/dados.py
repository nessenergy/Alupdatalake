"""De onde o Portal lê o que mostra.

Duas implementações do mesmo contrato: BigQuery, para quando o ambiente GCP
existir (pendência A3), e um provedor simulado que permite construir e testar a
tela antes disso. A troca é a variável `portal_provedor`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any, Protocol

from src.core.bigquery import cliente
from src.core.config import get_settings
from src.portal.custo import (
    BYTES_POR_LINHA,
    BYTES_POR_LINHA_PADRAO,
    TARIFA_EXECUCAO_JOB_USD,
    ConsultaCara,
    CustoDia,
    CustoFonte,
    Orcamento,
    PainelCusto,
    custo_de_armazenamento_dia,
    custo_de_query,
)


@dataclass(frozen=True)
class Painel:
    """O que a tela precisa: uma tabela e quando ela foi alimentada."""

    view: str
    colunas: list[str]
    linhas: list[dict[str, Any]]
    ultima_ingestao: datetime | None
    fonte_ultima_ingestao: str | None


@dataclass(frozen=True)
class SaudeConector:
    """Uma linha de `gold.saude_ingestao`."""

    conector: str
    situacao: str
    ultimo_sucesso: datetime | None
    minutos_desde_sucesso: int | None
    intervalo_tipico_min: int | None
    taxa_sucesso_30d: float | None
    taxa_invalidas: float | None
    linhas_carregadas_total: int
    duracao_p95_seg: float | None
    ultimo_erro: str | None = None


@dataclass(frozen=True)
class SerieVolumetria:
    """Linhas carregadas por dia, de um conector — `gold.volumetria_lake`."""

    conector: str
    dias: list[date]
    linhas: list[int]

    @property
    def total(self) -> int:
        return sum(self.linhas)


class ProvedorDados(Protocol):
    def painel(self, view: str) -> Painel: ...
    def saude(self) -> list[SaudeConector]: ...
    def volumetria(self, dias: int = 30) -> list[SerieVolumetria]: ...
    def custo(self, dias: int = 30) -> PainelCusto: ...


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

    def saude(self) -> list[SaudeConector]:
        return [
            SaudeConector(
                "bcb_cambio_ptax", "OK", datetime(2026, 8, 26, 9, 0, tzinfo=UTC), 95, 1440, 1.0, 0.0, 1_284, 4.2
            ),
            SaudeConector(
                "ons_carga", "OK", datetime(2026, 8, 26, 8, 2, tzinfo=UTC), 153, 1440, 0.97, 0.004, 8_930, 11.8
            ),
            SaudeConector(
                "aneel_siga",
                "ATRASADA",
                datetime(2026, 8, 17, 7, 0, tzinfo=UTC),
                13_055,
                10_080,
                0.92,
                0.0,
                75_789,
                31.4,
            ),
            SaudeConector(
                "ibge_ipca", "OK", datetime(2026, 8, 12, 10, 0, tzinfo=UTC), 20_315, 43_200, 1.0, 0.0, 72, 2.1
            ),
            SaudeConector(
                "hubspot_negocios",
                "SEM_SUCESSO",
                None,
                None,
                None,
                0.0,
                None,
                0,
                None,
                "PermissionDenied: 401 — token ausente (pendência A9)",
            ),
        ]

    def volumetria(self, dias: int = 30) -> list[SerieVolumetria]:
        """Séries determinísticas: mesma entrada, mesmo desenho — teste não oscila."""
        fim = date(2026, 8, 26)
        calendario = [fim - timedelta(days=i) for i in reversed(range(dias))]
        # (base, amplitude, período) — só as séries diárias; as outras três têm
        # forma própria logo abaixo.
        diarios = {"bcb_cambio_ptax": (3, 1, 7), "ons_carga": (28, 9, 7)}

        def onda(base: int, amplitude: int, periodo: int) -> list[int]:
            return [
                max(0, base + round(amplitude * ((i % periodo) - periodo / 2) / periodo * 2))
                if dia.weekday() < 5
                else 0
                for i, dia in enumerate(calendario)
            ]

        linhas_por_conector = {
            **{conector: onda(*perfil) for conector, perfil in diarios.items()},
            "aneel_siga": [25_263 if dia.weekday() == 0 else 0 for dia in calendario],  # cadastro semanal
            "ibge_ipca": [12 if dia.day == 12 else 0 for dia in calendario],  # mensal: um ponto só
            "hubspot_negocios": [0] * dias,  # sem token: série vazia
        }
        return [SerieVolumetria(conector, calendario, linhas) for conector, linhas in linhas_por_conector.items()]

    # Quanto cada camada varre, como fração do que está acumulado em Bronze.
    # A Silver varre a partição do dia; a Gold e o Portal varrem histórico.
    FRACAO_VARRIDA = {"silver": 0.0, "gold": 0.15, "portal": 0.02}

    # Uma consulta deliberadamente mal escrita, para a tela ter o que denunciar:
    # a Gold da ANEEL varre a tabela inteira em vez da partição.
    VARREDURA_INTEGRAL = "aneel_siga"

    ORCADO_MENSAL_USD = Decimal("120.00")

    def custo(self, dias: int = 30) -> PainelCusto:
        """Custo derivado da própria volumetria simulada — não é número solto.

        Byte varrido acompanha linha carregada, e armazenamento acompanha o
        acumulado. Assim a tela de custo conta a mesma história que a de saúde:
        a fonte que carrega mais é a que aparece na conta.
        """
        series = self.volumetria(dias)
        calendario = series[0].dias if series else []

        por_dia: dict[date, dict[str, Decimal]] = {
            dia: {"query": Decimal(0), "armazenamento": Decimal(0), "compute": Decimal(0)} for dia in calendario
        }
        totais: dict[str, dict[str, int | Decimal]] = {}

        for serie in series:
            bpl = BYTES_POR_LINHA.get(serie.conector, BYTES_POR_LINHA_PADRAO)
            acumulado = 0
            varrido_fonte = 0
            query_fonte = Decimal(0)
            armazenamento_fonte = Decimal(0)

            for dia, linhas in zip(serie.dias, serie.linhas, strict=True):
                acumulado += linhas
                if not acumulado:
                    # Fonte que nunca carregou nada não tem tabela para varrer,
                    # e portanto não custa. O Hubspot está exatamente nesse
                    # estado enquanto o token de A9 não chega.
                    continue
                armazenado = acumulado * bpl

                fracao_gold = 1.0 if serie.conector == self.VARREDURA_INTEGRAL else self.FRACAO_VARRIDA["gold"]
                varrido = (
                    linhas * bpl  # Silver: só a partição do dia
                    + int(armazenado * fracao_gold)  # Gold
                    + int(armazenado * self.FRACAO_VARRIDA["portal"])  # Portal
                )

                custo_query = custo_de_query(varrido, consultas=3 if linhas else 2)
                custo_armazenamento = custo_de_armazenamento_dia(armazenado)
                custo_compute = TARIFA_EXECUCAO_JOB_USD if linhas else Decimal(0)

                por_dia[dia]["query"] += custo_query
                por_dia[dia]["armazenamento"] += custo_armazenamento
                por_dia[dia]["compute"] += custo_compute

                varrido_fonte += varrido
                query_fonte += custo_query
                armazenamento_fonte += custo_armazenamento

            totais[serie.conector] = {
                "query": query_fonte,
                "armazenamento": armazenamento_fonte,
                "bytes": varrido_fonte,
                "linhas": acumulado,
            }

        dias_custo = [
            CustoDia(dia, valores["query"], valores["armazenamento"], valores["compute"])
            for dia, valores in por_dia.items()
        ]
        fontes = sorted(
            (
                CustoFonte(
                    fonte=conector,
                    query_usd=v["query"],  # type: ignore[arg-type]
                    armazenamento_usd=v["armazenamento"],  # type: ignore[arg-type]
                    bytes_varridos=int(v["bytes"]),
                    linhas=int(v["linhas"]),
                )
                for conector, v in totais.items()
            ),
            key=lambda f: f.total_usd,
            reverse=True,
        )

        return PainelCusto(
            dias=dias_custo,
            fontes=fontes,
            consultas=self._consultas_caras(series),
            orcamento=self._orcamento(dias_custo),
        )

    def _consultas_caras(self, series: list[SerieVolumetria]) -> list[ConsultaCara]:
        """As consultas do último dia, ordenadas por byte varrido."""
        consultas = []
        for serie in series:
            if not serie.linhas or not any(serie.linhas):
                continue
            bpl = BYTES_POR_LINHA.get(serie.conector, BYTES_POR_LINHA_PADRAO)
            acumulado = sum(serie.linhas) * bpl
            integral = serie.conector == self.VARREDURA_INTEGRAL

            varrido = int(acumulado * (1.0 if integral else self.FRACAO_VARRIDA["gold"]))
            consultas.append(
                ConsultaCara(
                    rotulo=f"gold.{serie.conector}",
                    fonte=serie.conector,
                    camada="gold",
                    execucoes=len([v for v in serie.linhas if v]),
                    bytes_varridos=varrido,
                    custo_usd=custo_de_query(varrido, consultas=len([v for v in serie.linhas if v])),
                    # A varredura integral custa o histórico inteiro toda vez;
                    # é isso que a faz destoar da própria média.
                    variacao_vs_media=5.6 if integral else 0.08,
                )
            )
        # Ordena por custo, não por byte varrido: com o mínimo por consulta em
        # vigor, a consulta que varre mais nem sempre é a que custa mais.
        return sorted(consultas, key=lambda c: c.custo_usd, reverse=True)

    def _orcamento(self, dias: list[CustoDia]) -> Orcamento:
        if not dias:
            hoje = date(2026, 8, 26)
            return Orcamento(hoje.replace(day=1), self.ORCADO_MENSAL_USD, Decimal(0), 0, 31)
        ultimo = dias[-1].dia
        do_mes = [d for d in dias if d.dia.month == ultimo.month and d.dia.year == ultimo.year]
        return Orcamento(
            mes=ultimo.replace(day=1),
            orcado_usd=self.ORCADO_MENSAL_USD,
            realizado_usd=sum((d.total_usd for d in do_mes), Decimal(0)),
            dias_decorridos=ultimo.day,
            dias_do_mes=31,
        )


NOME_VALIDO = re.compile(r"[a-z][a-z0-9_]{2,62}")


class ProvedorBigQuery:
    """Lê a view Gold e o log de ingestão do BigQuery.

    Sobre as supressões `S608`/`B608` abaixo: nome de dataset e de view não é
    parametrizável em SQL — só valor é. Os identificadores vêm da configuração
    do serviço, nunca do request, e o único que varia (`view`) passa por
    `NOME_VALIDO` antes de entrar na query. Todo valor de request continua indo
    por `ScalarQueryParameter`.
    """

    def painel(self, view: str) -> Painel:
        # O nome da view vem da configuração, não do request — mas identificador
        # não é parametrizável em SQL, então ele é conferido antes de entrar na
        # query, e não depois.
        if not NOME_VALIDO.fullmatch(view):
            raise ValueError(f"nome de view inválido: {view!r}")

        from google.cloud import bigquery  # import tardio

        cfg = get_settings()
        bq = cliente()

        resultado = bq.query(
            f"SELECT * FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.{view}` LIMIT @limite",  # noqa: S608  # nosec B608
            job_config=bigquery.QueryJobConfig(
                query_parameters=[bigquery.ScalarQueryParameter("limite", "INT64", cfg.portal_limite_linhas)]
            ),
        ).result()
        colunas = [campo.name for campo in resultado.schema]
        linhas = [dict(linha) for linha in resultado]

        execucao = next(
            iter(
                bq.query(
                    f"SELECT fonte, encerrada_em FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_bronze}._execucoes` "  # noqa: S608  # nosec B608
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

    def saude(self) -> list[SaudeConector]:
        cfg = get_settings()
        sql = (
            "SELECT conector, situacao, ultimo_sucesso, minutos_desde_sucesso, "  # noqa: S608  # nosec B608
            "intervalo_tipico_min, taxa_sucesso_30d, taxa_invalidas, "
            "linhas_carregadas_total, duracao_p95_seg, ultimo_erro "
            f"FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.saude_ingestao` "
            "ORDER BY conector"
        )
        linhas = cliente().query(sql).result()
        return [
            SaudeConector(
                conector=linha.conector,
                situacao=linha.situacao,
                ultimo_sucesso=linha.ultimo_sucesso,
                minutos_desde_sucesso=linha.minutos_desde_sucesso,
                intervalo_tipico_min=linha.intervalo_tipico_min,
                taxa_sucesso_30d=linha.taxa_sucesso_30d,
                taxa_invalidas=linha.taxa_invalidas,
                linhas_carregadas_total=linha.linhas_carregadas_total or 0,
                duracao_p95_seg=linha.duracao_p95_seg,
                ultimo_erro=linha.ultimo_erro,
            )
            for linha in linhas
        ]

    def volumetria(self, dias: int = 30) -> list[SerieVolumetria]:
        from google.cloud import bigquery  # import tardio

        cfg = get_settings()
        linhas = (
            cliente()
            .query(
                f"SELECT conector, dia, linhas_carregadas "  # noqa: S608  # nosec B608
                f"FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.volumetria_lake` "
                "WHERE dia >= DATE_SUB(CURRENT_DATE(), INTERVAL @dias DAY) ORDER BY conector, dia",
                job_config=bigquery.QueryJobConfig(
                    query_parameters=[bigquery.ScalarQueryParameter("dias", "INT64", dias)]
                ),
            )
            .result()
        )

        por_conector: dict[str, list[tuple[date, int]]] = {}
        for linha in linhas:
            por_conector.setdefault(linha.conector, []).append((linha.dia, linha.linhas_carregadas or 0))
        return [
            SerieVolumetria(conector, [d for d, _ in pontos], [v for _, v in pontos])
            for conector, pontos in por_conector.items()
        ]

    def custo(self, dias: int = 30) -> PainelCusto:
        """Lê `gold.custo_consultas` — a regra fica no SQL, como na ADR 006.

        Enquanto a camada F2 não existir, isto cobre o BigQuery (byte varrido e
        armazenamento), que é a maior parcela da conta do lake. Compute e
        serviços de terceiros só entram com o billing export.
        """
        from google.cloud import bigquery  # import tardio

        cfg = get_settings()
        cliente = bigquery.Client(project=cfg.gcp_project_id)
        config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("dias", "INT64", dias)],
            # O próprio Portal rotula suas consultas: sem isto, a tela de custo
            # não consegue separar o que ela mesma gasta.
            labels={"componente": "portal", "camada": "gold"},
        )
        sql = (
            "SELECT dia, fonte, camada, consulta, execucoes, bytes_varridos, "  # noqa: S608  # nosec B608
            "custo_query_usd, custo_armazenamento_usd, linhas_carregadas, variacao_vs_media "
            f"FROM `{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.custo_consultas` "
            "WHERE dia >= DATE_SUB(CURRENT_DATE(), INTERVAL @dias DAY) ORDER BY dia"
        )
        linhas = list(cliente.query(sql, job_config=config).result())

        por_dia: dict[date, dict[str, Decimal]] = {}
        por_fonte: dict[str, dict[str, Decimal | int]] = {}
        for linha in linhas:
            dia = por_dia.setdefault(
                linha.dia, {"query": Decimal(0), "armazenamento": Decimal(0), "compute": Decimal(0)}
            )
            dia["query"] += Decimal(str(linha.custo_query_usd or 0))
            dia["armazenamento"] += Decimal(str(linha.custo_armazenamento_usd or 0))

            fonte = por_fonte.setdefault(
                linha.fonte or "não rotulado",
                {"query": Decimal(0), "armazenamento": Decimal(0), "bytes": 0, "linhas": 0},
            )
            fonte["query"] += Decimal(str(linha.custo_query_usd or 0))
            fonte["armazenamento"] += Decimal(str(linha.custo_armazenamento_usd or 0))
            fonte["bytes"] += linha.bytes_varridos or 0
            fonte["linhas"] += linha.linhas_carregadas or 0

        dias_custo = [CustoDia(dia, v["query"], v["armazenamento"], v["compute"]) for dia, v in sorted(por_dia.items())]
        fontes = sorted(
            (
                CustoFonte(nome, v["query"], v["armazenamento"], int(v["bytes"]), int(v["linhas"]))  # type: ignore[arg-type]
                for nome, v in por_fonte.items()
            ),
            key=lambda f: f.total_usd,
            reverse=True,
        )
        consultas = [
            ConsultaCara(
                rotulo=linha.consulta,
                fonte=linha.fonte or "não rotulado",
                camada=linha.camada or "—",
                execucoes=linha.execucoes or 0,
                bytes_varridos=linha.bytes_varridos or 0,
                custo_usd=Decimal(str(linha.custo_query_usd or 0)),
                variacao_vs_media=float(linha.variacao_vs_media or 0.0),
            )
            for linha in sorted(linhas, key=lambda linha: linha.bytes_varridos or 0, reverse=True)[:10]
        ]

        ultimo = dias_custo[-1].dia if dias_custo else date.today()  # noqa: DTZ011
        do_mes = [d for d in dias_custo if (d.dia.year, d.dia.month) == (ultimo.year, ultimo.month)]
        orcamento = Orcamento(
            mes=ultimo.replace(day=1),
            orcado_usd=Decimal(str(cfg.portal_orcamento_mensal_usd)),
            realizado_usd=sum((d.total_usd for d in do_mes), Decimal(0)),
            dias_decorridos=ultimo.day,
            dias_do_mes=31,
        )
        return PainelCusto(dias=dias_custo, fontes=fontes, consultas=consultas, orcamento=orcamento)


def obter_provedor() -> ProvedorDados:
    """Provedor conforme a configuração. `simulado` enquanto A3 não chega."""
    return ProvedorBigQuery() if get_settings().portal_provedor == "bigquery" else ProvedorSimulado()
