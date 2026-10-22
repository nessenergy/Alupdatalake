# CI e CD completos fora do GitHub Actions — plano de execução

> **Para agentes:** usar `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans`, tarefa a tarefa. Os passos usam caixas `- [ ]`.

**Meta:** o GitHub Actions deixa de executar qualquer coisa do AlupData. O CI, o deploy, as operações sob demanda e os agendados passam a rodar no Cloud Build, e o GitHub fica só como repositório, PRs, issues, Projects e Dependabot.

**Arquitetura:** a lógica vive em `make` e em scripts do repositório, testados. Os arquivos do Cloud Build só chamam esses comandos. Cada ambiente (dev, hml, prod) tem os próprios gatilhos, que rodam como a conta de deploy daquele ambiente. Os agendados são Cloud Scheduler chamando a API do Cloud Build. Tudo isso é declarado em `infra/` (regra 5). Nenhuma credencial entra em arquivo; as do GitHub vêm do Secret Manager (regra 2).

**Tecnologia:** Cloud Build (gatilhos de GitHub e manuais), Cloud Scheduler, Terraform, Python 3.13 com `uv`, `cryptography` para assinar o token do GitHub App.

**Spec:** [ADR 030](../../arquitetura/decisoes/030-cicd-fora-do-github-actions.md) e o plano de fases [`2026-10-15-migracao-cicd.md`](2026-10-15-migracao-cicd.md), que este plano substitui nas Fases 1 a 4. As correções à ADR estão na Tarefa 0.

## Onde estamos em 22/10/2026

| Peça | Estado |
|---|---|
| Alvos `make ci-*` e `cloudbuild/ci.yaml` | feito |
| Gatilhos de PR e de push na `main` (`infra/modules/cicd`, só em dev) | **no ar e verdes** desde o PR #408: lint, testes, SAST, segredos, Terraform, Dataform e SCA |
| Checagem de atribuição (regra 6) no Cloud Build | **fora**: o build não tem credencial para buscar a `main` do repositório privado |
| Deploy, operações, agendados | só no Actions |
| Gatilhos em hml e prod | não existem (o módulo `cicd` só está ligado em dev) |

## Fatos que mudam a ADR 030 (medidos em 22/10/2026)

- O repositório é **privado** (`gh repo view`: `isPrivate: true`; o GitHub responde 401 sem login). A ADR diz "público". Por isso nenhuma etapa do build lê o repositório sem credencial: o Cloud Build usa o token do aplicativo do GitHub só para baixar o commit, e `git fetch` dentro do build pede usuário.
- O Painel publica num **projeto da ness. fora deste `infra/`**: `ness-painel-projetos`, bucket `ness-painel-projetos-alupdata`, conta `painel-publicador`, entrada por Workload Identity Federation do GitHub. A migração precisa de uma concessão nesse projeto.
- As variáveis hoje no GitHub (`TF_STATE_BUCKET`, `IMAGEM_INGESTAO`, `GCP_REGION`, `DATAFORM_GIT_TOKEN_VERSAO`, `GCP_DEPLOY_SA`) passam a ser **substituições do gatilho**, calculadas no Terraform.

## Restrições globais

- Regra 2: credencial só no Secret Manager. O build lê o segredo por `availableSecrets`, nunca por arquivo versionado.
- Regra 5: gatilho, conta, agendamento e papel só existem se estiverem em `infra/`.
- Regra 6: nada de atribuição a ferramenta de IA em commit, PR, issue, comentário ou documento.
- TDD: teste antes do código. Commits convencionais em português, PR para `main`, nome de branch pelo assunto.
- Cada fase termina com o caminho antigo ainda funcionando. Só a Tarefa 9 desliga o Actions.
- Decisão fora deste plano: tornar o repositório privado ou público não muda nada aqui, porque nada mais depende de ambientes do GitHub.

## Decisões e passos humanos

| # | O quê | Quem | Bloqueia |
|---|---|---|---|
| D1 | **Credencial de leitura do GitHub para o CI.** Recomendado: um GitHub App novo, `alupdata-ci`, só com leitura de conteúdo, issues e pull requests, instalado em `Alupdatalake`; a chave privada vai para o segredo `alupdata-github-ci-app-key`. A alternativa é reaproveitar o token do Dataform (`alupdata-dataform-git-token`), cujo escopo não foi verificado | Ricardo, com o dono da organização | Tarefas 1, 4 e 7 |
| D2 | Conceder `roles/storage.objectAdmin` no bucket `ness-painel-projetos-alupdata` à conta `alupdata-painel` do projeto dev (criada na Tarefa 7) | ness., no projeto `ness-painel-projetos` | Tarefa 7 |
| D3 | Aplicar o bootstrap em hml (e em prod, quando existir) com os papéis novos das tarefas 3 e 5 | pessoa com Owner | Tarefas 5 a 7 em hml |
| D4 | Desligar o CodeQL no repositório (configuração do GitHub, não é workflow versionado) | dono da organização | Tarefa 9 |

