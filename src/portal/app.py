"""Portal MVP — item 0.15 do plano. Escopo cravado na ADR 005.

Uma tela: uma view Gold e quando o lake foi alimentado pela última vez. Não é
ferramenta de BI, e a ADR 005 lista o que deliberadamente não faz.

Autenticação não é escrita aqui. No Cloud Run o acesso é restrito por IAM /
IAP, e a identidade chega no cabeçalho `X-Goog-Authenticated-User-Email` — a
plataforma faz isso melhor do que qualquer login que escrevêssemos em 8h, e
sem guardar senha nenhuma.

Delegar não é confiar cegamente: em modo real o portal **falha fechado** se a
identidade não chegar. Sem essa trava, um deploy com `--allow-unauthenticated`,
ou um IAP mal configurado, serviria dado do lake a qualquer visitante — e a
tela apenas o rotularia como "não autenticado" em vez de recusá-lo.

    uv run flask --app src.portal.app run    # local, provedor simulado
"""

from __future__ import annotations

import html
import logging
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from flask import Flask, Response, request
from src.core.config import get_settings
from src.core.observabilidade import configurar_logging
from src.portal.dados import Painel, SaudeConector, SerieVolumetria, obter_provedor
from src.portal.grafico import _milhar, area, barras_custo, cor_do_conector, legenda_custo, tabela, usd

if TYPE_CHECKING:
    from src.portal.custo import PainelCusto

configurar_logging()
logger = logging.getLogger("portal")
app = Flask(__name__)

CABECALHO_IDENTIDADE = "X-Goog-Authenticated-User-Email"

# Rotas que respondem sem identidade: o health check do Cloud Run é chamado
# pela própria plataforma, antes e fora de qualquer sessão de usuário.
ROTAS_PUBLICAS = frozenset({"/saude"})


@app.before_request
def exigir_identidade() -> Response | None:
    """Recusa a requisição quando o modo é real e o IAP não identificou ninguém.

    Em modo simulado a trava não se aplica — é o desenvolvimento na máquina de
    quem escreve, sem dado real na frente. Em modo `bigquery` a ausência do
    cabeçalho significa que a requisição não passou pelo IAP, e a resposta certa
    é 403, não uma página rotulada.
    """
    if request.path in ROTAS_PUBLICAS:
        return None
    if get_settings().portal_provedor != "bigquery":
        return None
    if not request.headers.get(CABECALHO_IDENTIDADE):
        logger.warning("requisição sem identidade recusada em %s", request.path)
        return Response(
            "<h1>403</h1><p>Acesso restrito. Esta aplicação exige autenticação pela plataforma.</p>",
            status=403,
            mimetype="text/html",
        )
    return None


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


