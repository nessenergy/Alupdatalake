variable "project_id" {
  description = "ID do projeto GCP"
  type        = string
}

variable "region" {
  description = "Região GCP (ADR 011) — irreversível depois do primeiro apply"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Ambiente: dev, hml (homologação) ou prod — ADR 015"
  type        = string
  validation {
    condition     = contains(["dev", "hml", "prod"], var.environment)
    error_message = "Ambiente deve ser 'dev', 'hml' ou 'prod'."
  }
}

variable "agendamentos_ativos" {
  description = "Cria os agendamentos: Scheduler das ingestões e workflow diário do Dataform. Em hml, false fora da homologação (E2)"
  type        = bool
  default     = true
}

variable "cadeia_onda3" {
  description = <<-EOT
    Conectores cuja carga precisa terminar antes de o Dataform rodar — as
    fontes internas da Onda 3 (ADR 017). Vazia, nenhum recurso de orquestração
    é criado: o fluxo nasce com a primeira fonte interna, não antes.
  EOT
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for conector in var.cadeia_onda3 : can(regex("^[a-z0-9_]+$", conector))])
    error_message = "Use o rótulo do conector em snake_case, como `fmb_contrato`."
  }
}

variable "conectores_sem_agendamento" {
  description = <<-EOT
    Conectores que não recebem disparo do Cloud Scheduler, em geral porque a
    credencial ainda não chegou. O Cloud Run Job continua existindo e roda à
    mão. Quando a credencial chegar, tire o conector da lista.
  EOT
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for conector in var.conectores_sem_agendamento : can(regex("^[a-z0-9_]+$", conector))])
    error_message = "Use o rótulo do conector em snake_case, como `hubspot_negocios`."
  }
}

variable "imagem_ingestao" {
  description = "Imagem do container com a CLI alupdata; vazio desliga o agendamento"
  type        = string
  default     = ""
  validation {
    condition = var.imagem_ingestao == "" || can(regex(
      "(:[0-9a-f]{40}|@sha256:[0-9a-f]{64})$", var.imagem_ingestao
    ))
    error_message = "Use imagem vazia, tag de SHA completo ou digest sha256."
  }
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

variable "leitura_projeto" {
  description = <<-EOT
    Quem lê o projeto inteiro — configuração, logs, jobs, metadado de segredo —
    sem ler valor de segredo (`roles/viewer`). Para o dado das camadas, use
    também `grupo_operacao`. Só group:<e-mail> ou domain:<domínio> (R01).
  EOT
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for m in var.leitura_projeto : can(regex("^(group|domain):[^\\s]+$", m))])
    error_message = "Use só group:<e-mail> ou domain:<domínio>; acesso individual (user:) não entra."
  }
}

variable "gravacao_segredos" {
  description = <<-EOT
    Quem grava versão nova de secret — o token do Dataform e as credenciais das
    fontes — **sem poder ler** (`roles/secretmanager.secretVersionAdder`). É o
    "acesso de operação depois do bootstrap" que a ADR 015 manda entrar por
    variável. Só group:<e-mail> ou domain:<domínio> (R01); vazio não concede.
  EOT
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for m in var.gravacao_segredos : can(regex("^(group|domain):[^\\s]+$", m))])
    error_message = "Use só group:<e-mail> ou domain:<domínio>; acesso individual (user:) não entra."
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
