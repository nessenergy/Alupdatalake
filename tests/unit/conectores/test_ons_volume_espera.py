"""Conector ONS — volume de espera recomendado, diário por reservatório."""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_volume_espera import OnsVolumeEspera, VolumeEspera
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_volume_espera_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsVolumeEspera()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def _registro(conector, codigo):
    linhas = conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    return VolumeEspera.model_validate(conector.transformar(next(r for r in linhas if r["id_reservatorio"] == codigo)))


def test_trim_de_bacia_e_ree_e_acento_preservado(conector):
    registro = _registro(conector, "PIBESP")

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.submercado == "NE"
    assert registro.bacia == "PARNAIBA"  # a origem traz com espaços à direita
    assert registro.ree == "NORDESTE"
    assert registro.reservatorio == "BOA ESPERANÇA"
    assert registro.volume_espera_percentual == Decimal("64.9")


def test_ordem_vazia_fica_nula(conector):
    assert _registro(conector, "PNTIRM").ordem_cascata is None


def test_percentual_acima_de_100_e_rejeitado():
    """Volume de espera é fração do volume útil: 50,4 a 100 em 2026."""
    with pytest.raises(ValidationError):
        VolumeEspera.model_validate(
            {
                "data_referencia": "2026-03-04",
                "submercado": "NE",
                "codigo_reservatorio": "X",
                "reservatorio": "X",
                "volume_espera_percentual": "100.5",
            }
        )
