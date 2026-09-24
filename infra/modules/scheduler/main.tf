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
    timeout = optional(string, "1800s")
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
    ons_ear = {
      # Mesmo catálogo do ons_carga, mesmo horário de publicação; 15 min depois
      # para não disputar a mesma janela de execução com ele.
      cron         = "15 8 * * *"
      ultimos_dias = 30 # janela larga: o ONS revisa dado publicado
    }
    ons_ena = {
      # Mesmo catálogo do ons_ear; mais 15 min de espaçamento entre os três
      # conectores do ONS.
      cron         = "30 8 * * *"
      ultimos_dias = 30 # janela larga: o ONS revisa dado publicado
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
      # madrugada, um dia depois das entidades mensais leves.
      #
      # A CCEE publica o mês com cerca de dois meses de defasagem: em 24/09
      # o recurso mensal mais recente no CKAN (`geracao_horaria_usina`) era
      # 202607. `ultimos_dias` 40 não alcançava essa defasagem — a execução
      # de 24/09 extraiu zero linhas com status SUCESSO. `ultimos_dias` 100
      # alcança o mês publicado mais recente e o anterior (recontabilização,
      # ADR 016) — em geral três recursos mensais.
      #
      # Medido em 24/09: com o teto default de 8 MiB por lote, cada load job
      # carregava ~5.900 linhas, e o mês inteiro (~3 milhões de linhas) levava
      # ~42 min só de carga — estourando o `timeout` de 1800s sozinho, antes
      # mesmo de somar os outros dois meses da janela. `bytes_por_lote` do
      # conector (`src/conectores/ccee_geracao_usina.py`) subiu para 32 MiB,
      # 4x menos load jobs; com isso, três meses cabem com folga numa hora —
      # daí o `timeout` de 3600s abaixo.
      #
      # `memoria` deixou de ser premissa. Medido em 15/09 com o mês de julho
      # (2.964.096 registros), somando processo e filhos: o runner em fatias
      # marcou **225 MiB** de pico, contra **9.859 MiB** da versão que
      # materializava a janela inteira. Os 4 GiB que estavam aqui cobriam o
      # código antigo pela metade — ele teria sido morto por OOM na primeira
      # execução real. Com 1 GiB sobra folga de 4x sobre o pico medido, e a
      # medição do dry-run não inclui o payload que o `load_table_from_json`
      # monta por fatia, que é o que a folga cobre.
      cron         = "0 3 7 * *"
      ultimos_dias = 100
      memoria      = "1Gi"
      cpu          = "2"
      timeout      = "3600s"
    }
    ons_geracao_usina = {
      # Um CSV de ~66 MB por mês, ~534 mil linhas — a mesma forma do
      # ccee_geracao_usina (recurso mensal), numa escala bem menor (~1/6 das
      # linhas). Roda uma hora depois dele, mesmo dia, para não disputar a
      # mesma janela. `ultimos_dias` 40 pela mesma conta: cobre o mês fechado e
      # o anterior (recontabilização) sem abrir um terceiro.
      #
      # `memoria` **deixou de ser premissa**. Medida em 15/09 com o mês de
      # julho (533.832 linhas), somando processo e filhos: **440 MiB** de pico
      # em 84 s. Os 2 GiB que estavam aqui eram chute do tempo em que o runner
      # materializava a janela inteira; com o runner em fatias, 1 GiB dá folga
      # de mais de 2x sobre o medido — e a medição do dry-run não inclui o
      # payload que o `load_table_from_json` monta por fatia, que é o que a
      # folga cobre.
      cron         = "0 4 7 * *"
      ultimos_dias = 40
      memoria      = "1Gi"
      cpu          = "1"
    }
    ons_restricao_coff_eolica = {
      # Constrained-off eólico: CSV mensal de 46 MB, 227.664 linhas — passo de
      # 30 minutos, não de hora. Dia 7, uma hora depois da disponibilidade,
      # mantendo o espaçamento entre os conectores mensais pesados.
      #
      # Medido em 15/09 com o mês de agosto: **389 MiB** de pico em 60 s.
      # 1 GiB dá folga de 2,5x sobre o medido, que é o que cobre o payload do
      # `load_table_from_json` por fatia — o dry-run não o exercita.
      cron         = "0 6 7 * *"
      ultimos_dias = 40
      memoria      = "1Gi"
      cpu          = "1"
    }
    ons_restricao_coff_fotovoltaica = {
      # Mesmo arquivo, metade do tamanho: 121.536 linhas, 83 usinas. Meia hora
      # depois da eólica.
      #
      # Medido em 15/09 com o mês de agosto: **275 MiB** de pico em 33 s.
      cron         = "30 6 7 * *"
      ultimos_dias = 40
      memoria      = "1Gi"
      cpu          = "1"
    }
    ons_disponibilidade_usina = {
      # Mesmo formato do ons_geracao_usina (CSV mensal do mesmo catálogo), em
      # escala menor: ~117 mil linhas e 17 MB por mês. Roda uma hora depois
      # dele, mesmo dia, mantendo o espaçamento entre os conectores pesados.
      #
      # Medida em 15/09 com o mês de agosto (117.480 linhas): **226 MiB** de
      # pico em 30 s. O default de 512Mi cobriria o medido, mas com menos de
      # 2,3x de folga; 1 GiB mantém a mesma margem dos outros dois mensais.
      cron         = "0 5 7 * *"
      ultimos_dias = 40
      memoria      = "1Gi"
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
    tempook_ena_prevs = {
      # Previsão de ENA, um tar.gz de ~94 KB por dia — **diário, inclusive fim de
      # semana** (sondagem de 21/09: buracos pontuais, todos em sábado).
      # Mesmo endpoint e mesma cautela do boletim (ADR 019): cada dia é um POST
      # próprio, ~4,6 s cada medido em 21/09, então janela de 5 dias fica em ~25 s
      # e cobre execução perdida e publicação atrasada. Meia hora depois do
      # boletim para não disputar a mesma janela. Arquivo minúsculo: a memória
      # padrão sobra.
      cron         = "30 11 * * *"
      ultimos_dias = 5
    }
  }
}

variable "agendar" {
  description = "Cria os disparos do Cloud Scheduler; false deixa só os Cloud Run Jobs, para execução manual"
  type        = bool
  default     = true
}

variable "sem_agendamento" {
  description = "Conectores sem disparo agendado: o Cloud Run Job existe e roda à mão"
  type        = list(string)
  default     = []
}

locals {
  # Fonte sem credencial falha a cada disparo, e o erro repetido enterra o
  # alerta que importa. Sai do Scheduler; o job fica para quando a credencial
  # chegar.
  agendados = { for k, v in var.conectores : k => v if !contains(var.sem_agendamento, k) }
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
      timeout         = each.value.timeout

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
  for_each = var.agendar ? local.agendados : {}

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
