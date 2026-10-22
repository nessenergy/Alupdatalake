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
    assert modulo.count('resource "google_cloudbuild_trigger"') == 2


def test_modulo_cicd_so_existe_quando_a_variavel_for_preenchida() -> None:
    principal = _ler("infra/main.tf")
    assert 'module "cicd"' in principal
    assert re.search(r"count\s*=\s*var\.cicd\s*==\s*null\s*\?\s*0\s*:\s*1", principal)
    variavel = _ler("infra/variables.tf")
    assert re.search(r'variable "cicd" \{.*?default\s*=\s*null', variavel, re.DOTALL)


def test_conta_de_deploy_pode_criar_gatilho() -> None:
    bootstrap = _ler("infra/bootstrap/main.tf")
    assert '"roles/cloudbuild.builds.editor"' in bootstrap
