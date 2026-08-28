"""Gráficos do painel: SVG gerado no servidor, sem biblioteca e sem JavaScript.

Cinco séries pequenas de 30 pontos não justificam trazer uma biblioteca de
charts, um bundler e um build para dentro do Portal. O SVG sai pronto do
servidor e é acessível: cada ponto carrega `<title>`, que o navegador mostra no
hover e o leitor de tela anuncia, e a página oferece a tabela completa.

Paleta validada em `scripts/validate_palette.js` do skill dataviz — os seis
checks passam (banda de luminosidade, croma, separação para daltonismo,
piso de visão normal e contraste com a superfície).
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.portal.custo import CustoDia
    from src.portal.dados import SerieVolumetria

# Ordem fixa: a cor segue o conector, nunca a posição na lista. Filtrar não
# repinta quem sobrou.
CORES = ("#8B2A78", "#1863dc", "#0E8A6B", "#B26A00", "#C2185B")

LARGURA = 260
ALTURA = 64
MARGEM = 3


def cor_do_conector(conector: str, ordem: list[str]) -> str:
    """Cor fixa por conector, atribuída na ordem alfabética estável."""
    return CORES[ordem.index(conector) % len(CORES)]


def _milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def area(serie: SerieVolumetria, cor: str) -> str:
    """Área de 30 dias. Baseline em zero — área nunca tem eixo truncado."""
    if not serie.linhas:
        return f'<svg viewBox="0 0 {LARGURA} {ALTURA}" class="grafico" role="img"></svg>'

    teto = max(serie.linhas) or 1
    passo = LARGURA / max(len(serie.linhas) - 1, 1)
    altura_util = ALTURA - 2 * MARGEM

    pontos = [(i * passo, ALTURA - MARGEM - (valor / teto) * altura_util) for i, valor in enumerate(serie.linhas)]
    linha = " ".join(f"{x:.1f},{y:.1f}" for x, y in pontos)
    area_fechada = f"{pontos[0][0]:.1f},{ALTURA} {linha} {pontos[-1][0]:.1f},{ALTURA}"

    # Alvo de hover maior que a marca: uma faixa por dia, invisível.
    faixas = "".join(
        f'<rect x="{x - passo / 2:.1f}" y="0" width="{passo:.1f}" height="{ALTURA}" fill="transparent">'
        f"<title>{serie.dias[i].strftime('%d/%m')} · {_milhar(serie.linhas[i])} linhas</title></rect>"
        for i, (x, _) in enumerate(pontos)
    )

    rotulo = f"{serie.conector}: {_milhar(serie.total)} linhas em {len(serie.linhas)} dias"
    return (
        f'<svg viewBox="0 0 {LARGURA} {ALTURA}" class="grafico" role="img" '
        f'aria-label="{html.escape(rotulo)}" preserveAspectRatio="none">'
        f'<polygon points="{area_fechada}" fill="{cor}" opacity=".14"/>'
        f'<polyline points="{linha}" fill="none" stroke="{cor}" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round" vector-effect="non-scaling-stroke"/>'
        f"{faixas}</svg>"
    )


def tabela(series: list[SerieVolumetria]) -> str:
    """Mesma informação em texto — exigência de acessibilidade do gráfico."""
    if not series:
        return ""
    dias = series[0].dias
    cabecalho = "".join(f"<th>{dia.strftime('%d/%m')}</th>" for dia in dias)
    corpo = "".join(
        f'<tr><th scope="row">{html.escape(s.conector)}</th>'
        + "".join(f"<td>{_milhar(v)}</td>" for v in s.linhas)
        + f"<td class='total'>{_milhar(s.total)}</td></tr>"
        for s in series
    )
    return (
        "<details class='tabela'><summary>Ver os números em tabela</summary>"
        f"<div class='rolagem'><table><thead><tr><th>Conector</th>{cabecalho}<th>Total</th></tr></thead>"
        f"<tbody>{corpo}</tbody></table></div></details>"
    )


# Composição do gasto: cor por natureza de custo, não por fonte. São escalas
# diferentes e não podem compartilhar paleta com as séries de volumetria.
CORES_CUSTO = {
    "query": ("#1863dc", "Consulta"),
    "armazenamento": ("#0E8A6B", "Armazenamento"),
    "compute": ("#B26A00", "Compute"),
}

LARGURA_BARRAS = 720
ALTURA_BARRAS = 132


def usd(valor: object) -> str:
    """Dólar no formato brasileiro, com casas suficientes para o valor não sumir.

    Duas casas escondem a conta de um lake pequeno: quase tudo vira US$ 0,00 e
    a tela passa a impressão de que não há o que olhar.
    """
    numero = float(valor)
    casas = 2 if abs(numero) >= 1 else 4
    return f"US$ {numero:,.{casas}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def barras_custo(dias: list[CustoDia]) -> str:
    """Barras empilhadas por dia: quanto se gastou e em quê.

    Empilhada porque a pergunta é de composição — "o que puxou a conta hoje" —
    e não de comparação entre séries. Baseline em zero, como toda barra.
    """
    if not dias:
        return ""

    teto = max((float(d.total_usd) for d in dias), default=0.0) or 1.0
    largura_barra = LARGURA_BARRAS / len(dias)
    util = ALTURA_BARRAS - 4

    barras = []
    for i, dia in enumerate(dias):
        x = i * largura_barra
        y = float(ALTURA_BARRAS)
        pedacos = []
        for chave in ("query", "armazenamento", "compute"):
            valor = float(getattr(dia, f"{chave}_usd"))
            if valor <= 0:
                continue
            altura = valor / teto * util
            y -= altura
            cor, _ = CORES_CUSTO[chave]
            pedacos.append(
                f'<rect x="{x + largura_barra * 0.15:.1f}" y="{y:.1f}" '
                f'width="{largura_barra * 0.7:.1f}" height="{altura:.1f}" fill="{cor}"/>'
            )
        rotulo = (
            f"{dia.dia.strftime('%d/%m')} · {usd(dia.total_usd)} "
            f"(consulta {usd(dia.query_usd)}, armazenamento {usd(dia.armazenamento_usd)})"
        )
        barras.append(
            "".join(pedacos) + f'<rect x="{x:.1f}" y="0" width="{largura_barra:.1f}" height="{ALTURA_BARRAS}" '
            f'fill="transparent"><title>{html.escape(rotulo)}</title></rect>'
        )

    legenda = " · ".join(f"{nome}" for _, (_, nome) in CORES_CUSTO.items())
    return (
        f'<svg viewBox="0 0 {LARGURA_BARRAS} {ALTURA_BARRAS}" class="grafico grafico-alto" role="img" '
        f'aria-label="Custo diário empilhado por natureza: {html.escape(legenda)}. '
        f'Maior dia: {html.escape(usd(teto))}." preserveAspectRatio="none">' + "".join(barras) + "</svg>"
    )


def legenda_custo() -> str:
    """Legenda da composição — a cor precisa dizer o que significa."""
    itens = "".join(
        f'<li><span class="chave" style="background:{cor}"></span>{nome}</li>' for _, (cor, nome) in CORES_CUSTO.items()
    )
    return f'<ul class="legenda">{itens}</ul>'
