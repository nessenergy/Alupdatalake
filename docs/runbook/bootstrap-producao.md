# Bootstrap de produção (`prod-alupdata`)

Plano: [`2026-10-14-bootstrap-producao.md`](../superpowers/plans/2026-10-14-bootstrap-producao.md). Detalhe de cada comando: [`primeiro-deploy.md`](primeiro-deploy.md) §0 e [`deploy.md`](deploy.md). Este runbook é a ordem e as provas. Nada daqui foi executado.

**Estado de partida (30/10):** projeto ativo, seis papéis de bootstrap presentes, API do Cloud Run desabilitada, bootstrap não aplicado, ambiente `prod` do GitHub sem variáveis.

**Região:** `us-central1` (ADR 023). Mudar depois do primeiro apply é migração de dado.

## Antes de começar

- [ ] Alup avisada de que `prod` vai receber o apply e de que o agendamento nasce desligado.
- [ ] Quem executa faz `gcloud auth application-default login --account=<conta nominal da ness.>` e confere a ADC (`primeiro-deploy.md` §0).
- [ ] Perguntas do PR sobre orçamento e janela de aceite respondidas antes do passo 10; não bloqueiam os passos 1 a 9.

## Ordem de execução

| # | Passo | Quem | Como | Prova |
|---|---|---|---|---|
| 1 | Conferir os seis papéis de bootstrap e a API do Cloud Run | ness. (conta nominal) | Console do Google Cloud, IAM e APIs e serviços do projeto `prod-alupdata` | seis papéis listados |
| 2 | Aplicar `infra/bootstrap/` (workspace `prod`, `environments/prod.tfvars`) | ness. (conta nominal) | `primeiro-deploy.md` §0: `plan`, revisar, `apply`, `output` | saídas anotadas: bucket de state, pool `github`, SA `alupdata-deploy` sem chave |
| 3 | Guardar a cópia do state no bucket | ness. | `primeiro-deploy.md` §0 | arquivo em `bootstrap/terraform.tfstate` do bucket |
| 4 | Gravar as variáveis no ambiente `prod` do GitHub: `GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`, `TF_STATE_BUCKET`, `GCP_REGION`, `IMAGEM_INGESTAO` | ness. | tabela de `deploy.md`; saídas do passo 2 | as cinco aparecem no ambiente |
| 5 | Depois do merge do PR, rodar **Deploy GCP**, ambiente `prod`, módulo `all` | ness. (workflow) | Actions, Run workflow | `plan` revisado; para no Dataform com `::error::` (esperado, token vazio) |
| 6 | Conferir o que o `apply` criou | ness. | lista abaixo, no Console | todos os itens marcados |
| 7 | Gravar o token do Dataform no secret `alupdata-dataform-git-token` e definir `DATAFORM_GIT_TOKEN_VERSAO` | grupo de operação da ness. | Console do Secret Manager, "Nova versão"; o valor nunca passa por terminal, chat nem arquivo. Depois, a variável no ambiente do GitHub | segundo deploy (`infra`, com `image_sha`) termina com o Dataform em `SUCCEEDED` |
| 8 | Conferir `TABLE_STORAGE` e a ACL do dataset `faturamento` | ness. | Console do BigQuery | `gold.custo_consultas` criada; ACL sem concessão extra |
| 9 | Rodar **Conferir cargas** em `prod` | ness. (workflow) | Actions | tabelas existem; sem carga, só estrutura |
| 10 | Decidir ligar o agendamento | Ricardo, com a Alup | PR que troca `agendamentos_ativos` para `true` em `prod.tfvars`, com a data da janela no comentário, e novo deploy | 3 dias de carga com `SUCESSO` |

Credencial de BBCE, Hubspot ou qualquer fonte sem o valor correto do fornecedor não entra em `prod`. Valor de segredo só pelo console do Secret Manager, por membro dos grupos de `gravacao_segredos`, nunca por terminal.

## Depois do passo 5, conferir

- [ ] Datasets `bronze`, `silver`, `gold`, `qualidade` e `faturamento`, e o bucket raw, em `us-central1`.
- [ ] Cloud Run Jobs dos conectores existem. **Nenhum job no Cloud Scheduler** e nenhum workflow `diario` do Dataform (`agendamentos_ativos = false`).
- [ ] `hubspot_negocios` e `bbce_curva_forward` existem para execução manual, sem agendamento.
- [ ] IAM: só os grupos de `prod.tfvars` (`operacao-datalake@ness.com.br` e `alup.alertas@alupar.com.br`); nenhuma pessoa, nenhum papel básico (`owner`, `editor`).
- [ ] Alertas configurados para os dois e-mails de `emails_alerta`.
- [ ] Portal no ar, acesso só do grupo `portal_acesso`. O login (cliente OAuth "Externo" e IAP) é o passo manual já admitido pela regra 5, descrito em [`portal.md`](portal.md).
- [ ] Orçamento **não criado** (`billing_account` vazio) até a pergunta 1 do PR.
- [ ] 403 do Dataform logo após o apply é propagação de IAM: repetir o passo.

## Custo mensal estimado

Ordem de grandeza, **não medida em prod**. Premissas:

- BigQuery sob demanda a US$ 6,25 por TiB (valor do registro de custo de 27/10 em `docs/status.md`).
- Dataform diário medido em dev: cerca de 0,021 TiB por dia comum, ou US$ 0,13/dia, ou US$ 4/mês; mantido igual em prod.
- Cloud Scheduler: US$ 0,10 por job por mês, cerca de 25 jobs, sem descontar a franquia gratuita da conta.
- Secret Manager: cerca de US$ 0,06 por versão ativa por mês, até uns 30 secrets com uma versão; secret sem versão não cobra.
- Artifact Registry: poucos GB de imagem a US$ 0,10 por GB. Cloud Run, Monitoring e logs dentro da franquia, sem instância mínima.
- Armazenamento desprezível nos primeiros meses, pois não há carga real.

| Fase | O que está ligado | Estimativa |
|---|---|---|
| Bootstrap (agendamento desligado) | estrutura, secrets, imagem, Portal em escala zero | US$ 1 a 5/mês |
| Janela de aceite só com fontes públicas | acima, mais Scheduler e Dataform diário | US$ 8 a 12/mês |
| Agendamento completo | idem, mais cargas e consultas do Portal | US$ 10 a 20/mês, a medir |

O orçamento informado pela Alup (US$ 20/mês até novembro, US$ 400/mês depois, em 01/10) comporta as três fases. O módulo de custo declara o teto em BRL e o alerta depende de papel na conta de faturamento, que é da Alup: ver perguntas do PR. Vira medição quando `prod` tiver uma semana de faturamento.

## Reverter

Antes de haver carga, o bootstrap e o `infra/` de `prod` se corrigem por `plan` e `apply` no mesmo workspace. Não destruir o bootstrap (o pool de WIF fica 30 dias em exclusão reversível). Os seis papéis só são revogados na homologação final (ADR 015).
