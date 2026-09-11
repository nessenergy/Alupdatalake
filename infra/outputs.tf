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
  value       = try(module.scheduler[0].jobs, [])
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
