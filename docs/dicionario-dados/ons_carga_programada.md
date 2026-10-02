# ONS — carga programada (API)

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `carga-energia-programada` (API; o catálogo não publica CSV) |
| Endpoint | `GET https://apicarga.ons.org.br/prd/cargaprogramada?dat_inicio=AAAA-MM-DD&dat_fim=AAAA-MM-DD&cod_areacarga=<área>` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — item 18 |
| Frequência | Semi-horária, publicada diariamente; agendamento diário |
| Histórico | Conferido de 09/2024 a 09/2026; o que existe antes disso não foi verificado |
| Credencial | **nenhuma.** A API é pública: sem token, sem cadastro, sem IP liberado (conferido em 02/10/2026). Nada a declarar no Secret Manager |
| Conector | `src/conectores/ons_carga_programada.py`, sobre a mecânica compartilhada em `src/conectores/ons_carga_api.py` |
| Volume verificado | 47.520 linhas em set/2026 (33 áreas × 1.440 meias horas), sem chave repetida — lido em 02/10/2026 |

## Por que esta fonte existe no lake

A carga que o ONS usa na programação diária da operação (modelo DESSEM), por área de carga. Pedida pela Alup em 28/09/2026. Par da [carga verificada](ons_carga_verificada.md): juntas dizem o quanto a programação acerta.

## Diferença para `ons_carga`

| | [`ons_carga`](ons_carga.md) | `ons_carga_programada` |
|---|---|---|
| Origem | CSV anual `carga_energia_di` | API `apicarga.ons.org.br` |
| Grandeza | carga **verificada**, média do **dia**, por subsistema (N, NE, S, SE) | carga **programada**, **meia hora**, por 33 áreas |
| Granularidade | 4 linhas por dia | até 33 × 48 linhas por dia |

Não se duplicam: `ons_carga` é a realizada diária; esta é a prevista semi-horária. `ons_carga_verificada` é a realizada semi-horária por área, e **não substitui** `ons_carga` (outro conjunto, outra publicação do ONS; a conciliação entre os dois não foi feita).

## Contrato da API (o que se viu)

- `cod_areacarga` é **obrigatório**: sem ele a API devolve `[]` com HTTP 200, sem erro.
- `dat_inicio` e `dat_fim` são **inclusivas**: 2 dias pedidos dão 96 linhas.
- **Limite documentado de 3 meses por chamada** (Swagger do ONS). Na programada, 200 dias numa chamada voltaram inteiros; o conector usa 31 dias de qualquer forma, porque a verificada, no mesmo gateway, trunca em silêncio.
- Resposta: lista JSON, sem paginação. Sem limite de taxa observado: ~200 chamadas seguidas em 02/10/2026, sem 429. Não foi lido nenhum cabeçalho de cota. O que **não** foi verificado: comportamento sob carga contínua, que não é o uso (66 chamadas por dia).
- Catálogo de áreas (Swagger do ONS): 4 subsistemas (`SECO`, `S`, `NE`, `N`), 25 áreas geoelétricas (estados e agrupamentos como `BASE` Bahia/Sergipe, `ALPE` Alagoas/Pernambuco, `PBRN` Paraíba/Rio Grande do Norte) e 4 áreas de perdas (`PESE`, `PES`, `PENE`, `PEN`). O conector pede as 33.
- **Fora do catálogo**: `SIN` (a API responde, mas só com zeros) e `SE` (responde com ~650 MWmed até 04/2025 e some depois, sem documentação). Não são ingeridos, e o Pydantic recusa essas siglas.

## Particularidades

- **As áreas se sobrepõem**: o estado está dentro do subsistema. Somar áreas diferentes conta a mesma carga duas vezes. A Silver traz `tipo_area` (`subsistema`, `area_geoeletrica`, `perdas`) para filtrar antes de somar.
- **`instante_utc` é o fim da meia hora**, em UTC. A primeira meia hora do dia tem `instante_utc` 03:30Z (00:30 em Brasília) e a última, 03:00Z do dia seguinte, mas com `data_referencia` ainda no dia. `data_referencia` é o dia em Brasília.
- Há dias sem publicação em alguns meses (ex.: NE, BASE, BAOE, ALPE, PBRN, CE, PI e PENE em 03/2025 vieram com 1.440 de 1.488 linhas). Lacuna da origem; o conector não preenche.
- Nenhum valor negativo nem nulo visto na programada (33 áreas, 09/2024, 03/2025, 09/2026). A Silver recusa negativo por *assertion*; se o ONS passar a publicar, a *assertion* avisa em vez de a Gold sair errada.
- O dicionário oficial do ONS é só a lista de colunas; o significado de "global" (se inclui a MMGD) **não está nele**. Ver a Gold, que o infere dos dados.

## Campos

| Origem (JSON) | Bronze / Silver | Tipo |
|---|---|---|
| `dat_referencia` | `data_referencia` | DATE |
| `din_referenciautc` | `instante_utc` | TIMESTAMP |
| `cod_areacarga` | `area_carga` | STRING, 33 códigos |
| `val_cargaglobalprogramada` | `carga_programada_mwmed` | NUMERIC, MWmed |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia em Brasília |
| `submercado` | só para as 4 áreas de subsistema | `SECO` vira `SE`; estado, área geoelétrica e perdas ficam nulos, porque o estado não é um submercado |
| `codigo_usina` | não | carga agregada por área |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante_utc`, `area_carga`), com *assertion* de unicidade. Vence a ingestão mais recente. A janela diária é de 30 dias.

## Gold

`gold.desvio_carga_programada_verificada_mensal` — por mês e área: o desvio entre a carga verificada e a programada. Sem KPI (ADR 012): diferenças em MWmed, sem meta.

## O que não foi verificado

- A execução no Cloud Run e no Dataform (ocorre no deploy).
- Séries anteriores a 09/2024.
- Se o ONS revisa a programada depois de publicada: a origem não traz `din_atualizacao` nesse endpoint, então a Silver só enxerga mudança pela ingestão mais recente.

## Linhagem

```
apicarga.ons.org.br/prd/cargaprogramada (33 áreas × janelas de 31 dias)
  → gs://<bucket>-raw/ons/carga_programada/dt=…/<ingestao_id>.json.gz
    → bronze.ons_carga_programada     (append-only, particionado por _ingestao_timestamp, cluster data_referencia, area_carga)
      → silver.ons_carga_programada   (vigente; QUALIFY por instante_utc e area_carga, _ingestao_timestamp DESC)
        → gold.desvio_carga_programada_verificada_mensal
```
