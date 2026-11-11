# O ID é `prod-alupdata`, sem o prefixo `alupar-` dos outros dois; o nome do
# projeto é `alupar-prd-alupdata`. Vale o ID.
project_id  = "prod-alupdata"
region      = "us-central1"
environment = "prod"

# Bootstrap de produção (plano de 14/10, runbook/bootstrap-producao.md). Região
# mantida em us-central1 (ADR 023: a política da organização não admite us-east1)
# e grupos iguais aos de hml, por decisão do Ricardo em 30/10. O orçamento ainda
# não entra: billing_account vazio até a Alup fechar valor e papel (pergunta no PR).
#
# Agendamento DESLIGADO até a decisão de ligar (runbook/bootstrap-producao.md, passo 10): o Scheduler cobra
# por job existente e o workflow diário do Dataform consulta o BigQuery todo dia.
# Cloud Run Jobs seguem disponíveis para execução manual. Ligar = trocar para true
# com a data da janela de aceite no comentário.
agendamentos_ativos = false
emails_alerta       = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]

# Sem credencial em prod: ficam sem agendamento, como em hml.
conectores_sem_agendamento = ["hubspot_negocios", "bbce_curva_forward"]

# Mesmos grupos de hml, exceto grupo_bronze (pedido da Alup só para dev e hml; R01: só grupo).
gravacao_segredos = [
  "group:operacao-datalake@ness.com.br",
  "group:alup.alertas@alupar.com.br",
]
leitura_projeto           = ["group:operacao-datalake@ness.com.br"]
configuracao_login_portal = ["group:operacao-datalake@ness.com.br"]
portal_acesso             = ["group:operacao-datalake@ness.com.br", "group:alup.alertas@alupar.com.br"]
grupo_consumidores        = "alup.alertas@alupar.com.br"