## Custo (da Alup, cláusula 5ª) — estimativa a conferir na primeira fatura

Franquia do Cloud Build: 2.500 minutos por mês (ADR 030, §4). Uso estimado: CI de PR e de push, cerca de 2,5 min cada x 80 = 200; deploy, 8 min x 20 = 160; operações sob demanda, 3 min x 60 = 180; Painel, 2,5 min x 8 por dia x 30 = 600; Quadro, Atribuição e SCA, cerca de 120. **Total estimado de 1.260 minutos**, abaixo da franquia. O Painel é o maior consumidor; se apertar, volta para de 6 em 6 horas.

## Mapa de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `scripts/github_app_token.py` (novo) | gera o token de instalação de um GitHub App a partir da chave no ambiente |
| `scripts/operacoes.py` (novo) | valida as entradas e monta os comandos das quatro operações sob demanda |
| `cloudbuild/ci.yaml` (alterar) | volta a rodar `ci-atribuicao`, com o token de leitura |
| `cloudbuild/deploy.yaml`, `cloudbuild/deploy.sh` (novos) | imagem, Terraform, Dataform e catálogo, por ambiente |
| `cloudbuild/operar.yaml` (novo) | as quatro operações sob demanda |
| `cloudbuild/agendado.yaml` (novo) | Painel, Quadro, Atribuição diária e SCA semanal |
| `infra/modules/cicd/` (estender) | gatilhos manuais e de deploy, Scheduler, contas e papéis |
| `infra/environments/{dev,hml}.tfvars` (alterar) | liga o módulo em hml e traz os valores que hoje estão no GitHub |
| `.github/workflows/*` (remover, Tarefa 9) | só depois de tudo estável |

---

### Task 0: corrigir a ADR 030 e registrar as decisões

**Arquivos:** alterar `docs/arquitetura/decisoes/030-cicd-fora-do-github-actions.md`.

- [ ] **Passo 1:** no §1, trocar a frase "O repositório é **público**..." por "O repositório é **privado** (verificado em 22/10/2026, `gh repo view`)". Remover o parágrafo "Repositório público expõe detalhes do cliente" ou reescrevê-lo como histórico.
- [ ] **Passo 2:** no §4, acrescentar um adendo datado com três itens: (a) o build do Cloud Build não tem credencial do GitHub nas etapas, então a `main` e as APIs do GitHub exigem um token de leitura vindo do Secret Manager (D1); (b) o CI deixa de ser "só escreve log" e passa a ler **um** segredo, o do App de leitura; (c) a estimativa de custo desta página.
- [ ] **Passo 3:** rodar `uv run pytest tests/unit/test_infra.py tests/unit/test_cicd.py -q`. Esperado: passa (nenhum teste lê a ADR).
- [ ] **Passo 4:** commit `docs: ADR 030 corrigida (repositório privado) e custo estimado do CI/CD completo`.

### Task 1: gerar o token do GitHub App (TDD)

**Arquivos:** criar `scripts/github_app_token.py` e `tests/unit/test_github_app_token.py`. Declarar `cryptography>=43` em `pyproject.toml` (já está no `uv.lock` como transitiva) e rodar `uv lock`.

**Interfaces:**
- Produz: `jwt_do_app(client_id: str, chave_pem: bytes, agora: int | None = None) -> str` e `token_de_instalacao(client_id: str, chave_pem: bytes, dono: str, permissoes: dict[str, str], sessao: requests.Session | None = None) -> str`, e a linha de comando `python -m scripts.github_app_token --dono nessenergy --permissao contents=read ...`, que imprime só o token em stdout.

- [ ] **Passo 1: teste que falha.** `tests/unit/test_github_app_token.py`:

