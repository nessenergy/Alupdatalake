variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP (ADR 011) — irreversível depois do primeiro apply"
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

variable "dataform_git_token_versao" {
  description = "Versão do secret alupdata-dataform-git-token; vazio não cria o repositório Dataform"
  type        = string
  default     = ""
}

variable "deploy_service_account" {
  description = "SA do workflow Deploy GCP, que dispara o Dataform após o apply"
  type        = string
  default     = ""
}
