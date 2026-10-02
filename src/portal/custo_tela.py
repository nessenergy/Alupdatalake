"""Tela de custo de nuvem: a mesma conta lida de três jeitos, nesta ordem.

Operacional (o que mudo hoje), orçamento (estamos dentro do previsto) e diretoria
(vale o que custa) — §5-A do plano de FinOps. Só entra o que o modelo
(`src/portal/custo.py`) calcula: sem previsto por categoria e sem histórico de
meses, que o Portal ainda não tem. Enquadramento em `docs/arquitetura/portal-finops.md`.
"""

from __future__ import annotations

import html
from decimal import Decimal
from typing import TYPE_CHECKING

from src.portal.formato import bytes_humano, milhar, pct
from src.portal.grafico import barras_custo, legenda_custo, usd
from src.portal.pagina import icone

if TYPE_CHECKING:
    from src.portal.custo import ConsultaCara, PainelCusto

MESES_POR_EXTENSO = (
    "janeiro",
    "fevereiro",
    "março",
    "abril",
    "maio",
    "junho",
    "julho",
    "agosto",
    "setembro",
    "outubro",
    "novembro",
    "dezembro",
)
# Barra cheia de cada medidor = 112% do previsto; o traço marca os 100%.
TETO_DO_MEDIDOR = 1.12
# No telão cada lista mostra o topo: nada de rolagem, e o resto está na tela normal.
LINHAS_NO_TELAO = 4
# Na tela normal, "as mais caras" é o topo, não a lista inteira.
LINHAS_NA_TELA = 10


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def banda(dados: PainelCusto) -> str:
    o = dados.orcamento
    anomalas = [c for c in dados.consultas if c.anomala]
    pilulas = ""
    if anomalas:
        pilulas += (
            f'<span class="ad-pill ad-pill--warn" role="status">{icone("warn", "")}'
            f"{_plural(len(anomalas), 'consulta pede', 'consultas pedem')} atenção</span>"
        )
    if o.estoura:
        pilulas += (
            f'<span class="ad-pill ad-pill--warn" role="status">{icone("warn", "")}'
            f"a projeção passa o orçado em {usd(o.projetado_usd - o.orcado_usd)}</span>"
        )
    return (
        '<section class="ad-band ad-band--centered" aria-label="Resumo do mês"><div class="ad-summary">'
        f'<p class="ad-summary__num"><small>US$</small>{usd(o.realizado_usd).removeprefix("US$ ")}</p>'
        '<div class="ad-summary__text">'
        f'<h2 class="ad-summary__title">gastos em {MESES_POR_EXTENSO[o.mes.month - 1]} de {o.mes.year}</h2>'
        f'<p class="ad-summary__sub">{pct(o.consumo_pct, 0)} do orçado ({usd(o.orcado_usd)}) · '
        f"dia {o.dias_decorridos} de {o.dias_do_mes}</p></div>{pilulas}</div></section>"
    )


def _linha_consulta(c: ConsultaCara) -> str:
    estado = "warn" if c.anomala else "ok"
    nota = (
        f'<span class="ad-qrow__note">custo {pct(c.variacao_vs_media, 0)} acima da própria média</span>'
        if c.anomala
        else ""
    )
    return (
        f'<li class="ad-qrow ad-qrow--{estado}">{icone(estado, "pede atenção" if c.anomala else "dentro da média")}'
        f'<span class="ad-qrow__name">{html.escape(c.rotulo)}{nota}</span>'
        f'<span class="ad-qrow__meta">{milhar(c.execucoes)} exec. · {bytes_humano(c.bytes_varridos)}</span>'
        f'<span class="ad-qrow__cost">{usd(c.custo_usd)}</span></li>'
    )


def _operacional(dados: PainelCusto, *, telao: bool) -> str:
    consultas = dados.consultas[: LINHAS_NO_TELAO if telao else LINHAS_NA_TELA]
    anomalas = [c for c in dados.consultas if c.anomala]
    linhas_consulta = "".join(_linha_consulta(c) for c in consultas)
    por_fonte = sorted(dados.fontes, key=lambda f: f.total_usd, reverse=True)
    por_fonte = por_fonte[:LINHAS_NO_TELAO] if telao else por_fonte
    linhas_fonte = "".join(
        f'<li class="ad-qrow ad-qrow--ok">{icone("ok", "")}<span class="ad-qrow__name">{html.escape(f.fonte)}</span>'
        f'<span class="ad-qrow__meta">'
        f"{'—' if f.usd_por_milhao_de_linhas is None else usd(f.usd_por_milhao_de_linhas) + ' por milhão de linhas'}"
        f'</span><span class="ad-qrow__cost">{usd(f.total_usd)}</span></li>'
        for f in por_fonte
    )
    varredura = (
        f'<p class="ad-stat"><b>{_plural(len(anomalas), "consulta", "consultas")}</b>'
        f"<span>varrendo mais que o dobro da própria média · {bytes_humano(sum(c.bytes_varridos for c in anomalas))} · "
        f"{usd(sum((c.custo_usd for c in anomalas), Decimal(0)))} em 30 dias</span></p>"
        if anomalas
        else '<p class="ad-stat"><span>Nenhuma consulta destoando da própria média.</span></p>'
    )
    return (
        '<section class="ad-block" aria-labelledby="op"><p class="ad-block__eyebrow">1 · Operacional</p>'
        '<h2 class="ad-block__title" id="op">O que mudar hoje</h2>'
        f'<h3>Consultas mais caras · 30 dias</h3><ul class="ad-qlist">{linhas_consulta}</ul>'
        f"<h3>Fora do padrão</h3>{varredura}"
        f'<h3>Fontes que mais custam</h3><ul class="ad-qlist">{linhas_fonte}</ul></section>'
    )


