"""Conector ONS/ENA por bacia — a ENA compara com a média histórica e passa de 100%."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_ena_bacia import EnaBacia, OnsEnaBacia
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_ena_bacia_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsEnaBacia()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_recorta_pela_janela(conector):
    assert len(list(conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04")))) == 2


def test_transformar_e_percentual_acima_de_100(conector):
    linhas = conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    bruto = next(r for r in linhas if r["nom_bacia"] == "SAO FRANCISCO")
    registro = EnaBacia.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.bacia == "SAO FRANCISCO"
    assert registro.ena_bruta_percentual_mlt == Decimal("139.0539")  # acima da média histórica
    assert registro.ena_armazenavel_mwmed == Decimal("19432.999")


def test_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        EnaBacia.model_validate(
            {
                "data_referencia": "2026-03-04",
                "bacia": "X",
                "ena_bruta_mwmed": "-1",
                "ena_bruta_percentual_mlt": "1",
                "ena_armazenavel_mwmed": "1",
                "ena_armazenavel_percentual_mlt": "1",
            }
        )
