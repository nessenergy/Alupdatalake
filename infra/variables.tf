variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP"
  type        = string
  default     = "southamerica-east1"
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

variable "emails_alerta" {
  description = "Destinatários dos alertas. Vazio cria as políticas sem notificar ninguém — ver modules/monitoramento/README.md"
  type        = list(string)
  default     = []
}

variable "billing_account" {
  description = "ID da conta de faturamento, para o alerta de custo. Vazio desliga — ver issue #55"
  type        = string
  default     = ""
}
