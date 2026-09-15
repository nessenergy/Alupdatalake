# CCEE — exposição financeira mensal

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `exposicao_financeira_mensal` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=exposicao_financeira_mensal` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2023` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal, mercado inteiro**: uma linha por `MES_REFERENCIA`, sem agente |
| Volume verificado | 7 linhas, 968 bytes em 2026, em 14/09/2026 |
| Encoding | ASCII — não há texto, só números |
| Dono do dado (Alup) | Letícia Ferreira — Risco e Compliance (B1) |
| Credencial | nenhuma |

Ordem 2 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
É a **menor fonte do lake**. Sem agente, sem submercado; o que ela responde é
quanto o mercado de curto prazo (MCP) ficou exposto e quanto disso foi
coberto.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `EXCEDENTE_FINANCEIRO` | `excedente_financeiro` | NUMERIC | vazio → NULL |
| `EXCEDENTE_FINANCEIRO_POSITIVO` | `excedente_financeiro_positivo` | NUMERIC | vazio → NULL |
| `TOTAL_RECURSO_DISPONIVEL` | `total_recurso_disponivel` | NUMERIC | vazio → NULL |
| `TOTAL_EXPOSICAO_NEGATIVA` | `total_exposicao_negativa` | NUMERIC | vazio → NULL |
| `COBERTURA_EXPOSICAO_NEGATIVA` | `cobertura_exposicao_negativa` | NUMERIC | vazio → NULL |
| `TOTAL_EXPOSICAO_NEGATIVA_REM` | `total_exposicao_negativa_remanescente` | NUMERIC | vazio → NULL |
| `TOTAL_EXPOSICAO_NEGATIVA_LIQ` | `total_exposicao_negativa_liquidada` | NUMERIC | vazio → NULL |
| `TOTAL_RECURSO_DISPONIVEL_EF_ANT` | `total_recurso_disponivel_ef_anterior` | NUMERIC | vazio → NULL |
| `TOTAL_RECURSO_COMPENSACAO_EF_N` | `total_recurso_compensacao_ef` | NUMERIC | vazio → NULL |
| `RESERVA_ALIVIO_ESS` | `reserva_alivio_ess` | NUMERIC | vazio → NULL |

Todos os valores são em R$, com ponto decimal na origem. Colunas técnicas do
Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | total do mercado, sem submercado |
| `codigo_usina` | não | total do mercado, sem ativo |
| `agente_ccee` | não | total do mercado, sem agente |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`). Vence a **publicação mais recente**
(`versao_publicacao`), e a hora da leitura só desempata leituras da mesma
publicação — opção B da ADR 016.

## Gold

`gold.exposicao_mercado_mensal` — exposição negativa, cobertura, remanescente
e liquidada em R$, mês a mês, mais `fracao_coberta`. **`fracao_coberta` é
aritmética de leitura, não indicador de negócio** (ADR 012): ninguém definiu
meta para ela.

## Qualidade e observações

- Valores em R$ com ponto decimal; sem separador de milhar.
- O significado exato de `TOTAL_RECURSO_DISPONIVEL_EF_ANT` (`EF_ANT`) e
  `TOTAL_RECURSO_COMPENSACAO_EF_N` (`EF_N`) **não está documentado pela CCEE
  no catálogo**. Os nomes do lake ficam próximos da origem por isso, em vez de
  arriscar uma tradução errada; a dúvida vai ao dono do domínio (B3: 3 dias
  úteis).

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → exposicao_financeira_mensal_{ano}.csv
  → gs://<bucket>-raw/ccee/exposicao_financeira/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_exposicao_financeira   (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_exposicao_financeira (QUALIFY por mês, versao_publicacao DESC)
        → gold.exposicao_mercado_mensal
```
