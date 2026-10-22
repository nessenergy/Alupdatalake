"""Operações sob demanda: validação das entradas e comandos. As regras são as dos workflows de hoje."""

from __future__ import annotations

import subprocess
from types import SimpleNamespace

import pytest
from scripts.operacoes import EntradaInvalida, Executor, args_sonda, executar_job, ingestao, job_teste_conexao, main


def test_ingestao_sem_janela_usa_a_do_agendamento() -> None:
    assert ingestao("ons_carga") == ("ingestao-ons-carga", [], "a do agendamento")


def test_ingestao_com_janela() -> None:
    job, args, janela = ingestao("cptec_previsao", "2026-10-01", "2026-10-21")

    assert job == "ingestao-cptec-previsao"
    assert args == ["--args=ingerir,cptec_previsao,--de,2026-10-01,--ate,2026-10-21"]
    assert janela == "2026-10-01 a 2026-10-21"


def test_replay_exige_a_janela_original() -> None:
    uri = "gs://alupar-dev-alupdata-raw/ons/carga/dt=2026-10-01/abc.json.gz"
    _, args, _ = ingestao("ons_carga", "2026-10-01", "2026-10-01", uri)
    assert args == [f"--args=reprocessar-raw,ons_carga,--uri,{uri},--de,2026-10-01,--ate,2026-10-01"]
    with pytest.raises(EntradaInvalida, match="janela"):
        ingestao("ons_carga", uri=uri)


@pytest.mark.parametrize(
    ("kw", "trecho"),
    [
        ({"conector": "ONS-carga; rm -rf /"}, "conector"),
        ({"conector": "ons_carga", "de": "2026-10-01"}, "juntos"),
        ({"conector": "ons_carga", "de": "01/10/2026", "ate": "02/10/2026"}, "data"),
        ({"conector": "ons_carga", "de": "2026-10-01", "ate": "2026-10-02", "uri": "http://x/y"}, "uri"),
    ],
)
def test_entrada_invalida_e_recusada_antes_do_gcloud(kw: dict, trecho: str) -> None:
    with pytest.raises(EntradaInvalida, match=trecho):
        ingestao(**kw)


def test_teste_de_conexao_e_sonda_validam_o_nome() -> None:
    assert job_teste_conexao("portal-alup") == "teste-conexao-portal-alup"
    assert args_sonda("cptec") == ["--args=sondar,cptec"]
    for chamada, valor in ((job_teste_conexao, "fmb;ls"), (args_sonda, "CPTEC")):
        with pytest.raises(EntradaInvalida):
            chamada(valor)


def test_job_que_falha_busca_o_log_do_conteiner_e_devolve_o_status() -> None:
    chamadas: list[list[str]] = []

    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        if cmd[:4] == ["gcloud", "run", "jobs", "execute"]:
            return 1, "To describe: gcloud run jobs executions describe ingestao-ons-carga-abc12"
        return 0, "linha de log"

    status = executar_job("ingestao-ons-carga", [], "alupar-dev-alupdata", "us-central1", executor=executor)

    assert status == 1
    assert chamadas[0][:6] == ["gcloud", "run", "jobs", "execute", "ingestao-ons-carga", "--project"]
    assert chamadas[1][:3] == ["gcloud", "logging", "read"]
    assert "ingestao-ons-carga-abc12" in " ".join(chamadas[1])


def test_job_que_passa_nao_le_log() -> None:
    chamadas: list[list[str]] = []

    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        return 0, ""

    assert executar_job("ingestao-ons-carga", [], "p", "r", executor=executor) == 0
    assert len(chamadas) == 1


def _executor_falso(chamadas: list[list[str]], saida: str = "") -> Executor:
    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        return 0, saida

    return executor


def test_main_executar_ingestao_com_flags_vazias_usa_a_janela_do_agendamento() -> None:
    chamadas: list[list[str]] = []
    argv = ["executar-ingestao", "--projeto", "p", "--regiao", "r", "--conector", "ons_carga"]
    argv += ["--de", "", "--ate", "", "--uri", ""]

    assert main(argv, executor=_executor_falso(chamadas)) == 0
    assert chamadas == [
        ["gcloud", "run", "jobs", "execute", "ingestao-ons-carga", "--project", "p", "--region", "r", "--wait"]
    ]


def test_main_executar_ingestao_com_replay() -> None:
    chamadas: list[list[str]] = []
    uri = "gs://p-raw/ons/carga/dt=2026-10-01/abc.json.gz"
    argv = ["executar-ingestao", "--projeto", "p", "--regiao", "r", "--conector", "ons_carga"]
    argv += ["--de", "2026-10-01", "--ate", "2026-10-01", "--uri", uri]

    assert main(argv, executor=_executor_falso(chamadas)) == 0
    assert chamadas[0][-1] == f"--args=reprocessar-raw,ons_carga,--uri,{uri},--de,2026-10-01,--ate,2026-10-01"


