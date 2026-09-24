# Knowledge Catalog — lake, zonas e ativos (ADR 014, item 4.3 do plano).
#
# O que o contrato chama de catálogo é, no produto, um **lake** com **zonas** e
# **ativos**: o lake representa o AlupData, cada zona representa uma camada da
# arquitetura Medallion e cada ativo aponta para um dataset ou bucket que já
# existe. Nada disso copia dado — é metadado sobre o que o `infra/` já declara.
#
# **Descoberta desligada, de propósito.** O Dataplex cobra por unidade de
# processamento quando varre ativo para inferir esquema e partição, e o teto da
# E2 é de US$ 20/mês até novembro. O esquema das nossas tabelas vem do Dataform
# (ADR 012), que é fonte melhor que inferência: ligar descoberta pagaria para
# adivinhar o que já está declarado. Quando houver motivo, é uma variável.
#
# Fica de fora desta entrega, e está na issue #36: *aspect types* — os "Tag
# Templates" do contrato — e o glossário de negócio a partir de
# `docs/glossario.md`. Os dois descrevem **conteúdo** do catálogo, e conteúdo
# antes da primeira carga seria descrição de tabela vazia.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }

variable "datasets_por_camada" {
  description = "Dataset de cada camada Medallion, na ordem em que o dado anda"
  type        = map(string)
}

variable "dataset_qualidade" {
  description = "Dataset das assertions do Dataform; entra na zona da Gold"
  type        = string
}

variable "bucket_raw" {
  description = "Bucket do dado bruto; é o ativo cru da zona Bronze"
  type        = string
}

variable "descoberta_ativa" {
  description = "Liga a varredura do Dataplex nos ativos. Custa por DPU (E2)"
  type        = bool
  default     = false
}

locals {
  # A zona Bronze é crua: guarda o que chegou como chegou, e recebe também o
  # bucket. Silver e Gold são curadas — dado com esquema e regra aplicada.
  zonas = {
    bronze = { tipo = "RAW", rotulo = "Bronze — o que chegou da origem, sem transformação" }
    silver = { tipo = "CURATED", rotulo = "Silver — deduplicada, com dimensões comuns" }
    gold   = { tipo = "CURATED", rotulo = "Gold — responde pergunta de negócio" }
  }
}

resource "google_dataplex_lake" "alupdata" {
  name         = "alupdata"
  project      = var.project_id
  location     = var.region
  display_name = "AlupData ${var.environment}"
  description  = "Lake do AlupData: Bronze, Silver e Gold, mais o dado bruto no GCS"

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

resource "google_dataplex_zone" "camada" {
  for_each = local.zonas

  name         = each.key
  project      = var.project_id
  location     = var.region
  lake         = google_dataplex_lake.alupdata.name
  type         = each.value.tipo
  display_name = title(each.key)
  description  = each.value.rotulo

  discovery_spec {
    enabled = var.descoberta_ativa
  }

  resource_spec {
    # Os datasets e o bucket vivem no mesmo projeto do lake.
    location_type = "SINGLE_REGION"
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# Um ativo por dataset. `qualidade` entra na Gold porque é onde as assertions
# do Dataform materializam o resultado — é dado sobre o dado servido.
resource "google_dataplex_asset" "dataset" {
  for_each = merge(
    { for camada, dataset in var.datasets_por_camada : camada => { zona = camada, dataset = dataset } },
    { qualidade = { zona = "gold", dataset = var.dataset_qualidade } },
  )

  name          = replace(each.key, "_", "-")
  project       = var.project_id
  location      = var.region
  lake          = google_dataplex_lake.alupdata.name
  dataplex_zone = google_dataplex_zone.camada[each.value.zona].name
  display_name  = each.value.dataset

  discovery_spec {
    enabled = var.descoberta_ativa
  }

  resource_spec {
    name = "projects/${var.project_id}/datasets/${each.value.dataset}"
    type = "BIGQUERY_DATASET"
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

resource "google_dataplex_asset" "raw" {
  name          = "raw"
  project       = var.project_id
  location      = var.region
  lake          = google_dataplex_lake.alupdata.name
  dataplex_zone = google_dataplex_zone.camada["bronze"].name
  display_name  = var.bucket_raw

  discovery_spec {
    enabled = var.descoberta_ativa
  }

  resource_spec {
    name = "projects/${var.project_id}/buckets/${var.bucket_raw}"
    type = "STORAGE_BUCKET"
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# O agente do Dataplex precisa alcançar o que o ativo aponta, ou o ativo nasce
# em estado de erro. `dataplex.serviceAgent` é o papel que o Google publica
# para isso; no projeto ele é suficiente, porque lake e ativos vivem aqui.
resource "google_project_service_identity" "dataplex" {
  provider = google-beta

  project = var.project_id
  service = "dataplex.googleapis.com"
}

resource "google_project_iam_member" "agente" {
  project = var.project_id
  role    = "roles/dataplex.serviceAgent"
  member  = "serviceAccount:${google_project_service_identity.dataplex.email}"
}

output "lake" {
  description = "Nome do lake do Knowledge Catalog"
  value       = google_dataplex_lake.alupdata.name
}

output "zonas" {
  description = "Zonas criadas, uma por camada"
  value       = [for zona in google_dataplex_zone.camada : zona.name]
}
