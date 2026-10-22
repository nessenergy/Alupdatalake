# CI no Cloud Build (ADR 030, fase 1).
#
# Os gatilhos rodam `cloudbuild/ci.yaml` como uma conta de serviço própria, que só escreve log:
# o CI lê o repositório pela conexão do GitHub e não toca em dado, segredo nem deploy.
#
# O repositório precisa estar conectado ao projeto antes (passo humano de dono da organização:
# aplicativo do Cloud Build no GitHub). Sem isso, a criação do gatilho falha.

variable "project_id" { type = string }
variable "repositorio_dono" { type = string }
variable "repositorio_nome" { type = string }

# Operações sob demanda (ADR 030): gatilhos manuais que rodam como a conta de deploy.
variable "deploy_service_account_id" {
  description = "id completo da conta de deploy: projects/<projeto>/serviceAccounts/<e-mail>"
  type        = string
  validation {
    condition     = can(regex("^projects/[^/]+/serviceAccounts/.+$", var.deploy_service_account_id))
    error_message = "Informe projects/<projeto>/serviceAccounts/<e-mail>; deploy_service_account vazio não serve."
  }
}
variable "regiao" { type = string }

# Deploy no Cloud Build (ADR 030): um gatilho por ambiente, criado pela chamada do módulo em cada projeto.
variable "ambiente" {
  description = "Ambiente do deploy: dev, hml ou prod"
  type        = string
  validation {
    condition     = contains(["dev", "hml", "prod"], var.ambiente)
    error_message = "Ambiente deve ser 'dev', 'hml' ou 'prod'."
  }
}
variable "dataform_token_versao" {
  description = "Versão do secret do token do Dataform (alupdata-dataform-git-token)"
  type        = string
  default     = "1"
}

# Checagem de atribuição no Cloud Build: o passo busca-main lê a main do repositório privado com o token de um
# GitHub App (decisão D1). Vazio, o gatilho de PR segue com `cloudbuild/ci.yaml`, sem a checagem e sem segredo.
variable "github_app_ci_client_id" {
  description = "client_id do GitHub App de leitura do CI; vazio mantém o PR sem ci-atribuicao"
  type        = string
  default     = ""
}

resource "google_service_account" "ci" {
  project      = var.project_id
  account_id   = "alupdata-ci"
  display_name = "CI do AlupData no Cloud Build"
}

# Só escreve log. Nenhum papel de dado, de segredo ou de deploy.
resource "google_project_iam_member" "ci_log" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ci.email}"
}

# Chave privada do GitHub App de leitura do CI. Contêiner vazio: o valor entra fora do Terraform (regra 2):
#   gcloud secrets versions add alupdata-github-ci-app-key --data-file=chave.pem
# Criado sempre; só o gatilho de PR o usa, e só com github_app_ci_client_id preenchido.
resource "google_secret_manager_secret" "ci_app_key" {
  secret_id = "alupdata-github-ci-app-key"
  project   = var.project_id

  # Réplica só na região do ambiente (ADR 011), como os outros segredos.
  replication {
    user_managed {
      replicas {
        location = var.regiao
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.ambiente
  }
}

# Único segredo que a conta do CI lê.
resource "google_secret_manager_secret_iam_member" "ci_le_chave_do_app" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.ci_app_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ci.email}"
}

# PR de quem não é dono só roda depois de um comentário de aprovação (o repositório é privado, mas a regra vale se mudar).
resource "google_cloudbuild_trigger" "pr" {
  project         = var.project_id
  name            = "alupdata-ci-pr"
  description     = "CI de todo PR para a main (ADR 030)"
  filename        = var.github_app_ci_client_id == "" ? "cloudbuild/ci.yaml" : "cloudbuild/ci-com-atribuicao.yaml"
  service_account = google_service_account.ci.id

  # Sem client id: os alvos de hoje, sem ci-atribuicao. Com ele: o ci completo e o passo busca-main.
  substitutions = var.github_app_ci_client_id == "" ? {
    _ALVOS = "ci-lint ci-testes ci-sast ci-segredos ci-terraform ci-dataform ci-sca"
    } : {
    _ALVOS         = "ci"
    _CLIENT_ID_APP = var.github_app_ci_client_id
  }

  github {
    owner = var.repositorio_dono
    name  = var.repositorio_nome

    pull_request {
      branch          = "^main$"
      comment_control = "COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY"
    }
  }

  depends_on = [google_project_iam_member.ci_log]
}

# Push na main: as mesmas etapas, menos a checagem de atribuição, que compara com o ramo do PR.
resource "google_cloudbuild_trigger" "main" {
  project         = var.project_id
  name            = "alupdata-ci-main"
  description     = "CI depois do merge na main (ADR 030)"
  filename        = "cloudbuild/ci.yaml"
  service_account = google_service_account.ci.id

  substitutions = {
    _ALVOS = "ci-lint ci-testes ci-sast ci-segredos ci-terraform ci-dataform ci-sca"
  }

  github {
    owner = var.repositorio_dono
    name  = var.repositorio_nome

    push {
      branch = "^main$"
    }
  }

  depends_on = [google_project_iam_member.ci_log]
}

