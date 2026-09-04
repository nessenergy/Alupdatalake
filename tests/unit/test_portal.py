"""Portal MVP: o que a tela mostra e o que ela não deixa passar.

Escopo em `docs/arquitetura/decisoes/005-escopo-do-portal-mvp.md`.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from src.core.config import get_settings
from src.portal import app as portal_app
from src.portal.app import CABECALHO_IDENTIDADE, app
from src.portal.dados import Painel, ProvedorSimulado, obter_provedor


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)
    return app.test_client()


def test_pagina_mostra_a_view_e_as_linhas(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "cambio_mensal" in corpo
    assert "2026-08" in corpo
    assert "5.4501" in corpo


def test_pagina_diz_quando_foi_a_ultima_ingestao(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "26/08/2026 09:00" in corpo
    assert "bcb_cambio_ptax" in corpo


def test_dado_simulado_e_rotulado_como_tal(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "Dados de exemplo" in corpo  # ninguém pode confundir com dado do lake


def test_identidade_vem_do_cabecalho_do_iap(cliente) -> None:
    corpo = cliente.get("/", headers={CABECALHO_IDENTIDADE: "accounts.google.com:fulano@alupar.com.br"}).get_data(
        as_text=True
    )
    assert "fulano@alupar.com.br" in corpo
    assert "accounts.google.com" not in corpo


def test_sem_cabecalho_a_tela_diz_que_nao_ha_autenticacao(cliente) -> None:
    assert "não autenticado" in cliente.get("/").get_data(as_text=True)


def test_conteudo_de_celula_e_escapado(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    malicioso = Painel(
        view="cambio_mensal",
        colunas=["nota"],
        linhas=[{"nota": "<script>alert(1)</script>"}],
        ultima_ingestao=datetime(2026, 8, 26, tzinfo=UTC),
        fonte_ultima_ingestao="<b>x</b>",
    )
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: type("P", (), {"painel": lambda _s, _v: malicioso})())
    corpo = cliente.get("/").get_data(as_text=True)
    assert "<script>" not in corpo
    assert "&lt;script&gt;" in corpo


def test_celula_vazia_vira_travessao_nao_none(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    vazio = Painel(
        view="cambio_mensal",
        colunas=["valor"],
        linhas=[{"valor": None}],
        ultima_ingestao=None,
        fonte_ultima_ingestao=None,
    )
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: type("P", (), {"painel": lambda _s, _v: vazio})())
    corpo = cliente.get("/").get_data(as_text=True)
    assert "<td>—</td>" in corpo
    assert "None" not in corpo
    assert "Nenhuma ingestão registrada" in corpo


def test_saude_responde_sem_tocar_no_bigquery(cliente) -> None:
    assert cliente.get("/saude").get_json() == {"status": "ok"}


def test_provedor_padrao_e_o_simulado_enquanto_gcp_nao_existe() -> None:
    get_settings.cache_clear()
    assert isinstance(obter_provedor(), ProvedorSimulado)


def test_nome_de_view_invalido_nao_chega_na_query() -> None:
    from src.portal.dados import ProvedorBigQuery

    with pytest.raises(ValueError, match="view inválido"):
        ProvedorBigQuery().painel("gold`; DROP TABLE x --")


def test_lake_mostra_cada_conector_com_situacao(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    for conector in ("bcb_cambio_ptax", "ons_carga", "aneel_siga", "ibge_ipca", "hubspot_negocios"):
        assert conector in corpo
    assert "3 de 5 conectores em dia" in corpo  # aneel atrasada, hubspot sem token


def test_lake_destaca_atraso_e_erro(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "atrasada" in corpo
    assert "nunca teve sucesso" in corpo
    assert "pendência A9" in corpo  # o erro da última execução aparece na tela


def test_lake_formata_numero_para_leitura_humana(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "75.789" in corpo  # separador de milhar brasileiro
    assert "há 9 dias" in corpo  # 13.055 minutos, não "13055 min"
    assert "97,0%" in corpo  # taxa com vírgula decimal


def test_lake_sem_conector_nao_quebra(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.portal.app.obter_provedor",
        lambda: type("P", (), {"saude": lambda _s: [], "volumetria": lambda _s, dias=30: []})(),
    )
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "Nenhum conector executou ainda" in corpo


def test_lake_escapa_mensagem_de_erro(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    from src.portal.dados import SaudeConector

    ruim = SaudeConector("x", "OK", None, None, None, None, None, 0, None, "<img src=x onerror=alert(1)>")
    monkeypatch.setattr(
        "src.portal.app.obter_provedor",
        lambda: type("P", (), {"saude": lambda _s: [ruim], "volumetria": lambda _s, dias=30: []})(),
    )
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "<img" not in corpo
    assert "&lt;img" in corpo


def test_lake_desenha_serie_temporal_por_conector(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert corpo.count("<polyline") == 4  # os 4 com dado; hubspot sem token não desenha
    assert "Linhas por dia · 30 dias" in corpo
    assert "linhas carregadas nos últimos 30 dias" in corpo


def test_grafico_tem_alternativa_em_texto(cliente) -> None:
    corpo = cliente.get("/lake").get_data(as_text=True)
    assert "Ver os números em tabela" in corpo
    assert "25.263" in corpo  # o pico semanal da ANEEL aparece na tabela


def test_cor_da_serie_segue_o_conector_nao_a_posicao() -> None:
    from src.portal.grafico import cor_do_conector

    ordem = ["aneel_siga", "bcb_cambio_ptax", "hubspot_negocios", "ibge_ipca", "ons_carga"]
    antes = cor_do_conector("ons_carga", ordem)
    assert cor_do_conector("ons_carga", ordem) == antes
    assert cor_do_conector("aneel_siga", ordem) != antes


def test_ponto_do_grafico_tem_rotulo_para_hover_e_leitor_de_tela() -> None:
    from src.portal.dados import ProvedorSimulado
    from src.portal.grafico import area

    serie = next(s for s in ProvedorSimulado().volumetria() if s.conector == "aneel_siga")
    svg = area(serie, "#8B2A78")
    assert svg.count("<title>") == len(serie.linhas)
    assert "25.263 linhas" in svg
    assert 'aria-label="aneel_siga: 101.052 linhas em 30 dias"' in svg


def test_area_de_serie_vazia_nao_quebra() -> None:
    from src.portal.dados import SerieVolumetria
    from src.portal.grafico import area

    assert "<polyline" not in area(SerieVolumetria("x", [], []), "#8B2A78")


# --- custo de nuvem (rota /custo) -------------------------------------------


def test_custo_traz_as_tres_visoes(cliente) -> None:
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "Operacional" in corpo
    assert "Orçamento" in corpo
    assert "Diretoria" in corpo


def test_custo_rotula_o_dado_como_exemplo(cliente) -> None:
    assert "Nenhum valor desta tela veio de uma fatura" in cliente.get("/custo").get_data(as_text=True)


def test_fonte_que_nunca_carregou_nao_custa() -> None:
    """Sem tabela não há o que varrer — o Hubspot está nesse estado (A9)."""
    from src.portal.dados import ProvedorSimulado

    fontes = {f.fonte: f for f in ProvedorSimulado().custo().fontes}
    assert fontes["hubspot_negocios"].total_usd == 0
    assert fontes["hubspot_negocios"].usd_por_milhao_de_linhas is None


def test_custo_nao_e_arredondado_a_cada_dia() -> None:
    """Trinta parcelas de meio centavo não podem virar trinta zeros."""
    from src.portal.dados import ProvedorSimulado

    painel = ProvedorSimulado().custo()
    assert painel.total_usd > 0
    assert all(dia.total_usd >= 0 for dia in painel.dias)
    # se houvesse arredondamento por dia, a soma bateria exatamente em centavos
    assert painel.total_usd != painel.total_usd.quantize(Decimal("0.01"))


def test_minimo_faturado_por_consulta_vale_mesmo_varrendo_quase_nada() -> None:
    from src.portal.custo import MINIMO_BYTES_FATURADOS, custo_de_query

    assert custo_de_query(1) == custo_de_query(MINIMO_BYTES_FATURADOS)
    assert custo_de_query(1, consultas=3) == custo_de_query(MINIMO_BYTES_FATURADOS * 3)


def test_consultas_sao_ordenadas_por_custo_nao_por_byte() -> None:
    """Com mínimo por consulta em vigor, varrer mais não é custar mais."""
    from src.portal.dados import ProvedorSimulado

    consultas = ProvedorSimulado().custo().consultas
    assert [c.custo_usd for c in consultas] == sorted((c.custo_usd for c in consultas), reverse=True)
    mais_varrida = max(consultas, key=lambda c: c.bytes_varridos)
    assert mais_varrida is not consultas[0]


def test_varredura_integral_e_marcada_como_anomala(cliente) -> None:
    from src.portal.dados import ProvedorSimulado

    anomalas = [c for c in ProvedorSimulado().custo().consultas if c.anomala]
    assert [c.fonte for c in anomalas] == ["aneel_siga"]
    assert "varredura integral" in cliente.get("/custo").get_data(as_text=True)


def test_orcamento_projeta_o_fechamento_do_mes() -> None:
    from src.portal.custo import Orcamento

    o = Orcamento(date(2026, 8, 1), Decimal("100"), Decimal("50"), dias_decorridos=10, dias_do_mes=30)
    assert o.projetado_usd == Decimal("150")
    assert o.estoura


def test_orcamento_sem_dia_decorrido_nao_divide_por_zero() -> None:
    from src.portal.custo import Orcamento

    o = Orcamento(date(2026, 8, 1), Decimal("100"), Decimal("0"), dias_decorridos=0, dias_do_mes=30)
    assert o.projetado_usd == 0
    assert not o.estoura


def test_dominio_de_negocio_e_provisorio_ate_o_questionario_de_gaps(cliente) -> None:
    from src.portal.dados import ProvedorSimulado

    dominios = dict(ProvedorSimulado().custo().por_dominio)
    assert "Macroeconomia" in dominios  # BCB + IBGE
    assert "provisório" in cliente.get("/custo").get_data(as_text=True)


def test_valor_pequeno_nao_vira_zero_na_formatacao() -> None:
    from src.portal.grafico import usd

    assert usd(Decimal("0.0068")) == "US$ 0,0068"
    assert usd(Decimal("1234.5")) == "US$ 1.234,50"


def test_grafico_de_custo_vazio_nao_quebra() -> None:
    from src.portal.grafico import barras_custo

    assert barras_custo([]) == ""


def test_cada_barra_do_custo_tem_rotulo_para_leitor_de_tela() -> None:
    from src.portal.dados import ProvedorSimulado
    from src.portal.grafico import barras_custo

    svg = barras_custo(ProvedorSimulado().custo().dias)
    assert svg.count("<title>") == 30
    assert "US$" in svg


# ------------------------------------------------- falha fechado sem identidade
# A ADR 005 diz que a autenticação é da plataforma. Delegar não é confiar
# cegamente: se o IAP não identificar ninguém, o portal recusa em vez de servir.


def _cliente_em_modo_real(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PORTAL_PROVEDOR", "bigquery")
    get_settings.cache_clear()
    return app.test_client()


def test_modo_real_sem_identidade_responde_403(monkeypatch: pytest.MonkeyPatch) -> None:
    """Deploy com --allow-unauthenticated ou IAP mal configurado não serve dado."""
    resposta = _cliente_em_modo_real(monkeypatch).get("/")
    assert resposta.status_code == 403
    assert b"Acesso restrito" in resposta.data


@pytest.mark.parametrize("rota", ["/", "/lake", "/custo"])
def test_a_trava_vale_para_toda_tela_com_dado(monkeypatch: pytest.MonkeyPatch, rota: str) -> None:
    assert _cliente_em_modo_real(monkeypatch).get(rota).status_code == 403


def test_health_check_responde_sem_identidade(monkeypatch: pytest.MonkeyPatch) -> None:
    """O Cloud Run chama /saude fora de qualquer sessão de usuário."""
    assert _cliente_em_modo_real(monkeypatch).get("/saude").status_code == 200


def test_modo_real_com_identidade_do_iap_passa(monkeypatch: pytest.MonkeyPatch) -> None:
    """Testa o portão isolado: com identidade ele não interrompe a requisição.

    Exercitar a rota inteira exigiria BigQuery real — o que este teste não quer
    nem precisa. O que importa aqui é a decisão do `before_request`.
    """
    monkeypatch.setenv("PORTAL_PROVEDOR", "bigquery")
    get_settings.cache_clear()
    cabecalho = {"X-Goog-Authenticated-User-Email": "accounts.google.com:pessoa@alupar.com"}
    with app.test_request_context("/", headers=cabecalho):
        assert portal_app.exigir_identidade() is None, "identidade presente não pode ser recusada"


def test_modo_simulado_nao_e_travado(cliente) -> None:
    """Desenvolvimento local não tem IAP na frente e não serve dado real."""
    assert cliente.get("/").status_code == 200


# ------------------------------------------------- endurecimento das respostas


def test_toda_resposta_leva_os_cabecalhos_de_seguranca(cliente) -> None:
    resposta = cliente.get("/saude")

    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["X-Frame-Options"] == "DENY"
    assert resposta.headers["Referrer-Policy"] == "no-referrer"
    assert resposta.headers["Cache-Control"] == "no-store"
    assert "noindex" in resposta.headers["X-Robots-Tag"]


def test_politica_proibe_script_porque_o_portal_nao_tem_nenhum(cliente) -> None:
    """`default-src 'none'` sem `script-src` é afirmação, não descrição."""
    csp = cliente.get("/saude").headers["Content-Security-Policy"]

    assert "default-src 'none'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "'unsafe-eval'" not in csp
    assert "script-src" not in csp, "sem script-src explícito, herda o default-src 'none'"


def test_recusa_por_falta_de_identidade_tambem_e_endurecida(cliente, monkeypatch) -> None:
    """403 é resposta como outra e não pode sair sem cabeçalho."""
    from src.core import config

    monkeypatch.setattr(config, "get_settings", lambda: _cfg_real())
    from src.portal import app as modulo

    monkeypatch.setattr(modulo, "get_settings", lambda: _cfg_real())

    resposta = cliente.get("/")

    assert resposta.status_code == 403
    assert resposta.headers["X-Content-Type-Options"] == "nosniff"
    assert resposta.headers["Content-Security-Policy"].startswith("default-src 'none'")


def _cfg_real():
    """Cópia das settings com o provedor real, para acionar a trava do IAP."""
    from src.core.config import Settings

    return Settings(portal_provedor="bigquery")


def test_falha_do_provedor_nao_vaza_o_motivo_na_tela(cliente, monkeypatch) -> None:
    """Erro do BigQuery traz projeto, dataset e por vezes o SQL — nada disso vai à tela."""
    from src.portal import app as modulo

    def explodir():
        raise RuntimeError("403 Access Denied: Table alupdata-dev:bronze._execucoes")

    monkeypatch.setattr(modulo, "obter_provedor", explodir)
    # TESTING=True propaga a exceção e passaria por cima do handler; aqui
    # queremos justamente exercitar o handler, como em produção.
    cliente.application.config.update(TESTING=False, PROPAGATE_EXCEPTIONS=False)
    try:
        resposta = cliente.get("/")
        corpo = resposta.get_data(as_text=True)
    finally:
        cliente.application.config.update(TESTING=True, PROPAGATE_EXCEPTIONS=None)

    assert resposta.status_code == 500
    assert "alupdata-dev" not in corpo
    assert "Access Denied" not in corpo
    assert "registrada" in corpo
