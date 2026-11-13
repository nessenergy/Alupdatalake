# CCEE — consumo horário por perfil de agente

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `consumo_horario_perfil_agente` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=consumo_horario_perfil_agente` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso gzip por mês (`consumo_horario_perfil_agente_AAAAMM`) |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 26) — arquivo público, sem credencial |
| Dimensionamento | [`superpowers/specs/2026-11-10-item26-consumo-horario-design.md`](../superpowers/specs/2026-11-10-item26-consumo-horario-design.md) |
| Volume | ~34,9 milhões de linhas por mês (46.890 cargas × 744 horas, perfilado em 28/09/2026 sobre `202607`); ~11 GiB por mês na Bronze, **estimado** (a carga de prova mede o real) |
| Histórico no lake | `dev`: janela recorrente de 3 meses, com a carga de prova entrando por 1 mês (jul/2026); `hml`: 1 mês |
| Frequência | mensal; a CCEE publica o mês com cerca de dois meses de defasagem (referência "MS+22du") |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

Consumo por carga e por hora dos perfis de agente do mercado livre. Uma linha por carga por hora — granularidade muito mais fina que os outros conjuntos CCEE do Aditivo 01, que somam poucas centenas de linhas por mês. Pedido pela Alup em 28/09/2026.

## Como consultar sem pagar varredura completa

O custo de BigQuery é da Alup (regra 4). Por isso:

- **Consumidor lê a Gold.** `gold.consumo_horario_submercado_classe` (~18 mil linhas por mês) e `gold.consumo_mensal_carga` (~47 mil por mês) respondem às perguntas usuais em KB.
- **A Bronze exige filtro de partição**: `require_partition_filter = TRUE` em `data_referencia`. Consulta sem filtro é recusada.
- **A Silver tem um limite fixo (`data_referencia >= 2024-03-01`)** só para as asserções e a Gold poderem ler a view inteira; ele não protege consulta avulsa. Consulta exploratória na Silver filtra `data_referencia`: um `SELECT *` sem filtro varre tudo o que está carregado (cerca de 11 GiB por mês).
- Jobs do lake rodam com `maximum_bytes_billed`.

## Particularidades

- **`PERIODO_COMERCIALIZACAO` é a hora do dia (0..23)** e a coluna `DATA` (dd/mm/aaaa) traz o dia, diferente do PLD e do `ccee_geracao_usina`. Constatado na carga de prova de 12/11/2026 (a primeira leitura, que tratava o período como índice 1..744 do mês, colapsou o mês inteiro no dia 1). `data_referencia` é a `DATA` e `data_hora` é a `DATA` mais a hora. Hora fora de 0..23 é linha inválida, contada em `linhas_invalidas`.
- **`data_hora` é `DATETIME`**: horário de Brasília, sem fuso, como a CCEE publica. Não é conversão para UTC.
- **Medida vazia é nula, não zero.** Zero continua zero.
- **Partição pelo dia do consumo**, e não por data de ingestão como nas outras Bronzes: a carga de um mês cai em ~31 partições diárias, e a consulta típica filtra o dia. Cluster por `codigo_carga`, `submercado`, `classe_perfil_agente`.
- **Guarda de recarga.** A Bronze é append-only e cada mês pesa ~11 GiB; reler o mês a cada execução triplicaria o armazenamento. O conector consulta a Bronze (filtrando a partição do mês, com teto de bytes) e **não relê o mês** que já tem linhas de uma execução concluída (`SUCESSO`) na mesma `versao_publicacao`. Mês republicado, com versão nova, é relido. Mês cujo recurso vem sem `last_modified` vale pelo mês, e não pela versão. Para reprocessar de propósito: `RELER_MESES_CARREGADOS=true`.
- **`last_modified` pode vir nulo** (em 10/11/2026, nos recursos `202605` a `202609`): a `versao_publicacao` assume a data da carga, com aviso no log, e a Silver continua correta (a carga mais recente vence).
- **`SUBMERCADO` vem por extenso** e vira a sigla do ONS (N, NE, S, SE). Nome desconhecido é linha inválida.
- **Campos a confirmar na primeira carga real** (a CDN da CCEE bloqueou o download a partir da estação de desenvolvimento, e o conector foi escrito pelo catálogo e pelo perfilamento de 28/09): a coluna `MES_REFERENCIA` (a base usa-a para recortar a janela; sem ela a execução extrairia zero linha), o formato de `DATA_MIGRACAO` (aceita `dd/mm/aaaa` e ISO) e a unicidade da chave (a asserção `uniqueKey` da Silver confirma).
- Delimitado por `;`; encoding por linha, como a base `CceeCsvCkan`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` + `PERIODO_COMERCIALIZACAO` | `data_referencia` | DATE, o dia da hora |
| `MES_REFERENCIA` + `PERIODO_COMERCIALIZACAO` | `data_hora` | DATETIME, hora cheia de Brasília |
| `DATA` | `data_referencia`, `data_hora` | DATE `dd/mm/aaaa`; o dia da medida |
| `PERIODO_COMERCIALIZACAO` | `periodo_comercializacao`, `data_hora` | INT64, 0..23 (hora do dia) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE |
| `CODIGO_CARGA` | `codigo_carga` | INT64 |
| `NOME_CARGA` | `nome_carga` | STRING |
| `DATA_MIGRACAO` | `data_migracao` | DATE, nulo quando vazio |
| `CODIGO_PERFIL_AGENTE` | `codigo_perfil_agente` | INT64 |
| `SIGLA_PERFIL_AGENTE` | `sigla_perfil_agente` | STRING |
| `CLASSE_PERFIL_AGENTE` | `classe_perfil_agente` | STRING |
| `NOME_EMPRESARIAL` | `nome_empresarial` | STRING |
| `CNPJ_CARGA` | `cnpj_carga` | STRING |
| `CIDADE_CARGA` | `cidade_carga` | STRING |
| `ESTADO_CARGA` | `estado_carga` | STRING |
| `SUBMERCADO` | `submercado` | STRING, sigla (N, NE, S, SE) |
| `CODIGO_PERFIL_AGENTE_DISTRIBUIDORA` | `codigo_perfil_agente_distribuidora` | INT64, nulo quando vazio |
| `SIGLA_PERFIL_AGENTE_DISTRIBUIDORA` | `sigla_perfil_agente_distribuidora` | STRING |
| `CAPACIDADE_CARGA` | `capacidade_carga` | NUMERIC, MW |
| `CONSUMO_CARGA_ACL` | `consumo_carga_acl` | NUMERIC, MWh |
| `CONSUMO_CARGA_AJUSTADO_ACL` | `consumo_carga_ajustado_acl` | NUMERIC, MWh |
| `CONSUMO_CARGA_AJUSTADO` | `consumo_carga_ajustado` | NUMERIC, MWh |
| `CONSUMO_CARGA_PONTO_CONEXAO` | `consumo_carga_ponto_conexao` | NUMERIC, MWh |