```python
"""Token de instalação de GitHub App: JWT RS256 e troca por token de acesso. Sem rede."""

from __future__ import annotations

import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from scripts.github_app_token import jwt_do_app, token_de_instalacao


@pytest.fixture(scope="module")
def chave() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _pem(chave: rsa.RSAPrivateKey) -> bytes:
    return chave.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()
    )


def _decodificar(parte: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(parte + "=" * (-len(parte) % 4)))


def test_jwt_tem_a_forma_e_a_assinatura_que_o_github_exige(chave) -> None:
    jwt = jwt_do_app("Iv-teste", _pem(chave), agora=1_000_000)

    cabecalho, corpo, assinatura = jwt.split(".")
    assert _decodificar(cabecalho) == {"alg": "RS256", "typ": "JWT"}
    assert _decodificar(corpo) == {"iat": 999_940, "exp": 1_000_540, "iss": "Iv-teste"}
    bruta = base64.urlsafe_b64decode(assinatura + "=" * (-len(assinatura) % 4))
    chave.public_key().verify(bruta, f"{cabecalho}.{corpo}".encode(), padding.PKCS1v15(), hashes.SHA256())


class _Resposta:
    def __init__(self, corpo: dict) -> None:
        self._corpo = corpo

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._corpo


class _Sessao:
    def __init__(self) -> None:
        self.chamadas: list[tuple[str, str, dict]] = []

    def get(self, url: str, **kw) -> _Resposta:
        self.chamadas.append(("GET", url, kw))
        return _Resposta({"id": 42})

    def post(self, url: str, **kw) -> _Resposta:
        self.chamadas.append(("POST", url, kw))
        return _Resposta({"token": "ghs_abc"})


def test_troca_o_jwt_por_token_com_so_as_permissoes_pedidas(chave) -> None:
    sessao = _Sessao()

    token = token_de_instalacao("Iv-teste", _pem(chave), "nessenergy", {"contents": "read"}, sessao=sessao)

    assert token == "ghs_abc"
    (_, url_get, _), (_, url_post, kw_post) = sessao.chamadas
    assert url_get == "https://api.github.com/orgs/nessenergy/installation"
    assert url_post == "https://api.github.com/app/installations/42/access_tokens"
    assert kw_post["json"] == {"permissions": {"contents": "read"}}
    assert kw_post["headers"]["Authorization"].startswith("Bearer ")
```

- [ ] **Passo 2:** `uv run pytest tests/unit/test_github_app_token.py -q`. Esperado: FALHA com `ModuleNotFoundError: scripts.github_app_token`.
- [ ] **Passo 3: implementação mínima.** `scripts/github_app_token.py`:

```python
"""Token de instalação de um GitHub App, para o CI ler o repositório privado, as issues e os PRs.

A chave privada vem do Secret Manager pelo Cloud Build (`availableSecrets`), na variável de ambiente `CHAVE_APP`; o
`client_id` vem de `CLIENT_ID_APP`. O token vale uma hora e sai só em stdout, nunca em log nem em arquivo.

    python -m scripts.github_app_token --dono nessenergy --permissao contents=read --permissao issues=read
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import time

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

API = "https://api.github.com"
TIMEOUT = 30


def _b64(dados: bytes) -> bytes:
    return base64.urlsafe_b64encode(dados).rstrip(b"=")


def jwt_do_app(client_id: str, chave_pem: bytes, agora: int | None = None) -> str:
    agora = int(time.time()) if agora is None else agora
    cabecalho = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    corpo = _b64(json.dumps({"iat": agora - 60, "exp": agora + 540, "iss": client_id}).encode())
    chave = serialization.load_pem_private_key(chave_pem, password=None)
    assinatura = chave.sign(cabecalho + b"." + corpo, padding.PKCS1v15(), hashes.SHA256())  # type: ignore[union-attr]
    return (cabecalho + b"." + corpo + b"." + _b64(assinatura)).decode()


def token_de_instalacao(
    client_id: str,
    chave_pem: bytes,
    dono: str,
    permissoes: dict[str, str],
    sessao: requests.Session | None = None,
) -> str:
    sessao = sessao or requests.Session()
    cabecalhos = {
        "Authorization": f"Bearer {jwt_do_app(client_id, chave_pem)}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    instalacao = sessao.get(f"{API}/orgs/{dono}/installation", headers=cabecalhos, timeout=TIMEOUT)
    instalacao.raise_for_status()
    resposta = sessao.post(
        f"{API}/app/installations/{instalacao.json()['id']}/access_tokens",
        headers=cabecalhos,
        json={"permissions": permissoes},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()["token"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dono", required=True)
    parser.add_argument("--permissao", action="append", required=True, help="nome=nivel, ex.: contents=read")
    args = parser.parse_args(argv)
    permissoes = dict(item.split("=", 1) for item in args.permissao)
    print(token_de_instalacao(os.environ["CLIENT_ID_APP"], os.environ["CHAVE_APP"].encode(), args.dono, permissoes))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Passo 4:** `uv run pytest tests/unit/test_github_app_token.py -q`. Esperado: 2 passam. Rodar `uv run ruff check scripts tests && uv run ruff format --check scripts tests && uv run bandit -q -r scripts/github_app_token.py`.
- [ ] **Passo 5:** commit `feat(ci): script que gera o token de instalação de um GitHub App`.

### Task 2: as operações sob demanda como código testado (TDD)

Hoje a validação e a montagem dos comandos estão dentro de YAML do Actions, sem teste. Aqui elas viram Python.

**Arquivos:** criar `scripts/operacoes.py` e `tests/unit/test_operacoes.py`.

**Interfaces:**
- Produz: `EntradaInvalida(ValueError)`; `ingestao(conector: str, de: str = "", ate: str = "", uri: str = "") -> tuple[str, list[str], str]`, que devolve `(job, args_do_gcloud, descricao_da_janela)`; `job_teste_conexao(fonte: str) -> str`; `args_sonda(sonda: str) -> list[str]`; e a linha de comando `python -m scripts.operacoes <operacao> --ambiente ... --projeto ... --regiao ...` que executa o `gcloud`.

- [ ] **Passo 1: teste que falha.** `tests/unit/test_operacoes.py`:

```python
"""Operações sob demanda: validação das entradas e comandos. As regras são as dos workflows de hoje."""

