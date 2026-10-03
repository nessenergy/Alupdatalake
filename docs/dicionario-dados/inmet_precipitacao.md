# INMET — Precipitação horária por estação

| Item | Valor |
|---|---|
| Fonte | INMET, portal de dados históricos das estações automáticas |
| Recurso | zip anual, um CSV por estação |
| Endpoint | `portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip` |
| Escopo | **Onda 1**, linha "INMET — precipitação histórica por bacia" da cláusula 4ª. A Gold é **por estação, com a bacia ao lado** (coluna `bacia`, ponto em polígono com os contornos do ONS: [ADR 026](../arquitetura/decisoes/026-precipitacao-por-bacia.md) e [`ons_bacia_contorno`](ons_bacia_contorno.md)); a chuva **não** é agregada por bacia |
| Frequência | O zip do ano é reescrito poucas vezes por mês e atrasa (ver "Defasagem") |
| Cobertura | 2025 completo (595 CSVs de estação); o de 2026 é parcial. A cobertura carregada no BigQuery será registrada aqui depois da carga do histórico |
| Volume | 60 a 90 MB por zip; 27.072 linhas e 564 estações em 01 e 02/03/2025 (medido na leitura real) |
| Licença | a do portal do INMET (não conferida aqui) |
| Credencial | nenhuma |

## Por que esta fonte existe no lake

A chuva explica a vazão e, daí, a ENA e o armazenamento dos reservatórios: é o
dado de Meteorologia que a cláusula 4ª pede. O INMET entrega por estação, com
latitude e longitude; a ligação com a bacia hidrográfica é o ADR 026, feita na Gold por ponto em polígono.

## Descoberta: o que o recurso é

- **A API `apitempo.inmet.gov.br` não serve para o histórico.** A lista de
  estações responde, mas o dado horário voltou **204 (vazio)**. Por isso o conector lê o zip do portal.
- **Um zip por ano**, com um CSV por estação. O do ano corrente é parcial.
- **Formato do CSV:** 8 linhas de metadados (`REGIAO:;`, `UF:;`, `ESTACAO:;`, `CODIGO (WMO):;`, `LATITUDE:;`,
  `LONGITUDE:;`, `ALTITUDE:;`, datas de fundação), o cabeçalho na linha 9, `;` como separador, vírgula decimal,
  codificação **latin-1**. A data vem como `aaaa/mm/dd` e a hora como `0100 UTC`. Só a 3ª coluna (precipitação
  total horária, mm) é lida.
- **Hora sem medição** vem como campo vazio ou como **`-9999`** (o INMET usou o sentinela em outros anos). Os dois
  viram `NULL`; **nunca zero**, que seria chuva inventada.

## Como a janela de datas se aplica

O conector baixa o zip de cada ano que a janela toca (uma janela que cruza o ano baixa dois) e recorta as linhas
por `data_referencia`. O zip é gravado em arquivo temporário e cada CSV é lido inteiro, um por vez.

- **Execução semanal:** janela de 62 dias (`ultimos_dias = 62`), cobre a virada do zip e a republicação.
- **Carga do histórico:** em janelas de até 3 meses, uma de cada vez.
- O job baixa **60 a 90 MB por execução, mesmo para uma janela de 1 dia**: o recurso não aceita recorte na origem.

## Particularidades vistas no arquivo real

Medidas em 01 e 02/03/2025 e no zip de 2025:

- **27.072 linhas e 564 estações** em 01 e 02/03/2025 (564 x 48 = 27.072: uma linha por estação e hora).
- **10.340 dessas horas sem medição (38%).** O buraco é grande e vem da origem; por isso a Gold o expõe em vez de
  somá-lo como zero.
- **47 horas vazias na estação A701 em 2025**, uma estação em geral bem coberta. Prova de que a lacuna não é só de
  estação nova.
- **`-9999`** aparece como sentinela de "sem dado" em outros anos; tratado igual ao campo vazio.
- **Leitura estrita (falha alto):** cabeçalho de coluna que não começa por `PRECIPITA`, metadado de estação
  ausente, data fora de `aaaa/mm/dd` e zip sem CSV levantam `LayoutInesperadoError`. Carregar zero linhas como
  sucesso esconderia a quebra por dias (o alerta de silêncio só enxerga depois).
