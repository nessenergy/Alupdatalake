# O ID é `prod-alupdata`, sem o prefixo `alupar-` dos outros dois; o nome do
# projeto é `alupar-prd-alupdata`. Vale o ID.
project_id  = "prod-alupdata"
region      = "us-central1"
environment = "prod"

# Acesso de pessoas (R01 do RIPD): grupos Google da Alup, preenchidos por ela.
# Vazio não concede nada.
# grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
# grupo_operacao     = "<grupo-operacao>@<dominio-da-alup>"
# portal_acesso      = ["group:<grupo-consumidores>@<dominio-da-alup>"]

# Preparado em 30/10/2026 (plano de 14/10). Valores seguros para o primeiro
# apply: nada agenda e nenhum acesso de pessoa é concedido até a Alup decidir
# os grupos (plano, decisão 2.3).
agendamentos_ativos = false
emails_alerta       = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]

# Sem credencial em prod: ficam sem agendamento, como em hml.
conectores_sem_agendamento = ["hubspot_negocios", "bbce_curva_forward"]
