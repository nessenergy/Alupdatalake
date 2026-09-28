# ONS — ENA diária por reservatório

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ena_reservatorio_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ena_reservatorio_di/ENA_DIARIO_RESERVATORIOS_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 41.695 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

Quanta água chega a cada reservatório, contra a média histórica dele. Inclui
as usinas a fio d'água, que não aparecem na EAR (não armazenam). Par da EAR
por reservatório. Pedida pela Alup em 28/09/2026.

## Particularidades

- **Tem subsistema** (`id_subsistema`) e alimenta `submercado`.
- **Sem medição, os campos de ENA vêm vazios**: 269 linhas em 2026. Vazio vira
  nulo e a linha continua válida.
- **O percentual é sobre a MLT e passa de 100 com folga**: até **1.750%** em
  2026, em reservatório pequeno com cheia. Só negativo é recusado.
- Mais de 40 mil linhas por ano parcial: é o maior dos conjuntos hidrológicos
  do Aditivo 01.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `nom_reservatorio` | `reservatorio` | STRING, obrigatório |
| `cod_resplanejamento` | `codigo_reservatorio_planejamento` | STRING |
| `tip_reservatorio` | `tipo_reservatorio` | STRING |
| `nom_bacia` | `bacia` | STRING |
| `nom_ree` | `ree` | STRING |
| `id_subsistema` | `submercado` | STRING, obrigatório, N/NE/S/SE |
| `ena_data` | `data_referencia` | DATE |
| `ena_bruta_res_mwmed` | `ena_bruta_mwmed` | NUMERIC |
| `ena_bruta_res_percentualmlt` | `ena_bruta_percentual_mlt` | NUMERIC |
| `ena_armazenavel_res_mwmed` | `ena_armazenavel_mwmed` | NUMERIC |
| `ena_armazenavel_res_percentualmlt` | `ena_armazenavel_percentual_mlt` | NUMERIC |
| `ena_queda_bruta` | `ena_queda_bruta_mwmed` | NUMERIC |
| `mlt_ena` | `mlt_ena_mwmed` | NUMERIC |

Campo numérico vazio vira nulo; negativo é recusado.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da ENA |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem identifica o reservatório, sem CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `reservatorio`) — nenhuma repetida em 2026.
Vence a ingestão mais recente.

## Gold

`gold.afluencia_mensal_reservatorio` — por mês, subsistema, bacia e
reservatório: dias no mês e dias com medição, ENA bruta média (MWmed e % da
MLT), máximo do percentual, ENA armazenável média e a MLT do reservatório. Sem
KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → ENA_DIARIO_RESERVATORIOS_{ano}.csv
  → gs://<bucket>-raw/ons/ena_reservatorio/dt=…/<ingestao_id>.json.gz
    → bronze.ons_ena_reservatorio     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_ena_reservatorio   (vigente; QUALIFY por data+reservatório)
        → gold.afluencia_mensal_reservatorio
```
