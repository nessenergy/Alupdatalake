"""Para onde cada endereço do Portal leva — em particular, a abertura em Indicadores."""

from __future__ import annotations

import pytest
from src.portal.app import app
from src.portal.pagina import ROTAS


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)
    return app.test_client()


def test_a_raiz_abre_em_indicadores(cliente) -> None:
    resposta = cliente.get("/")
    assert resposta.status_code == 302
    assert resposta.headers["Location"] == "/indicadores"


def test_a_raiz_leva_o_modo_telao_junto(cliente) -> None:
    """Quem abre só o endereço do Portal com `?telao=1` cai direto no rodízio."""
    assert cliente.get("/?telao=1").headers["Location"] == "/indicadores?telao=1"


@pytest.mark.parametrize("consulta", ["//evil.example", "p=1&x=%0d%0aSet-Cookie:a=b", "u=http://evil.example"])
def test_a_raiz_nao_vira_redirecionamento_aberto(cliente, consulta: str) -> None:
    """O destino é sempre um caminho do próprio Portal; a consulta só vai depois do `?`."""
    destino = cliente.get(f"/?{consulta}").headers["Location"]
    assert destino.startswith("/indicadores?")
    assert "\r" not in destino
    assert "\n" not in destino


def test_dado_de_negocio_tem_endereco_proprio(cliente) -> None:
    resposta = cliente.get("/dado")
    assert resposta.status_code == 200
    assert "Dado de negócio" in resposta.get_data(as_text=True)


def test_a_navegacao_comeca_pela_tela_de_abertura() -> None:
    assert [rota for rota, _ in ROTAS] == ["/indicadores", "/lake", "/custo", "/dado"]


def test_a_tela_de_abertura_vem_marcada_na_navegacao(cliente) -> None:
    corpo = cliente.get("/indicadores").get_data(as_text=True)
    assert '<a href="/indicadores" aria-current="page">Indicadores</a>' in corpo
