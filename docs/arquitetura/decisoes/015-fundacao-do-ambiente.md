# ADR 015 — Fundação do ambiente: três ambientes, bootstrap pela ness., chave gerenciada pelo Google

**Status**: aceito · **Data**: 2026-09-11 · **Revisada**: 2026-09-11 ·
**Complementa** a [ADR 011](011-regiao-us-east1.md)

> **Revisão de 11/09.** A primeira versão desta ADR, no PR #106, fixava dois
> ambientes, `dev` e `prod`, e deixava o bootstrap dos projetos com a TI da
> Alup. A revisão do PR #120 reforçou essa fronteira. As respostas da Alup ao
> Questionário de Gaps, recebidas em 11/09 e confirmadas pelo líder do projeto,
> mudaram os dois pontos. Pela **E4**, são três ambientes: `dev`, `hml` e
> `prod`, como alinhado com o Google em 10/09. Pela **E6**, a ness. faz o
> bootstrap de cada projeto. A **E2**, teto de custo, condiciona o desenho de
> `hml`. A decisão sobre criptografia não muda.

## Contexto

A reunião de revisão arquitetural com o Google, em 10/09 (G1), deixou três
pontos da fundação em aberto. As respostas de 11/09 fecharam dois deles e
acrescentaram uma restrição de custo.

- **Ambientes.** O Google sugeriu separar desenvolvimento, homologação e
  produção em projetos distintos. A ADR 011 e o `infra/` previam só `dev` e
  `prod`. Na E4, a Alup adotou os três, e a homologação das ondas passa a
  acontecer em `hml`.
- **Quem constrói.** Saíram da reunião tarefas para o Google: "criar a
  fundação de dados" e "estruturar os projetos e a esteira de CI/CD". Pela
  regra 5, recurso que não está em `infra/` não existe. Um Terraform paralelo,
  ou recurso criado pelo console, deixaria o ambiente com duas fontes de
  verdade. Na E6, a Alup atribuiu à ness. também o bootstrap de cada projeto:
  APIs, bucket de state do Terraform, repositório do Artifact Registry,
  Workload Identity Federation e conta de serviço de deploy.
- **Quem cria o projeto.** A ness. não pode criar projeto na organização da
  contratante. Criar os projetos e vinculá-los à conta de faturamento continua
  com a Alup. A conta de faturamento é aberta via QI Network (E1), com
  previsão para 18/09.
- **Custo (E2).** A Alup paga a nuvem, com teto de US$ 20/mês até novembro e de
  até US$ 400/mês a partir de meados de novembro. Três projetos não podem
  triplicar o custo, e `hml` precisa ser barato.
- **Criptografia.** Foi levantada a opção de criptografar o dado com chave
  própria da Alupar (CMEK).

## Decisão

### Três ambientes: `dev`, `hml` e `prod`

Há um projeto GCP por ambiente, na organização da Alupar:

| Ambiente | Para quê |
|---|---|
| `dev` | desenvolvimento da ness. e primeiro `apply` |
| `hml` | homologação das ondas pela Alup |
| `prod` | produção |

O mesmo `infra/` serve os três. Há um `.tfvars` por ambiente em
`infra/environments/`, e `variable "environment"` aceita os três valores. O
workflow de deploy oferece a opção `hml`, e a organização passa a assinar o
GitHub Team, com que os ambientes do GitHub (`dev`, `hml`, `prod`) passam a
funcionar e cada um carrega as variáveis do seu projeto.

**`hml` no custo mínimo.** Em `hml`, `agendamentos_ativos = false` é o padrão.
Com isso, não existem os disparos do Cloud Scheduler, que é cobrado por job
existente, pausado ou não, nem o workflow diário do Dataform, que consulta o
BigQuery todo dia. Continuam disponíveis, sob demanda, os Cloud Run Jobs, o
Portal e a execução do Dataform pelo deploy. Na janela de homologação de uma
onda, a variável vai para `true` em PR e volta para `false` ao fim. Os demais
recursos de `hml` custam por uso ou por volume armazenado, e o uso ali é só o
da homologação. Nos três ambientes, o Artifact Registry guarda só as dez
imagens mais recentes.

### Bootstrap pela ness., como código

A divisão fica assim:

- **A Alup** cria os três projetos na organização dela, vincula cada um à
  conta de faturamento (E1) e concede à ness., em cada projeto, os papéis da
  seção seguinte. `dev` vem primeiro, porque o primeiro `apply` depende dele.
