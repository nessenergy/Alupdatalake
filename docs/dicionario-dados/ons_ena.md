# ONS — energia natural afluente (ENA) diária por subsistema

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ena_subsistema_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ena_subsistema_di/ENA_DIARIO_SUBSISTEMA_{ano}.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Catálogo com 62 anos de arquivo (um CSV por ano) |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado (2026) | 1.029 linhas (4 subsistemas × ~257 dias), ~50–65 KB |

## Particularidades

- **CSV remoto particionado por ano**, separador `;`, mesma origem (S3 do
  ONS) e mesmo molde de extração do `ons_carga` e do `ons_ear`.
- **Data já ISO**: `ena_data` chega como `2026-01-01`, sem componente de hora.
- **`id_subsistema` com espaço à direita**: mesma armadilha do `ons_ear`. O
  trim vive no validador Pydantic (`EnaDiario._submercado_conhecido`), não na
  extração.
- Submercado fora de `{N, NE, S, SE}` é **rejeitado**, mesma regra das outras
  duas fontes do ONS.
- O ONS revisa dado já publicado; agendamento reprocessa janela de 30 dias.
- Ano sem CSV publicado no catálogo (404) vira aviso no log e é ignorado.

## Unidades

- `ena_bruta_mwmed` e `ena_armazenavel_mwmed` estão em **MWmed** (megawatt
  médio) — unidade de vazão de energia, diferente do MWmês do `ons_ear`, que
  é estoque.
- `ena_bruta_percentual_mlt` e `ena_armazenavel_percentual_mlt` são a
  afluência do dia **como percentual da MLT (média de longo termo)** da
  própria região — uma referência histórica, não uma capacidade física. Por
  isso, ao contrário do `ear_verificada_percentual` (que não pode passar de
  100, por ser fração de uma capacidade máxima), o percentual da ENA
  **ultrapassa 100 rotineiramente** em ano mais chuvoso que a média — a
  fixture de teste (`tests/fixtures/ons_ena_2026.csv`) inclui de propósito uma
  linha do submercado Sul acima de 120% para provar que isso é aceito, não
  rejeitado.
- Por essa razão, `definitions/silver/ons_ena.sqlx` **não** replica o teto de
  100 do `ons_ear` nas suas `rowConditions` — só o piso em zero. A defesa
  contra erro de captura (vírgula trocada, campo deslocado) fica no Pydantic
  do conector (`PERCENTUAL_MLT_MAXIMO = 500`), que rejeita valor absurdo sem
  rejeitar ano úmido de verdade.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `ena_data` | `data_referencia` | DATE | primeiros 10 caracteres (já ISO) |
| `id_subsistema` | `submercado` | STRING | trim + maiúsculas; validado contra a lista |
| `nom_subsistema` | `nome_subsistema` | STRING | direto |
| `ena_bruta_regiao_mwmed` | `ena_bruta_mwmed` | NUMERIC | afluência bruta, MWmed |
| `ena_bruta_regiao_percentualmlt` | `ena_bruta_percentual_mlt` | NUMERIC | percentual da MLT |
| `ena_armazenavel_regiao_mwmed` | `ena_armazenavel_mwmed` | NUMERIC | afluência armazenável, MWmed |
| `ena_armazenavel_regiao_percentualmlt` | `ena_armazenavel_percentual_mlt` | NUMERIC | percentual da MLT |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da ENA |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | não | ENA é agregada por subsistema |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS, não declara período próprio da CCEE |

## Deduplicação

Chave natural: (`data_referencia`, `submercado`). Vence a ingestão mais
recente (`_ingestao_timestamp`).

## Gold

`gold.armazenamento_e_afluencia_mensal` — uma só tabela para `ons_ear` e
`ons_ena`, e não duas separadas: as duas fontes descrevem o mesmo reservatório
visto de dois ângulos (quanto tem armazenado, quanto está chegando), que é
exatamente o par que se olha junto na operação. `FULL OUTER JOIN` por
(`periodo_apuracao`, `submercado`), porque as duas séries podem fechar o mês
em dias diferentes no catálogo do ONS — o mesmo motivo de
`mercado_mensal_submercado` usar `FULL OUTER JOIN` entre PLD e carga.
