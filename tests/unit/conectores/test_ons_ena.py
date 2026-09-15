"""Conector ONS/ENA — CSV anual remoto, recorte pela janela, sem rede."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_ena import EnaDiario, OnsEna
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ena_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_ena.criar_sessao", lambda: None)
    conector = OnsEna()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01")))

    assert len(registros) == 4  # os 4 subsistemas naquele dia
    assert {r["ena_data"] for r in registros} == {"2026-01-01"}


def test_janela_maior_pega_os_dois_dias(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-02")))
    assert len(registros) == 9  # 8 válidas + a linha com mwmed negativo


def test_janela_fora_do_arquivo_devolve_vazio(conector):
    assert list(conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30"))) == []


def test_ano_sem_recurso_publicado_e_ignorado(conector, monkeypatch, caplog):
    import requests

    def _ausente(_ano):
        resposta = requests.Response()
        resposta.status_code = 404
        raise requests.exceptions.HTTPError(response=resposta)

    monkeypatch.setattr(conector, "_baixar_ano", _ausente)

    with caplog.at_level("WARNING"):
        registros = list(conector.extrair(Janela.de_texto("1970-01-01", "1970-01-02")))

    assert registros == []
    assert any("1970" in registro.message for registro in caplog.records)


def test_transformar_normaliza_o_trim_do_submercado(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-02", "2026-01-02")))
    bruto_norte = next(r for r in registros if r["id_subsistema"] == "N ")

    registro = EnaDiario.model_validate(conector.transformar(bruto_norte))

    assert registro.submercado == "N"
    assert registro.data_referencia == date(2026, 1, 2)
    assert registro.ena_bruta_mwmed == Decimal("3300.000")


def test_percentual_mlt_acima_de_cem_e_valido():
    """MLT é média de longo termo: ENA acima de 100% é ano úmido, não erro."""
    registro = EnaDiario.model_validate(
        {
            "data_referencia": "2026-01-01",
            "submercado": "S",
            "nome_subsistema": "Sul",
            "ena_bruta_mwmed": "5400.000",
            "ena_bruta_percentual_mlt": "120.5",
            "ena_armazenavel_mwmed": "5300.000",
            "ena_armazenavel_percentual_mlt": "118.2",
        }
    )
    assert registro.ena_bruta_percentual_mlt == Decimal("120.5")


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        EnaDiario.model_validate(
            {
                "data_referencia": "2026-01-02",
                "submercado": "XX",
                "nome_subsistema": "Inventado",
                "ena_bruta_mwmed": "100",
                "ena_bruta_percentual_mlt": "50",
                "ena_armazenavel_mwmed": "100",
                "ena_armazenavel_percentual_mlt": "50",
            }
        )


def test_mwmed_negativo_e_rejeitado():
    with pytest.raises(ValueError, match="negativo"):
        EnaDiario.model_validate(
            {
                "data_referencia": "2026-01-02",
                "submercado": "SE",
                "nome_subsistema": "Sudeste/Centro-Oeste",
                "ena_bruta_mwmed": "-50",
                "ena_bruta_percentual_mlt": "10",
                "ena_armazenavel_mwmed": "-40",
                "ena_armazenavel_percentual_mlt": "9",
            }
        )


def test_ingerir_conta_extraidas_e_invalidas(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 9
    assert execucao.linhas_invalidas == 1  # a linha com mwmed negativo
