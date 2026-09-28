# ONS — intercâmbio entre subsistemas, horário

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `intercambio_nacional_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/intercambio_nacional_ho/INTERCAMBIO_NACIONAL_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, publicada diariamente |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 25.920 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

Quanto de energia atravessou de uma região para outra, hora a hora, e quanto o ONS tinha programado. Quando o intercâmbio bate no limite de transmissão, o PLD dos submercados se descola — é a explicação física da diferença de preço. Pedida pela Alup em 28/09/2026.

## Particularidades

- Uma linha por hora e par origem→destino (N↔NE, N↔SE, NE↔SE, S↔SE).
- O verificado veio sempre positivo em 2026 (o sentido está no par); o **programado chega a negativo** (-5.507 MWmed). Sinal não é validado.
- O nome do subsistema vem com espaço à esquerda (`" NORTE"`); o lake guarda só a sigla.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia` + `instante` (e `hora` na Silver) | DATE + DATETIME |
| `id_subsistema_origem` | `subsistema_origem` | STRING, N/NE/S/SE |
| `id_subsistema_destino` | `subsistema_destino` | STRING, N/NE/S/SE |
| `val_intercambiomwmed` | `intercambio_mwmed` | NUMERIC, MWmed |
| `val_intercambioprogmwmed` | `intercambio_programado_mwmed` | NUMERIC, MWmed |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | não | o fluxo liga dois submercados; origem e destino têm coluna própria |
| `codigo_usina` | não | dado agregado, sem usina |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante`, `subsistema_origem`, `subsistema_destino`) — nenhuma repetida em 2026. Vence a ingestão mais
recente.

## Gold

`gold.intercambio_mensal_subsistemas` — por mês e par origem→destino: horas, intercâmbio médio e máximo, e o programado médio. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → INTERCAMBIO_NACIONAL_{ano}.csv
  → gs://<bucket>-raw/ons/intercambio_nacional/dt=…/<ingestao_id>.json.gz
    → bronze.ons_intercambio_nacional     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_intercambio_nacional   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.intercambio_mensal_subsistemas
```
