"""Testes do conector ccee_pi/medida — sem rede, com a resposta de exemplo sintética da coleção pública da CCEE."""

import logging
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from defusedxml import ElementTree
from src.conectores import ccee_pi_medida as modulo
from src.conectores.ccee_pi_medida import CceePiMedida, CceePiMedidaRegistro
from src.conectores.ccee_pi_sessao import NS_BM1, Sessao
from src.core.execucao import Janela

RESPOSTA = (Path(__file__).parent.parent.parent / "fixtures" / "ccee_pi" / "medida_final.xml").read_text(
    encoding="utf-8"
)
JANELA = Janela(inicio=date(2023, 3, 1), fim=date(2023, 3, 1))


@pytest.fixture
def chamadas(monkeypatch):
    """Troca a sessão, o cadastro de pontos e a chamada à CCEE; guarda o que o conector pediu."""
    pedidos = []
    medidas = ElementTree.fromstring(RESPOSTA).findall(f".//{{{NS_BM1}}}medida")

    def falso(sessao, ponto, inicio, fim, tipo="FINAL"):
        pedidos.append({"perfil": sessao.perfil, "ponto": ponto, "inicio": inicio, "fim": fim, "tipo": tipo})
        return medidas

    monkeypatch.setattr(modulo, "abrir_sessao", lambda: Sessao(pfx=b"", perfil="padrao"))
    monkeypatch.setattr(modulo, "listar_medidas", falso)
    monkeypatch.setattr(modulo, "_pontos_com_perfil", lambda: [("P1", "111"), ("P2", "222")])
    return pedidos


def test_extrair_pede_cada_ponto_com_o_perfil_dele(chamadas):
    linhas = list(CceePiMedida().extrair(JANELA))

    assert [(p["ponto"], p["perfil"]) for p in chamadas] == [("P1", "111"), ("P2", "222")]
    assert chamadas[0]["inicio"] == "2023-03-01"
    assert chamadas[0]["fim"] == "2023-03-01"
    assert chamadas[0]["tipo"] == "FINAL"
    assert len(linhas) == 4  # 2 medidas da resposta x 2 pontos


def test_a_linha_traz_o_ponto_pedido_e_os_valores(chamadas):
    primeira = next(iter(CceePiMedida().extrair(JANELA)))

    assert primeira["ponto_codigo"] == "ABSCDEFGH101"  # o que a CCEE devolveu
    assert primeira["tipo_medida"] == "FINAL"
    assert primeira["fim_periodo"] == "2023-03-01T00:00:00-03:00"
    assert primeira["sub_tipo"] == "L"
    assert primeira["status"] == "HCC"
    assert primeira["consumo_ativo"] == "57.133"
    assert primeira["geracao_ativa"] == "0.0"


def test_transformar_valida_e_a_data_e_a_da_hora_medida(chamadas):
    linhas = list(CceePiMedida().extrair(JANELA))

    # a hora termina às 00:00 de 01/03: a energia é das 23h de 28/02; a seguinte, das 00h de 01/03
    registros = [CceePiMedidaRegistro(**CceePiMedida().transformar(linha)) for linha in linhas[:2]]
    assert [r.data_referencia for r in registros] == [date(2023, 2, 28), date(2023, 3, 1)]
    assert registros[0].consumo_ativo == Decimal("57.133")
    assert registros[1].consumo_reativo == Decimal("102.497")


def test_ponto_sem_perfil_e_pulado_e_registrado_no_log(chamadas, monkeypatch, caplog):
    monkeypatch.setattr(modulo, "_pontos_com_perfil", lambda: [("P1", None), ("P2", "222")])

    with caplog.at_level(logging.WARNING):
        list(CceePiMedida().extrair(JANELA))

    assert [p["ponto"] for p in chamadas] == ["P2"]
    assert "sem perfil" in caplog.text
    assert "P1" not in caplog.text  # código de ponto é dado de cliente: só a contagem vai ao log


def test_sem_nenhum_ponto_falha_alto(chamadas, monkeypatch):
    monkeypatch.setattr(modulo, "_pontos_com_perfil", lambda: [])

    with pytest.raises(RuntimeError, match="nenhum ponto"):
        list(CceePiMedida().extrair(JANELA))


def test_lista_de_pontos_da_credencial_dispensa_o_cadastro(chamadas, monkeypatch):
    monkeypatch.setattr(modulo, "abrir_sessao", lambda: Sessao(pfx=b"", perfil="6166", pontos=("P7", "P8")))

    def sem_cadastro():
        raise AssertionError("o cadastro não deve ser lido quando a credencial traz os pontos")

    monkeypatch.setattr(modulo, "_pontos_com_perfil", sem_cadastro)

    list(CceePiMedida().extrair(JANELA))

    assert [(p["ponto"], p["perfil"]) for p in chamadas] == [("P7", "6166"), ("P8", "6166")]
