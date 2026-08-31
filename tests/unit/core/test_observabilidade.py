"""Log estruturado: severidade, correlação por execução e agrupamento de erro."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date

import pytest
from src.core.execucao import Execucao, Janela
from src.core.observabilidade import (
    FormatadorJson,
    configurar_logging,
    contexto_execucao,
)


@pytest.fixture
def execucao() -> Execucao:
    return Execucao(fonte="bcb", entidade="cambio_ptax", janela=Janela(date(2026, 8, 25), date(2026, 8, 26)))


def _registro(nivel: int = logging.INFO, mensagem: str = "oi", **kwargs) -> logging.LogRecord:
    return logging.LogRecord("src.teste", nivel, "arquivo.py", 1, mensagem, (), kwargs.get("exc_info"))


def test_linha_e_json_com_severidade_que_o_cloud_logging_entende() -> None:
    saida = json.loads(FormatadorJson().format(_registro(logging.WARNING, "cuidado")))
    assert saida["severity"] == "WARNING"  # não "levelname": o Cloud Logging lê `severity`
    assert saida["message"] == "cuidado"
    assert saida["logger"] == "src.teste"


def test_fora_de_execucao_nao_inventa_correlacao() -> None:
    saida = json.loads(FormatadorJson().format(_registro()))
    assert "ingestao_id" not in saida


def test_toda_linha_da_execucao_carrega_a_identidade(execucao: Execucao) -> None:
    with contexto_execucao(execucao):
        saida = json.loads(FormatadorJson().format(_registro()))
    assert saida["ingestao_id"] == execucao.ingestao_id
    assert saida["fonte"] == "bcb"
    assert saida["entidade"] == "cambio_ptax"
    assert saida["janela"] == "2026-08-25..2026-08-26"


def test_contexto_e_desfeito_ao_sair(execucao: Execucao) -> None:
    with contexto_execucao(execucao):
        pass
    assert "ingestao_id" not in json.loads(FormatadorJson().format(_registro()))


def test_excecao_vira_stack_trace_para_o_error_reporting() -> None:
    try:
        raise ValueError("quebrou")
    except ValueError:
        import sys

        registro = _registro(logging.ERROR, "falhou", exc_info=sys.exc_info())
    saida = json.loads(FormatadorJson().format(registro))
    assert "ValueError: quebrou" in saida["stack_trace"]


def test_mensagem_e_stack_trace_sao_sanitizados() -> None:
    marcador = uuid.uuid4().hex
    try:
        raise ValueError(f"Bearer {marcador}")
    except ValueError:
        import sys

        registro = _registro(logging.ERROR, f"Authorization: Bearer {marcador}", exc_info=sys.exc_info())

    saida = json.loads(FormatadorJson().format(registro))
    assert marcador not in saida["message"]
    assert marcador not in saida["stack_trace"]


def test_formato_e_texto_no_laptop_e_json_no_cloud_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOG_FORMATO", raising=False)
    monkeypatch.delenv("CLOUD_RUN_JOB", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    configurar_logging()
    assert not isinstance(logging.getLogger().handlers[0].formatter, FormatadorJson)

    monkeypatch.setenv("CLOUD_RUN_JOB", "ingestao-bcb-cambio-ptax")
    configurar_logging()
    assert isinstance(logging.getLogger().handlers[0].formatter, FormatadorJson)


def test_variavel_explicita_vence_o_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLOUD_RUN_JOB", "x")
    monkeypatch.setenv("LOG_FORMATO", "texto")
    configurar_logging()
    assert not isinstance(logging.getLogger().handlers[0].formatter, FormatadorJson)


def test_configurar_duas_vezes_nao_duplica_linha(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOG_FORMATO", "json")
    configurar_logging()
    configurar_logging()
    assert len(logging.getLogger().handlers) == 1
