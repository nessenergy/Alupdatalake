# Cria os secrets vazios das fontes que dependem de credencial da Alup.
# O VALOR nunca vem do Terraform — é adicionado fora do versionamento:
#   gcloud secrets versions add alupdata-ccee-api-token --data-file=-
# Enquanto a Alup não entrega o token (Ondas 2 e 3), o secret existe sem versão.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "service_account_email" { type = string }
variable "segredos" {
  description = "Nomes no padrão alupdata-<fonte>-<campo>"
  type        = list(string)
  default = [
    "alupdata-ccee-api-token",
    "alupdata-bbce-api-token",
    "alupdata-hubspot-api-token",
    "alupdata-tempook-api-token",
    "alupdata-fmb-dsn",
    "alupdata-portal-alup-dsn",
    "alupdata-comercializacao-dsn",
    "alupdata-rm-dsn",
  ]
}

resource "google_secret_manager_secret_iam_member" "ingestao" {
  for_each = google_secret_manager_secret.fonte

  project   = var.project_id
  secret_id = each.value.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.service_account_email}"
}

resource "google_secret_manager_secret" "fonte" {
  for_each = toset(var.segredos)

  secret_id = each.value
  project   = var.project_id

  # Réplica só na região do ambiente (ADR 011). Replicação automática espalha
  # o secret por várias regiões e exige que a política de localização da
  # organização permita `global`.
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

# Chave privada do GitHub App que sincroniza o quadro de acompanhamento
# (.github/workflows/quadro.yml). Não é credencial de fonte: fica fora de
# `segredos` para que a ingestão não a leia. O valor entra fora do Terraform:
#   gcloud secrets versions add alupdata-github-quadro-app-key --data-file=chave.pem
variable "github_service_account" {
  description = "SA que o GitHub usa via WIF (a do deploy); vazio não concede"
  type        = string
  default     = ""
}

resource "google_secret_manager_secret" "quadro_app_key" {
  secret_id = "alupdata-github-quadro-app-key"
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

resource "google_secret_manager_secret_iam_member" "github_le_chave_quadro" {
  count = var.github_service_account == "" ? 0 : 1

  project   = var.project_id
  secret_id = google_secret_manager_secret.quadro_app_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${var.github_service_account}"
}

output "secret_ids" {
  description = "Ids dos secrets criados"
  value       = [for s in google_secret_manager_secret.fonte : s.secret_id]
}
