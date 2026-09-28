"""Conector ONS/EAR por reservatório — reservatório sem medição tem campos vazios."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_ear_reservatorio import EarReservatorio, OnsEarReservatorio
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ear_reservatorio_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsEarReservatorio()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def _bruto(conector, nome):
    linhas = conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    return next(r for r in linhas if r["nom_reservatorio"] == nome)


def test_reservatorio_com_usina_traz_subsistema_e_valores(conector):
    registro = EarReservatorio.model_validate(conector.transformar(_bruto(conector, "A. VERMELHA")))

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.submercado == "SE"
    assert registro.tipo_reservatorio == "Reservatório com Usina"
    assert registro.ear_percentual == Decimal("66.7345")
    assert registro.subsistema_jusante is None


def test_reservatorio_sem_medicao_fica_nulo_e_nao_e_descartado(conector):
    """ANTA, reservatório sem usina: 2.421 linhas assim em 2026 — ausência, não erro."""
    registro = EarReservatorio.model_validate(conector.transformar(_bruto(conector, "ANTA")))

    assert registro.ear_proprio_mwmes is None
    assert registro.ear_percentual is None
    assert registro.ear_total_mwmes == Decimal("0.0")


def test_submercado_desconhecido_e_rejeitado(conector):
    bruto = dict(_bruto(conector, "A. VERMELHA"), id_subsistema="XX")
    with pytest.raises(ValidationError):
        EarReservatorio.model_validate(conector.transformar(bruto))


def test_ingerir_carrega_as_tres(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-03-04", "2026-03-04"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (3, 0)
