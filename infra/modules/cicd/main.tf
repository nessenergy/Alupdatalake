# CI no Cloud Build (ADR 030, fase 1).
#
# Os gatilhos rodam `cloudbuild/ci.yaml` como uma conta de serviço própria, que só escreve log:
# o CI lê o repositório pela conexão do GitHub e não toca em dado, segredo nem deploy.
#
# O repositório precisa estar conectado ao projeto antes (passo humano de dono da organização:
# aplicativo do Cloud Build no GitHub). Sem isso, a criação do gatilho falha.

variable "project_id" { type = string }
variable "repositorio_dono" { type = string }
variable "repositorio_nome" { type = string }

# Operações sob demanda (ADR 030): gatilhos manuais que rodam como a conta de deploy.
variable "deploy_service_account_id" {
  description = "id completo da conta de deploy: projects/<projeto>/serviceAccounts/<e-mail>"
  type        = string
  validation {
    condition     = can(regex("^projects/[^/]+/serviceAccounts/.+$", var.deploy_service_account_id))
    error_message = "Informe projects/<projeto>/serviceAccounts/<e-mail>; deploy_service_account vazio não serve."
  }
}
variable "regiao" { type = string }

# Deploy no Cloud Build (ADR 030): um gatilho por ambiente, criado pela chamada do módulo em cada projeto.
variable "ambiente" {
  description = "Ambiente do deploy: dev, hml ou prod"
  type        = string
  validation {
    condition     = contains(["dev", "hml", "prod"], var.ambiente)
    error_message = "Ambiente deve ser 'dev', 'hml' ou 'prod'."
  }
}
variable "dataform_token_versao" {
  description = "Versão do secret do token do Dataform (alupdata-dataform-git-token)"
  type        = string
  default     = "1"
}

# Checagem de atribuição no Cloud Build: o passo busca-main lê a main do repositório privado com o token de um
# GitHub App (decisão D1). Vazio, o gatilho de PR segue com `cloudbuild/ci.yaml`, sem a checagem e sem segredo.
variable "github_app_ci_client_id" {
  description = "client_id do GitHub App de leitura do CI; vazio mantém o PR sem ci-atribuicao"
  type        = string
  default     = ""
}

resource "google_service_account" "ci" {
  project      = var.project_id
  account_id   = "alupdata-ci"
  display_name = "CI do AlupData no Cloud Build"
}

# Só escreve log. Nenhum papel de dado, de segredo ou de deploy.
resource "google_project_iam_member" "ci_log" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.ci.email}"
}

# Chave privada do GitHub App de leitura do CI. Contêiner vazio: o valor entra fora do Terraform (regra 2):
#   gcloud secrets versions add alupdata-github-ci-app-key --data-file=chave.pem
# Criado sempre; só o gatilho de PR o usa, e só com github_app_ci_client_id preenchido.
resource "google_secret_manager_secret" "ci_app_key" {
  secret_id = "alupdata-github-ci-app-key"
  project   = var.project_id

  # Réplica só na região do ambiente (ADR 011), como os outros segredos.
  replication {
    user_managed {
      replicas {
        location = var.regiao
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.ambiente
  }
}

# Único segredo que a conta do CI lê.
resource "google_secret_manager_secret_iam_member" "ci_le_chave_do_app" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.ci_app_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.ci.email}"
}

# PR de quem não é dono só roda depois de um comentário de aprovação (o repositório é privado, mas a regra vale se mudar).
resource "google_cloudbuild_trigger" "pr" {
  project         = var.project_id
  name            = "alupdata-ci-pr"
  description     = "CI de todo PR para a main (ADR 030)"
  filename        = var.github_app_ci_client_id == "" ? "cloudbuild/ci.yaml" : "cloudbuild/ci-com-atribuicao.yaml"
  service_account = google_service_account.ci.id

  # Sem client id: os alvos de hoje, sem ci-atribuicao. Com ele: o ci completo e o passo busca-main.
  substitutions = var.github_app_ci_client_id == "" ? {
    _ALVOS = "ci-lint ci-testes ci-sast ci-segredos ci-terraform ci-dataform ci-sca"
    } : {
    _ALVOS         = "ci"
    _CLIENT_ID_APP = var.github_app_ci_client_id
  }

  github {
    owner = var.repositorio_dono
    name  = var.repositorio_nome

    pull_request {
      branch          = "^main$"
      comment_control = "COMMENTS_ENABLED_FOR_EXTERNAL_CONTRIBUTORS_ONLY"
    }
  }

  depends_on = [google_project_iam_member.ci_log]
}

