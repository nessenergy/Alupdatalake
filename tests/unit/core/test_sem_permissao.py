"""`SemPermissaoError` fecha a execução como SEM_PERMISSAO: erro visível, mas sem derrubar o job."""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest
from pydantic import BaseModel
from src.cli import main
from src.core.conector import Conector, SemPermissaoError
from src.core.config import get_settings
from src.core.execucao import Execucao, Janela


class Registro(BaseModel):
    data_referencia: date


class SemAcesso(Conector):
    fonte = "teste"
    entidade = "sem_permissao"
    schema = Registro

    def extrair(self, janela: Janela):
        del janela
        raise SemPermissaoError("Fault Server.4001 [errorCode=4001]")
        yield  # pragma: no cover — faz de `extrair` um gerador

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return bruto


class ComErro(SemAcesso):
    entidade = "com_erro"

    def extrair(self, janela: Janela):
        del janela
        raise RuntimeError("nosso")
        yield  # pragma: no cover


@pytest.fixture
def execucoes(monkeypatch):
    gravadas: list[Execucao] = []
    monkeypatch.setattr("src.core.conector.registrar_inicio", lambda _e: None)
    monkeypatch.setattr("src.core.conector.registrar_execucao", gravadas.append)
    monkeypatch.setattr(get_settings(), "dry_run", True)
    return gravadas


JANELA = Janela.de_texto("2026-11-01", "2026-11-09")


def test_status_sem_permissao_guarda_o_erro(execucoes):
    execucao = SemAcesso().ingerir(JANELA)

    assert execucao.status == "SEM_PERMISSAO"
    assert "errorCode=4001" in execucao.erro
    assert execucoes == [execucao]
    assert execucao.to_row()["status"] == "SEM_PERMISSAO"
    assert execucao.to_row()["erro"]


def test_o_log_avisa_em_warning_e_nao_em_error(execucoes, caplog):
    SemAcesso().ingerir(JANELA)

    registros = [r for r in caplog.records if "sem permissão" in r.getMessage()]
    assert registros
    assert {r.levelname for r in registros} == {"WARNING"}


def test_outro_erro_continua_erro_e_sobe(execucoes):
    with pytest.raises(RuntimeError, match="nosso"):
        ComErro().ingerir(JANELA)

    assert execucoes[0].status == "ERRO"


def test_cli_sai_com_zero_em_sem_permissao_e_sobe_o_erro_nos_outros_casos(execucoes, monkeypatch):
    argumentos = ["ingerir", "x", "--de", "2026-11-01", "--ate", "2026-11-09"]

    monkeypatch.setattr("src.cli.obter", lambda _rotulo: SemAcesso())
    assert main(argumentos) == 0

    monkeypatch.setattr("src.cli.obter", lambda _rotulo: ComErro())
    with pytest.raises(RuntimeError):
        main(argumentos)
