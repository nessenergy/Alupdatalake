"""Portal MVP — item 0.15 do plano. Escopo cravado na ADR 005.

Uma tela: uma view Gold e quando o lake foi alimentado pela última vez. Não é
ferramenta de BI, e a ADR 005 lista o que deliberadamente não faz.

Autenticação não é escrita aqui. No Cloud Run o acesso é restrito por IAM /
IAP, e a identidade chega no cabeçalho `X-Goog-Authenticated-User-Email` — a
plataforma faz isso melhor do que qualquer login que escrevêssemos em 8h, e
sem guardar senha nenhuma.

    uv run flask --app src.portal.app run    # local, provedor simulado
"""

from __future__ import annotations

import html
from datetime import datetime
from typing import Any

from flask import Flask, Response, request
from src.core.config import get_settings
from src.portal.dados import Painel, SaudeConector, obter_provedor

app = Flask(__name__)

CABECALHO_IDENTIDADE = "X-Goog-Authenticated-User-Email"


@app.get("/")
def painel() -> Response:
    cfg = get_settings()
    dados = obter_provedor().painel(cfg.portal_view)
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(_pagina(dados, usuario, simulado=cfg.portal_provedor != "bigquery"), mimetype="text/html")


@app.get("/lake")
def lake() -> Response:
    """Painel de saúde do DataLake — monitoramento, não relatório de negócio.

    Escopo em `docs/arquitetura/decisoes/006-painel-de-saude.md`.
    """
    cfg = get_settings()
    conectores = obter_provedor().saude()
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(
        _pagina_lake(conectores, usuario, simulado=cfg.portal_provedor != "bigquery"),
        mimetype="text/html",
    )


@app.get("/saude")
def saude() -> dict[str, str]:
    """Sonda do Cloud Run: responde sem tocar no BigQuery."""
    return {"status": "ok"}


def _usuario(cabecalho: str | None) -> str:
    """E-mail do usuário autenticado; o IAP prefixa com `accounts.google.com:`."""
    if not cabecalho:
        return "não autenticado (execução local)"
    return cabecalho.split(":")[-1]


def _celula(valor: Any) -> str:
    if valor is None:
        return "—"
    if isinstance(valor, datetime):
        return valor.strftime("%d/%m/%Y %H:%M")
    return html.escape(str(valor))


SITUACOES = {
    "OK": ("#1F9D55", "em dia"),
    "ATRASADA": ("#C9A227", "atrasada"),
    "FALHA_RECENTE": ("#D2492A", "falha na última execução"),
    "SEM_SUCESSO": ("#8A94A0", "nunca teve sucesso"),
}


def _duracao(minutos: int | None) -> str:
    """Minutos como algo que uma pessoa lê sem converter de cabeça."""
    if minutos is None:
        return "—"
    if minutos < 90:
        return f"há {minutos} min"
    if minutos < 60 * 36:
        return f"há {minutos // 60} h"
    return f"há {minutos // 1440} dias"


def _pct(valor: float | None) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%".replace(".", ",")


def _milhar(valor: int) -> str:
    """Separador de milhar brasileiro."""
    return f"{valor:,}".replace(",", ".")


def _cartao(c: SaudeConector) -> str:
    cor, rotulo = SITUACOES.get(c.situacao, ("#8A94A0", c.situacao))
    p95 = "—" if c.duracao_p95_seg is None else f"{c.duracao_p95_seg:.0f}s"
    erro = f'<p class="erro">{html.escape(c.ultimo_erro)}</p>' if c.ultimo_erro else ""
    return f"""<article class="cartao">
  <div class="topo"><span class="ponto" style="background:{cor}"></span>
    <strong>{html.escape(c.conector)}</strong></div>
  <div class="estado">{rotulo} · último sucesso {_duracao(c.minutos_desde_sucesso)}</div>
  <dl>
    <div><dt>Sucesso 30d</dt><dd>{_pct(c.taxa_sucesso_30d)}</dd></div>
    <div><dt>Inválidas</dt><dd>{_pct(c.taxa_invalidas)}</dd></div>
    <div><dt>Linhas carregadas</dt><dd>{_milhar(c.linhas_carregadas_total)}</dd></div>
    <div><dt>Duração p95</dt><dd>{p95}</dd></div>
  </dl>
  {erro}
</article>"""