- **A ness.** aplica `infra/bootstrap/` uma vez por projeto. É uma raiz
  Terraform separada, com state local, que:
  - habilita as APIs que o `infra/` usa;
  - cria o bucket de state em `us-east1` e o repositório do Artifact Registry;
  - cria o pool e o provedor de WIF, que só aceitam token do repositório
    `nessenergy/Alupdatalake`. Em `hml` e `prod`, só aceitam token de job que
    roda no ambiente do GitHub de mesmo nome;
  - cria a conta de serviço de deploy, sem chave, com os papéis que o
    `infra/` exige.

  As saídas do bootstrap viram as variáveis do ambiente no GitHub. Daí em
  diante, tudo o que existe no projeto é declarado no `infra/` e aplicado pelo
  workflow: IAM, contas de serviço de execução, datasets, buckets, Dataform,
  Knowledge Catalog, agendamentos, Portal e alertas.

Isso reverte a fronteira de 04/09 (A3,
[issue #55](https://github.com/nessenergy/Alupdatalake/issues/55)) e a revisão
do PR #120. A regra 5 continua valendo: o bootstrap está em `infra/bootstrap/`,
não em comandos de console.

### Papéis que a Alup concede à ness. em cada projeto

São seis papéis predefinidos, concedidos no projeto. Nenhum é papel básico:

| Papel | Para quê, no bootstrap |
|---|---|
| `roles/serviceusage.serviceUsageAdmin` | habilitar as APIs e usar o próprio projeto como projeto de cota das chamadas |
| `roles/storage.admin` | criar o bucket de state e guardar nele a cópia do state do bootstrap |
| `roles/artifactregistry.admin` | criar o repositório de imagens e dar à conta de deploy a escrita só nele |
| `roles/iam.workloadIdentityPoolAdmin` | criar o pool e o provedor de WIF |
| `roles/iam.serviceAccountAdmin` | criar a conta de serviço de deploy e permitir que o GitHub a personifique |
| `roles/resourcemanager.projectIamAdmin` | conceder à conta de deploy os papéis de projeto que o `infra/` exige |

Os papéis são concedidos às contas da ness. que aplicam o bootstrap, de
preferência por um grupo. Nenhum dos seis dá leitura de dataset do BigQuery
nem de segredo. O `storage.admin` lê objeto em qualquer bucket do projeto: no
bootstrap, só existe o de state; depois do primeiro `apply`, existe também o
bucket raw.

O papel mais sensível é o `projectIamAdmin`, porque quem concede papel de
projeto pode conceder qualquer papel, inclusive a si. Ele é inevitável: é
exatamente o que o bootstrap faz, e é também o que a conta de deploy precisa
para aplicar o IAM do `infra/`. Duas coisas contêm esse poder. Toda concessão
fica no log de auditoria de atividade administrativa, que o Google mantém
sempre ligado. E o IAM da conta de deploy está versionado em
`infra/bootstrap/main.tf`.

Terminado o bootstrap de um projeto, a Alup pode revogar os seis papéis e
concedê-los de novo quando o bootstrap mudar, por exemplo com uma API nova ou
um papel novo para a conta de deploy. Toda mudança passa por PR. Na
homologação final e no handoff, a revogação é obrigatória, conforme a política
de retenção.

Fica fora desta lista o acesso de operação depois do bootstrap. Um exemplo é
gravar o token do Dataform no secret `alupdata-dataform-git-token`. Esse acesso
entra no `infra/` por variável, como o acesso de pessoas (R01).

**Conta de deploy.** Os papéis estão em `infra/bootstrap/main.tf`
(`papeis_deploy`), um por tipo de recurso que o `infra/` declara, conferidos
por teste. A publicação da imagem é concedida só no repositório do Artifact
Registry do ambiente. Duas consequências foram aceitas:

- `roles/secretmanager.admin` também lê o valor dos segredos, e não há papel
  predefinido que crie segredo e configure o IAM dele sem ler. A conta só é
  usável pelos workflows do repositório, via WIF.
- O orçamento (`billing_account` preenchido) exige que a Alup conceda
  *Billing Account Costs Manager* à conta de deploy **na conta de
  faturamento**, e não no projeto.

### Alternativa descartada: Owner durante o bootstrap, reduzido depois

A alternativa foi descartada pelos seguintes motivos:

- Para produção, o Google orienta não conceder papel básico quando há
  alternativa, e aqui há: os seis papéis acima.
- Owner para conta de fora da organização só pode ser concedido pelo console.
  Isso cria um passo manual na entrada e outro na saída, e nada verifica que a
  redução aconteceu.
- O bootstrap não é aplicado uma vez só. São três projetos, e ele volta a ser
  aplicado quando o `infra/` exigir API ou papel novo. Seriam várias janelas de
  Owner.
- Owner inclui o que o bootstrap nunca faz, como apagar o projeto e ler
  qualquer dado.

A lista específica não é uma barreira absoluta, porque o `projectIamAdmin` já
permite escalar. O ganho é outro: o pedido fica delimitado e auditável, e
qualquer escalada vira uma concessão explícita, registrada no log.

Também foi considerada, e não adotada, a condição do IAM que limita quais
papéis podem ser concedidos (`modifiedGrantsByRole`). Ela aceita no máximo dez
papéis, a conta de deploy precisa de treze, e o Google desaconselha incluir
papéis que alteram IAM, o que vale para vários da lista.

### Criptografia com chave gerenciada pelo Google

Não há CMEK. BigQuery, Cloud Storage e os demais serviços usam a criptografia
em repouso padrão, com chave gerenciada pelo Google.

Chave própria perdida ou desabilitada torna o dado ilegível, sem recuperação,
e a troca periódica da chave passaria a ser uma operação da Alup. Esse risco
pesou mais do que a restrição adicional de acesso que a chave própria daria.

## Consequências

- **No `infra/`:**
  - há três `.tfvars`, e `environment` aceita `hml`;
  - `agendamentos_ativos` desliga, em `hml`, o Scheduler e o workflow diário
    do Dataform;
  - o state vai para o bucket do próprio projeto: `backend "gcs"` com
    configuração parcial, e o nome do bucket vem de `TF_STATE_BUCKET`;
  - `infra/bootstrap/` é novo, com um workspace de state local por projeto e
    uma cópia no bucket de state depois do `apply`.
- **A3 muda de conteúdo.** Para cada ambiente, a Alup entrega o projeto
  criado, vinculado ao faturamento e com os papéis concedidos à ness. O
  primeiro `apply` depende disso em `dev`.
- **Três verificações na organização**, antes do bootstrap:
  - `iam.allowedPolicyMemberDomains`: se restringe domínios, a Alup precisa
    admitir as contas da ness., senão a concessão dos papéis falha;
  - `iam.workloadIdentityPoolProviders`: se restringe emissores, precisa
    admitir `https://token.actions.githubusercontent.com`;
  - `gcp.resourceLocations`, como já previsto na ADR 011.
- **A conferir no primeiro `apply`.** A conta de deploy recebe
  `serviceusage.serviceUsageConsumer` para gerar os agentes de serviço do
  Dataform e do IAP. A documentação do Google não nomeia a permissão exigida.
  Se houver 403 nesse passo, o bootstrap passa a conceder
  `serviceusage.serviceUsageAdmin`.
- **Orçamento.** O orçamento padrão por ambiente do módulo de monitoramento
  (R$ 500/mês) é maior que o teto da E2 até novembro. O valor por ambiente
  precisa ser acertado com a Alup antes de ser preenchido.
- **Criptografia.** Nenhum recurso de KMS entra em `infra/`. Adotar CMEK
  depois exige ADR própria.

## Fontes

Documentação do Google Cloud, conferida em 11/09:

- [Service Usage — controle de acesso](https://docs.cloud.google.com/service-usage/docs/access-control)
- [Cloud Storage — papéis do IAM](https://docs.cloud.google.com/storage/docs/access-control/iam-roles)
- [Artifact Registry — controle de acesso](https://docs.cloud.google.com/artifact-registry/docs/access-control)
- [Workload Identity Federation com pipelines de deploy](https://docs.cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines)
- [Criar contas de serviço](https://docs.cloud.google.com/iam/docs/service-accounts-create) e [gerenciar acesso a contas de serviço](https://docs.cloud.google.com/iam/docs/manage-access-service-accounts)
- [Papéis do IAM — visão geral (papéis básicos e Owner fora da organização)](https://docs.cloud.google.com/iam/docs/roles-overview)
- [Limitar quais papéis podem ser concedidos](https://docs.cloud.google.com/iam/docs/setting-limits-on-granting-roles)
- [BigQuery — controle de acesso](https://docs.cloud.google.com/bigquery/docs/access-control)
- [Secret Manager — controle de acesso](https://docs.cloud.google.com/secret-manager/docs/access-control)
- [IAP no Cloud Run](https://docs.cloud.google.com/run/docs/securing/identity-aware-proxy-cloud-run)
- [Preços do Cloud Scheduler](https://cloud.google.com/scheduler/pricing)
