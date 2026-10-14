# Bootstrap de produção (`prod-alupdata`) — plano

> Só documento. Nada foi aplicado no GCP. O que depende do GCP real está marcado **não verificado**.

**Objetivo:** levar `prod-alupdata` ao mesmo estado de `hml`, sem carga de fonte sem credencial e sem ligar nada que gere custo antes da hora.

**Por que agora:** as Ondas 0 e 1 foram aprovadas por escrito em 05/10/2026 (Eduardo Pires). O `docs/status.md` registrava "o bootstrap espera o aceite", e a Alup disse ao Jefferson que `prod-alupdata` "entra depois do aceite, quando a ness. montar o ambiente" (e-mail de 29/09).

**Spec:** [ADR 015](../../arquitetura/decisoes/015-fundacao-do-ambiente.md), [`runbook/primeiro-deploy.md`](../../runbook/primeiro-deploy.md), [`runbook/deploy.md`](../../runbook/deploy.md), [`runbook/credenciais.md`](../../runbook/credenciais.md) §5.

## 1. O que existe e o que falta

| Item | Estado | Fonte |
|---|---|---|
| Projeto `prod-alupdata`, ativo | existe; API do Cloud Run desabilitada | `docs/status.md` (05/10) |
| Seis papéis de bootstrap às contas nominais da ness. | concedidos nos três projetos em 23/09 | `docs/status.md`, A1. **Não verificado** hoje |
| Bootstrap de prod aplicado | **não parece** (há `tfplan-dev` e `tfplan-hml` locais, nenhum de prod). **Não verificado** | `infra/bootstrap/` |
| `infra/bootstrap/environments/prod.tfvars` | existe, com `github_repositorio_id` | arquivo |
| `infra/environments/prod.tfvars` | só projeto, região e ambiente; todos os grupos comentados, ou seja, **nenhum acesso de pessoa** | arquivo |
| Ambiente `prod` do GitHub com as 5 variáveis | **não verificado** | `runbook/deploy.md` |
| Billing export | só em `dev`, e não é movido quando `prod` existir | `runbook/primeiro-deploy.md` |
| Orçamento (`billing_account`) | vazio por padrão, e exige papel na conta de faturamento | `infra/variables.tf`, ADR 015 |

## 2. Decisões antes do primeiro apply

Estas quatro mudam o que se aplica. Nenhuma é minha.

1. **Região.** `us-central1` vale "até o primeiro apply de `prod`; depois, mudar região é migração de dado" (`docs/acoes-humanas.md` §4). A Alup precisa dizer se mantém.
2. **Rotação do token do TempoOK.** É a primeira ação da virada, antes de `prod` receber carga real: o valor novo é gravado pela Alup direto no Secret Manager de `prod`, e o antigo é revogado no fornecedor (`runbook/credenciais.md` §5, ADR 020).
3. **Quem acessa o Portal e os dados em prod.** `runbook/portal.md` diz que em prod só a Alup entra. Falta definir os grupos (`grupo_consumidores`, `grupo_bronze`, `grupo_operacao`, `portal_acesso`) e se a ness. mantém algum acesso de operação.
4. **Custo e agendamento.** `agendamentos_ativos` é `true` por padrão; fontes sem credencial (Hubspot, BBCE, TempoOK) ficam em `conectores_sem_agendamento`, como em hml. O orçamento de US$ 20/mês até novembro e US$ 400/mês depois, informado pela Alup em 01/10, ainda não está no Terraform (#87).

## 3. Passos, em ordem

Cada passo diz quem executa e o que prova que terminou.

| # | Passo | Quem | Prova |
|---|---|---|---|
| 1 | Decidir 2.1 a 2.4 | Ricardo, Alup | respostas por escrito |
| 2 | Conferir os seis papéis de bootstrap em `prod-alupdata` e a API do Cloud Run | ness., leitura | `gcloud projects get-iam-policy`, saída anexada. **Não executado** |
| 3 | Aplicar `infra/bootstrap/` com `environments/prod.tfvars` | ness., conta nominal | `terraform apply` sem erro; saídas anotadas |
| 4 | Criar o ambiente `prod` do GitHub com as variáveis (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `TF_STATE_BUCKET`, `GCP_REGION`, `IMAGEM_INGESTAO`) | ness. | `gh api` lista as variáveis |
| 5 | Preencher `infra/environments/prod.tfvars` (grupos, alertas, `conectores_sem_agendamento`, `billing_account` se houver) e abrir PR | ness. | PR com CI verde, `terraform plan` revisado |
| 6 | Primeiro `Deploy GCP`, módulo `all`, ambiente `prod` | ness., workflow | para no Dataform com `::error::`, esperado (secret do token vazio) |
| 7 | Gravar o token do Dataform e definir `DATAFORM_GIT_TOKEN_VERSAO` | grupo de operação, por variável | segundo deploy (`infra`, com `image_sha`) termina com o Dataform em `SUCCEEDED` |
| 8 | Rotacionar o token do TempoOK e revogar o antigo | Alup grava; ness. confere | `runbook/credenciais.md` §5 marcado |
| 9 | Conferir o `TABLE_STORAGE` e a ACL do `faturamento` | ness. | `gold.custo_consultas` criada; ACL sem concessão extra |
| 10 | Rodar `Conferir cargas` em `prod` | ness., workflow | tabelas existem; **sem carga ainda**, só estrutura |
| 11 | Ligar o Scheduler só das fontes públicas e abrir a janela de aceite | ness. | 3 dias de carga com `SUCESSO` |

## 4. O que não fazer

- **Não aplicar nada antes de 2.1.** Mudar de região depois é migração de dado.
- **Não gravar credencial de BBCE, Hubspot ou TempoOK em prod** antes de o fornecedor entregar o valor correto; o teste de 13/10 em dev mostrou BBCE sem versão e Hubspot com 401.
- **Não ligar o Scheduler** antes dos passos 7 e 9: carga cai em tabela Bronze que ainda não existe.
- **Nada por console**, exceto o que a regra 5 já admite e está documentado: cliente OAuth "Externo" do IAP e a exportação de faturamento.
- **Não conceder papel básico** (`owner`, `editor`) a ninguém.

## 5. Riscos

- **Custo é da Alup** (cláusula 5ª). Prod ligado com agendamento completo gera custo de Scheduler e de BigQuery desde o primeiro dia.
- **IAM do bootstrap:** o `projectIamAdmin` permite escalar; o log de auditoria e o IAM em `infra/bootstrap/main.tf` são a contenção (ADR 015).
- **Propagação de IAM:** o Dataform pode falhar com 403 logo após o primeiro apply; reexecutar o passo (`runbook/primeiro-deploy.md`).
- **Revogação dos seis papéis:** obrigatória na homologação final e no handoff (ADR 015); no handoff, prod fica sem acesso da ness. salvo decisão.

## 6. Perguntas

1. A Alup mantém `us-central1` em produção?
2. Quais grupos da Alup acessam prod (Portal, Gold, Bronze, operação)? A ness. mantém acesso de operação?
3. O orçamento de US$ 20 e US$ 400 entra no Terraform agora? Quem concede o papel na conta de faturamento?
4. Quando a Alup grava o valor novo do token do TempoOK em prod, e quem avisa a ness.?
5. Quer a janela de aceite de prod com agendamento completo ou só as fontes públicas?