from __future__ import annotations

import pytest
from scripts.operacoes import EntradaInvalida, args_sonda, ingestao, job_teste_conexao


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
```

- [ ] **Passo 2:** `uv run pytest tests/unit/test_operacoes.py -q`. Esperado: FALHA (`ModuleNotFoundError`).
- [ ] **Passo 3: implementação das funções puras.** `scripts/operacoes.py` (a parte de execução vem no passo 5):

```python
"""Operações sob demanda no Cloud Build (ADR 030): executar ingestão, conferir cargas, sondar rede, testar conexão.

As entradas chegam por substituição do gatilho e são validadas aqui antes de chegar ao `gcloud`.
"""

from __future__ import annotations

import re

_CONECTOR = re.compile(r"^[a-z0-9_]+$")
_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_URI = re.compile(r"^gs://[a-z0-9._-]+/[a-z0-9_=./-]+$")
_FONTE = re.compile(r"^[a-z0-9-]+$")
_SONDA = re.compile(r"^[a-z_]+$")


class EntradaInvalida(ValueError):
    """Entrada fora do formato esperado; nada chega ao gcloud."""


def ingestao(conector: str, de: str = "", ate: str = "", uri: str = "") -> tuple[str, list[str], str]:
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
        return job, [f"--args=reprocessar-raw,{conector},--uri,{uri},--de,{de},--ate,{ate}"], f"replay de {uri} ({de} a {ate})"
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
```

- [ ] **Passo 4:** `uv run pytest tests/unit/test_operacoes.py -q`. Esperado: passa. Ruff e bandit limpos (a linha longa do `return` de replay: quebrar em duas se o ruff reclamar).
- [ ] **Passo 5: teste da execução, que falha.** Em `tests/unit/test_operacoes.py`, com um executor falso que grava os comandos e devolve o status programado:

```python
from scripts.operacoes import executar_job


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
```

- [ ] **Passo 6: implementação.** Acrescentar a `scripts/operacoes.py`:

```python
import re
import subprocess
import sys
from collections.abc import Callable

Executor = Callable[[list[str]], tuple[int, str]]


def _rodar(cmd: list[str]) -> tuple[int, str]:
    resultado = subprocess.run(cmd, capture_output=True, text=True, check=False)  # noqa: S603
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
            ["gcloud", "logging", "read", filtro, "--project", projeto, "--order=asc", "--limit=500",
             "--format=value(timestamp,severity,textPayload)"]
        )
    return status
```

  Em seguida, `main(argv)` com os quatro subcomandos: `executar-ingestao` (usa `ingestao()` e `executar_job`), `testar-conexao` (usa `job_teste_conexao()` e `executar_job`), `sondar-rede` (usa `executar_job("ingestao-bcb-cambio-ptax", args_sonda(sonda), ...)` e depois `gcloud storage ls gs://<projeto>-raw/sondas/<sonda>/` e `gcloud storage cat` do último objeto) e `conferir-cargas` (`subprocess.run([sys.executable, "-m", "scripts.conferir_cargas"], env={**os.environ, "GCP_PROJECT_ID": projeto})`). Cada subcomando devolve `1` com a mensagem de `EntradaInvalida` se a validação reprovar.
- [ ] **Passo 7:** `uv run pytest tests/unit/test_operacoes.py -q` (todos passam), ruff e bandit limpos, e commit `feat(ci): operações sob demanda como código testado, fora do YAML`.

### Task 3: gatilhos manuais, contas e papéis em `infra/` (Terraform)

**Arquivos:** estender `infra/modules/cicd/main.tf`; alterar `infra/main.tf` (chamada do módulo), `infra/variables.tf`, `infra/environments/dev.tfvars` e `hml.tfvars`; testes em `tests/unit/test_cicd.py`.

- [ ] **Passo 1: testes que falham** em `tests/unit/test_cicd.py`, no estilo dos existentes (regex sobre o arquivo): o módulo declara os quatro gatilhos `alupdata-op-executar-ingestao`, `-conferir-cargas`, `-sondar-rede` e `-testar-conexao`; todos com `filename = "cloudbuild/operar.yaml"` e `service_account` igual à conta de deploy do ambiente; nenhum deles usa o bloco `github {` (é manual, não pode disparar no push); e o papel `roles/logging.logWriter` aparece para a conta de deploy.
- [ ] **Passo 2:** novas variáveis do módulo: `deploy_service_account_id` (o `id` completo da conta de deploy, vindo de `var.deploy_service_account`), `regiao` e `imagem_ingestao_base`. O módulo passa a ser ligado em **dev e hml** (`cicd = { ... }` em `hml.tfvars`).
- [ ] **Passo 3:** o recurso dos gatilhos manuais, com este formato (gatilho manual de repositório do GitHub conectado: `source_to_build` e `git_file_source`, sem `github {}`):

