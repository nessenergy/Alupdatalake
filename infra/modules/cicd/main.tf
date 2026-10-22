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

# PR de quem não é dono só roda depois de um comentário de aprovação (o repositório é privado, mas a regra vale se mudar).
resource "google_cloudbuild_trigger" "pr" {
  project         = var.project_id
  name            = "alupdata-ci-pr"
  description     = "CI de todo PR para a main (ADR 030)"
  filename        = "cloudbuild/ci.yaml"
  service_account = google_service_account.ci.id

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
