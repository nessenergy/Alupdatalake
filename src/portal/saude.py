"""Tela de saúde do lake: um veredito, os grupos de origem e uma linha por fonte.

A regra de estado mora no Gold (`gold.saude_ingestao`, ADR 006); aqui só se traduz
o que ele diz para o que a Alup lê — sem texto técnico de erro e sem lista de
fontes escrita na tela. O grupo vem do prefixo do conector.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.portal.formato import duracao, milhar, pct
from src.portal.pagina import glifo, icone

if TYPE_CHECKING:
    from src.portal.dados import SaudeConector, SerieVolumetria

DIAS_DA_TIRA = 30

# Prefixo do conector → nome da origem, na ordem em que os grupos aparecem.
# Prefixo fora desta lista cai em "Outras", que vai sempre por último.
ORIGENS = {
    "ons": "ONS",
    "ccee": "CCEE",
    "aneel": "ANEEL",
    "bcb": "BCB",
    "ibge": "IBGE",
    "tempook": "TempoOK",
}
OUTRAS = "Outras"

# A situação do Gold, em linguagem de estado do Portal. Atraso e falha recente
# pedem atenção; fonte que nunca carregou (e não espera credencial) é crítica.
ESTADO_DA_SITUACAO = {"OK": "ok", "ATRASADA": "warn", "FALHA_RECENTE": "warn", "SEM_SUCESSO": "crit"}
ROTULO_DO_ESTADO = {"ok": "em dia", "warn": "pede atenção", "crit": "crítica", "idle": "aguardando credencial"}

# Gravidade para o grupo: o pior estado de uma fonte vira o do grupo.
_GRAVIDADE = {"ok": 0, "warn": 1, "crit": 2}


@dataclass(frozen=True)
class Fonte:
    conector: str
    nome: str
    grupo: str
    estado: str  # ok | warn | crit | idle
    frase: str
    idade: str
    tira: list[str]  # "c" carregou · "n" sem carga · "f" falha, do dia mais antigo ao de hoje
    linhas_total: int
    sucesso: str


def grupo_de(conector: str) -> str:
    return ORIGENS.get(conector.partition("_")[0], OUTRAS)


def _nome(conector: str, grupo: str) -> str:
    """Nome legível: sem o prefixo do grupo (já está no título dele) e sem sublinhado."""
    if grupo == OUTRAS:
        return conector.replace("_", " ")
    return conector.partition("_")[2].replace("_", " ") or conector


def _tira(serie: SerieVolumetria | None) -> list[str]:
    """Um sinal por dia. Falha só conta se o dia não carregou nada: uma nova tentativa
    que deu certo no mesmo dia entregou o dado, e a tira mostra isso."""
    if serie is None:
        return ["n"] * DIAS_DA_TIRA
    falhas = serie.falhas or [0] * len(serie.linhas)
    dias = [
        "c" if linhas > 0 else "f" if erros > 0 else "n" for linhas, erros in zip(serie.linhas, falhas, strict=False)
    ]
    return (["n"] * DIAS_DA_TIRA + dias)[-DIAS_DA_TIRA:]


def _frase(conector: SaudeConector, estado: str) -> str:
    if estado == "idle":
        return "aguardando credencial"
    if conector.situacao == "ATRASADA":
        return f"sem carga {duracao(conector.minutos_desde_sucesso)}"
    if conector.situacao == "FALHA_RECENTE":
        return "a última execução falhou"
    if conector.situacao == "SEM_SUCESSO":
        return "ainda não carregou"
    return ""


def _sucesso(conector: SaudeConector) -> str:
    if not conector.execucoes_30d or conector.taxa_sucesso_30d is None:
        return pct(conector.taxa_sucesso_30d, 0)
    certas = round(conector.taxa_sucesso_30d * conector.execucoes_30d)
    return f"{pct(conector.taxa_sucesso_30d, 0)} · {certas} de {conector.execucoes_30d} execuções"


def montar(conectores: list[SaudeConector], series: list[SerieVolumetria]) -> list[Fonte]:
    por_conector = {s.conector: s for s in series}
    fontes = []
    for c in sorted(conectores, key=lambda c: c.conector):
        estado = "idle" if c.aguardando_credencial else ESTADO_DA_SITUACAO.get(c.situacao, "warn")
        grupo = grupo_de(c.conector)
        fontes.append(
            Fonte(
                conector=c.conector,
                nome=_nome(c.conector, grupo),
                grupo=grupo,
                estado=estado,
                frase=_frase(c, estado),
                idade="—" if estado == "idle" else duracao(c.minutos_desde_sucesso),
                tira=_tira(por_conector.get(c.conector)),
                linhas_total=c.linhas_carregadas_total,
                sucesso=_sucesso(c),
            )
        )
    return fontes


def _grupos(fontes: list[Fonte]) -> list[tuple[str, list[Fonte]]]:
    ordem = [*ORIGENS.values(), OUTRAS]
    achados: dict[str, list[Fonte]] = {}
    for f in fontes:
        achados.setdefault(f.grupo, []).append(f)
    return [(g, achados[g]) for g in ordem if g in achados]


def _contagem(fontes: list[Fonte], estado: str) -> int:
    return sum(1 for f in fontes if f.estado == estado)


def _plural(n: int, singular: str, plural: str) -> str:
    return f"{n} {singular if n == 1 else plural}"


def _lampadas() -> str:
    return "".join(f'<span class="ad-lamp ad-lamp--{e}">{glifo(e)}</span>' for e in ("crit", "warn", "ok"))


def veredito(fontes: list[Fonte]) -> str:
    """O semáforo e a frase que ocupam a faixa. Fonte aguardando credencial não pesa."""
    if not fontes:
        return (
            '<div class="ad-verdict" role="status"><div class="ad-lamps" aria-hidden="true">'
            f'{_lampadas()}</div><div><h2 class="ad-verdict__title">Nenhuma fonte executou ainda</h2></div></div>'
        )
    criticas = _contagem(fontes, "crit")
    atencao = _contagem(fontes, "warn") + criticas
    esperando = _contagem(fontes, "idle")
    estado = "crit" if criticas else "warn" if atencao else "ok"
    titulo = "Tudo em dia" if estado == "ok" else f"{_plural(atencao, 'fonte pede', 'fontes pedem')} atenção"
    apoio = f"{_contagem(fontes, 'ok')} de {len(fontes)} em dia"
    if esperando:
        apoio += " · " + _plural(esperando, "aguardando credencial", "aguardando credencial")
    return (
        f'<div class="ad-verdict ad-verdict--{estado}" role="status">'
        f'<div class="ad-lamps" aria-hidden="true">{_lampadas()}</div>'
        f'<div><h2 class="ad-verdict__title">{titulo}</h2><p class="ad-verdict__sub">{apoio}</p></div></div>'
    )


def _pilula(estado: str, texto: str) -> str:
    return f'<span class="ad-pill ad-pill--{estado}">{icone(estado, "")}{html.escape(texto)}</span>'


def _contador(grupo: str, fontes: list[Fonte]) -> str:
    pior = max((f.estado for f in fontes if f.estado in _GRAVIDADE), key=_GRAVIDADE.__getitem__, default="ok")
    avisos = _contagem(fontes, "warn")
    criticas = _contagem(fontes, "crit")
    pilulas = ""
    if avisos:
        pilulas += _pilula("warn", f"{_plural(avisos, 'pede', 'pedem')} atenção")
    if criticas:
        pilulas += _pilula("crit", _plural(criticas, "crítica", "críticas"))
    if _contagem(fontes, "idle"):
        pilulas += _pilula("idle", "aguardando credencial")
    classe = f" ad-tile--{pior}" if pior != "ok" else ""
    return (
        f'<li class="ad-tile{classe}"><h3 class="ad-tile__name">{html.escape(grupo)}'
        f"{icone(pior, ROTULO_DO_ESTADO[pior])}</h3>{pilulas}</li>"
    )


def banda(fontes: list[Fonte]) -> str:
    contadores = "".join(_contador(g, fs) for g, fs in _grupos(fontes))
    return (
        f'<section class="ad-band" aria-label="Veredito">{veredito(fontes)}'
        f'<ul class="ad-tiles" aria-label="Grupos de origem">{contadores}</ul></section>'
    )


def _tira_html(fonte: Fonte) -> str:
    classe = {"n": ' class="n"', "f": ' class="f"', "c": ""}
    celulas = "".join(f"<i{classe[t]}></i>" for t in fonte.tira)
    texto = (
        f"Últimos 30 dias: {fonte.tira.count('c')} com carga, "
        f"{fonte.tira.count('n')} sem carga, {fonte.tira.count('f')} com falha"
    )
    return f'<span class="ad-strip" role="img" aria-label="{texto}">{celulas}</span>'


def _linha(f: Fonte) -> str:
    nota = f'<span class="ad-row__note">{html.escape(f.frase)}</span>' if f.frase and f.estado != "idle" else ""
    meio = '<span class="ad-pending">aguardando credencial</span>' if f.estado == "idle" else _tira_html(f)
    return (
        f'<details class="ad-row ad-row--{f.estado}"><summary>{icone(f.estado, ROTULO_DO_ESTADO[f.estado])}'
        f'<span class="ad-row__name" title="{html.escape(f.conector)}">{html.escape(f.nome)}{nota}</span>'
        f'<span class="ad-row__age">{html.escape(f.idade)}</span>{meio}<span class="ad-chev"></span></summary>'
        f'<dl class="ad-evid"><div><dt>Linhas carregadas no total</dt><dd>{milhar(f.linhas_total)}</dd></div>'
        f"<div><dt>Sucesso em 30 dias</dt><dd>{html.escape(f.sucesso)}</dd></div></dl></details>"
    )


def _legenda() -> str:
    def item(celula: str, texto: str) -> str:
        return f'<span class="ad-legend__item"><span class="ad-strip">{celula}</span>{texto}</span>'

    return (
        '<p class="ad-legend"><span>Últimos 30 dias, hoje à direita:</span>'
        + item("<i></i>", "carregou")
        + item('<i class="n"></i>', "sem carga")
        + item('<i class="f"></i>', "execução com falha")
        + "</p>"
    )


def corpo(fontes: list[Fonte], *, telao: bool = False) -> str:
    """A lista agrupada. No telão, muita fonte vai para três colunas, para caber sem rolar."""
    secoes = "".join(
        f'<section class="ad-group" aria-label="{html.escape(g)}"><div class="ad-group__head">'
        f"<h2>{html.escape(g)}</h2></div>{''.join(_linha(f) for f in fs)}</section>"
        for g, fs in _grupos(fontes)
    )
    densa = " ad-sources--densa" if telao and len(fontes) > 26 else ""
    return (
        f'<div class="ad-sources{densa}">{secoes}</div>{_legenda()}'
        '<p class="ad-foot">O atraso de cada fonte é medido contra o limite de silêncio dela, o mesmo do alerta, '
        "e não contra um limite fixo. Detalhe de cada fonte: clique na linha.</p>"
    )
