project_id  = "alupar-dev-alupdata"
region      = "us-central1"
environment = "dev"

# Acesso de pessoas (R01 do RIPD): grupos Google da Alup, preenchidos por ela.
# Vazio não concede nada.
# grupo_consumidores = "<grupo-consumidores>@<dominio-da-alup>"
# Em dev, a operação é da ness. (24/09): dado das três camadas e consulta, para
# conferir a carga. Em hml e prod, o grupo é o da Alup.
grupo_operacao = "operacao-datalake@ness.com.br"
# portal_acesso      = ["group:<grupo-consumidores>@<dominio-da-alup>"]

# Quem grava versão de secret sem poder ler — o token do Dataform e as
# credenciais das fontes (ADR 015, acesso de operação). Grupo da ness., nunca
# pessoa (R01). Vazio não concede nada.
gravacao_segredos = ["group:operacao-datalake@ness.com.br"]

# Leitura do projeto inteiro, sem valor de segredo (roles/viewer).
leitura_projeto = ["group:operacao-datalake@ness.com.br"]

# Validação do Portal com dado real (Onda 0). O grupo da Alup entra em hml.
portal_acesso = ["group:operacao-datalake@ness.com.br"]
