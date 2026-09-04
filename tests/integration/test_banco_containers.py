"""Exercita `src/core/banco.py` contra bancos reais em contêiner.

Prova o caminho relacional da Onda 3 sem VPN e sem dado da Alup: conexão pela
DSN, paginação no cursor, colunas em minúscula e recusa de comando de escrita.
Quando a credencial de A7 chegar, a tarefa é apontar uma DSN — não descobrir se
o framework fala com banco.

    docker compose -f tests/integration/docker-compose.bancos.yml up -d
    ALUPDATA_INTEGRACAO_BANCOS=1 uv run pytest tests/integration -q

Os três serviços sobem em `127.0.0.1`; o teste pula sozinho o banco cujo driver
não estiver instalado (`uv sync --extra bancos`).
"""

from __future__ import annotations

import os
from importlib.util import find_spec

import pytest
from src.core import banco

pytestmark = pytest.mark.skipif(
    not os.getenv("ALUPDATA_INTEGRACAO_BANCOS"),
    reason="requer os contêineres de docker-compose.bancos.yml",
)

# DSN, driver e o SELECT que cada dialeto entende sem tabela.
BANCOS = [
    pytest.param(
        "mysql://root:alupdata-local@127.0.0.1:3306/comercializacao",
        "pymysql",
        "SELECT 1 AS Numero, 'ons' AS Fonte",
        id="mysql",
    ),
    pytest.param(
        "oracle://leitor:alupdata-local@127.0.0.1:1521/FREEPDB1",
        "oracledb",
        "SELECT 1 AS Numero, 'ons' AS Fonte FROM dual",
        id="oracle",
    ),
    pytest.param(
        "sqlserver://sa:Alupdata-local1@127.0.0.1:1433/master",
        "pytds",
        "SELECT 1 AS Numero, 'ons' AS Fonte",
        id="sqlserver",
    ),
]


def _exigir_driver(modulo: str) -> None:
    if find_spec(modulo) is None:
        pytest.skip(f"driver {modulo} não instalado — rode `uv sync --extra bancos`")


@pytest.mark.parametrize(("dsn", "driver", "sql"), BANCOS)
def test_conecta_e_devolve_colunas_em_minuscula(dsn: str, driver: str, sql: str) -> None:
    """Oracle devolve coluna em maiúscula; o resto do framework é snake_case."""
    _exigir_driver(driver)
    conexao = banco.conectar(dsn)
    try:
        linhas = list(banco.consultar(conexao, sql))
    finally:
        conexao.close()

    assert len(linhas) == 1
    assert set(linhas[0]) == {"numero", "fonte"}, "coluna precisa chegar em minúscula"
    assert linhas[0]["fonte"] == "ons"


@pytest.mark.parametrize(("dsn", "driver", "sql"), BANCOS)
def test_recusa_escrita_antes_de_tocar_o_banco(dsn: str, driver: str, sql: str) -> None:
    """A origem é read-only por contrato; a recusa não pode depender do banco."""
    _exigir_driver(driver)
    conexao = banco.conectar(dsn)
    try:
        with pytest.raises(ValueError, match="somente leitura"):
            list(banco.consultar(conexao, "DELETE FROM qualquer_tabela"))
    finally:
        conexao.close()


@pytest.mark.parametrize(("dsn", "driver", "sql"), BANCOS)
def test_pagina_no_cursor_em_vez_de_carregar_tudo(dsn: str, driver: str, sql: str) -> None:
    """Com lote menor que o resultado, o cursor precisa ser lido mais de uma vez."""
    _exigir_driver(driver)
    if driver == "oracledb":
        muitos = "SELECT LEVEL AS n FROM dual CONNECT BY LEVEL <= 10"
    elif driver == "pytds":
        muitos = "SELECT TOP 10 ROW_NUMBER() OVER (ORDER BY object_id) AS n FROM sys.objects"
    else:
        muitos = "SELECT 1 AS n UNION ALL SELECT 2 UNION ALL SELECT 3"

    conexao = banco.conectar(dsn)
    try:
        linhas = list(banco.consultar(conexao, muitos, lote=2))
    finally:
        conexao.close()

    assert len(linhas) >= 3
    assert all(set(linha) == {"n"} for linha in linhas)
