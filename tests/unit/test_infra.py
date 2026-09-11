"""Invariantes locais da infraestrutura antes de existir um projeto GCP."""

import re
from pathlib import Path

RAIZ = Path(__file__).parents[2]


def _ler(caminho: str) -> str:
    return (RAIZ / caminho).read_text(encoding="utf-8")


def test_ingestao_nao_recebe_editor_bigquery_nem_secrets_no_projeto() -> None:
    principal = _ler("infra/main.tf")
    bloco_projeto = principal[
        principal.index("locals {\n  papeis_ingestao") : principal.index(
            'resource "google_bigquery_dataset_iam_member"'
        )
    ]

    assert '"roles/bigquery.jobUser"' in bloco_projeto
    # Linhagem é gravada no projeto; não há recurso mais estreito (ADR 013).
    assert '"roles/datalineage.producer"' in bloco_projeto
    assert '"roles/bigquery.dataEditor"' not in bloco_projeto
    assert '"roles/secretmanager.secretAccessor"' not in bloco_projeto
    assert 'resource "google_bigquery_dataset_iam_member" "ingestao_bronze"' in principal


def test_bucket_e_secrets_tem_iam_no_proprio_recurso() -> None:
    assert 'resource "google_storage_bucket_iam_member"' in _ler("infra/modules/storage/main.tf")
    assert '"roles/storage.objectViewer"' in _ler("infra/modules/storage/main.tf")
    assert 'resource "google_secret_manager_secret_iam_member"' in _ler("infra/modules/secrets/main.tf")


def test_deploy_all_publica_imagem_antes_do_terraform_e_executa_o_dataform_depois() -> None:
    workflow = _ler(".github/workflows/deploy.yml")
    bloco_terraform = workflow[workflow.index("  terraform:") : workflow.index("  sync-dags:")]

    assert "needs: imagem" in bloco_terraform
    assert 'TAG="${GITHUB_SHA}"' in bloco_terraform
    # A carga nunca cria tabela Bronze: o Dataform precisa rodar antes da primeira ingestão.
    assert bloco_terraform.index("terraform apply") < bloco_terraform.index("scripts.executar_dataform")
    assert "scripts.deploy_views" not in workflow
    # Sem repositório (primeiro apply, token ainda não gravado), falha explícita.
    assert "repositorio_dataform" in bloco_terraform
    assert "::error::" in bloco_terraform
    assert "--repositorio" in bloco_terraform


def _tem(padrao: str, texto: str) -> bool:
    """Regex tolerante ao alinhamento que o `terraform fmt` impõe."""
    return re.search(padrao, texto) is not None


def test_regiao_padrao_e_us_east1_em_todo_o_ambiente() -> None:
    """ADR 011: dataset do BigQuery não muda de região depois do primeiro apply."""
    assert _tem(r'variable "region" \{[^}]*default\s*=\s*"us-east1"', _ler("infra/variables.tf"))
    for ambiente in ("dev", "prod"):
        assert _tem(r'region\s*=\s*"us-east1"', _ler(f"infra/environments/{ambiente}.tfvars"))


def test_secrets_ficam_na_regiao_do_ambiente() -> None:
    """ADR 011: réplica só na região do ambiente, sem depender de `global` na política de localização."""
    modulo = _ler("infra/modules/secrets/main.tf")
    assert "user_managed" in modulo
    assert _tem(r"location\s*=\s*var\.region", modulo)
    assert "auto {}" not in modulo

    principal = _ler("infra/main.tf")
    inicio = principal.index('module "secrets" {')
    bloco = principal[inicio : principal.index("\n}\n", inicio)]
    assert _tem(r"region\s*=\s*var\.region", bloco)


def test_nenhuma_regiao_antiga_sobrou_na_infra() -> None:
    for caminho in (RAIZ / "infra").rglob("*.tf*"):
        if ".terraform" in caminho.parts:
            continue
        assert "southamerica" not in caminho.read_text(encoding="utf-8"), caminho


def test_config_aponta_para_a_regiao_do_ambiente() -> None:
    """O INFORMATION_SCHEMA é por região: padrão errado devolve zero linhas em silêncio."""
    from src.core.config import Settings

    assert Settings.model_fields["gcp_region"].default == "us-east1"


def test_dataset_do_billing_export_existe_sem_acesso_da_ingestao() -> None:
    """ADR 007, adendo de 10/09: dataset regional não recebe carga retroativa."""
    modulo = _ler("infra/modules/bigquery/main.tf")
    inicio = modulo.index('resource "google_bigquery_dataset" "faturamento"')
    bloco = modulo[inicio : modulo.index("\n}\n", inicio)]

    assert _tem(r'dataset_id\s*=\s*"faturamento"', bloco)
    assert _tem(r"location\s*=\s*var\.region", bloco)
    assert _tem(r"delete_contents_on_destroy\s*=\s*false", bloco)
    # IAM aditivo: bloco `access` autoritativo apagaria o OWNER que o Cloud
    # Billing se concede no dataset quando o export é ligado.
    assert "access {" not in bloco

    # A ingestão não recebe IAM sobre a fatura, que traz todos os projetos da conta.
    for caminho in (RAIZ / "infra").rglob("*.tf*"):
        if ".terraform" in caminho.parts:
            continue
        texto = caminho.read_text(encoding="utf-8")
        for iam in re.finditer(r'resource "google_bigquery_dataset_iam_\w+" "\w+" \{.*?\n\}', texto, re.DOTALL):
            assert "faturamento" not in iam.group(0), caminho