def _medidor(consumo: float, rotulo: str) -> str:
    largura = min(consumo, TETO_DO_MEDIDOR) / TETO_DO_MEDIDOR * 100
    marca = 1 / TETO_DO_MEDIDOR * 100
    return (
        f'<div class="ad-meter" role="img" aria-label="{html.escape(rotulo)}">'
        f'<span style="width:{largura:.1f}%"></span><i style="left:{marca:.1f}%"></i></div>'
    )


def _orcamento(dados: PainelCusto) -> str:
    o = dados.orcamento
    dia = f"{o.dias_decorridos} de {o.dias_do_mes} dias"
    return (
        '<section class="ad-block" aria-labelledby="orc"><p class="ad-block__eyebrow">2 · Orçamento</p>'
        '<h2 class="ad-block__title" id="orc">Gasto vs. orçado</h2>'
        f'<dl class="ad-budget"><dt>Realizado no mês</dt><dd><b>{usd(o.realizado_usd)}</b> de {usd(o.orcado_usd)}</dd>'
        f"{_medidor(o.consumo_pct, f'{pct(o.consumo_pct, 0)} do orçado, {dia}')}"
        f"<dt>Projeção de fechamento</dt><dd><b>{usd(o.projetado_usd)}</b> · {pct(o.projecao_pct, 0)} do orçado</dd>"
        f"{_medidor(o.projecao_pct, f'projeção de {pct(o.projecao_pct, 0)} do orçado')}</dl>"
        f"<h3>Gasto por dia · composição · 30 dias</h3>{barras_custo(dados.dias)}{legenda_custo()}</section>"
    )


def _diretoria(dados: PainelCusto, *, telao: bool) -> str:
    dominios = dados.por_dominio
    total = sum((valor for _, valor in dominios), Decimal(0)) or Decimal(1)
    maior = dominios[0][0] if dominios else "—"
    exibidos = dominios[:LINHAS_NO_TELAO] if telao else dominios
    linhas = "".join(
        f'<li class="ad-qrow ad-qrow--ok">{icone("ok", "")}<span class="ad-qrow__name">{html.escape(nome)}</span>'
        f'<span class="ad-qrow__meta">{pct(float(valor / total), 0)}</span>'
        f'<span class="ad-qrow__cost">{usd(valor)}</span></li>'
        for nome, valor in exibidos
    )
    return (
        '<section class="ad-block" aria-labelledby="dir"><p class="ad-block__eyebrow">3 · Diretoria</p>'
        '<h2 class="ad-block__title" id="dir">Numa olhada</h2>'
        '<dl class="ad-glance">'
        f"<div><dt>Custo mensal projetado</dt><dd>{usd(dados.orcamento.projetado_usd)}</dd></div>"
        f"<div><dt>Gasto em 30 dias</dt><dd>{usd(dados.total_usd)}</dd></div>"
        f"<div><dt>Maior domínio</dt><dd>{html.escape(maior)}</dd></div>"
        f"<div><dt>Fontes em produção</dt><dd>{len(dados.fontes)}</dd></div></dl>"
        f'<h3>Por domínio de negócio · 30 dias</h3><ul class="ad-qlist">{linhas}</ul></section>'
    )


def corpo(dados: PainelCusto, *, telao: bool = False) -> str:
    blocos = (
        f'<div class="ad-cost">{_operacional(dados, telao=telao)}{_orcamento(dados)}'
        f"{_diretoria(dados, telao=telao)}</div>"
    )
    if telao:
        premissa = (
            '<p class="ad-foot"><strong>Premissas.</strong> Valores em US$ pela tarifa declarada em '
            "<code>src/portal/custo.py</code>, sem crédito, desconto nem camada gratuita: o lake cabe no 1 TB de "
            "consulta grátis por mês, então a conta real tende a ser menor. Barra cheia = 112% do orçado; o traço "
            "marca 100%.</p>"
        )
        return blocos + premissa
    return blocos + (
        '<p class="ad-foot"><strong>Premissas.</strong> Os valores usam a tarifa por byte varrido e por GiB '
        "armazenado declaradas em <code>src/portal/custo.py</code>, e não enxergam crédito nem desconto por uso "
        "comprometido: isso só chega com o billing export (camada F2 do plano). <strong>Nem a camada "
        "gratuita:</strong> o BigQuery dá 1 TB de consulta por mês sem cobrar, e o lake inteiro cabe nesse teto "
        "hoje, de modo que a linha de consulta da fatura real tende a ser zero e o número aqui superestima de "
        "propósito. Compute aparece no agregado e não por fonte: existe um Cloud Run Job para todas elas. "
        "&quot;Pede atenção&quot; = consulta com custo mais que o dobro da própria média. Barra cheia de cada "
        "medidor = 112% do orçado; o traço marca 100%. Plano em <code>docs/arquitetura/portal-finops.md</code>.</p>"
    )
