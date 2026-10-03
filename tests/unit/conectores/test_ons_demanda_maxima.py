"""Conector ONS/demanda máxima diária por subsistema — CSV anual remoto, sem rede.

O que estes testes protegem, e que não é óbvio no código:

- a origem traz `id_subsistema` e `nom_subsistema` com **espaços** (`"SE "`,
  `" SUDESTE    "`); sem aparar, a sigla reprova e a Silver deduplicaria errado;
- a demanda integralizada (MWmed) e a instantânea (MW) são duas medidas, cada
  uma com o seu instante; vazio é nulo, nunca zero;
- ano sem arquivo é ignorado, mas a janela inteira sem arquivo falha alto.
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_demanda_maxima import DemandaMaxima, OnsDemandaMaxima
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_demanda_maxima_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsDemandaMaxima()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01")))

    assert len(registros) == 4
    assert {r["dat_referencia"] for r in registros} == {"2026-01-01"}


def test_janela_fora_do_arquivo_devolve_vazio(conector):
    assert list(conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30"))) == []


def test_transformar_apara_a_sigla_e_leva_as_duas_demandas(conector):
    linhas = conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01"))
    bruto = next(r for r in linhas if r["id_subsistema"].strip() == "SE")
    registro = DemandaMaxima.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.submercado == "SE"
    assert registro.nome_subsistema == "SUDESTE"
    assert registro.demanda_integralizada_mwmed == Decimal("48126.387")
    assert registro.instante_integralizada == datetime(2026, 1, 1, 21, 0)
    assert registro.demanda_instantanea_mw == Decimal("48722.59")
    assert registro.instante_instantanea == datetime(2026, 1, 1, 21, 11)


@pytest.mark.parametrize("sigla", ["SE ", "NE ", "N  ", "S  "])
def test_sigla_com_espacos_a_direita_e_aceita(sigla):
    assert DemandaMaxima.model_validate(_linha(submercado=sigla)).submercado == sigla.strip()


def test_sigla_desconhecida_e_rejeitada():
    with pytest.raises(ValidationError):
        DemandaMaxima.model_validate(_linha(submercado="SIN"))


def test_valor_vazio_vira_nulo_nunca_zero(conector):
    bruto = {
        "id_subsistema": "N  ",
        "nom_subsistema": " NORTE      ",
        "dat_referencia": "2026-01-03",
        "din_demandaintegralizada": "",
        "val_demandaintegralizada": "",
        "din_demandainstantanea": "2026-01-03 22:40:00",
        "val_demandainstantanea": "9141.481",
    }
    registro = DemandaMaxima.model_validate(conector.transformar(bruto))

    assert registro.demanda_integralizada_mwmed is None
    assert registro.instante_integralizada is None
    assert registro.demanda_instantanea_mw == Decimal("9141.481")


def test_demanda_negativa_e_rejeitada():
    with pytest.raises(ValidationError):
        DemandaMaxima.model_validate(_linha(demanda_instantanea_mw="-1"))


def test_janela_que_cruza_o_ano_baixa_os_dois_arquivos(conector, monkeypatch):
    anos = []

    def baixar(ano):
        anos.append(ano)
        return FIXTURE.read_text(encoding="utf-8") if ano == 2026 else None

    monkeypatch.setattr(conector, "_baixar_ano", baixar)

    registros = list(conector.extrair(Janela.de_texto("2025-12-20", "2026-01-01")))

    assert anos == [2025, 2026]
    assert len(registros) == 4


def test_ano_sem_arquivo_na_janela_com_outro_ano_publicado_e_ignorado(conector, monkeypatch, caplog):
    monkeypatch.setattr(
        conector, "_baixar_ano", lambda ano: FIXTURE.read_text(encoding="utf-8") if ano == 2026 else None
    )

    with caplog.at_level("WARNING"):
        registros = list(conector.extrair(Janela.de_texto("2025-12-31", "2026-01-01")))

    assert len(registros) == 4
    assert any("2025" in r.message for r in caplog.records)


def test_nenhum_ano_da_janela_publicado_falha_alto(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: None)

    with pytest.raises(RuntimeError, match="2023"):
        list(conector.extrair(Janela.de_texto("2023-01-01", "2023-01-31")))


def test_ingerir_valida_as_seis_linhas_do_arquivo(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-02"))

    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 0


def _linha(**sobrescritas):
    base = {
        "data_referencia": "2026-01-01",
        "submercado": "SE",
        "nome_subsistema": "SUDESTE",
        "demanda_integralizada_mwmed": "48126.387",
        "instante_integralizada": "2026-01-01T21:00:00",
        "demanda_instantanea_mw": "48722.59",
        "instante_instantanea": "2026-01-01T21:11:00",
    }
    return base | sobrescritas
