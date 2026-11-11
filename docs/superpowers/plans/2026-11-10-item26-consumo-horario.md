# Plano — conector `ccee_consumo_horario_perfil_agente` (item 26)

Spec: [`2026-11-10-item26-consumo-horario-design.md`](../specs/2026-11-10-item26-consumo-horario-design.md).
Só começa depois da decisão do Ricardo sobre a janela (spec, seção 7). Janela
assumida aqui: a recomendada (1 mês de prova, depois 3). Padrão do código:
`src/conectores/ccee_consumo_classe_agente.py` e `ccee_geracao_usina.py`.
Branch: `feat/aditivo01-item26`. Teste antes do código em toda tarefa.

## Tarefas

1. **Fixture e teste do conector** (`tests/fixtures/ccee_consumo_horario_perfil_agente_202607.csv`,
   `tests/unit/conectores/test_ccee_consumo_horario_perfil_agente.py`). Fixture
   sintética de poucas linhas, sem dado real de cliente (CNPJ e nomes fictícios).
   Casos: 19 colunas viram o schema; `PERIODO_COMERCIALIZACAO` 1..744 vira
   `data_hora` e `data_referencia`; período fora de 1..744 é inválido; vazio na
   medida vira nulo; janela de 1 mês baixa só o recurso `_AAAAMM`; recurso ainda
   não publicado é ignorado; gzip e encoding misto.
2. **Conector** (`src/conectores/ccee_consumo_horario_perfil_agente.py`):
   subclasse de `CceeCsvCkan` com `dataset`, `recurso_por = "mes"`, schema
   Pydantic e `transformar()`; `bytes_por_lote` de 32 MiB como no
   `ccee_geracao_usina`. Registrar com `@registrar`. Nenhuma credencial.
3. **Guarda de recarga**: não reler mês cuja `versao_publicacao` já está na Bronze
   (consulta a `bronze._execucoes`, não à tabela de 11 GiB/mês). Teste com mês
   já carregado e com mês republicado.
4. **Bronze** (`definitions/bronze/ccee_consumo_horario_perfil_agente.sqlx`):
   `PARTITION BY data_referencia`, `require_partition_filter = TRUE`,
   `CLUSTER BY codigo_carga, submercado, classe_perfil_agente`, colunas técnicas
   `_ingestao_*`, `_fonte`, `_schema_versao`. Append-only.
5. **Silver** (`definitions/silver/ccee_consumo_horario_perfil_agente.sqlx`):
   view com `QUALIFY ROW_NUMBER()` particionando por `data_referencia, data_hora,
   codigo_carga`; assertions `uniqueKey`, `nonNull` e `consumo >= 0`.
6. **Gold** (`consumo_horario_submercado_classe`, `consumo_mensal_carga`):
   tabelas incrementais por mês, lendo a Silver sempre com filtro de partição.
7. **Agendamento** (`infra/modules/scheduler/main.tf`): cron mensal após os
   demais da CCEE, `ultimos_dias = 45`, `cpu = 2`, `memoria = 1Gi`, `timeout`
   conforme decisão 7 da spec. Tabela Bronze e Dataform pelo `infra/`; nenhum
   recurso criado por console. Deploy é do Ricardo.
8. **Documentação**: `docs/dicionario-dados/ccee_consumo_horario_perfil_agente.md`
   (campos, tipos, origem para destino, linhagem, volume real medido), linha no
   `docs/dicionario-dados/README.md` e no controle de horas do aditivo.
9. **Carga de prova** (Ricardo executa): 1 mês em `dev` por janela explícita.
   Registrar tamanho real (`INFORMATION_SCHEMA.TABLE_STORAGE`), vazão (linhas/s),
   unicidade da chave e `maximum_bytes_billed` dos jobs; então estender para 3
   meses e atualizar a spec com os números medidos.

## Fora do plano

Caminho de carga por arquivo (spec, seção 5) e histórico além de 3 meses: só
com a decisão 3 da spec e ADR própria.

## Verificação

`.venv\Scripts\python.exe -m pytest tests/unit/conectores/test_ccee_consumo_horario_perfil_agente.py`,
`ruff`, `bandit`, `pip-audit`, Gitleaks; `python scripts/verifica_atribuicao.py`
em cada mensagem de commit.
