# Orquestração da Onda 3 (item 3.5, ADR 017).
#
# As Ondas 1 e 2 são independentes: cada conector tem seu Cloud Run Job e seu
# disparo no Cloud Scheduler, e a ordem entre eles não importa. A Onda 3 traz o
# que a ADR 004 chamou de gatilho: **fonte interna alimentando view Gold que
# cruza fontes**. Isso é sequência — ingerir tudo, depois transformar — e é o
# que este módulo expressa, em Cloud Workflows e não em Composer, porque o
# Composer cobra por ambiente ligado 24×7 e o teto da E2 não comporta.
#
# O fluxo é um só e tem três partes: executar as ingestões da cadeia em
# paralelo e esperar todas; compilar a release do Dataform; invocar a execução
# e esperar o estado terminal. Falha em qualquer parte para o fluxo e aparece
# no alerta do Dataform, que já existe.
#
# **Nada é criado enquanto a cadeia estiver vazia.** A lista sai das fontes
# internas, que dependem de VPN e credencial (A7): até elas existirem, este
# módulo é um plano sem recurso — o que não é o mesmo que código sem uso, e é
# a diferença entre entregar o mecanismo e provisionar custo pelo que não roda.

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }

variable "cadeia" {
  description = <<-EOT
    Rótulos dos conectores cuja carga precisa terminar antes do Dataform rodar
    — as fontes internas da Onda 3. Vazia, o módulo não cria recurso algum.
  EOT
  type        = list(string)
  default     = []
}

variable "cron" {
  description = "Quando a cadeia inteira roda, no fuso de Brasília"
  type        = string
  default     = "0 5 * * *"
}

variable "agendar" {
  description = "Falso deixa o fluxo existente e disparável à mão, sem Scheduler"
  type        = bool
  default     = true
}

variable "repositorio_dataform" {
  description = "Nome completo do repositório Dataform; vazio desliga o módulo"
  type        = string
  default     = ""
}

variable "service_account_dataform" {
  description = "Identidade com que o Dataform executa as transformações"
  type        = string
  default     = ""
}

variable "timeout_ingestao_segundos" {
  description = "Teto de espera por ingestão da cadeia; o Cloud Run Job tem 1800s"
  type        = number
  default     = 1800
}

locals {
  # Sem cadeia ou sem repositório não há o que orquestrar. A segunda condição
  # importa no primeiro deploy: o repositório do Dataform só existe depois de
  # o token do GitHub ser gravado no secret.
  ativo = length(var.cadeia) > 0 && var.repositorio_dataform != "" ? 1 : 0

  jobs = [for conector in var.cadeia : "ingestao-${replace(conector, "_", "-")}"]
}

# Identidade própria, com o mínimo: invocar os jobs da cadeia, mandar o
# Dataform executar e usar a identidade dele na invocação. Não lê dado.
resource "google_service_account" "orquestracao" {
  count = local.ativo

  account_id   = "alupdata-orquestracao"
  project      = var.project_id
  display_name = "AlupData ${var.environment} — orquestração da Onda 3"
}

resource "google_cloud_run_v2_job_iam_member" "executa" {
  for_each = local.ativo == 1 ? toset(local.jobs) : toset([])

  project  = var.project_id
  location = var.region
  name     = each.value
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.orquestracao[0].email}"
}

resource "google_dataform_repository_iam_member" "invoca" {
  count = local.ativo

  provider   = google-beta
  project    = var.project_id
  region     = var.region
  repository = reverse(split("/", var.repositorio_dataform))[0]
  role       = "roles/dataform.editor"
  member     = "serviceAccount:${google_service_account.orquestracao[0].email}"
}

# Invocar o Dataform passando `invocationConfig.serviceAccount` exige poder
# agir como aquela identidade — é a mesma regra que vale para a SA de deploy.
resource "google_service_account_iam_member" "usa_dataform" {
  count = local.ativo

  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.service_account_dataform}"
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.orquestracao[0].email}"
}

resource "google_workflows_workflow" "onda3" {
  count = local.ativo

  name            = "alupdata-onda3"
  project         = var.project_id
  region          = var.region
  description     = "Ingestões internas da Onda 3 e, depois delas, o Dataform"
  service_account = google_service_account.orquestracao[0].id

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }

  source_contents = templatefile("${path.module}/onda3.yaml.tftpl", {
    projeto                  = var.project_id
    regiao                   = var.region
    jobs                     = local.jobs
    repositorio              = var.repositorio_dataform
    service_account_dataform = var.service_account_dataform
    timeout_ingestao         = var.timeout_ingestao_segundos
  })
}

resource "google_cloud_scheduler_job" "onda3" {
  count = local.ativo == 1 && var.agendar ? 1 : 0

  name     = "alupdata-onda3"
  project  = var.project_id
  region   = var.region
  schedule = var.cron
  # Mesmo fuso das ingestões: o cron do Scheduler roda no fuso declarado aqui.
  time_zone = "America/Sao_Paulo"

  retry_config {
    # Uma repetição só: a cadeia inteira reexecutando sozinha custa caro e
    # repete ingestão que já pode ter funcionado.
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri = join("", [
      "https://workflowexecutions.googleapis.com/v1/",
      google_workflows_workflow.onda3[0].id,
      "/executions",
    ])

    oauth_token {
      service_account_email = google_service_account.orquestracao[0].email
    }
  }
}

resource "google_project_iam_member" "dispara" {
  count = local.ativo

  project = var.project_id
  role    = "roles/workflows.invoker"
  member  = "serviceAccount:${google_service_account.orquestracao[0].email}"
}

output "fluxo" {
  description = "Nome do fluxo de orquestração; nulo enquanto a cadeia estiver vazia"
  value       = one(google_workflows_workflow.onda3[*].name)
}

output "cadeia" {
  description = "Jobs que o fluxo executa antes do Dataform"
  value       = local.jobs
}
