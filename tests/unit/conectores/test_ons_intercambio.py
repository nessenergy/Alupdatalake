"""Conectores ONS de intercâmbio — nacional (entre subsistemas) e internacional.

O que estes testes protegem:

- o passo é **horário**: a chave inclui o instante, não só o dia;
- no internacional, **valor negativo é importação**, não erro — o sentido do
  fluxo está no sinal (conferido em 2026: -500 MWmed da Argentina);
- o nome do país vem com espaços à direita, e o do subsistema com espaço à
  esquerda (`" NORTE"`).
"""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_intercambio_internacional import IntercambioInternacional, OnsIntercambioInternacional
from src.conectores.ons_intercambio_nacional import IntercambioNacional, OnsIntercambioNacional
from src.core.execucao import Janela

FIXTURES = Path(__file__).parents[2] / "fixtures"


def _conector(monkeypatch, classe, arquivo):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = classe()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: (FIXTURES / arquivo).read_text(encoding="utf-8"))
    return conector


@pytest.fixture
def nacional(monkeypatch):
    return _conector(monkeypatch, OnsIntercambioNacional, "ons_intercambio_nacional_2026.csv")


@pytest.fixture
def internacional(monkeypatch):
    return _conector(monkeypatch, OnsIntercambioInternacional, "ons_intercambio_internacional_2026.csv")


def test_nacional_traz_origem_destino_e_instante(nacional):
    bruto = next(iter(nacional.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))))
    registro = IntercambioNacional.model_validate(nacional.transformar(bruto))

    assert registro.data_referencia == date(2026, 3, 4)
    assert registro.instante == datetime(2026, 3, 4, 0, 0)
    assert (registro.subsistema_origem, registro.subsistema_destino) == ("N", "NE")
    assert registro.intercambio_mwmed == Decimal("2685.532")
    assert registro.intercambio_programado_mwmed == Decimal("2871.928")


def test_nacional_subsistema_desconhecido_e_rejeitado(nacional):
    bruto = dict(next(iter(nacional.extrair(Janela.de_texto("2026-03-04", "2026-03-04")))), id_subsistema_destino="XX")
    with pytest.raises(ValidationError):
        IntercambioNacional.model_validate(nacional.transformar(bruto))


def test_nacional_duas_horas_do_mesmo_dia_sao_registros_distintos(nacional):
    registros = [
        IntercambioNacional.model_validate(nacional.transformar(b))
        for b in nacional.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    ]
    chaves = {(r.instante, r.subsistema_origem, r.subsistema_destino) for r in registros}
    assert len(chaves) == len(registros) == 8


def test_internacional_negativo_e_importacao(internacional):
    bruto = next(iter(internacional.extrair(Janela.de_texto("2026-01-04", "2026-01-04"))))
    registro = IntercambioInternacional.model_validate(internacional.transformar(bruto))

    assert registro.pais == "Argentina"  # sem os espaços à direita
    assert registro.intercambio_mwmed == Decimal("-439.064")


def test_internacional_ingere_sem_descartar(internacional):
    execucao = internacional.ingerir(Janela.de_texto("2026-01-01", "2026-01-31"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (4, 0)
