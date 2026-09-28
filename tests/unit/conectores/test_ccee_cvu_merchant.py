"""Conector CCEE — CVU merchant, uma linha por mês e por modelo de preço, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ccee_cvu_merchant import CceeCvuMerchant, CvuMerchant
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_cvu_merchant_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeCvuMerchant()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "custo_variavel_unitario_merchant_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def _registros(conector, de, ate):
    return [CvuMerchant.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(de, ate))]


def test_transformar_tipa_o_cvu(conector):
    alfa = next(r for r in _registros(conector, "2026-07-01", "2026-07-31") if r.codigo_modelo_preco == "43")

    assert alfa.data_referencia == date(2026, 7, 1)
    assert alfa.cvu_sem_custo_fixo == Decimal("551.12")
    assert alfa.cvu_com_custo_fixo == Decimal("984.89")
    assert alfa.recupera_custo_fixo is False
    assert alfa.inicio_suprimento == date(2025, 7, 17)
    assert alfa.termino_suprimento == date(2026, 7, 17)
    assert alfa.periodo_cotacao == "2025-12"


def test_cvu_com_custo_fixo_traco_vira_nulo(conector):
    beta = next(r for r in _registros(conector, "2026-07-01", "2026-07-31") if r.codigo_modelo_preco == "54")

    assert beta.cvu_com_custo_fixo is None


def test_recuperacao_custo_fixo_sim_vira_true(conector):
    gama = next(r for r in _registros(conector, "2026-07-01", "2026-07-31") if r.codigo_modelo_preco == "60")

    assert gama.recupera_custo_fixo is True


def test_recuperacao_custo_fixo_invalido_e_rejeitado():
    with pytest.raises(ValidationError):
        CvuMerchant.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_modelo_preco": "43",
                "empreendimento": "UTE Alfa",
                "despacho": "2.144/2025",
                "tipo_combustivel": "Gás natural",
                "cvu_sem_custo_fixo": "551.12",
                "recupera_custo_fixo": "Talvez",
                "inicio_suprimento": "2025-07-17",
                "termino_suprimento": "2026-07-17",
                "origem_cotacao": "Platts",
                "periodo_cotacao": "2025-12",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
