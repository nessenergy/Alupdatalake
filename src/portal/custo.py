"""Modelo de custo de nuvem do DataLake — as três visões da §5-A do plano.

Uma tela, três recortes do mesmo número: operacional (o que eu mudo hoje),
orçamento (estamos dentro do previsto) e diretoria (vale o que custa).
Plano completo em `docs/arquitetura/portal-finops.md`.

As tarifas abaixo são **premissa declarada**, não verdade. Quando a camada F2
existir, o número oficial vem do billing export — que enxerga crédito e
desconto por uso comprometido, coisas que nenhuma conta feita aqui vê.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

TIB = 1024**4
GIB = 1024**3

# Premissas de tarifa. Conferir na tabela vigente da região antes de tratar
# qualquer número desta tela como oficial — ver docstring do módulo.
TARIFA_TIB_VARRIDO_USD = Decimal("6.25")
TARIFA_GIB_MES_ATIVO_USD = Decimal("0.020")
TARIFA_EXECUCAO_JOB_USD = Decimal("0.004")

# O BigQuery cobra um mínimo por consulta, independente do quanto ela varreu.
# Ignorar isso subestima justamente o caso do lake pequeno com muita consulta —
# que é exatamente o nosso hoje.
MINIMO_BYTES_FATURADOS = 10 * 1024**2

# Agrupamento provisório de fontes em domínio de negócio. Os 8 domínios
# analíticos dependem do Questionário de Gaps (pendência A4) — até lá, a visão
# de diretoria agrupa por afinidade óbvia e diz que é provisório.
DOMINIO_PROVISORIO = {
    "bcb_cambio_ptax": "Macroeconomia",
    "ibge_ipca": "Macroeconomia",
    "ons_carga": "Operação do sistema",
    "aneel_siga": "Ativos de geração",
    "hubspot_negocios": "Comercial",
}

# Quanto ocupa uma linha de cada fonte, em bytes. Estimativa de largura de
# schema; no ambiente real sai de `INFORMATION_SCHEMA.PARTITIONS`.
BYTES_POR_LINHA = {
    "bcb_cambio_ptax": 96,
    "ibge_ipca": 128,
    "ons_carga": 184,
    "aneel_siga": 640,
    "hubspot_negocios": 512,
}
BYTES_POR_LINHA_PADRAO = 256


@dataclass(frozen=True)
class CustoDia:
    """Um dia de gasto, quebrado pelo que a fatura separa."""

    dia: date
    query_usd: Decimal
    armazenamento_usd: Decimal
    compute_usd: Decimal

    @property
    def total_usd(self) -> Decimal:
        return self.query_usd + self.armazenamento_usd + self.compute_usd


@dataclass(frozen=True)
class CustoFonte:
    """Gasto atribuído a uma fonte — só existe porque F0 rotulou o job."""

    fonte: str
    query_usd: Decimal
    armazenamento_usd: Decimal
    bytes_varridos: int
    linhas: int

    @property
    def total_usd(self) -> Decimal:
        return self.query_usd + self.armazenamento_usd

    @property
    def dominio(self) -> str:
        return DOMINIO_PROVISORIO.get(self.fonte, "Não classificado")

    @property
    def usd_por_milhao_de_linhas(self) -> Decimal | None:
        """O número que diz se uma fonte é cara pelo que entrega, ou só cara."""
        if not self.linhas:
            return None
        return self.total_usd / Decimal(self.linhas) * Decimal(1_000_000)


@dataclass(frozen=True)
class ConsultaCara:
    """Uma consulta que puxa a conta — a unidade de ação da visão operacional."""

    rotulo: str
    fonte: str
    camada: str
    execucoes: int
    bytes_varridos: int
    custo_usd: Decimal
    variacao_vs_media: float
    """Quanto o custo desta consulta desviou da média móvel dela mesma."""

    @property
    def anomala(self) -> bool:
        """Dobrar em relação à própria média é sinal, não ruído."""
        return self.variacao_vs_media >= 1.0


@dataclass(frozen=True)
class Orcamento:
    """Realizado contra orçado, e para onde a curva do mês aponta."""

    mes: date
    orcado_usd: Decimal
    realizado_usd: Decimal
    dias_decorridos: int
    dias_do_mes: int

    @property
    def projetado_usd(self) -> Decimal:
        if not self.dias_decorridos:
            return Decimal(0)
        return self.realizado_usd / Decimal(self.dias_decorridos) * Decimal(self.dias_do_mes)

    @property
    def consumo_pct(self) -> float:
        if not self.orcado_usd:
            return 0.0
        return float(self.realizado_usd / self.orcado_usd)

    @property
    def projecao_pct(self) -> float:
        if not self.orcado_usd:
            return 0.0
        return float(self.projetado_usd / self.orcado_usd)

    @property
    def estoura(self) -> bool:
        return self.projetado_usd > self.orcado_usd


@dataclass(frozen=True)
class PainelCusto:
    """Tudo que a rota `/custo` precisa, em uma leitura só."""

    dias: list[CustoDia]
    fontes: list[CustoFonte]
    consultas: list[ConsultaCara]
    orcamento: Orcamento

    @property
    def total_usd(self) -> Decimal:
        return sum((d.total_usd for d in self.dias), Decimal(0))

    @property
    def por_dominio(self) -> list[tuple[str, Decimal]]:
        """Visão de diretoria: agrupamento provisório até A4 definir os domínios."""
        acumulado: dict[str, Decimal] = {}
        for fonte in self.fontes:
            acumulado[fonte.dominio] = acumulado.get(fonte.dominio, Decimal(0)) + fonte.total_usd
        return sorted(acumulado.items(), key=lambda item: item[1], reverse=True)


def custo_de_query(bytes_varridos: int, consultas: int = 1) -> Decimal:
    """Custo exato, sem arredondar — quem arredonda é a formatação, no fim.

    Arredondar a cada dia zera tudo num lake pequeno: trinta parcelas de meio
    centavo viram trinta zeros, e o total mente.
    """
    faturado = max(bytes_varridos, MINIMO_BYTES_FATURADOS * max(consultas, 1))
    return Decimal(faturado) / Decimal(TIB) * TARIFA_TIB_VARRIDO_USD


def custo_de_armazenamento_dia(bytes_armazenados: int) -> Decimal:
    """Tarifa é mensal; um dia é 1/30 dela."""
    return Decimal(bytes_armazenados) / Decimal(GIB) * TARIFA_GIB_MES_ATIVO_USD / Decimal(30)
