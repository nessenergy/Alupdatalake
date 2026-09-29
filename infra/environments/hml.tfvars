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
agendamentos_ativos = true # janela de homologação das Ondas 0 e 1, 25/09
emails_alerta       = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]
# Em hml, o TempoOK também fica fora: a credencial só existe em dev, e a
# janela é das Ondas 0 e 1 — o TempoOK é Onda 2.
conectores_sem_agendamento = ["hubspot_negocios", "bbce_curva_forward", "tempook_boletins", "tempook_ena_prevs"]

# Quem grava versão de secret sem poder ler (ADR 015): o token do Dataform em
# hml é da ness., gravado pelo grupo de operação da ness. Nunca pessoa (R01).
gravacao_segredos = ["group:operacao-datalake@ness.com.br"]

# Leitura do projeto inteiro, sem valor de segredo (roles/viewer), como em dev:
# sem ela a operação não confere versão de secret nem configuração do Dataform.
leitura_projeto = ["group:operacao-datalake@ness.com.br"]

# Quem configura o login do Portal no console (cliente OAuth "Externo" e IAP):
# a ness. confere o que entrega. Sem acesso a dado (runbook/portal.md).
configuracao_login_portal = ["group:operacao-datalake@ness.com.br"]

# Acesso de pessoas ao Portal (R01 do RIPD: só grupo). A operação da ness. entra
# sempre: quem entrega confere o que entregou (runbook/portal.md, "Acesso da
# ness."). O grupo da Alup, pedido na #261, entra ao lado quando chegar —
# descomente grupo_consumidores e acrescente o mesmo e-mail à lista abaixo
# (runbook em docs/runbook/portal.md#liberar-o-dado-real-para-a-alup).
portal_acesso = ["group:operacao-datalake@ness.com.br"]
# grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
#
# grupo_operacao dá também Bronze e Silver — só se a Alup pedir explicitamente
# mais que a Gold; não presumir.
# grupo_operacao     = "<grupo-operacao>@<dominio-da-alup>"
