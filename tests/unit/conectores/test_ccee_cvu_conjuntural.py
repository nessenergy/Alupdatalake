"""Conector CCEE — CVU conjuntural, uma linha por mês e por agente vendedor, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ccee_cvu_conjuntural import CceeCvuConjuntural, CvuConjuntural
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_cvu_conjuntural_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeCvuConjuntural()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {"name": "custo_variavel_unitario_conjuntural_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_o_cvu_conjuntural(conector):
    bruto = next(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = CvuConjuntural.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.agente_vendedor == "UTE ALFA"
    assert registro.cnpj_agente_vendedor == "06212748000134"
    assert registro.cvu_conjuntural == Decimal("2584.06")
    assert registro.inicio_suprimento == date(2020, 10, 6)
    assert registro.termino_suprimento == date(2035, 10, 5)


def test_cnpj_com_tamanho_errado_e_rejeitado():
    with pytest.raises(ValidationError):
        CvuConjuntural.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "agente_vendedor": "UTE ALFA",
                "cnpj_agente_vendedor": "123",
                "sigla_parcela": "UTE Alfa",
                "tipo_combustivel": "Diesel",
                "leilao": "2º Leilão de Energia Nova",
                "produto": "2009-15",
                "custo_combustivel": "2492.92",
                "cvu_conjuntural": "2584.06",
                "codigo_modelo_preco": "235",
                "inicio_suprimento": "2020-10-06",
                "termino_suprimento": "2035-10-05",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
