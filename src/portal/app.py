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
from src.core.observabilidade import configurar_logging
from src.portal.dados import Painel, SaudeConector, SerieVolumetria, obter_provedor
from src.portal.grafico import area, cor_do_conector, tabela

configurar_logging()
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
    provedor = obter_provedor()
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(
        _pagina_lake(
            provedor.saude(),
            provedor.volumetria(),
            usuario,
            simulado=cfg.portal_provedor != "bigquery",
        ),
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


# Cores de estado são reservadas: nunca reaproveitadas como cor de série.
SITUACOES = {
    "OK": ("var(--good)", "em dia"),
    "ATRASADA": ("var(--warning)", "atrasada"),
    "FALHA_RECENTE": ("var(--critical)", "falha na última execução"),
    "SEM_SUCESSO": ("var(--idle)", "nunca teve sucesso"),
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


def _cartao(c: SaudeConector, serie: SerieVolumetria | None, cor_serie: str) -> str:
    cor, rotulo = SITUACOES.get(c.situacao, ("var(--idle)", c.situacao))
    p95 = "—" if c.duracao_p95_seg is None else f"{c.duracao_p95_seg:.0f}s"
    erro = f'<p class="erro">{html.escape(c.ultimo_erro)}</p>' if c.ultimo_erro else ""
    grafico = (
        f'<figure class="figura"><figcaption>Linhas por dia · 30 dias</figcaption>{area(serie, cor_serie)}</figure>'
        if serie and any(serie.linhas)
        else ""
    )
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
  {grafico}
  {erro}
</article>"""


def _pagina_lake(
    conectores: list[SaudeConector],
    series: list[SerieVolumetria],
    usuario: str,
    *,
    simulado: bool,
) -> str:
    atrasados = [c for c in conectores if c.situacao != "OK"]
    por_conector = {s.conector: s for s in series}
    ordem = sorted(por_conector)
    resumo = (
        f"{len(conectores) - len(atrasados)} de {len(conectores)} conectores em dia"
        if conectores
        else "Nenhum conector executou ainda"
    )

    cartoes = "".join(
        _cartao(c, por_conector.get(c.conector), cor_do_conector(c.conector, ordem))
        if c.conector in ordem
        else _cartao(c, None, "#8A94A0")
        for c in conectores
    )
    total_linhas = sum(s.total for s in series)

    aviso = (
        '<p class="aviso">Dados de exemplo — o ambiente GCP ainda não existe (pendência A3).</p>' if simulado else ""
    )

    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlupData — saúde do DataLake</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600
&family=Zilla+Slab:wght@500;600&display=swap">
<style>
 /* Tokens no formato do shadcn/ui, com a paleta do alup.io.
    Sem React e sem build: a ADR 005 mantém o Portal renderizado no servidor. */
 :root{{
   --background:#fcfcfb; --foreground:#212121;
   --card:#ffffff; --card-foreground:#212121;
   --muted:#f4f4f4; --muted-foreground:#6b6675;
   --border:#e6e3ea; --ring:#520042;
   --primary:#520042; --primary-foreground:#ffffff;
   --radius:.6rem;
   --good:#0E8A6B; --warning:#B26A00; --critical:#C2185B; --idle:#8A94A0;
 }}
 *{{box-sizing:border-box}}
 body{{font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,Arial,sans-serif;
   color:var(--foreground);background:var(--background);margin:0;
   padding:clamp(24px,4vw,48px);-webkit-font-smoothing:antialiased}}
 header{{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
   border-bottom:1px solid var(--border);padding-bottom:16px}}
 h1{{font-family:'Zilla Slab',Georgia,serif;font-weight:600;font-size:clamp(20px,2.4vw,27px);
   margin:0;letter-spacing:-.01em}}
 .quem{{font-size:13px;color:var(--muted-foreground)}}
 .cabeca-secao{{display:flex;justify-content:space-between;align-items:baseline;
   flex-wrap:wrap;gap:8px;margin:26px 0 2px}}
 .resumo{{font-size:16px;font-weight:600;margin:0}}
 .muted{{font-size:13px;color:var(--muted-foreground);margin:0;font-variant-numeric:tabular-nums}}
 .aviso{{background:#fff8ec;border:1px solid #f0dcb8;border-radius:var(--radius);
   padding:12px 16px;font-size:14px;margin-top:20px}}
 .grade{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
   gap:16px;margin-top:16px}}
 .cartao{{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
   padding:18px 18px 14px;display:flex;flex-direction:column}}
 .topo{{display:flex;align-items:center;gap:8px;font-size:15px;letter-spacing:-.01em}}
 .topo strong{{font-weight:600}}
 .ponto{{width:8px;height:8px;border-radius:50%;flex:none}}
 .estado{{font-size:12.5px;color:var(--muted-foreground);margin:6px 0 16px}}
 dl{{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px;margin:0}}
 dt{{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
   color:var(--muted-foreground);margin:0}}
 dd{{margin:3px 0 0;font-size:16px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}}
 .figura{{margin:18px 0 0}}
 .figura figcaption{{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
   color:var(--muted-foreground);margin-bottom:6px}}
 .grafico{{width:100%;height:64px;display:block;overflow:visible}}
 .erro{{margin:14px 0 0;font-size:12.5px;color:var(--critical);word-break:break-word}}
 .tabela{{margin-top:26px;border:1px solid var(--border);border-radius:var(--radius);
   background:var(--card)}}
 .tabela summary{{cursor:pointer;padding:12px 16px;font-size:14px;font-weight:500}}
 .rolagem{{overflow-x:auto;padding:0 16px 16px}}
 .tabela table{{border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}}
 .tabela th,.tabela td{{padding:6px 10px;text-align:right;white-space:nowrap;
   border-bottom:1px solid var(--border)}}
 .tabela thead th{{text-align:right;color:var(--muted-foreground);font-weight:500}}
 .tabela tbody th{{text-align:left;font-weight:500}}
 .tabela .total{{font-weight:600}}
 footer{{margin-top:28px;font-size:12.5px;color:var(--muted-foreground)}}
 a{{color:var(--primary)}}
</style></head>
<body>
<header><h1>AlupData · saúde do DataLake</h1><span class="quem">{html.escape(usuario)}</span></header>
{aviso}
<div class="cabeca-secao">
  <p class="resumo">{resumo}</p>
  <p class="muted">{_milhar(total_linhas)} linhas carregadas nos últimos 30 dias</p>
</div>
<div class="grade">{cartoes}</div>
{tabela(series)}
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
