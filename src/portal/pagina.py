"""Casca comum das telas do Portal: faixa de topo, navegação, rodapé e modo telão.

Cada tela entrega só a faixa (`banda`) e o corpo; a moldura é uma só, para que o
cabeçalho, a navegação e o rodapé não divirjam entre as quatro rotas.

O modo telão (`?telao=1`) passa as telas sozinhas, sem JavaScript: cada página
traz um `<meta http-equiv="refresh">` para a próxima. O Portal continua sem uma
linha de script (política de segurança em `app.py`).
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from src.portal.estilo import ESTILO
from src.portal.marca import LOGO_ALUP

# Brasília não tem horário de verão desde 2019: deslocamento fixo dispensa o banco de fusos.
BRASILIA = timezone(timedelta(hours=-3), "BRT")
SEGUNDOS_POR_TELA = 20

ROTAS = (
    ("/", "Dado de negócio"),
    ("/indicadores", "Indicadores"),
    ("/lake", "Saúde do lake"),
    ("/custo", "Custo de nuvem"),
)

FONTES = (
    "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700"
    "&family=Zilla+Slab:wght@500;600;700&display=swap"
)

_GLIFOS = {
    "ok": '<path d="M20 6 9 17l-5-5"/>',
    "warn": '<path d="M12 6v7"/><path d="M12 18h.01"/>',
    "crit": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "idle": '<path d="M12 6v6l4 2"/>',
}
_ATRIBUTOS_SVG = 'viewBox="0 0 24 24" fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"'


def glifo(estado: str) -> str:
    """O traço do estado (✓ ! × relógio). A cor vem do CSS, não do markup."""
    return f'<svg {_ATRIBUTOS_SVG} aria-hidden="true">{_GLIFOS[estado]}</svg>'


def icone(estado: str, rotulo: str) -> str:
    """Disco de estado com glifo: cor nunca é o único sinal."""
    return f'<span class="ad-ico ad-ico--{estado}" role="img" aria-label="{html.escape(rotulo)}">{glifo(estado)}</span>'


@dataclass(frozen=True)
class Telao:
    """Onde o rodízio está e para onde vai."""

    rotulo: str
    proxima: str


def proxima_do_telao(rota: str, pagina: int = 1, paginas: int = 1) -> str:
    """Próximo endereço do rodízio: Indicadores (todas as páginas) → Saúde → Custo → volta."""
    if rota == "/indicadores":
        if pagina < paginas:
            return f"/indicadores?telao=1&p={pagina + 1}"
        return "/lake?telao=1"
    if rota == "/lake":
        return "/custo?telao=1"
    return "/indicadores?telao=1"


def _carimbo(agora: datetime | None) -> str:
    instante = (agora or datetime.now(UTC)).astimezone(BRASILIA)
    return (
        f'<p class="ad-stamp">consultado às <time datetime="{instante.isoformat(timespec="minutes")}">'
        f"{instante:%H:%M}</time> (Brasília)</p>"
    )


def _navegacao(atual: str) -> str:
    itens = "".join(
        f'<a href="{rota}"' + (' aria-current="page"' if rota == atual else "") + f">{html.escape(nome)}</a>"
        for rota, nome in ROTAS
    )
    return f'<nav class="ad-nav" aria-label="Portal AlupData">{itens}</nav>'


def pagina(
    *,
    titulo: str,
    rota: str,
    usuario: str,
    banda: str,
    corpo: str,
    aviso: str = "",
    telao: Telao | None = None,
    agora: datetime | None = None,
) -> str:
    """Documento completo. `banda` e `corpo` já chegam como HTML escapado."""
    if telao:
        refresh = f'<meta http-equiv="refresh" content="{SEGUNDOS_POR_TELA};url={html.escape(telao.proxima)}">'
        modo = (
            f'<p class="ad-telao">Modo telão · {html.escape(telao.rotulo)} · troca a cada {SEGUNDOS_POR_TELA} s '
            f'<a href="{rota}">sair do modo telão</a></p>'
        )
        classe = "ad-page ad-page--telao"
    else:
        refresh = ""
        modo = f'<a class="ad-telao-link" href="{rota}?telao=1">modo telão</a>' if rota != "/" else ""
        classe = "ad-page"
    nota = f'<p class="ad-notice">{aviso}</p>' if aviso else ""
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
{refresh}<title>{html.escape(titulo)} · AlupData</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTES}">
{ESTILO}</head>
<body class="{classe}">
<header class="ad-head"><div class="ad-head__bar">{LOGO_ALUP}<span class="ad-divider"></span>
<p class="ad-title"><b>AlupData</b> · {html.escape(titulo)}</p>
<div class="ad-head__meta">{modo}{_carimbo(agora)}</div></div>
{_navegacao(rota)}</header>
{banda}
<main class="ad-main">{nota}{corpo}
<p class="ad-foot ad-quem">Conectado como {html.escape(usuario)}</p></main>
</body></html>"""
