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
    assert '"roles/bigquery.dataEditor"' not in bloco_projeto
    assert '"roles/secretmanager.secretAccessor"' not in bloco_projeto
    assert 'resource "google_bigquery_dataset_iam_member" "ingestao_bronze"' in principal


def test_bucket_e_secrets_tem_iam_no_proprio_recurso() -> None:
    assert 'resource "google_storage_bucket_iam_member"' in _ler("infra/modules/storage/main.tf")
    assert '"roles/storage.objectViewer"' in _ler("infra/modules/storage/main.tf")
    assert 'resource "google_secret_manager_secret_iam_member"' in _ler("infra/modules/secrets/main.tf")


def test_deploy_all_publica_imagem_antes_do_terraform() -> None:
    workflow = _ler(".github/workflows/deploy.yml")
    bloco_terraform = workflow[workflow.index("  terraform:") : workflow.index("  sync-dags:")]

    assert "needs: imagem" in bloco_terraform
    assert 'TAG="${GITHUB_SHA}"' in bloco_terraform
    assert "scripts.deploy_views" in bloco_terraform


def _tem(padrao: str, texto: str) -> bool:
    """Regex tolerante ao alinhamento que o `terraform fmt` impõe."""
    return re.search(padrao, texto) is not None


def test_regiao_padrao_e_us_east1_em_todo_o_ambiente() -> None:
    """ADR 011: dataset do BigQuery não muda de região depois do primeiro apply."""
    assert _tem(r'default\s*=\s*"us-east1"', _ler("infra/variables.tf"))
    for ambiente in ("dev", "prod"):
        assert _tem(r'region\s*=\s*"us-east1"', _ler(f"infra/environments/{ambiente}.tfvars"))


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
    # IAM aditivo: bloco `access` autoritativo apagaria a escrita que o Cloud
    # Billing concede a si mesmo quando o export é ligado.
    assert "access {" not in bloco
    # A ingestão não lê a fatura, que traz todos os projetos da conta.
    assert "faturamento" not in _ler("infra/main.tf")
