# Bootstrap do projeto dev (ADR 015). ID criado pela Alup em 23/09, o mesmo de
# infra/environments/dev.tfvars.
project_id  = "alupar-dev-alupdata"
region      = "us-central1"
environment = "dev"

# O quadro (.github/workflows/quadro.yml) roda sem `environment:` e usa a SA de
# deploy de dev pelas variáveis do repositório: em dev, o WIF não exige ambiente.
restringir_ao_ambiente_github = false