```hcl
locals {
  operacoes = {
    "alupdata-op-executar-ingestao" = { _OPERACAO = "executar-ingestao", _CONECTOR = "", _DE = "", _ATE = "", _URI = "" }
    "alupdata-op-conferir-cargas"   = { _OPERACAO = "conferir-cargas" }
    "alupdata-op-sondar-rede"       = { _OPERACAO = "sondar-rede", _SONDA = "cptec" }
    "alupdata-op-testar-conexao"    = { _OPERACAO = "testar-conexao", _FONTE = "" }
  }
}

resource "google_cloudbuild_trigger" "operacao" {
  for_each        = local.operacoes
  project         = var.project_id
  name            = each.key
  description     = "Operação sob demanda (ADR 030): gcloud builds triggers run ${each.key} --branch=main --substitutions=..."
  service_account = var.deploy_service_account_id
  filename        = "cloudbuild/operar.yaml"
  substitutions   = merge(each.value, { _REGIAO = var.regiao })

  source_to_build {
    uri       = "https://github.com/${var.repositorio_dono}/${var.repositorio_nome}"
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = "cloudbuild/operar.yaml"
    uri       = "https://github.com/${var.repositorio_dono}/${var.repositorio_nome}"
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }
}
```

- [ ] **Passo 4:** papéis para a conta de deploy rodar build com log próprio: `roles/logging.logWriter` no projeto, em `infra/bootstrap/main.tf` (`papeis_deploy`) **e** o teste `tests/unit/test_bootstrap.py` que compara a lista com o que `infra/` declara. Quem dispara (grupo `operacao-datalake`) já tem `cloudbuild.builds.editor` por `gestao_cicd`; acrescentar `roles/iam.serviceAccountUser` sobre a conta de deploy para esse grupo, porque disparar gatilho com conta própria exige agir como ela.
- [ ] **Passo 5:** `terraform fmt -check -recursive infra`, `uv run pytest tests/unit/test_cicd.py tests/unit/test_bootstrap.py tests/unit/test_infra.py -q`, `terraform -chdir=infra validate`. Esperado: tudo verde.
- [ ] **Passo 6:** commit `feat(infra): gatilhos manuais das operações e papéis de log da conta de deploy`. **Aplicar em dev** (Tarefa 6 faz isso por deploy). Em hml depende de D3.

### Task 4: a checagem de atribuição volta ao Cloud Build

Depende de D1.

**Arquivos:** alterar `cloudbuild/ci.yaml`, `infra/modules/cicd/main.tf` (segredo e acesso), `tests/unit/test_cicd.py`.

- [ ] **Passo 1: testes que falham.** O módulo declara o segredo `alupdata-github-ci-app-key` (contêiner vazio, valor gravado por pessoa, regra 2) e dá `roles/secretmanager.secretAccessor` **só nesse segredo** à conta `alupdata-ci`; `ci.yaml` tem `availableSecrets` e um passo `busca-main` antes do `ci`; `_ALVOS` volta a incluir `ci-atribuicao` no gatilho de PR (o de push continua sem ele).
- [ ] **Passo 2:** `cloudbuild/ci.yaml`:

```yaml
steps:
  - id: busca-main
    name: node:22-bookworm
    entrypoint: bash
    secretEnv: [CHAVE_APP]
    env: ["CLIENT_ID_APP=${_CLIENT_ID_APP}"]
    args:
      - -c
      - |
        set -euo pipefail
        curl -LsSf "https://astral.sh/uv/0.5.11/install.sh" | sh
        export PATH="$$HOME/.local/bin:$$PATH"
        TOKEN="$(uv run --no-project --with cryptography --with requests python -m scripts.github_app_token --dono nessenergy --permissao contents=read)"
        git fetch --unshallow --quiet "https://x-access-token:$${TOKEN}@github.com/nessenergy/Alupdatalake.git" || true
        git fetch --quiet "https://x-access-token:$${TOKEN}@github.com/nessenergy/Alupdatalake.git" main:refs/remotes/origin/main
  - id: ci
    name: node:22-bookworm
    entrypoint: bash
    args: ["cloudbuild/ci.sh", "${_ALVOS}"]

availableSecrets:
  secretManager:
    - versionName: projects/$PROJECT_ID/secrets/alupdata-github-ci-app-key/versions/latest
      env: CHAVE_APP
```

  O `_CLIENT_ID_APP` é substituição do gatilho (não é segredo). `ci.sh` volta a conferir `git rev-parse --verify origin/main` e falhar alto se não existir.
