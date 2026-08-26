"""Portal MVP: o que a tela mostra e o que ela não deixa passar.

Escopo em `docs/arquitetura/decisoes/005-escopo-do-portal-mvp.md`.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from src.core.config import get_settings
from src.portal.app import CABECALHO_IDENTIDADE, app
from src.portal.dados import Painel, ProvedorSimulado, obter_provedor


@pytest.fixture
def cliente():
    app.config.update(TESTING=True)
    return app.test_client()


def test_pagina_mostra_a_view_e_as_linhas(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "cambio_mensal" in corpo
    assert "2026-08" in corpo
    assert "5.4501" in corpo


def test_pagina_diz_quando_foi_a_ultima_ingestao(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "26/08/2026 09:00" in corpo
    assert "bcb_cambio_ptax" in corpo


def test_dado_simulado_e_rotulado_como_tal(cliente) -> None:
    corpo = cliente.get("/").get_data(as_text=True)
    assert "Dados de exemplo" in corpo  # ninguém pode confundir com dado do lake


def test_identidade_vem_do_cabecalho_do_iap(cliente) -> None:
    corpo = cliente.get("/", headers={CABECALHO_IDENTIDADE: "accounts.google.com:fulano@alupar.com.br"}).get_data(
        as_text=True
    )
    assert "fulano@alupar.com.br" in corpo
    assert "accounts.google.com" not in corpo


def test_sem_cabecalho_a_tela_diz_que_nao_ha_autenticacao(cliente) -> None:
    assert "não autenticado" in cliente.get("/").get_data(as_text=True)


def test_conteudo_de_celula_e_escapado(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    malicioso = Painel(
        view="cambio_mensal",
        colunas=["nota"],
        linhas=[{"nota": "<script>alert(1)</script>"}],
        ultima_ingestao=datetime(2026, 8, 26, tzinfo=UTC),
        fonte_ultima_ingestao="<b>x</b>",
    )
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: type("P", (), {"painel": lambda _s, _v: malicioso})())
    corpo = cliente.get("/").get_data(as_text=True)
    assert "<script>" not in corpo
    assert "&lt;script&gt;" in corpo


def test_celula_vazia_vira_travessao_nao_none(cliente, monkeypatch: pytest.MonkeyPatch) -> None:
    vazio = Painel(
        view="cambio_mensal",
        colunas=["valor"],
        linhas=[{"valor": None}],
        ultima_ingestao=None,
        fonte_ultima_ingestao=None,
    )
    monkeypatch.setattr("src.portal.app.obter_provedor", lambda: type("P", (), {"painel": lambda _s, _v: vazio})())
    corpo = cliente.get("/").get_data(as_text=True)
    assert "<td>—</td>" in corpo
    assert "None" not in corpo
    assert "Nenhuma ingestão registrada" in corpo


def test_saude_responde_sem_tocar_no_bigquery(cliente) -> None:
    assert cliente.get("/saude").get_json() == {"status": "ok"}


def test_provedor_padrao_e_o_simulado_enquanto_gcp_nao_existe() -> None:
    get_settings.cache_clear()
    assert isinstance(obter_provedor(), ProvedorSimulado)


def test_nome_de_view_invalido_nao_chega_na_query() -> None:
    from src.portal.dados import ProvedorBigQuery

    with pytest.raises(ValueError, match="view inválido"):
        ProvedorBigQuery().painel("gold`; DROP TABLE x --")
