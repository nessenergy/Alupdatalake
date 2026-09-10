# ADR 004 — SQL versionado sem dbt; Cloud Run Jobs antes de Composer

**Status**: aceito · **Data**: 2026-08-25 · **Parcialmente substituído** em
2026-09-10: a decisão de transformação passou para a
[ADR 012](012-dataform.md) (Dataform); a de orquestração segue valendo.

## Contexto

Duas escolhas de infraestrutura que são caras de reverter no meio do
cronograma: como transformar (Silver/Gold) e como orquestrar.

## Decisão — transformação em SQL puro

Silver e Gold são arquivos `.sql` versionados em `sql/`, aplicados por
`make deploy-views` (`scripts/deploy_views.py`), idempotente:
`CREATE TABLE IF NOT EXISTS` no Bronze, `CREATE OR REPLACE VIEW` nas demais.
O projeto **não** adota dbt na Fase 1.

Razões: o contrato não pede dbt; o handoff (Onda 4) fica com uma peça a menos
para operar; e o volume da Fase 1 é de views, não de um DAG de transformação
com centenas de modelos.

Custo assumido: teste de dado e linhagem automática — que o dbt daria de graça
— ficam por nossa conta. A linhagem é o componente 07 (dicionário de dados) e
Dataplex entra na Onda 4.

## Decisão — Cloud Run Jobs + Cloud Scheduler antes de Composer

A orquestração das Ondas 1 e 2 é Cloud Run Job disparado por Cloud Scheduler,
executando a mesma CLI. Cloud Composer entra na Onda 3, quando aparecerem
dependências reais entre pipelines (sistemas internos alimentando views Gold
que cruzam fontes).

Razões: Composer cobra por ambiente ligado, 24×7, e o custo de infra é da
contratante (cláusula 5ª) — pagar isso desde a semana 3 para agendar cinco
extrações diárias não se justifica. A CLI única torna a migração barata: a DAG
passa a chamar o mesmo comando.

## Consequências

- `dags/` só recebe conteúdo na Onda 3; até lá o agendamento vive no Terraform
  (`infra/modules/scheduler`).
- Toda transformação é legível por quem sabe SQL, sem ferramenta intermediária.
- Se o número de views crescer muito além do previsto, reavaliar dbt vira um
  ADR novo — não um remendo.
