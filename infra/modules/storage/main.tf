# Bucket de dado bruto: todo payload é gravado aqui antes do parsing, para que
# um bug de parser seja reprocessável sem bater de novo na fonte.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "service_account_email" { type = string }
variable "dias_retencao_raw" {
  description = "Dias até o dado bruto ir para Nearline; 0 desliga a regra"
  type        = number
  default     = 90
}

resource "google_storage_bucket" "raw" {
  name     = "${var.project_id}-raw"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  dynamic "lifecycle_rule" {
    for_each = var.dias_retencao_raw > 0 ? [1] : []
    content {
      condition {
        age = var.dias_retencao_raw
      }
      action {
        type          = "SetStorageClass"
        storage_class = "NEARLINE"
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

resource "google_storage_bucket_iam_member" "ingestao" {
  for_each = toset([
    "roles/storage.objectCreator",
    "roles/storage.objectViewer",
  ])

  bucket = google_storage_bucket.raw.name
  role   = each.value
  member = "serviceAccount:${var.service_account_email}"
}

# Entrada de arquivos da Alup: planilhas de exemplo, tabelas de de-para, o que
# for dado de negócio que chega por mão humana. Existe para que esse dado não
# viaje por e-mail nem pare no GitHub (regra: nada de dado real no repositório)
# e não saia do projeto da contratante.
#
# Não é o bucket raw: o raw é da ingestão, append-only, e fonte de replay. Misturar
# arquivo enviado à mão ali confundiria as duas coisas.
#
# Quem envia são as pessoas da Alup que já têm `storage.admin` no projeto, por
# concessão dela; quem lê é quem tem `roles/viewer` (`leitura_projeto`). Nenhuma
# concessão nova de IAM aqui. Versionado, para que um arquivo substituído não se
# perca; sem regra de exclusão, porque é insumo, não cache.
resource "google_storage_bucket" "entrada" {
  name     = "${var.project_id}-entrada"
  project  = var.project_id
  location = var.region

  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# Uma pasta por pedido, cada uma com a instrução do que colocar nela. Pasta
# vazia não existe no Cloud Storage; o arquivo de instrução é o que a faz
# aparecer no console para quem vai enviar.
locals {
  pastas_de_entrada = {
    planilhas = "Exemplos reais das planilhas da proposta (G3, issue #142): um exemplo preenchido de cada planilha, no formato em que é usada hoje (XLSX ou CSV)."
    usinas    = "De-para de usinas (issue #141): uma tabela com duas colunas, sigla interna da Alup e CEG (código da usina na ANEEL)."
  }
}

resource "google_storage_bucket_object" "instrucao" {
  for_each = local.pastas_de_entrada

  bucket       = google_storage_bucket.entrada.name
  name         = "${each.key}/LEIA-ME.txt"
  content_type = "text/plain; charset=utf-8"
  content      = "${each.value}\n\nNão envie credenciais por aqui: elas vão só para o Secret Manager.\n"
}

output "bucket_entrada" {
  description = "Bucket onde a Alup envia arquivos com dado de negócio"
  value       = google_storage_bucket.entrada.name
}

output "bucket_raw" {
  description = "Nome do bucket de dado bruto"
  value       = google_storage_bucket.raw.name
}
