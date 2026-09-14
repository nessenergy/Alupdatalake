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


AMBIENTES = ("dev", "hml", "prod")


def test_regiao_padrao_e_us_east1_em_todo_o_ambiente() -> None:
    """ADR 011: dataset do BigQuery não muda de região depois do primeiro apply."""
    assert _tem(r'variable "region" \{[^}]*default\s*=\s*"us-east1"', _ler("infra/variables.tf"))
    for ambiente in AMBIENTES:
        tfvars = _ler(f"infra/environments/{ambiente}.tfvars")
        assert _tem(r'region\s*=\s*"us-east1"', tfvars), ambiente
        assert _tem(rf'environment\s*=\s*"{ambiente}"', tfvars), ambiente


def test_infra_aceita_os_tres_ambientes() -> None:
    """ADR 015, revisão de 11/09 (E4): dev, hml e prod, cada um no seu projeto."""
    variavel = _bloco(_ler("infra/variables.tf"), 'variable "environment"')
    assert _tem(r'contains\(\["dev", "hml", "prod"\], var\.environment\)', variavel)


def test_deploy_oferece_os_tres_ambientes() -> None:
    workflow = _ler(".github/workflows/deploy.yml")
    entrada = workflow[workflow.index("      environment:") : workflow.index("      module:")]
    assert re.findall(r"^\s+- (\w+)$", entrada, re.MULTILINE) == list(AMBIENTES)


def test_state_do_infra_fica_no_bucket_do_proprio_ambiente() -> None:
    """Um bucket de state por projeto, criado pelo bootstrap; o nome vem do GitHub."""
    principal = _ler("infra/main.tf")
    backend = re.search(r'(?m)^  backend "gcs" \{(.*?)\n  \}', principal, re.DOTALL)
    assert backend, "backend gcs precisa estar declarado, não comentado"
    assert "bucket" not in backend.group(1)  # configuração parcial: vem no init
    assert _tem(r'prefix\s*=\s*"infra"', backend.group(1))

    workflow = _ler(".github/workflows/deploy.yml")
    bloco_terraform = workflow[workflow.index("  terraform:") : workflow.index("  sync-dags:")]
    assert 'terraform init -backend-config="bucket=${{ vars.TF_STATE_BUCKET }}"' in bloco_terraform
    # O CI valida sem credencial.
    assert "terraform init -backend=false" in _ler(".github/workflows/ci.yml")


def test_hml_nasce_sem_agendamento() -> None:
    """E2: hml é barato — Scheduler cobra por job existente, pausado ou não."""
    assert _tem(r"agendamentos_ativos\s*=\s*false", _ler("infra/environments/hml.tfvars"))
    for ambiente in ("dev", "prod"):
        assert "agendamentos_ativos" not in _ler(f"infra/environments/{ambiente}.tfvars")

    variavel = _bloco(_ler("infra/variables.tf"), 'variable "agendamentos_ativos"')
    assert _tem(r"type\s*=\s*bool", variavel)
    assert _tem(r"default\s*=\s*true", variavel)

    principal = _ler("infra/main.tf")
    for modulo in ('module "scheduler" {', 'module "dataform" {'):
        assert _tem(r"agendar\s*=\s*var\.agendamentos_ativos", _bloco(principal, modulo)), modulo

    # Sem agendamento, o Cloud Run Job continua existindo para execução manual.
    scheduler = _ler("infra/modules/scheduler/main.tf")
    disparo = _bloco(scheduler, 'resource "google_cloud_scheduler_job" "ingestao"')
    assert _tem(r"for_each\s*=\s*var\.agendar \? var\.conectores : \{\}", disparo)
    job = _bloco(scheduler, 'resource "google_cloud_run_v2_job" "ingestao"')
    assert _tem(r"for_each\s*=\s*var\.conectores", job)

    dataform = _ler("infra/modules/dataform/main.tf")
    assert "var.agendar" in _bloco(dataform, 'resource "google_dataform_repository_workflow_config" "diario"')


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


