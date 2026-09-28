# ONS — balanço de energia nos subsistemas, horário

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `balanco_energia_subsistema_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_energia_subsistema_ho/BALANCO_ENERGIA_SUBSISTEMA_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, publicada diariamente |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 32.280 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

De onde veio a energia de cada região em cada hora — hidráulica, térmica, eólica, solar — contra quanto ela consumiu e trocou com as vizinhas. É a foto de oferta e demanda por submercado. Pedida pela Alup em 28/09/2026.

## Particularidades

- **Há uma linha "SIN"**, o total do sistema, junto com N, NE, S e SE. Ela fica, fiel à origem; a Silver deixa `submercado` nulo nela, porque SIN não é submercado.
- A sigla vem com espaços à direita (`"N  "`).
- **Carga e intercâmbio podem ser negativos**: a carga chegou a -4.729 MWmed em 2026, e intercâmbio negativo é importação líquida. Geração negativa é recusada.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia` + `instante` (e `hora` na Silver) | DATE + DATETIME |
| `id_subsistema` | `subsistema` | STRING, N/NE/S/SE/SIN |
| `nom_subsistema` | `nome_subsistema` | STRING |
| `val_gerhidraulica` | `geracao_hidraulica_mwmed` | NUMERIC, MWmed |
| `val_gertermica` | `geracao_termica_mwmed` | NUMERIC, MWmed |
| `val_gereolica` | `geracao_eolica_mwmed` | NUMERIC, MWmed |
| `val_gersolar` | `geracao_solar_mwmed` | NUMERIC, MWmed |
| `val_carga` | `carga_mwmed` | NUMERIC, MWmed; pode ser negativa |
| `val_intercambio` | `intercambio_mwmed` | NUMERIC, MWmed; negativo é importação |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim, exceto na linha SIN | `subsistema`, nulo no total do sistema |
| `codigo_usina` | não | dado agregado, sem usina |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante`, `subsistema`) — nenhuma repetida em 2026. Vence a ingestão mais
recente.

## Gold

`gold.balanco_energia_mensal_subsistema` — por mês e subsistema (inclusive SIN): médias da geração por fonte, da carga e do intercâmbio líquido. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → BALANCO_ENERGIA_SUBSISTEMA_{ano}.csv
  → gs://<bucket>-raw/ons/balanco_energia/dt=…/<ingestao_id>.json.gz
    → bronze.ons_balanco_energia     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_balanco_energia   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.balanco_energia_mensal_subsistema
```
