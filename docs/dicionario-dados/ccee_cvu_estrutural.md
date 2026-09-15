# CCEE — CVU estrutural

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_estrutural` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=custo_variavel_unitario_estrutural` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2025`, `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Delimitador | **vírgula** — o único CSV da CCEE nesta fonte que não usa `;` |
| Natureza | **Uma linha por usina, leilão, produto e ano de horizonte**, no mês de referência: a mesma usina aparece uma vez por ano projetado |
| Volume verificado | 4.715 linhas no recurso `custo_variavel_unitario_estrutural_2026`, em 14/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia (B1) |
| Credencial | nenhuma |

Ordem 5 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
O CVU (custo variável unitário) estrutural que o B1 nomeia em Mercado de
Energia — o custo que explica o despacho por ordem de mérito. Datas em
`dd/mm/aaaa`.

## Perfilamento (Step 1, 14/09/2026)

Rodado contra a API real (`custo_variavel_unitario_estrutural_2026`), só com
o padrão do módulo (`csv.DictReader`, sem regra de negócio):

| Métrica | Valor |
|---|---|
| Linhas | 4.715 |
| Duplicatas na chave candidata do Questionário — (`MES_REFERENCIA`, `ANO_HORIZONTE`, `CODIGO_PARCELA_USINA`, `LEILAO`, `PRODUTO`) | **185** |
| Duplicatas com `CODIGO_MODELO_PRECO` acrescentado à chave | **0** |
| Anos de horizonte (`ANO_HORIZONTE`) | 2026, 2027, 2028, 2029, 2030 (5) |
| Tipos de combustível (`TIPO_COMBUSTIVEL`) | 10: Bagaço de Cana de Açúcar, Biocombustíveis, Carvão, Carvão Mineral Importado, Carvão Mineral Nacional, Casca de Arroz, Cavaco de Madeira, Diesel, Gás Natural, Óleo Combustível B1 |

**A chave escolhida** é (`periodo_apuracao_ccee`, `ano_horizonte`,
`codigo_parcela_usina`, `leilao`, `produto`, `codigo_modelo_preco`) — seis
colunas. A candidata de cinco colunas do Questionário duplicava 185 vezes no
arquivo inteiro (duas linhas da mesma usina, no mesmo horizonte, leilão e
produto, com `CODIGO_MODELO_PRECO` diferente — modelos de precificação
distintos aplicados à mesma parcela); acrescentar essa coluna, como instruído,
zera as duplicatas. Não foi preciso registrar pendência técnica.

`CODIGO_PARCELA_USINA` vem **vazio em 1.125 das 4.715 linhas** (~24%),
concentrado nos meses mais recentes do ano corrente (jun–set/2026: 15, 360,
360 e 390 linhas, respectivamente). Não é erro do conector: a coluna aceita
string vazia (`limpar()` devolve `""`, que não é `NULL`), e a chave de seis
colunas continua sem duplicata mesmo com o código vazio — outras colunas da
chave distinguem essas linhas. Registrado aqui porque é o mesmo padrão que
bloqueia o de-para de usina (#141): sem `CODIGO_PARCELA_USINA`, essas linhas
também não têm como ganhar `codigo_usina` depois.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `ANO_HORIZONTE` | `ano_horizonte` | INT64 | ano projetado ao qual este CVU se refere |
| `CODIGO_PARCELA_USINA` | `codigo_parcela_usina` | STRING | código interno da CCEE — **não é o CEG** (#141) |
| `SIGLA_PARCELA` | `sigla_parcela` | STRING | — |
| `TIPO_COMBUSTIVEL` | `tipo_combustivel` | STRING | — |
| `LEILAO` | `leilao` | STRING | — |
| `PRODUTO` | `produto` | STRING | — |
| `CVU_ESTRUTURAL` | `cvu_estrutural` | NUMERIC | **R$/MWh** — a única unidade que o próprio nome da coluna deixa clara |
| `CODIGO_MODELO_PRECO` | `codigo_modelo_preco` | STRING | discrimina o modelo de precificação; parte da chave |
| `INICIO_SUPRIMENTO` | `inicio_suprimento` | DATE | `dd/mm/aaaa` → `DATE`; formato que não bate vira linha inválida (`field_validator` no schema) |
| `TERMINO_SUPRIMENTO` | `termino_suprimento` | DATE | idem |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`,
`_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | a origem não traz submercado por usina |
| `codigo_usina` | não | `CODIGO_PARCELA_USINA` não é o CEG; de-para pendente (#141), mesma regra de `ccee_geracao_usina` |
| `agente_ccee` | não | a usina não é agente |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `ano_horizonte`,
`codigo_parcela_usina`, `leilao`, `produto`, `codigo_modelo_preco`) —
confirmada no perfilamento acima. Vence a **publicação mais recente**
(`versao_publicacao`), e a hora da leitura só desempata leituras da mesma
publicação — opção B da ADR 016.

## Gold

`gold.cvu_estrutural_vigente_usina` — o CVU de cada usina por ano de
horizonte, como publicado no mês de referência mais recente (`QUALIFY` por
`periodo_apuracao DESC`). Cruza com `geracao_mensal_usina` por
`codigo_parcela_usina`. Sem KPI (ADR 012).

## Qualidade e observações

- `CVU_ESTRUTURAL` não pode ser negativo (faixa da Silver, issue #110).
- `ANO_HORIZONTE` não pode ser anterior ao ano do mês de referência — um
  horizonte "passado" seria a origem revisando o próprio conceito de
  horizonte, não um dado válido.
- `TERMINO_SUPRIMENTO` não pode ser anterior a `INICIO_SUPRIMENTO`.
- `CODIGO_PARCELA_USINA` não é o CEG da ANEEL: `codigo_usina` fica nulo até o
  de-para da Lacuna 1 (#141), como em `ccee_geracao_usina`.
- Datas na origem em `dd/mm/aaaa`; uma data malformada vira linha inválida
  (contada em `linhas_invalidas`), não derruba o mês inteiro.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → custo_variavel_unitario_estrutural_{ano}.csv
  → gs://<bucket>-raw/ccee/cvu_estrutural/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_cvu_estrutural   (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_cvu_estrutural (QUALIFY por chave de seis colunas, versao_publicacao DESC)
        → gold.cvu_estrutural_vigente_usina
```