# Operações sob demanda: gatilhos manuais (sem bloco github{}, não disparam no push), rodados com
# `gcloud builds triggers run <nome> --branch=main --substitutions=...`. O repositório é o do
# GitHub conectado pelo aplicativo do Cloud Build (1ª geração).
locals {
  repositorio_uri = "https://github.com/${var.repositorio_dono}/${var.repositorio_nome}"
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
    uri       = local.repositorio_uri
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = "cloudbuild/operar.yaml"
    uri       = local.repositorio_uri
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }
}

# Deploy (ADR 030): gatilho manual, como a conta de deploy, com o comportamento do workflow deploy.yml.
# `_MODULO=infra` exige `_IMAGEM_SHA` (SHA completo de uma imagem já publicada).
resource "google_cloudbuild_trigger" "deploy" {
  project         = var.project_id
  name            = "alupdata-deploy"
  description     = "Deploy de ${var.ambiente} (ADR 030): gcloud builds triggers run alupdata-deploy --branch=main --substitutions=_MODULO=all"
  service_account = var.deploy_service_account_id
  filename        = "cloudbuild/deploy.yaml"

  substitutions = {
    _AMBIENTE              = var.ambiente
    _MODULO                = "all"
    _IMAGEM_SHA            = ""
    _IMAGEM_BASE           = "${var.regiao}-docker.pkg.dev/${var.project_id}/alupdata/cli"
    _TF_ESTADO             = "${var.project_id}-tfstate"
    _REGIAO                = var.regiao
    _CONTA_DEPLOY          = element(split("/", var.deploy_service_account_id), 3)
    _DATAFORM_TOKEN_VERSAO = var.dataform_token_versao
  }

  source_to_build {
    uri       = local.repositorio_uri
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = "cloudbuild/deploy.yaml"
    uri       = local.repositorio_uri
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }
}

# ---------------------------------------------------------------------------------------------- agendados
# Agendados (ADR 030, Tarefa 7): SCA, atribuição, quadro e painel saem do GitHub Actions. Cada um tem o próprio
# yaml (cloudbuild/agendado-<tarefa>.yaml), um gatilho manual `alupdata-ag-<tarefa>` e um job do Cloud Scheduler
# que o dispara pela API (`triggers/<nome>:run`). Tudo é opt-in por tarefa e vem desligado: um agendado cujo
# segredo ainda não tem versão derrubaria o build, e o Scheduler só geraria falha diária.
#
# Pré-requisitos humanos, por tarefa:
#   atribuicao e painel: `github_app_ci_client_id` preenchido e versão do segredo alupdata-github-ci-app-key (D1).
#   quadro: `github_app_quadro_client_id` e versão do segredo alupdata-github-quadro-app-key.
#   painel: a ness. concede `roles/storage.objectAdmin` sobre o bucket ness-painel-projetos-alupdata à conta
#     alupdata-painel (D2); o projeto da ness. está fora deste infra/. Em hml, a conta entra na variável raiz
#     `leitores_execucoes`.
variable "agendados" {
  description = "Liga cada tarefa agendada (gatilho e Scheduler); tudo desligado por padrão"
  type = object({
    sca        = bool
    atribuicao = bool
    quadro     = bool
    painel     = bool
  })
  default = {
    sca        = false
    atribuicao = false
    quadro     = false
    painel     = false
  }
}
variable "github_app_quadro_client_id" {
  description = "client_id do GitHub App do quadro; vazio faz o agendado do quadro avisar e sair com sucesso"
  type        = string
  default     = ""
}
variable "quadro_secret_id" {
  description = "Id do segredo da chave do App do quadro (módulo secrets)"
  type        = string
  default     = "alupdata-github-quadro-app-key"
}
variable "dataset_bronze" {
  description = "Dataset bronze do projeto, que a conta do painel lê"
  type        = string
  default     = "bronze"
}
variable "painel_bucket" {
  description = "Bucket do painel, no projeto da ness."
  type        = string
  default     = "ness-painel-projetos-alupdata"
}
variable "projeto_hml" {
  description = "Projeto de hml que o painel lê"
  type        = string
  default     = "alupar-hm-alupdata"
}

resource "google_service_account" "agendador" {
  project      = var.project_id
  account_id   = "alupdata-agendador"
  display_name = "Cloud Scheduler dos agendados do AlupData"
}

