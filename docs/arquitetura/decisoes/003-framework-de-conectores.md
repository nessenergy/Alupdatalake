# ADR 003 — Framework de conectores com runner único

**Status**: aceito · **Data**: 2026-08-25

## Contexto

A Fase 1 prevê 13 conectores em 5 ondas, escritos ao longo de 19 semanas e
entregues a terceiros no handoff. Cada fonte precisa dos mesmos 7 componentes
(cláusula 2ª) e das mesmas garantias: reprocessamento, idempotência, colunas
técnicas, log de execução e ausência de credencial em código.

Se cada fonte virar um script próprio, no fim da Onda 3 existem 13 formas
diferentes de fazer a mesma coisa — e a Onda 4 (governança e handoff) vira
uma reescrita.

## Decisão

`src/core/` é um framework de ingestão. Um conector implementa apenas
`extrair()` e `transformar()`, declarando `fonte`, `entidade` e um schema
Pydantic. O runner em `Conector.ingerir()` cuida do resto:

1. particiona a janela pelo limite da fonte (`max_dias_por_requisicao`);
2. grava o payload cru no GCS **antes** de qualquer parsing;
3. valida registro a registro — inválido é descartado com log, não em silêncio;
4. acrescenta `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`;
5. carrega no Bronze em modo append;
6. registra a execução em `bronze._execucoes`, inclusive quando falha.

Decisões que vêm junto:

- **Ingestão sempre por janela.** `extrair(janela)` é obrigatório; nenhum
  conector decide "hoje" sozinho. Backfill é um parâmetro, não um script novo.
- **Bronze append-only, dedup na Silver** (`QUALIFY ROW_NUMBER()`). Mantém a
  auditoria do que a fonte devolveu em cada execução e simplifica a carga.
- **GCS antes do BigQuery.** Bug de parser reprocessa do raw, sem bater de novo
  numa fonte com rate limit ou retenção curta. O comando
  `alupdata reprocessar-raw` cria nova execução com `modo=REPLAY` e referência
  à ingestão que produziu o objeto original.
- **CLI única** (`alupdata ingerir <conector> --de --ate`), usada igual no
  laptop, no Cloud Run Job e na DAG. Não existe código que só roda em produção.
- **Scaffolding** (`make novo-conector`) gera os 7 componentes esqueletados,
  para que nenhuma fonte chegue à homologação com 5 de 7.

## Consequências

- Um conector novo é código específico da fonte e mais nada; o custo marginal
  cai a cada onda.
- Mudança de política (retry, coluna técnica nova, formato do raw) é feita em
  um lugar e vale para todas as fontes.
- Em troca, o framework precisa acomodar fontes que não são HTTP — bancos
  internos da Onda 3 e planilhas da Onda 4 implementam o mesmo contrato com
  outro `extrair()`; `criar_sessao` fica no conector, não na base.
