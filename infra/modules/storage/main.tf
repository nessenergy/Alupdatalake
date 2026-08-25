# Bucket de dado bruto: todo payload é gravado aqui antes do parsing, para que
# um bug de parser seja reprocessável sem bater de novo na fonte.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
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

output "bucket_raw" {
  description = "Nome do bucket de dado bruto"
  value       = google_storage_bucket.raw.name
}
