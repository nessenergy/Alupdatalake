# Item 26 do Aditivo 01 — `consumo_horario_perfil_agente`: dimensionamento

**Data:** 10/11/2026 · **Status:** proposta, aguardando decisão do Ricardo ·
**Origem:** [`aditivo-01-conjuntos-publicos.md`](../../contrato/aditivo-01-conjuntos-publicos.md)
§4.1 e [`proximos-passos.md`](../../proximos-passos.md) item 1.11.

Objetivo: dizer quanto histórico carregar em `dev`, quanto isso custa de BigQuery
(custo da Alup, regra 4) e como carregar sem varredura completa. O conector não
foi implementado: o desenho tem uma decisão de vazão (seção 5) que não é pequena
nem segura de tomar sozinho.

## 1. O que foi verificado e o que não foi

| Item | Situação |
|---|---|
| Catálogo CKAN (`package_show`) | **Verificado em 10/11/2026**, por leitura da página pública. 31 recursos mensais, `consumo_horario_perfil_agente_202403` a `_202609`, formato GZIP, um recurso por mês. Periodicidade mensal; referência de publicação "MS+22du" (mês seguinte + 22 dias úteis) |
| Colunas | **Verificado**: 19 colunas (seção 3) |
| Tamanho por recurso | **Não verificado.** O campo `size` do CKAN vem `null` nos 31 recursos, e a CDN da CCEE (`pda-download`) bloqueou `curl` a partir desta estação (página "acesso bloqueado"). Não contornei o bloqueio. Um `HEAD` pelo ambiente de `dev` (Cloud Run) resolve em minutos |
| Linhas e texto por mês | **Dado de 28/09/2026, do perfilamento do próprio projeto** (mês 202607): 34,9 milhões de linhas, ~7,7 GB de texto, 46.890 cargas. Confere: 46.890 × 744 h = 34,88 milhões, ou seja, **uma linha por carga por hora** |
| `last_modified` | Nulo nos recursos `202605` a `202609` na resposta de hoje (só até `202604` vem preenchido). O `publicado_em` do conector assume a data da carga, com aviso; `versao_publicacao` vira a data de cada carga, e a Silver continua correta (a mais recente vence) |
| Limites de download | Não documentados no catálogo. Sem autenticação; o runner já lê em fluxo os ~800 MB de texto mensais do `geracao_horaria_usina` |
| Preços | Premissas de `src/portal/custo.py`, conferidas na tabela do BigQuery em 14/09/2026: **US$ 6,25 por TiB varrido; US$ 0,023 por GiB-mês de armazenamento lógico ativo**. A página de preços não pôde ser relida hoje (a ferramenta devolveu só o título). Partição sem alteração por 90 dias cai para a metade do preço (longo prazo). Carga em lote não é cobrada. Camada gratuita (1 TiB de consulta, 10 GiB de armazenamento por mês) **ignorada**, por conservadorismo |

**Sobre os 185 GB:** é texto de origem (24 × 7,7 GB). Para custo, o que vale é o
tamanho lógico no BigQuery (seção 4).

## 2. Extração por janela

- **Um recurso por mês**, gzip. O molde `CceeCsvCkan` com `recurso_por = "mes"`
  (o mesmo de `ccee_geracao_usina`) já faz descoberta no CKAN, fluxo, gzip e
  decodificação por linha. Nada de arquivo inteiro em memória.
- A janela vira lista de meses (`AAAAMM`); o recorte final é por `MES_REFERENCIA`
  da linha. A janela escolhe quantos meses; reprocessar é passar outra janela.
- `PERIODO_COMERCIALIZACAO` é a hora dentro do mês (1..744), como no PLD e no
  `ccee_geracao_usina`: o conector deriva `data_hora` com a mesma aritmética.
- **Cuidado com a recarga.** A janela de 100 a 120 dias das outras fontes relê 2
  a 3 meses a cada execução, e a Bronze é append-only. Aqui cada mês pesa 11 GiB,
  então três leituras por mês triplicam o armazenamento. Proposta: janela
  recorrente de **~45 dias** (o mês publicado mais recente e, se republicado, o
  anterior), e carga histórica por janela explícita, uma vez.
- Credencial: nenhuma (dado público).

## 3. Colunas e desenho das camadas