def _pagina_lake(conectores: list[SaudeConector], usuario: str, *, simulado: bool) -> str:
    atrasados = [c for c in conectores if c.situacao != "OK"]
    resumo = (
        f"{len(conectores) - len(atrasados)} de {len(conectores)} conectores em dia"
        if conectores
        else "Nenhum conector executou ainda"
    )

    cartoes = "".join(_cartao(c) for c in conectores)

    aviso = (
        '<p class="aviso">Dados de exemplo — o ambiente GCP ainda não existe (pendência A3).</p>' if simulado else ""
    )

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlupData — saúde do DataLake</title>
<style>
 body{{font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;
       color:#2B333B;margin:0;padding:40px;background:#fff}}
 header{{display:flex;justify-content:space-between;align-items:baseline;
         border-bottom:2px solid #00ADE8;padding-bottom:12px}}
 h1{{font-size:22px;margin:0;letter-spacing:-.02em}}
 .quem{{font-size:13px;color:#5A6473}}
 .resumo{{font-size:15px;margin:22px 0 4px;font-weight:500}}
 .aviso{{background:#FFF4E5;border-left:3px solid #C9A227;padding:12px 16px;font-size:14px}}
 .grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px;margin-top:20px}}
 .cartao{{border:1px solid #E4E8EC;border-radius:6px;padding:16px}}
 .topo{{display:flex;align-items:center;gap:8px;font-size:15px}}
 .ponto{{width:10px;height:10px;border-radius:50%;flex:none}}
 .estado{{font-size:13px;color:#5A6473;margin:6px 0 14px}}
 dl{{display:grid;grid-template-columns:1fr 1fr;gap:10px 16px;margin:0}}
 dt{{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#8A94A0;margin:0}}
 dd{{margin:2px 0 0;font-size:15px;font-variant-numeric:tabular-nums}}
 .erro{{margin:14px 0 0;font-size:12.5px;color:#D2492A;word-break:break-word}}
 footer{{margin-top:28px;font-size:13px;color:#5A6473}}
 a{{color:#0090C4}}
</style></head>
<body>
<header><h1>AlupData · saúde do DataLake</h1><span class="quem">{html.escape(usuario)}</span></header>
{aviso}
<p class="resumo">{resumo}</p>
<div class="grade">{cartoes}</div>
<footer>Atraso é medido contra a cadência da própria fonte, não contra um limite fixo.
 · <a href="/">ver dado de negócio</a></footer>
</body></html>"""


def _pagina(dados: Painel, usuario: str, *, simulado: bool) -> str:
    cabecalhos = "".join(f"<th>{html.escape(c)}</th>" for c in dados.colunas)
    linhas = "".join(
        "<tr>" + "".join(f"<td>{_celula(linha.get(coluna))}</td>" for coluna in dados.colunas) + "</tr>"
        for linha in dados.linhas
    )
    if dados.ultima_ingestao:
        rodape = (
            f"Última ingestão bem-sucedida: <strong>{_celula(dados.ultima_ingestao)}</strong> "
            f"({html.escape(dados.fonte_ultima_ingestao or '')})"
        )
    else:
        rodape = "Nenhuma ingestão registrada ainda."

    aviso = (
        '<p class="aviso">Dados de exemplo — o ambiente GCP ainda não existe (pendência A3). '
        "Nenhum número nesta tela veio do DataLake.</p>"
        if simulado
        else ""
    )

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlupData — {html.escape(dados.view)}</title>
<style>
 body{{font-family:system-ui,-apple-system,Segoe UI,Arial,sans-serif;
       color:#2B333B;margin:0;padding:40px;background:#fff}}
 header{{display:flex;justify-content:space-between;align-items:baseline;
         border-bottom:2px solid #00ADE8;padding-bottom:12px}}
 h1{{font-size:22px;margin:0;letter-spacing:-.02em}}
 .quem{{font-size:13px;color:#5A6473}}
 .aviso{{background:#FFF4E5;border-left:3px solid #C9A227;padding:12px 16px;font-size:14px}}
 table{{width:100%;border-collapse:collapse;margin-top:24px;font-size:14px}}
 th{{background:#0E1116;color:#fff;text-align:left;padding:10px 12px;font-weight:500}}
 td{{padding:10px 12px;border-bottom:1px solid #E4E8EC}}
 footer{{margin-top:24px;font-size:13px;color:#5A6473}}
</style></head>
<body>
<header><h1>AlupData · {html.escape(dados.view)}</h1><span class="quem">{html.escape(usuario)}</span></header>
{aviso}
<table><thead><tr>{cabecalhos}</tr></thead><tbody>{linhas}</tbody></table>
<footer>{rodape}</footer>
</body></html>"""
