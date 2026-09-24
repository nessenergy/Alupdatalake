# Portal MVP (ADR 005) no Cloud Run, atrás do IAP (R01 do RIPD).
#
# O IAP fica no próprio serviço, sem load balancer (GA no Cloud Run desde
# 13/03/2026). Na série 6.x do provider, fixada em infra/main.tf, o atributo
# `iap_enabled` só existe no `google-beta`. O Portal ainda recusa requisição
# sem o cabeçalho de identidade do IAP (src/portal/app.py): IAP desligado por
# engano vira 403, não vazamento.
#
# Pré-requisito fora do Terraform, como as demais APIs do projeto:
# iap.googleapis.com habilitada (docs/runbook/primeiro-deploy.md).

terraform {
  required_providers {
    google      = { source = "hashicorp/google" }
    google-beta = { source = "hashicorp/google-beta" }
  }
}

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "imagem" {
  description = "Imagem da CLI alupdata; o Portal roda na mesma imagem, com gunicorn"
  type        = string
}
variable "datasets" {
  description = "Datasets que o Portal lê: as três camadas"
  type        = list(string)
}
variable "acesso" {
  description = "Membros IAM (group: ou domain:) autorizados no IAP; vazio não libera ninguém"
  type        = list(string)
  default     = []
}

# Agente de serviço do IAP: é ele quem invoca o serviço depois de autenticar a
# pessoa. Vem de recurso, como o do Dataform, e não de nome montado à mão.
resource "google_project_service_identity" "iap" {
  provider = google-beta
  project  = var.project_id
  service  = "iap.googleapis.com"
}

# ------------------------------------------------------------------ identidade

# SA própria, só de leitura. Publicado com `gcloud run deploy`, o Portal rodava
# com a SA padrão do Compute Engine.
resource "google_service_account" "portal" {
  account_id   = "alupdata-portal"
  display_name = "AlupData — Portal"
  project      = var.project_id
}

# As três camadas: as views da Gold leem Silver e Bronze e não são views
# autorizadas, e `/lake` lê `bronze._execucoes` diretamente.
resource "google_bigquery_dataset_iam_member" "portal" {
  for_each = toset(var.datasets)

  project    = var.project_id
  dataset_id = each.value
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.portal.email}"
}

# Rodar consulta, e ler o metadado de que `gold.custo_consultas` depende
# (JOBS_BY_PROJECT e TABLE_STORAGE), como a SA do Dataform. Metadado, nunca dado.
resource "google_project_iam_member" "portal" {
  for_each = toset([
    "roles/bigquery.jobUser",
    "roles/bigquery.resourceViewer",
    "roles/bigquery.metadataViewer",
  ])

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.portal.email}"
}

# ------------------------------------------------------------------ serviço

resource "google_cloud_run_v2_service" "portal" {
  provider = google-beta

  name     = "alupdata-portal"
  project  = var.project_id
  location = var.region

  # O IAP protege todas as entradas, inclusive a URL run.app.
  ingress     = "INGRESS_TRAFFIC_ALL"
  iap_enabled = true

  # O Portal não guarda estado: lê BigQuery e devolve HTML. Recriá-lo custa um
  # deploy, não um dado. Com a proteção ligada — o padrão do provider — o apply
  # trava no dia em que o serviço precisa ser substituído, que foi o que
  # aconteceu em 23/09, quando a revisão anterior ficou de pé mas sem subir:
  # "cannot destroy service without setting deletion_protection=false".
  # A proteção que importa está no dado, e essa fica nos datasets e no bucket.
  deletion_protection = false

  template {
    service_account = google_service_account.portal.email

    containers {
      image   = var.imagem
      command = ["gunicorn"]
      args    = ["--bind=:8080", "--workers=2", "src.portal.app:app"]

      env {
        name  = "PORTAL_PROVEDOR"
        value = "bigquery"
      }
      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }

      # Sonda que não toca o BigQuery: sonda que consulta banco derruba o
      # serviço junto com o banco.
      startup_probe {
        http_get {
          path = "/saude"
        }
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# Só o agente do IAP invoca o serviço. Pessoa nenhuma recebe run.invoker.
resource "google_cloud_run_v2_service_iam_member" "iap_invoca" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.portal.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_project_service_identity.iap.email}"
}

# Quem passa pelo IAP: grupo ou domínio da Alup, vindos de variável.
resource "google_iap_web_cloud_run_service_iam_member" "acesso" {
  for_each = toset(var.acesso)

  project                = var.project_id
  location               = var.region
  cloud_run_service_name = google_cloud_run_v2_service.portal.name
  role                   = "roles/iap.httpsResourceAccessor"
  member                 = each.value
}

output "url" {
  description = "URL do Portal (run.app), atrás do IAP"
  value       = google_cloud_run_v2_service.portal.uri
}