- [ ] **Passo 3:** `uv run pytest tests/unit/test_cicd.py -q`, depois PR de teste (qualquer mudança de documentação) e conferir o `alupdata-ci-pr` verde **com** `ci-atribuicao`.
- [ ] **Passo 4:** commit `feat(ci): a checagem de atribuição volta ao Cloud Build, com token de leitura do GitHub`.

### Task 5: deploy no Cloud Build

**Arquivos:** criar `cloudbuild/deploy.yaml`, `cloudbuild/deploy.sh`; estender o módulo `cicd` com os gatilhos de deploy; teste em `tests/unit/test_cicd.py`.

- [ ] **Passo 1: testes que falham:** o gatilho `alupdata-deploy` existe, é manual, roda como a conta de deploy, e tem as substituições `_AMBIENTE`, `_MODULO` (`all|infra|connectors`), `_IMAGEM_SHA`, `_IMAGEM_BASE`, `_TF_ESTADO`, `_REGIAO` e `_DATAFORM_TOKEN_VERSAO`. `deploy.yaml` chama só `cloudbuild/deploy.sh`.
- [ ] **Passo 2:** `cloudbuild/deploy.yaml`:

```yaml
steps:
  - id: imagem
    name: gcr.io/cloud-builders/docker
    entrypoint: bash
    args:
      - -c
      - |
        set -euo pipefail
        [[ "${_MODULO}" == "all" || "${_MODULO}" == "connectors" ]] || { echo "módulo ${_MODULO}: imagem não é construída"; exit 0; }
        docker build -t "${_IMAGEM_BASE}:${COMMIT_SHA}" -t "${_IMAGEM_BASE}:latest" .
        docker push "${_IMAGEM_BASE}:${COMMIT_SHA}"
        docker push "${_IMAGEM_BASE}:latest"
  - id: infra
    name: node:22-bookworm
    entrypoint: bash
    args: ["cloudbuild/deploy.sh"]
    env:
      - "AMBIENTE=${_AMBIENTE}"
      - "MODULO=${_MODULO}"
      - "IMAGEM_SHA=${_IMAGEM_SHA}"
      - "IMAGEM_BASE=${_IMAGEM_BASE}"
      - "TF_ESTADO=${_TF_ESTADO}"
      - "REGIAO=${_REGIAO}"
      - "DATAFORM_TOKEN_VERSAO=${_DATAFORM_TOKEN_VERSAO}"
      - "COMMIT_SHA=${COMMIT_SHA}"
      - "PROJETO=$PROJECT_ID"
options:
  logging: CLOUD_LOGGING_ONLY
timeout: 3000s
```

- [ ] **Passo 3:** `cloudbuild/deploy.sh` é a tradução, sem mudança de comportamento, do que está em `.github/workflows/deploy.yml` (linhas 60 a 155): validar `TAG` (`COMMIT_SHA` quando o módulo é `all`, `IMAGEM_SHA` quando é `infra`, 40 hexadecimais); `gcloud artifacts docker images list ... --filter="tags:$TAG"` e falhar se a imagem não existir; instalar `terraform` e `uv` como `cloudbuild/ci.sh` faz; `terraform init -backend-config="bucket=$TF_ESTADO"`; `terraform plan` e `apply` com `-var-file=environments/$AMBIENTE.tfvars`, `-var=imagem_ingestao=$IMAGEM_BASE:$TAG`, `-var=deploy_service_account=...` e `-var=dataform_git_token_versao=$DATAFORM_TOKEN_VERSAO`; o `bq query` do `TABLE_STORAGE`; `uv run python -m scripts.executar_dataform ...`; `uv run python -m scripts.anotar_catalogo ...`. Um erro do Dataform ou do Terraform derruba o build.
- [ ] **Passo 4:** os gatilhos de deploy no módulo, um por ambiente (a chamada do módulo em cada projeto cria o seu, com os valores da tabela de variáveis levantada em 22/10: `_TF_ESTADO = "<projeto>-tfstate"`, `_IMAGEM_BASE = "us-central1-docker.pkg.dev/<projeto>/alupdata/cli"`, `_DATAFORM_TOKEN_VERSAO = "1"`).
- [ ] **Passo 5:** `bash -n cloudbuild/deploy.sh`, `uv run pytest tests -q`, `terraform validate`. Depois do PR mesclado, **provar em dev**: `gcloud builds triggers run alupdata-deploy --project=alupar-dev-alupdata --branch=main --substitutions=_AMBIENTE=dev,_MODULO=all`. Esperado: build verde, Dataform concluído, mesma infraestrutura do deploy do Actions (o `terraform plan` seguinte não mostra mudança).
- [ ] **Passo 6:** commit `feat(ci): deploy no Cloud Build, por ambiente`.

### Task 6: operações sob demanda no Cloud Build

**Arquivos:** criar `cloudbuild/operar.yaml`; documentação em `docs/runbook/`.

