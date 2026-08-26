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
from src.portal.dados import Painel, obter_provedor

app = Flask(__name__)

CABECALHO_IDENTIDADE = "X-Goog-Authenticated-User-Email"


@app.get("/")
def painel() -> Response:
    cfg = get_settings()
    dados = obter_provedor().painel(cfg.portal_view)
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(_pagina(dados, usuario, simulado=cfg.portal_provedor != "bigquery"), mimetype="text/html")


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
