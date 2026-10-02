"""A tela de custo não afirma o que não sabe (02/10).

Com dado real de `hml` a tela mostrava "1 fonte em produção", "100% Não classificado" e uma
projeção de 2 dias esticada para 31. Aqui ficam as regras que impedem isso, e a que faz o
custo de armazenamento aparecer.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from src.core.config import Settings
from src.portal.app import app
from src.portal.custo import (
    DIAS_MINIMOS_PARA_PROJETAR,
    SEM_ROTULO,
    ConsultaCara,
    CustoDia,
    CustoFonte,
    Orcamento,
    PainelCusto,
)
from src.portal.dados import ProvedorSimulado, SaudeConector, montar_painel_de_custo


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)
    return app.test_client()


def _linha(dia, fonte, consulta, *, query="0", armazenamento="0", bytes_=0, linhas=0):
    return SimpleNamespace(
        dia=dia,
        fonte=fonte,
        camada="gold",
        consulta=consulta,
        execucoes=1,
        bytes_varridos=bytes_,
        custo_query_usd=Decimal(query),
        custo_armazenamento_usd=Decimal(armazenamento),
        linhas_carregadas=linhas,
        variacao_vs_media=0.0,
    )


def _painel(*, dias_decorridos=2, fontes=None, ndias=8, orcado="20"):
    fontes = fontes or [CustoFonte(SEM_ROTULO, Decimal("2.68"), Decimal(0), 10_000, 0)]
    dias = [
        CustoDia(
            date(2026, 9, 25 + i) if 25 + i <= 30 else date(2026, 10, i - 5), Decimal("0.3"), Decimal(0), Decimal(0)
        )
        for i in range(ndias)
    ]
    consultas = [ConsultaCara("SELECT", SEM_ROTULO, "gold", 4, 5_000, Decimal("0.4"), 0.0)]
    orc = Orcamento(date(2026, 10, 1), Decimal(orcado), Decimal("0.9593"), dias_decorridos, 31)
    return PainelCusto(dias=dias, fontes=fontes, consultas=consultas, orcamento=orc)


def _servir(monkeypatch, painel, *, carregando=3):
    saude = [SaudeConector(f"ons_f{i}", "OK", None, 5, 1440, 1.0, 0.0, 10, 1.0) for i in range(carregando)]
    saude = [SaudeConector(c.conector, c.situacao, date(2026, 10, 1), 5, 1440, 1.0, 0.0, 10, 1.0) for c in saude] + [
        SaudeConector("hubspot_negocios", "SEM_SUCESSO", None, None, None, 0.0, None, 0, None)
    ]
    base = ProvedorSimulado()
    provedor = SimpleNamespace(
        custo=lambda dias=30: painel,
        saude=lambda: saude,
        painel=base.painel,
        volumetria=lambda dias=30: [],
        indicadores=lambda meses=12: [],
    )
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: provedor)


# --- o modelo ------------------------------------------------------------------


def test_projecao_so_vale_com_dias_suficientes_no_mes() -> None:
    antes = Orcamento(date(2026, 10, 1), Decimal(20), Decimal(1), DIAS_MINIMOS_PARA_PROJETAR - 1, 31)
    depois = Orcamento(date(2026, 10, 1), Decimal(20), Decimal(1), DIAS_MINIMOS_PARA_PROJETAR, 31)
    assert not antes.projecao_confiavel
    assert depois.projecao_confiavel


def test_parcela_sem_rotulo_e_a_fatia_do_custo_sem_fonte() -> None:
    fontes = [
        CustoFonte(SEM_ROTULO, Decimal("0.9"), Decimal(0), 0, 0),
        CustoFonte("ons_carga", Decimal("0.1"), Decimal(0), 0, 0),
    ]
    assert _painel(fontes=fontes).parcela_sem_rotulo == pytest.approx(0.9)
    assert _painel(fontes=[CustoFonte("ons_carga", Decimal(1), Decimal(0), 0, 0)]).parcela_sem_rotulo == 0.0


def test_parcela_sem_rotulo_de_conta_zerada_nao_divide_por_zero() -> None:
    assert _painel(fontes=[CustoFonte(SEM_ROTULO, Decimal(0), Decimal(0), 0, 0)]).parcela_sem_rotulo == 0.0


@pytest.mark.parametrize(
    ("dia", "esperado"), [(date(2026, 10, 2), 31), (date(2026, 9, 30), 30), (date(2027, 2, 3), 28)]
)
def test_dias_do_mes_vem_do_calendario_nao_de_31_fixo(dia, esperado) -> None:
    painel = montar_painel_de_custo([_linha(dia, "ons_carga", "SELECT", query="0.01", bytes_=10)], Decimal(20))
    assert painel.orcamento.dias_do_mes == esperado


def test_armazenamento_aparece_por_tabela_e_nao_vira_consulta() -> None:
    """Antes a view juntava o armazenamento pelo rótulo do job: sem rótulo, ele sumia."""
    dia = date(2026, 10, 1)
    linhas = [
        _linha(dia, SEM_ROTULO, "SELECT", query="0.01", bytes_=1000),
        _linha(dia, "ons_carga", "armazenamento", armazenamento="0.005"),
        _linha(dia, "bcb_juros", "armazenamento", armazenamento="0.001"),
    ]
    painel = montar_painel_de_custo(linhas, Decimal(20))
    por_fonte = {f.fonte: f for f in painel.fontes}
    assert por_fonte["ons_carga"].armazenamento_usd == Decimal("0.005")
    assert por_fonte["bcb_juros"].armazenamento_usd == Decimal("0.001")
    assert [c.rotulo for c in painel.consultas] == ["SELECT"]  # armazenamento não é consulta
    assert painel.dias[0].armazenamento_usd == Decimal("0.006")  # e entra no gasto do dia


def test_orcamento_do_portal_parte_da_referencia_da_alup() -> None:
    assert Settings.model_fields["portal_orcamento_mensal_usd"].default == 20.0


# --- a tela --------------------------------------------------------------------


def test_resumo_diz_que_nao_sabe_atribuir_quando_o_custo_nao_tem_rotulo(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel())
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "Atribuição por fonte indisponível" in corpo
    assert "Maior domínio" not in corpo
    assert "Não classificado" not in corpo.split("</style>", 1)[1]
    assert "Sem atribuição por fonte" in corpo  # e a lista de fontes que mais custam também


def test_resumo_mostra_o_ranking_quando_ha_rotulo(cliente, monkeypatch) -> None:
    fontes = [
        CustoFonte("ons_carga", Decimal("2"), Decimal(0), 10, 10),
        CustoFonte("bcb_juros", Decimal("1"), Decimal(0), 10, 10),
    ]
    _servir(monkeypatch, _painel(fontes=fontes))
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "Maior domínio" in corpo
    assert "Atribuição por fonte indisponível" not in corpo


def test_fontes_em_producao_conta_quem_carrega_nao_grupos_de_custo(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel(), carregando=3)
    corpo = cliente.get("/custo").get_data(as_text=True)
    resumo = corpo.split('id="dir">Resumo</h2>', 1)[1]
    assert "<dt>Fontes em produção</dt><dd>3</dd>" in resumo  # o Hubspot, sem sucesso, não conta


def test_projecao_nao_aparece_com_poucos_dias_no_mes(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel(dias_decorridos=2))
    corpo = cliente.get("/custo").get_data(as_text=True).split("</style>", 1)[1]
    assert "poucos dias no mês" in corpo
    assert "Projeção de fechamento" not in corpo
    assert "Custo mensal projetado" not in corpo


def test_projecao_aparece_com_dias_suficientes(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel(dias_decorridos=10))
    corpo = cliente.get("/custo").get_data(as_text=True).split("</style>", 1)[1]
    assert "Projeção de fechamento" in corpo
    assert "Custo mensal projetado" in corpo


def test_orcado_diz_de_onde_vem(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel())
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "referência da Alup" in corpo
    assert "US$ 20,00" in corpo


def test_grafico_diz_quantos_dias_realmente_tem(cliente, monkeypatch) -> None:
    _servir(monkeypatch, _painel(ndias=8))
    corpo = cliente.get("/custo").get_data(as_text=True)
    assert "composição · 8 dias" in corpo
    assert "composição · 30 dias" not in corpo
