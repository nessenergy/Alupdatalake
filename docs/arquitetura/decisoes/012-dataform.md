# ADR 012 — Dataform para o SQL das três camadas

**Status**: aceito · **Data**: 2026-09-10 · **Revisada** em 2026-09-11
(materialização da Gold; Gold na Fase 1) · **Substitui** a decisão de
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
- **Silver**: `type: "view"`, com o mesmo SQL de hoje — a deduplicação segue
  na Silver com `QUALIFY ROW_NUMBER()`, e o componente 03 ("View Silver") fica
  cumprido ao pé da letra. Materializar uma Silver tem dois gatilhos, e só
  eles: consulta direta frequente fora do Dataform, ou uma Silver — tipicamente
  dimensão comum — lida por tantas Gold na mesma execução que o painel de custo
  (ADR 007) mostre o peso. O BigQuery não reaproveita o resultado de uma view
  entre consultas: cada Gold que a lê refaz a deduplicação.
- **Gold de negócio**: `type: "table"`, recarregada inteira a cada execução.
  Em view, cada consulta do BI refaria a deduplicação da Silver sobre a Bronze
  inteira — a partição por data de ingestão não poda quando o filtro é a data
  do negócio —, e o custo de BigQuery é da Alup. Materializada, a cadeia roda
  uma vez por execução, depois das *assertions*: dado que falha na Silver não
  chega à Gold. Materializar a Gold foi consenso na reunião de revisão com o
  Google (G1).
  - **`incremental` só quando o painel de custo pedir.** Gold incremental sobre
    Silver em view continua varrendo a Bronze inteira; só compensa com a Silver
    também incremental, e aí a deduplicação vira `MERGE` por chave — que
    sobrescreve sem olhar prioridade, o que quebra fontes em que o registro
    certo não é o mais recente (medição da CCEE).
  - **Equivalência contratual.** O componente 04 da cláusula 2.2 ("View Gold")
    passa a ser lido como "camada Gold publicada pelo Dataform, materializada
    como tabela" — como a ADR 014 fez com Tag Templates = *aspect types*. A
    equivalência precisa de aceite da Alup por escrito antes da homologação da
    Onda 1.
- **Gold operacional** (`saude_ingestao`, `volumetria_lake`,
  `custo_consultas`): continua `type: "view"`. Lê `bronze._execucoes` ou
  `INFORMATION_SCHEMA.JOBS_BY_PROJECT` — tabelas pequenas — e alimenta os
  painéis de saúde e de custo do Portal (ADRs 006 e 007). Materializada uma vez
  por dia, o painel de saúde mostraria a falha de hoje amanhã.
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

### Descrições de tabela e coluna

Decidido em 11/09. O assistente do espaço de trabalho do Dataform pode ser
usado como **rascunho** de descrição de tabela e coluna, sob três condições:

1. **Só entra por PR.** O rascunho gerado na interface é levado para o branch;
   nada é commitado pela interface (ver *Deploy e execução*).
2. **Revisada no PR é `curada`.** A descrição que passou por revisão de PR
   recebe o *aspect* `origem = curada` (ADR 014) e conta como documentação do
   componente 07. O que nunca passou por PR segue `automatica`.
3. **Sem dado pessoal na amostra.** Para sugerir, o assistente lê uma amostra
   real da tabela. Ele não é apontado para tabela com dado pessoal (negócios
   do Hubspot, Portal Alup) antes de o RIPD estar assinado (ADR 011).

A habilitação do recurso no projeto é declarada em `infra/` (regra 5).

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

## Gold na Fase 1

Acrescentado em 2026-09-11, com as respostas da Alup ao
[Questionário de Gaps](../../questionario-gaps.md).

A Alup respondeu que não existe KPI formalizado (A5, A6) e que defini-los **não
é objetivo desta fase**: o objetivo agora é ter os dados organizados e a
estrutura do datalake funcionando. Os indicadores serão definidos no projeto de
front da Fase 2.

### O que a Gold entrega nesta fase

- **Tabelas prontas para consumo, por domínio** — os domínios de dado do B1,
  cada um com seu data owner. A Gold consolida e agrega; não calcula indicador
  com fórmula de negócio.
- **Na granularidade de A7**, que depende do dado: usina, para o portfólio da
  Alup; usina, estado ou submercado, para o SIN. A Gold não agrega acima disso —
  agregar no consumo é fácil, desagregar é impossível.
- **Com unidade explícita (D6)**: energia em MWh ou MWmed; valor em R$, milhares
  de R$ ou milhões de R$. A unidade vai no nome da coluna, como já faz
  `carga_media_mwmed`, e na descrição (componente 07).
- **R$/MWh com duas casas decimais (D7).** O arredondamento é o último passo:
  somas e médias partem do valor sem arredondar, e a Silver guarda a precisão
  da fonte.
- **Com as dimensões comuns da Silver** (usina, submercado, agente CCEE e
  período de apuração), nos dois calendários que a Alup usa, mês civil e mês
  CCEE (D4). A sigla interna das empresas (D1) entra como atributo da dimensão
  de usina; o de-para entre sigla, CEG e os nomes da CCEE e do ONS é trabalho
  da dimensão, não de cada Gold.

### KPIs ficam para a Fase 2

Indicador — fórmula, meta, comparação entre coligadas — é construído no front
da Fase 2 (Looker Studio ou fronts internos, G1), lendo a Gold. Se um indicador
precisar voltar ao lake depois, entra como Gold nova, com dono (B1) e fórmula
por escrito.

### Leitura do componente 04

O resumo do contrato descreve o componente 04 da cláusula 2.2 ("View Gold")
como "regras de negócio complexas e KPIs consolidados"
([resumo do contrato](../../contrato/resumo-contrato.md)). Sem KPI nesta fase,
por decisão da própria Alup, o componente passa a ser lido como "tabelas Gold
de consumo por domínio, publicadas pelo Dataform e materializadas".

Essa leitura exige **aceite da Alup por escrito**, no mesmo documento que aceita
a Gold materializada (acima, *Equivalência contratual*), antes da homologação
da Onda 1. Sem esse aceite, a medição pode cobrar KPI que a Alup declarou fora
da fase.

## Consequências

- Linhagem entre camadas e teste de dado deixam de ser código nosso.
- A migração toca: as 19 definições de `sql/` (6 Bronze, incluindo
  `_execucoes`; 5 Silver; 8 Gold), `tests/unit/test_sql.py`,
  `scripts/novo_conector.py` (o esqueleto passa a gerar `.sqlx`), `Makefile`,
  `.github/workflows/deploy.yml`, a skill de conector, o template de issue de
  conector e o runbook de deploy.
- A ADR 002 (monorepo) continua valendo, ao custo de duas entradas a mais na
  raiz.
- A revisão de 11/09 toca a migração em `feat/dataform`: as cinco Gold de
  negócio (`cambio_mensal`, `carga_mensal_submercado`, `funil_comercial`,
  `inflacao_mensal`, `parque_gerador`) passam a `type: "table"`; a expectativa
  de `tests/unit/test_sql.py`, que hoje exige `view` em toda Gold, passa a
  distinguir negócio de operacional; e o esqueleto de `scripts/novo_conector.py`
  gera a Gold como `table`.
- A migração é feita **antes do primeiro `apply`**: com o ambiente vazio, não há
  view publicada por `deploy_views.py` para conviver com as do Dataform.
- A seção *Gold na Fase 1* não reescreve as cinco Gold de negócio existentes:
  conferir unidade no nome da coluna e arredondamento de R$/MWh entra na
  homologação de cada fonte.
