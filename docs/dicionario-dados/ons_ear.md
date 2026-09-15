# ONS — energia armazenada (EAR) diária por subsistema

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `ear_subsistema_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_subsistema_di/EAR_DIARIO_SUBSISTEMA_{ano}.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Catálogo com 83 anos de arquivo (um CSV por ano) |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado (2026) | 1.029 linhas (4 subsistemas × ~257 dias), ~50–65 KB |

## Particularidades

- **CSV remoto particionado por ano**, separador `;`, mesma origem (S3 do
  ONS) e mesmo molde de extração do `ons_carga`.
- **Data já ISO**: `ear_data` chega como `2026-01-01`, sem componente de hora
  — diferente da CCEE, que costuma exigir parsing de formato próprio.
- **`id_subsistema` com espaço à direita**: alguns anos do catálogo trazem
  `"N "` em vez de `"N"`. O trim vive no validador Pydantic
  (`EarDiario._submercado_conhecido`), não na extração — as quatro siglas
  (`N`, `NE`, `S`, `SE`) são exatamente as do `submercado` do projeto, então
  não há conversão de nome, só remoção do espaço.
- Submercado fora de `{N, NE, S, SE}` é **rejeitado**, mesma regra do
  `ons_carga`: sigla nova sem revisão do contrato de dados seria dado
  silenciosamente errado.
- O ONS revisa dado já publicado; por isso o agendamento reprocessa uma
  janela de 30 dias e a Silver fica com a ingestão mais recente.
- Ano sem CSV publicado no catálogo (404) vira aviso no log e é ignorado —
  não derruba a execução.

## Unidades

- `ear_max_mwmes` e `ear_verificada_mwmes` estão em **MWmês** (megawatt-mês),
  a unidade padrão do setor para energia armazenada.
- `ear_verificada_percentual` é `ear_verificada_mwmes` **como percentual da
  capacidade máxima do próprio subsistema** (`ear_max_mwmes`) — por isso o
  intervalo válido é fechado em `[0, 100]`: o reservatório não pode armazenar
  mais que a sua própria capacidade máxima. Isso é diferente do percentual do
  `ons_ena` (ver `docs/dicionario-dados/ons_ena.md`), que compara com uma
  média histórica e pode ultrapassar 100.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `ear_data` | `data_referencia` | DATE | primeiros 10 caracteres (já ISO) |
| `id_subsistema` | `submercado` | STRING | trim + maiúsculas; validado contra a lista |
| `nom_subsistema` | `nome_subsistema` | STRING | direto |
| `ear_max_subsistema` | `ear_max_mwmes` | NUMERIC | capacidade máxima, MWmês |
| `ear_verif_subsistema_mwmes` | `ear_verificada_mwmes` | NUMERIC | armazenado verificado, MWmês |
| `ear_verif_subsistema_percentual` | `ear_verificada_percentual` | NUMERIC | percentual da capacidade máxima |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da EAR |
| `submercado` | sim | N, NE, S, SE — mesma dimensão que `ons_carga` alimenta |
| `codigo_usina` | não | EAR é agregada por subsistema |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS, não declara período próprio da CCEE |

## Deduplicação

Chave natural: (`data_referencia`, `submercado`). Vence a ingestão mais
recente (`_ingestao_timestamp`).

## Gold

`gold.armazenamento_e_afluencia_mensal` — junto com `ons_ena`, por mês e
submercado. Ver `docs/dicionario-dados/ons_ena.md` para o porquê de uma só
Gold para as duas fontes.
