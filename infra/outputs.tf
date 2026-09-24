output "project_id" {
  description = "ID do projeto GCP"
  value       = var.project_id
}

output "region" {
  description = "Região GCP"
  value       = var.region
}

output "datasets" {
  description = "Datasets por camada"
  value       = module.bigquery.dataset_ids
}

output "bucket_raw" {
  description = "Bucket de dado bruto"
  value       = module.storage.bucket_raw
}

output "service_account_ingestao" {
  description = "Service account que executa as ingestões"
  value       = google_service_account.ingestao.email
}

output "jobs_ingestao" {
  description = "Cloud Run Jobs agendados (vazio até existir imagem publicada)"
  value       = one(module.scheduler[*].jobs)
}

# `one()` e não `try()`: valor que só se conhece depois do apply — a URL é um
# deles — faz o `try` cair no fallback já no plano, e o output nasce vazio e
# assim fica. Foi o que aconteceu no primeiro apply de dev, em 23/09: o
# serviço subiu com URL e o output veio "". Com `one()`, módulo sem instância
# devolve `null` e módulo com instância devolve o valor de verdade.
output "url_portal" {
  description = "URL do Portal, atrás do IAP (nulo até existir imagem publicada)"
  value       = one(module.portal[*].url)
}

output "dataset_faturamento" {
  description = "Destino do billing export — ligado no console pela Alup (ADR 007)"
  value       = module.bigquery.dataset_faturamento
}

output "service_account_dataform" {
  description = "SA que executa o Dataform"
  value       = module.dataform.service_account
}

output "repositorio_dataform" {
  description = "Repositório Dataform (vazio enquanto não houver token do GitHub)"
  value       = module.dataform.repositorio
}