As medidas são `NUMERIC` (padrão do projeto, 16 bytes); `FLOAT64` cortaria cerca de 25% da Bronze mas quebra o padrão — decisão de 10/11/2026.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | o dia da hora |
| `submercado` | sim | sigla do ONS |
| `codigo_usina` | não | a origem é de carga, não de usina |
| `agente_ccee` | não | a origem traz o código do perfil, não o do agente |
| `periodo_apuracao` | sim | derivado de `data_referencia` na Silver |
| `periodo_apuracao_ccee` | sim | `AAAA-MM`, como a CCEE declara |

## Deduplicação

Chave natural: (`data_referencia`, `data_hora`, `codigo_carga`) — uma linha por carga por hora. Vence a publicação mais recente (`versao_publicacao`, depois `_ingestao_timestamp` — ADR 016, opção B). `data_referencia` entra no `PARTITION BY` da janela para o filtro de partição descer pela análise.

## Silver — asserções

`uniqueKey` na chave acima, `nonNull` nas chaves e no perfil, submercado em N/NE/S/SE, `periodo_apuracao = periodo_apuracao_ccee` e `consumo_carga_ajustado_acl` e `consumo_carga_ponto_conexao` `>= 0`. `consumo_carga_acl` e `consumo_carga_ajustado` não têm essa condição: a carga de jul/2026 trouxe 33 linhas (8 cargas, 3 dias) com resíduo de medição negativo, entre -0,057 e -0,000007 MWh, que é dado da CCEE e fica como veio. A Gold só roda se elas passarem.

## Gold

- `gold.consumo_horario_submercado_classe` — hora × submercado × classe de perfil, somando as cargas: número de cargas, capacidade e as quatro medidas de consumo. Sem KPI (ADR 012).
- `gold.consumo_mensal_carga` — mês × carga: total das medidas, maior hora, horas com consumo e capacidade. Sem KPI.

Ambas são tabelas recarregadas inteiras (ADR 012). O custo de recarga cresce com o histórico carregado (cerca de US$ 0,01 por mês de histórico, lendo ~20% das colunas).

## Agendamento

`infra/modules/scheduler/main.tf`, entrada `ccee_consumo_horario_perfil_agente`: dia 10 de cada mês, 03:00, janela de 45 dias, `timeout` de 28.800 s, 2 vCPU, 1 GiB, sem retentativa (recarregaria o mês inteiro numa Bronze append-only). Carga histórica por janela explícita (`alupdata ingerir ccee_consumo_horario_perfil_agente --de … --ate …`). Mês perdido por atraso de publicação se recupera assim. Alerta de silêncio em 780 horas.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → consumo_horario_perfil_agente_<AAAAMM> (gzip)
  → gs://<bucket>-raw/ccee/consumo_horario_perfil_agente/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_consumo_horario_perfil_agente   (append-only, particionado por data_referencia, require_partition_filter)
      → silver.ccee_consumo_horario_perfil_agente (vigente; QUALIFY por data_referencia, data_hora, codigo_carga)
        → gold.consumo_horario_submercado_classe
        → gold.consumo_mensal_carga
```

## Volume e custo

Estimativa do dimensionamento (a carga de prova mede o real em `INFORMATION_SCHEMA.TABLE_STORAGE`, e o resultado entra aqui): ~340 bytes por linha, ~11 GiB por mês de Bronze, ~US$ 0,26 por mês de armazenamento por mês carregado, ~5,4 horas de carga por mês (extrapolado de 1.800 linhas/s do `ccee_geracao_usina`). Medido em dev (jul/2026): primeira carga em 3h06, 33,4 milhões de linhas; replay do raw arquivado em 2h54; Bronze com ~11,7 GB; Silver com 34.886.160 linhas (46.890 cargas × 744 horas). O custo de bytes faturados da Silver e das Golds ainda não foi medido.

**Cota de partições.** A Bronze é particionada pelo dia do consumo e cada lote de carga toca os 31 dias do mês. O BigQuery limita as modificações de partição por tabela em janela móvel de 24 horas; a carga de junho em dev, feita no dia seguinte a uma carga e a um replay do mesmo mês, esgotou a cota depois de ~1h38 (`partition_modifications_per_column_partitioned_table`). Regra de operação: um mês por execução e no máximo uma carga ou replay por tabela a cada 24 horas; a reexecução depois da janela é segura, porque a Silver deduplica.
