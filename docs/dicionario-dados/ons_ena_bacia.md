# ONS — ENA diária por bacia

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ena_bacia_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ena_bacia_di/ENA_DIARIO_BACIAS_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 6.210 linhas (23 bacias × ~270 dias) — lido em 28/09/2026 |

## Por que esta fonte existe no lake

A ENA diz quanta água está chegando, comparada com a média histórica (MLT). Por
subsistema (`ons_ena`) ela esconde onde está chovendo; por bacia, mostra. Par
da EAR por bacia (`ons_ear_bacia`). Pedida pela Alup em 28/09/2026.

## Particularidades

- **O percentual é sobre a média de longo termo, não sobre uma capacidade.**
  Passa de 100 sempre que a afluência está acima da média — chegou a
  **1.048%** em 2026. Só negativo é recusado.
- **Não há subsistema na origem**; `submercado` fica nulo.
- Nenhum campo vazio e nenhuma chave `(bacia, data)` repetida em 2026.
- Um valor da origem vem com 11 casas decimais (`19953.27700000001`, resíduo
  de ponto flutuante); o runner arredonda para as 9 do `NUMERIC`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `nom_bacia` | `bacia` | STRING | trim + maiúsculas; vazio é recusado |
| `ena_data` | `data_referencia` | DATE | primeiros 10 caracteres (já ISO) |
| `ena_bruta_bacia_mwmed` | `ena_bruta_mwmed` | NUMERIC | MWmed |
| `ena_bruta_bacia_percentualmlt` | `ena_bruta_percentual_mlt` | NUMERIC | % da MLT; passa de 100 |
| `ena_armazenavel_bacia_mwmed` | `ena_armazenavel_mwmed` | NUMERIC | MWmed |
| `ena_armazenavel_bacia_percentualmlt` | `ena_armazenavel_percentual_mlt` | NUMERIC | % da MLT; passa de 100 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da ENA |
| `submercado` | **não** | a origem não traz; bacia pode atravessar subsistemas |
| `codigo_usina` | não | ENA é agregada por bacia |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `bacia`). Vence a ingestão mais recente.

## Gold

`gold.afluencia_mensal_bacia` — por mês e bacia: dias com dado, ENA bruta e
armazenável médias (MWmed e % da MLT), mínimo e máximo do percentual bruto.
Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → ENA_DIARIO_BACIAS_{ano}.csv
  → gs://<bucket>-raw/ons/ena_bacia/dt=…/<ingestao_id>.json.gz
    → bronze.ons_ena_bacia     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_ena_bacia   (vigente; QUALIFY por data+bacia, _ingestao_timestamp DESC)
        → gold.afluencia_mensal_bacia
```
