"""Carga e controle BigQuery com clientes simulados."""

from __future__ import annotations

import uuid

import pytest
from src.core.bigquery import RegistroExecucaoError, registrar_execucao
from src.core.config import get_settings
from src.core.execucao import Execucao, Janela


def _execucao() -> Execucao:
    execucao = Execucao(fonte="teste", entidade="medicao", janela=Janela.de_texto("2026-01-01", "2026-01-01"))
    execucao.encerrar()
    return execucao


def test_registrar_execucao_falha_alto_quando_bigquery_recusa(monkeypatch: pytest.MonkeyPatch) -> None:
    class ClienteFalso:
        def insert_rows_json(self, _tabela, _linhas):
            return [{"reason": "invalid"}]

    get_settings().dry_run = False
    monkeypatch.setattr("src.core.bigquery.cliente", ClienteFalso)

    with pytest.raises(RegistroExecucaoError, match="recusou"):
        registrar_execucao(_execucao())


def test_erro_do_cliente_e_sanitizado(monkeypatch: pytest.MonkeyPatch) -> None:
    marcador = uuid.uuid4().hex

    class ClienteFalso:
        def insert_rows_json(self, _tabela, _linhas):
            raise RuntimeError(f"Bearer {marcador}")

    get_settings().dry_run = False
    monkeypatch.setattr("src.core.bigquery.cliente", ClienteFalso)

    with pytest.raises(RegistroExecucaoError) as erro:
        registrar_execucao(_execucao())

    assert marcador not in str(erro.value)
