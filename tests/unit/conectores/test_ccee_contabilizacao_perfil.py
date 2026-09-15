"""Conector CCEE/contabilização por perfil — a fonte que aceita a ADR 016, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_contabilizacao_perfil import CceeContabilizacaoPerfil, ContabilizacaoPerfil
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_contabilizacao_perfil_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeContabilizacaoPerfil()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {
                    "name": "contabilizacao_montante_perfil_agente_2026",
                    "url": "u",
                    "last_modified": "2026-09-01T14:50:45",
                }
            ]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_o_mes_pedido(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert [r["COD_PERF_AGENTE"] for r in registros] == ["100", "83729", "200"]


def test_transformar_tipa_valores_e_preserva_os_codigos(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ContabilizacaoPerfil.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.versao_publicacao == date(2026, 9, 1)
    assert registro.codigo_agente == "100"
    assert registro.codigo_perfil == "100"
    assert registro.sigla_perfil == "ALFA DIST"
    assert registro.cnpj == "11111111000111"
    assert registro.valor_tm_mcp == Decimal("8815202.25")
    assert registro.resultado_final == Decimal("-13028903.59")
    assert registro.ajuste_recontab == Decimal("-484932.82")


def test_vazio_vira_nulo_e_zero_continua_zero(conector):
    registros = {r["COD_PERF_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))}
    beta = ContabilizacaoPerfil.model_validate(conector.transformar(registros["200"]))
    alfa_sul = ContabilizacaoPerfil.model_validate(conector.transformar(registros["83729"]))

    assert beta.valor_tm_mcp is None  # vazio na origem
    assert beta.compensacao_mre == Decimal("1500.5")
    assert beta.valor_encargo == Decimal("0")  # zero é valor
    assert alfa_sul.ajuste_recontab is None


def test_dois_perfis_do_mesmo_agente_no_mesmo_mes_sao_linhas_distintas(conector):
    registros = [
        ContabilizacaoPerfil.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))
    ]
    alfa = [r for r in registros if r.codigo_agente == "100"]

    assert {r.codigo_perfil for r in alfa} == {"100", "83729"}


def test_cnpj_invalido_e_rejeitado():
    with pytest.raises(ValueError, match="14"):
        ContabilizacaoPerfil.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_agente": "1",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "cnpj": "12",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