# Push na main: as mesmas etapas, menos a checagem de atribuição, que compara com o ramo do PR.
resource "google_cloudbuild_trigger" "main" {
  project         = var.project_id
  name            = "alupdata-ci-main"
  description     = "CI depois do merge na main (ADR 030)"
  filename        = "cloudbuild/ci.yaml"
  service_account = google_service_account.ci.id

  substitutions = {
    _ALVOS = "ci-lint ci-testes ci-sast ci-segredos ci-terraform ci-dataform ci-sca"
  }

  github {
    owner = var.repositorio_dono
    name  = var.repositorio_nome

    push {
      branch = "^main$"
    }
  }

  depends_on = [google_project_iam_member.ci_log]
}

# Operações sob demanda: gatilhos manuais (sem bloco github{}, não disparam no push), rodados com
# `gcloud builds triggers run <nome> --branch=main --substitutions=...`. O repositório é o do
# GitHub conectado pelo aplicativo do Cloud Build (1ª geração).
locals {
  repositorio_uri = "https://github.com/${var.repositorio_dono}/${var.repositorio_nome}"
  operacoes = {
    "alupdata-op-executar-ingestao" = { _OPERACAO = "executar-ingestao", _CONECTOR = "", _DE = "", _ATE = "", _URI = "" }
    "alupdata-op-conferir-cargas"   = { _OPERACAO = "conferir-cargas" }
    "alupdata-op-sondar-rede"       = { _OPERACAO = "sondar-rede", _SONDA = "cptec" }
    "alupdata-op-testar-conexao"    = { _OPERACAO = "testar-conexao", _FONTE = "" }
  }
}

resource "google_cloudbuild_trigger" "operacao" {
  for_each        = local.operacoes
  project         = var.project_id
  name            = each.key
  description     = "Operação sob demanda (ADR 030): gcloud builds triggers run ${each.key} --branch=main --substitutions=..."
  service_account = var.deploy_service_account_id
  filename        = "cloudbuild/operar.yaml"
  substitutions   = merge(each.value, { _REGIAO = var.regiao })

  source_to_build {
    uri       = local.repositorio_uri
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = "cloudbuild/operar.yaml"
    uri       = local.repositorio_uri
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }
}

# Deploy (ADR 030): gatilho manual, como a conta de deploy, com o comportamento do workflow deploy.yml.
# `_MODULO=infra` exige `_IMAGEM_SHA` (SHA completo de uma imagem já publicada).
resource "google_cloudbuild_trigger" "deploy" {
  project         = var.project_id
  name            = "alupdata-deploy"
  description     = "Deploy de ${var.ambiente} (ADR 030): gcloud builds triggers run alupdata-deploy --branch=main --substitutions=_MODULO=all"
  service_account = var.deploy_service_account_id
  filename        = "cloudbuild/deploy.yaml"

  substitutions = {
    _AMBIENTE              = var.ambiente
    _MODULO                = "all"
    _IMAGEM_SHA            = ""
    _IMAGEM_BASE           = "${var.regiao}-docker.pkg.dev/${var.project_id}/alupdata/cli"
    _TF_ESTADO             = "${var.project_id}-tfstate"
    _REGIAO                = var.regiao
    _CONTA_DEPLOY          = element(split("/", var.deploy_service_account_id), 3)
    _DATAFORM_TOKEN_VERSAO = var.dataform_token_versao
  }

  source_to_build {
    uri       = local.repositorio_uri
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }
  git_file_source {
    path      = "cloudbuild/deploy.yaml"
    uri       = local.repositorio_uri
    revision  = "refs/heads/main"
    repo_type = "GITHUB"
  }
}
