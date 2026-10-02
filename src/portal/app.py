"""Portal MVP — item 0.15 do plano. Escopo cravado na ADR 005.

Quatro telas — dado de negócio, indicadores, saúde do lake e custo de nuvem —,
todas HTML do servidor, na identidade da Alup (ADR 022). Não é ferramenta de BI,
e a ADR 005 lista o que deliberadamente não faz.

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
from typing import TYPE_CHECKING, Any

from flask import Flask, Response, request
from src.core.config import get_settings
from src.core.observabilidade import configurar_logging
from src.core.seguranca import sanitizar
from src.portal import custo_tela, saude
from src.portal import indicadores as indicadores_tela
from src.portal.dados import Painel, obter_provedor
from src.portal.pagina import Telao, pagina, proxima_do_telao

if TYPE_CHECKING:
    from src.core.config import Settings

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


# O Portal não tem uma linha de JavaScript — as três visões são HTML e SVG
# embutido (ADR 005 e 006). Isso permite `script-src 'none'`, que é uma
# afirmação forte: não é "não usamos script", é "script não executa aqui".
#
# `style-src` precisa de 'unsafe-inline' porque a folha de estilo vai embutida
# na página; separá-la em arquivo estático renderia uma política mais estrita,
# mas o Portal é uma tela só e servir estático exigiria rota nova.
CSP = (
    "default-src 'none'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'none'; "
    "form-action 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'"
)

CABECALHOS_SEGURANCA = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    # O Portal expõe dado operacional da contratante: não deve ser emoldurado
    # por terceiro nem indexado.
    "X-Frame-Options": "DENY",
    "X-Robots-Tag": "noindex, nofollow",
    "Cache-Control": "no-store",
}


@app.after_request
def _aplicar_cabecalhos(resposta: Response) -> Response:
    """Endurece toda resposta, inclusive as de erro."""
    for nome, valor in CABECALHOS_SEGURANCA.items():
        resposta.headers.setdefault(nome, valor)
    return resposta


@app.errorhandler(Exception)
def _falha(exc: Exception) -> tuple[str, int]:
    """Falha fechada: registra o motivo, não o mostra.

    Sem isto, uma exceção do BigQuery sobe até o handler padrão do Flask e o
    texto do erro — que costuma trazer projeto, dataset e às vezes o SQL —
    chega ao navegador ou ao log sem passar pelo sanitizador que o resto do
    projeto aplica (cláusula 8.5).
    """
    logger.error("falha ao responder %s: %s", request.path, sanitizar(f"{type(exc).__name__}: {exc}"))
    return (
        "<h1>500</h1><p>Não foi possível carregar os dados agora. A falha foi registrada.</p>",
        500,
    )


@app.get("/")
def painel() -> Response:
    cfg = get_settings()
    provedor = obter_provedor()
    dados = provedor.painel(cfg.portal_view)
    usuario = _usuario(request.headers.get(CABECALHO_IDENTIDADE))
    return Response(
        _pagina(dados, usuario, simulado=cfg.portal_provedor != "bigquery", agora=_instante(provedor, "painel")),
        mimetype="text/html",
    )


@app.get("/lake")
def lake() -> Response:
    """Painel de saúde do DataLake — monitoramento, não relatório de negócio.

    Escopo em `docs/arquitetura/decisoes/006-painel-de-saude.md`.
    """
    cfg = get_settings()
    provedor = obter_provedor()
    fontes = saude.montar(provedor.saude(), provedor.volumetria())
    telao = _telao("/lake", nome="Saúde do lake")
    aviso = "Dados de exemplo — o ambiente GCP ainda não existe (pendência A3)." if _simulado(cfg) else ""
    return _responder(
        pagina(
            titulo="Saúde do lake",
            rota="/lake",
            usuario=_usuario(request.headers.get(CABECALHO_IDENTIDADE)),
            banda=saude.banda(fontes),
            corpo=saude.corpo(fontes, telao=telao is not None),
            aviso=aviso,
            telao=telao,
            agora=_instante(provedor, "saude", "volumetria"),
        )
    )


@app.get("/custo")
def custo() -> Response:
    """Custo de nuvem do DataLake, nos três recortes da §5-A do plano de FinOps.

    Operacional, orçamento e diretoria — a mesma conta, três leituras. Escopo e
    enquadramento contratual em `docs/arquitetura/portal-finops.md`.
    """
    cfg = get_settings()
    provedor = obter_provedor()
    dados = provedor.custo()
    telao = _telao("/custo", nome="Custo de nuvem")
    aviso = (
        "Dados de exemplo, derivados da volumetria simulada — o ambiente GCP ainda não existe (pendência A3). "
        "Nenhum valor desta tela veio de uma fatura."
        if _simulado(cfg)
        else ""
    )
    return _responder(
        pagina(
            titulo="Custo de nuvem",
            rota="/custo",
            usuario=_usuario(request.headers.get(CABECALHO_IDENTIDADE)),
            banda=custo_tela.banda(dados),
            corpo=custo_tela.corpo(dados, telao=telao is not None),
            aviso=aviso,
            telao=telao,
            agora=_instante(provedor, "custo"),
        )
    )


@app.get("/indicadores")
def indicadores() -> Response:
    """Razões técnicas do setor, com numerador e denominador — sem meta (ADR 012, adendo de 27/09).

    A conta é do Dataform (`gold.indicadores_mensais`); a tela só mostra. No modo
    telão os cartões vêm em páginas de 12, para nenhum ficar escondido por rolagem.
    """
    cfg = get_settings()
    provedor = obter_provedor()
    linhas = provedor.indicadores()
    prontos = indicadores_tela.cartoes(linhas)
    paginas = indicadores_tela.paginas_do_telao(len(prontos))
    numero = min(max(_inteiro(request.args.get("p"), 1), 1), paginas)
    telao = _telao("/indicadores", numero, paginas, nome="Indicadores")
    aviso = (
        "Dados de exemplo — números inventados para mostrar o formato. Nenhum valor desta tela veio do DataLake."
        if _simulado(cfg)
        else ""
    )
    return _responder(
        pagina(
            titulo="Indicadores",
            rota="/indicadores",
            usuario=_usuario(request.headers.get(CABECALHO_IDENTIDADE)),
            banda=indicadores_tela.banda(len(prontos), indicadores_tela.referencia(linhas)),
            corpo=indicadores_tela.corpo(prontos, pagina=numero if telao else None),
            aviso=aviso,
            telao=telao,
            agora=_instante(provedor, "indicadores"),
        )
    )


@app.get("/saude")
def sonda() -> dict[str, str]:
    """Sonda do Cloud Run: responde sem tocar no BigQuery."""
    return {"status": "ok"}


def _instante(provedor: Any, *leituras: str) -> datetime | None:
    """Quando o dado foi lido de verdade. Só o provedor com cache sabe; sem ele, é agora."""
    consultado_em = getattr(provedor, "consultado_em", None)
    return consultado_em(*leituras) if consultado_em else None


def _responder(documento: str) -> Response:
    return Response(documento, mimetype="text/html")


def _simulado(cfg: Settings) -> bool:
    return cfg.portal_provedor != "bigquery"


def _inteiro(texto: str | None, padrao: int) -> int:
    try:
        return int(texto) if texto else padrao
    except ValueError:
        return padrao


def _telao(rota: str, pagina_atual: int = 1, paginas: int = 1, *, nome: str) -> Telao | None:
    """Modo telão: só liga com `?telao=1`, e nunca por acidente."""
    if request.args.get("telao") != "1":
        return None
    rotulo = f"{nome} {pagina_atual} de {paginas}" if paginas > 1 else nome
    return Telao(rotulo, proxima_do_telao(rota, pagina_atual, paginas))


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


def _pagina(dados: Painel, usuario: str, *, simulado: bool, agora: datetime | None = None) -> str:
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
        "Dados de exemplo — o ambiente GCP ainda não existe (pendência A3). Nenhum número nesta tela veio do DataLake."
        if simulado
        else ""
    )
    banda = (
        '<section class="ad-band ad-band--centered" aria-label="Resumo"><div class="ad-summary">'
        f'<div class="ad-summary__text"><h2 class="ad-summary__title">{html.escape(dados.view)}</h2>'
        f'<p class="ad-summary__sub">{rodape}</p></div></div></section>'
    )
    corpo = (
        f'<div class="ad-rolagem"><table class="ad-lista"><thead><tr>{cabecalhos}</tr></thead>'
        f"<tbody>{linhas}</tbody></table></div>"
    )
    return pagina(
        titulo="Dado de negócio", rota="/", usuario=usuario, banda=banda, corpo=corpo, aviso=aviso, agora=agora
    )
