"""Conector CCEE — TRC de segurança energética, uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_energia_reserva_consumo_referencia import (
    CceeEnergiaReservaConsumoReferencia,
    ConsumoReferenciaEnergiaReserva,
)
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_energia_reserva_consumo_referencia_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeEnergiaReservaConsumoReferencia()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "energia_reserva_consumo_referencia_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_o_trc(conector):
    bruto = next(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = ConsumoReferenciaEnergiaReserva.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.trc_seguranca_energetica == Decimal("46696229.92089")
    assert registro.trc_seguranca_energetica_suc is None


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