- **Valor acima de 500 mm numa hora** é recusado pelo schema (o recorde horário do país é da ordem de 200 mm).

## Defasagem do zip do ano corrente

O `2026.zip` tinha `Last-Modified` de **02/09/2026 quando foi lido, em 02/10/2026**: um mês sem hora nova.
Uma janela recente pode vir sem as últimas semanas, e **dia sem linhas não quer dizer dia sem chuva**. Um mês
sem dado novo não pode parecer erro nem sucesso silencioso: a Gold traz `ultima_hora_com_dado` por estação.

## Frequência

Agendamento **semanal** (segunda, 6h), janela de 62 dias. Limite de silêncio de 180 h (`includes/silencio.js` e
`infra/modules/monitoramento`), como as outras semanais. Memória: **1 GiB**, 1 CPU, `timeout` de 1800 s
(`infra/modules/scheduler`). A justificativa está no bloco do Terraform: o zip ocupa o `/tmp` (que no Cloud Run
conta na memória), o runner grava em fatias de 8 MiB e a janela rende cerca de 900 mil linhas. O pico **não foi
medido** para este conector; confirmar na primeira carga em hml.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `CODIGO (WMO)` (metadado) | `estacao` | STRING | ex.: `A701` |
| `ESTACAO` (metadado) | `nome_estacao` | STRING | como veio |
| `REGIAO` (metadado) | `regiao` | STRING | N, NE, CO, SE ou S |
| `UF` (metadado) | `uf` | STRING | sigla |
| `LATITUDE` (metadado) | `latitude` | NUMERIC | vírgula decimal vira ponto |
| `LONGITUDE` (metadado) | `longitude` | NUMERIC | idem |
| `ALTITUDE` (metadado) | `altitude_m` | NUMERIC | pode ser vazia |
| coluna 1, `Data` | `data_referencia` | DATE | `aaaa/mm/dd` vira ISO; UTC |
| coluna 2, `Hora UTC` | `hora_utc` | INT64 | `0100 UTC` vira 1; 0 a 23 |
| coluna 3, `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)` | `precipitacao_mm` | NUMERIC | vazio e `-9999` viram NULL; 0 a 500 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da medição, UTC |
| `submercado` | **não** | a estação é do INMET, não do submercado |
| `codigo_usina` | **não** | estação não é usina |
| `agente_ccee` | **não** | a origem é o INMET |
| `periodo_apuracao` | sim | `YYYY-MM` do dia |
| `periodo_apuracao_ccee` | não | a origem é o INMET |

## Deduplicação

Chave natural da Silver: (`estacao`, `data_referencia`, `hora_utc`). Vence a ingestão mais recente (o INMET
republica o zip com correções). A janela de 62 dias relê as mesmas horas a cada semana, e o Bronze é append-only;
a Silver fica com uma linha por estação, dia e hora.

## Gold

`gold.precipitacao_diaria_estacao`: chuva diária por estação (`precipitacao_mm_dia`), com `horas_com_medicao`,
`horas_sem_medicao` e `ultima_hora_com_dado` (por estação, para o zip atrasado não parecer sucesso). **Hora sem
medição fica fora da soma, nunca vira zero**; um dia com 0 horas medidas dá `precipitacao_mm_dia` nulo.
Sem KPI e sem comparação entre estações (ADR 012).

### A coluna `bacia` (ADR 026, implementado)

`bacia` (STRING) é o `Nome_Bacia` do contorno do ONS (`silver.ons_bacia_contorno`) que contém a estação, escrito como
o ONS o escreve (com acento: `Paraná`, `Itajaí-Açu`). `bacia_chave` (STRING) é o mesmo nome em maiúsculas e sem
acento (`PARANA`, `ITAJAI-ACU`), para cruzar com `silver.ons_ear_bacia.nomecurto`: **19 dos 23 `nomecurto` casam** pela
chave (calculado localmente com os 31 nomes reais; o ADR 026 dizia 20 por contar o Itajaí, mas `ITAJAI-ACU` não é
`ITAJAI`: esse cruzamento precisa de um de-para manual). A regra, escrita no SQL:

