"""As três telas redesenhadas do Portal (01/10): saúde do lake, indicadores e custo.

O que importa aqui é o que a Alup lê: um veredito, a espera por credencial que não
é erro, a tira de 30 dias, o modo telão sem JavaScript e a casca na identidade da
Alup. A regra de estado em si é do Gold (`tests/unit/test_sql.py`).
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest
from src.portal import saude as tela_saude
from src.portal.app import app
from src.portal.dados import Indicador, ProvedorSimulado, SaudeConector, SerieVolumetria
from src.portal.pagina import Telao, pagina, proxima_do_telao

TELAS = ["/", "/lake", "/custo", "/indicadores"]


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)
    return app.test_client()


def _provedor(*, saude=(), volumetria=(), indicadores=()):
    base = ProvedorSimulado()
    return SimpleNamespace(
        saude=lambda: list(saude),
        volumetria=lambda dias=30: list(volumetria),
        indicadores=lambda meses=12: list(indicadores),
        custo=base.custo,
        painel=base.painel,
    )


def _conector(nome, situacao="OK", **extra):
    base = {
        "ultimo_sucesso": datetime(2026, 10, 1, 9, 0, tzinfo=UTC),
        "minutos_desde_sucesso": 120,
        "intervalo_tipico_min": 1440,
        "taxa_sucesso_30d": 1.0,
        "taxa_invalidas": 0.0,
        "linhas_carregadas_total": 1000,
        "duracao_p95_seg": 3.0,
        "ultimo_erro": None,
    }
    return SaudeConector(nome, situacao, **{**base, **extra})


# --- saúde do lake -------------------------------------------------------------


def test_veredito_conta_so_o_que_pede_atencao(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "1 fonte pede atenção" in corpo  # a ANEEL atrasada
    assert "3 de 5 em dia" in corpo
    assert "1 aguardando credencial" in corpo  # o Hubspot espera o token e não pesa no veredito


def test_tudo_em_dia_acende_o_verde(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor(saude=[_conector("ons_carga")]))
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "Tudo em dia" in corpo
    assert "ad-verdict--ok" in corpo


def test_fonte_aguardando_credencial_nao_e_erro(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True).split("</style>", 1)[1]
    assert "ad-row--idle" in corpo
    assert "ad-verdict--crit" not in corpo  # esperar a Alup não pinta a tela de vermelho


def test_erro_tecnico_nao_chega_na_tela(cliente) -> None:
    """Para a Alup, a frase é curta e em português; o texto do erro fica no log."""
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "PermissionDenied" not in corpo
    assert "pendência A9" not in corpo


def test_fonte_fora_do_verde_diz_o_que_acontece_em_portugues(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "sem carga há 9 dias" in corpo  # ANEEL: 13.055 minutos desde o último sucesso


def test_cor_nao_e_o_unico_sinal_de_estado(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert 'aria-label="pede atenção"' in corpo
    assert 'aria-label="aguardando credencial"' in corpo
    assert "<svg" in corpo.split('ad-row--warn"', 1)[1].split("</summary>", 1)[0]  # glifo junto da cor


def test_evidencia_de_entrega_fica_na_pagina_recolhida(cliente) -> None:
    """Linhas carregadas e taxa de sucesso: a prova das Ondas 0 e 1, sem ocupar o telão."""
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "<details" in corpo
    assert "Linhas carregadas no total" in corpo
    assert "75.789" in corpo  # separador de milhar brasileiro
    assert "Sucesso em 30 dias" in corpo
    assert "p95" not in corpo.lower()


def test_lake_sem_conector_nao_quebra(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor())
    assert "Nenhuma fonte executou ainda" in cliente.get("/lake").get_data(as_text=True)


def test_lake_escapa_o_nome_do_conector(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    ruim = _conector("<img src=x onerror=alert(1)>")
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor(saude=[ruim]))
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "<img" not in corpo
    assert "&lt;img" in corpo


def test_grupo_vem_do_prefixo_e_outras_vai_por_ultimo() -> None:
    assert tela_saude.grupo_de("ons_ear_bacia") == "ONS"
    assert tela_saude.grupo_de("tempook_ena_prevs") == "TempoOK"
    assert tela_saude.grupo_de("hubspot_negocios") == "Outras"
    fontes = tela_saude.montar([_conector("hubspot_negocios"), _conector("ccee_pld"), _conector("ons_carga")], [])
    assert [g for g, _ in tela_saude._grupos(fontes)] == ["ONS", "CCEE", "Outras"]


def test_nome_da_linha_perde_o_prefixo_do_grupo() -> None:
    fonte = tela_saude.montar([_conector("ons_ear_bacia")], [])[0]
    assert fonte.nome == "ear bacia"
    assert tela_saude.montar([_conector("hubspot_negocios")], [])[0].nome == "hubspot negocios"


def test_estado_segue_a_situacao_do_gold() -> None:
    def estado(situacao, **extra):
        return tela_saude.montar([_conector("ons_carga", situacao, **extra)], [])[0].estado

    assert estado("OK") == "ok"
    assert estado("ATRASADA") == "warn"
    assert estado("FALHA_RECENTE") == "warn"
    assert estado("SEM_SUCESSO") == "crit"
    assert estado("SEM_SUCESSO", aguardando_credencial=True) == "idle"


def test_tira_de_30_dias_tem_tres_estados() -> None:
    dias = [date(2026, 10, 1) - timedelta(days=i) for i in reversed(range(30))]
    linhas = [0] * 30
    falhas = [0] * 30
    linhas[29] = 10  # hoje carregou
    falhas[28] = 1  # ontem falhou e não carregou
    linhas[27], falhas[27] = 5, 1  # tentou de novo e deu certo: o dado chegou
    serie = SerieVolumetria("ons_carga", dias, linhas, falhas)
    tira = tela_saude.montar([_conector("ons_carga")], [serie])[0].tira
    assert len(tira) == 30
    assert tira[29] == "c"
    assert tira[28] == "f"
    assert tira[27] == "c"
    assert tira[0] == "n"


def test_tira_curta_completa_com_sem_carga_a_esquerda() -> None:
    serie = SerieVolumetria("ons_carga", [date(2026, 10, 1)], [3])
    tira = tela_saude.montar([_conector("ons_carga")], [serie])[0].tira
    assert tira == ["n"] * 29 + ["c"]
    assert tela_saude.montar([_conector("ons_carga")], [])[0].tira == ["n"] * 30


def test_tira_na_tela_descreve_os_30_dias_em_texto(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "Últimos 30 dias:" in corpo
    assert corpo.count('class="ad-strip" role="img"') >= 4


# --- modo telão ----------------------------------------------------------------


@pytest.mark.parametrize("rota", ["/lake", "/custo", "/indicadores"])
def test_sem_telao_nao_ha_troca_automatica(cliente, rota) -> None:
    corpo = cliente.get(rota).get_data(as_text=True)
    assert "http-equiv" not in corpo
    assert '<body class="ad-page">' in corpo
    assert f'href="{rota}?telao=1"' in corpo


@pytest.mark.parametrize(
    ("rota", "proxima"),
    [("/lake", "/custo?telao=1"), ("/custo", "/indicadores?telao=1")],
)
def test_telao_troca_de_tela_por_meta_refresh_sem_script(cliente, rota, proxima) -> None:
    corpo = cliente.get(f"{rota}?telao=1").get_data(as_text=True)
    assert f'<meta http-equiv="refresh" content="20;url={proxima}">' in corpo
    assert '<body class="ad-page ad-page--telao">' in corpo
    assert f'<a href="{rota}">sair do modo telão</a>' in corpo
    assert "<script" not in corpo


def test_so_telao_igual_a_1_liga_o_modo(cliente) -> None:
    assert "http-equiv" not in cliente.get("/lake?telao=0").get_data(as_text=True)
    assert "http-equiv" not in cliente.get("/lake?telao=sim").get_data(as_text=True)


def test_dado_de_negocio_fica_fora_do_rodizio(cliente) -> None:
    corpo = cliente.get("/?telao=1").get_data(as_text=True)
    assert "http-equiv" not in corpo
    assert "modo telão" not in corpo


def test_rodizio_percorre_indicadores_saude_custo_e_volta() -> None:
    assert proxima_do_telao("/indicadores", 1, 2) == "/indicadores?telao=1&p=2"
    assert proxima_do_telao("/indicadores", 2, 2) == "/lake?telao=1"
    assert proxima_do_telao("/lake") == "/custo?telao=1"
    assert proxima_do_telao("/custo") == "/indicadores?telao=1"


def _indicadores(recortes: int) -> list[Indicador]:
    linhas = []
    for k in range(recortes):
        for mes in ("2026-07", "2026-08"):
            linhas.append(
                Indicador(
                    mes,
                    "disponibilidade",
                    f"S{k}",
                    "UHE",
                    Decimal(40 + k),
                    "MW",
                    Decimal(100),
                    "MW",
                    Decimal("0.4"),
                    "fração",
                )
            )
    return linhas


def test_indicadores_no_telao_vem_em_paginas_de_12(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor(indicadores=_indicadores(26)))
    p1 = cliente.get("/indicadores?telao=1").get_data(as_text=True)
    p3 = cliente.get("/indicadores?telao=1&p=3").get_data(as_text=True)
    assert p1.count('class="ad-card"') == 12
    assert 'content="20;url=/indicadores?telao=1&amp;p=2"' in p1
    assert "Indicadores 1 de 3" in p1
    assert p3.count('class="ad-card"') == 2  # 26 = 12 + 12 + 2
    assert "url=/lake?telao=1" in p3  # acabou a última página: segue para a saúde


@pytest.mark.parametrize("p", ["99", "0", "abc", "-4"])
def test_pagina_do_telao_fora_da_faixa_nao_quebra(cliente, monkeypatch: pytest.MonkeyPatch, p: str) -> None:
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor(indicadores=_indicadores(26)))
    resposta = cliente.get(f"/indicadores?telao=1&p={p}")
    assert resposta.status_code == 200
    assert 'class="ad-card"' in resposta.get_data(as_text=True)


def test_fora_do_telao_todos_os_cartoes_estao_na_pagina(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: _provedor(indicadores=_indicadores(26)))
    assert cliente.get("/indicadores").get_data(as_text=True).count('class="ad-card"') == 26


# --- indicadores ---------------------------------------------------------------


def test_cartao_de_indicador_traz_valor_conta_variacao_e_tendencia(cliente) -> None:
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    assert corpo.count('class="ad-card"') == 5
    assert "ago/2026" in corpo
    assert "÷" in corpo.split('<p class="ad-calc">', 1)[1].split("</p>", 1)[0]  # a conta à vista
    assert "vs. jul/2026" in corpo
    assert corpo.count('class="ad-spark"') == 5
    assert "Série completa" in corpo


def test_indicador_nao_tem_estado_de_bom_ou_ruim(cliente) -> None:
    """Sem meta (ADR 012): variação neutra, nenhuma cor de estado na tela de indicadores."""
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    corpo = corpo.split("</style>", 1)[1]
    assert "ad-pill" not in corpo
    assert "ad-ico" not in corpo


def test_indicador_fracao_vira_percentual_e_pld_real_vira_reais(cliente) -> None:
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    assert "<small>%</small>" in corpo
    assert "<small>R$</small>" in corpo


def test_banda_dos_indicadores_conta_os_cartoes(cliente) -> None:
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    assert '<p class="ad-summary__num">5</p>' in corpo
    assert "referência ago/2026" in corpo


# --- custo ---------------------------------------------------------------------


def test_custo_na_banda_diz_o_gasto_e_o_que_pede_atencao(cliente) -> None:
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "gastos em " in corpo
    assert "1 consulta pede atenção" in corpo  # a varredura integral da ANEEL


def test_custo_mantem_as_tres_leituras_na_ordem(cliente) -> None:
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert corpo.index("1 · Operacional") < corpo.index("2 · Orçamento") < corpo.index("3 · Diretoria")


def test_custo_no_telao_mostra_so_o_topo_de_cada_lista(cliente) -> None:
    normal = cliente.get("/custo").get_data(as_text=True)
    telao = cliente.get("/custo?telao=1").get_data(as_text=True)
    assert telao.count('class="ad-qrow') < normal.count('class="ad-qrow')


def test_cor_de_custo_nao_reaproveita_cor_de_estado() -> None:
    from src.portal.grafico import CORES_CUSTO

    reservadas = {"#0E8A6B", "#B26A00", "#C2185B", "#8A94A0"}
    assert not {cor for cor, _ in CORES_CUSTO.values()} & reservadas


# --- casca: identidade, segurança e hora ---------------------------------------


@pytest.mark.parametrize("rota", TELAS)
def test_logo_e_vetor_puro_sem_imagem_nem_metadado(cliente, rota) -> None:
    """A política do Portal proíbe imagem (`img-src 'none'`), e o arquivo de logo
    original traz metadados de procedência: só o caminho vetorizado entra na página."""
    corpo = cliente.get(rota).get_data(as_text=True)
    assert 'class="ad-logo"' in corpo
    assert "<image" not in corpo
    assert "data:" not in corpo
    assert "mask-image" not in corpo
    for rastro in ("c2pa", "<metadata", "manifest", "credentials"):
        assert rastro not in corpo.lower()


@pytest.mark.parametrize("rota", TELAS)
def test_toda_tela_tem_o_cabecalho_fixo_com_a_navegacao(cliente, rota) -> None:
    corpo = cliente.get(rota).get_data(as_text=True)
    cabecalho = corpo.split('<header class="ad-head">', 1)[1].split("</header>", 1)[0]
    assert '<nav class="ad-nav"' in cabecalho
    assert "position:sticky" in corpo
    assert cabecalho.count('aria-current="page"') == 1
    for destino in ("/", "/indicadores", "/lake", "/custo"):
        assert f'href="{destino}"' in cabecalho


@pytest.mark.parametrize("rota", TELAS)
def test_toda_tela_usa_a_mesma_faixa_e_os_mesmos_tokens(cliente, rota) -> None:
    corpo = cliente.get(rota).get_data(as_text=True)
    assert '<section class="ad-band' in corpo
    assert "--primary:#520042" in corpo


def test_carimbo_e_hora_de_brasilia_e_diz_que_e_da_consulta() -> None:
    doc = pagina(
        titulo="Teste",
        rota="/lake",
        usuario="x@alupar.com.br",
        banda="",
        corpo="",
        agora=datetime(2026, 10, 1, 17, 32, tzinfo=UTC),
    )
    assert "consultado às <time" in doc
    assert ">14:32</time> (Brasília)" in doc


def test_pagina_escapa_o_usuario_e_o_rotulo_do_telao() -> None:
    doc = pagina(
        titulo="Teste",
        rota="/lake",
        usuario="<b>x</b>",
        banda="",
        corpo="",
        telao=Telao("<i>y</i>", "/custo?telao=1"),
    )
    assert "<b>x</b>" not in doc
    assert "<i>y</i>" not in doc


def test_a_politica_continua_sem_imagem_e_sem_script(cliente) -> None:
    politica = cliente.get("/lake").headers["Content-Security-Policy"]
    assert "img-src 'none'" in politica
    assert "script-src" not in politica  # default-src 'none' já veda
    assert "default-src 'none'" in politica


def test_estilo_nao_importa_fonte_por_import_externo(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "@import" not in corpo
    assert re.search(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com/', corpo)


# --- leitura do BigQuery -------------------------------------------------------


def _cliente_falso(linhas):
    consulta = SimpleNamespace(result=lambda: linhas)
    return SimpleNamespace(query=lambda sql, job_config=None: consulta)


def test_volumetria_do_bigquery_devolve_calendario_inteiro_terminando_hoje(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dia sem execução não existe na view: a tela precisa dele para mostrar o buraco."""
    from src.portal.dados import ProvedorBigQuery

    hoje = datetime.now(UTC).date()
    linhas = [
        SimpleNamespace(conector="ons_carga", dia=hoje, linhas_carregadas=40, execucoes_com_erro=0),
        SimpleNamespace(
            conector="ons_carga", dia=hoje - timedelta(days=2), linhas_carregadas=None, execucoes_com_erro=1
        ),
    ]
    monkeypatch.setattr("src.portal.dados.cliente", lambda: _cliente_falso(linhas))
    serie = ProvedorBigQuery().volumetria()[0]
    assert len(serie.dias) == len(serie.linhas) == len(serie.falhas) == 30
    assert serie.dias[-1] == hoje
    assert serie.linhas[-1] == 40
    assert serie.falhas[-3] == 1  # o dia da falha, sem linhas carregadas
    assert serie.linhas[-2] == 0  # ontem: sem execução nenhuma


