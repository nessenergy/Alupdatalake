"""Gráficos do portal: SVG gerado no servidor, sem biblioteca e sem JavaScript.

A tendência mensal dos indicadores e as barras de custo são pequenas demais para
justificar uma biblioteca de charts, um bundler e um build dentro do Portal. O SVG
sai pronto do servidor e é acessível: cada gráfico traz `aria-label` em texto, e as
barras de custo carregam `<title>` por dia, que o leitor de tela anuncia.
"""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.portal.custo import CustoDia


def _milhar(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def tendencia_mensal(pontos: list[tuple[str, float]], rotulo: str) -> str:
    """Linha mensal de uma razão, no desenho do cartão: (rótulo do mês, valor).

    Razão não tem baseline em zero que faça sentido: a escala vai do menor ao maior
    valor da série. O último ponto é marcado, porque é o número em destaque no
    cartão, e os meses das pontas ficam escritos para a linha não flutuar sem tempo.
    """
    if not pontos:
        return ""
    valores = [v for _, v in pontos]
    piso, teto = min(valores), max(valores)
    amplitude = teto - piso
    passo = 240 / max(len(pontos) - 1, 1)
    xy = [
        (i * passo if len(pontos) > 1 else 120.0, 25.0 if not amplitude else 46 - (v - piso) / amplitude * 42)
        for i, v in enumerate(valores)
    ]
    linha = " ".join(f"{x:.1f},{y:.1f}" for x, y in xy)
    x_fim, y_fim = xy[-1]
    return (
        f'<svg class="ad-spark" viewBox="0 0 240 64" role="img" aria-label="{html.escape(rotulo)}">'
        f'<polyline points="{linha}"/><circle cx="{x_fim:.1f}" cy="{y_fim:.1f}" r="4"/>'
        f'<text x="0" y="63">{html.escape(pontos[0][0])}</text>'
        f'<text x="240" y="63" text-anchor="end">{html.escape(pontos[-1][0])}</text></svg>'
    )


# Composição do gasto: cor por natureza de custo, não por fonte. São escalas
# diferentes e não podem compartilhar paleta com as séries de volumetria.
CORES_CUSTO = {
    "query": ("#1863dc", "Consulta"),
    "armazenamento": ("#8B2A78", "Armazenamento"),
    "compute": ("#6b6675", "Compute"),
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
