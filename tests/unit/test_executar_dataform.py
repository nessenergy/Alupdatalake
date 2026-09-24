"""Execução do Dataform no deploy — sem rede, com sessão simulada."""

from __future__ import annotations

import logging

import pytest
from scripts.executar_dataform import erros_de_compilacao, executar, repositorio

REPO = repositorio("alupdata-test", "us-central1")


class Resposta:
    def __init__(self, corpo: dict) -> None:
        self._corpo = corpo

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._corpo


class SessaoFalsa:
    def __init__(self, compilacao: dict, estados: list[str]) -> None:
        self.compilacao = compilacao
        self.estados = list(estados)
        self.chamadas: list[tuple[str, str, dict | None]] = []

    def post(self, url: str, json: dict) -> Resposta:
        self.chamadas.append(("POST", url, json))
        if url.endswith("/compilationResults"):
            return Resposta(self.compilacao)
        return Resposta({"name": f"{REPO}/workflowInvocations/inv1"})

    def get(self, url: str) -> Resposta:
        self.chamadas.append(("GET", url, None))
        if url.endswith(":query"):
            return Resposta({"workflowInvocationActions": self.acoes})
        return Resposta({"state": self.estados.pop(0)})

    acoes: list[dict] = []


def test_repositorio_monta_o_nome_completo() -> None:
    assert REPO == "projects/alupdata-test/locations/us-central1/repositories/alupdata"


def test_compila_a_release_main_e_executa_com_a_service_account() -> None:
    sessao = SessaoFalsa({"name": f"{REPO}/compilationResults/c1"}, ["RUNNING", "SUCCEEDED"])

    estado = executar(sessao, REPO, "alupdata-dataform@alupdata-test.iam.gserviceaccount.com", intervalo=0)

    assert estado == "SUCCEEDED"
    _, _, compilacao = sessao.chamadas[0]
    assert compilacao == {"releaseConfig": f"{REPO}/releaseConfigs/main"}
    _, url, invocacao = sessao.chamadas[1]
    assert url.endswith("/workflowInvocations")
    assert invocacao["compilationResult"] == f"{REPO}/compilationResults/c1"
    assert invocacao["invocationConfig"]["serviceAccount"].startswith("alupdata-dataform@")


def test_erro_de_compilacao_interrompe_antes_de_executar() -> None:
    compilacao = {"name": "c1", "compilationErrors": [{"path": "definitions/silver/x.sqlx", "message": "ref"}]}
    sessao = SessaoFalsa(compilacao, [])

    with pytest.raises(RuntimeError, match="definitions/silver/x.sqlx: ref"):
        executar(sessao, REPO, "sa", intervalo=0)
    assert len(sessao.chamadas) == 1


def test_estado_terminal_de_falha_e_devolvido() -> None:
    sessao = SessaoFalsa({"name": "c1"}, ["FAILED"])
    assert executar(sessao, REPO, "sa", intervalo=0) == "FAILED"


def test_execucao_sem_fim_estoura_o_limite() -> None:
    sessao = SessaoFalsa({"name": "c1"}, ["RUNNING"] * 5)
    with pytest.raises(TimeoutError):
        executar(sessao, REPO, "sa", intervalo=0, limite=0)


def test_erros_de_compilacao_vazio_quando_nao_ha_erro() -> None:
    assert erros_de_compilacao({"name": "c1"}) == []


def test_repositorio_aceita_nome_customizado() -> None:
    assert (
        repositorio("alupdata-test", "us-central1", "outro")
        == "projects/alupdata-test/locations/us-central1/repositories/outro"
    )


class RespostaComErro:
    """Simula uma resposta HTTP de erro, com corpo de mensagem da API."""

    def __init__(self, texto: str) -> None:
        self.text = texto

    def raise_for_status(self) -> None:
        raise RuntimeError("HTTP 400")

    def json(self) -> dict:
        return {}


def test_erro_http_registra_o_corpo_da_resposta_no_log(caplog: pytest.LogCaptureFixture) -> None:
    class SessaoComErro:
        def post(self, url: str, json: dict) -> RespostaComErro:
            return RespostaComErro("mensagem de erro da API do Dataform")

    with caplog.at_level(logging.ERROR, logger="executar-dataform"), pytest.raises(RuntimeError):
        executar(SessaoComErro(), REPO, "sa", intervalo=0)

    assert "mensagem de erro da API do Dataform" in caplog.text


def test_falha_nomeia_cada_acao_reprovada_e_o_motivo(caplog: pytest.LogCaptureFixture) -> None:
    """Em 24/09 o primeiro Dataform real terminou em FAILED, e o log só dizia isso.

    Sem o nome da ação e o motivo, a causa exige acesso ao console — que a
    conta de quem opera não tem. A execução já sabe o motivo; o deploy tem de
    dizê-lo.
    """
    sessao = SessaoFalsa({"name": "c1"}, ["FAILED"])
    sessao.acoes = [
        {"target": {"schema": "bronze", "name": "bcb_cambio_ptax"}, "state": "SUCCEEDED"},
        {"target": {"schema": "silver", "name": "ons_carga"}, "state": "FAILED", "failureReason": "Not found: Table x"},
        {"target": {"schema": "gold", "name": "carga_mensal"}, "state": "SKIPPED"},
    ]

    with caplog.at_level(logging.ERROR, logger="executar-dataform"):
        assert executar(sessao, REPO, "sa", intervalo=0) == "FAILED"

    assert "silver.ons_carga: Not found: Table x" in caplog.text
    assert "bronze.bcb_cambio_ptax" not in caplog.text  # só o que reprovou
    assert any(url.endswith("/workflowInvocations/inv1:query") for _, url, _ in sessao.chamadas)


def test_sucesso_nao_consulta_as_acoes() -> None:
    sessao = SessaoFalsa({"name": "c1"}, ["SUCCEEDED"])
    assert executar(sessao, REPO, "sa", intervalo=0) == "SUCCEEDED"
    assert not any(url.endswith(":query") for _, url, _ in sessao.chamadas)
