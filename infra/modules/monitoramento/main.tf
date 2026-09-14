# Alertas do AlupData.
#
# O painel `/lake` responde quando alguém olha. Estas políticas são o que avisa
# quando ninguém está olhando — que é justamente quando o job quebra.
#
# Todas dependem do log estruturado de `src/core/observabilidade.py`: é o campo
# `fonte` no jsonPayload que permite contar sucesso por conector.

variable "project_id" { type = string }
variable "environment" { type = string }

variable "emails_alerta" {
  description = "Quem recebe. Sem destinatário, alerta configurado é alerta que ninguém lê."
  type        = list(string)
  default     = []
}

variable "conectores_criticos" {
  description = "Conectores cuja ausência de sucesso dispara alerta, e em quantas horas"
  type        = map(number)
  default = {
    bcb_cambio_ptax = 26  # diário + folga para feriado
    ons_carga       = 26  # diário
    aneel_siga      = 180 # semanal + folga
    ibge_ipca       = 780 # mensal + folga
    ccee_pld        = 780 # mensal + folga; mede a execução, não a defasagem da CCEE
    ccee_perfil     = 180 # semanal + folga
    # tempook_boletins fica fora enquanto não houver token (A7): alerta de
    # fonte que nunca rodou dispara todo dia e ensina a equipe a ignorá-lo.
  }
}

# ------------------------------------------------------------------ destinatário

resource "google_monitoring_notification_channel" "email" {
  for_each = toset(var.emails_alerta)

  project      = var.project_id
  display_name = "AlupData ${var.environment} — ${each.value}"
  type         = "email"

  labels = {
    email_address = each.value
  }
}

# ------------------------------------------------------------------ métricas de log

# Conta ingestões bem-sucedidas, rotuladas por fonte. É a base do alerta de
# frescor: o que importa não é "houve erro", é "faz tempo que não dá certo".
resource "google_logging_metric" "ingestao_sucesso" {
  project = var.project_id
  name    = "alupdata_ingestao_sucesso"

  filter = <<-EOT
    resource.type="cloud_run_job"
    jsonPayload.message=~"SUCESSO"
    jsonPayload.fonte!=""
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"

    labels {
      key         = "fonte"
      value_type  = "STRING"
      description = "Identificador da fonte de dados"
    }

    # Uma fonte pode ter várias entidades (`ccee_pld` e `ccee_perfil`), com
    # frequências diferentes. Sem este rótulo, a execução semanal de uma
    # satisfaria o alerta mensal da outra e o silêncio passaria despercebido.
    labels {
      key         = "entidade"
      value_type  = "STRING"
      description = "Entidade ingerida dentro da fonte"
    }
  }

  label_extractors = {
    "fonte"    = "EXTRACT(jsonPayload.fonte)"
    "entidade" = "EXTRACT(jsonPayload.entidade)"
  }
}

# Registros descartados por validação. Salto aqui costuma significar que o
# schema da origem mudou — o tipo de problema que passa despercebido porque a
# ingestão continua "funcionando".
resource "google_logging_metric" "registros_invalidos" {
  project = var.project_id
  name    = "alupdata_registros_invalidos"

  filter = <<-EOT
    resource.type="cloud_run_job"
    severity="WARNING"
    jsonPayload.message=~"registro inválido descartado"
  EOT

  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"

    labels {
      key        = "fonte"
      value_type = "STRING"
    }
  }

  label_extractors = {
    "fonte" = "EXTRACT(jsonPayload.fonte)"
  }
}

# ------------------------------------------------------------------ alertas

