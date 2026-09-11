# Bootstrap do projeto dev (ADR 015). O ID definitivo é o que a Alup criar;
# este é o previsto, o mesmo de infra/environments/dev.tfvars.
project_id  = "alupdata-dev"
region      = "us-east1"
environment = "dev"

# O quadro (.github/workflows/quadro.yml) roda sem `environment:` e usa a SA de
# deploy de dev pelas variáveis do repositório: em dev, o WIF não exige ambiente.
restringir_ao_ambiente_github = false
