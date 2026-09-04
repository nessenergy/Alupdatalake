"""Acesso a banco relacional das fontes internas (Onda 3), sem rede."""

from __future__ import annotations

import sys
from datetime import date
from typing import Any

import pytest
from src.core import banco
from src.core.execucao import Janela


class CursorFalso:
    """Cursor DB-API mínimo: devolve `linhas` em lotes, como um driver real."""

    def __init__(self, colunas: list[str], linhas: list[tuple[Any, ...]]) -> None:
        self.description = [(c, None, None, None, None, None, None) for c in colunas]
        self._linhas = linhas
        self._pos = 0
        self.sql: str | None = None
        self.parametros: dict[str, Any] | None = None
        self.fechado = False

    def execute(self, sql: str, parametros: dict[str, Any] | None = None) -> None:
        self.sql = sql
        self.parametros = parametros

    def fetchmany(self, tamanho: int) -> list[tuple[Any, ...]]:
        pedaco = self._linhas[self._pos : self._pos + tamanho]
        self._pos += len(pedaco)
        return pedaco

    def close(self) -> None:
        self.fechado = True


class ConexaoFalsa:
    def __init__(self, cursor: CursorFalso) -> None:
        self._cursor = cursor

    def cursor(self) -> CursorFalso:
        return self._cursor

    def close(self) -> None:
        self.fechada = True


@pytest.fixture
def cursor() -> CursorFalso:
    return CursorFalso(
        colunas=["COD_USINA", "DATA_REFERENCIA", "VALOR"],
        linhas=[("CEG001", date(2026, 1, 1), 10.5), ("CEG002", date(2026, 1, 2), 20.0)],
    )


def test_consultar_devolve_dicionarios_com_colunas_minusculas(cursor: CursorFalso) -> None:
    linhas = list(banco.consultar(ConexaoFalsa(cursor), "SELECT 1"))

    assert linhas == [
        {"cod_usina": "CEG001", "data_referencia": date(2026, 1, 1), "valor": 10.5},
        {"cod_usina": "CEG002", "data_referencia": date(2026, 1, 2), "valor": 20.0},
    ]


def test_consultar_pagina_em_lotes_ate_esgotar(cursor: CursorFalso) -> None:
    # Lote menor que o total: o cursor precisa ser consumido mais de uma vez.
    assert len(list(banco.consultar(ConexaoFalsa(cursor), "SELECT 1", lote=1))) == 2


def test_consultar_repassa_parametros_da_janela(cursor: CursorFalso) -> None:
    janela = Janela(date(2026, 1, 1), date(2026, 1, 31))
    sql = "SELECT * FROM t WHERE d BETWEEN :inicio AND :fim"

    list(banco.consultar(ConexaoFalsa(cursor), sql, {"inicio": janela.inicio, "fim": janela.fim}))

    assert cursor.parametros == {"inicio": date(2026, 1, 1), "fim": date(2026, 1, 31)}


def test_consultar_fecha_o_cursor_mesmo_com_erro() -> None:
    class CursorQueFalha(CursorFalso):
        def execute(self, sql: str, parametros: dict[str, Any] | None = None) -> None:
            raise RuntimeError("ORA-00942: table or view does not exist")

    cursor = CursorQueFalha([], [])
    with pytest.raises(RuntimeError):
        list(banco.consultar(ConexaoFalsa(cursor), "SELECT 1"))

    assert cursor.fechado, "cursor precisa ser fechado; conexão sob VPN não perdoa vazamento"


@pytest.mark.parametrize("sql", ["INSERT INTO t VALUES (1)", "UPDATE t SET x = 1", "DELETE FROM t", "DROP TABLE t"])
def test_consultar_recusa_comando_de_escrita_antes_de_abrir_cursor(sql: str, cursor: CursorFalso) -> None:
    with pytest.raises(ValueError, match="somente leitura"):
        list(banco.consultar(ConexaoFalsa(cursor), sql))

    assert cursor.sql is None


def test_consultar_e_preguicoso_ate_o_primeiro_next(cursor: CursorFalso) -> None:
    banco.consultar(ConexaoFalsa(cursor), "SELECT 1")

    assert cursor.sql is None, "gerador não deve executar SQL antes de ser consumido"


def test_abrir_conexao_fecha_mesmo_quando_o_bloco_falha(monkeypatch: pytest.MonkeyPatch, cursor: CursorFalso) -> None:
    conexao = ConexaoFalsa(cursor)
    conexao.fechada = False
    monkeypatch.setattr(banco, "criar_conexao", lambda *_args: conexao)

    with pytest.raises(RuntimeError, match="falha simulada"), banco.abrir_conexao("fmb"):
        raise RuntimeError("falha simulada")

    assert conexao.fechada


