# CCEE — energia de reserva (EER)

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `energia_reserva_liquidacao` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=energia_reserva_liquidacao` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2024` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal, mercado inteiro**: uma linha por `MES_REFERENCIA`, sem agente |
| Volume verificado | 7 linhas em 2026, em 14/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia (B1) |
| Credencial | nenhuma |

Ordem 5 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
A liquidação da energia de reserva (EER) que o B1 nomeia em Mercado de
Energia. Mesma forma da exposição financeira: uma linha por mês, valores do
mercado inteiro em R$, sem agente e sem submercado.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `EFEITO_CCEAR_DISP_CER` | `efeito_ccear_disponibilidade_cer` | NUMERIC | R$; vazio → NULL |
| `REPASSE_USUARIOS_RESERVA` | `repasse_usuarios_reserva` | NUMERIC | R$; vazio → NULL |
| `AJUSTE` | `ajuste` | NUMERIC | R$; vazio → NULL; **pode ser negativo** |
| `VALOR_TOTAL_LIQUID` | `valor_total_liquidado` | NUMERIC | R$; vazio → NULL |

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

`gold.encargos_setoriais_mensal` — ESS e EER lado a lado, mês a mês, com
`FULL OUTER JOIN` (as duas séries fecham em datas diferentes). Sem KPI
(ADR 012).

## Qualidade e observações

- Valores em R$ com ponto decimal; sem separador de milhar.
- `valor_total_liquidado` não pode ser negativo (faixa da Silver, issue
  #110) — é o total já líquido.
- `AJUSTE` **pode ser negativo** (visto no arquivo real, ex.: -3.547.179,17
  em junho/2026): é um ajuste sobre o efeito CCEAR, não um montante, e por
  isso fica de fora da faixa de não-negatividade.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → energia_reserva_liquidacao_{ano}.csv
  → gs://<bucket>-raw/ccee/energia_reserva/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_energia_reserva   (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_energia_reserva (QUALIFY por mês, versao_publicacao DESC)
        → gold.encargos_setoriais_mensal
```
