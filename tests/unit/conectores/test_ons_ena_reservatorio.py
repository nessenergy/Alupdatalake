"""Conector ONS/ENA por reservatório — vazio é ausência de medição; a MLT vai a 1.750%."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ons_ena_reservatorio import EnaReservatorio, OnsEnaReservatorio
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ena_reservatorio_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsEnaReservatorio()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def _registro(conector, nome):
    linhas = conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    bruto = next(r for r in linhas if r["nom_reservatorio"] == nome)
    return EnaReservatorio.model_validate(conector.transformar(bruto))


def test_fio_dagua_traz_os_valores(conector):
    registro = _registro(conector, "14 DE JULHO")

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.submercado == "S"
    assert registro.tipo_reservatorio == "Fio dagua"
    assert registro.ena_bruta_mwmed == Decimal("10.086")
    assert registro.mlt_ena_mwmed == Decimal("48.256")


def test_sem_medicao_fica_nulo(conector):
    registro = _registro(conector, "CANASTRA")
    assert registro.ena_bruta_mwmed is None
    assert registro.ena_bruta_percentual_mlt is None


def test_ingerir_nao_descarta_a_linha_sem_medicao(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-03-04", "2026-03-04"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (3, 0)
