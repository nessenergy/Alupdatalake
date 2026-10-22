"""Operações sob demanda no Cloud Build (ADR 030): executar ingestão, conferir cargas, sondar rede, testar conexão.

As entradas chegam por substituição do gatilho e são validadas aqui antes de chegar ao `gcloud`.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess  # nosec B404
import sys
from collections.abc import Callable, Sequence

_CONECTOR = re.compile(r"^[a-z0-9_]+$")
_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URI = re.compile(r"^gs://[a-z0-9._-]+/[a-z0-9_=./-]+$")
_FONTE = re.compile(r"^[a-z0-9-]+$")
_SONDA = re.compile(r"^[a-z_]+$")
_PROJETO = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_REGIAO = re.compile(r"^[a-z0-9][a-z0-9-]*$")

# O job que serve de casca de execução para a sonda (mesmo contêiner dos demais).
_JOB_SONDA = "ingestao-bcb-cambio-ptax"

Executor = Callable[[list[str]], tuple[int, str]]


class EntradaInvalida(ValueError):  # noqa: N818 - nome fixado pelo contrato da tarefa
    """Entrada fora do formato esperado; nada chega ao gcloud."""


def ingestao(conector: str, de: str = "", ate: str = "", uri: str = "") -> tuple[str, list[str], str]:
    """Valida a entrada e devolve (job, args do gcloud, descrição da janela)."""
    if not _CONECTOR.fullmatch(conector):
        raise EntradaInvalida("conector inválido: use o rótulo em snake_case")
    for data in (de, ate):
        if data and not _DATA.fullmatch(data):
            raise EntradaInvalida("data inválida: use AAAA-MM-DD")
    if bool(de) != bool(ate):
        raise EntradaInvalida("informe de e ate juntos, ou nenhum dos dois")
    if uri and not _URI.fullmatch(uri):
        raise EntradaInvalida("uri inválida: use gs://bucket/fonte/entidade/dt=AAAA-MM-DD/id.json.gz")
    if uri and not de:
        raise EntradaInvalida("replay exige a janela original em de/ate")
    job = f"ingestao-{conector.replace('_', '-')}"
    if uri:
        args = [f"--args=reprocessar-raw,{conector},--uri,{uri},--de,{de},--ate,{ate}"]
        return job, args, f"replay de {uri} ({de} a {ate})"
    if de:
        return job, [f"--args=ingerir,{conector},--de,{de},--ate,{ate}"], f"{de} a {ate}"
    return job, [], "a do agendamento"


def job_teste_conexao(fonte: str) -> str:
    if not _FONTE.fullmatch(fonte):
        raise EntradaInvalida("fonte inválida: use o nome do secret, como fmb")
    return f"teste-conexao-{fonte}"


def args_sonda(sonda: str) -> list[str]:
    if not _SONDA.fullmatch(sonda):
        raise EntradaInvalida("sonda inválida")
    return [f"--args=sondar,{sonda}"]


def _rodar(cmd: list[str]) -> tuple[int, str]:
    # Entradas já validadas pelas regex acima; comando montado como lista, sem shell.
    resultado = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603  # nosec B603
    saida = resultado.stdout + resultado.stderr
    print(saida)
    return resultado.returncode, saida


def executar_job(job: str, args: list[str], projeto: str, regiao: str, executor: Executor = _rodar) -> int:
    """Executa o Cloud Run Job e espera. Se falhar, imprime o log do contêiner, que o `--wait` não mostra."""
    comando = ["gcloud", "run", "jobs", "execute", job, "--project", projeto, "--region", regiao, "--wait", *args]
    status, saida = executor(comando)
    if status == 0:
        return 0
    achada = re.search(r"executions describe ([a-zA-Z0-9-]+)", saida)
    if achada:
        filtro = (
            f'resource.type="cloud_run_job" AND resource.labels.job_name="{job}" '
            f'AND labels."run.googleapis.com/execution_name"="{achada.group(1)}"'
        )
        executor(
            [
                "gcloud",
                "logging",
                "read",
                filtro,
                "--project",
                projeto,
                "--order=asc",
                "--limit=500",
                "--format=value(timestamp,severity,textPayload)",
            ]
        )
    return status


def _sondar(sonda: str, projeto: str, regiao: str, executor: Executor) -> int:
    """Roda a sonda no job e lê o resultado no bucket raw (a SA de deploy não lê o Cloud Logging)."""
    args = args_sonda(sonda)
    executar_job(_JOB_SONDA, args, projeto, regiao, executor)
    bucket = f"gs://{projeto}-raw/sondas/{sonda}/"
    _, listagem = executor(["gcloud", "storage", "ls", bucket, "--project", projeto])
    objetos = sorted(linha.strip() for linha in listagem.splitlines() if linha.strip().startswith("gs://"))
    if not objetos:
        print(f"não achei o resultado em {bucket} (a sonda não gravou ou a SA não lê o bucket)")
        return 1
    status, _ = executor(["gcloud", "storage", "cat", objetos[-1], "--project", projeto])
    return status


def _conferir_cargas(projeto: str) -> int:
    ambiente = {**os.environ, "GCP_PROJECT_ID": projeto}
    return subprocess.run([sys.executable, "-m", "scripts.conferir_cargas"], env=ambiente, check=False).returncode  # noqa: S603  # nosec B603


def _exigir(valor: str | None, formato: re.Pattern[str], nome: str) -> str:
    if not valor or not formato.fullmatch(valor):
        raise EntradaInvalida(f"{nome} inválido ou ausente")
    return valor


def main(argv: Sequence[str] | None = None, executor: Executor = _rodar) -> int:
    """Linha de comando usada pelos gatilhos do Cloud Build. Flag vazia vale como ausente."""
    parser = argparse.ArgumentParser(prog="python -m scripts.operacoes")
    parser.add_argument("operacao", choices=["executar-ingestao", "conferir-cargas", "sondar-rede", "testar-conexao"])
    parser.add_argument("--projeto", default="")
    parser.add_argument("--regiao", default="")
    for flag in ("conector", "de", "ate", "uri", "fonte", "sonda"):
        parser.add_argument(f"--{flag}", default="")
    p = parser.parse_args(argv)
    try:
        projeto = _exigir(p.projeto, _PROJETO, "projeto")
        if p.operacao == "conferir-cargas":
            return _conferir_cargas(projeto)
        regiao = _exigir(p.regiao, _REGIAO, "regiao")
        if p.operacao == "executar-ingestao":
            job, args, janela = ingestao(p.conector, p.de, p.ate, p.uri)
            print(f"Job: {job}\nJanela: {janela}")
            return executar_job(job, args, projeto, regiao, executor)
        if p.operacao == "testar-conexao":
            return executar_job(job_teste_conexao(p.fonte), [], projeto, regiao, executor)
        return _sondar(p.sonda, projeto, regiao, executor)
    except EntradaInvalida as erro:
        print(erro)
        return 1


if __name__ == "__main__":
    sys.exit(main())
