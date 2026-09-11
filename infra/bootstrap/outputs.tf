# Cada saída vira uma variável do ambiente de mesmo nome no GitHub
# (docs/runbook/deploy.md). Nenhuma é segredo.

output "workload_identity_provider" {
  description = "GCP_WIF_PROVIDER"
  value       = google_iam_workload_identity_pool_provider.github.name
}

output "service_account_deploy" {
  description = "GCP_DEPLOY_SA"
  value       = google_service_account.deploy.email
}

output "bucket_state" {
  description = "TF_STATE_BUCKET"
  value       = google_storage_bucket.state.name
}

output "imagem_ingestao" {
  description = "IMAGEM_INGESTAO (sem tag)"
  value       = "${google_artifact_registry_repository.imagens.location}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.imagens.repository_id}/cli"
}

output "region" {
  description = "GCP_REGION"
  value       = var.region
}