def test_saude_do_bigquery_traz_execucoes_e_credencial(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.portal.dados import ProvedorBigQuery

    linha = SimpleNamespace(
        conector="tempook_ena_prevs",
        situacao="SEM_SUCESSO",
        ultimo_sucesso=None,
        minutos_desde_sucesso=None,
        intervalo_tipico_min=None,
        taxa_sucesso_30d=0.0,
        taxa_invalidas=None,
        linhas_carregadas_total=None,
        duracao_p95_seg=None,
        ultimo_erro="NotFound: 404 Secret x",
        execucoes_30d=4,
        aguardando_credencial=True,
    )
    monkeypatch.setattr("src.portal.dados.cliente", lambda: _cliente_falso([linha]))
    conector = ProvedorBigQuery().saude()[0]
    assert conector.aguardando_credencial is True
    assert conector.execucoes_30d == 4
    assert conector.linhas_carregadas_total == 0


def test_telao_com_muitas_fontes_usa_o_layout_denso() -> None:
    """hml tem 41 fontes: em duas colunas a linha dobra de altura e o telão corta o fim da lista."""
    muitas = tela_saude.montar([_conector(f"ons_fonte_{i:02d}") for i in range(41)], [])
    poucas = tela_saude.montar([_conector(f"ons_fonte_{i:02d}") for i in range(26)], [])
    assert "ad-sources--densa" in tela_saude.corpo(muitas, telao=True)
    assert "ad-sources--densa" not in tela_saude.corpo(poucas, telao=True)
    assert "ad-sources--densa" not in tela_saude.corpo(muitas)  # fora do telão a página rola


def test_layout_denso_do_telao_mantem_a_tira_na_mesma_linha_do_nome() -> None:
    from src.portal.estilo import ESTILO

    regra = [r for r in ESTILO.splitlines() if r.startswith(".ad-page--telao .ad-sources--densa .ad-row>summary")]
    assert regra
    assert '"ico name age strip chev"' in regra[0]  # vence a regra de container que desce a tira
    assert "--strip-w:calc(30 * 6px + 29 * 2px)" in ESTILO  # a variável derivada precisa ser refeita


# --- cache das leituras --------------------------------------------------------


class _BaseContada:
    """Conta quantas vezes o BigQuery seria consultado."""

    def __init__(self) -> None:
        self.chamadas: list[str] = []
        self.falhar = False

    def saude(self):
        self.chamadas.append("saude")
        if self.falhar:
            raise RuntimeError("bigquery fora")
        return [_conector("ons_carga")]

    def volumetria(self, dias=30):
        self.chamadas.append(f"volumetria{dias}")
        return []


def _com_cache(ttl=300):
    from src.portal.dados import ProvedorComCache

    base = _BaseContada()
    tempo = {"t": 0.0, "dia": datetime(2026, 10, 2, 12, 0, tzinfo=UTC)}
    cache = ProvedorComCache(
        base, ttl, relogio=lambda: tempo["t"], agora=lambda: tempo["dia"] + timedelta(seconds=tempo["t"])
    )
    return cache, base, tempo


def test_cache_evita_consultar_o_bigquery_de_novo_dentro_do_prazo() -> None:
    cache, base, tempo = _com_cache()
    cache.saude()
    tempo["t"] = 299
    cache.saude()
    assert base.chamadas == ["saude"]  # o telão pede a cada 20 s e o BigQuery foi consultado uma vez


def test_cache_expira_depois_do_prazo() -> None:
    cache, base, tempo = _com_cache()
    cache.saude()
    tempo["t"] = 301
    cache.saude()
    assert base.chamadas == ["saude", "saude"]


def test_argumento_diferente_e_outra_leitura() -> None:
    cache, base, _ = _com_cache()
    cache.volumetria(30)
    cache.volumetria(7)
    cache.volumetria(30)
    assert base.chamadas == ["volumetria30", "volumetria7"]


def test_erro_nao_e_guardado() -> None:
    cache, base, _ = _com_cache()
    base.falhar = True
    with pytest.raises(RuntimeError):
        cache.saude()
    base.falhar = False
    assert cache.saude()  # a falha de agora não vira resposta ruim pelos próximos minutos
    assert base.chamadas == ["saude", "saude"]


def test_consultado_em_e_a_hora_da_leitura_nao_a_da_pagina() -> None:
    cache, _, tempo = _com_cache()
    assert cache.consultado_em("saude") is None
    cache.saude()
    tempo["t"] = 120  # a página é montada dois minutos depois, com o dado do cache
    cache.saude()
    assert cache.consultado_em("saude") == datetime(2026, 10, 2, 12, 0, tzinfo=UTC)


def test_consultado_em_toma_a_leitura_mais_antiga_das_pedidas() -> None:
    cache, _, tempo = _com_cache()
    cache.saude()
    tempo["t"] = 60
    cache.volumetria()
    assert cache.consultado_em("saude", "volumetria") == datetime(2026, 10, 2, 12, 0, tzinfo=UTC)
    assert cache.consultado_em("volumetria") == datetime(2026, 10, 2, 12, 1, tzinfo=UTC)


def test_tela_mostra_a_hora_em_que_o_dado_foi_lido(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    provedor = _provedor(saude=[_conector("ons_carga")])
    provedor.consultado_em = lambda *leituras: datetime(2026, 10, 2, 17, 32, tzinfo=UTC)
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: provedor)
    assert ">14:32</time> (Brasília)" in cliente.get("/lake").get_data(as_text=True)


def test_provedor_real_usa_cache_e_zero_desliga(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.core.config import get_settings
    from src.portal import dados
    from src.portal.dados import ProvedorBigQuery, ProvedorComCache, obter_provedor

    monkeypatch.setenv("PORTAL_PROVEDOR", "bigquery")
    monkeypatch.setattr(dados, "_COM_CACHE", None)
    get_settings.cache_clear()
    assert isinstance(obter_provedor(), ProvedorComCache)
    assert obter_provedor() is obter_provedor()  # um só, para o cache valer entre requisições
    monkeypatch.setenv("PORTAL_CACHE_SEGUNDOS", "0")
    get_settings.cache_clear()
    assert isinstance(obter_provedor(), ProvedorBigQuery)
    get_settings.cache_clear()
