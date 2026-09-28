# ONS — CMO semi-horário

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `cmo_tm` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/cmo_tm/CMO_SEMIHORARIO_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Semi-horária, publicada diariamente |
| Histórico | Um CSV por ano, desde 2020 |
| Credencial | nenhuma |
| Volume verificado (2026) | 51.072 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

O Custo Marginal de Operação: quanto custa produzir o próximo MWh em cada subsistema. É a base do PLD, e compará-los mostra quando o preço de liquidação se afasta do custo. Pedida pela Alup em 28/09/2026.

## Particularidades

- **O passo é de 30 minutos** (minutos 00 e 30): a chave é o instante inteiro, como no constrained-off. A Silver expõe também `hora`.
- Chegou a **R$ 7.854,60/MWh** em 2026. Só negativo é recusado.
- Série só desde 2020.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia + instante` | DATE + DATETIME |
| `id_subsistema` | `submercado` | STRING, N/NE/S/SE |
| `val_cmo` | `cmo_reais_mwh` | NUMERIC, R$/MWh |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem não traz CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante`, `submercado`). Vence a ingestão mais recente.

## Gold

`gold.cmo_mensal_submercado` — por mês e submercado: meias-horas, CMO médio, mínimo e máximo. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → CMO_SEMIHORARIO_{ano}.csv
  → gs://<bucket>-raw/ons/cmo_semi_horario/dt=…/<ingestao_id>.json.gz
    → bronze.ons_cmo_semi_horario     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_cmo_semi_horario   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.cmo_mensal_submercado
```
