# Cria os secrets vazios das fontes que dependem de credencial da Alup.
# O VALOR nunca vem do Terraform — é adicionado fora do versionamento:
#   gcloud secrets versions add alupdata-ccee-api-token --data-file=-
# Enquanto a Alup não entrega o token (Ondas 2 e 3), o secret existe sem versão.

variable "project_id" { type = string }
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

  replication {
    auto {}
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

output "secret_ids" {
  description = "Ids dos secrets criados"
  value       = [for s in google_secret_manager_secret.fonte : s.secret_id]
}
