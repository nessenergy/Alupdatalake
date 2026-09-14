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

# Premissas de tarifa, conferidas na tabela oficial do BigQuery em 2026-09-14
# (issue #112). Continuam sendo **premissa declarada**, por dois motivos
# registrados aqui para quem ler o número depois:
#
# 1. A página cota armazenamento **por GiB-hora**, não por mês. A conversão usa
#    as 730 horas que o próprio Google adota: 0,000031507 × 730 = 0,023. O
#    valor anterior, 0,020, não corresponde a nenhuma linha de armazenamento
#    *lógico* da tabela atual — corresponde a *físico de longo prazo*, que é
#    outra coisa. Subestimava o armazenamento em ~15%.
# 2. A tabela tem três preços de consulta por TiB (6,25 / 6,5625 / 6,8125),
#    selecionados por região num seletor que roda no navegador. **Não foi
#    possível confirmar pela página pública qual deles vale para `us-east1`**;
#    adotamos o preço-base, que é o dos EUA. Se us-east1 estiver numa faixa
#    superior, a conta subestima na mesma proporção (5% ou 9%).
#
# A conferência definitiva não é esta: é o billing export (camada F2), que vê
# crédito e desconto por uso comprometido. Até lá, estes números servem para
# ordem de grandeza e comparação entre fontes, não para fatura.
TARIFA_TIB_VARRIDO_USD = Decimal("6.25")
TARIFA_GIB_MES_ATIVO_USD = Decimal("0.023")
TARIFA_EXECUCAO_JOB_USD = Decimal("0.004")

# O BigQuery cobra um mínimo por consulta, independente do quanto ela varreu.
# Ignorar isso subestima justamente o caso do lake pequeno com muita consulta —
# que é exatamente o nosso hoje.
MINIMO_BYTES_FATURADOS = 10 * 1024**2

# Os 8 domínios analíticos da resposta da Alup ao item B1, de 11/09:
# `docs/arquitetura/dominios-analiticos.md`. Deixou de ser agrupamento
# provisório por afinidade — a visão de diretoria fala o vocabulário que a
# própria Alup usa, e cada domínio tem dono nomeado.
DOMINIOS_VALIDOS = frozenset(
    {
        "Mercado de Energia",
        "Geração e Operacional",
        "Meteorologia",
        "Comercial e Contratos",
        "CRM e Marketing",
        "Risco e Compliance",
        "Econômico",
        "Planejamento",
    }
)

# Conector sem domínio cai em "Não classificado" e some da leitura da diretoria;
# o teste em `tests/unit/test_portal.py` impede que isso passe despercebido
# quando uma fonte nova entrar.
DOMINIO_ANALITICO = {
    "ccee_pld": "Mercado de Energia",
    "bbce_curva_forward": "Mercado de Energia",
    "ons_carga": "Mercado de Energia",
    # Cadastro do mercado: dá nome ao que nas outras fontes é código.
    "ccee_perfil": "Mercado de Energia",
    "aneel_siga": "Geração e Operacional",
    "tempook_boletins": "Meteorologia",
    "hubspot_negocios": "Comercial e Contratos",
    "bcb_cambio_ptax": "Econômico",
    "ibge_ipca": "Econômico",
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
        return DOMINIO_ANALITICO.get(self.fonte, "Não classificado")

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
        """Visão de diretoria: agrupamento pelos 8 domínios analíticos (14/09)."""
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
