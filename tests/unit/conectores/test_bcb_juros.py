"""Conector BCB juros (Selic e CDI) — parsing, rotulagem da série e ciclo sem rede.

Payload real do SGS, colhido em 14/09 para janeiro de 2026. As duas séries vêm
com o mesmo valor: o CDI segue a Selic e coincide com ela em quase todo o
histórico recente. Por isso os testes conferem o **rótulo** da série, e não o
valor — trocar 11 por 12 no código não mudaria um único número.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from src.conectores.bcb_juros import SERIES, BcbJuros, TaxaJuros
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "bcb_juros.json"


@pytest.fixture
def payload():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture
def conector(monkeypatch, payload):
    """Conector com a chamada HTTP substituída pela fixture, série a série."""
    monkeypatch.setattr("src.conectores.bcb_juros.criar_sessao", lambda: None)
    monkeypatch.setattr(
        "src.conectores.bcb_juros.get_json",
        lambda _sessao, url, params=None: payload[url.split("sgs.")[1].split("/")[0]],
    )
    return BcbJuros()


def test_as_duas_series_do_b1_estao_no_conector():
    """Selic e CDI foram nomeadas no B1; o conector cobre as duas de uma vez."""
    assert set(SERIES) == {"selic", "cdi"}


def test_transformar_converte_data_brasileira_e_rotula_a_serie(conector):
    registro = conector.transformar({"data": "02/01/2026", "valor": "0.055131", "serie": "selic"})

    assert registro["data_referencia"] == "2026-01-02"  # não 01 de fevereiro
    validado = TaxaJuros.model_validate(registro)
    assert validado.data_referencia == date(2026, 1, 2)
    assert validado.serie == "selic"
    assert float(validado.taxa_percentual_dia) == pytest.approx(0.055131)


def test_extrair_marca_cada_registro_com_a_sua_serie(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31")))

    assert len(registros) == 12  # 6 dias úteis × 2 séries
    series = [r["serie"] for r in registros]
    assert series.count("selic") == 6
    assert series.count("cdi") == 6


def test_serie_desconhecida_e_rejeitada():
    with pytest.raises(ValueError):
        TaxaJuros.model_validate({"data_referencia": "2026-01-02", "serie": "ipca", "taxa_percentual_dia": 0.05})


def test_taxa_negativa_e_rejeitada():
    with pytest.raises(ValueError):
        TaxaJuros.model_validate({"data_referencia": "2026-01-02", "serie": "selic", "taxa_percentual_dia": -0.01})


def test_taxa_diaria_absurda_e_rejeitada():
    """1% ao dia é ~1.100% ao ano. Valor assim é erro da origem, não juro."""
    with pytest.raises(ValueError):
        TaxaJuros.model_validate({"data_referencia": "2026-01-02", "serie": "selic", "taxa_percentual_dia": 5})


def test_ingerir_em_dry_run_valida_sem_gravar(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 12
    assert execucao.linhas_invalidas == 0
    assert execucao.linhas_carregadas == 0  # dry-run não carrega


def test_janela_longa_e_quebrada_pelo_limite_da_api(conector, monkeypatch):
    """O SGS recusa mais de 10 anos de série diária numa requisição."""
    chamadas = []
    monkeypatch.setattr(
        "src.conectores.bcb_juros.get_json",
        lambda _s, _u, params=None: chamadas.append(params) or [],
    )

    conector.ingerir(Janela.de_texto("2010-01-01", "2026-01-31"))

    assert len(chamadas) > len(SERIES), "16 anos deveriam ser particionados"


def test_dia_sem_publicacao_devolve_lista_vazia_sem_falhar(conector, monkeypatch):
    """Fim de semana e feriado: o SGS devolve `[]`, e isso é sucesso com zero linhas."""
    monkeypatch.setattr("src.conectores.bcb_juros.get_json", lambda *_a, **_k: [])

    execucao = conector.ingerir(Janela.de_texto("2026-01-03", "2026-01-04"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 0


def test_registro_invalido_nao_derruba_a_ingestao(conector, monkeypatch):
    monkeypatch.setattr(
        "src.conectores.bcb_juros.get_json",
        lambda *_a, **_k: [
            {"data": "02/01/2026", "valor": "0.055131"},
            {"data": "05/01/2026", "valor": ""},  # série sem valor publicado
        ],
    )

    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))

    assert execucao.linhas_extraidas == 4  # 2 registros × 2 séries
    assert execucao.linhas_invalidas == 2


def test_erro_na_fonte_encerra_a_execucao_como_erro(conector, monkeypatch):
    def explode(*_args, **_kwargs):
        raise ConnectionError("timeout no SGS")

    monkeypatch.setattr("src.conectores.bcb_juros.get_json", explode)

    with pytest.raises(ConnectionError):
        conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-05"))
