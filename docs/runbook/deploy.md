# Runbook — deploy da infraestrutura e das ingestões

Para a primeira implantação, use também a checklist
[`primeiro-deploy.md`](primeiro-deploy.md).

## O que existe

| Recurso | Onde é declarado |
|---|---|
| Datasets `bronze`, `silver`, `gold` | `infra/modules/bigquery` |
| Dataset `faturamento` (destino do billing export) | `infra/modules/bigquery` |
| Bucket `<projeto>-raw` | `infra/modules/storage` |
| Secrets das fontes credenciadas (vazios) | `infra/modules/secrets` |
| Cloud Run Job + Cloud Scheduler por conector | `infra/modules/scheduler` |
| Service account `alupdata-ingestao` e seu IAM | `infra/main.tf` |
| Repositório Dataform, release config `main`, workflow config `diario` e SA `alupdata-dataform` | `infra/modules/dataform` |
| Dataset `qualidade` (assertions do Dataform) | `infra/modules/bigquery` |

IAM da identidade de ingestão:

| Escopo | Papel |
|---|---|
| Projeto | `roles/bigquery.jobUser`, `roles/datalineage.producer` |
| Dataset Bronze | `roles/bigquery.dataEditor` |
| Bucket raw | `roles/storage.objectCreator` e `roles/storage.objectViewer` |
| Cada secret declarado | `roles/secretmanager.secretAccessor` |
| Cada Cloud Run Job | `roles/run.invoker` |

IAM do lado do Dataform (ADR 012):

| Identidade | Papel |
|---|---|
| SA `alupdata-dataform` | `roles/bigquery.jobUser`, `roles/bigquery.resourceViewer` e `roles/bigquery.metadataViewer` no projeto; `roles/bigquery.dataEditor` em `bronze`, `silver`, `gold` e `qualidade` |
| SA de deploy | `roles/dataform.editor` no repositório `alupdata`; `roles/iam.serviceAccountUser` na SA do Dataform |
| Agente de serviço do Dataform | `roles/iam.serviceAccountTokenCreator` e `roles/iam.serviceAccountUser` na SA do Dataform; `roles/secretmanager.secretAccessor` no secret do token |

Recurso criado no console não existe: some no próximo `apply`.

## Pré-requisitos (uma vez por ambiente)

1. Projeto GCP criado, APIs habilitadas: BigQuery, Cloud Storage, Secret
   Manager, Cloud Run, Cloud Scheduler, Artifact Registry, Dataform, Data Lineage, Dataplex.
2. Bucket de state do Terraform, criado em `us-east1` (ADR 011), e o
   `backend "gcs"` descomentado em `infra/main.tf`.
3. Repositório no Artifact Registry para a imagem da CLI, criado em
   `us-east1` (ADR 011).
4. **Workload Identity Federation** entre o GitHub e o GCP — o deploy **não**
   usa chave JSON de service account (cláusula 8.5).
5. Variáveis do repositório/ambiente no GitHub:

| Variável | Exemplo |
|---|---|
| `GCP_WIF_PROVIDER` | `projects/123/locations/global/workloadIdentityPools/github/providers/alupdata` |
| `GCP_DEPLOY_SA` | `alupdata-deploy@alupdata-dev.iam.gserviceaccount.com` |
| `GCP_REGION` | `us-east1` |
| `IMAGEM_INGESTAO` | `us-east1-docker.pkg.dev/alupdata-dev/alupdata/cli` (sem tag) |
| `DATAFORM_GIT_TOKEN_VERSAO` | `1` (versão do secret `alupdata-dataform-git-token`) |

## Deploy

Workflow **Deploy GCP** (`workflow_dispatch`), escolhendo ambiente e módulo:

- `connectors` → constrói e publica a imagem da CLI (`:<sha completo>` e `:latest`)
- `infra` → `terraform plan` + `apply` usando a imagem já publicada em `:latest`
- `all` → publica a imagem imutável, aplica Terraform com essa mesma tag e
  depois aplica o SQL versionado

No fluxo `all`, o job Terraform depende explicitamente do job de imagem. Isso
impede o primeiro `apply` de disputar com o primeiro push. O estado guarda a tag
imutável do commit; `latest` permanece apenas como conveniência operacional.

## SQL das camadas (Dataform)

O SQL de `definitions/` é compilado pelo Dataform a partir da `main` (ADR 012):

```bash
make dataform-compile                                   # valida localmente, sem credencial
uv run python -m scripts.executar_dataform --service-account alupdata-dataform@<projeto>.iam.gserviceaccount.com
```

O deploy `all`/`infra` executa o segundo comando logo após o `apply`. Depois
disso, a *workflow config* `diario` roda às 11h (horário de Brasília).

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

Reprocessar um payload já arquivado, sem chamar a fonte novamente:

```bash
alupdata reprocessar-raw bcb_cambio_ptax \
  --uri gs://<bucket>/bcb/cambio_ptax/dt=2026-01-01/<ingestao_id>.json.gz \
  --de 2026-01-01 --ate 2026-01-31
```

O replay cria uma nova execução com `modo=REPLAY` e preenche
`origem_ingestao_id`. A janela é obrigatória porque os objetos raw gravados até
esta versão não carregam a data final no próprio arquivo.

## Segredos

O Terraform cria o secret vazio; o valor entra fora do versionamento:

```bash
gcloud secrets versions add alupdata-ccee-api-token --data-file=-
```

Enquanto a Alup não entrega o token, o secret existe sem versão — e o conector
da onda correspondente falha explicitamente, em vez de silenciar.

O Dataform lê o repositório com um token *fine-grained* do GitHub restrito a
`nessenergy/Alupdatalake`, permissão *Contents: Read-only*:
`gcloud secrets versions add alupdata-dataform-git-token --data-file=-`. Sem
ele, o deploy falha no passo do Dataform — de propósito: sem Dataform não há
tabela Bronze.
