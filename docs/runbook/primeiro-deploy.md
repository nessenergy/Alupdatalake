# Checklist do primeiro deploy no GCP

Use esta lista quando A3 estiver entregue para o ambiente — projeto criado,
vinculado ao faturamento e papéis de bootstrap concedidos à ness. (ADR 015).
Ela complementa [`deploy.md`](deploy.md) e produz as evidências para
homologação da Onda 0. O primeiro ambiente é `dev`; `hml` e `prod` seguem a
mesma lista, com o `.tfvars` e o ambiente do GitHub de cada um.

## 0. Bootstrap do projeto (ness.)

Uma vez por projeto, antes de qualquer deploy. O que ele cria existe porque
está em `infra/bootstrap/` (regra 5).

Da Alup, antes:

- [ ] Projeto `<ambiente>` criado na organização da Alupar e vinculado à conta
  de faturamento.
- [ ] Papéis concedidos à ness. no projeto (ADR 015):
  `roles/serviceusage.serviceUsageAdmin`, `roles/storage.admin`,
  `roles/artifactregistry.admin`, `roles/iam.workloadIdentityPoolAdmin`,
  `roles/iam.serviceAccountAdmin` e `roles/resourcemanager.projectIamAdmin`.
- [ ] Políticas da organização conferidas: `iam.allowedPolicyMemberDomains`
  admite as contas da ness.; `iam.workloadIdentityPoolProviders`, se
  restringir emissores, admite `https://token.actions.githubusercontent.com`.

Da ness.:

```bash
gcloud auth application-default login
cd infra/bootstrap
terraform init
terraform workspace select -or-create <ambiente>
terraform plan -var-file=environments/<ambiente>.tfvars -out=tfplan
terraform apply tfplan
terraform output
```

- [ ] Conferir no `plan`: as APIs, o bucket `<projeto>-tfstate` em
  `us-east1`, o repositório `alupdata`, o pool `github` e o provedor
  `alupdata` com a condição do repositório, e a SA `alupdata-deploy` sem
  chave.
- [ ] Se o projeto veio sem as APIs padrão e o `apply` falhar ao habilitar
  serviços, habilitar antes as duas de que o Terraform depende e reaplicar:
  `gcloud services enable serviceusage.googleapis.com cloudresourcemanager.googleapis.com --project=<projeto>`.
  As duas estão na lista do bootstrap.
- [ ] Guardar a cópia do state no bucket que ele criou:
  `gcloud storage cp terraform.tfstate.d/<ambiente>/terraform.tfstate gs://<projeto>-tfstate/bootstrap/terraform.tfstate`.
  O state não contém segredo — a SA de deploy não tem chave.
- [ ] Criar o ambiente `<ambiente>` no GitHub e gravar as variáveis com as
  saídas ([`deploy.md`](deploy.md), pré-requisitos). Em `dev`, também as
  variáveis de repositório do quadro.
- [ ] Recomendado: preencher `github_repositorio_id` no `.tfvars` com o ID
  numérico do repositório e reaplicar — o Google recomenda exigir o ID, que
  não se reutiliza, contra repositório homônimo.
- [ ] Avisar a Alup de que os papéis de bootstrap podem ser revogados (ADR 015).

> Não destrua o bootstrap para recriá-lo: pool de WIF apagado fica em exclusão
> reversível por 30 dias, e o ID não pode ser reutilizado nesse período.
> Mudança é `plan` e `apply` no mesmo workspace.

## 1. Pré-condições

- [ ] Bootstrap do projeto aplicado (§0).
- [ ] Grupos Google de consumidores e de operação, e quem acessa o Portal,
  informados pela Alup — ou deliberadamente vazios (R01 do RIPD).
- [ ] Política `gcp.resourceLocations` efetiva da organização Alupar permite
  `us-east1` (ADR 011) — por exemplo `in:us-locations` ou
  `in:us-east1-locations`: `gcloud resource-manager org-policies describe
  constraints/gcp.resourceLocations --project=<projeto> --effective`.
- [ ] Quem liga o billing export combinado: pessoa da Alup com papel *Billing
  Account Costs Manager* ou *Billing Account Administrator* na conta de
  faturamento, **e** papel *BigQuery User* (`roles/bigquery.user`) no projeto
  que hospeda o dataset `faturamento` — o Google exige os dois papéis, um na
  conta de faturamento e outro no projeto.
