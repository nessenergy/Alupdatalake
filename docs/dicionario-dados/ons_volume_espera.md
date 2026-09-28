# ONS — volume de espera recomendado

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `res_volumeespera` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/res_volumeespera/RES_VOLUMEESPERA_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Um CSV por ano, desde 2006 |
| Credencial | nenhuma |
| Volume verificado (2026) | 8.680 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

O limite de enchimento que o ONS recomenda para cada reservatório, reservando espaço para amortecer cheias. É uma restrição direta ao armazenamento — e por isso à EAR e à geração hidráulica. Pedida pela Alup em 28/09/2026.

## Particularidades

- Em **% do volume útil**: 50,4 a 100 em 2026. Acima de 100 é recusado.
- A série tem **anos faltando** (2008 não existe no catálogo) e um arquivo do ano seguinte; ano ausente vira aviso, não erro.
- Bacia e REE vêm com espaços à direita; o trim vive no validador.
- A ordem na cascata (`num_ordemcs`) vem vazia em 310 linhas de 2026 e fica nula.
- Arquivo em UTF-8 (conferido nos bytes: `BOA ESPERANÇA`).

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia` | DATE |
| `id_subsistema` | `submercado` | STRING, N/NE/S/SE |
| `tip_reservatorio` | `tipo_reservatorio` | STRING |
| `nom_bacia` | `bacia` | STRING, sem espaços |
| `nom_ree` | `ree` | STRING, sem espaços |
| `id_reservatorio` | `codigo_reservatorio` | STRING, obrigatório |
| `nom_reservatorio` | `reservatorio` | STRING, obrigatório |
| `num_ordemcs` | `ordem_cascata` | INT64 |
| `cod_usina` | `codigo_usina_ons` | STRING |
| `val_volumeespera` | `volume_espera_percentual` | NUMERIC, 0 a 100 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia de referência |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem não traz CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `codigo_reservatorio`). Vence a ingestão mais recente.

## Gold

`gold.volume_espera_mensal_reservatorio` — por mês, submercado, bacia e reservatório: dias, volume de espera mínimo, médio e máximo. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → RES_VOLUMEESPERA_{ano}.csv
  → gs://<bucket>-raw/ons/volume_espera/dt=…/<ingestao_id>.json.gz
    → bronze.ons_volume_espera     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_volume_espera   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.volume_espera_mensal_reservatorio
```
