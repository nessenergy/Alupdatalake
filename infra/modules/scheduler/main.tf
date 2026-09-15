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
    # `_ingerir()` do runner (`src/core/conector.py`) materializa a janela
    # inteira em memória antes de gravar o raw e validar — o default (512Mi)
    # basta para toda fonte mensal leve. Só o conector que lê um volume
    # grande por execução (hoje só `ccee_geracao_usina`) precisa de mais.
    memoria = optional(string, "512Mi")
    cpu     = optional(string, "1")
  }))
  default = {
    bcb_cambio_ptax = {
      cron         = "0 9 * * *" # após a publicação do boletim de fechamento
      ultimos_dias = 3           # cobre feriado e republicação
    }
    bcb_juros = {
      # Selic e CDI do dia útil anterior. Meia hora depois do PTAX para não
      # disputar a mesma janela de execução com ele.
      cron         = "30 9 * * *"
      ultimos_dias = 5 # cobre feriado prolongado e execução perdida
    }
    ons_carga = {
      cron         = "0 8 * * *" # o ONS publica o dia anterior de manhã
      ultimos_dias = 30          # janela larga: o ONS revisa dado publicado
    }
    aneel_siga = {
      cron         = "0 7 * * 1" # cadastro muda devagar: semanal, segunda
      ultimos_dias = 1           # cadastro completo; a janela não se aplica
    }
    ons_capacidade = {
      # Cadastro de unidades geradoras; muda devagar, como o aneel_siga.
      # Segunda de manhã, uma hora depois do SIGA, para não disputar a mesma
      # janela de execução.
      cron         = "0 8 * * 1"
      ultimos_dias = 1 # cadastro completo; a janela não se aplica
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
    ccee_perfil = {
      # Cadastro muda devagar e o retrato tem ~60 mil linhas: semanal basta, e
      # o Bronze acumula um retrato por semana em vez de um por dia.
      cron         = "0 7 * * 2" # terça, depois do semanal da ANEEL
      ultimos_dias = 1           # cadastro completo; a janela não se aplica
    }
    ccee_agente = {
      # Retrato mensal; a CCEE republica meses fechados (ADR 016). Dia 6, depois
      # do PLD (dia 5), para não disputar a mesma janela.
      cron         = "0 10 6 * *"
      ultimos_dias = 120 # cobre a recontabilização e a defasagem de publicação
    }
    ccee_exposicao_financeira = {
      cron         = "0 10 6 * *" # publicação mensal; dia 6, depois do PLD
      ultimos_dias = 120          # recontabilização (ADR 016)
    }
    ccee_contabilizacao_perfil = {
      # 43 MB por ano, ~47 mil perfis por mês. A janela de 120 dias lê o ano
      # corrente inteiro (o arquivo é anual), o que é o custo de ver a
      # recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    ccee_geracao_usina = {
      # Um recurso gzip de 61 MB por mês, ~3 milhões de linhas. Roda de
      # madrugada, um dia depois das entidades mensais leves, com janela que
      # alcança o mês fechado e o anterior (recontabilização, ADR 016).
      # `ultimos_dias` 40, não 70: o runner materializa a janela inteira em
      # memória (`src/core/conector.py`), e 70 dias abre 3-4 recursos mensais
      # de uma vez (~9-12 M linhas, ~4 GB de dicts) — risco de OOM na primeira
      # execução real. 40 dias cobre um mês fechado inteiro mais folga, sem
      # abrir um quarto mês. `memoria`/`cpu` abaixo é a premissa a confirmar no
      # primeiro apply — o pico real ainda não foi medido.
      cron         = "0 3 7 * *"
      ultimos_dias = 40
      memoria      = "4Gi"
      cpu          = "2"
    }
    ons_geracao_usina = {
      # Um CSV de ~66 MB por mês, ~534 mil linhas — a mesma forma do
      # ccee_geracao_usina (recurso mensal, runner que materializa a janela
      # inteira em memória), numa escala bem menor (~1/6 das linhas). Roda uma
      # hora depois dele, mesmo dia, para não disputar a mesma janela.
      # `ultimos_dias` 40 pela mesma conta: cobre o mês fechado e o anterior
      # (recontabilização) sem abrir um terceiro. `memoria`/`cpu` é premissa
      # declarada, a confirmar no primeiro apply — o pico real ainda não foi
      # medido.
      cron         = "0 4 7 * *"
      ultimos_dias = 40
      memoria      = "2Gi"
      cpu          = "1"
    }
    ccee_contrato_montante = {
      # Publicação mensal; dia 6, depois do PLD (dia 5). Janela de 120 dias
      # cobre a recontabilização (ADR 016), como as demais entidades mensais.
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    ccee_varejista_consumidor = {
      # Mesmo ritmo mensal das demais entidades desta fonte; janela de 120
      # dias cobre a recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    ccee_encargo_ess = {
      # Mesmo ritmo mensal das demais entidades desta fonte; janela de 120
      # dias cobre a recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    ccee_energia_reserva = {
      # Mesmo ritmo mensal das demais entidades desta fonte; janela de 120
      # dias cobre a recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    ccee_cvu_estrutural = {
      # Mesmo ritmo mensal das demais entidades desta fonte; janela de 120
      # dias cobre a recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
    bbce_curva_forward = {
      # A curva sai por pregão, em dia útil. Janela curta porque cada dia é uma
      # requisição própria; 7 dias cobrem feriado prolongado e execução perdida.
      cron         = "0 20 * * 1-5" # após o fechamento do pregão
      ultimos_dias = 7
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

        resources {
          limits = {
            memory = each.value.memoria
            cpu    = each.value.cpu
          }
        }

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
