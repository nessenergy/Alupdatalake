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

# Acesso de pessoas (R01 do RIPD). Os grupos são da Alup; vazio não concede nada.

variable "grupo_consumidores" {
  description = "E-mail do grupo Google da Alup que lê a Gold; vazio não concede nada"
  type        = string
  default     = ""
  validation {
    condition     = var.grupo_consumidores == "" || can(regex("^[^@:\\s]+@[^@:\\s]+$", var.grupo_consumidores))
    error_message = "Informe só o e-mail do grupo, sem o prefixo group:."
  }
}

variable "grupo_operacao" {
  description = "E-mail do grupo Google da Alup que lê Bronze, Silver e Gold; vazio não concede nada"
  type        = string
  default     = ""
  validation {
    condition     = var.grupo_operacao == "" || can(regex("^[^@:\\s]+@[^@:\\s]+$", var.grupo_operacao))
    error_message = "Informe só o e-mail do grupo, sem o prefixo group:."
  }
}

variable "portal_acesso" {
  description = "Quem passa pelo IAP do Portal: group:<e-mail> ou domain:<domínio> da Alup; vazio não libera ninguém"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for m in var.portal_acesso : can(regex("^(group|domain):[^\\s]+$", m))])
    error_message = "Use só group:<e-mail> ou domain:<domínio>; acesso individual (user:) não entra."
  }
}
