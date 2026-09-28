# ONS — EAR diária por bacia

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ear_bacia_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_bacia_di/EAR_DIARIO_BACIAS_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Um CSV por ano, desde 2000 |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado (2026) | 6.210 linhas (23 bacias × ~270 dias), 267 KB — lido em 28/09/2026 |

## Por que esta fonte existe no lake

A EAR por subsistema (`ons_ear`) diz quanto o Sudeste tem armazenado, não
**em qual rio**. A mesma média de subsistema pode esconder uma bacia cheia e
outra vazia — e é a bacia que determina o que cada usina consegue gerar.
Pedida pela Alup em 28/09/2026.

## Particularidades

- **Não há subsistema na origem.** A unidade é a bacia (`nomecurto`); uma
  bacia pode atravessar subsistemas, então `submercado` fica nulo em vez de
  inventado.
- **O percentual passa de 100.** Em 2026 a bacia do **Paraguaçu** ficou acima
  da própria capacidade máxima em 176 dias (até 154%), e o percentual bate com
  `verificada / máxima`. É dado real: a regra 0-100 do `ons_ear` (subsistema)
  não vale aqui, e só negativo é recusado. Parnaíba passou de 100 em 2 dias.
- **O número de bacias muda com o tempo:** 18 em 2000, 23 em 2026. Bacia
  nova aparece sem aviso; a Gold agrupa pelo nome, sem lista fixa.
- **Nenhum campo vazio** em 2000 e 2026, e nenhuma chave `(bacia, data)`
  repetida em 2026.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `nomecurto` | `bacia` | STRING | trim + maiúsculas; vazio é recusado |
| `ear_data` | `data_referencia` | DATE | primeiros 10 caracteres (já ISO) |
| `ear_max_bacia` | `ear_max_mwmes` | NUMERIC | capacidade máxima, MWmês |
| `ear_verif_bacia_mwmes` | `ear_verificada_mwmes` | NUMERIC | armazenado verificado, MWmês |
| `ear_verif_bacia_percentual` | `ear_verificada_percentual` | NUMERIC | percentual da capacidade máxima; pode passar de 100 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da EAR |
| `submercado` | **não** | a origem não traz; bacia pode atravessar subsistemas |
| `codigo_usina` | não | EAR é agregada por bacia |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `bacia`). Vence a ingestão mais recente — o
ONS revisa dado publicado, como no `ons_ear`.

## Gold

`gold.armazenamento_mensal_bacia` — por mês e bacia: dias com dado, capacidade
máxima no fim do mês, e o percentual médio, mínimo, máximo e **no último dia
do mês** (o número que se compara mês contra mês). Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → EAR_DIARIO_BACIAS_{ano}.csv
  → gs://<bucket>-raw/ons/ear_bacia/dt=…/<ingestao_id>.json.gz
    → bronze.ons_ear_bacia     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_ear_bacia   (vigente; QUALIFY por data+bacia, _ingestao_timestamp DESC)
        → gold.armazenamento_mensal_bacia
```
