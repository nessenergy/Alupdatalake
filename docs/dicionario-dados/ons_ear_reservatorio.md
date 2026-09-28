# ONS — EAR diária por reservatório

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ear_reservatorio_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_reservatorio_di/EAR_DIARIO_RESERVATORIOS_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Um CSV por ano, desde 2000 |
| Credencial | nenhuma |
| Volume verificado (2026) | 20.444 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

O nível mais fino da EAR: quanto cada reservatório tem, e quanto ele pesa na
bacia, no subsistema e no SIN. É o que separa o reservatório grande, que move
o agregado, do pequeno, que não move. Pedida pela Alup em 28/09/2026.

## Particularidades

- **Tem subsistema** (`id_subsistema`, N/NE/S/SE) e alimenta `submercado`.
  Reservatório que contribui para outro subsistema a jusante traz também
  `id_subsistema_jusante`; em 18.561 das 20.444 linhas esse par vem vazio.
- **Reservatório sem medição vem com os campos de EAR vazios**: 2.421 linhas em
  2026, tipicamente "Reservatório sem usina". Vazio vira nulo e a linha
  continua válida — ausência, não erro. Os totais dessas linhas vêm `0.0`.
- **O percentual passa de 100**: até **182%** em 2026. Só negativo é recusado.
- As oito colunas `val_contribear*` são a participação do reservatório nos
  agregados, como fração (0 a 1).
- Arquivo em UTF-8 (conferido nos bytes em 28/09); a extração aceita
  ISO-8859-1 linha a linha, caso algum ano venha diferente.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `nom_reservatorio` | `reservatorio` | STRING, obrigatório |
| `cod_resplanejamento` | `codigo_reservatorio_planejamento` | STRING |
| `tip_reservatorio` | `tipo_reservatorio` | STRING |
| `nom_bacia` | `bacia` | STRING |
| `nom_ree` | `ree` | STRING |
| `id_subsistema` | `submercado` | STRING, obrigatório, N/NE/S/SE |
| `id_subsistema_jusante` | `subsistema_jusante` | STRING |
| `ear_data` | `data_referencia` | DATE |
| `ear_reservatorio_subsistema_proprio_mwmes` | `ear_proprio_mwmes` | NUMERIC |
| `ear_reservatorio_subsistema_jusante_mwmes` | `ear_jusante_mwmes` | NUMERIC |
| `earmax_reservatorio_subsistema_proprio_mwmes` | `ear_max_proprio_mwmes` | NUMERIC |
| `earmax_reservatorio_subsistema_jusante_mwmes` | `ear_max_jusante_mwmes` | NUMERIC |
| `ear_reservatorio_percentual` | `ear_percentual` | NUMERIC |
| `ear_total_mwmes` | `ear_total_mwmes` | NUMERIC |
| `ear_maxima_total_mwmes` | `ear_max_total_mwmes` | NUMERIC |
| `val_contribearbacia` / `val_contribearmaxbacia` | `contribuicao_ear_bacia` / `contribuicao_ear_max_bacia` | NUMERIC |
| `val_contribearsubsistema` / `val_contribearmaxsubsistema` | `contribuicao_ear_subsistema` / `contribuicao_ear_max_subsistema` | NUMERIC |
| `val_contribearsubsistemajusante` / `val_contribearmaxsubsistemajusante` | `contribuicao_ear_subsistema_jusante` / `contribuicao_ear_max_subsistema_jusante` | NUMERIC |
| `val_contribearsin` / `val_contribearmaxsin` | `contribuicao_ear_sin` / `contribuicao_ear_max_sin` | NUMERIC |

Campo numérico vazio vira nulo; negativo é recusado.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da EAR |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem identifica o reservatório, sem CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `reservatorio`) — nenhuma repetida em 2026.
Vence a ingestão mais recente.

## Gold

`gold.armazenamento_mensal_reservatorio` — por mês, subsistema, bacia e
reservatório: dias no mês e **dias com medição** (separados, para mês com
lacuna não passar por completo), percentual médio, mínimo e máximo, EAR total
média, capacidade máxima e a participação média na EAR do subsistema. Sem KPI
(ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → EAR_DIARIO_RESERVATORIOS_{ano}.csv
  → gs://<bucket>-raw/ons/ear_reservatorio/dt=…/<ingestao_id>.json.gz
    → bronze.ons_ear_reservatorio     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_ear_reservatorio   (vigente; QUALIFY por data+reservatório)
        → gold.armazenamento_mensal_reservatorio
```