- [ ] **Passo 1:** `cloudbuild/operar.yaml` (os gatilhos da Tarefa 3 apontam para ele):

```yaml
steps:
  - id: operar
    name: gcr.io/google.com/cloudsdktool/cloud-sdk:stable
    entrypoint: bash
    args:
      - -c
      - |
        set -euo pipefail
        curl -LsSf "https://astral.sh/uv/0.5.11/install.sh" | sh
        export PATH="$$HOME/.local/bin:$$PATH"
        uv sync --frozen --no-dev
        uv run python -m scripts.operacoes "${_OPERACAO}" --projeto "$PROJECT_ID" --regiao "${_REGIAO}" \
          --conector "${_CONECTOR}" --de "${_DE}" --ate "${_ATE}" --uri "${_URI}" --fonte "${_FONTE}" --sonda "${_SONDA}"
options:
  logging: CLOUD_LOGGING_ONLY
timeout: 3300s
substitutions:
  _OPERACAO: ""
  _REGIAO: us-central1
  _CONECTOR: ""
  _DE: ""
  _ATE: ""
  _URI: ""
  _FONTE: ""
  _SONDA: ""
```

  A imagem `cloud-sdk:stable` traz `gcloud`, `curl` e Python, e o `uv` entra pelo instalador, como em `ci.sh`. O passo falha com o status do job, e o log do contêiner aparece no log do build.
- [ ] **Passo 2:** provar cada operação em dev: `gcloud builds triggers run alupdata-op-executar-ingestao --project=alupar-dev-alupdata --branch=main --substitutions=_CONECTOR=cptec_previsao`; `alupdata-op-conferir-cargas`; `alupdata-op-sondar-rede` com `_SONDA=cptec`; `alupdata-op-testar-conexao` com `_FONTE=comercializacao`. Esperado: o mesmo resultado dos workflows (162 linhas do CPTEC na conferência).
- [ ] **Passo 3:** reescrever em `docs/runbook/deploy.md`, `docs/runbook/incidentes.md` e `docs/runbook/conferencia-e-sondas.md` os comandos de `gh workflow run` para `gcloud builds triggers run ...`, com a tabela de substituições de cada operação.
- [ ] **Passo 4:** commit `feat(ci): operações sob demanda no Cloud Build e runbooks`.

### Task 7: agendados (Painel, Quadro, Atribuição, SCA)

Depende de D1 (Atribuição, Painel) e D2 (Painel).

**Arquivos:** criar `cloudbuild/agendado.yaml`; estender o módulo `cicd` com os gatilhos agendados e o Cloud Scheduler.

- [ ] **Passo 1: testes que falham** em `tests/unit/test_cicd.py`: existe um `google_cloud_scheduler_job` por agendado, com `http_target` para `cloudbuild.googleapis.com/v1/projects/.../triggers/<nome>:run`, `oauth_token` da conta `alupdata-agendador`, e a tabela de crons abaixo.

| Agendado | Gatilho | Cron (UTC) | Equivale a |
|---|---|---|---|
| SCA semanal | `alupdata-ag-sca` | `0 11 * * 1` | `sca.yml` |
| Atribuição diária | `alupdata-ag-atribuicao` | `0 11 * * *` | `atribuicao.yml` |
| Quadro | `alupdata-ag-quadro` | `0 11 * * 1-5` | `quadro.yml` |
| Painel | `alupdata-ag-painel` | `7 */3 * * *` | `painel.yml` |

- [ ] **Passo 2:** `cloudbuild/agendado.yaml` com `_TAREFA` (`sca|atribuicao|quadro|painel`) chamando `make ci-sca`, `scripts/verifica_atribuicao.py --github nessenergy/Alupdatalake` (com o token de leitura, `GH_TOKEN`), `scripts.quadro --aplicar` (com o App do quadro, `alupdata-github-quadro-app-key`, permissões `organization_projects=write`, `issues=write`, `pull_requests=read`) e `scripts.painel` (token de leitura de issues). O Quadro mantém a guarda de hoje: sem chave gravada, avisa e sai com sucesso.
- [ ] **Passo 3: Painel, o mais delicado.** O Painel lê dev e hml e grava no bucket do projeto da ness. Criar em `infra/` a conta `alupdata-painel` (dev). Em hml, uma variável `leitores_execucoes` concede a ela `roles/bigquery.dataViewer` no dataset `bronze` e `roles/bigquery.jobUser` no projeto. A publicação usa `gcloud storage cp dados.json dados-aditivo.json painel/index.html painel/aditivo.html gs://ness-painel-projetos-alupdata/ --cache-control=no-store`, e exige D2. O encadeamento "depois do deploy e da ingestão" (hoje `workflow_run`) vira um último passo dos builds de deploy e de `executar-ingestao` que roda `gcloud builds triggers run alupdata-ag-painel --branch=main`.
- [ ] **Passo 4:** `terraform validate`, testes verdes; aplicar em dev (pelo deploy da Tarefa 5) e disparar cada agendado uma vez à mão: `gcloud builds triggers run alupdata-ag-painel ...`. Conferir `dados.json` novo no bucket e a página do painel atualizada.
- [ ] **Passo 5:** commit `feat(ci): agendados no Cloud Scheduler e no Cloud Build`.

