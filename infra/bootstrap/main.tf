# Bootstrap de um projeto do AlupData (ADR 015, revisão de 11/09).
#
# Raiz Terraform separada de `infra/`, aplicada pela ness. uma vez por projeto
# (dev, hml e prod), com a identidade de uma pessoa, antes do primeiro deploy.
# Cria o que o deploy precisa para existir: as APIs, o bucket de state do
# `infra/`, o repositório de imagens, a federação com o GitHub e a conta de
# serviço de deploy. Todo o resto é do `infra/`, aplicado pelo workflow.
#
# State local, um workspace por projeto (`terraform.tfstate.d/<ambiente>/`,
# fora do git). Depois do apply, uma cópia vai para o próprio bucket de state —
# passo a passo em docs/runbook/primeiro-deploy.md. O state não guarda segredo:
# a SA de deploy não tem chave.
#
# Os papéis que a Alup concede à ness. no projeto para aplicar esta raiz estão
# na ADR 015.

terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

# A credencial é de pessoa (ADC): cota e faturamento das chamadas vão para o
# próprio projeto, e não para um projeto padrão do gcloud.
provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}

locals {
  # APIs que o `infra/` usa. O teste compara esta lista com todo
  # `*.googleapis.com` citado em `infra/`: API nova no código entra aqui antes.
  apis = [
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "billingbudgets.googleapis.com", # orçamento, infra/modules/monitoramento/custo.tf
    "cloudresourcemanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "dataform.googleapis.com",    # ADR 012
    "datalineage.googleapis.com", # ADR 013
    "dataplex.googleapis.com",    # Knowledge Catalog, ADR 014
    "iam.googleapis.com",
    "iamcredentials.googleapis.com", # WIF: token de curta duração da SA de deploy
    "iap.googleapis.com",            # Portal
    "logging.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "serviceusage.googleapis.com",
    "storage.googleapis.com",
    "sts.googleapis.com", # WIF: troca do token do GitHub
  ]

  # Papéis da SA de deploy no projeto: o que o `infra/` declara, tipo de
  # recurso a tipo de recurso (tests/unit/test_bootstrap.py). Nenhum papel
  # básico. A publicação da imagem é concedida no repositório, mais abaixo.
  papeis_deploy = [
    "roles/bigquery.dataOwner",                # datasets e o IAM de cada um
    "roles/cloudscheduler.admin",              # disparos das ingestões
    "roles/dataform.admin",                    # repositório, configs e o IAM do repositório
    "roles/iam.serviceAccountAdmin",           # SAs de ingestão, Dataform e Portal, e o IAM delas
    "roles/iam.serviceAccountUser",            # Cloud Run, Scheduler e Dataform agem como essas SAs
    "roles/iap.admin",                         # quem passa pelo IAP do Portal
    "roles/logging.configWriter",              # métricas de log
    "roles/monitoring.editor",                 # canais, alertas e painel
    "roles/resourcemanager.projectIamAdmin",   # papéis de projeto e log de auditoria
    "roles/run.admin",                         # Jobs, Portal e o IAM de cada um
    "roles/secretmanager.admin",               # secrets vazios e o IAM de cada um
    "roles/serviceusage.serviceUsageConsumer", # agentes de serviço do Dataform e do IAP
    "roles/storage.admin",                     # bucket raw, o IAM dele e o state
  ]

  # Token do GitHub só vale se vier do repositório do projeto; em hml e prod,
  # também só de job que roda no ambiente do GitHub de mesmo nome.
  condicao_repositorio = "assertion.repository == '${var.github_repositorio}'"
  condicao_id          = var.github_repositorio_id == "" ? "" : " && assertion.repository_id == '${var.github_repositorio_id}'"
  condicao_ambiente    = var.restringir_ao_ambiente_github ? " && assertion.sub == 'repo:${var.github_repositorio}:environment:${var.environment}'" : ""
  condicao_wif         = "${local.condicao_repositorio}${local.condicao_id}${local.condicao_ambiente}"
}

# ------------------------------------------------------------------ APIs

resource "google_project_service" "api" {
  for_each = toset(local.apis)

  project = var.project_id
  service = each.value

  # Tirar uma API da lista não a desliga: o que já roda no projeto continua.
  disable_on_destroy = false
}

# ------------------------------------------------------------------ state

# State do `infra/` deste projeto. O deploy passa o nome no init
# (`-backend-config="bucket=..."`, variável TF_STATE_BUCKET no GitHub).
resource "google_storage_bucket" "state" {
  name     = "${var.project_id}-tfstate"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  # Versão antiga do state é o que permite desfazer um apply ruim. Dez bastam;
  # o resto seria armazenamento pago sem uso (E2).
  lifecycle_rule {
    condition {
      num_newer_versions = 10
      with_state         = "ARCHIVED"
    }
    action {
      type = "Delete"
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }

  lifecycle {
    prevent_destroy = true
  }

  depends_on = [google_project_service.api]
}

# ------------------------------------------------------------------ imagens

resource "google_artifact_registry_repository" "imagens" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repositorio_imagens
  format        = "DOCKER"
  description   = "Imagem da CLI alupdata: ingestões e Portal"

  # Custo (E2): o deploy publica uma imagem por commit. Ficam as dez mais
  # recentes, entre as quais está a do último deploy; as demais saem depois
  # de 30 dias.
  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "manter-recentes"
    action = "KEEP"
    most_recent_versions {
      keep_count = 10
    }
  }

  cleanup_policies {
    id     = "apagar-antigas"
    action = "DELETE"
    condition {
      tag_state  = "ANY"
      older_than = "2592000s"
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }

  depends_on = [google_project_service.api]
}

# ------------------------------------------------------------------ WIF

resource "google_iam_workload_identity_pool" "github" {
  project                   = var.project_id
  workload_identity_pool_id = "github"
  display_name              = "GitHub Actions"
  description               = "Workflows do repositório ${var.github_repositorio}"

  depends_on = [google_project_service.api]
}

resource "google_iam_workload_identity_pool_provider" "github" {
  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_provider_id = "alupdata"
  display_name                       = "AlupData"

  attribute_condition = local.condicao_wif
  attribute_mapping = {
    "google.subject"       = "assertion.sub"
    "attribute.repository" = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# ------------------------------------------------------------------ SA de deploy

# Usada só pelos workflows, via WIF. Não existe chave dela em lugar nenhum
# (cláusula 8.5).
resource "google_service_account" "deploy" {
  project      = var.project_id
  account_id   = "alupdata-deploy"
  display_name = "AlupData — deploy"
  description  = "Aplica o infra/ e publica a imagem; usada só pelo GitHub, via WIF"

  depends_on = [google_project_service.api]
}

resource "google_service_account_iam_member" "github_personifica" {
  service_account_id = google_service_account.deploy.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.github.name}/attribute.repository/${var.github_repositorio}"
}

resource "google_project_iam_member" "deploy" {
  for_each = toset(local.papeis_deploy)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.deploy.email}"
}

# Publicar imagem só neste repositório, não em qualquer um do projeto.
resource "google_artifact_registry_repository_iam_member" "deploy_publica" {
  project    = var.project_id
  location   = google_artifact_registry_repository.imagens.location
  repository = google_artifact_registry_repository.imagens.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.deploy.email}"
}
