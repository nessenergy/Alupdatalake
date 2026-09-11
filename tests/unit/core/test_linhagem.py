"""Linhagem OpenLineage da origem ao Bronze — sem rede."""

from __future__ import annotations

import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel
from src.core import linhagem
from src.core.conector import Conector
from src.core.config import get_settings
from src.core.execucao import Execucao, Janela

if TYPE_CHECKING:
    import pytest


def _execucao(erro: str | None = None) -> Execucao:
    execucao = Execucao(fonte="bcb", entidade="cambio_ptax", janela=Janela.de_texto("2026-01-01", "2026-01-02"))
    execucao.encerrar(erro=erro)
    return execucao


def test_evento_liga_a_origem_custom_a_tabela_bronze():
    execucao = _execucao()

    corpo = linhagem.evento(execucao, "bcb.cambio_ptax", "alupdata-test.bronze.bcb_cambio_ptax")

    assert corpo["eventType"] == "COMPLETE"
    assert corpo["inputs"] == [{"namespace": "custom", "name": "bcb.cambio_ptax"}]
    assert corpo["outputs"] == [{"namespace": "bigquery", "name": "alupdata-test.bronze.bcb_cambio_ptax"}]
    assert corpo["job"] == {"namespace": "alupdata", "name": "ingestao.bcb_cambio_ptax"}
    assert uuid.UUID(corpo["run"]["runId"]).hex == execucao.ingestao_id
    assert corpo["eventTime"] == execucao.encerrada_em.isoformat()
    assert corpo["producer"].startswith("https://")


def test_evento_de_execucao_com_erro_e_fail():
    assert linhagem.evento(_execucao(erro="x"), "o", "p.bronze.t")["eventType"] == "FAIL"


def test_dry_run_nao_envia_nada():
    class SessaoProibida:
        def post(self, *_a, **_k):
            raise AssertionError("dry-run não pode chamar a API")

    linhagem.emitir(_execucao(), "bcb.cambio_ptax", sessao=SessaoProibida())


def test_envia_para_o_endpoint_da_regiao(monkeypatch: pytest.MonkeyPatch):
    enviado = {}

    class Resposta:
        def raise_for_status(self):
            return None

    class Sessao:
        def post(self, url, json, timeout):
            enviado.update(url=url, corpo=json, timeout=timeout)
            return Resposta()

    monkeypatch.setenv("DRY_RUN", "false")
    monkeypatch.setenv("GCP_REGION", "us-east1")
    get_settings.cache_clear()

    linhagem.emitir(_execucao(), "bcb.cambio_ptax", sessao=Sessao())

    assert enviado["url"] == (
        "https://datalineage.googleapis.com/v1/projects/alupdata-test/locations/us-east1:processOpenLineageRunEvent"
    )
    assert enviado["corpo"]["outputs"][0]["name"] == "alupdata-test.bronze.bcb_cambio_ptax"


def test_falha_ao_emitir_nao_derruba_e_nao_vaza_credencial(monkeypatch, caplog):
    marcador = uuid.uuid4().hex

    class Sessao:
        def post(self, *_a, **_k):
            raise RuntimeError(f"Bearer {marcador}")

    monkeypatch.setenv("DRY_RUN", "false")
    get_settings.cache_clear()

    with caplog.at_level(logging.WARNING, logger="src.core.linhagem"):
        linhagem.emitir(_execucao(), "bcb.cambio_ptax", sessao=Sessao())

    assert "linhagem não registrada" in caplog.text
    assert marcador not in caplog.text


class Registro(BaseModel):
    data_referencia: date
    valor: Decimal


class ConectorTeste(Conector):
    fonte = "teste"
    entidade = "medicao"
    schema = Registro

    def extrair(self, janela):
        del janela
        yield {"data_referencia": "2026-01-01", "valor": "1.5"}


def _silenciar_gcp(monkeypatch):
    monkeypatch.setattr("src.core.conector.gravar_raw", lambda *_a: None)
    monkeypatch.setattr("src.core.conector.carregar_bronze", lambda _e, linhas: len(linhas))
    monkeypatch.setattr("src.core.conector.registrar_execucao", lambda _e: None)


def test_ingestao_bem_sucedida_emite_uma_vez(monkeypatch):
    emitidos = []
    _silenciar_gcp(monkeypatch)
    monkeypatch.setattr("src.core.conector.emitir_linhagem", lambda e, origem: emitidos.append((e, origem)))

    execucao = ConectorTeste().ingerir(Janela.de_texto("2026-01-01", "2026-01-01"))

    assert emitidos == [(execucao, "teste.medicao")]


def test_replay_nao_emite(monkeypatch):
    emitidos = []
    _silenciar_gcp(monkeypatch)
    monkeypatch.setattr("src.core.conector.ler_raw", lambda _uri: [{"data_referencia": "2026-01-01", "valor": "1"}])
    monkeypatch.setattr("src.core.conector.emitir_linhagem", lambda *a: emitidos.append(a))

    ConectorTeste().reprocessar_raw(
        "gs://lake-raw/teste/medicao/dt=2026-01-01/origem123.json.gz", Janela.de_texto("2026-01-01", "2026-01-01")
    )

    assert emitidos == []
