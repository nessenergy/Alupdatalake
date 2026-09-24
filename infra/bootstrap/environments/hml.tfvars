# Bootstrap do projeto hml (ADR 015). ID criado pela Alup em 23/09, o mesmo de
# infra/environments/hml.tfvars: `alupar-hm-alupdata`, sem o "l" do nome do
# projeto (`alupar-hml-alupdata`).
project_id  = "alupar-hm-alupdata"
region      = "us-central1"
environment = "hml"

# Mesmo motivo do `dev`: nome de repositório pode ser liberado e recriado por
# outra pessoa; ID numérico não se reutiliza. É público na API do GitHub.
github_repositorio_id = "1345311867"
