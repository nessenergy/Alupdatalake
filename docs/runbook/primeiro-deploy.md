# Checklist do primeiro deploy no GCP

Use esta lista apenas quando A3 estiver entregue. Ela complementa
[`deploy.md`](deploy.md) e produz as evidências para homologação da Onda 0.

## 1. Pré-condições

- [ ] Projeto, região e conta de faturamento confirmados pela Alup.
- [ ] APIs de BigQuery, Storage, Secret Manager, Cloud Run, Scheduler,
  Artifact Registry, Dataform, Data Lineage e Dataplex habilitadas.
- [ ] Política `gcp.resourceLocations` efetiva da organização Alupar permite
  `us-east1` (ADR 011) — por exemplo `in:us-locations` ou
  `in:us-east1-locations`: `gcloud resource-manager org-policies describe
  constraints/gcp.resourceLocations --project=<projeto> --effective`.
- [ ] Quem liga o billing export combinado: pessoa da Alup com papel *Billing
  Account Costs Manager* ou *Billing Account Administrator* na conta de
  faturamento, **e** papel *BigQuery User* (`roles/bigquery.user`) no projeto
  que hospeda o dataset `faturamento` — o Google exige os dois papéis, um na
  conta de faturamento e outro no projeto.
- [ ] Backend GCS do Terraform criado e configurado.
- [ ] Artifact Registry criado.
- [ ] WIF e service account de deploy configurados.
- [ ] Variáveis `GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `GCP_REGION` e
  `IMAGEM_INGESTAO` presentes no ambiente GitHub `dev`.
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
  Dataform cria as tabelas Bronze e as views Silver/Gold.
- [ ] Ingestões agendadas que dispararem entre as duas execuções falham — a
  tabela Bronze ainda não existe — e são reprocessadas por janela depois que
  o Dataform rodar.
- [ ] Se o passo do Dataform falhar com 403 logo após o primeiro `apply`
  (propagação de IAM), reexecutar o passo.
- [ ] Confirmar aplicação das tabelas Bronze e views Silver/Gold.
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
  (ADR 013) e as views Silver e Gold do Dataform à direita (ADR 012).
- [ ] Conferir `/lake` e `/custo` usando o provedor BigQuery.

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
