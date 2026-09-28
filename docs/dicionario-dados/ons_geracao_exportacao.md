# ONS — geração comercial para exportação internacional, horária

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `geracao_exportacao_internacional_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_exportacao_internacional_ho/GERACAO_EXPORTACAO_INTERNACIONAL_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, publicada diariamente |
| Histórico | Um CSV por ano, desde 2022 |
| Credencial | nenhuma |
| Volume verificado (2026) | 6.456 linhas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

Quanto foi gerado especificamente para vender fora — energia vertida turbinável e térmica — e quanto saiu para cada país. Complementa o intercâmbio internacional, que é o fluxo físico. Pedida pela Alup em 28/09/2026.

## Particularidades

- Uma linha por hora, sem dimensão de país na chave: os países são colunas.
- Todos os valores de 2026 são zero ou positivos; negativo é recusado.
- Série só desde 2022.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `din_instante` | `data_referencia` + `instante` (e `hora` na Silver) | DATE + DATETIME |
| `val_gerexpevt_ar` | `geracao_exportacao_evt_argentina_mwmed` | NUMERIC, MWmed |
| `val_gerexpevt_uy` | `geracao_exportacao_evt_uruguai_mwmed` | NUMERIC, MWmed |
| `val_gerexptermica` | `geracao_exportacao_termica_mwmed` | NUMERIC, MWmed |
| `val_exportacao_ar` | `exportacao_argentina_mwmed` | NUMERIC, MWmed |
| `val_exportacao_uy` | `exportacao_uruguai_mwmed` | NUMERIC, MWmed |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | não | total do SIN para exportação |
| `codigo_usina` | não | dado agregado, sem usina |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante`) — nenhuma repetida em 2026. Vence a ingestão mais
recente.

## Gold

`gold.exportacao_mensal` — por mês: médias da geração para exportação por tipo e da exportação por país. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → GERACAO_EXPORTACAO_INTERNACIONAL_{ano}.csv
  → gs://<bucket>-raw/ons/geracao_exportacao/dt=…/<ingestao_id>.json.gz
    → bronze.ons_geracao_exportacao     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_geracao_exportacao   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.exportacao_mensal
```
