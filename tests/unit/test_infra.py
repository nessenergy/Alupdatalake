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


# ------------------------------------------------ medidas do RIPD (item k)


def _bloco(texto: str, cabecalho: str) -> str:
    """Bloco HCL de nível superior que começa em `cabecalho`."""
    inicio = texto.index(cabecalho)
    return texto[inicio : texto.index("\n}\n", inicio)]


def _arquivos_tf() -> list[tuple[Path, str]]:
    """Código Terraform, sem os `.tfvars`: é neles que a Alup preenche os grupos."""
    return [
        (caminho, caminho.read_text(encoding="utf-8"))
        for caminho in (RAIZ / "infra").rglob("*.tf")
        if ".terraform" not in caminho.parts
    ]


def test_acesso_a_dado_do_bigquery_e_do_storage_gera_log_de_auditoria() -> None:
    """R07: log de acesso a dado declarado em `infra/`, não ligado no console."""
    bloco = _bloco(_ler("infra/main.tf"), 'resource "google_project_iam_audit_config" "acesso_dados"')

    assert '"bigquery.googleapis.com"' in bloco
    assert '"storage.googleapis.com"' in bloco
    assert _tem(r'log_type\s*=\s*"DATA_READ"', bloco)
    assert _tem(r'log_type\s*=\s*"DATA_WRITE"', bloco)
    # Isenção esconderia do log justamente as identidades que mais leem.
    assert "exempted_members" not in bloco


def test_grupos_de_pessoas_nascem_vazios() -> None:
    """R01: o e-mail do grupo é da Alup; sem ele preenchido, nada é concedido."""
    variaveis = _ler("infra/variables.tf")
    for nome in ("grupo_consumidores", "grupo_operacao"):
        assert _tem(rf'variable "{nome}" \{{[^}}]*default\s*=\s*""', variaveis), nome
    assert _tem(r'variable "portal_acesso" \{[^}]*default\s*=\s*\[\]', variaveis)


def test_consumidores_leem_so_a_gold_e_operacao_le_as_tres_camadas() -> None:
    """R01: Bronze e Silver só para quem opera."""
    principal = _ler("infra/main.tf")
    grupos = _bloco(principal, "locals {\n  camadas_por_grupo")

    assert _tem(r'consumidores\s*=\s*\{[^}]*camadas\s*=\s*\["gold"\]', grupos)
    assert _tem(r'operacao\s*=\s*\{[^}]*camadas\s*=\s*\["bronze", "silver", "gold"\]', grupos)
    assert _tem(r'if g\.grupo != ""', grupos)

    leitura = _bloco(principal, 'resource "google_bigquery_dataset_iam_member" "pessoas"')
    assert _tem(r"for_each\s*=\s*local\.leitura_pessoas", leitura)
    assert '"roles/bigquery.dataViewer"' in leitura
    assert "group:" in leitura

    jobs = _bloco(principal, 'resource "google_project_iam_member" "pessoas_jobs"')
    assert '"roles/bigquery.jobUser"' in jobs
    assert "for_each" in jobs


def test_nenhum_binding_humano_existe_com_os_defaults() -> None:
    """R01: todo IAM que não é de service account depende de variável preenchida."""
    for caminho, texto in _arquivos_tf():
        assert "allUsers" not in texto, caminho
        assert "allAuthenticatedUsers" not in texto, caminho
        # E-mail de pessoa ou de grupo não entra no código: vem de variável.
        for email in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", texto):
            assert email.endswith("gserviceaccount.com"), (caminho, email)

        for recurso in re.finditer(r'resource "\w+_iam_(?:member|binding)" "\w+" \{.*?\n\}', texto, re.DOTALL):
            bloco = recurso.group(0)
            membro = re.search(r"\n\s*members?\s*=\s*(.+)", bloco)
            assert membro, (caminho, bloco)
            if "serviceAccount:" not in membro.group(1):
                assert _tem(r"\n\s*(for_each|count)\s*=", bloco), (caminho, bloco)


def test_portal_publicado_pelo_terraform_atras_do_iap() -> None:
    """R01: o Portal sai do `gcloud run deploy` e o IAP entra em `infra/`."""
    modulo = _ler("infra/modules/portal/main.tf")
    servico = _bloco(modulo, 'resource "google_cloud_run_v2_service" "portal"')

    # Na 6.x fixada, `iap_enabled` só existe no provider beta.
    assert _tem(r"provider\s*=\s*google-beta", servico)
    assert _tem(r"iap_enabled\s*=\s*true", servico)
    assert "invoker_iam_disabled" not in servico
    assert _tem(r"service_account\s*=\s*google_service_account\.portal\.email", servico)
    assert _tem(r'path\s*=\s*"/saude"', servico)
    assert _tem(r'name\s*=\s*"PORTAL_PROVEDOR"\s*\n\s*value\s*=\s*"bigquery"', servico)

    # Quem invoca o serviço é o agente do IAP; pessoas passam pelo IAP.
    assert _tem(r'service\s*=\s*"iap\.googleapis\.com"', modulo)
    invocador = _bloco(modulo, 'resource "google_cloud_run_v2_service_iam_member" "iap_invoca"')
    assert '"roles/run.invoker"' in invocador
    assert "google_project_service_identity.iap.email" in invocador

    acesso = _bloco(modulo, 'resource "google_iap_web_cloud_run_service_iam_member" "acesso"')
    assert '"roles/iap.httpsResourceAccessor"' in acesso
    assert _tem(r"for_each\s*=\s*toset\(var\.acesso\)", acesso)


def test_portal_so_le_dado() -> None:
    modulo = _ler("infra/modules/portal/main.tf")
    assert 'resource "google_service_account" "portal"' in modulo
    assert '"roles/bigquery.dataViewer"' in modulo
    assert '"roles/bigquery.jobUser"' in modulo
    assert "dataEditor" not in modulo
    assert "roles/editor" not in modulo


def test_portal_sobe_com_a_imagem_e_acesso_vem_de_variavel_restrita() -> None:
    bloco = _bloco(_ler("infra/main.tf"), 'module "portal" {')
    assert _tem(r'count\s*=\s*var\.imagem_ingestao == "" \? 0 : 1', bloco)
    assert _tem(r"acesso\s*=\s*var\.portal_acesso", bloco)

    # Só grupo ou domínio: `user:` espalharia concessão individual pelo tfvars.
    variavel = _bloco(_ler("infra/variables.tf"), 'variable "portal_acesso"')
    assert "validation" in variavel
    assert "group:" in variavel
    assert "domain:" in variavel
