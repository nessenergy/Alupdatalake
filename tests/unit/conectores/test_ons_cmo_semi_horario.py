"""Conector ONS — CMO semi-horário: passo de 30 minutos, a chave é o instante inteiro."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_cmo_semi_horario import CmoSemiHorario, OnsCmoSemiHorario
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_cmo_semi_horario_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsCmoSemiHorario()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def _registros(conector):
    return [
        CmoSemiHorario.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    ]


def test_meia_hora_e_registro_distinto_da_hora_cheia(conector):
    registros = _registros(conector)
    instantes = {r.instante for r in registros}

    assert datetime(2026, 3, 4, 0, 0) in instantes
    assert datetime(2026, 3, 4, 0, 30) in instantes
    assert len({(r.instante, r.submercado) for r in registros}) == len(registros) == 8


def test_valor_do_nordeste(conector):
    ne = next(r for r in _registros(conector) if r.submercado == "NE" and r.instante.minute == 0)
    assert ne.cmo_reais_mwh == Decimal("533.54")


def test_cmo_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        CmoSemiHorario.model_validate(
            {
                "data_referencia": "2026-03-04",
                "instante": "2026-03-04T00:00:00",
                "submercado": "NE",
                "cmo_reais_mwh": "-1",
            }
        )
