# O ID é `prod-alupdata`, sem o prefixo `alupar-` dos outros dois; o nome do
# projeto é `alupar-prd-alupdata`. Vale o ID.
project_id  = "prod-alupdata"
region      = "us-central1"
environment = "prod"

# Preparado em 30/10/2026 (plano de 14/10). Região mantida em us-central1 e grupos
# iguais aos de hml, por decisão do Ricardo em 30/10. O orçamento ainda não entra
# (decisão 2.4). O agendamento não é
# declarado aqui (regra do test_infra): o primeiro apply o desliga por variável.
emails_alerta = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]

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
