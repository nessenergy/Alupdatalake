"""CI no Cloud Build (ADR 030, fase 1): o arquivo do build só chama `make`, e os gatilhos são seguros."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parents[2]
_BASH = shutil.which("bash")


def _ler(caminho: str) -> str:
    return (RAIZ / caminho).read_text(encoding="utf-8")


def test_ci_yaml_so_chama_o_script_e_grava_log_no_cloud_logging() -> None:
    ci = yaml.safe_load(_ler("cloudbuild/ci.yaml"))
    assert ci["options"]["logging"] == "CLOUD_LOGGING_ONLY", "conta de serviço própria exige log no Cloud Logging"
    passos = ci["steps"]
    assert len(passos) == 1
    assert "cloudbuild/ci.sh" in " ".join(passos[0]["args"])
    alvos = ci["substitutions"]["_ALVOS"].split()
    assert "ci-atribuicao" not in alvos, "sem credencial para buscar a main no repositório privado"
    assert "ci-testes" in alvos


def test_ci_yaml_sem_atribuicao_nao_declara_segredo() -> None:
    ci = yaml.safe_load(_ler("cloudbuild/ci.yaml"))
    assert "availableSecrets" not in ci, "segredo sem versão derruba o build na largada"


def test_ci_com_atribuicao_busca_a_main_com_o_token_antes_do_ci() -> None:
    ci = yaml.safe_load(_ler("cloudbuild/ci-com-atribuicao.yaml"))
    assert ci["options"]["logging"] == "CLOUD_LOGGING_ONLY"
    assert [p["id"] for p in ci["steps"]] == ["busca-main", "ci"]
    busca = ci["steps"][0]
    assert busca["secretEnv"] == ["CHAVE_APP"]
    assert busca["args"] == ["cloudbuild/busca-main.sh"]
    assert "CLIENT_ID_APP=${_CLIENT_ID_APP}" in busca["env"]
    assert "${_" not in " ".join(busca["args"])
    (segredo,) = ci["availableSecrets"]["secretManager"]
    assert segredo["versionName"] == "projects/$PROJECT_ID/secrets/alupdata-github-ci-app-key/versions/latest"
    assert segredo["env"] == "CHAVE_APP"
    assert "_CLIENT_ID_APP" in ci["substitutions"]
    assert ci["substitutions"]["_ALVOS"] == "ci", "o ci completo inclui ci-atribuicao"
    assert ci["timeout"] == yaml.safe_load(_ler("cloudbuild/ci.yaml"))["timeout"]


def test_busca_main_nunca_expoe_o_token() -> None:
    script = _ler("cloudbuild/busca-main.sh")
    assert "\r" not in script
    assert "set -euo pipefail" in script
    assert not re.search(r"set\s+-\w*x", script), "xtrace imprimiria o token"
    assert not re.search(r"(echo|printf)[^\n]*\$\{?(TOKEN|CHAVE_APP)", script)
    assert "scripts.github_app_token" in script and "contents=read" in script
    assert script.count("git fetch") == 2
    assert "${_" not in script


def test_ci_sh_exige_a_main_so_quando_ha_ci_atribuicao() -> None:
    script = _ler("cloudbuild/ci.sh")
    assert re.search(r"ci-atribuicao[^\n]*\n[^\n]*git rev-parse --verify --quiet origin/main", script)
    assert "git fetch" not in script


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
def test_ci_sh_falha_sem_origin_main_quando_ha_ci_atribuicao(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)  # noqa: S607
    r = subprocess.run(  # noqa: S603
        [_BASH, str(RAIZ / "cloudbuild/ci.sh"), "ci-lint ci-atribuicao"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1 and "origin/main" in r.stdout + r.stderr


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
@pytest.mark.parametrize("faltando", ["CLIENT_ID_APP", "CHAVE_APP"])
def test_busca_main_recusa_entrada_vazia(faltando: str, tmp_path: Path) -> None:
    env = {"CLIENT_ID_APP": "Iv1.x", "CHAVE_APP": "k", "PATH": str(tmp_path)}
    env[faltando] = ""
    r = subprocess.run(  # noqa: S603
        [_BASH, str(RAIZ / "cloudbuild/busca-main.sh")], env=env, capture_output=True, text=True, check=False
    )
    assert r.returncode == 1 and faltando in r.stdout + r.stderr


def test_script_de_ci_roda_make_e_nao_tem_credencial() -> None:
    script = _ler("cloudbuild/ci.sh")
    assert "set -euo pipefail" in script
    assert re.search(r"make\s+.*\$ALVOS|make\s+\$\{?ALVOS", script)
    for proibido in ("gcloud auth", "GOOGLE_APPLICATION_CREDENTIALS", "secretmanager"):
        assert proibido not in script


def test_modulo_cicd_so_escreve_log_e_nao_roda_pr_de_fora_sem_aprovacao() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    papeis = re.findall(r'role\s*=\s*"(roles/[^"]+)"', modulo)
    assert papeis == ["roles/logging.logWriter", "roles/secretmanager.secretAccessor"], papeis
    assert "COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY" in modulo, (
        "PR de fora exige aprovação, mesmo com o repositório privado"
    )
    assert 'filename        = "cloudbuild/ci.yaml"' in modulo
    assert modulo.count("service_account") >= 2
    assert modulo.count('resource "google_cloudbuild_trigger"') == 4, "pr, main, as operações (for_each) e o deploy"


def test_segredo_do_app_de_ci_e_lido_so_pela_conta_do_ci_e_o_gatilho_pr_escolhe_pelo_client_id() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    assert re.search(
        r'resource "google_secret_manager_secret" "ci_app_key" \{[^}]*"alupdata-github-ci-app-key"', modulo
    )
    assert "google_secret_manager_secret_version" not in modulo, "valor gravado por pessoa (regra 2)"
    acesso = modulo[modulo.index('resource "google_secret_manager_secret_iam_member"') :]
    assert "google_secret_manager_secret.ci_app_key.secret_id" in acesso
    assert "google_service_account.ci.email" in acesso.split("}")[0]
    assert 'variable "github_app_ci_client_id"' in modulo
    pr = modulo[modulo.index('resource "google_cloudbuild_trigger" "pr"') : modulo.index('"main" {')]
    assert re.search(
        r'filename\s*=\s*var\.github_app_ci_client_id\s*==\s*""\s*\?\s*"cloudbuild/ci\.yaml"\s*:\s*"cloudbuild/ci-com-atribuicao\.yaml"',
        pr,
    )
    assert "_CLIENT_ID_APP" in pr and "ci-atribuicao" in pr
    principal = _ler("infra/main.tf")
    assert "github_app_ci_client_id" in principal
    assert "github_app_ci_client_id" not in _ler("infra/environments/dev.tfvars"), "vazio até a decisão D1"


def test_modulo_cicd_so_existe_quando_a_variavel_for_preenchida() -> None:
    principal = _ler("infra/main.tf")
    assert 'module "cicd"' in principal
    assert re.search(r"count\s*=\s*var\.cicd\s*==\s*null\s*\?\s*0\s*:\s*1", principal)
    variavel = _ler("infra/variables.tf")
    assert re.search(r'variable "cicd" \{.*?default\s*=\s*null', variavel, re.DOTALL)


def test_conta_de_deploy_pode_criar_gatilho() -> None:
    bootstrap = _ler("infra/bootstrap/main.tf")
    assert '"roles/cloudbuild.builds.editor"' in bootstrap


def test_operacoes_sob_demanda_sao_gatilhos_manuais_da_conta_de_deploy() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    for nome in ("executar-ingestao", "conferir-cargas", "sondar-rede", "testar-conexao"):
        assert f'"alupdata-op-{nome}"' in modulo, nome
    bloco = modulo[modulo.index('resource "google_cloudbuild_trigger" "operacao"') :]
    assert 'filename        = "cloudbuild/operar.yaml"' in bloco
    assert "service_account = var.deploy_service_account_id" in bloco
    assert "github {" not in bloco, "é manual: não pode disparar no push"
    assert "git_file_source" in bloco
    assert (RAIZ / "cloudbuild/operar.yaml").exists()


def test_modulo_cicd_declara_as_variaveis_das_operacoes_e_o_main_as_liga() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    for variavel in ("deploy_service_account_id", "regiao"):
        assert f'variable "{variavel}"' in modulo, variavel
    principal = _ler("infra/main.tf")
    assert "projects/${var.project_id}/serviceAccounts/${var.deploy_service_account}" in principal
    assert "imagem_ingestao_base" not in modulo + principal
    assert not re.search(r"^\s*cicd\s*=", _ler("infra/environments/hml.tfvars"), re.MULTILINE), (
        "hml só liga depois de D3"
    )


def test_modulo_cicd_recusa_conta_de_deploy_vazia() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    bloco = modulo[modulo.index('variable "deploy_service_account_id"') :]
    assert re.search(
        r"validation\s*\{\s*condition\s*=\s*can\(regex\(\"\^projects/\[\^/\]\+/serviceAccounts/\.\+\$\"", bloco
    )


def test_conta_de_deploy_escreve_log_proprio_e_operacao_age_como_ela() -> None:
    lista = re.search(r"papeis_deploy\s*=\s*\[(.*?)\]", _ler("infra/bootstrap/main.tf"), re.DOTALL)
    assert lista and "roles/logging.logWriter" in re.findall(r'"(roles/[^"]+)"', lista.group(1))
    principal = _ler("infra/main.tf")
    assert re.search(r'resource "google_service_account_iam_member" "operacao_age_como_deploy"', principal)
    assert "roles/iam.serviceAccountUser" in principal


def test_gatilho_de_deploy_e_manual_roda_como_a_conta_de_deploy_e_tem_as_substituicoes() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    bloco = modulo[modulo.index('resource "google_cloudbuild_trigger" "deploy"') :]
    assert 'name            = "alupdata-deploy"' in bloco
    assert 'filename        = "cloudbuild/deploy.yaml"' in bloco
    assert "service_account = var.deploy_service_account_id" in bloco
    assert "github {" not in bloco, "é manual: não pode disparar no push"
    assert "git_file_source" in bloco
    for sub in (
        "_AMBIENTE",
        "_MODULO",
        "_IMAGEM_SHA",
        "_IMAGEM_BASE",
        "_TF_ESTADO",
        "_REGIAO",
        "_DATAFORM_TOKEN_VERSAO",
        "_CONTA_DEPLOY",
    ):
        assert sub in bloco, sub
    assert '"${var.project_id}-tfstate"' in modulo
    assert "${var.regiao}-docker.pkg.dev/${var.project_id}/alupdata/cli" in modulo
    assert re.search(r'variable "dataform_token_versao" \{[^}]*default\s*=\s*"1"', modulo, re.DOTALL)
    assert re.search(r'variable "ambiente"', modulo) and '["dev", "hml", "prod"]' in modulo
    assert re.search(r"ambiente\s*=\s*var\.environment", _ler("infra/main.tf"))


def test_deploy_yaml_so_chama_o_script_e_grava_log_no_cloud_logging() -> None:
    deploy = yaml.safe_load(_ler("cloudbuild/deploy.yaml"))
    assert deploy["options"]["logging"] == "CLOUD_LOGGING_ONLY"
    passos = {p["id"]: p for p in deploy["steps"]}
    assert set(passos) == {"imagem", "infra"}
    assert passos["infra"]["args"] == ["cloudbuild/deploy.sh"]
    assert "cloud-sdk" in passos["infra"]["name"]
    assert passos["imagem"]["args"] == ["cloudbuild/imagem.sh"]
    assert "PROJECT_ID" not in " ".join(passos["infra"]["env"])
    assert passos["imagem"]["name"] == "gcr.io/cloud-builders/docker"
    env = " ".join(passos["infra"]["env"])
    for nome in (
        "AMBIENTE",
        "MODULO",
        "IMAGEM_SHA",
        "IMAGEM_BASE",
        "TF_ESTADO",
        "REGIAO",
        "DATAFORM_TOKEN_VERSAO",
        "CONTA_DEPLOY",
    ):
        assert f"{nome}=${{_" in env, nome


def test_deploy_sh_valida_antes_de_agir_e_nao_usa_sintaxe_do_actions() -> None:
    script = _ler("cloudbuild/deploy.sh")
    assert "set -euo pipefail" in script
    assert "::error::" not in script and "GITHUB_" not in script
    assert "[0-9a-f]{40}" in script
    assert script.index("[0-9a-f]{40}") < script.index("terraform init")
    assert script.index("images list") < script.index("terraform init")
    for trecho in (
        "terraform init",
        "terraform plan",
        "terraform apply",
        "-var-file=",
        "deploy_service_account=",
        "dataform_git_token_versao=",
        "enable_info_schema_storage",
        "scripts.executar_dataform",
        "scripts.anotar_catalogo",
    ):
        assert trecho in script, trecho
    assert "gcloud config" not in script


_SHA = "a" * 40
_BASE = "us-central1-docker.pkg.dev/proj/alupdata/cli"
_OK = {
    "AMBIENTE": "dev",
    "MODULO": "all",
    "COMMIT_SHA": _SHA,
    "IMAGEM_BASE": _BASE,
    "REGIAO": "us-central1",
    "CONTA_DEPLOY": "deploy@proj.iam.gserviceaccount.com",
}


def _rodar(script: str, tmp_path: Path, **env: str) -> subprocess.CompletedProcess[str]:
    # PATH vazio: se o script chamasse gcloud, terraform ou docker antes de validar, o comando falharia
    # com 127 e o teste não veria o código esperado.
    vazio = tmp_path / "vazio"
    vazio.mkdir(exist_ok=True)
    ambiente = {**_OK, **env, "PATH": str(vazio)}
    return subprocess.run(  # noqa: S603
        [_BASH, str(RAIZ / script)], env=ambiente, capture_output=True, text=True, cwd=tmp_path, check=False
    )


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
@pytest.mark.parametrize("script", ["cloudbuild/deploy.sh", "cloudbuild/imagem.sh"])
@pytest.mark.parametrize(
    "env",
    [{"MODULO": "foo"}, {"AMBIENTE": "x"}, {"MODULO": "all", "COMMIT_SHA": "xyz"}, {"MODULO": "all", "COMMIT_SHA": ""}],
)
def test_scripts_recusam_entrada_invalida_antes_de_qualquer_efeito(
    script: str, env: dict[str, str], tmp_path: Path
) -> None:
    r = _rodar(script, tmp_path, **env)
    assert r.returncode == 1, r.stderr + r.stdout


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
def test_modulo_connectors_nao_toca_no_terraform_e_infra_nao_constroi_imagem(tmp_path: Path) -> None:
    assert _rodar("cloudbuild/deploy.sh", tmp_path, MODULO="connectors").returncode == 0
    assert _rodar("cloudbuild/imagem.sh", tmp_path, MODULO="infra").returncode == 0
    assert _rodar("cloudbuild/deploy.sh", tmp_path, MODULO="infra", IMAGEM_SHA="curto").returncode == 1


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
def test_deploy_exige_conta_de_deploy(tmp_path: Path) -> None:
    r = _rodar("cloudbuild/deploy.sh", tmp_path, CONTA_DEPLOY="")
    assert r.returncode == 1 and "CONTA_DEPLOY" in r.stdout


def test_operar_yaml_so_chama_o_script_e_passa_tudo_por_env() -> None:
    operar = yaml.safe_load(_ler("cloudbuild/operar.yaml"))
    assert operar["options"]["logging"] == "CLOUD_LOGGING_ONLY"
    (passo,) = operar["steps"]
    assert passo["args"] == ["cloudbuild/operar.sh"]
    assert "cloud-sdk" in passo["name"]
    assert "${_" not in " ".join(passo["args"]), "substituição é textual: dentro do shell seria injeção"
    env = " ".join(passo["env"])
    for nome in ("OPERACAO", "REGIAO", "CONECTOR", "DE", "ATE", "URI", "FONTE", "SONDA"):
        assert f"{nome}=${{_" in env, nome
    assert "PROJETO=${PROJECT_ID}" in env
    for sub in ("_OPERACAO", "_REGIAO", "_CONECTOR", "_DE", "_ATE", "_URI", "_FONTE", "_SONDA"):
        assert sub in operar["substitutions"], sub


def test_operar_sh_valida_a_operacao_antes_de_instalar_qualquer_coisa() -> None:
    script = _ler("cloudbuild/operar.sh")
    assert "set -euo pipefail" in script
    assert "${_" not in script and "GITHUB_" not in script
    assert script.index("executar-ingestao|conferir-cargas|sondar-rede|testar-conexao") < script.index("astral.sh")
    assert "scripts.operacoes" in script


@pytest.mark.skipif(_BASH is None, reason="precisa de bash")
@pytest.mark.parametrize("operacao", ["", "deploy", "executar-ingestao; id", "sondar-rede "])
def test_operar_sh_recusa_operacao_fora_da_lista(tmp_path: Path, operacao: str) -> None:
    resultado = _rodar("cloudbuild/operar.sh", tmp_path, OPERACAO=operacao, PROJETO="proj")
    assert resultado.returncode == 1, resultado.stderr
    assert "OPERACAO inv" in resultado.stdout