def test_projeto_dataform_na_raiz_com_versao_e_regiao_fixas() -> None:
    """ADR 012: o Dataform lê o projeto só a partir da raiz do repositório Git."""
    settings = _ler("workflow_settings.yaml")
    assert _tem(r"dataformCoreVersion:\s*3\.0\.69", settings)
    assert _tem(r"defaultLocation:\s*us-east1", settings)
    assert _tem(r"regiao:\s*us-east1", settings)
    assert _tem(r"defaultAssertionDataset:\s*qualidade", settings)


def test_ci_e_makefile_compilam_o_dataform_na_mesma_versao() -> None:
    assert "dataform-compile:" in _ler(".github/workflows/ci.yml")
    assert "@dataform/cli@3.0.69 compile" in _ler(".github/workflows/ci.yml")
    assert "@dataform/cli@3.0.69 compile" in _ler("Makefile")


def test_dataform_executa_com_service_account_propria() -> None:
    """Strict act-as: o agente do Dataform personifica uma SA do projeto."""
    modulo = _ler("infra/modules/dataform/main.tf")
    assert 'resource "google_service_account" "dataform"' in modulo
    assert _tem(r"service_account\s*=\s*google_service_account\.dataform\.email", modulo)
    assert '"roles/iam.serviceAccountTokenCreator"' in modulo
    assert 'resource "google_project_service_identity" "dataform"' in modulo
    assert _tem(r'service\s*=\s*"dataform\.googleapis\.com"', modulo)
    assert "local.agente_dataform" in modulo


def test_repositorio_dataform_roda_como_a_propria_service_account() -> None:
    """A execução herda o IAM da SA do Dataform, não do agente de serviço."""
    modulo = _ler("infra/modules/dataform/main.tf")
    inicio = modulo.index('resource "google_dataform_repository" "alupdata"')
    bloco = modulo[inicio : modulo.index("\n}\n", inicio)]
    assert _tem(r"service_account\s*=\s*google_service_account\.dataform\.email", bloco)


def test_dataform_le_metadados_do_projeto_para_a_view_de_custo() -> None:
    """gold.custo_consultas le JOBS_BY_PROJECT e TABLE_STORAGE: metadado, nunca dado (regra 2)."""
    modulo = _ler("infra/modules/dataform/main.tf")
    inicio = modulo.index('resource "google_project_iam_member" "dataform_metadados"')
    bloco = modulo[inicio : modulo.index("\n}\n", inicio)]
    assert "for_each" in bloco
    assert '"roles/bigquery.resourceViewer"' in bloco
    assert '"roles/bigquery.metadataViewer"' in bloco
    assert "google_service_account.dataform.email" in bloco


def test_token_do_git_so_e_legivel_pelo_agente_do_dataform() -> None:
    modulo = _ler("infra/modules/dataform/main.tf")
    assert _tem(r'secret_id\s*=\s*"alupdata-dataform-git-token"', modulo)
    assert "google_secret_manager_secret_version" not in modulo  # valor fora do Terraform (regra 2)
    assert "alupdata-dataform-git-token" not in _ler("infra/modules/secrets/main.tf")  # a ingestão não lê


def test_dataform_compila_a_main_na_regiao_do_ambiente() -> None:
    modulo = _ler("infra/modules/dataform/main.tf")
    assert _tem(r'git_commitish\s*=\s*"main"', modulo)
    assert _tem(r"default_location\s*=\s*var\.region", modulo)
    assert _tem(r"regiao\s*=\s*var\.region", modulo)
    assert _tem(r'assertion_schema\s*=\s*"qualidade"', modulo)
    assert 'resource "google_bigquery_dataset" "qualidade"' in _ler("infra/modules/bigquery/main.tf")


def test_deploy_edita_so_o_repositorio_dataform_nao_o_projeto() -> None:
    """Least privilege: o deploy so precisa compilar e executar o repositorio alupdata."""
    modulo = _ler("infra/modules/dataform/main.tf")
    assert 'resource "google_dataform_repository_iam_member" "deploy_dataform"' in modulo
    assert '"roles/dataform.editor"' in modulo

    for bloco in re.finditer(r'resource "google_project_iam_member" "\w+" \{.*?\n\}', modulo, re.DOTALL):
        assert "roles/dataform.editor" not in bloco.group(0)
