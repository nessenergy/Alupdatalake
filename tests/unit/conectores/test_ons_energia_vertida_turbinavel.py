"""Conector ONS — energia vertida turbinável: CSV mensal, sem rede.

A fixture tem linhas reais do arquivo de 09/2026 (Balbina, Belo Monte vertendo, Baixo Iguaçu
com decimais longos, rio com acento).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_energia_vertida_turbinavel import EnergiaVertidaTurbinavel, OnsEnergiaVertidaTurbinavel
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_energia_vertida_turbinavel_202609.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_mensal.criar_sessao", lambda: None)
    conector = OnsEnergiaVertidaTurbinavel()
    monkeypatch.setattr(
        conector, "_abrir_mes", lambda _ano, _mes: iter(FIXTURE.read_text(encoding="utf-8").splitlines())
    )
    return conector


def _registros(conector, inicio="2026-09-01", fim="2026-09-30"):
    return [
        EnergiaVertidaTurbinavel.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto(inicio, fim))
    ]


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01")))) == 3
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-30")))) == 6


def test_a_serie_mensal_comeca_em_2024_01_e_antes_o_arquivo_e_anual():
    """Confirmado no catálogo em 02/10/2026: 2015 a 2023 são um CSV por ano (~190 MB cada)."""
    assert OnsEnergiaVertidaTurbinavel.primeiro_mes == (2024, 1)


def test_janela_de_2023_e_recusada(conector):
    with pytest.raises(ValueError, match="anual"):
        list(conector.extrair(Janela.de_texto("2023-11-01", "2024-01-31")))


def test_transformar_nomeia_as_colunas_e_deriva_data_e_instante(conector):
    balbina = _registros(conector, "2026-09-01", "2026-09-01")[0]

    assert balbina.data_referencia == date(2026, 9, 1)
    assert balbina.instante == datetime(2026, 9, 1, 0)  # início da hora, ao contrário do hidrológico
    assert balbina.submercado == "N"
    assert balbina.bacia == "AMAZONAS"
    assert balbina.rio == "UATUMA"
    assert balbina.agente == "AXIA NORTE"
    assert balbina.reservatorio == "BALBINA"
    assert balbina.codigo_usina_modelo == 277
    assert balbina.geracao_mwmed == Decimal("244.451")
    assert balbina.disponibilidade_mwmed == Decimal("250.0")


def test_acentos_do_utf8_sao_preservados(conector):
    sao_francisco = next(r for r in _registros(conector) if r.reservatorio == "APOLONIO SALES")
    assert sao_francisco.rio == "SÃO FRANCISCO"


def test_vertimento_turbinavel_com_decimais_longos(conector):
    """O ONS publica float (0.0007989898989898991); o runner ajusta às 9 casas do NUMERIC."""
    baixo_iguacu = next(r for r in _registros(conector) if r.reservatorio == "BAIXO IGUACU")

    assert baixo_iguacu.energia_vertida_turbinavel_mwmed == Decimal("4.325731313131314")
    assert baixo_iguacu.produtividade_mw_por_m3s == Decimal("0.0007989898989898991")


def test_usina_vertendo_o_que_poderia_turbinar(conector):
    belo_monte = next(r for r in _registros(conector) if r.reservatorio == "BELO MONTE")

    assert belo_monte.geracao_mwmed == Decimal("0.0")
    assert belo_monte.energia_vertida_turbinavel_mwmed == Decimal("139.145")
    assert belo_monte.vazao_vertida_turbinavel_m3s == Decimal("170.0")


def test_codigo_de_usina_vazio_e_rejeitado(conector):
    """O código identifica a usina na chave da Silver: sem ele a linha é inválida, não NULL."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["cod_usina"] = ""

    with pytest.raises(ValidationError):
        EnergiaVertidaTurbinavel.model_validate(conector.transformar(bruto))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-09-01", "2026-09-30"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 0
