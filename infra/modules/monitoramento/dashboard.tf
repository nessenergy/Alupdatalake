# Painel no Cloud Monitoring.
#
# É o par do `/lake`: o Portal responde "as fontes estão em dia?" para quem
# opera o dado; este responde "a plataforma está saudável?" para quem opera a
# infraestrutura — e fica no mesmo lugar onde o alerta dispara, que é onde a
# pessoa já está quando o alerta chega.

resource "google_monitoring_dashboard" "plataforma" {
  project = var.project_id

  dashboard_json = jsonencode({
    displayName = "AlupData ${var.environment} — plataforma"
    mosaicLayout = {
      columns = 12
      tiles = [
        {
          width  = 6
          height = 4
          widget = {
            title = "Ingestões bem-sucedidas por fonte"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.ingestao_sucesso.name}\""
                    aggregation = {
                      alignmentPeriod    = "3600s"
                      perSeriesAligner   = "ALIGN_SUM"
                      groupByFields      = ["metric.label.fonte"]
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = { label = "execuções", scale = "LINEAR" }
            }
          }
        },
        {
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            title = "Registros descartados na validação"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "metric.type=\"logging.googleapis.com/user/${google_logging_metric.registros_invalidos.name}\""
                    aggregation = {
                      alignmentPeriod    = "3600s"
                      perSeriesAligner   = "ALIGN_SUM"
                      groupByFields      = ["metric.label.fonte"]
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "STACKED_BAR"
              }]
              yAxis = { label = "registros", scale = "LINEAR" }
            }
          }
        },
        {
          yPos   = 4
          width  = 6
          height = 4
          widget = {
            title = "Tarefas do Cloud Run Job por resultado"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = join(" ", [
                      "metric.type=\"run.googleapis.com/job/completed_task_attempt_count\"",
                      "resource.type=\"cloud_run_job\"",
                    ])
                    aggregation = {
                      alignmentPeriod    = "3600s"
                      perSeriesAligner   = "ALIGN_SUM"
                      groupByFields      = ["metric.label.result"]
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "STACKED_BAR"
              }]
              yAxis = { label = "tarefas", scale = "LINEAR" }
            }
          }
        },
        {
          yPos   = 4
          xPos   = 6
          width  = 6
          height = 4
          widget = {
            # Duração p95 por conector vive no painel /lake, que lê
            # `bronze._execucoes` — o registro tem o número exato por execução.
            title = "Execuções concluídas"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = join(" ", [
                      "metric.type=\"run.googleapis.com/job/completed_execution_count\"",
                      "resource.type=\"cloud_run_job\"",
                    ])
                    aggregation = {
                      alignmentPeriod  = "3600s"
                      perSeriesAligner = "ALIGN_DELTA"
                    }
                  }
                }
                plotType = "LINE"
              }]
              yAxis = { label = "execuções", scale = "LINEAR" }
            }
          }
        },
        {
          yPos   = 8
          width  = 12
          height = 3
          widget = {
            title = "Erros da ingestão"
            logsPanel = {
              filter        = "severity>=ERROR resource.type=\"cloud_run_job\""
              resourceNames = ["projects/${var.project_id}"]
            }
          }
        },
      ]
    }
  })
}