### Task 8: operar em paralelo por uma semana

- [ ] **Passo 1:** com tudo no ar, manter o Actions ligado e **não** disparar nada novo por ele. Registrar a cada dia útil, em `docs/status.md`, se os agendados do Cloud Scheduler rodaram e comparar com o Painel.
- [ ] **Passo 2:** critérios de saída: (a) ao menos 5 PRs com os checks do Cloud Build iguais aos do Actions; (b) um deploy completo de dev e um de hml pelo Cloud Build; (c) cada agendado rodou 3 vezes; (d) o custo de build do mês dentro da franquia (conferir no Billing); (e) as quatro operações sob demanda provadas em dev e hml.
- [ ] **Passo 3:** só com (a) a (e) cumpridos, seguir para a Tarefa 9.

### Task 9: desligar o Actions

Depende de D3 (hml), D4 e da Tarefa 8.

**Arquivos:** remover `.github/workflows/*.yml`; alterar `infra/bootstrap/main.tf` e `tests/unit/test_bootstrap.py`; atualizar `AGENTS.md`, `CLAUDE.md`, `docs/runbook/deploy.md`, `docs/arquitetura/decisoes/015-fundacao-do-ambiente.md` (adendo), `docs/auditoria.md` e `README.md`.

- [ ] **Passo 1:** `git rm .github/workflows/*.yml`. Manter `.github/dependabot.yml`, `PULL_REQUEST_TEMPLATE.md` e `ISSUE_TEMPLATE/`.
- [ ] **Passo 2:** em `infra/bootstrap/main.tf`, remover o provedor de Workload Identity Federation do GitHub, o pool e a condição por `environment`, e ajustar `tests/unit/test_bootstrap.py` (que hoje exige a condição). Aplicar o bootstrap em dev e hml (D3).
- [ ] **Passo 3:** apagar os ambientes `dev`, `hml` e `prod` do GitHub e as variáveis do repositório (`GCP_*`, `PAINEL_*`, `QUADRO_APP_CLIENT_ID` passa a ser substituição do gatilho). Remover o provedor WIF do projeto `ness-painel-projetos` (pedido à ness.).
- [ ] **Passo 4:** atualizar a documentação: o CI e a operação passam a ser descritos como Cloud Build; o `docs/auditoria.md` troca os comandos `gh workflow run ...` por `gcloud builds triggers run ...`; o `README.md` e o `AGENTS.md` deixam de citar workflows. Escrever o adendo da ADR 015 ("WIF e ambientes do GitHub desativados em <data>").
- [ ] **Passo 5:** `uv run pytest tests -q`, `terraform validate`, e um PR de teste que mostre só os checks do Cloud Build. O painel segue atualizando 3 vezes depois do desligamento.
- [ ] **Passo 6:** commit `chore(ci): desliga o GitHub Actions; CI, deploy e operação ficam no Cloud Build`.

---

## Riscos

- **Credencial de leitura do GitHub (D1).** É a única credencial nova do CI. Mitigação: App só de leitura, token de uma hora, segredo com acesso restrito à conta do CI, nunca em log (o Cloud Build mascara o valor de `availableSecrets`).
- **Painel no projeto da ness. (D2).** Sem a concessão no bucket, o painel para de atualizar. Mitigação: manter o workflow `painel.yml` até a Tarefa 9 e só removê-lo depois de três publicações pelo Cloud Build.
- **Gatilho manual com repositório de 1ª geração.** O formato `source_to_build` e `git_file_source` com `repo_type = "GITHUB"` precisa ser provado em dev no primeiro `terraform apply`; se o provedor recusar, o recurso muda para um gatilho de 2ª geração (exige criar a conexão) e o plano é ajustado.
- **Conta de deploy executando build.** Precisa de `logging.logWriter` e de permissão para quem dispara agir como ela. Está na Tarefa 3.
- **Perda do formulário do GitHub.** Quem opera usa `gcloud builds triggers run`. Mitigação: runbooks da Tarefa 6 e o papel por grupo.
- **Custo.** Estimado dentro da franquia, mas não medido. A Tarefa 8 confere.

## Pronto quando

Nenhum arquivo em `.github/workflows/`; todo PR mostra só checks do Cloud Build (com a atribuição incluída); deploy, as quatro operações e os quatro agendados rodam pelo Cloud Build em dev e hml; o painel atualiza sozinho; WIF e ambientes do GitHub removidos; documentação e auditoria apontam para os comandos novos.