locals {
  agendados_def = {
    sca = {
      cron          = "0 11 * * 1"
      arquivo       = "cloudbuild/agendado-sca.yaml"
      conta         = "ci"
      substitutions = tomap({})
    }
    atribuicao = {
      cron          = "0 11 * * *"
      arquivo       = "cloudbuild/agendado-atribuicao.yaml"
      conta         = "ci"
      substitutions = tomap({ _CLIENT_ID_APP = var.github_app_ci_client_id })
    }
    quadro = {
      cron          = "0 11 * * 1-5"
      arquivo       = "cloudbuild/agendado-quadro.yaml"
      conta         = "ci"
      substitutions = tomap({ _CLIENT_ID_APP = var.github_app_quadro_client_id })
    }
    painel = {
      cron    = "7 */3 * * *"
      arquivo = "cloudbuild/agendado-painel.yaml"
      conta   = "painel"
      substitutions = tomap({
        _CLIENT_ID_APP = var.github_app_ci_client_id
        _PAINEL_BUCKET = var.painel_bucket
        _PROJETO_DEV   = var.project_id
        _PROJETO_HML   = var.projeto_hml
      })
    }
  }
  agendados_ligados = { for k, v in local.agendados_def : k => v if var.agendados[k] }
}

# Só roda gatilho. `builds.editor` é o menor papel predefinido com `cloudbuild.builds.create`, que o `:run` exige.
resource "google_project_iam_member" "agendador_roda_gatilho" {
  count = length(local.agendados_ligados) > 0 ? 1 : 0

  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.agendador.email}"
}

# Disparar gatilho com conta própria exige agir como essa conta.
resource "google_service_account_iam_member" "agendador_age_como" {
  for_each = toset([for k, v in local.agendados_ligados : v.conta])

  service_account_id = each.value == "painel" ? google_service_account.painel[0].id : google_service_account.ci.id
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.agendador.email}"
}

# A conta do CI só lê o segredo do quadro se o agendado do quadro estiver ligado.
resource "google_secret_manager_secret_iam_member" "ci_le_chave_do_quadro" {
  count = var.agendados.quadro ? 1 : 0

  project   = var.project_id
  secret_id = var.quadro_secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ci.email}"
}

# Conta própria do painel: lê metadado de execução de dev e o segredo do App de leitura. Escrita no bucket do
# painel não está aqui (projeto da ness.): ver o cabeçalho desta seção.
resource "google_service_account" "painel" {
  count = var.agendados.painel ? 1 : 0

  project      = var.project_id
  account_id   = "alupdata-painel"
  display_name = "Painel do AlupData no Cloud Build"
}

resource "google_project_iam_member" "painel" {
  for_each = var.agendados.painel ? toset(["roles/logging.logWriter", "roles/bigquery.jobUser", "roles/run.viewer"]) : toset([])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.painel[0].email}"
}

resource "google_bigquery_dataset_iam_member" "painel_le_bronze" {
  count = var.agendados.painel ? 1 : 0

  project    = var.project_id
  dataset_id = var.dataset_bronze
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.painel[0].email}"
}

resource "google_secret_manager_secret_iam_member" "painel_le_chave_do_app" {
  count = var.agendados.painel ? 1 : 0

  project   = var.project_id
  secret_id = google_secret_manager_secret.ci_app_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.painel[0].email}"
}

resource "google_cloudbuild_trigger" "agendado" {
  for_each = local.agendados_ligados

  project         = var.project_id
  name            = "alupdata-ag-${each.key}"
  description     = "Agendado ${each.key} (ADR 030): disparado pelo Cloud Scheduler, ou gcloud builds triggers run alupdata-ag-${each.key} --branch=main"
  service_account = each.value.conta == "painel" ? google_service_account.painel[0].id : google_service_account.ci.id
  filename        = each.value.arquivo
  substitutions   = each.value.substitutions

  source_to_build {
    uri       = local.repositorio_uri
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = each.value.arquivo
    uri       = local.repositorio_uri
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }

  lifecycle {
    # Atribuição e painel usam o token do App de leitura do CI; sem client id o build falharia todo dia.
    precondition {
      condition     = !contains(["atribuicao", "painel"], each.key) || var.github_app_ci_client_id != ""
      error_message = "Os agendados atribuicao e painel exigem github_app_ci_client_id preenchido (decisão D1)."
    }
  }

  depends_on = [google_project_iam_member.painel]
}

resource "google_cloud_scheduler_job" "agendado" {
  for_each = local.agendados_ligados

  project   = var.project_id
  region    = var.regiao
  name      = "alupdata-ag-${each.key}"
  schedule  = each.value.cron
  time_zone = "Etc/UTC"

  # Sem nova tentativa: um build repetido em cima de outro só duplicaria o efeito (comentário, publicação).
  retry_config {
    retry_count = 0
  }

  http_target {
    http_method = "POST"
    uri         = "https://cloudbuild.googleapis.com/v1/projects/${var.project_id}/locations/global/triggers/${google_cloudbuild_trigger.agendado[each.key].name}:run"
    headers     = { "Content-Type" = "application/json" }
    body        = base64encode(jsonencode({ source = { branchName = "main" } }))

    oauth_token {
      service_account_email = google_service_account.agendador.email
    }
  }

  depends_on = [google_project_iam_member.agendador_roda_gatilho]
}