def test_chave_do_app_do_quadro_so_e_legivel_pela_conta_do_github() -> None:
    """Regra 2: a chave do GitHub App do quadro vive no Secret Manager, lida só pelo WIF do GitHub."""
    modulo = _ler("infra/modules/secrets/main.tf")
    assert _tem(r'secret_id\s*=\s*"alupdata-github-quadro-app-key"', modulo)
    assert "google_secret_manager_secret_version" not in modulo  # valor fora do Terraform

    # Fora da lista das fontes: o for_each da ingestão não pode alcançá-lo.
    segredos = _bloco(modulo, 'variable "segredos"')
    assert "alupdata-github-quadro-app-key" not in segredos

    acessos = [
        bloco.group(0)
        for bloco in re.finditer(r'resource "google_secret_manager_secret_iam_\w+" "\w+" \{.*?\n\}', modulo, re.DOTALL)
        if "quadro" in bloco.group(0)
    ]
    assert len(acessos) == 1
    assert '"roles/secretmanager.secretAccessor"' in acessos[0]
    assert _tem(r'member\s*=\s*"serviceAccount:\$\{var\.github_service_account\}"', acessos[0])
    assert _tem(r'count\s*=\s*var\.github_service_account == "" \? 0 : 1', acessos[0])

    # A conta do GitHub é a do WIF do deploy, não a da ingestão.
    bloco = _bloco(_ler("infra/main.tf"), 'module "secrets" {')
    assert _tem(r"github_service_account\s*=\s*var\.deploy_service_account", bloco)


def _quadro() -> str:
    return _ler(".github/workflows/quadro.yml")


def test_quadro_dispara_apos_deploy_com_sucesso_em_dia_util_e_a_mao() -> None:
    workflow = _quadro()
    nome_deploy = re.search(r"^name:\s*(.+)$", _ler(".github/workflows/deploy.yml"), re.MULTILINE).group(1).strip()

    assert _tem(
        rf'workflow_run:\s*\n\s*workflows:\s*\["{re.escape(nome_deploy)}"\]\s*\n\s*types:\s*\[completed\]', workflow
    )
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert _tem(r'schedule:\s*\n\s*-\s*cron:\s*"0 11 \* \* 1-5"', workflow)
    assert _tem(r"workflow_dispatch:\s*\n\s*inputs:\s*\n\s*simular:[^\n]*\n(\s+\w+:.*\n)*?\s*type:\s*boolean", workflow)


def test_quadro_tem_permissoes_minimas_e_nunca_roda_em_paralelo() -> None:
    workflow = _quadro()
    permissoes = re.search(r"^permissions:\n((?:  .+\n)+)", workflow, re.MULTILINE).group(1)
    assert sorted(linha.strip() for linha in permissoes.splitlines()) == ["contents: read", "id-token: write"]
    assert _tem(r"(?m)^concurrency:\n\s+group:\s*\S+\n\s+cancel-in-progress:\s*false", workflow)


def test_quadro_le_a_chave_do_secret_manager_e_mascara_sem_gravar_no_ambiente() -> None:
    workflow = _quadro()
    assert "google-github-actions/auth@v2" in workflow
    # A org está no plano Free e o repositório é privado: ambiente do GitHub
    # não existe nesse caso, e variável de ambiente nunca chegaria ao job.
    assert not _tem(r"(?m)^\s*environment:", workflow), "as variáveis do quadro ficam no repositório, não em ambiente"
    assert "gcloud secrets versions access latest --secret=alupdata-github-quadro-app-key" in workflow
    assert "::add-mask::" in workflow
    assert "actions/create-github-app-token@v3" in workflow
    assert "GITHUB_ENV" not in workflow
    assert "upload-artifact" not in workflow
    assert "secrets." not in workflow  # nada de chave nos secrets do GitHub (regra 2)
    assert "python -m scripts.quadro --aplicar" in workflow
    assert "GITHUB_TOKEN: ${{ steps.token.outputs.token }}" in workflow


