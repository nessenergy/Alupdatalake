# ONS — intercâmbio do SIN com outros países, horário

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `intercambio_internacional_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/intercambio_internacional_ho/INTERCAMBIO_INTERNACIONAL_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, publicada diariamente |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 12.864 linhas (Argentina e Uruguai) — lido em 28/09/2026 |

## Por que esta fonte existe no lake

Se o Brasil está exportando ou importando energia, de/para qual país, hora a hora. Sinal de sobra ou falta no sistema. Pedida pela Alup em 28/09/2026.

## Particularidades

- **O sinal é o sentido do fluxo**: positivo é exportação, negativo é importação (-500 MWmed da Argentina em janeiro de 2026). Sinal não é validado.
- O nome do país vem com espaços à direita (`"Argentina                     "`); o trim vive no validador.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia` + `instante` (e `hora` na Silver) | DATE + DATETIME |
| `nom_paisdestino` | `pais` | STRING, sem espaços |
| `val_intercambiomwmed` | `intercambio_mwmed` | NUMERIC, MWmed; negativo é importação |
| `val_intercambioprogmwmed` | `intercambio_programado_mwmed` | NUMERIC, MWmed |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | não | fluxo do SIN inteiro com outro país |
| `codigo_usina` | não | dado agregado, sem usina |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante`, `pais`) — nenhuma repetida em 2026. Vence a ingestão mais
recente.

## Gold

`gold.intercambio_internacional_mensal` — por mês e país: horas exportando e importando, o líquido médio e, separadas, a exportação e a importação médias — para um mês com as duas não se anular em zero. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → INTERCAMBIO_INTERNACIONAL_{ano}.csv
  → gs://<bucket>-raw/ons/intercambio_internacional/dt=…/<ingestao_id>.json.gz
    → bronze.ons_intercambio_internacional     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_intercambio_internacional   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.intercambio_internacional_mensal
```
