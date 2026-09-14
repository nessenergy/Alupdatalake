# Agendamento das ingestões (componente 06).
#
# Cada conector vira um Cloud Run Job que executa a mesma CLI do repositório, e
# um job do Cloud Scheduler que o dispara. Composer entra na Onda 3, quando
# houver dependência entre pipelines (ADR 004).

variable "project_id" { type = string }
variable "region" { type = string }
variable "environment" { type = string }
variable "imagem" {
  description = "Imagem do container com a CLI alupdata (Artifact Registry)"
  type        = string
}
variable "service_account_email" {
  description = "Service account que executa as ingestões"
  type        = string
}
variable "conectores" {
  description = "Ingestões agendadas, por rótulo do conector"
  type = map(object({
    cron         = string
    ultimos_dias = number
  }))
  default = {
    bcb_cambio_ptax = {
      cron         = "0 9 * * *" # após a publicação do boletim de fechamento
      ultimos_dias = 3           # cobre feriado e republicação
    }
    ons_carga = {
      cron         = "0 8 * * *" # o ONS publica o dia anterior de manhã
      ultimos_dias = 30          # janela larga: o ONS revisa dado publicado
    }
    aneel_siga = {
      cron         = "0 7 * * 1" # cadastro muda devagar: semanal, segunda
      ultimos_dias = 1           # cadastro completo; a janela não se aplica
    }
    ibge_ipca = {
      cron         = "0 10 12 * *" # IPCA sai por volta do dia 10
      ultimos_dias = 90            # janela larga: o IBGE revisa série publicada
    }
    hubspot_negocios = {
      cron         = "0 */6 * * *" # CRM muda ao longo do dia; 4x por dia basta
      ultimos_dias = 2             # cobre execução perdida sem varrer o funil todo
    }
    ccee_pld = {
      # O PLD sai por fechamento mensal, com defasagem: em 01/09/2026 o arquivo
      # ia até julho. Rodar diariamente só varreria o mesmo CSV sem dado novo.
      cron         = "0 9 5 * *" # dia 5, depois do fechamento do mês anterior
      ultimos_dias = 120         # cobre a defasagem de publicação e a recontabilização (ADR 016)
    }
    tempook_boletins = {
      # Boletim diário; a janela curta é deliberada, porque cada dia é uma
      # requisição própria (ADR 019) — janela larga multiplica chamadas à
      # origem sem trazer dado novo. Dia sem boletim vira aviso, não falha.
      cron         = "0 11 * * *" # depois da publicação do boletim do dia
      ultimos_dias = 5            # cobre execução perdida e publicação atrasada
    }
  }
}

variable "agendar" {
  description = "Cria os disparos do Cloud Scheduler; false deixa só os Cloud Run Jobs, para execução manual"
  type        = bool
  default     = true
}

resource "google_cloud_run_v2_job" "ingestao" {
  for_each = var.conectores

  name     = "ingestao-${replace(each.key, "_", "-")}"
  project  = var.project_id
  location = var.region

  template {
    template {
      service_account = var.service_account_email
      max_retries     = 2
      timeout         = "1800s"

      containers {
        image = var.imagem
        args  = ["ingerir", each.key, "--ultimos-dias", tostring(each.value.ultimos_dias)]

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        # A regiao decide onde a linhagem e gravada e qual INFORMATION_SCHEMA
        # e lido; precisa vir do Terraform, nao do default do config (ADR 013).
        env {
          name  = "GCP_REGION"
          value = var.region
        }
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

# Sem `agendar`, nenhum disparo existe: o Scheduler cobra por job existente,
# pausado ou não. O Cloud Run Job acima continua disponível para execução manual.
resource "google_cloud_scheduler_job" "ingestao" {
  for_each = var.agendar ? var.conectores : {}

  name     = "ingestao-${replace(each.key, "_", "-")}"
  project  = var.project_id
  region   = var.region
  schedule = each.value.cron
  # Horário de Brasília: o cron do Scheduler roda no fuso declarado aqui.
  time_zone = "America/Sao_Paulo"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri = join("", [
      "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/",
      "${var.project_id}/jobs/${google_cloud_run_v2_job.ingestao[each.key].name}:run",
    ])

    oauth_token {
      service_account_email = var.service_account_email
    }
  }
}

resource "google_cloud_run_v2_job_iam_member" "scheduler" {
  for_each = google_cloud_run_v2_job.ingestao

  project  = var.project_id
  location = var.region
  name     = each.value.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.service_account_email}"
}

output "jobs" {
  description = "Nomes dos Cloud Run Jobs de ingestão"
  value       = [for j in google_cloud_run_v2_job.ingestao : j.name]
}