- **Junção espacial por estação, não por dia:** uma CTE de uma linha por estação (coordenada da leitura mais
  recente que tenha latitude e longitude) liga o ponto `ST_GEOGPOINT(longitude, latitude)` ao contorno por `ST_COVERS`; depois a Gold junta o
  resultado às linhas por dia.
- **LEFT JOIN, nunca INNER:** a estação fora de todo contorno **continua na Gold, com `bacia` nula**. A estação
  exatamente sobre uma borda **recebe** a bacia (`ST_COVERS` inclui a fronteira). Nenhuma bacia é inventada.
- **Estação em mais de um polígono:** vale o de **menor área** (`ST_AREA`); o nome da bacia desempata. A regra é
  determinística, e um teste (`tests/unit/test_sql.py`) a fixa.
- **Contorno vigente:** o da data de referência mais recente de cada bacia.
- **Sem agregação por bacia.** A Gold não faz média nem soma por bacia: a regra de agregação (média das estações,
  ponderada ou não) é decisão metodológica da Alup (ADR 026, §5). A chuva segue por estação.

**Granularidade (o que `bacia` quer dizer).** Os contornos do ONS são faixas, não regiões aninhadas: o polígono
"Paraná" **não contém** Grande, Paranaíba nem Paranapanema. A chuva "do Paraná" é a da faixa desse polígono, não a de
toda a bacia do rio. O conjunto cobre as bacias "com aproveitamentos no SIN": no teste de 03/10/2026 com as 672
estações da lista do INMET, **408 (61%) caíram em alguma bacia e 264 (39%) ficaram fora**, e 1 caiu em duas (litoral,
Nordeste e Norte sem aproveitamentos do SIN). Três bacias do EAR (AMAZONAS, PARAGUAI, SANTA MARIA VIT) não têm
polígono e, portanto, não têm chuva por bacia. Esses números vêm do ADR 026 (medidos com `shapely`); **não foram
reproduzidos no BigQuery**.

## O que foi verificado e como

- O zip real de 2025 foi lido pelo conector (Passo 6 da tarefa do conector): 27.072 linhas e 564 estações em
  01 e 02/03/2025, 10.340 horas sem medição, 47 horas vazias em A701.
- A fixture é pequena e de dado público.
- As três camadas foram lidas pelo `sqlglot` (`tests/unit/test_sql.py`); um teste fixa que a Gold não usa
  `COALESCE(precipitacao_mm, ...)`, e outro que a junção da bacia usa `ST_COVERS` e `ST_AREA`, é um `LEFT JOIN` e
  não agrega por bacia.

## O que não foi verificado

- A execução no Cloud Run e no Dataform: só ocorre no deploy. A Gold usa `MAX(MAX(...)) OVER (...)` sobre agregado,
  SQL válido no BigQuery que nenhum teste local compila; só o Dataform o valida. As `ASSERTIONS` da Silver nunca
  rodaram contra o BigQuery.
- O pico de memória e o tempo do job com a janela de 62 dias.
- A cobertura carregada no BigQuery (estações, primeira e última data).
- Por que parte das horas não tem medição (38% em março de 2025): a origem não explica.
- O texto da licença do portal.
- **A junção espacial da `bacia`:** nenhuma consulta espacial foi executada. `ST_COVERS` e o contorno com
  `make_valid` só rodam no BigQuery; quantas estações caem em cada bacia na Gold, e o tempo da junção, são hipótese
  até a primeira execução em hml.

## Linhagem

```
portal.inmet.gov.br → {ano}.zip (um CSV por estação)
  → gs://<bucket>-raw/inmet/precipitacao/dt=…/<ingestao_id>.json.gz
    → bronze.inmet_precipitacao   (append-only, particionado por _ingestao_timestamp)
      → silver.inmet_precipitacao (QUALIFY por estação, dia e hora, _ingestao_timestamp DESC)
        → gold.precipitacao_diaria_estacao   (+ coluna `bacia`, por ponto em polígono)
              ↑
silver.ons_bacia_contorno  (contornos do ONS, CC-BY; ver ons_bacia_contorno.md)
```
