"""Conector CCEE/exposição financeira — uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_exposicao_financeira import CceeExposicaoFinanceira, ExposicaoFinanceira
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_exposicao_financeira_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeExposicaoFinanceira()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "exposicao_financeira_mensal_2026", "url": "u", "last_modified": "2026-09-01T14:54:27"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_os_meses_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-06-01", "2026-07-31")))

    assert sorted(r["MES_REFERENCIA"] for r in registros) == ["202606", "202607"]


def test_transformar_tipa_os_valores_e_data_o_mes(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = ExposicaoFinanceira.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.versao_publicacao == date(2026, 9, 1)
    assert registro.excedente_financeiro == Decimal("3410635.09")
    assert registro.total_exposicao_negativa == Decimal("516305.12")
    assert registro.reserva_alivio_ess == Decimal("3766115.14")


def test_campo_vazio_vira_nulo(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-05-01", "2026-05-31")))
    registro = ExposicaoFinanceira.model_validate(conector.transformar(bruto))

    assert registro.excedente_financeiro_positivo is None


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-05-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
