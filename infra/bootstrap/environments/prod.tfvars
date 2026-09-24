# Bootstrap do projeto prod (ADR 015). ID criado pela Alup em 23/09, o mesmo de
# infra/environments/prod.tfvars: `prod-alupdata`, sem o prefixo `alupar-`.
project_id  = "prod-alupdata"
region      = "us-central1"
environment = "prod"

# Mesmo motivo do `dev`: nome de repositório pode ser liberado e recriado por
# outra pessoa; ID numérico não se reutiliza. É público na API do GitHub.
github_repositorio_id = "1345311867"
