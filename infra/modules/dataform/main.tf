# Dataform (ADR 012): o SQL das três camadas, compilado a partir da `main`.
#
# Strict act-as: o Dataform executa com uma service account própria, que o
# agente de serviço do Dataform personifica. O token do GitHub entra fora do
# versionamento, como os secrets das fontes:
#   gcloud secrets versions add alupdata-dataform-git-token --data-file=-
# Enquanto `git_token_versao` estiver vazio, repositório e configs não são
# criados: sem credencial para ler o Git, não há o que compilar.

terraform {
  required_providers {
    google      = { source = "hashicorp/google" }
    google-beta = { source = "hashicorp/google-beta" }
  }
}

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "datasets" {
  description = "Datasets em que o Dataform escreve: as três camadas e o de assertions"
  type        = list(string)
}
variable "git_url" {
  description = "Repositório Git lido pelo Dataform"
  type        = string
  default     = "https://github.com/nessenergy/Alupdatalake.git"
}
variable "git_token_versao" {
  description = "Versão do secret com o token do GitHub (ex.: \"1\"); vazio não cria o repositório"
  type        = string
  default     = ""
}
variable "deploy_service_account" {
  description = "SA do workflow de deploy, que dispara o Dataform após o apply; vazio não concede"
  type        = string
  default     = ""
}

variable "agendar" {
  description = "Cria o workflow config `diario`; false deixa o Dataform só sob demanda, disparado pelo deploy"
  type        = bool
  default     = true
}

# Agente de serviço do Dataform: existe só depois que a API é habilitada, daí
# vir de um recurso, e não de uma convenção de nome montada à mão.
resource "google_project_service_identity" "dataform" {
  provider = google-beta
  project  = var.project_id
  service  = "dataform.googleapis.com"
}

locals {
  agente_dataform = google_project_service_identity.dataform.email
  criar           = var.git_token_versao != ""
}

# ------------------------------------------------------------------ identidade

resource "google_service_account" "dataform" {
  account_id   = "alupdata-dataform"
  display_name = "AlupData — Dataform"
  project      = var.project_id
}

resource "google_project_iam_member" "dataform_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.dataform.email}"
}

resource "google_bigquery_dataset_iam_member" "dataform" {
  for_each = toset(var.datasets)

  project    = var.project_id
  dataset_id = each.value
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.dataform.email}"
}

# Só metadado, nunca dado: `gold.custo_consultas` lê quem rodou cada consulta
# (INFORMATION_SCHEMA.JOBS_BY_PROJECT, exige `bigquery.jobs.listAll`) e o
# tamanho de cada tabela (INFORMATION_SCHEMA.TABLE_STORAGE) do projeto inteiro.
resource "google_project_iam_member" "dataform_metadados" {
  for_each = toset(["roles/bigquery.resourceViewer", "roles/bigquery.metadataViewer"])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.dataform.email}"
}

# O agente de serviço personifica a SA nas execuções (strict act-as).
resource "google_service_account_iam_member" "agente_personifica" {
  for_each = toset(["roles/iam.serviceAccountTokenCreator", "roles/iam.serviceAccountUser"])

  service_account_id = google_service_account.dataform.name
  role               = each.value
  member             = "serviceAccount:${local.agente_dataform}"
}

# O deploy dispara a execução logo após o apply, agindo como a SA do Dataform.
resource "google_service_account_iam_member" "deploy_age_como_dataform" {
  count = var.deploy_service_account == "" ? 0 : 1

  service_account_id = google_service_account.dataform.name
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${var.deploy_service_account}"
}

# O deploy só precisa compilar e executar este repositório, não qualquer
# repositório Dataform do projeto.
resource "google_dataform_repository_iam_member" "deploy_dataform" {
  count    = local.criar && var.deploy_service_account != "" ? 1 : 0
  provider = google-beta

  project    = var.project_id
  region     = var.region
  repository = google_dataform_repository.alupdata[0].name
  role       = "roles/dataform.editor"
  member     = "serviceAccount:${var.deploy_service_account}"
}

# ------------------------------------------------------------------ Git

resource "google_secret_manager_secret" "git_token" {
  secret_id = "alupdata-dataform-git-token"
  project   = var.project_id

  # Réplica só na região do ambiente (ADR 011), como os secrets das fontes.
  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

resource "google_secret_manager_secret_iam_member" "agente_le_token" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.git_token.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${local.agente_dataform}"
}

# ------------------------------------------------------------------ Dataform

resource "google_dataform_repository" "alupdata" {
  count    = local.criar ? 1 : 0
  provider = google-beta

  name            = "alupdata"
  project         = var.project_id
  region          = var.region
  service_account = google_service_account.dataform.email

  git_remote_settings {
    url                                 = var.git_url
    default_branch                      = "main"
    authentication_token_secret_version = "${google_secret_manager_secret.git_token.id}/versions/${var.git_token_versao}"
  }

  depends_on = [
    google_secret_manager_secret_iam_member.agente_le_token,
    google_service_account_iam_member.agente_personifica,
    google_service_account_iam_member.deploy_age_como_dataform,
  ]
}

resource "google_dataform_repository_release_config" "main" {
  count    = local.criar ? 1 : 0
  provider = google-beta

  project    = var.project_id
  region     = var.region
  repository = google_dataform_repository.alupdata[0].name

  name          = "main"
  git_commitish = "main"
  cron_schedule = "30 10 * * *"
  time_zone     = "America/Sao_Paulo"

  code_compilation_config {
    default_database = var.project_id
    default_location = var.region
    assertion_schema = "qualidade"
    vars = {
      regiao = var.region
    }
  }
}

# As ingestões diárias da manhã rodam entre 07h e 10h; o Hubspot, porém, roda a
# cada 6h, então suas cargas de 12h e 18h só são conferidas por este workflow
# no dia seguinte. Na Onda 3 o Airflow assume o disparo, com dependência real
# em vez de horário (ADR 004).
#
# Sem `agendar` (hml fora da homologação), o workflow não existe: o deploy
# continua executando o Dataform pela release config `main`.
resource "google_dataform_repository_workflow_config" "diario" {
  count    = local.criar && var.agendar ? 1 : 0
  provider = google-beta

  project        = var.project_id
  region         = var.region
  repository     = google_dataform_repository.alupdata[0].name
  name           = "diario"
  release_config = google_dataform_repository_release_config.main[0].id
  cron_schedule  = "0 11 * * *"
  time_zone      = "America/Sao_Paulo"

  invocation_config {
    transitive_dependencies_included = true
    service_account                  = google_service_account.dataform.email
  }

  depends_on = [
    google_service_account_iam_member.agente_personifica,
    google_service_account_iam_member.deploy_age_como_dataform,
  ]
}

output "service_account" {
  description = "SA que executa o Dataform"
  value       = google_service_account.dataform.email
}

output "repositorio" {
  description = "Nome do repositório Dataform (vazio enquanto não houver token)"
  value       = try(google_dataform_repository.alupdata[0].name, "")
}
