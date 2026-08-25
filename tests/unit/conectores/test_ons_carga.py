"""Conector ONS/carga — CSV anual remoto, recorte pela janela, sem rede."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_carga import CargaDiaria, OnsCarga
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_carga_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_carga.criar_sessao", lambda: None)
    conector = OnsCarga()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01")))

    assert len(registros) == 4  # os 4 subsistemas naquele dia
    assert {r["din_instante"] for r in registros} == {"2026-01-01"}


def test_janela_maior_pega_os_dois_dias(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-02")))
    assert len(registros) == 8


def test_janela_fora_do_arquivo_devolve_vazio(conector):
    assert list(conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30"))) == []


def test_janela_que_cruza_o_ano_baixa_cada_ano(conector, monkeypatch):
    anos = []
    monkeypatch.setattr(conector, "_baixar_ano", lambda ano: anos.append(ano) or "")

    list(conector.extrair(Janela.de_texto("2025-12-30", "2026-01-02")))

    assert anos == [2025, 2026]


def test_transformar_normaliza_carga_e_submercado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-01"))))
    registro = CargaDiaria.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.submercado in {"N", "NE", "S", "SE"}
    assert registro.carga_mwmed > Decimal(0)


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        CargaDiaria.model_validate(
            {
                "data_referencia": "2026-01-01",
                "submercado": "XX",
                "nome_subsistema": "Inventado",
                "carga_mwmed": "100",
            }
        )


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-02"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 8
    assert execucao.linhas_invalidas == 0