@app.get("/custo")
def custo() -> Response:
    """Custo de nuvem do DataLake, nos três recortes da §5-A do plano de FinOps.

    Operacional, orçamento e diretoria — a mesma conta, três leituras. Escopo e
    enquadramento contratual em `docs/arquitetura/portal-finops.md`.
    """
    cfg = get_settings()
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(
        _pagina_custo(obter_provedor().custo(), usuario, simulado=cfg.portal_provedor != "bigquery"),
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


# Estilo compartilhado por `/lake` e `/custo`. Uma cópia só: divergir o token
# entre duas telas do mesmo Portal é como o desalinho visual começa.
ESTILO = """<style>
 /* Tokens no formato do shadcn/ui, com a paleta do alup.io.
    Sem React e sem build: a ADR 005 mantém o Portal renderizado no servidor. */
 :root{
   --background:#fcfcfb; --foreground:#212121;
   --card:#ffffff; --card-foreground:#212121;
   --muted:#f4f4f4; --muted-foreground:#6b6675;
   --border:#e6e3ea; --ring:#520042;
   --primary:#520042; --primary-foreground:#ffffff;
   --radius:.6rem;
   --good:#0E8A6B; --warning:#B26A00; --critical:#C2185B; --idle:#8A94A0;
 }
 *{box-sizing:border-box}
 body{font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,Arial,sans-serif;
   color:var(--foreground);background:var(--background);margin:0;
   padding:clamp(24px,4vw,48px);-webkit-font-smoothing:antialiased}
 header{display:flex;justify-content:space-between;align-items:baseline;gap:16px;
   border-bottom:1px solid var(--border);padding-bottom:16px}
 h1{font-family:'Zilla Slab',Georgia,serif;font-weight:600;font-size:clamp(20px,2.4vw,27px);
   margin:0;letter-spacing:-.01em}
 .quem{font-size:13px;color:var(--muted-foreground)}
 .cabeca-secao{display:flex;justify-content:space-between;align-items:baseline;
   flex-wrap:wrap;gap:8px;margin:26px 0 2px}
 .resumo{font-size:16px;font-weight:600;margin:0}
 .muted{font-size:13px;color:var(--muted-foreground);margin:0;font-variant-numeric:tabular-nums}
 .aviso{background:#fff8ec;border:1px solid #f0dcb8;border-radius:var(--radius);
   padding:12px 16px;font-size:14px;margin-top:20px}
 .grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
   gap:16px;margin-top:16px}
 .cartao{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
   padding:18px 18px 14px;display:flex;flex-direction:column}
 .topo{display:flex;align-items:center;gap:8px;font-size:15px;letter-spacing:-.01em}
 .topo strong{font-weight:600}
 .ponto{width:8px;height:8px;border-radius:50%;flex:none}
 .estado{font-size:12.5px;color:var(--muted-foreground);margin:6px 0 16px}
 dl{display:grid;grid-template-columns:1fr 1fr;gap:12px 16px;margin:0}
 dt{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
   color:var(--muted-foreground);margin:0}
 dd{margin:3px 0 0;font-size:16px;font-variant-numeric:tabular-nums;letter-spacing:-.01em}
 .figura{margin:18px 0 0}
 .figura figcaption{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
   color:var(--muted-foreground);margin-bottom:6px}
 .grafico{width:100%;height:64px;display:block;overflow:visible}
 .erro{margin:14px 0 0;font-size:12.5px;color:var(--critical);word-break:break-word}
 .tabela{margin-top:26px;border:1px solid var(--border);border-radius:var(--radius);
   background:var(--card)}
 .tabela summary{cursor:pointer;padding:12px 16px;font-size:14px;font-weight:500}
 .rolagem{overflow-x:auto;padding:0 16px 16px}
 .tabela table{border-collapse:collapse;font-size:12.5px;font-variant-numeric:tabular-nums}
 .tabela th,.tabela td{padding:6px 10px;text-align:right;white-space:nowrap;
   border-bottom:1px solid var(--border)}
 .tabela thead th{text-align:right;color:var(--muted-foreground);font-weight:500}
 .tabela tbody th{text-align:left;font-weight:500}
 .tabela .total{font-weight:600}
 footer{margin-top:28px;font-size:12.5px;color:var(--muted-foreground)}
 a{color:var(--primary)}

 /* Custo — a rota /custo reaproveita tudo acima e acrescenta só o que é dela. */
 .naves{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;margin:14px 0 0}
 .naves a{text-decoration:none;color:var(--muted-foreground);padding-bottom:3px;
   border-bottom:2px solid transparent}
 .naves a.atual{color:var(--foreground);border-bottom-color:var(--primary);font-weight:500}
 .visao{margin-top:34px}
 .visao > h2{font-family:'Zilla Slab',Georgia,serif;font-size:19px;font-weight:600;
   margin:0;letter-spacing:-.01em}
 .visao > .para-quem{font-size:12.5px;color:var(--muted-foreground);margin:4px 0 0}
 .tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
   gap:16px;margin-top:16px}
 .tile{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);
   padding:16px 18px}
 .tile .rot{font-size:10.5px;letter-spacing:.07em;text-transform:uppercase;
   color:var(--muted-foreground)}
 .tile .val{font-size:27px;margin-top:6px;font-variant-numeric:tabular-nums;
   letter-spacing:-.02em;line-height:1.1}
 .tile .sub{font-size:12.5px;color:var(--muted-foreground);margin-top:6px}
 .tile .val.alerta{color:var(--critical)}
 .tile .val.bom{color:var(--good)}
 .barra{height:7px;border-radius:4px;background:var(--muted);margin-top:12px;overflow:hidden}
 .barra span{display:block;height:100%;background:var(--good)}
 .barra span.estoura{background:var(--critical)}
 .grafico-alto{height:132px}
 .legenda{display:flex;gap:16px;list-style:none;padding:0;margin:10px 0 0;
   font-size:12px;color:var(--muted-foreground);flex-wrap:wrap}
 .legenda .chave{display:inline-block;width:9px;height:9px;border-radius:2px;
   margin-right:6px;vertical-align:baseline}
 .lista{width:100%;border-collapse:collapse;font-size:13px;margin-top:14px;
   font-variant-numeric:tabular-nums}
 .lista th{text-align:right;font-weight:500;color:var(--muted-foreground);
   padding:8px 10px;border-bottom:1px solid var(--border);font-size:11px;
   letter-spacing:.05em;text-transform:uppercase}
 .lista th:first-child,.lista td:first-child{text-align:left}
 .lista td{padding:9px 10px;border-bottom:1px solid var(--border);text-align:right}
 .lista tr:last-child td{border-bottom:none}
 .marca{display:inline-block;font-size:10.5px;font-weight:600;letter-spacing:.05em;
   text-transform:uppercase;padding:2px 6px;border-radius:3px;
   background:#fdecef;color:var(--critical)}
 .nota{font-size:12.5px;color:var(--muted-foreground);margin:12px 0 0;max-width:70ch}
 .premissa{background:var(--muted);border-radius:var(--radius);padding:14px 16px;
   font-size:12.5px;color:var(--muted-foreground);margin-top:26px;max-width:80ch}
"""


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
{ESTILO}</style></head>
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


def _naves(atual: str) -> str:
    """As três telas do Portal. Uma barra só, para não haver tela órfã."""
    rotas = (("/", "Dado de negócio"), ("/lake", "Saúde do lake"), ("/custo", "Custo de nuvem"))
    itens = []
    for rota, nome in rotas:
        classe = ' class="atual"' if rota == atual else ""
        itens.append(f'<a href="{rota}"{classe}>{html.escape(nome)}</a>')
    return '<nav class="naves">' + "".join(itens) + "</nav>"


def _tile(rotulo: str, valor: str, sub: str = "", classe: str = "") -> str:
    extra = f' class="val {classe}"' if classe else ' class="val"'
    sublinha = f'<div class="sub">{sub}</div>' if sub else ""
    return f'<div class="tile"><div class="rot">{html.escape(rotulo)}</div><div{extra}>{valor}</div>{sublinha}</div>'


def _bytes_humano(valor: int) -> str:
    """Byte varrido só significa alguma coisa na unidade em que se cobra."""
    for unidade, divisor in (("TiB", 1024**4), ("GiB", 1024**3), ("MiB", 1024**2)):
        if valor >= divisor:
            return f"{valor / divisor:.2f} {unidade}".replace(".", ",")
    return f"{_milhar(valor)} B"


def _visao_operacional(dados: PainelCusto) -> str:
    """O que eu mudo hoje: consulta cara, view degradada, dataset que cresce."""
    anomalas = [c for c in dados.consultas if c.anomala]
    linhas = "".join(
        f"<tr><td>{html.escape(c.rotulo)}"
        + (' <span class="marca">varredura integral</span>' if c.anomala else "")
        + f"</td><td>{_milhar(c.execucoes)}</td><td>{_bytes_humano(c.bytes_varridos)}</td>"
        f"<td>{usd(c.custo_usd)}</td>"
        f"<td>{'+' if c.variacao_vs_media >= 0 else ''}{c.variacao_vs_media * 100:.0f}%</td></tr>"
        for c in dados.consultas
    )
    alerta = (
        f'<p class="nota"><span class="marca">atenção</span> '
        f"{len(anomalas)} consulta(s) varrendo mais que o dobro da própria média. "
        "Varredura integral quase sempre é filtro de partição faltando na view. "
        "Vale corrigir antes que o volume cresça — mas repare na coluna de custo: "
        "hoje ela não é a consulta mais cara.</p>"
        if anomalas
        else '<p class="nota">Nenhuma consulta destoando da própria média.</p>'
    )
    return f"""<section class="visao">
  <h2>Operacional</h2>
  <p class="para-quem">Para quem opera o pipeline · o que dá para mudar hoje</p>
  <figure class="figura">
    <figcaption>Gasto por dia · composição · 30 dias</figcaption>
    {barras_custo(dados.dias)}
    {legenda_custo()}
  </figure>
  <table class="lista">
    <thead><tr><th>Consulta</th><th>Execuções</th><th>Varrido</th><th>Custo</th><th>vs. média</th></tr></thead>
    <tbody>{linhas}</tbody>
  </table>
  {alerta}
  <p class="nota">A lista está ordenada por custo, não por byte varrido — e o gráfico
    acima explica por quê: nesta escala a conta é quase toda <strong>custo fixo por
    execução</strong>, não volume. O job de ingestão e o mínimo faturado por consulta
    somam mais que todo o byte varrido do lake. Enquanto for assim, <strong>reduzir
    número de execuções rende mais que otimizar varredura</strong>. Isso se inverte
    quando a Onda 3 trouxer os sistemas internos, e é aí que a varredura integral
    marcada acima passa a doer — corrigir antes é mais barato que corrigir depois.</p>
</section>"""


def _visao_orcamento(dados: PainelCusto) -> str:
    """Estamos dentro do previsto, e para onde a curva do mês aponta."""
    o = dados.orcamento
    largura = min(o.consumo_pct, 1.0) * 100
    classe_barra = " estoura" if o.estoura else ""
    projecao = (
        f"projeta {_pct(o.projecao_pct)} do orçado — estouro de {usd(o.projetado_usd - o.orcado_usd)}"
        if o.estoura
        else f"projeta {_pct(o.projecao_pct)} do orçado"
    )

    linhas = "".join(
        f"<tr><td>{html.escape(f.fonte)}</td><td>{usd(f.query_usd)}</td>"
        f"<td>{usd(f.armazenamento_usd)}</td><td>{usd(f.total_usd)}</td>"
        f"<td>{'—' if f.usd_por_milhao_de_linhas is None else usd(f.usd_por_milhao_de_linhas)}</td></tr>"
        for f in dados.fontes
    )
    return f"""<section class="visao">
  <h2>Orçamento</h2>
  <p class="para-quem">Para quem responde pelo orçamento de nuvem · fecha o mês</p>
  <div class="tiles">
    {_tile("Realizado no mês", usd(o.realizado_usd), f"{o.dias_decorridos} de {o.dias_do_mes} dias")}
    {_tile("Orçado", usd(o.orcado_usd), "premissa de configuração")}
    {
        _tile(
            "Projeção de fechamento",
            usd(o.projetado_usd),
            projecao,
            "alerta" if o.estoura else "bom",
        )
    }
    {_tile("Gasto em 30 dias", usd(dados.total_usd), "consulta + armazenamento + compute")}
  </div>
  <div class="barra"><span class="{classe_barra.strip()}" style="width:{largura:.0f}%"></span></div>
  <table class="lista">
    <thead><tr><th>Fonte</th><th>Consulta</th><th>Armazenamento</th><th>Total</th>
      <th>US$ por milhão de linhas</th></tr></thead>
    <tbody>{linhas}</tbody>
  </table>
  <p class="nota">A última coluna é a que separa fonte cara de fonte cara à toa:
    ela mede o custo pelo que a fonte entrega, não pelo que ela consome.
    Só existe porque o job é rotulado por fonte (camada F0 do plano).</p>
</section>"""


def _visao_diretoria(dados: PainelCusto) -> str:
    """Vale o que custa. Poucos números, cada um defensável em reunião."""
    dominios = dados.por_dominio
    total = sum((valor for _, valor in dominios), Decimal(0)) or Decimal(1)
    linhas = "".join(
        f"<tr><td>{html.escape(nome)}</td><td>{usd(valor)}</td><td>{_pct(float(valor / total))}</td></tr>"
        for nome, valor in dominios
    )
    maior = dominios[0][0] if dominios else "—"
    return f"""<section class="visao">
  <h2>Diretoria</h2>
  <p class="para-quem">Para quem decide renovar · trimestral</p>
  <div class="tiles">
    {_tile("Custo mensal projetado", usd(dados.orcamento.projetado_usd), "todo o DataLake")}
    {_tile("Maior domínio", html.escape(maior), "onde o dinheiro está")}
    {_tile("Fontes em produção", str(len(dados.fontes)), "custo atribuído a cada uma")}
  </div>
  <table class="lista">
    <thead><tr><th>Domínio de negócio</th><th>Custo em 30 dias</th><th>Participação</th></tr></thead>
    <tbody>{linhas}</tbody>
  </table>
  <p class="nota"><span class="marca">provisório</span> O agrupamento por domínio é
    provisório: os 8 domínios analíticos dependem do Questionário de Gaps
    (pendência A4). Até lá, as fontes estão agrupadas por afinidade óbvia — serve
    para desenhar a tela, não para levar a uma reunião de diretoria.</p>
</section>"""


def _pagina_custo(dados: PainelCusto, usuario: str, *, simulado: bool) -> str:
    aviso = (
        '<p class="aviso">Dados de exemplo, derivados da volumetria simulada — o ambiente GCP '
        "ainda não existe (pendência A3). Nenhum valor desta tela veio de uma fatura.</p>"
        if simulado
        else ""
    )
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AlupData — custo de nuvem</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600
&family=Zilla+Slab:wght@500;600&display=swap">
{ESTILO}</style></head>
<body>
<header><h1>AlupData · custo de nuvem</h1><span class="quem">{html.escape(usuario)}</span></header>
{_naves("/custo")}
{aviso}
{_visao_operacional(dados)}
{_visao_orcamento(dados)}
{_visao_diretoria(dados)}
<p class="premissa"><strong>Premissas.</strong> Os valores usam a tarifa por byte varrido e por
 GiB armazenado declaradas em <code>src/portal/custo.py</code>, e não enxergam crédito nem
 desconto por uso comprometido — isso só chega com o billing export (camada F2 do plano).
 Compute aparece no agregado e não por fonte: existe um Cloud Run Job para todas elas.
 Plano e enquadramento em <code>docs/arquitetura/portal-finops.md</code>.</p>
</body></html>"""
