"""Conector CCEE — consumo por classe de agente, uma linha por mês e classe, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_consumo_classe_agente import CceeConsumoClasseAgente, ConsumoClasseAgente
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_consumo_classe_agente_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeConsumoClasseAgente()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [{"name": "consumo_classe_agente_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]
        },
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def _registros(conector, de, ate):
    return [
        ConsumoClasseAgente.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto(de, ate))
    ]


def test_transformar_tipa_o_consumo_por_classe(conector):
    distribuidor = next(
        r for r in _registros(conector, "2026-07-01", "2026-07-31") if r.classe_agente == "Distribuidor"
    )

    assert distribuidor.data_referencia == date(2026, 7, 1)
    assert distribuidor.consumo == Decimal("39454.29477489113")
    assert distribuidor.consumo_ponto_conexao_classe_acl == Decimal("0")


def test_duas_classes_no_mesmo_mes_sao_registros_distintos(conector):
    registros = _registros(conector, "2026-07-01", "2026-07-31")

    assert {r.classe_agente for r in registros} == {"Distribuidor", "Consumidor Livre"}


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
