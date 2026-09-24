# O ID é `alupar-hm-alupdata`, sem o "l" — o nome do projeto é
# `alupar-hml-alupdata`. Divergência de origem, e ID de projeto não se
# renomeia: vale o ID.
project_id  = "alupar-hm-alupdata"
region      = "us-central1"
environment = "hml"

# Custo mínimo (E2, 11/09): hml não agenda nada fora da homologação. O Cloud
# Scheduler cobra por job existente, pausado ou não, e o workflow `diario` do
# Dataform consulta o BigQuery todo dia. Cloud Run Jobs, Portal e o Dataform
# disparado pelo deploy continuam disponíveis. Janela aberta desde 25/09 para
# a homologação das Ondas 0 e 1; fecha (volta para false) depois do aceite.
agendamentos_ativos        = true # janela de homologação das Ondas 0 e 1, 25/09
emails_alerta              = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]
conectores_sem_agendamento = ["hubspot_negocios", "bbce_curva_forward", "tempook_boletins"]

# Acesso de pessoas (R01 do RIPD): grupos Google da Alup, preenchidos por ela.
# Vazio não concede nada.
# grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
# grupo_operacao     = "<grupo-operacao>@<dominio-da-alup>"
# portal_acesso      = ["group:<grupo-consumidores>@<dominio-da-alup>"]