Origem (19): `PERIODO_COMERCIALIZACAO`, `CODIGO_CARGA`, `NOME_CARGA`,
`DATA_MIGRACAO`, `CODIGO_PERFIL_AGENTE`, `SIGLA_PERFIL_AGENTE`,
`CLASSE_PERFIL_AGENTE`, `NOME_EMPRESARIAL`, `CNPJ_CARGA`, `CIDADE_CARGA`,
`ESTADO_CARGA`, `SUBMERCADO`, `CODIGO_PERFIL_AGENTE_DISTRIBUIDORA`,
`SIGLA_PERFIL_AGENTE_DISTRIBUIDORA`, `CAPACIDADE_CARGA` (MW),
`CONSUMO_CARGA_ACL`, `CONSUMO_CARGA_AJUSTADO_ACL`, `CONSUMO_CARGA_AJUSTADO`,
`CONSUMO_CARGA_PONTO_CONEXAO` (MWh).

**Bronze** (`bronze.ccee_consumo_horario_perfil_agente`): as colunas acima em
`snake_case`, mais `data_referencia` (DATE, dia da hora), `data_hora`
(TIMESTAMP), `periodo_apuracao_ccee`, `versao_publicacao` e as técnicas
`_ingestao_*`, `_fonte`, `_schema_versao`.

- `PARTITION BY data_referencia` (partição diária pelo dia do consumo; ~730
  partições em 24 meses, longe do limite de 10.000) e
  `require_partition_filter = TRUE`. Difere das outras Bronzes (que particionam
  por `DATE(_ingestao_timestamp)`) de propósito: aqui a consulta filtra o dia do
  consumo, e uma carga mensal numa só partição de ingestão não pouparia varredura
  nenhuma. Sem o filtro obrigatório, um `SELECT *` esquecido varre tudo.
- `CLUSTER BY codigo_carga, submercado, classe_perfil_agente`.
- As cinco medidas entram como `NUMERIC` (padrão do projeto, 16 B). `FLOAT64`
  (8 B) cortaria ~25% da Bronze, mas quebra o padrão; fica como decisão.

**Silver** (view): dedup por `QUALIFY ROW_NUMBER() OVER (PARTITION BY
data_referencia, data_hora, codigo_carga ORDER BY versao_publicacao DESC,
_ingestao_timestamp DESC) = 1`. `data_referencia` entra no `PARTITION BY` para o
filtro de partição descer pela janela analítica e a view ler só os dias pedidos.
A chave (`data_hora`, `codigo_carga`) se apoia na conta de uma linha por carga por
hora; **a unicidade deve ser confirmada na primeira carga** (a `assertion
uniqueKey` do Dataform faz isso).

**Gold** (tabelas incrementais por mês, não views). É o que o painel e a Alup
consultam; **ninguém consulta a Silver sem filtro**:
1. `gold.consumo_horario_submercado_classe`: hora × submercado × classe de perfil,
   somando as medidas e contando cargas. ~744 × 4 × ~6 ≈ 18 mil linhas por mês.
2. `gold.consumo_mensal_carga`: mês × carga (46.890 linhas por mês), consumo
   total, pico de MW e horas com consumo.

Ambas ficam em KB a MB: custo de consulta desprezível.

## 4. Volume e custo

Tamanho lógico estimado por linha no BigQuery (strings e NUMERIC não comprimem na
cobrança; estimativa por tipo, **não medida**): 3 datas/timestamps × 8 B; 3
códigos inteiros × 8 B; strings (nome da carga, siglas, classe, razão social,
CNPJ, cidade, UF, submercado, distribuidora, técnicas) ~190 B; 5 NUMERIC × 16 B;
total ≈ **340 B por linha**. Com 34,9 milhões de linhas: ≈ **11 GiB por mês** de
Bronze (faixa de 9 a 14 GiB). A primeira carga em `dev` mede o valor real em
`INFORMATION_SCHEMA.TABLE_STORAGE`.

Silver é view e a Gold é pequena: o volume está na Bronze. O raw no GCS (JSONL
gzip, com lifecycle para Nearline) deve ficar em ~1 a 2 GiB por mês carregado
(por analogia com o gzip 13:1 do `geracao_horaria_usina`): centavos.

