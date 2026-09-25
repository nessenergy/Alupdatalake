terraform {
  required_version = ">= 1.5"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
  }

  # Um bucket de state por projeto, criado pelo bootstrap (infra/bootstrap). O
  # nome entra no init — `terraform init -backend-config="bucket=<bucket>"`,
  # variável TF_STATE_BUCKET do ambiente no GitHub. O CI valida com
  # `-backend=false`.
  backend "gcs" {
    prefix = "infra"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Release e workflow configs do Dataform só existem no provider beta.
provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ------------------------------------------------------------------ identidade

# Uma service account para as ingestões. Permissões de dado ficam no recurso
# específico (dataset, bucket, secret e job); só a criação de jobs BigQuery é
# inevitavelmente concedida no projeto.
resource "google_service_account" "ingestao" {
  account_id   = "alupdata-ingestao"
  display_name = "AlupData — ingestão"
  project      = var.project_id
}

locals {
  papeis_ingestao = [
    "roles/bigquery.jobUser",
    "roles/datalineage.producer",
  ]
}

resource "google_project_iam_member" "ingestao" {
  for_each = toset(local.papeis_ingestao)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${google_service_account.ingestao.email}"
}

resource "google_bigquery_dataset_iam_member" "ingestao_bronze" {
  project    = var.project_id
  dataset_id = module.bigquery.dataset_ids["bronze"]
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.ingestao.email}"
}

# --------------------------------------------------------------------- pessoas

# R01 do RIPD: pessoa entra por grupo Google da Alup, nunca por e-mail
# individual. Os grupos são da Alup; com o e-mail vazio (padrão), nada é
# concedido.
#
# As views da Gold leem Silver e Bronze e não são views autorizadas: até isso
# ser decidido, o grupo de consumidores enxerga a Gold mas a consulta falha por
# falta de acesso às camadas de baixo. Autorizar exige trocar o IAM aditivo por
# `google_bigquery_dataset_access`, que o provider diz não conviver com
# `google_bigquery_dataset_iam_member` no mesmo dataset.
locals {
  camadas_por_grupo = {
    consumidores = { grupo = var.grupo_consumidores, camadas = ["gold"] }
    operacao     = { grupo = var.grupo_operacao, camadas = ["bronze", "silver", "gold"] }
  }

  leitura_pessoas = merge([
    for nome, g in local.camadas_por_grupo : {
      for camada in g.camadas : "${nome}_${camada}" => { grupo = g.grupo, camada = camada }
    } if g.grupo != ""
  ]...)
}

resource "google_bigquery_dataset_iam_member" "pessoas" {
  for_each = local.leitura_pessoas

  project    = var.project_id
  dataset_id = module.bigquery.dataset_ids[each.value.camada]
  role       = "roles/bigquery.dataViewer"
  member     = "group:${each.value.grupo}"
}

# jobUser não dá acesso a dado: só permite rodar consulta neste projeto.
resource "google_project_iam_member" "pessoas_jobs" {
  for_each = toset([for g in local.camadas_por_grupo : g.grupo if g.grupo != ""])

  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "group:${each.value}"
}

# Leitura do projeto inteiro para quem opera: configuração, logs, execuções de
# job e metadado de segredo — **sem o valor de segredo nenhum**, que `viewer`
# não inclui (`secretmanager.versions.access` fica de fora). Somado ao
# `grupo_operacao`, que dá o dado das três camadas, é o que falta para conferir
# carga e investigar falha sem console de ninguém. Só group:/domain: (R01).
resource "google_project_iam_member" "leitura_projeto" {
  for_each = toset(var.leitura_projeto)

  project = var.project_id
  role    = "roles/viewer"
  member  = each.value
}

# ------------------------------------------------------------------- auditoria