# 1. O job falhou.
resource "google_monitoring_alert_policy" "job_falhou" {
  project      = var.project_id
  display_name = "AlupData ${var.environment} — ingestão falhou"
  combiner     = "OR"

  conditions {
    display_name = "Cloud Run Job com tarefa falhada"

    condition_threshold {
      filter = join(" AND ", [
        "resource.type = \"cloud_run_job\"",
        "metric.type = \"run.googleapis.com/job/completed_task_attempt_count\"",
        "metric.labels.result = \"failed\"",
      ])
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      duration        = "0s"

      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [for canal in google_monitoring_notification_channel.email : canal.id]

  documentation {
    content   = <<-EOT
      Uma execução de ingestão falhou.

      1. Abra o painel: /lake — o cartão do conector mostra o último erro.
      2. Para ver a execução inteira, filtre o log por `jsonPayload.ingestao_id`.
      3. Reexecutar é seguro: o Bronze é append-only e a Silver deduplica.
    EOT
    mime_type = "text/markdown"
  }
}

# 2. A fonte parou de dar certo — sem erro, só silêncio.
resource "google_monitoring_alert_policy" "fonte_sem_sucesso" {
  for_each = var.conectores_criticos

  project      = var.project_id
  display_name = "AlupData ${var.environment} — ${each.key} sem sucesso há ${each.value}h"
  combiner     = "OR"

  conditions {
    display_name = "Nenhuma ingestão bem-sucedida de ${each.key}"

    condition_absent {
      filter = join(" AND ", [
        "resource.type = \"cloud_run_job\"",
        "metric.type = \"logging.googleapis.com/user/${google_logging_metric.ingestao_sucesso.name}\"",
        # A chave do mapa é o rótulo do conector (`ccee_pld`): a `fonte` é a
        # primeira parte e a `entidade`, o resto. As duas são necessárias —
        # `ccee_pld` e `ccee_perfil` dividem a fonte e têm frequências
        # diferentes.
        "metric.labels.fonte = \"${split("_", each.key)[0]}\"",
        "metric.labels.entidade = \"${join("_", slice(split("_", each.key), 1, length(split("_", each.key))))}\"",
      ])
      duration = "${each.value * 3600}s"

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [for canal in google_monitoring_notification_channel.email : canal.id]

  documentation {
    content   = <<-EOT
      A fonte `${each.key}` não registra ingestão bem-sucedida há ${each.value} horas.

      Isso é diferente de "falhou": pode ser job que não disparou, agendamento
      removido, ou a origem devolvendo vazio sem erro. Comece pelo histórico de
      execuções do Cloud Run Job antes de olhar o código.
    EOT
    mime_type = "text/markdown"
  }
}

# 3. Salto de registros inválidos.
resource "google_monitoring_alert_policy" "invalidos_em_alta" {
  project      = var.project_id
  display_name = "AlupData ${var.environment} — registros inválidos em alta"
  combiner     = "OR"

  conditions {
    display_name = "Mais de 100 registros descartados em uma hora"

    condition_threshold {
      filter          = "metric.type = \"logging.googleapis.com/user/${google_logging_metric.registros_invalidos.name}\" AND resource.type = \"cloud_run_job\""
      comparison      = "COMPARISON_GT"
      threshold_value = 100
      duration        = "0s"

      aggregations {
        alignment_period   = "3600s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = [for canal in google_monitoring_notification_channel.email : canal.id]

  documentation {
    content   = <<-EOT
      Muitos registros descartados na validação. A causa quase sempre é mudança
      de schema na origem — a ingestão continua "funcionando" e o dado para de
      chegar.

      Compare o payload bruto no bucket raw com o schema Pydantic do conector.
      Se a origem mudou de verdade, incremente `schema_versao`.
    EOT
    mime_type = "text/markdown"
  }
}

# 4. O workflow do Dataform falhou — asserção reprovada, ou erro de execução.
#
# É o portão de qualidade da camada Silver (ADR 012, issue #110). Sem este
# alerta, uma asserção violada não impede nada que alguém perceba: a view
# continua servindo dado que já foi reprovado, e o erro só aparece quando
# alguém questiona um número — meses depois, sem rastro de quando começou.
#
# O sinal vem do log do próprio serviço: a invocação do workflow registra
# entrada com severidade ERROR quando termina em falha.
resource "google_monitoring_alert_policy" "dataform_falhou" {
  project      = var.project_id
  display_name = "AlupData ${var.environment} — Dataform falhou (asserção ou execução)"
  combiner     = "OR"

  conditions {
    display_name = "Invocação do workflow do Dataform com erro"

    condition_matched_log {
      filter = join(" AND ", [
        "resource.type = \"dataform.googleapis.com/Repository\"",
        "severity >= ERROR",
      ])
    }
  }

  # Log-based alert exige estratégia de notificação; sem ela o Terraform recusa.
  alert_strategy {
    notification_rate_limit {
      # Uma asserção violada costuma violar em várias linhas e várias tabelas
      # na mesma execução. Sem o limite, uma falha vira dezenas de e-mails e a
      # equipe aprende a ignorar o alerta — que é o pior resultado possível.
      period = "3600s"
    }
  }

  notification_channels = [for canal in google_monitoring_notification_channel.email : canal.id]

  documentation {
    content   = <<-EOT
      O workflow do Dataform terminou em falha.

      1. A causa mais comum é **asserção reprovada**. As linhas que violaram
         ficam no dataset `qualidade`, uma tabela por asserção — comece por lá,
         não pelo log.
      2. Asserção de **faixa** (`rowConditions`) reprovando quase sempre
         significa que a origem mudou o conteúdo sem mudar o schema: sigla nova
         de submercado, preço negativo, campo que passou a vir nulo.
      3. Enquanto não for resolvido, a Silver segue servindo o dado anterior —
         o Bronze é append-only e nada foi perdido.
    EOT
    mime_type = "text/markdown"
  }
}

output "canais" {
  description = "IDs dos canais de notificação, para reuso em outros alertas"
  value       = [for canal in google_monitoring_notification_channel.email : canal.id]
}