**Vazão da carga**, o custo real: o runner carrega por `load_table_from_json`.
Medido em 24/09 no `ccee_geracao_usina`: 2,96 milhões de linhas em 1.650 s, ou
~1.800 linhas/s. Extrapolando linearmente, **um mês do item 26 leva ~5,4 horas**
(34,9 M ÷ 1.800). Cloud Run Job de 2 vCPU / 1 GiB custa cerca de US$ 0,18 por
hora (tarifa pública, de memória, não relida hoje): ~US$ 1 por mês carregado.

| Opção de janela | Bronze (GiB) | Armazenamento/mês | Tempo de carga | Compute (carga única) | Varredura da carga + Gold completa |
|---|---|---|---|---|---|
| **A. 1 mês** | 11 | US$ 0,26 | ~5,4 h | ~US$ 1 | ~US$ 0,01 |
| **B. 3 meses** | 33 | US$ 0,77 | ~16 h (3 execuções) | ~US$ 3 | ~US$ 0,04 |
| **C. 6 meses** | 67 | US$ 1,53 | ~32 h | ~US$ 6 | ~US$ 0,08 |
| **D. 12 meses** | 133 | US$ 3,06 | ~65 h | ~US$ 12 | ~US$ 0,16 |
| **E. 24 meses** | 266 | US$ 6,13 | ~130 h (5,4 dias) | ~US$ 24 | ~US$ 0,32 |

Cada linha vale por ambiente: carregar `hml` e `dev` duplica. Depois da carga, a
recorrência é 1 mês por mês: +11 GiB, +US$ 0,26 de armazenamento por mês
acumulado e ~US$ 1 de compute. A última coluna supõe ler ~20% das colunas da
Bronze (chaves e medidas) para montar a Gold.

**O risco é consulta, não armazenamento.** Um `SELECT *` sem filtro sobre 24
meses varre 266 GiB: **US$ 1,62 por execução** (US$ 0,07 sobre 1 mês). Um painel
que repita isso a cada atualização chega a dezenas de dólares por dia. Proteções:
filtro de partição obrigatório; consumidores só leem a Gold; jobs do lake com
`maximum_bytes_billed`.

## 5. Decisão de vazão

Seis horas por mês cabem num Cloud Run Job (`timeout` de 21.600 a 28.800 s), mas
24 meses em ~5 dias seguidos de execução é frágil e caro de supervisionar. Dois
caminhos:

1. **Manter o runner e carregar por fatias de meses**, em execuções separadas e
   em paralelo (cada mês é um recurso independente). Zero código novo de carga;
   o tempo de parede cai com o paralelismo.
2. **Carga por arquivo**: o conector grava o CSV validado no GCS e um load job
   (gratuito) lê o arquivo, em minutos por mês. É o caminho certo para 12 a 24
   meses, mas é um segundo caminho de carga no projeto, com validação própria, e
   merece ADR e tarefa própria.

## 6. Recomendação

**Opção B (3 meses em `dev`), entrando pela A.** Carregar primeiro 1 mês (jul/2026,
o já perfilado) para medir tamanho real, vazão real e a unicidade da chave; se
confirmar, completar mais 2 meses. Custo: ~US$ 0,77 por mês de armazenamento e
~US$ 3 de compute, sem risco de consulta (Gold pequena). O contrato pede o
conjunto no lake com o padrão demonstrado; 24 meses de granularidade horária por
carga só se justificam com um uso concreto da Alup, e não há pedido registrado.
`hml` fica com 1 mês. Nada de 12 ou 24 meses antes do caminho 2 da seção 5.

A janela é parâmetro (`ultimos_dias` no agendamento; carga histórica por janela
explícita). Padrão do agendamento: 45 dias.

## 7. Decisões que cabem ao Ricardo

1. Janela em `dev`: 1, 3 (recomendada), 6, 12 ou 24 meses?
2. `hml` também carrega? (recomendado: 1 mês)
3. A Alup tem uso concreto para granularidade horária por carga além de 3 meses? Se sim, abrir ADR do caminho de carga por arquivo (seção 5, caminho 2).
4. `NUMERIC` em todas as medidas (padrão) ou `FLOAT64` no item 26 (~25% menos Bronze)?
5. Horas do item 26: reabrir as 6h originais (o desenho acrescenta partição própria, Gold e carga em fatias) ou propor valor novo à Alup?
6. Autorizar o `HEAD` de tamanho real e a carga de prova de 1 mês em `dev` (o deploy é seu).
7. Aceitar `timeout` de 28.800 s, 2 vCPU e 1 GiB para a carga mensal?