# R07 do RIPD: quem leu e quem gravou dado no BigQuery e no Cloud Storage. O
# log vai para o bucket _Default, com a retenção padrão do Cloud Logging, até a
# política de retenção ser aprovada. O volume é cobrado da Alup pelo Cloud
# Logging (docs/runbook/deploy.md). ADMIN_READ fica de fora: é leitura de
# metadado, não de dado, e multiplicaria o volume.
resource "google_project_iam_audit_config" "acesso_dados" {
  for_each = toset(["bigquery.googleapis.com", "storage.googleapis.com"])

  project = var.project_id
  service = each.value

  audit_log_config {
    log_type = "DATA_READ"
  }
  audit_log_config {
    log_type = "DATA_WRITE"
  }
}

# --------------------------------------------------------------------- módulos

module "bigquery" {
  source      = "./modules/bigquery"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
}

module "storage" {
  source                = "./modules/storage"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = google_service_account.ingestao.email
}

module "secrets" {
  source                = "./modules/secrets"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  service_account_email = google_service_account.ingestao.email
  # A SA do deploy é a que o GitHub assume via WIF; o quadro a reutiliza.
  github_service_account = var.deploy_service_account
  gravacao_segredos      = var.gravacao_segredos
}

# Alertas. `emails_alerta` vazio cria as políticas sem destinatário — ver o
# README do módulo: quem recebe é acordo operacional, não configuração.
module "monitoramento" {
  source          = "./modules/monitoramento"
  project_id      = var.project_id
  environment     = var.environment
  emails_alerta   = var.emails_alerta
  billing_account = var.billing_account
}

# Só sobe quando existe imagem publicada — antes disso o agendamento não tem o
# que executar.
module "scheduler" {
  count = var.imagem_ingestao == "" ? 0 : 1

  source                = "./modules/scheduler"
  project_id            = var.project_id
  region                = var.region
  environment           = var.environment
  imagem                = var.imagem_ingestao
  service_account_email = google_service_account.ingestao.email
  agendar               = var.agendamentos_ativos
  sem_agendamento       = var.conectores_sem_agendamento

  rede_interna            = var.rede_interna
  conectores_rede_interna = var.conectores_rede_interna
  fontes_teste_conexao    = var.fontes_teste_conexao
}

# Portal atrás do IAP (R01). Sobe com a imagem publicada, que é a mesma da CLI;
# `portal_acesso` vazio publica o serviço sem ninguém autorizado.
module "portal" {
  count = var.imagem_ingestao == "" ? 0 : 1

  source      = "./modules/portal"
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  imagem      = var.imagem_ingestao
  datasets    = values(module.bigquery.dataset_ids)
  acesso      = var.portal_acesso
}

module "dataform" {
  source                 = "./modules/dataform"
  project_id             = var.project_id
  region                 = var.region
  environment            = var.environment
  datasets               = concat(values(module.bigquery.dataset_ids), [module.bigquery.dataset_qualidade])
  git_token_versao       = var.dataform_git_token_versao
  deploy_service_account = var.deploy_service_account
  agendar                = var.agendamentos_ativos
  gravacao_segredos      = var.gravacao_segredos
}

# Knowledge Catalog (ADR 014): lake, zonas e ativos sobre o que já existe.
# Descoberta desligada — o esquema vem do Dataform, não de varredura paga.
module "catalogo" {
  source              = "./modules/catalogo"
  project_id          = var.project_id
  region              = var.region
  environment         = var.environment
  datasets_por_camada = module.bigquery.dataset_ids
  dataset_qualidade   = module.bigquery.dataset_qualidade
  bucket_raw          = module.storage.bucket_raw
}

# Onda 3 (ADR 017): a cadeia só existe quando houver fonte interna ingerida.
# Com `cadeia_onda3` vazia — o padrão — nenhum recurso é criado.
module "orquestracao" {
  source                   = "./modules/orquestracao"
  project_id               = var.project_id
  region                   = var.region
  environment              = var.environment
  cadeia                   = var.cadeia_onda3
  agendar                  = var.agendamentos_ativos
  repositorio_dataform     = module.dataform.repositorio
  service_account_dataform = module.dataform.service_account
}
