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
| Serviço `alupdata-portal` no Cloud Run, IAP e SA `alupdata-portal` | `infra/modules/portal` |
| Lake `alupdata`, zonas Bronze/Silver/Gold e ativos do Knowledge Catalog, com descoberta desligada | `infra/modules/catalogo` |
| Fluxo `alupdata-onda3` no Cloud Workflows, seu Scheduler e a SA `alupdata-orquestracao` — **só quando `cadeia_onda3` tiver conector** | `infra/modules/orquestracao` |
| Leitura de pessoas por grupo (R01 do RIPD) | `infra/main.tf` |
| Log de auditoria de acesso a dado do BigQuery e do Cloud Storage (R07 do RIPD) | `infra/main.tf` |

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

IAM do Portal ([`portal.md`](portal.md)):

| Identidade | Papel |
|---|---|
| SA `alupdata-portal` | `roles/bigquery.dataViewer` em `bronze`, `silver` e `gold`; `roles/bigquery.jobUser`, `roles/bigquery.resourceViewer` e `roles/bigquery.metadataViewer` no projeto |
| Agente de serviço do IAP | `roles/run.invoker` no serviço `alupdata-portal` — o único invocador |
| Membros de `portal_acesso` | `roles/iap.httpsResourceAccessor` no serviço |

Acesso de pessoas (R01 do RIPD). Os grupos são da Alup e entram pelo `.tfvars`
do ambiente; **com as variáveis vazias, que é o padrão, nenhuma pessoa recebe
papel algum**:

| Variável | Papel |
|---|---|
| `grupo_consumidores` (e-mail do grupo) | `roles/bigquery.dataViewer` em `gold`; `roles/bigquery.jobUser` no projeto |
| `grupo_operacao` (e-mail do grupo) | `roles/bigquery.dataViewer` em `bronze`, `silver` e `gold`; `roles/bigquery.jobUser` no projeto |
| `portal_acesso` (`group:` ou `domain:`) | acesso ao Portal pelo IAP |

> As views da Gold leem Silver e Bronze e não são views autorizadas. Até isso
> ser decidido, quem está só em `grupo_consumidores` vê a Gold, mas a consulta
> falha por falta de acesso às camadas de baixo.

Recurso criado no console não existe: some no próximo `apply`.

IAM da SA de deploy — concedido pelo bootstrap (`infra/bootstrap/`, ADR 015),
um papel por tipo de recurso que o `infra/` declara
(`tests/unit/test_bootstrap.py` confere):

| Escopo | Papel | Para quê |
|---|---|---|
| Projeto | `roles/bigquery.dataOwner` | datasets e o IAM de cada um |
| Projeto | `roles/storage.admin` | bucket raw, o IAM dele e o state do Terraform |
| Projeto | `roles/secretmanager.admin` | secrets vazios e o IAM de cada um |
| Projeto | `roles/run.admin` | Cloud Run Jobs, Portal e o IAM de cada um |
| Projeto | `roles/cloudscheduler.admin` | disparos das ingestões |
| Projeto | `roles/dataform.admin` | repositório, configs e o IAM do repositório |
| Projeto | `roles/iap.admin` | quem passa pelo IAP do Portal |
| Projeto | `roles/monitoring.editor` | canais, alertas e painel |
| Projeto | `roles/logging.configWriter` | métricas de log |
| Projeto | `roles/iam.serviceAccountAdmin` | SAs de ingestão, Dataform e Portal, e o IAM delas |
| Projeto | `roles/iam.serviceAccountUser` | Cloud Run, Scheduler e Dataform agem como essas SAs |
| Projeto | `roles/resourcemanager.projectIamAdmin` | papéis de projeto e log de auditoria |
| Projeto | `roles/serviceusage.serviceUsageConsumer` | agentes de serviço do Dataform e do IAP |
| Repositório do Artifact Registry do ambiente | `roles/artifactregistry.writer` | publicar a imagem |
| Conta de faturamento — da Alup, só com `billing_account` preenchido | *Billing Account Costs Manager* | orçamento |

Quem personifica a SA de deploy: só o WIF do repositório
`nessenergy/Alupdatalake`; em `hml` e `prod`, só job no ambiente do GitHub de
mesmo nome. Não há chave.

## Ambiente `hml`

Homologação das ondas, no custo mínimo (E2). `hml.tfvars` traz
`agendamentos_ativos = false`: não existem os disparos do Cloud Scheduler, que
cobra por job existente, pausado ou não, nem o workflow `diario` do Dataform.
Os Cloud Run Jobs existem e rodam sob demanda:

```bash
gcloud run jobs execute ingestao-bcb-cambio-ptax --region us-central1 --project <projeto-hml>
```

Na janela de homologação de uma onda, `agendamentos_ativos = true` em PR e
deploy `infra` em `hml`; ao fim dela, de volta a `false`.

## Log de auditoria de acesso a dado (R07 do RIPD)

`DATA_READ` e `DATA_WRITE` ficam ligados para `bigquery.googleapis.com` e
`storage.googleapis.com`: toda consulta, leitura de tabela e leitura ou gravação
de objeto no bucket raw deixa registro de quem fez. No BigQuery esse log já vem
ligado por padrão; a declaração em `infra/` o torna explícito. No Cloud Storage
ele só existe por causa dela.

