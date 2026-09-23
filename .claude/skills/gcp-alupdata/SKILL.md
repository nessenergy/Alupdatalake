---
name: gcp-alupdata
description: Convenções de GCP do AlupData — BigQuery (datasets Bronze/Silver/Gold, nomenclatura, particionamento, clustering, custo), Cloud Storage, Secret Manager, Cloud Run/Scheduler e Cloud Workflows e os módulos Terraform em infra/. Use ao criar ou alterar dataset, tabela, view, bucket, workflow, job agendado, IAM, secret ou qualquer recurso GCP, e ao escrever ou revisar SQL/Terraform deste repositório.
---

# GCP no AlupData

Para a mecânica dos produtos (sintaxe, flags, APIs), use as skills do Google em
`.claude/skills/google/` — `bigquery-basics`, `google-cloud-storage-basics`,
`gcloud`, `cloud-run-basics`. **Este documento tem precedência sobre elas**:
onde a convenção do projeto e o material do produto divergirem, vale o que está
aqui.

Tudo em GCP, arquitetura Medallion, infraestrutura por Terraform. Recurso criado
à mão no console **não existe** — se não está em `infra/`, some no próximo
`terraform apply` e não sobe para produção.

## Ambientes

Três, um projeto GCP cada: `dev`, `hml` (homologação das ondas) e `prod`
(`infra/variables.tf` valida; ADR 015). Região padrão `us-east1` (Carolina do
Sul) — ver ADR 011, que substitui a 009. Variáveis por ambiente em
`infra/environments/{dev,hml,prod}.tfvars`; `hml` nasce com
`agendamentos_ativos = false` (custo). Nunca aponte código para `prod` por
default — `src/core/config.py` cai em `alupar-dev-alupdata`.

Os IDs foram criados pela Alup em 23/09 e **não seguem um padrão**:
`alupar-dev-alupdata`, `alupar-hm-alupdata` (nome do projeto:
`alupar-hml-alupdata`) e `prod-alupdata`. Use o ID, nunca o nome, e nunca o
padrão deduzido do ambiente.

APIs, bucket de state, Artifact Registry, WIF e SA de deploy vêm do bootstrap
(`infra/bootstrap/`), aplicado pela ness. uma vez por projeto. Papel novo para
a SA de deploy ou API nova entra na lista de lá — os testes de
`tests/unit/test_bootstrap.py` cobram.

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

**Views e tabelas** (ADR 012) — Silver é view. Gold de negócio é tabela,
recarregada inteira a cada execução do Dataform; Gold operacional
(`saude_ingestao`, `volumetria_lake`, `custo_consultas`) segue view, porque os
painéis do Portal precisam de dado atual. Nunca duplique dado entre camadas sem
necessidade.
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

- Service account por função (ingestão, transformação, orquestração), com o mínimo
  necessário: `roles/bigquery.dataEditor` na camada que grava,
  `roles/bigquery.dataViewer` no resto.
- Nada de chave de service account em JSON no repositório. Local usa ADC
  (`gcloud auth application-default login`); CI usa Workload Identity Federation.
- Acesso a bancos internos da Alup (Onda 3) é **read-only** — se um conector
  precisa de escrita na origem, o desenho está errado.

## Cloud Run / Scheduler / Workflows

- Ingestões periódicas usam Cloud Scheduler + Cloud Run Jobs.
- Cloud Workflows é o destino da Onda 3 (ADR 017); não assumir implantação.
- Não há sincronização de DAGs nem configuração de Composer no deploy.
- Toda execução precisa de timeout, política de tentativas e janela explícita;
  reprocessamento histórico é intencional, nunca acidente de deploy.

## Terraform

Módulos em `infra/modules/`: `bigquery`, `storage`, `secrets`, `scheduler`,
`dataform`, `monitoramento` e `portal`. Fluxo:

```bash
cd infra
terraform init -backend-config="bucket=<projeto>-tfstate"   # bucket criado pelo bootstrap
terraform plan  -var-file=environments/dev.tfvars
terraform apply -var-file=environments/dev.tfvars
```

Regras: `plan` revisado antes de qualquer `apply`; backend GCS remoto para o
state, um bucket por projeto (nunca state local commitado — o bootstrap, que
cria esse bucket, é a única raiz com state local, fora do git e copiado para o
bucket depois do apply); nenhum valor sensível em `.tfvars` versionado — use
Secret Manager e referencie.

No workflow de deploy, `all` publica e aplica a imagem de `GITHUB_SHA`;
`connectors` apenas publica. Para `infra`, informar `image_sha` com SHA completo
de uma imagem já publicada no ambiente selecionado. A validação antecede a
autenticação, e a consulta ao Artifact Registry antecede `terraform init/plan`.
Nunca usar `latest` como entrada do Terraform: `imagem_ingestao` aceita apenas
vazio (bootstrap), tag de SHA completo ou digest `sha256`.

Antes de existir o ambiente, validar localmente com `terraform init -backend=false`,
`terraform validate` e os testes; registrar a ausência de plano real e manter a
validação operacional pendente, sem provisionar só para testar o reparo.

## Antes de abrir PR que toca GCP

- [ ] Recurso declarado em `infra/`, não criado a mão
- [ ] Tabela Bronze particionada e clusterizada
- [ ] Consulta nova estimada com dry-run
- [ ] Credencial via Secret Manager, com IAM mínimo
- [ ] Validação local aprovada; quando o ambiente estiver disponível, `terraform plan` revisado e anexado ao PR
