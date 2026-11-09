"""Testes do conector ccee_pi/ponto_medicao — sem rede, com a página de exemplo sintética da CCEE."""

from datetime import date
from pathlib import Path

import pytest
from defusedxml import ElementTree
from src.conectores import ccee_pi_ponto_medicao as modulo
from src.conectores.ccee_pi_ponto_medicao import CceePiPontoMedicao, CceePiPontoMedicaoRegistro
from src.core.execucao import Janela

PAGINA = (Path(__file__).parent.parent.parent / "fixtures" / "ccee_pi" / "ponto_medicao_pagina1.xml").read_text(
    encoding="utf-8"
)
JANELA = Janela(inicio=date(2026, 11, 1), fim=date(2026, 11, 9))


@pytest.fixture
def conector(monkeypatch):
    pontos = ElementTree.fromstring(PAGINA).findall(f".//{{{modulo.NS_BO2}}}pontoMedicao")
    monkeypatch.setattr(modulo, "abrir_sessao", lambda: object())
    monkeypatch.setattr(modulo, "pontos_medicao", lambda sessao: iter(pontos))
    return CceePiPontoMedicao()


def test_extrair_gera_uma_linha_por_ponto_e_agente_relacionado(conector):
    linhas = list(conector.extrair(JANELA))

    assert len(linhas) == 6  # 2 pontos x 3 agentes relacionados
    primeira = linhas[0]
    assert primeira["ponto_codigo"] == "ABCDEFGH01-01"
    assert primeira["ponto_nome"] == "PONTO DE MEDICAO 001"
    assert primeira["tipo_coleta"] == "DIRETA"
    assert primeira["tipo_relacao"] == "AGENTE_CONECTADO"
    assert primeira["perfil_codigo"] == "999"
    assert primeira["agente_nome"] == "EMPRESA A"


def test_a_data_do_retrato_e_o_fim_da_janela(conector):
    assert {linha["data_referencia"] for linha in conector.extrair(JANELA)} == {"2026-11-09"}


def test_transformar_valida_no_schema(conector):
    linha = conector.transformar(next(iter(conector.extrair(JANELA))))

    registro = CceePiPontoMedicaoRegistro(**linha)
    assert registro.data_referencia == date(2026, 11, 9)
    assert registro.ponto_codigo == "ABCDEFGH01-01"


def test_ponto_sem_agente_relacionado_ainda_gera_uma_linha(monkeypatch):
    xml = (
        '<r xmlns:bo="http://xmlns.energia.org.br/BO/v2"><bo:pontoMedicao><bo:codigo>P1</bo:codigo>'
        "<bo:nome>SEM AGENTE</bo:nome></bo:pontoMedicao></r>"
    )
    pontos = ElementTree.fromstring(xml).findall(f".//{{{modulo.NS_BO2}}}pontoMedicao")
    monkeypatch.setattr(modulo, "abrir_sessao", lambda: object())
    monkeypatch.setattr(modulo, "pontos_medicao", lambda sessao: iter(pontos))

    linhas = list(CceePiPontoMedicao().extrair(JANELA))

    assert len(linhas) == 1
    assert linhas[0]["ponto_codigo"] == "P1"
    assert linhas[0]["tipo_relacao"] is None


def test_cadastro_vazio_falha_alto(monkeypatch):
    monkeypatch.setattr(modulo, "abrir_sessao", lambda: object())
    monkeypatch.setattr(modulo, "pontos_medicao", lambda sessao: iter([]))

    with pytest.raises(RuntimeError, match="nenhum ponto"):
        list(CceePiPontoMedicao().extrair(JANELA))
