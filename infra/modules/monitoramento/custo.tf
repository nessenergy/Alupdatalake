# Alerta de custo.
#
# Orçamento não impede gasto — o Google não desliga nada sozinho. O que ele faz
# é avisar antes da fatura, que é a diferença entre corrigir em um dia e
# descobrir no fim do mês.
#
# Requer o ID da conta de faturamento, que é da Alup (pendência A3, issue #55).
# Sem ele o recurso não é criado: orçamento com número inventado é pior que
# nenhum.

variable "billing_account" {
  description = "ID da conta de faturamento (formato 000000-000000). Vazio desliga o alerta de custo."
  type        = string
  default     = ""
}

variable "orcamento_mensal_brl" {
  description = "Teto mensal esperado, em BRL. Ondas 0–2 estimadas em US$ 5–15/mês; o salto vem com o Composer."
  type        = number
  default     = 500
}

resource "google_billing_budget" "mensal" {
  count = var.billing_account == "" ? 0 : 1

  billing_account = var.billing_account
  display_name    = "AlupData ${var.environment} — orçamento mensal"

  budget_filter {
    projects = ["projects/${var.project_id}"]
  }

  amount {
    specified_amount {
      currency_code = "BRL"
      units         = tostring(var.orcamento_mensal_brl)
    }
  }

  # 50% e 90% avisam a tempo de agir; 100% sobre a projeção pega a curva antes
  # de ela virar fatura.
  dynamic "threshold_rules" {
    for_each = [0.5, 0.9]
    content {
      threshold_percent = threshold_rules.value
      spend_basis       = "CURRENT_SPEND"
    }
  }

  threshold_rules {
    threshold_percent = 1.0
    spend_basis       = "FORECASTED_SPEND"
  }

  dynamic "all_updates_rule" {
    for_each = length(var.emails_alerta) > 0 ? [1] : []
    content {
      monitoring_notification_channels = [for canal in google_monitoring_notification_channel.email : canal.id]
      disable_default_iam_recipients   = true
    }
  }
}
