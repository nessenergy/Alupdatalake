"""Conector ONS — geração comercial para exportação internacional, horária."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_geracao_exportacao import GeracaoExportacao, OnsGeracaoExportacao
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_geracao_exportacao_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: None)
    conector = OnsGeracaoExportacao()
    monkeypatch.setattr(conector, "_baixar_ano", lambda _ano: FIXTURE.read_text(encoding="utf-8"))
    return conector


def test_transformar_nomeia_os_paises(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-24", "2026-01-24"))))
    registro = GeracaoExportacao.model_validate(conector.transformar(bruto))

    assert registro.instante == datetime(2026, 1, 24, 0, 0)
    assert registro.geracao_exportacao_termica_mwmed == Decimal("255.7845")
    assert registro.exportacao_argentina_mwmed == Decimal("310.147")
    assert registro.exportacao_uruguai_mwmed == Decimal("0.0")


def test_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        GeracaoExportacao.model_validate(
            {
                "data_referencia": "2026-01-24",
                "instante": "2026-01-24T00:00:00",
                "geracao_exportacao_evt_argentina_mwmed": "-1",
                "geracao_exportacao_evt_uruguai_mwmed": "0",
                "geracao_exportacao_termica_mwmed": "0",
                "exportacao_argentina_mwmed": "0",
                "exportacao_uruguai_mwmed": "0",
            }
        )


def test_ingere_as_tres_horas(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-24", "2026-01-24"))
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (3, 0)
