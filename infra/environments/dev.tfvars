project_id  = "alupar-dev-alupdata"
region      = "us-central1"
environment = "dev"

# Acesso de pessoas (R01 do RIPD): grupos Google da Alup, preenchidos por ela.
# Vazio não concede nada.
# grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
# grupo_operacao     = "<grupo-operacao>@<dominio-da-alup>"
# portal_acesso      = ["group:<grupo-consumidores>@<dominio-da-alup>"]

# Quem grava versão de secret sem poder ler — o token do Dataform e as
# credenciais das fontes (ADR 015, acesso de operação). Grupo da ness., nunca
# pessoa (R01). Vazio não concede nada.
gravacao_segredos = ["group:operacao-datalake@ness.com.br"]
