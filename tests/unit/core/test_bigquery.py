"""Carga e controle BigQuery com clientes simulados."""

from __future__ import annotations

import re
import uuid

import pytest
from src.core import bigquery as bq
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


# ---------------------------------------------------------------- rótulos FinOps


def test_rotulos_trazem_os_eixos_de_atribuicao_de_custo():
    """Sem estes eixos a fatura vira massa indistinta — e não se rateia depois."""
    execucao = Execucao(fonte="ons", entidade="carga", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    r = bq.rotulos(execucao)
    assert r["projeto"] == "alupdata"
    assert r["fonte"] == "ons"
    assert r["entidade"] == "carga"
    assert r["camada"] == "bronze"
    assert r["modo"] == "fonte"
    assert r["ingestao_id"] == execucao.ingestao_id


def test_rotulo_recusado_pelo_bigquery_nao_quebra_a_carga():
    """Maiúscula, ponto e acento fariam o job ser recusado inteiro."""
    execucao = Execucao(fonte="RM.TOTVS", entidade="Contas a Pagar", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    r = bq.rotulos(execucao)
    assert r["fonte"] == "rm-totvs"
    assert r["entidade"] == "contas-a-pagar"
    for chave, valor in r.items():
        assert re.fullmatch(r"[a-z0-9_-]{0,63}", valor), (chave, valor)


def test_rotulo_longo_e_truncado_no_limite_do_bigquery():
    execucao = Execucao(fonte="f" * 100, entidade="e", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    assert len(bq.rotulos(execucao)["fonte"]) == 63


def test_replay_e_distinguivel_na_fatura():
    """Reprocessamento custa varredura; separar do primeiro carregamento importa."""
    execucao = Execucao(
        fonte="bcb", entidade="cambio_ptax", janela=Janela.de_texto("2026-01-01", "2026-01-02"), modo="REPLAY"
    )
    assert bq.rotulos(execucao)["modo"] == "replay"


def test_carga_leva_os_rotulos_para_o_job(monkeypatch):
    """O rótulo tem de chegar no job; rotular só o recurso não separa por fonte."""
    capturado = {}

    class FakeJob:
        def result(self):
            return None

    class FakeCliente:
        def load_table_from_json(self, linhas, tabela, job_config):
            capturado["labels"] = job_config.labels
            return FakeJob()

    monkeypatch.setenv("DRY_RUN", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(bq, "cliente", lambda: FakeCliente())
    execucao = Execucao(fonte="ons", entidade="carga", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    bq.carregar_bronze(execucao, [{"a": 1}])
    assert capturado["labels"]["fonte"] == "ons"
    assert capturado["labels"]["camada"] == "bronze"
