variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP"
  type        = string
  default     = "us-east1"
}

variable "environment" {
  description = "Ambiente: dev ou prod"
  type        = string
  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Ambiente deve ser 'dev' ou 'prod'."
  }
}

variable "imagem_ingestao" {
  description = "Imagem do container com a CLI alupdata; vazio desliga o agendamento"
  type        = string
  default     = ""
}
