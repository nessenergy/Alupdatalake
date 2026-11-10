"""Conectores do MySQL Alup (Onda 3): SQL montado, janela, campos recusados e schema, sem rede.

A fixture é sintética: nenhum valor veio do banco da Alup. O contrato de colunas é o
`docs/dicionario-dados/mysql_alup_esquema.md`.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError
from src.conectores import mysql_alup
from src.conectores.mysql_alup import (
    PortalAlupBandeira,
    PortalAlupClient,
    PortalAlupFaturasProcessadas,
    PortalAlupInvoice,
    PortalAlupUc,
)
from src.core.execucao import Janela
from src.core.registry import carregar_conectores, listar

JANELA = Janela.de_texto("2026-11-01", "2026-11-07")
RETRATOS = [PortalAlupClient, PortalAlupUc, PortalAlupBandeira]
INCREMENTAIS = [PortalAlupInvoice, PortalAlupFaturasProcessadas]
TODOS = RETRATOS + INCREMENTAIS
# O que a spec decidiu não ler: dado pessoal, endereço de arquivo e JSON de conteúdo desconhecido.
NAO_LIDAS = {
    "uc": ["address", "vendedor"],
    "invoice": ["barcode", "s3_key", "s3_key_report", "s3_key_xml", "s3_key_danfe", "nfe", "jsonInfo"],
    "faturas_processadas": ["nome"],
}


class CursorFalso:
    def __init__(self, linhas: list[tuple[Any, ...]], colunas: list[str], registro: list[tuple[str, dict]]):
        self._linhas = list(linhas)
        self.description = [(c,) for c in colunas]
        self._registro = registro

    def execute(self, sql: str, parametros: dict[str, Any]) -> None:
        self._registro.append((sql, parametros))

    def fetchmany(self, tamanho: int) -> list[tuple[Any, ...]]:
        lote, self._linhas = self._linhas[:tamanho], self._linhas[tamanho:]
        return lote

    def close(self) -> None:
        pass


class ConexaoFalsa:
    def __init__(self, cursor: CursorFalso):
        self._cursor = cursor

    def cursor(self) -> CursorFalso:
        return self._cursor


@pytest.fixture
def banco(monkeypatch: pytest.MonkeyPatch):
    """Troca a conexão por um cursor falso; devolve `(registro, definir_linhas, fontes_abertas)`."""
    estado: dict[str, Any] = {"linhas": [], "colunas": []}
    registro: list[tuple[str, dict]] = []
    fontes: list[str] = []

    @contextmanager
    def abrir(fonte: str, campo: str = "dsn"):
        fontes.append(f"{fonte}/{campo}")
        yield ConexaoFalsa(CursorFalso(estado["linhas"], estado["colunas"], registro))

    monkeypatch.setattr(mysql_alup, "abrir_conexao", abrir)

    def definir(colunas: list[str], linhas: list[tuple[Any, ...]]) -> None:
        estado["colunas"], estado["linhas"] = colunas, linhas

    return registro, definir, fontes


def test_os_cinco_conectores_estao_registrados_sob_a_fonte_portal_alup():
    carregar_conectores()
    esperados = {
        "portal_alup_client",
        "portal_alup_uc",
        "portal_alup_bandeira",
        "portal_alup_invoice",
        "portal_alup_faturas_processadas",
    }
    assert esperados <= set(listar())
    assert {c.tabela for c in TODOS} == {"client", "uc", "bandeira", "invoice", "faturas_processadas"}


@pytest.mark.parametrize("conector", TODOS)
def test_o_select_so_tem_constantes_e_so_le(conector):
    sql = conector.sql()

    assert sql.startswith("SELECT ")
    assert f"FROM `{conector.tabela}`" in sql
    assert ";" not in sql
    assert all(f"`{origem}` AS {destino}" in sql for origem, destino in conector.colunas.items())


@pytest.mark.parametrize("conector", TODOS)
def test_coluna_sem_finalidade_nao_entra_no_select_nem_no_schema(conector):
    for coluna in NAO_LIDAS.get(conector.tabela, []):
        assert coluna not in conector.colunas
        assert f"`{coluna}`" not in conector.sql()
    campos_do_schema = set(conector.schema.model_fields)
    assert set(conector.colunas.values()) <= campos_do_schema


@pytest.mark.parametrize("conector", RETRATOS)
def test_cadastro_le_a_tabela_inteira_sem_filtro_de_data(conector):
    assert "WHERE" not in conector.sql()


@pytest.mark.parametrize("conector", INCREMENTAIS)
def test_fato_filtra_pela_modificacao_com_fim_exclusivo(conector):
    sql = conector.sql()

    assert "COALESCE(" in sql
    assert ">= %(inicio)s" in sql
    assert "< %(fim)s" in sql


def test_camel_case_ganha_apelido_em_snake_case():
    assert PortalAlupFaturasProcessadas.colunas["idUc"] == "id_uc"
    assert PortalAlupFaturasProcessadas.colunas["idTransacaoFMB"] == "id_transacao_fmb"
    assert PortalAlupFaturasProcessadas.colunas["cnpjEmpresaDestino"] == "cnpj_empresa_destino"


def test_retrato_ignora_a_janela_e_carimba_a_data_do_fim(banco):
    registro, definir, fontes = banco
    definir(["id", "nickname", "corporate_name", "cnpj"], [(1, "Alfa", "Alfa Ltda", "00.000.000/0001-00")])

    linhas = list(PortalAlupClient().extrair(JANELA))

    assert fontes == ["portal-alup/dsn"]  # a DSN vem do secret alupdata-portal-alup-dsn
    assert registro[0][1] == {}  # nenhum parâmetro de janela
    assert linhas == [
        {
            "id": 1,
            "nickname": "Alfa",
            "corporate_name": "Alfa Ltda",
            "cnpj": "00.000.000/0001-00",
            "data_referencia": "2026-11-07",
        }
    ]


def test_retrato_e_idempotente_na_extracao(banco):
    _, definir, _ = banco
    linha = (1, "Alfa", "Alfa Ltda", "00.000.000/0001-00")
    definir(["id", "nickname", "corporate_name", "cnpj"], [linha])
    primeira = list(PortalAlupClient().extrair(JANELA))
    definir(["id", "nickname", "corporate_name", "cnpj"], [linha])

    assert list(PortalAlupClient().extrair(JANELA)) == primeira


def test_cliente_sem_id_e_rejeitado():
    with pytest.raises(ValidationError):
        PortalAlupClient.schema.model_validate({"id": None, "cnpj": "x", "data_referencia": "2026-11-07"})


def test_uc_aceita_linha_sintetica_com_tipos_do_dicionario():
    registro = PortalAlupUc.schema.model_validate(
        {
            "id": "UC-0001",
            "client_id": 1,
            "contrato": "C-1",
            "cnpj": "00.000.000/0001-00",
            "state": "SP",
            "contract_start_date": date(2026, 1, 1),
            "submarket": "SE",
            "contracted_demand_peak": "100.50",
            "ccee_last_date": datetime(2026, 11, 1, 3, 0),
            "id_contrato": 7,
            "data_referencia": "2026-11-07",
        }
    )

    assert registro.contracted_demand_peak == Decimal("100.50")
    assert registro.model_dump(mode="json")["ccee_last_date"] == "2026-11-01T03:00:00"


def test_uc_sem_id_e_rejeitado():
    with pytest.raises(ValidationError):
        PortalAlupUc.schema.model_validate({"id": "  ", "data_referencia": "2026-11-07"})


def test_bandeira_guarda_o_mes_como_texto_e_o_valor_como_decimal():
    registro = PortalAlupBandeira.schema.model_validate(
        {"id": 1, "mes": "2026-11", "bandeira": "Amarela", "valor": 1.885, "data_referencia": "2026-11-07"}
    )

    assert registro.mes == "2026-11"
    assert registro.valor == Decimal("1.885")


def test_fato_passa_a_janela_como_datas_de_inicio_e_fim_exclusivo(banco):
    registro, definir, _ = banco
    definir(["id"], [])

    list(PortalAlupInvoice().extrair(JANELA))

    assert registro[0][1] == {"inicio": datetime(2026, 11, 1), "fim": datetime(2026, 11, 8)}


def test_fato_nao_carimba_data_referencia(banco):
    _, definir, _ = banco
    definir(["id", "client_id"], [(9, 1)])

    (linha,) = PortalAlupInvoice().extrair(JANELA)

    assert "data_referencia" not in linha


def test_fatura_aceita_linha_sintetica_e_mantem_o_json_como_texto():
    registro = PortalAlupFaturasProcessadas.schema.model_validate(
        {
            "id": 5,
            "id_uc": "UC-0001",
            "id_transacao_fmb": "T1",
            "id_pre_fatura_fmb": "P1",
            "id_contrato": "10",
            "mes_suprimento": "2026-10",
            "quantidade": "12.5000",
            "valor_total": "1500.00",
            "consumidor_final": 1,
            "parcelas": '[{"n": 1}]',
            "updated_at": datetime(2026, 11, 2, 8, 30),
        }
    )

    assert registro.consumidor_final is True
    assert registro.parcelas == '[{"n": 1}]'


def test_invoice_aceita_linha_sintetica():
    registro = PortalAlupInvoice.schema.model_validate(
        {
            "id": 1,
            "client_id": 1,
            "uc_id": "UC-0001",
            "month": "2026-10",
            "consumption": "100.000",
            "value": "250.00",
            "tax": "10.00",
            "status": 1,
            "due_date": date(2026, 11, 10),
            "updated_at": None,
            "created_at": datetime(2026, 11, 1, 9, 0),
        }
    )

    assert registro.value == Decimal("250.00")
    assert registro.updated_at is None
