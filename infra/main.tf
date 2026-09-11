terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }

  # Backend será configurado por ambiente
  # backend "gcs" {
  #   bucket = "alupdata-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------ identidade

# Uma service account para as ingestões. Permissões de dado ficam no recurso
# específico (dataset, bucket, secret e job); só a criação de jobs BigQuery é
# inevitavelmente concedida no projeto.
resource "google_service_account" "ingestao" {
  account_id   = "alupdata-ingestao"
  display_name = "AlupData — ingestão"
  project      = var.project_id
}

locals {
  papeis_ingestao = [
    "roles/bigquery.jobUser",
  ]
}

resource "google_project_iam_member" "ingestao" {
  for_each = toset(local.papeis_ingestao)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.ingestao.email}"
}

resource "google_bigquery_dataset_iam_member" "ingestao_bronze" {
  project    = var.project_id
  dataset_id = module.bigquery.dataset_ids["bronze"]
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestao.email}"
}

# --------------------------------------------------------------------- módulos

module "bigquery" {
  source      = "./modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

module "storage" {
  source                = "./modules/storage"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = google_service_account.ingestao.email
}

module "secrets" {
  source                = "./modules/secrets"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = google_service_account.ingestao.email
}

# Alertas. `emails_alerta` vazio cria as políticas sem destinatário — ver o
# README do módulo: quem recebe é acordo operacional, não configuração.
module "monitoramento" {
  source          = "./modules/monitoramento"
  project_id      = var.project_id
  environment     = var.environment
  emails_alerta   = var.emails_alerta
  billing_account = var.billing_account
}

# Só sobe quando existe imagem publicada — antes disso o agendamento não tem o
# que executar.
module "scheduler" {
  count = var.imagem_ingestao == "" ? 0 : 1

  source                = "./modules/scheduler"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  imagem                = var.imagem_ingestao
  service_account_email = google_service_account.ingestao.email
}
