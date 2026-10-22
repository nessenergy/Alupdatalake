"""CI no Cloud Build (ADR 030, fase 1): o arquivo do build só chama `make`, e os gatilhos são seguros."""

import re
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parents[2]


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


def test_script_de_ci_roda_make_e_nao_tem_credencial() -> None:
    script = _ler("cloudbuild/ci.sh")
    assert "set -euo pipefail" in script
    assert re.search(r"make\s+.*\$ALVOS|make\s+\$\{?ALVOS", script)
    for proibido in ("gcloud auth", "GOOGLE_APPLICATION_CREDENTIALS", "secretmanager"):
        assert proibido not in script


def test_modulo_cicd_so_escreve_log_e_nao_roda_pr_de_fora_sem_aprovacao() -> None:
    modulo = _ler("infra/modules/cicd/main.tf")
    papeis = re.findall(r'role\s*=\s*"(roles/[^"]+)"', modulo)
    assert papeis == ["roles/logging.logWriter"], papeis
    assert "COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY" in modulo, (
        "PR de fora exige aprovação, mesmo com o repositório privado"
    )
    assert 'filename        = "cloudbuild/ci.yaml"' in modulo
    assert modulo.count("service_account") >= 2
    assert modulo.count('resource "google_cloudbuild_trigger"') == 4, "pr, main, as operações (for_each) e o deploy"


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
    assert passos["imagem"]["name"] == "gcr.io/cloud-builders/docker"
    env = " ".join(passos["infra"]["env"])
    for nome in ("AMBIENTE", "MODULO", "IMAGEM_SHA", "IMAGEM_BASE", "TF_ESTADO", "REGIAO", "DATAFORM_TOKEN_VERSAO"):
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