- [ ] Variáveis `GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `TF_STATE_BUCKET`,
  `GCP_REGION` e `IMAGEM_INGESTAO` presentes no ambiente GitHub `dev`, com as
  saídas do bootstrap.
- [ ] Destinatários de alerta e `billing_account` confirmados.
- [ ] `make all`, Gitleaks e `terraform validate` aprovados no commit candidato.
- [ ] Token do GitHub *fine-grained*, restrito a `nessenergy/Alupdatalake`,
  permissão *Contents: Read-only*, pronto para ser gravado — ele só é escrito
  no secret `alupdata-dataform-git-token` depois do primeiro `apply`, quando o
  secret passa a existir (item 3, abaixo).

## 2. Plano e IAM

- [ ] Rodar `terraform plan` com `dev.tfvars` e guardar a saída no PR.
- [ ] Confirmar que a identidade de ingestão só edita o Bronze.
- [ ] Confirmar IAM do bucket raw, secrets e jobs no próprio recurso.
- [ ] Confirmar que nenhum secret possui versão criada pelo Terraform.
- [ ] Confirmar que o plano não concede papel a `user:`, e que `group:` e
  `domain:` só aparecem com as variáveis de acesso preenchidas.
- [ ] Confirmar `google_project_iam_audit_config` para BigQuery e Cloud
  Storage (R07) e o serviço `alupdata-portal` com `iap_enabled = true`.
- [ ] Revisar recursos destrutivos ou substituições antes do apply.

## 3. Implantação

- [ ] Executar o workflow `Deploy GCP`, módulo `all`, ambiente `dev`.
- [ ] Confirmar imagem publicada com tag igual ao SHA completo.
- [ ] Confirmar que Terraform usa a mesma tag imutável.
- [ ] **No mesmo dia do apply**, a Alup liga no console o billing export
  (*Faturamento → Exportação de faturamento → BigQuery*: custo padrão e
  detalhado) apontando para o dataset `faturamento` do **primeiro ambiente
  aplicado (`dev`)** (ADR 007, adendo de 10/09). Dataset regional só recebe
  dado a partir do dia em que o export é ligado. O export traz **todos** os
  projetos pagos pela mesma conta: o dataset bruto não é exposto ao Portal.
  O export **não é movido** quando `prod` existir: o Cloud Billing não
  transfere histórico entre datasets, e mover o destino dividiria a série. A
  camada F2 lê deste dataset; o `faturamento` dos demais ambientes fica
  vazio.
- [ ] Conferir a ACL do dataset `faturamento`: a conta
  `billing-export-bigquery@system.gserviceaccount.com` como *owner* e nenhuma
  concessão além das herdadas do projeto — o export traz o faturamento de
  todos os projetos pagos pela conta.
- [ ] O primeiro `Deploy GCP` (`all`) cria o secret `alupdata-dataform-git-token`
  vazio e para no passo do Dataform com a mensagem `::error::` — esperado, não
  é falha do deploy.
- [ ] `gcloud secrets versions add alupdata-dataform-git-token --data-file=-`
  com o token do GitHub do item 1, definir `DATAFORM_GIT_TOKEN_VERSAO` no
  ambiente do GitHub e reexecutar o deploy (módulo `infra`): agora o passo do
  Dataform cria as tabelas Bronze, as views Silver e a Gold.
- [ ] Ingestões agendadas que dispararem entre as duas execuções falham — a
  tabela Bronze ainda não existe — e são reprocessadas por janela depois que
  o Dataform rodar.
- [ ] Se o passo do Dataform falhar com 403 logo após o primeiro `apply`
  (propagação de IAM), reexecutar o passo.
- [ ] Confirmar aplicação das tabelas Bronze, das views Silver e da Gold.
- [ ] Guardar logs dos três passos.

> Uma vez definido, `DATAFORM_GIT_TOKEN_VERSAO` precisa continuar definido em
> todos os ambientes: deixá-lo vazio faz o próximo `terraform plan` destruir o
> repositório e as duas configs (`main` e `diario`).

## 4. Smoke test ponta a ponta

- [ ] Executar BCB/PTAX para uma janela curta já conhecida.
- [ ] Confirmar JSONL gzip no bucket raw.
- [ ] Confirmar linha na tabela Bronze.
- [ ] Confirmar deduplicação e dimensões comuns na Silver.
- [ ] Confirmar agregação na Gold.
- [ ] Confirmar execução `FONTE` em `bronze._execucoes`.
- [ ] Confirmar no Knowledge Catalog a linhagem da tabela
  `bronze.bcb_cambio_ptax`: a origem `custom:bcb.cambio_ptax` à esquerda
  (ADR 013) e a view Silver e a tabela Gold do Dataform à direita (ADR 012).
- [ ] Conferir `/lake` e `/custo` usando o provedor BigQuery, pela URL de
  `terraform output url_portal`.
- [ ] Abrir o Portal com uma conta fora de `portal_acesso`: o IAP recusa.
- [ ] Encontrar no Cloud Logging o registro `data_access` da consulta e do
  objeto raw do smoke test (R07).

## 5. Replay e recuperação

- [ ] Executar `alupdata reprocessar-raw` para o objeto criado no smoke test.
- [ ] Confirmar que nenhuma chamada foi feita ao BCB durante o replay.
- [ ] Confirmar `modo=REPLAY` e `origem_ingestao_id` em `_execucoes`.
- [ ] Confirmar nova linha Bronze e ausência de duplicação lógica na Silver.
- [ ] Simular uma falha controlada e conferir o alerta.

## 6. Fechamento

- [ ] Exportar evidências sem dado real de cliente.
- [ ] Registrar custo e bytes processados do smoke test.
- [ ] Remover dados de teste conforme a cláusula 8.3.
- [ ] Atualizar `docs/status.md` com commit, data e resultados reais.
- [ ] Submeter o pacote à homologação; até o aceite, manter o estado como
  “implantado em dev, aguardando homologação”.
