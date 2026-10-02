"""Conector ONS — dados hidrológicos por reservatório, base horária: CSV mensal, sem rede.

A fixture tem linhas reais do arquivo de 09/2026 (campos de texto com espaço à direita,
volume útil negativo, colunas vazias, a hora fim do dia em 23:59:00).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_dados_hidrologicos import DadoHidrologico, OnsDadosHidrologicos
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_dados_hidrologicos_202609.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_mensal.criar_sessao", lambda: None)
    conector = OnsDadosHidrologicos()
    monkeypatch.setattr(
        conector, "_abrir_mes", lambda _ano, _mes: iter(FIXTURE.read_text(encoding="utf-8").splitlines())
    )
    return conector


def _registros(conector, inicio="2026-09-01", fim="2026-09-30"):
    return [
        DadoHidrologico.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(inicio, fim))
    ]


def test_extrai_apenas_as_linhas_dentro_da_janela(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01")))) == 7
    assert len(list(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-30")))) == 10


def test_a_serie_mensal_comeca_em_2010_01():
    assert OnsDadosHidrologicos.primeiro_mes == (2010, 1)


def test_texto_com_espaco_a_direita_e_aparado(conector):
    balbina = _registros(conector, "2026-09-01", "2026-09-01")[0]

    assert balbina.submercado == "N"  # veio "N "
    assert balbina.tipo_reservatorio == "Reservatório com Usina"
    assert balbina.bacia == "AMAZONAS"
    assert balbina.id_reservatorio == "AMUHBB"
    assert balbina.nome_reservatorio == "BALBINA"


def test_instante_e_a_hora_fim_e_a_data_e_a_do_proprio_instante(conector):
    registros = _registros(conector, "2026-09-01", "2026-09-01")
    instantes = [r.instante for r in registros if r.id_reservatorio == "AMUHBB"]

    assert instantes == [
        datetime(2026, 9, 1, 1),
        datetime(2026, 9, 1, 2),
        datetime(2026, 9, 1, 3),
        datetime(2026, 9, 1, 23, 59),
    ]
    assert {r.data_referencia for r in registros} == {date(2026, 9, 1)}


def test_colunas_vazias_viram_nulo_e_nao_zero(conector):
    balbina = _registros(conector, "2026-09-01", "2026-09-01")[0]

    assert balbina.vazao_outras_estruturas_m3s is None
    assert balbina.vazao_transferida_m3s is None
    assert balbina.vazao_vertida_m3s == Decimal("0.0")  # zero informado continua zero


def test_codigo_de_usina_vazio_e_nulo_e_nao_e_ceg(conector):
    blang = next(r for r in _registros(conector) if r.id_reservatorio == "JIBLNG")

    assert blang.codigo_usina_modelo is None
    assert blang.vazao_turbinada_m3s is None  # reservatório sem usina


def test_valores_negativos_sao_aceitos(conector):
    """Achado no arquivo real: volume útil de -1.917% e afluência de -93.681 m3/s existem na origem."""
    registros = _registros(conector)

    assert next(r for r in registros if r.id_reservatorio == "AMDA").volume_util_percentual == Decimal("-4.58")
    assert next(r for r in registros if r.id_reservatorio == "CASPSO").vazao_afluente_m3s == Decimal("-4.0")
    assert next(r for r in registros if r.id_reservatorio == "IGSEGR").vazao_transferida_m3s == Decimal("-160.0")


def test_afluencia_vazia_e_nula(conector):
    igarapava = next(r for r in _registros(conector) if r.id_reservatorio == "GRIGAR")
    assert igarapava.vazao_afluente_m3s is None


def test_submercado_desconhecido_e_rejeitado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["id_subsistema"] = "XX"

    with pytest.raises(ValidationError):
        DadoHidrologico.model_validate(conector.transformar(bruto))


def test_instante_malformado_e_rejeitado_nao_derruba(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-01", "2026-09-01"))))
    bruto["din_instante"] = "01/09/2026 01:00"

    with pytest.raises(ValidationError):
        DadoHidrologico.model_validate(conector.transformar(bruto))


def test_ingerir_conta_as_linhas_da_janela(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-09-01", "2026-09-30"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 10
    assert execucao.linhas_invalidas == 0
