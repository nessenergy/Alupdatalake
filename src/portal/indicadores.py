"""Tela de indicadores: um cartão por recorte, com a conta à vista.

Razões técnicas do setor (ADR 012, adendo de 27/09). A conta é do Dataform
(`gold.indicadores_mensais`); aqui só se mostra. Indicador não tem meta: a
variação é texto neutro, sem cor de bom ou ruim.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

from src.portal.grafico import tendencia_mensal

if TYPE_CHECKING:
    from decimal import Decimal

    from src.portal.dados import Indicador

POR_PAGINA_NO_TELAO = 12

# Ordem, título e o que cada razão mede — em linguagem de quem lê, não de SQL.
INDICADORES = (
    (
        "taxa_corte_renovavel",
        "Taxa de corte renovável",
        "Quanto da geração eólica e solar possível o sistema mandou não gerar (constrained-off).",
    ),
    ("disponibilidade", "Disponibilidade", "Quanto da potência instalada das usinas despachadas estava apta a gerar."),
    (
        "fator_capacidade",
        "Fator de capacidade",
        "Quanto a geração média ocupou da potência efetiva, por submercado e fonte.",
    ),
    ("armazenamento", "Armazenamento", "Quanto dos reservatórios estava cheio, em energia armazenada."),
    ("pld_real", "PLD real", "O PLD médio descontada a inflação, em reais do mês-base."),
)

MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def mes(periodo: str, *, curto: bool = False) -> str:
    """`2026-08` vira `ago/2026` (ou `ago/26`); formato inesperado passa como veio."""
    ano, _, numero = periodo.partition("-")
    if not (numero.isdigit() and 1 <= int(numero) <= 12):
        return periodo
    return f"{MESES[int(numero) - 1]}/{ano[-2:] if curto else ano}"


def _br(valor: float, casas: int) -> str:
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _grandeza(valor: Decimal) -> str:
    """Numerador e denominador com as casas que a ordem de grandeza pede."""
    absoluto = abs(float(valor))
    return _br(float(valor), 0 if absoluto >= 100 else 2 if absoluto >= 1 else 4)


def valor_texto(linha: Indicador) -> str:
    if linha.valor is None:
        return "—"
    if linha.unidade_valor == "fração":
        return f"{_br(float(linha.valor) * 100, 1)}%"
    return f"R$ {_br(float(linha.valor), 2)}"


def _valor_destaque(linha: Indicador) -> str:
    if linha.valor is None:
        return "—"
    if linha.unidade_valor == "fração":
        return f"{_br(float(linha.valor) * 100, 1)}<small>%</small>"
    return f"<small>R$</small> {_br(float(linha.valor), 2)}"


def _variacao(atual: Indicador, anterior: Indicador | None) -> str:
    """Diferença contra o mês anterior, em texto e sem cor: não há meta (ADR 012)."""
    if anterior is None or atual.valor is None or anterior.valor is None:
        return "sem mês anterior para comparar"
    delta = float(atual.valor) - float(anterior.valor)
    seta = "↑" if delta > 0 else "↓" if delta < 0 else "="
    sinal = "+" if delta >= 0 else "−"
    texto = (
        f"{sinal}{_br(abs(delta) * 100, 1)} p.p."
        if atual.unidade_valor == "fração"
        else f"{sinal}R$ {_br(abs(delta), 2)}"
    )
    return f'<span aria-hidden="true">{seta}</span> <b>{texto}</b> vs. {mes(anterior.periodo_apuracao)}'


def _cartao(titulo: str, recorte: str, por_mes: dict[str, Indicador]) -> str:
    meses = sorted(por_mes)
    atual = por_mes[meses[-1]]
    anterior = por_mes[meses[-2]] if len(meses) > 1 else None
    com_valor = [(m, por_mes[m]) for m in meses if por_mes[m].valor is not None]
    pontos = [(mes(m, curto=True), float(ind.valor)) for m, ind in com_valor if ind.valor is not None]
    rotulo = (
        f"Tendência de {mes(meses[0])} a {mes(meses[-1])}: de {valor_texto(com_valor[0][1])} a "
        f"{valor_texto(com_valor[-1][1])}"
        if com_valor
        else f"{titulo}, {recorte}: sem valor calculado"
    )
    # Só os números na conta; o que cada um mede vem na linha de baixo, em letra menor.
    conta = f"{_grandeza(atual.numerador)} ÷ {_grandeza(atual.denominador)}"
    termos = f"{html.escape(atual.unidade_numerador)} ÷ {html.escape(atual.unidade_denominador)}"
    serie = "".join(
        f"<tr><td>{mes(m, curto=True)}</td><td>{valor_texto(por_mes[m])}</td></tr>" for m in reversed(meses)
    )
    return (
        f'<article class="ad-card"><div class="ad-card__head"><h2 class="ad-card__title">{html.escape(titulo)}</h2>'
        f'<span class="ad-chip">{html.escape(recorte)}</span></div>'
        f'<p class="ad-card__value">{_valor_destaque(atual)}</p>'
        f'<p class="ad-calc">{conta}<span class="ad-calc__terms">{termos}</span></p>'
        f'<p class="ad-delta">{_variacao(atual, anterior)}</p>'
        f"{tendencia_mensal(pontos, rotulo)}"
        f'<details class="ad-series"><summary>Série completa ({len(meses)} meses)</summary>'
        f"<table><tbody>{serie}</tbody></table></details></article>"
    )


def cartoes(linhas: list[Indicador]) -> list[str]:
    """Um cartão por (indicador, recorte), na ordem do catálogo e depois pelo recorte."""
    prontos = []
    for nome, titulo, _ in INDICADORES:
        recortes: dict[str, dict[str, Indicador]] = {}
        for ind in linhas:
            if ind.indicador == nome:
                recorte = " · ".join(p for p in (ind.submercado, ind.fonte) if p) or "Brasil"
                recortes.setdefault(recorte, {})[ind.periodo_apuracao] = ind
        prontos += [_cartao(titulo, r, por_mes) for r, por_mes in sorted(recortes.items())]
    return prontos


def referencia(linhas: list[Indicador]) -> str:
    """Último mês calculado entre todos os indicadores."""
    return mes(max(ind.periodo_apuracao for ind in linhas)) if linhas else "—"


def banda(total: int, referencia_texto: str) -> str:
    return (
        '<section class="ad-band ad-band--centered" aria-label="Resumo"><div class="ad-summary">'
        f'<p class="ad-summary__num">{total}</p><div class="ad-summary__text">'
        f'<h2 class="ad-summary__title">indicadores · referência {html.escape(referencia_texto)}</h2>'
        '<p class="ad-summary__sub">Razões técnicas do setor, por submercado e fonte. Sem meta: a variação é '
        "informativa, não boa nem ruim.</p></div></div></section>"
    )


def paginas_do_telao(total: int) -> int:
    return max(1, -(-total // POR_PAGINA_NO_TELAO))


def corpo(prontos: list[str], *, pagina: int | None = None) -> str:
    """Os cartões. No telão só uma página de cada vez, para nenhum ficar escondido por rolagem."""
    if not prontos:
        return '<p class="ad-premissa">Nenhum indicador calculado ainda.</p>'
    visiveis = prontos
    if pagina is not None:
        inicio = (pagina - 1) * POR_PAGINA_NO_TELAO
        visiveis = prontos[inicio : inicio + POR_PAGINA_NO_TELAO]
    return (
        f'<div class="ad-cards">{"".join(visiveis)}</div>'
        '<p class="ad-foot">Calculado em <code>gold.indicadores_mensais</code>. Sem meta nem comparação entre '
        "coligadas: indicador de negócio é da Fase 2 (ADR 012).</p>"
    )
