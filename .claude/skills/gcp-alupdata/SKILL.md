---
name: gcp-alupdata
description: Convenções de GCP do AlupData — BigQuery (datasets Bronze/Silver/Gold, nomenclatura, particionamento, clustering, custo), Cloud Storage, Secret Manager, Cloud Composer/Scheduler e os módulos Terraform em infra/. Use ao criar ou alterar dataset, tabela, view, bucket, DAG, job agendado, IAM, secret ou qualquer recurso GCP, e ao escrever ou revisar SQL/Terraform deste repositório.
---

# GCP no AlupData

Tudo em GCP, arquitetura Medallion, infraestrutura por Terraform. Recurso criado
à mão no console **não existe** — se não está em `infra/`, some no próximo
`terraform apply` e não sobe para produção.

## Ambientes

Dois: `dev` e `prod` (`infra/variables.tf` valida). Região padrão `us-east1`.
Variáveis por ambiente em `infra/environments/{dev,prod}.tfvars`. Nunca aponte
código para `prod` por default — `src/core/config.py` cai em `alupdata-dev`.

## BigQuery

**Datasets**: `bronze`, `silver`, `gold` (nomes vêm de `src/core/config.py`, não
os escreva literalmente no código Python).

**Nomenclatura**

| Camada | Padrão | Exemplo |
|---|---|---|
| Bronze | `bronze.<fonte>_<entidade>` | `bronze.ccee_infomercado_precos` |
| Silver | `silver.<fonte>_<entidade>` | `silver.ccee_precos` |
| Gold | `gold.<pergunta_de_negocio>` | `gold.preco_medio_submercado` |

Nomes de objeto e coluna em `snake_case`, sem acento, sem maiúscula. Colunas
técnicas com prefixo `_`.

**Particionamento e clustering** — obrigatórios em toda tabela Bronze:

```sql
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, submercado
```

Sem partição, cada consulta varre a tabela inteira e a conta de BigQuery é da
Alup (cláusula 5ª: infra é custo da contratante — desperdício aparece na fatura
dela, e volta como problema nosso).

**Views** — Silver e Gold são views (ou materialized views quando o custo de
recomputar justificar). Nunca duplique dado entre camadas sem necessidade.
Sempre filtre por partição nas consultas: `WHERE DATE(_ingestao_timestamp) >= …`.

**Custo**: prefira `SELECT` com colunas explícitas a `SELECT *`; use
`--dry_run`/`dry_run=True` para estimar bytes antes de rodar consulta nova em
volume; evite `ORDER BY` sem `LIMIT` em tabela grande.

## Cloud Storage

Bucket raw: `{project_id}-raw` (`GCS_BUCKET_RAW`). Layout do dado bruto:

```
gs://<bucket>/<fonte>/<entidade>/dt=YYYY-MM-DD/<ingestao_id>.<ext>
```

Lifecycle definido no Terraform, não no console. Bucket sempre com acesso
uniforme e sem exposição pública.

## Secret Manager

Toda credencial (token CCEE, BBCE, Hubspot, TempoOK, usuário Oracle/MySQL) vive
no Secret Manager. Convenção de nome: `alupdata-<fonte>-<campo>`, por exemplo
`alupdata-ccee-api-token`. Leia em runtime; nunca materialize em arquivo, log ou
mensagem de erro. O código nunca recebe o segredo por parâmetro default.

## Identidade e acesso

- Service account por função (ingestão, transformação, Composer), com o mínimo
  necessário: `roles/bigquery.dataEditor` na camada que grava,
  `roles/bigquery.dataViewer` no resto.
- Nada de chave de service account em JSON no repositório. Local usa ADC
  (`gcloud auth application-default login`); CI usa Workload Identity Federation.
- Acesso a bancos internos da Alup (Onda 3) é **read-only** — se um conector
  precisa de escrita na origem, o desenho está errado.

## Composer / Scheduler

- DAGs em `dags/`, sincronizadas para `COMPOSER_BUCKET`.
- Toda task com `retries` e timeout; DAG com `catchup` decidido conscientemente
  (reprocessamento histórico é intencional, nunca acidente de deploy).
- Job leve e periódico pode ser Cloud Scheduler + Cloud Run em vez de Composer —
  Composer custa por hora ligado.

## Terraform

Módulos em `infra/modules/`: `bigquery`, `storage`, `secrets`, `composer`,
`scheduler`, `networking`. Fluxo:

```bash
cd infra
terraform init
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Regras: `plan` revisado antes de qualquer `apply`; backend GCS remoto para o
state (nunca state local commitado); nenhum valor sensível em `.tfvars`
versionado — use Secret Manager e referencie.

## Antes de abrir PR que toca GCP

- [ ] Recurso declarado em `infra/`, não criado a mão
- [ ] Tabela Bronze particionada e clusterizada
- [ ] Consulta nova estimada com dry-run
- [ ] Credencial via Secret Manager, com IAM mínimo
- [ ] `terraform plan` limpo e anexado ao PR
