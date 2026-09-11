# Checklist do primeiro deploy no GCP

Use esta lista apenas quando A3 estiver entregue. Ela complementa
[`deploy.md`](deploy.md) e produz as evidências para homologação da Onda 0.

## 1. Pré-condições

- [ ] Projeto, região e conta de faturamento confirmados pela Alup.
- [ ] APIs de BigQuery, Storage, Secret Manager, Cloud Run, Scheduler,
  Artifact Registry, Dataform, Data Lineage e Dataplex habilitadas.
- [ ] Organização da Alupar sem restrição de localização que barre `us-east1`
  (ADR 011): `gcloud resource-manager org-policies describe
  constraints/gcp.resourceLocations --project=<projeto> --effective` não pode
  listar apenas locais do Brasil.
- [ ] Quem liga o billing export combinado: pessoa da Alup com papel *Billing
  Account Costs Manager* ou *Billing Account Administrator* na conta de
  faturamento.
- [ ] Backend GCS do Terraform criado e configurado.
- [ ] Artifact Registry criado.
- [ ] WIF e service account de deploy configurados.
- [ ] Variáveis `GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `GCP_REGION` e
  `IMAGEM_INGESTAO` presentes no ambiente GitHub `dev`.
- [ ] Destinatários de alerta e `billing_account` confirmados.
- [ ] `make all`, Gitleaks e `terraform validate` aprovados no commit candidato.

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
  detalhado) apontando para o dataset `faturamento` (ADR 007, adendo de
  10/09). Dataset regional só recebe dado a partir do dia em que o export é
  ligado. O export traz **todos** os projetos pagos pela mesma conta: o
  dataset bruto não é exposto ao Portal.
- [ ] Confirmar aplicação das tabelas Bronze e views Silver/Gold.
- [ ] Guardar logs dos três passos.

## 4. Smoke test ponta a ponta

- [ ] Executar BCB/PTAX para uma janela curta já conhecida.
- [ ] Confirmar JSONL gzip no bucket raw.
- [ ] Confirmar linha na tabela Bronze.
- [ ] Confirmar deduplicação e dimensões comuns na Silver.
- [ ] Confirmar agregação na Gold.
- [ ] Confirmar execução `FONTE` em `bronze._execucoes`.
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