@pytest.mark.parametrize("dsn", ["postgres://u:s@h/b", "http://exemplo", "sem-esquema"])
def test_conectar_recusa_driver_desconhecido(dsn: str) -> None:
    with pytest.raises(ValueError, match="driver não suportado"):
        banco.conectar(dsn)


def test_conectar_traduz_dsn_oracle_para_o_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, Any] = {}

    class OracleFalso:
        @staticmethod
        def connect(**kwargs: Any) -> str:
            capturado.update(kwargs)
            return "conexao"

    monkeypatch.setitem(sys.modules, "oracledb", OracleFalso)

    # Senha com caractere que exige percent-encoding na URL.
    assert banco.conectar("oracle://leitor:s%40nha@fmb.alup:1600/FMBPRD") == "conexao"
    assert capturado["user"] == "leitor"
    assert capturado["password"] == "s@nha"  # noqa: S105 — valor de teste, não credencial
    assert capturado["dsn"] == "fmb.alup:1600/FMBPRD"
    assert capturado["tcp_connect_timeout"] > 0


def test_conectar_usa_porta_padrao_quando_a_dsn_omite(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, Any] = {}

    class MysqlFalso:
        @staticmethod
        def connect(**kwargs: Any) -> str:
            capturado.update(kwargs)
            return "conexao"

    monkeypatch.setitem(sys.modules, "pymysql", MysqlFalso)

    banco.conectar("mysql://app:senha@portal.alup/comercializacao")

    assert capturado["port"] == 3306, "sem porta na DSN, vale a porta padrão do driver"
    assert capturado["database"] == "comercializacao"


def test_erro_de_dsn_nao_vaza_a_senha() -> None:
    with pytest.raises(ValueError) as exc:
        banco.conectar("postgres://usuario:SENHA_SECRETA@host/base")

    assert "SENHA_SECRETA" not in str(exc.value)
    assert "usuario" not in str(exc.value)


# ------------------------------------------------------------------ SQL Server
# Via (c) do adendo ao C4: ler o Balanço Energético do SQL Server da Alup, sem
# depender do desbloqueio do portal da CCEE.


def test_conectar_traduz_dsn_sqlserver_para_o_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, Any] = {}

    class TdsFalso:
        @staticmethod
        def connect(**kwargs: Any) -> str:
            capturado.update(kwargs)
            return "conexao"

    monkeypatch.setitem(sys.modules, "pytds", TdsFalso)

    assert banco.conectar("sqlserver://leitor:s%40nha@balanco.alup:1533/BALANCO") == "conexao"
    assert capturado["server"] == "balanco.alup"
    assert capturado["port"] == 1533
    assert capturado["user"] == "leitor"
    assert capturado["password"] == "s@nha"  # noqa: S105 — valor de teste, não credencial
    assert capturado["database"] == "BALANCO"
    assert capturado["login_timeout"] > 0


def test_sqlserver_usa_porta_padrao_1433(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict[str, Any] = {}

    class TdsFalso:
        @staticmethod
        def connect(**kwargs: Any) -> str:
            capturado.update(kwargs)
            return "conexao"

    monkeypatch.setitem(sys.modules, "pytds", TdsFalso)
    banco.conectar("sqlserver://app:senha@balanco.alup/BALANCO")

    assert capturado["port"] == 1433


def test_sqlserver_devolve_tupla_e_nao_dicionario(monkeypatch: pytest.MonkeyPatch) -> None:
    """`consultar()` monta o dicionário a partir de `cursor.description`.

    Com `as_dict=True` o driver devolveria dicionários e o `zip` de `consultar`
    quebraria — por isso o modo é fixado aqui, não deixado no padrão do driver.
    """
    capturado: dict[str, Any] = {}

    class TdsFalso:
        @staticmethod
        def connect(**kwargs: Any) -> str:
            capturado.update(kwargs)
            return "conexao"

    monkeypatch.setitem(sys.modules, "pytds", TdsFalso)
    banco.conectar("sqlserver://app:senha@balanco.alup/BALANCO")

    assert capturado["as_dict"] is False


def test_mensagem_de_driver_desconhecido_lista_os_tres_suportados() -> None:
    with pytest.raises(ValueError) as exc:
        banco.conectar("postgres://u:s@h/b")

    for esquema in ("oracle", "mysql", "sqlserver"):
        assert esquema in str(exc.value)
