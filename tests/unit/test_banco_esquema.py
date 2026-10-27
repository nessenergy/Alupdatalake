"""Esquema (colunas) das tabelas de um MySQL de fonte, lido só do `information_schema`.

A Alupar listou em 27/10/2026 as tabelas que quer ingerir (`uc`, `client`, `invoice`, ...) e não mandou as colunas.
Este comando as levanta de dentro do job, que é de onde a rede chega ao banco. O que os testes protegem:

- só metadado: nenhuma linha de dado do cliente passa por aqui, só nome, tipo, nulidade e chave de coluna;
- o nome da tabela vem de quem dispara o workflow: valida antes de abrir conexão e entra na consulta só como parâmetro;
- só MySQL (o `information_schema` das outras fontes é outro);
- erro do driver sai sem usuário e senha da DSN.
"""

from __future__ import annotations

from typing import Any

import pytest
from src import cli
from src.core import banco

DSN = "mysql://usuario-ficticio:senha-ficticia@host.exemplo:3306/base_ficticia"


class _Cursor:
    def __init__(self, linhas: list[tuple[Any, ...]], registro: dict[str, Any]) -> None:
        self._linhas = linhas
        self._registro = registro
        self.description = [
            (c,) for c in ("TABLE_NAME", "COLUMN_NAME", "ORDINAL_POSITION", "COLUMN_TYPE", "IS_NULLABLE", "COLUMN_KEY")
        ]

    def execute(self, sql: str, parametros: Any = None) -> None:
        self._registro["sql"] = sql
        self._registro["parametros"] = parametros

    def fetchmany(self, n: int) -> list[tuple[Any, ...]]:
        linhas, self._linhas = self._linhas[:n], self._linhas[n:]
        return linhas

    def close(self) -> None:
        pass


class _Conexao:
    def __init__(self, linhas: list[tuple[Any, ...]], registro: dict[str, Any]) -> None:
        self._linhas = linhas
        self._registro = registro

    def cursor(self) -> _Cursor:
        return _Cursor(self._linhas, self._registro)

    def close(self) -> None:
        self._registro["fechada"] = True


LINHAS = [
    ("uc", "id", 1, "bigint", "NO", "PRI"),
    ("uc", "nome", 2, "varchar(120)", "YES", ""),
    ("client", "id", 1, "bigint", "NO", "PRI"),
]


@pytest.fixture
def registro(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    registro: dict[str, Any] = {}
    monkeypatch.setattr(banco, "ler_secret", lambda fonte, campo: DSN)
    monkeypatch.setattr(banco, "conectar", lambda dsn: _Conexao(LINHAS, registro))
    return registro


def test_devolve_as_colunas_e_diz_quais_tabelas_nao_existem(registro: dict[str, Any]) -> None:
    resultado = banco.esquema("portal-alup", ["uc", "client", "bandeira"])

    assert [(c["tabela"], c["coluna"]) for c in resultado.colunas] == [("uc", "id"), ("uc", "nome"), ("client", "id")]
    assert resultado.colunas[1] == {
        "tabela": "uc",
        "coluna": "nome",
        "posicao": 2,
        "tipo": "varchar(120)",
        "aceita_nulo": True,
        "chave": "",
    }
    assert resultado.colunas[0]["chave"] == "PRI"
    assert resultado.tabelas_ausentes == ["bandeira"]
    assert registro["fechada"] is True


def test_consulta_so_o_information_schema_e_nome_de_tabela_vai_como_parametro(registro: dict[str, Any]) -> None:
    banco.esquema("portal-alup", ["uc", "client"])

    sql = registro["sql"].lower()
    assert "information_schema.columns" in sql
    assert "table_schema = database()" in sql
    assert "in (%(t0)s, %(t1)s)" in sql
    assert "client" not in sql and "'uc'" not in sql
    assert registro["parametros"] == {"t0": "uc", "t1": "client"}


@pytest.mark.parametrize("tabela", ["", "uc; drop table uc", "a b", "uc'--", "x" * 65, "../uc", "uc,client"])
def test_nome_de_tabela_malformado_falha_antes_de_conectar(monkeypatch: pytest.MonkeyPatch, tabela: str) -> None:
    def conectar(dsn: str) -> Any:
        raise AssertionError("não deveria conectar")

    monkeypatch.setattr(banco, "ler_secret", lambda fonte, campo: DSN)
    monkeypatch.setattr(banco, "conectar", conectar)

    with pytest.raises(ValueError, match="nome de tabela"):
        banco.esquema("portal-alup", [tabela])


def test_lista_vazia_de_tabelas_e_recusada() -> None:
    with pytest.raises(ValueError, match="nome de tabela"):
        banco.esquema("portal-alup", [])


def test_so_mysql(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(banco, "ler_secret", lambda fonte, campo: "oracle://u:s@host:1521/SERVICO")
    monkeypatch.setattr(banco, "conectar", lambda dsn: pytest.fail("não deveria conectar"))

    with pytest.raises(ValueError, match="só MySQL"):
        banco.esquema("fmb", ["uc"])


def test_cli_imprime_texto_e_nao_json_uma_linha_por_coluna(
    registro: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> None:
    """Linha que começa com `{` vira log estruturado no Cloud Run e some do texto lido pelo workflow."""
    codigo = cli.main(["esquema", "portal-alup", "--tabelas", "uc,client,bandeira"])

    linhas = capsys.readouterr().out.splitlines()
    assert codigo == 0
    assert linhas == [
        "uc.id | bigint | NOT NULL | PRI",
        "uc.nome | varchar(120) | NULL | ",
        "client.id | bigint | NOT NULL | PRI",
        "tabelas ausentes: bandeira",
    ]
    assert not any(linha.startswith("{") for linha in linhas)


def test_cli_erro_do_driver_sai_sem_usuario_nem_senha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def conectar(dsn: str) -> Any:
        raise OSError("falha ao abrir usuario-ficticio senha-ficticia em host.exemplo")

    monkeypatch.setattr(banco, "ler_secret", lambda fonte, campo: DSN)
    monkeypatch.setattr(banco, "conectar", conectar)

    codigo = cli.main(["esquema", "portal-alup", "--tabelas", "uc"])

    saida = capsys.readouterr().out
    assert codigo == 1
    assert "usuario-ficticio" not in saida and "senha-ficticia" not in saida
    assert "host.exemplo" in saida
