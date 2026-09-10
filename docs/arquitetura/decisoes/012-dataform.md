# ADR 012 — Dataform para o SQL das três camadas

**Status**: aceito · **Data**: 2026-09-10 · **Substitui** a decisão de
transformação da [ADR 004](004-sql-puro-e-orquestracao.md)

## Contexto

A ADR 004 deixou dbt de fora da Fase 1 e registrou o custo assumido: *teste de
dado e linhagem automática ficam por nossa conta*. Registrou também que
reavaliar a ferramenta de transformação seria um ADR novo, não um remendo.

A revisão arquitetural com o Google (G1) recomendou o **Dataform**, o
equivalente gerenciado do dbt dentro do GCP. Ele devolve exatamente o que a
ADR 004 abriu mão:

- *assertions* — testes de dado executados junto com a transformação;
- linhagem Bronze → Silver → Gold registrada automaticamente no Knowledge
  Catalog (ADR 014), que também cataloga os repositórios e o código do Dataform;
- nenhum servidor para operar: o Dataform executa como jobs do BigQuery, e o
  custo é o das consultas que ele dispara.

## Decisão

### Projeto Dataform na raiz do monorepo

`workflow_settings.yaml` e `definitions/{bronze,silver,gold}/` ficam na raiz do
repositório, ao lado de `src/` e `infra/`. `definitions/` substitui `sql/`.

A raiz não é preferência: **o Dataform lê o projeto apenas a partir da raiz do
repositório Git** — projeto em subdiretório não é suportado (pedido em aberto
na [issue dataform-co/dataform#2028](https://github.com/dataform-co/dataform/issues/2028)).

Alternativas descartadas:

- **repositório separado para o Dataform** — revoga a ADR 002 e espalha os 7
  componentes de uma mesma fonte por dois repositórios, com PR em ambos;
- **Dataform CLI no CI, sem repositório Dataform no GCP** — preserva um
  subdiretório, mas perde o agendamento nativo, a interface e o registro dos
  ativos do Dataform no catálogo, e põe Node dentro de uma imagem que é só
  Python.

### O que cada camada vira

- **Bronze**: o DDL passa a ser `operations` com `hasOutput: true` —
  `CREATE TABLE IF NOT EXISTS`, particionada e clusterizada (regra 4). A carga
  continua sendo do executor (ADR 003); o Dataform não escreve no Bronze.
- **Silver e Gold**: `type: "view"`, com o mesmo SQL de hoje — a deduplicação
  segue na Silver com `QUALIFY ROW_NUMBER()`. Materializar (`table` ou
  `incremental`) acontece caso a caso, quando o painel de custo (ADR 007)
  mostrar necessidade; é mudança de configuração, não de arquitetura.
- **Parâmetros**: os marcadores `${projeto}` e `${regiao}` que
  `scripts/deploy_views.py` substitui passam a vir de `workflow_settings.yaml`
  (`defaultProject`, `defaultLocation` e `vars`).

### Qualidade de dado

*Assertions* do Dataform são o portão: unicidade da chave de deduplicação,
obrigatoriedade e faixa de valores. Falha de *assertion* aparece na execução,
não depois.

O **pytest continua sendo o componente 5** — a cláusula 2.2 o cita
nominalmente. Ele segue cobrindo conectores e executor, e o CI passa a rodar
também `dataform compile`.

### Deploy e execução

- `scripts/deploy_views.py` e `make deploy-views` são **removidos**. Todo o SQL
  do projeto passa a ter um único mecanismo de deploy: *release configuration*
  do Dataform compilando a partir da `main`.
- Uma *workflow configuration* executa o projeto depois da janela diária de
  ingestão, com agendamento declarado no Terraform. Na Onda 3 o Airflow passa
  a invocar o Dataform ao fim dos conectores, com dependência real em vez de
  horário (a decisão de orquestração da ADR 004 segue valendo).
- O repositório Dataform é ligado ao GitHub com credencial no Secret Manager
  (regra 2). Ninguém faz commit pela interface do Dataform: alteração entra
  por PR, como qualquer outra.
- Repositório, *release* e *workflow configurations* e o IAM do agente de
  serviço do Dataform (jobs e escrita nos datasets, leitura do secret do Git)
  ficam em `infra/` (regra 5).
- O Node entra **só no CI e no ambiente de desenvolvimento**, para compilar.
  A imagem dos conectores continua só Python.

## Consequências

- Linhagem entre camadas e teste de dado deixam de ser código nosso.
- A migração toca: as 19 definições de `sql/` (6 Bronze, incluindo
  `_execucoes`; 5 Silver; 8 Gold), `tests/unit/test_sql.py`,
  `scripts/novo_conector.py` (o esqueleto passa a gerar `.sqlx`), `Makefile`,
  `.github/workflows/deploy.yml`, a skill de conector, o template de issue de
  conector e o runbook de deploy.
- A ADR 002 (monorepo) continua valendo, ao custo de duas entradas a mais na
  raiz.
- A migração é feita **antes do primeiro `apply`**: com o ambiente vazio, não há
  view publicada por `deploy_views.py` para conviver com as do Dataform.
