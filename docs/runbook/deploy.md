# Runbook — deploy da infraestrutura e das ingestões

## O que existe

| Recurso | Onde é declarado |
|---|---|
| Datasets `bronze`, `silver`, `gold` | `infra/modules/bigquery` |
| Bucket `<projeto>-raw` | `infra/modules/storage` |
| Secrets das fontes credenciadas (vazios) | `infra/modules/secrets` |
| Cloud Run Job + Cloud Scheduler por conector | `infra/modules/scheduler` |
| Service account `alupdata-ingestao` e seu IAM | `infra/main.tf` |

Recurso criado no console não existe: some no próximo `apply`.

## Pré-requisitos (uma vez por ambiente)

1. Projeto GCP criado, APIs habilitadas: BigQuery, Cloud Storage, Secret
   Manager, Cloud Run, Cloud Scheduler, Artifact Registry.
2. Bucket de state do Terraform e o `backend "gcs"` descomentado em
   `infra/main.tf`.
3. Repositório no Artifact Registry para a imagem da CLI.
4. **Workload Identity Federation** entre o GitHub e o GCP — o deploy **não**
   usa chave JSON de service account (cláusula 8.5).
5. Variáveis do repositório/ambiente no GitHub:

| Variável | Exemplo |
|---|---|
| `GCP_WIF_PROVIDER` | `projects/123/locations/global/workloadIdentityPools/github/providers/alupdata` |
| `GCP_DEPLOY_SA` | `alupdata-deploy@alupdata-dev.iam.gserviceaccount.com` |
| `GCP_REGION` | `us-east1` |
| `IMAGEM_INGESTAO` | `us-east1-docker.pkg.dev/alupdata-dev/alupdata/cli` (sem tag) |

## Deploy

Workflow **Deploy GCP** (`workflow_dispatch`), escolhendo ambiente e módulo:

- `connectors` → constrói e publica a imagem da CLI (`:<sha>` e `:latest`)
- `infra` → `terraform plan` + `apply` usando `IMAGEM_INGESTAO:latest`
- `all` → os dois

Ordem na primeira vez: **`connectors` antes de `infra`**. Sem imagem publicada,
`imagem_ingestao` fica vazio e o módulo de agendamento não sobe — de propósito,
para o `apply` não falhar referenciando uma imagem inexistente.

## Views

O SQL de `sql/` não é aplicado pelo Terraform:

```bash
make deploy-views                          # aplica bronze, silver e gold
uv run python -m scripts.deploy_views --dry-run   # revisa antes
```

## Verificar uma ingestão

```sql
SELECT fonte, janela_inicio, janela_fim, status, linhas_carregadas, erro
FROM `<projeto>.bronze._execucoes`
WHERE DATE(iniciada_em) = CURRENT_DATE()
ORDER BY iniciada_em DESC;
```

Reprocessar uma janela específica (o Bronze é append-only; a Silver deduplica):

```bash
alupdata ingerir bcb_cambio_ptax --de 2026-01-01 --ate 2026-01-31
```

## Segredos

O Terraform cria o secret vazio; o valor entra fora do versionamento:

```bash
gcloud secrets versions add alupdata-ccee-api-token --data-file=-
```

Enquanto a Alup não entrega o token, o secret existe sem versão — e o conector
da onda correspondente falha explicitamente, em vez de silenciar.