- **Retenção**: a padrão do bucket `_Default` do Cloud Logging, 30 dias. O RIPD
  propõe 1 ano, mas bucket de log dedicado e prazo dependem da política de
  retenção, ainda não aprovada.
- **Custo, da Alup**: o Cloud Logging cobra por GiB gravado acima da franquia
  mensal gratuita do projeto (preço na página de preços do Google Cloud
  Observability). O volume cresce com o número de consultas (ingestões,
  Dataform, Portal e uso da Alup) e de objetos lidos ou gravados no bucket.
  Acompanhe o volume de log do projeto nas primeiras semanas depois do apply.
- **`ADMIN_READ` fica desligado**: registra leitura de metadado e configuração
  (listar datasets, ler schema e IAM), não de dado, e multiplicaria o volume a
  cada navegação no console, compilação do Dataform e varredura do catálogo.
- **Efeito colateral no Cloud Storage**: com o log de acesso a objetos ligado,
  download autenticado pelo navegador em `storage.cloud.google.com` pode
  responder 403. Baixe pelo `gcloud storage cp`.

Quem leu o quê:

```
logName="projects/<projeto>/logs/cloudaudit.googleapis.com%2Fdata_access"
protoPayload.serviceName="bigquery.googleapis.com"
```

## Pré-requisitos (uma vez por ambiente)

São três ambientes, um projeto GCP cada: `dev`, `hml` (homologação das ondas)
e `prod` (ADR 015).

1. **Da Alup**: o projeto criado na organização dela, vinculado à conta de
   faturamento, e os papéis de bootstrap concedidos à ness. no projeto — a
   lista está na ADR 015.
2. **Da ness.**: o bootstrap aplicado (`infra/bootstrap/`, passo a passo em
   [`primeiro-deploy.md`](primeiro-deploy.md) §0). Ele habilita as APIs, cria o
   bucket de state e o repositório do Artifact Registry em `us-central1` (ADR
   011), o **Workload Identity Federation** e a SA de deploy — o deploy **não**
   usa chave JSON de service account (cláusula 8.5).
3. Um ambiente do GitHub com o nome do ambiente e as variáveis abaixo. Os
   valores saem de `terraform output` do bootstrap:

| Variável | Saída do bootstrap | Exemplo |
|---|---|---|
| `GCP_WIF_PROVIDER` | `workload_identity_provider` | `projects/123/locations/global/workloadIdentityPools/github/providers/alupdata` |
| `GCP_DEPLOY_SA` | `service_account_deploy` | `alupdata-deploy@alupar-dev-alupdata.iam.gserviceaccount.com` |
| `TF_STATE_BUCKET` | `bucket_state` | `alupar-dev-alupdata-tfstate` |
| `GCP_REGION` | `region` | `us-central1` |
| `IMAGEM_INGESTAO` | `imagem_ingestao` | `us-central1-docker.pkg.dev/alupar-dev-alupdata/alupdata/cli` (sem tag) |
| `DATAFORM_GIT_TOKEN_VERSAO` | — | `1` (versão do secret `alupdata-dataform-git-token`) |

Em `dev`, `GCP_WIF_PROVIDER` e `GCP_DEPLOY_SA` ficam também como variáveis do
repositório: o quadro (`quadro.yml`) roda sem ambiente do GitHub. Em `hml` e
`prod`, o WIF só aceita token de job que roda no ambiente de mesmo nome.

## Deploy

Workflow **Deploy GCP** (`workflow_dispatch`), escolhendo ambiente e módulo:

- `connectors` → constrói e publica a imagem da CLI (`:<sha completo>` e `:latest`)
- `infra` → exige `image_sha` com SHA completo (40 caracteres hexadecimais minúsculos)
  de imagem já publicada no ambiente; executa `terraform plan` + `apply` com essa tag
- `all` → publica a imagem imutável, aplica Terraform com essa mesma tag e
  depois aplica o SQL versionado

No fluxo `all`, o job Terraform depende explicitamente do job de imagem. Isso
impede o primeiro `apply` de disputar com o primeiro push. O estado guarda a tag
imutável do commit (`GITHUB_SHA`); `latest` permanece apenas como conveniência
operacional e nunca entra no Terraform. `connectors` apenas publica: para usar a
imagem publicada, execute depois `infra` com seu `image_sha`. Em `all`, a entrada
`image_sha` é ignorada.

O workflow rejeita SHA ausente, abreviado ou inválido antes da autenticação de
infraestrutura. Depois, confirma a existência da imagem no Artifact Registry do
ambiente antes de `terraform init/plan/apply`; falta de imagem ou acesso interrompe
o deploy. O Terraform aceita imagem vazia no bootstrap, tag de SHA completo ou
digest `sha256`; rejeita `latest`.

Não há sincronização de DAGs nem dependência de Composer. Cloud Workflows é o
destino de orquestração da Onda 3 (ADR 017), ainda sem implantação comprovada.
A validação local dessas guardas não comprova deploy nem homologação no GCP.

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
