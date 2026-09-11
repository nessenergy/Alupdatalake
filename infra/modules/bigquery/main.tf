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

# Destino do billing export (ADR 007, adendo de 10/09). O Terraform cria o
# dataset; ligar o export é passo de console na conta de faturamento da Alup —
# ver docs/runbook/primeiro-deploy.md. Nenhum bloco `access` aqui: ao ligar o
# export, o Cloud Billing se adiciona como OWNER (proprietário) do dataset, e
# um bloco autoritativo apagaria essa concessão no apply seguinte.
resource "google_bigquery_dataset" "faturamento" {
  dataset_id  = "faturamento"
  project     = var.project_id
  location    = var.region
  description = "Billing export da conta de faturamento — traz todos os projetos que ela paga"

  # Histórico de fatura não se recupera: dataset regional não tem carga retroativa.
  delete_contents_on_destroy = false

  labels = {
    projeto  = "alupdata"
    camada   = "faturamento"
    ambiente = var.environment
  }
}

output "dataset_faturamento" {
  description = "Dataset de destino do billing export"
  value       = google_bigquery_dataset.faturamento.dataset_id
}

# Resultado das assertions do Dataform (ADR 012). Separado das camadas: é
# evidência de qualidade, não dado de negócio.
resource "google_bigquery_dataset" "qualidade" {
  dataset_id  = "qualidade"
  project     = var.project_id
  location    = var.region
  description = "Assertions do Dataform — linhas que violaram uma regra de qualidade"

  delete_contents_on_destroy = var.environment == "dev"

  labels = {
    projeto  = "alupdata"
    camada   = "qualidade"
    ambiente = var.environment
  }
}

output "dataset_qualidade" {
  description = "Dataset das assertions do Dataform"
  value       = google_bigquery_dataset.qualidade.dataset_id
}
