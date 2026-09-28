# CCEE — encargo de reserva (CONER)

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `reserva_encargo` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=reserva_encargo` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 23, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 2 linhas de exemplo na fixture; a origem trouxe 8 linhas em 2026 (série desde 2023) — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O custo da energia de reserva (CONER) rateado entre os agentes: quanto foi pago, quanto ficou retido em fundo de garantia, e o custo administrativo/financeiro/tributário da própria CCEE na operação da câmara. Pedido pela Alup em 28/09/2026.

## Particularidades

- **Série mensal, mercado inteiro**: uma linha por `MES_REFERENCIA`, sem agente e sem submercado — mesma forma do ESS (`ccee_encargo_ess`) e do EER (`ccee_energia_reserva`).
- Delimitado por `;`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE, primeiro dia do mês |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `ENCARGO_ENERGIA_RESERVA` | `encargo_energia_reserva` | NUMERIC, R$; vazio → NULL |
| `TOTAL_PAGAMENTO_LIQ_ER` | `total_pagamento_liquido_er` | NUMERIC, R$; vazio → NULL |
| `FUNDO_GARANTIA_OPER_CONTR_ER` | `fundo_garantia_operacional_contratos_er` | NUMERIC, R$; vazio → NULL |
| `TOTAL_RECEITA_RETIDA_CONER` | `total_receita_retida_coner` | NUMERIC, R$; vazio → NULL |
| `CUSTO_ADIMN_FIN_TRIB_CCEE` | `custo_administrativo_financeiro_tributario_ccee` | NUMERIC, R$; vazio → NULL |
| `SALDO_EFETIVO_CONER` | `saldo_efetivo_coner` | NUMERIC, R$; vazio → NULL |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do `MES_REFERENCIA` |
| `submercado` | não | a origem não publica submercado |
| `codigo_usina` | não | ver campos acima |
| `agente_ccee` | ver campos | |
| `periodo_apuracao` | sim | derivado de `data_referencia` na Silver |
| `periodo_apuracao_ccee` | sim | `AAAA-MM`, como a CCEE declara |

## Deduplicação

Chave natural: (`periodo_apuracao_ccee`). Vence a publicação mais recente (`versao_publicacao`,
`last_modified` do recurso no CKAN — ADR 016, opção B).

## Gold

`gold.reserva_encargo_mensal` — passa os valores do mês e acrescenta o acumulado do ano civil de `encargo_energia_reserva` e `total_pagamento_liquido_er` (`SUM(...) OVER`). Sem KPI (ADR 012); nenhuma coluna divide série por série (ADR 012, adendo de 27/09) — a razão fica reservada a `indicadores_mensais`.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → reserva_encargo_<ano>
  → gs://<bucket>-raw/ccee/reserva_encargo/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_reserva_encargo     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_reserva_encargo   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.reserva_encargo_mensal
```
