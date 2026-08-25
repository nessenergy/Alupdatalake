# Datasets da arquitetura Medallion. Um por camada, no mesmo projeto.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }

locals {
  camadas = {
    bronze = "Dado bruto, append-only, fiel à origem"
    silver = "Dado higienizado, tipado, deduplicado, com dimensões comuns"
    gold   = "Regras de negócio e KPIs consolidados"
  }
}

resource "google_bigquery_dataset" "camada" {
  for_each = local.camadas

  dataset_id  = each.key
  project     = var.project_id
  location    = var.region
  description = each.value

  # Em dev o dataset pode ser destruído junto com as tabelas; em prod, não.
  delete_contents_on_destroy = var.environment == "dev"

  labels = {
    projeto  = "alupdata"
    camada   = each.key
    ambiente = var.environment
  }
}

output "dataset_ids" {
  description = "Ids dos datasets por camada"
  value       = { for k, v in google_bigquery_dataset.camada : k => v.dataset_id }
}
