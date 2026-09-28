# ONS — CVU das usinas térmicas

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `cvu_usitermica_se` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/cvu_usitermica_se/CVU_USINA_TERMICA_{ano}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Semanal (semana operativa do PMO) |
| Histórico | Um CSV por ano, desde 2020 |
| Credencial | nenhuma |
| Volume verificado (2026) | 4.062 linhas, 40 semanas — lido em 28/09/2026 |

## Por que esta fonte existe no lake

O Custo Variável Unitário que o ONS usa para decidir a ordem de despacho das térmicas, semana a semana. Diz quais térmicas entram e a que custo. Não é o CVU estrutural da CCEE (`ccee_cvu_estrutural`), que é o de contrato. Pedida pela Alup em 28/09/2026.

## Particularidades

- **A semana é filtrada pelo fim** (`dat_fimsemana`): o arquivo de 2026 traz a semana de 27/12/2025 a 02/01/2026, que o filtro pelo início deixaria de fora. `data_referencia` é o início da semana.
- **Cada revisão do PMO é uma semana diferente** (revisão 0 é a primeira semana do mês), não uma versão da mesma semana. A chave é (semana, usina); a revisão é atributo.
- **A origem publica linhas idênticas em dobro** — 38 em 2026. Entram as duas no Bronze (fiel à origem) e a Silver fica com uma.
- CVU zero é valor (usina a custo zero), não ausência.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `dat_iniciosemana` | `data_referencia` | DATE, início da semana |
| `dat_fimsemana` | `fim_semana` | DATE |
| `ano_referencia` | `ano_referencia` | INT64 |
| `mes_referencia` | `mes_referencia` | INT64 |
| `num_revisao` | `revisao` | INT64 |
| `nom_semanaoperativa` | `semana_operativa` | STRING |
| `cod_usinaplanejamento` | `codigo_usina_planejamento` | STRING |
| `id_subsistema` | `submercado` | STRING, N/NE/S/SE |
| `nom_usina` | `usina` | STRING |
| `val_cvu` | `cvu_reais_mwh` | NUMERIC, R$/MWh |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | início da semana operativa |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem não traz CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `codigo_usina_planejamento`). Vence a ingestão mais recente.

## Gold

`gold.cvu_mensal_termica` — por mês (da semana operativa), submercado e usina: semanas, CVU médio, mínimo e máximo. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → CVU_USINA_TERMICA_{ano}.csv
  → gs://<bucket>-raw/ons/cvu_termica/dt=…/<ingestao_id>.json.gz
    → bronze.ons_cvu_termica     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_cvu_termica   (vigente; QUALIFY pela chave natural, _ingestao_timestamp DESC)
        → gold.cvu_mensal_termica
```
