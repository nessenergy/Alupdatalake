"""Conector CCEE/ESS — encargos de serviço do sistema, uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_encargo_ess import CceeEncargoEss, EncargoEss
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_encargo_ess_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeEncargoEss()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [{"name": "encargo_ess_ancilar_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_os_encargos(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = EncargoEss.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.encargo_constrained_on == Decimal("2747079.77")
    assert registro.encargo_constrained_off == Decimal("19314484.15")
    assert registro.encargo_seguranca_energetica == Decimal("0")


def test_coluna_ausente_no_fim_da_linha_vira_nulo(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30")))
    registro = EncargoEss.model_validate(conector.transformar(bruto))

    assert registro.ressarcimento_custo_emergencial is None
    assert registro.ressarcimento_distribuidora_implantacao is None


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
