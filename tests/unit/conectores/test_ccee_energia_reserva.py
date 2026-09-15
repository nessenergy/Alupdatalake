"""Conector CCEE/EER — liquidação da energia de reserva, uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_energia_reserva import CceeEnergiaReserva, EnergiaReserva
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_energia_reserva_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeEnergiaReserva()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "energia_reserva_liquidacao_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_e_aceita_ajuste_negativo(conector):
    junho = next(r for r in conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30")))
    registro = EnergiaReserva.model_validate(conector.transformar(junho))

    assert registro.data_referencia == date(2026, 6, 1)
    assert registro.ajuste == Decimal("-3547179.17")  # ajuste pode ser negativo
    assert registro.valor_total_liquidado == Decimal("390762770.66")


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
