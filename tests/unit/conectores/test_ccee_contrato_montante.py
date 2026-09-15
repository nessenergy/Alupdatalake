"""Conector CCEE/contrato montante — compra e venda por perfil, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_contrato_montante import CceeContratoMontante, ContratoMontante
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_contrato_montante_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeContratoMontante()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {
                    "name": "contrato_montante_compra_venda_perfil_agente_2026",
                    "url": "u",
                    "last_modified": "2026-09-01T14:00:00",
                }
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_o_mes(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert [r["CODIGO_PERFIL_AGENTE"] for r in registros] == ["83729", "100", "300"]


def test_transformar_le_os_nomes_de_coluna_desta_fonte(conector):
    """Aqui é CODIGO_AGENTE / CODIGO_PERFIL_AGENTE, não COD_AGENTE / COD_PERF_AGENTE."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ContratoMontante.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.codigo_agente == "100"
    assert registro.codigo_perfil == "83729"
    assert registro.sigla_perfil == "ALFA DIST"
    assert registro.contratacao_venda == Decimal("18.12572811828")
    assert registro.contratacao_compra == Decimal("766.21345206586")


def test_venda_vazia_vira_nulo(conector):
    registros = {r["CODIGO_PERFIL_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))}
    gama = ContratoMontante.model_validate(conector.transformar(registros["300"]))

    assert gama.contratacao_venda is None
    assert gama.contratacao_compra == Decimal("12.5")


def test_montante_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        ContratoMontante.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_agente": "1",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "cnpj": "11111111000111",
                "contratacao_compra": "-1",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
