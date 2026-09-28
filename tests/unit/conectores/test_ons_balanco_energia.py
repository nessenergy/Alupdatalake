"""Conector ONS — balanço de energia nos subsistemas, horário.

O que estes testes protegem:

- a origem traz uma linha **"SIN"** (total do sistema) junto com os quatro
  subsistemas: ela fica, com a sigla em `subsistema`;
- a sigla vem com espaços à direita (`"N  "`);
- carga e intercâmbio podem ser **negativos** (carga até -4.729 MWmed em 2026;
  intercâmbio negativo é importação líquida); geração não.
"""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_balanco_energia import BalancoEnergia, OnsBalancoEnergia
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_balanco_energia_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsBalancoEnergia()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def _registros(conector):
    return [
        BalancoEnergia.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04"))
    ]


def test_subsistema_com_trim(conector):
    norte = next(r for r in _registros(conector) if r.subsistema == "N")

    assert norte.instante == datetime(2026, 3, 4, 0, 0)
    assert norte.geracao_hidraulica_mwmed == Decimal("15745.821999999998")


def test_linha_do_sin_e_mantida(conector):
    """O total do sistema fica; a Silver é quem deixa `submercado` nulo nela."""
    assert any(r.subsistema == "SIN" for r in _registros(conector))


def test_intercambio_negativo_e_aceito(conector):
    nordeste = next(r for r in _registros(conector) if r.subsistema == "NE")
    assert nordeste.intercambio_mwmed < 0


def test_geracao_negativa_e_rejeitada():
    with pytest.raises(ValidationError):
        BalancoEnergia.model_validate(
            {
                "data_referencia": "2026-03-04",
                "instante": "2026-03-04T00:00:00",
                "subsistema": "N",
                "nome_subsistema": "NORTE",
                "geracao_hidraulica_mwmed": "-1",
                "geracao_termica_mwmed": "0",
                "geracao_eolica_mwmed": "0",
                "geracao_solar_mwmed": "0",
                "carga_mwmed": "0",
                "intercambio_mwmed": "0",
            }
        )


def test_ingere_os_cinco(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-03-04", "2026-03-04"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (5, 0)
