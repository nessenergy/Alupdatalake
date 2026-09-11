variable "project_id" {
  description = "ID do projeto GCP, criado pela Alup na organização dela (E1)"
  type        = string
}

variable "environment" {
  description = "Ambiente do projeto: dev, hml (homologação) ou prod — ADR 015"
  type        = string
  validation {
    condition     = contains(["dev", "hml", "prod"], var.environment)
    error_message = "Ambiente deve ser 'dev', 'hml' ou 'prod'."
  }
}

variable "region" {
  description = "Região do bucket de state e do Artifact Registry (ADR 011)"
  type        = string
  default     = "us-east1"
}

variable "github_repositorio" {
  description = "Único repositório GitHub cujos workflows podem assumir a SA de deploy"
  type        = string
  default     = "nessenergy/Alupdatalake"
}

variable "github_repositorio_id" {
  description = "ID numérico do repositório no GitHub; preenchido, a condição do WIF também o exige (recomendação do Google contra repositório homônimo)"
  type        = string
  default     = ""
  validation {
    condition     = can(regex("^[0-9]*$", var.github_repositorio_id))
    error_message = "Use só o ID numérico do repositório."
  }
}

variable "restringir_ao_ambiente_github" {
  description = "Exige que o job rode no ambiente do GitHub de mesmo nome (environment:<ambiente>)"
  type        = bool
  default     = true
}

variable "repositorio_imagens" {
  description = "ID do repositório Docker no Artifact Registry"
  type        = string
  default     = "alupdata"
}
