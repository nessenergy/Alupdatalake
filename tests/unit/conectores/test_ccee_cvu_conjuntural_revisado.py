"""Conector CCEE — CVU conjuntural revisado: mesmo schema do conjuntural, dataset próprio."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_cvu_conjuntural import CvuConjuntural
from src.conectores.ccee_cvu_conjuntural_revisado import CceeCvuConjunturalRevisado
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_cvu_conjuntural_revisado_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeCvuConjunturalRevisado()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {
                    "name": "custo_variavel_unitario_conjuntural_revisado_2026",
                    "url": "u",
                    "last_modified": "2026-09-01T00:00:00",
                }
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_dataset_e_entidade_sao_proprios():
    conector = CceeCvuConjunturalRevisado()

    assert conector.dataset == "custo_variavel_unitario_conjuntural_revisado"
    assert conector.entidade == "cvu_conjuntural_revisado"


def test_transformar_reaproveita_o_schema_do_conjuntural(conector):
    bruto = next(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = CvuConjuntural.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.cvu_conjuntural == Decimal("2295.76")


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
