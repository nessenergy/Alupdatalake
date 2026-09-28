"""Conector CCEE — encargo de reserva (CONER), uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_reserva_encargo import CceeReservaEncargo, ReservaEncargo
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_reserva_encargo_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeReservaEncargo()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "reserva_encargo_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_o_encargo(conector):
    bruto = next(conector.extrair(Janela.de_texto("2026-08-01", "2026-08-31")))
    registro = ReservaEncargo.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 8, 1)
    assert registro.encargo_energia_reserva == Decimal("820268065.9")
    assert registro.saldo_efetivo_coner == Decimal("477177119.42")


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-08-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
