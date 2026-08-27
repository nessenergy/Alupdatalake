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
  }
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
      }
    }
  }

  labels = {
    projeto  = "alupdata"
    ambiente = var.environment
  }
}

resource "google_cloud_scheduler_job" "ingestao" {
  for_each = var.conectores

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

output "jobs" {
  description = "Nomes dos Cloud Run Jobs de ingestão"
  value       = [for j in google_cloud_run_v2_job.ingestao : j.name]
}