def test_main_entrada_invalida_devolve_1_sem_chamar_o_executor(capsys: pytest.CaptureFixture[str]) -> None:
    chamadas: list[list[str]] = []
    argv = ["executar-ingestao", "--projeto", "p", "--regiao", "r", "--conector", "ONS; rm", "--de", "", "--ate", ""]

    assert main(argv, executor=_executor_falso(chamadas)) == 1
    assert chamadas == []
    assert "conector inválido" in capsys.readouterr().out


def test_main_testar_conexao() -> None:
    chamadas: list[list[str]] = []
    argv = ["testar-conexao", "--projeto", "p", "--regiao", "r", "--fonte", "portal-alup"]

    assert main(argv, executor=_executor_falso(chamadas)) == 0
    assert chamadas[0][4] == "teste-conexao-portal-alup"


def test_main_sondar_rede_le_o_ultimo_resultado_do_bucket() -> None:
    chamadas: list[list[str]] = []
    saida = "gs://p-raw/sondas/cptec/a.json\ngs://p-raw/sondas/cptec/b.json\n"
    argv = ["sondar-rede", "--projeto", "p", "--regiao", "r", "--sonda", "cptec"]

    assert main(argv, executor=_executor_falso(chamadas, saida)) == 0
    assert chamadas[0][4] == "ingestao-bcb-cambio-ptax"
    assert chamadas[1][:4] == ["gcloud", "storage", "ls", "gs://p-raw/sondas/cptec/"]
    assert chamadas[2][:4] == ["gcloud", "storage", "cat", "gs://p-raw/sondas/cptec/b.json"]


def test_main_sondar_rede_com_job_falho_nao_lista_o_bucket() -> None:
    chamadas: list[list[str]] = []

    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        return 1, ""

    argv = ["sondar-rede", "--projeto", "p", "--regiao", "r", "--sonda", "cptec"]

    assert main(argv, executor=executor) == 1
    assert not any(c[:3] == ["gcloud", "storage", "ls"] for c in chamadas)


def test_testar_conexao_sem_linha_describe_acha_a_execucao_pela_listagem() -> None:
    chamadas: list[list[str]] = []

    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        if cmd[:4] == ["gcloud", "run", "jobs", "execute"]:
            return 1, "The execution failed"
        if cmd[:5] == ["gcloud", "run", "jobs", "executions", "list"]:
            return 0, "teste-conexao-fmb-xyz99\n"
        return 0, "log"

    argv = ["testar-conexao", "--projeto", "p", "--regiao", "r", "--fonte", "fmb"]

    assert main(argv, executor=executor) == 1
    assert chamadas[1][:5] == ["gcloud", "run", "jobs", "executions", "list"]
    assert chamadas[1][5:8] == ["--job", "teste-conexao-fmb", "--project"]
    assert chamadas[2][:3] == ["gcloud", "logging", "read"]
    assert "teste-conexao-fmb-xyz99" in chamadas[2][3]
    assert "--limit=200" in chamadas[2]


def test_ingestao_sem_linha_describe_nao_lista_execucoes() -> None:
    chamadas: list[list[str]] = []

    def executor(cmd: list[str]) -> tuple[int, str]:
        chamadas.append(cmd)
        return 1, "The execution failed"

    assert executar_job("ingestao-ons-carga", [], "p", "r", executor=executor) == 1
    assert len(chamadas) == 1


def test_main_conferir_cargas_passa_o_projeto_no_env_e_propaga_o_status(monkeypatch: pytest.MonkeyPatch) -> None:
    capturado: dict = {}

    def falso(cmd: list[str], **kw: object) -> SimpleNamespace:
        capturado.update(cmd=cmd, env=kw["env"])
        return SimpleNamespace(returncode=3)

    monkeypatch.setattr(subprocess, "run", falso)

    assert main(["conferir-cargas", "--projeto", "meu-proj", "--regiao", ""]) == 3
    assert capturado["cmd"][1:] == ["-m", "scripts.conferir_cargas"]
    assert capturado["env"]["GCP_PROJECT_ID"] == "meu-proj"


def test_main_projeto_invalido_devolve_1_sem_chamar_o_executor() -> None:
    chamadas: list[list[str]] = []
    argv = ["testar-conexao", "--projeto", "--wait; x", "--regiao", "r", "--fonte", "fmb"]

    assert main(argv, executor=_executor_falso(chamadas)) == 1
    assert chamadas == []