def test_quadro_sem_gcp_ou_app_avisa_e_termina_com_sucesso() -> None:
    """Enquanto A3 e o App não existem, o agendamento não pode falhar todo dia."""
    workflow = _quadro()
    guarda = workflow[workflow.index("id: guarda") :]
    for variavel in ("vars.GCP_WIF_PROVIDER", "vars.GCP_DEPLOY_SA", "vars.QUADRO_APP_CLIENT_ID"):
        assert variavel in guarda
    assert "::notice::" in guarda
    assert "exit 1" not in guarda
    # Todo passo depois da guarda depende dela.
    passos = re.split(r"\n      - ", guarda)[1:]
    assert passos
    for passo in passos:
        assert "steps.guarda.outputs.pronto == 'true'" in passo, passo


def test_scheduler_repassa_a_regiao_para_o_cloud_run_job() -> None:
    """A regiao decide onde a linhagem e gravada e qual INFORMATION_SCHEMA e lido (ADR 013)."""
    modulo = _ler("infra/modules/scheduler/main.tf")
    assert _tem(r'name\s*=\s*"GCP_REGION"[^}]*value\s*=\s*var\.region', modulo)


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
            # `principalSet://` é a identidade federada do GitHub (bootstrap),
            # carga de trabalho e não pessoa: restrita ao repositório pela condição do WIF.
            if "serviceAccount:" not in membro.group(1) and "principalSet://" not in membro.group(1):
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


def test_alerta_de_frescor_distingue_entidades_da_mesma_fonte() -> None:
    """`ccee_pld` e `ccee_perfil` têm a mesma `fonte`; o alerta precisa da entidade.

    Sem isso, a execução semanal do cadastro satisfaria o alerta mensal do PLD:
    a série pararia de chegar e ninguém seria avisado.
    """
    monitoramento = _ler("infra/modules/monitoramento/main.tf")

    # a métrica precisa extrair a entidade, não só a fonte
    assert '"entidade" = "EXTRACT(jsonPayload.entidade)"' in monitoramento
    # e o alerta precisa filtrar pelas duas, não por uma delas
    assert "metric.labels.fonte" in monitoramento
    assert "metric.labels.entidade" in monitoramento

    # As duas entidades da CCEE têm frequências diferentes; é o caso que o
    # rótulo por fonte sozinho não distinguia.
    scheduler = _ler("infra/modules/scheduler/main.tf")
    assert "ccee_pld" in scheduler
    assert "ccee_perfil" in scheduler


def test_alerta_quando_o_workflow_do_dataform_falha() -> None:
    """Asserção violada que ninguém vê não é portão de qualidade (issue #110).

    O workflow diário roda às 11h e, se uma asserção reprovar, a invocação
    termina em falha. Sem alerta, a Silver segue servindo dado que já foi
    reprovado — e o erro só aparece quando alguém questiona um número.
    """
    monitoramento = _ler("infra/modules/monitoramento/main.tf")

    assert 'resource "google_monitoring_alert_policy" "dataform_falhou"' in monitoramento
    assert "dataform.googleapis.com" in monitoramento
    # o alerta precisa chegar em alguém
    assert "notification_channels" in monitoramento


def test_toda_silver_tem_assercao_de_faixa() -> None:
    """Unicidade e obrigatoriedade repetem o QUALIFY e os NOT NULL (ADR 012).

    A faixa é a única das três que pega mudança silenciosa de conteúdo na
    origem — sigla nova de submercado, preço negativo, hora fora do dia.
    """
    silver = sorted((RAIZ / "definitions" / "silver").glob("*.sqlx"))
    assert silver, "nenhuma view Silver encontrada"

    sem_faixa = [p.name for p in silver if "rowConditions" not in p.read_text(encoding="utf-8")]

    assert not sem_faixa, f"Silver sem asserção de faixa: {', '.join(sem_faixa)}"


def test_row_conditions_e_lista_e_nao_objeto_nomeado() -> None:
    """O Dataform aceita `rowConditions` como string[]; a forma nomeada não compila.

    Descoberto compilando: `rowConditions: {nome: "expr"}` é recusado com
    ReferenceError, e o erro aparece como dependência faltando nas Gold — a
    causa fica três camadas longe do sintoma.
    """
    for p in (RAIZ / "definitions" / "silver").glob("*.sqlx"):
        texto = p.read_text(encoding="utf-8")
        assert "rowConditions: {" not in texto, f"{p.name}: rowConditions como objeto não compila"
