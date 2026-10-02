"""Conector ONS — DESSEM, balanço de energia geral, um CSV por dia.

O que estes testes protegem, e que vem do arquivo real (varredura dos 493
arquivos de 23/05/2025 a 02/10/2026, em 02/10/2026):

- a data vem ISO (`AAAA-MM-DD`), diferente do `programacao_x_previsao`;
- 4 subsistemas × 48 patamares = 192 linhas por dia, sem a linha SIN;
- nenhum valor negativo ou vazio, e o dicionário do ONS os proíbe.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError
from src.conectores.ons_balanco_dessem import BalancoDessem, OnsBalancoDessem
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ons_balanco_dessem_2026_10_02.csv"
DIA = Janela.de_texto("2026-10-02", "2026-10-02")
_FONTES = ("demanda_mw", "geracao_renovavel_mw", "geracao_hidraulica_mw", "geracao_termica_mw")


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ons_arquivo_diario.criar_sessao", lambda: None)
    conector = OnsBalancoDessem()
    monkeypatch.setattr(
        conector, "_abrir", lambda dia: FIXTURE.read_bytes().splitlines() if dia == date(2026, 10, 2) else None
    )
    return conector


def _registros(conector):
    return [BalancoDessem.model_validate(conector.transformar(b)) for b in conector.extrair(DIA)]


def _valido(**mudancas):
    base = {"data_referencia": "2026-10-02", "patamar": "1", "submercado": "N", "consumo_elevatoria_mw": "0"}
    return base | dict.fromkeys(_FONTES, "1") | mudancas


def test_campos_do_sudeste_no_patamar_1(conector):
    se = next(r for r in _registros(conector) if r.submercado == "SE" and r.patamar == 1)

    assert se.data_referencia == date(2026, 10, 2)
    assert se.demanda_mw == Decimal("46253.480")
    assert se.geracao_renovavel_mw == Decimal("5039.000")
    assert se.geracao_hidraulica_mw == Decimal("35879.060")
    assert se.geracao_termica_mw == Decimal("2898.000")
    assert se.consumo_elevatoria_mw == Decimal("28.84")


def test_subsistema_desconhecido_e_rejeitado():
    with pytest.raises(ValidationError):
        BalancoDessem.model_validate(_valido(submercado="SIN"))


def test_valor_negativo_e_rejeitado():
    with pytest.raises(ValidationError):
        BalancoDessem.model_validate(_valido(geracao_termica_mw="-1"))


def test_ingere_as_oito_linhas(conector):
    execucao = conector.ingerir(DIA)
    assert (execucao.linhas_extraidas, execucao.linhas_invalidas) == (8, 0)
