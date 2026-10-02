# ONS — DESSEM, balanço de energia geral

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `balanco_dessem_geral` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/balanco_dessem_geral/BALANCO_DESSEM_GERAL_{AAAA_MM_DD}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 17) — arquivo público, sem credencial |
| Frequência | Diária: **um arquivo por dia** (padrão C, base `OnsArquivoDiario`) |
| Histórico | 23/05/2025 a 02/10/2026: 493 arquivos de 498 dias possíveis. **Não há arquivo anterior a 23/05/2025** |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado | 192 linhas e ~11 KB por arquivo; 5,6 MB nos 493 — lidos em 02/10/2026 |

## Por que esta fonte existe no lake

O DESSEM é o modelo que o ONS usa para programar o despacho do dia seguinte. Este
arquivo é o balanço simplificado dessa programação: a demanda de cada
subsistema e quanta geração o modelo programou de cada fonte. É o **programado**,
não o realizado (o realizado é o `ons_balanco_energia`). Pedido pela Alup em
28/09/2026.

## Como a janela vira arquivos

Um GET por dia da janela, na URL previsível — **não** se lista o catálogo CKAN.
O catálogo e o S3 divergem: o CKAN listava 494 CSV e deixava de listar 4 dias,
mas um dia que ele lista (30/05/2026) dá 404 no S3. A resposta 404 é o "dia sem
arquivo": aviso no log, a execução segue. Janela de 3 dias ou mais sem nenhum
arquivo é erro (URL quebrada), para que a execução não feche em SUCESSO com zero
linha e escape do alerta de silêncio.

- **Quando o arquivo aparece:** o do dia D é gravado no fim da tarde de D-1 (o de
  02/10 tem `Last-Modified` 01/10 20:00 GMT). **Pode ser regravado**: o de
  15/09/2026 foi regravado em 18/09. Por isso a janela diária é de 7 dias
  (arquivo de 11 KB, custo desprezível); a Silver fica com a ingestão mais recente.
- **Buracos reais no S3:** 21/01/2026, 30/05/2026, 09/08/2026, 05/09/2026 e
  10/09/2026 (404).

## Tempo e recarga

Medido contra o dado real em 02/10/2026, só extração e validação: ~0,4 s por
arquivo (máximo 1,9 s em varredura com 8 conexões). Os 493 arquivos cabem em
poucos minutos, mas a recarga segue o mesmo padrão do runbook (janelas de até 3
meses: 92 arquivos, ~17 mil linhas, bem abaixo do limite de 1.800 s). O DESSEM
só existe desde 23/05/2025: a recarga de 24 meses cobre todo o histórico.

## Particularidades

- **A data vem ISO** (`2026-10-02`), ao contrário do `programacao_x_previsao`.
- **Quatro subsistemas** (N, NE, S, SE) × 48 patamares = **192 linhas por dia**,
  em todos os 493 arquivos. **Não há linha SIN**; um subsistema fora dos quatro
  é recusado.
- **48 patamares por dia** (1 a 48). O dicionário do ONS não diz a que hora cada
  um corresponde, e o conector não deriva hora; presume-se meia hora.
- **Sem negativo e sem vazio**, nos 493 arquivos, em qualquer coluna; o
  dicionário do ONS proíbe negativo e nulo. Negativo é recusado.
- **Nenhuma chave `(dia, patamar, subsistema)` repetida** em nenhum arquivo.
- **Encoding:** UTF-8 (e ASCII) em todos os 493. Sem acento nos valores; a
  decodificação linha a linha cai em ISO-8859-1 se preciso.
- `val_cons_elevatoria` é o consumo das usinas elevatórias, não geração.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_programacaodia` | `data_referencia` | DATE | já ISO |
| `num_patamar` | `patamar` | INT64 | 1 a 48 |
| `cod_subsistema` | `submercado` | STRING | trim + maiúsculas; N, NE, S, SE |
| `val_demanda` | `demanda_mw` | NUMERIC | MW |
| `val_geracao_renovavel` | `geracao_renovavel_mw` | NUMERIC | MW |
| `val_geracao_hidraulica` | `geracao_hidraulica_mw` | NUMERIC | MW |
| `val_geracao_termica` | `geracao_termica_mw` | NUMERIC | MW |
| `val_cons_elevatoria` | `consumo_elevatoria_mw` | NUMERIC | MW |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da programação |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | não | dado agregado |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `patamar`, `submercado`). Vence a ingestão
mais recente (o ONS regrava arquivo publicado).

## Gold

`gold.balanco_dessem_mensal_subsistema` — responde "quanta demanda o modelo de
despacho previu para cada região no mês e de que fonte programou atendê-la":
médias em MW por patamar, por mês e subsistema. Programado, não realizado
(compare com `balanco_energia_mensal_subsistema`). Sem KPI (ADR 012).

## O que não foi verificado

- A hora que cada patamar cobre (o dicionário não diz).
- A carga no BigQuery e no raw (só roda no Cloud Run).
- Por que 30/05/2026 consta no catálogo e dá 404 no S3.
- Se a unidade de `val_cons_elevatoria` é a mesma das demais colunas (o
  dicionário diz MW para todas).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → BALANCO_DESSEM_GERAL_{AAAA_MM_DD}.csv (um por dia)
  → gs://<bucket>-raw/ons/balanco_dessem/dt=…/<ingestao_id>.json.gz
    → bronze.ons_balanco_dessem   (append-only, particionado por _ingestao_timestamp)
      → silver.ons_balanco_dessem (vigente; QUALIFY por dia+patamar+subsistema, _ingestao_timestamp DESC)
        → gold.balanco_dessem_mensal_subsistema
```
