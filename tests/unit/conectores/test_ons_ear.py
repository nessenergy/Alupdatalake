"""Conector ONS/EAR — CSV anual remoto, recorte pela janela, sem rede."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_ear import EarDiario, OnsEar
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ear_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_ear.criar_sessao", lambda: None)
    conector = OnsEar()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01")))

    assert len(registros) == 4  # os 4 subsistemas naquele dia
    assert {r["ear_data"] for r in registros} == {"2026-01-01"}


def test_janela_maior_pega_os_dois_dias(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-02")))
    assert len(registros) == 9  # 8 válidas + a linha de submercado desconhecido


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

    registro = EarDiario.model_validate(conector.transformar(bruto_norte))

    assert registro.submercado == "N"
    assert registro.data_referencia == date(2026, 1, 2)
    assert registro.ear_verificada_mwmes == Decimal("9500.000")


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        EarDiario.model_validate(
            {
                "data_referencia": "2026-01-02",
                "submercado": "XX",
                "nome_subsistema": "Inventado",
                "ear_max_mwmes": "1000",
                "ear_verificada_mwmes": "500",
                "ear_verificada_percentual": "50",
            }
        )


def test_percentual_fora_de_faixa_e_rejeitado():
    with pytest.raises(ValueError, match="percentual"):
        EarDiario.model_validate(
            {
                "data_referencia": "2026-01-02",
                "submercado": "SE",
                "nome_subsistema": "Sudeste/Centro-Oeste",
                "ear_max_mwmes": "1000",
                "ear_verificada_mwmes": "500",
                "ear_verificada_percentual": "150",
            }
        )


def test_ingerir_conta_extraidas_e_invalidas(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 9
    assert execucao.linhas_invalidas == 1  # a linha de submercado "XX"
