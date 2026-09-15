# CCEE — consumo de varejo

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `varejista_consumidor` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=varejista_consumidor` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2024` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal por varejista × UF × distribuidora**: uma linha por (`MES_REFERENCIA`, `COD_PERF_AGENTE`, `ESTADO_UF_CARGA`, `SUBMERCADO_CARGA`, `COD_PERF_AGENTE_CONECTADO`) |
| Volume verificado | 23.478 linhas em 2026 (jan–jul), 2,6 MB, em 14/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Tahigo Santos — Comercial e Contratos, subtema varejo (B1) |
| Credencial | nenhuma |

Ordem 4 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
É o subtema "contratos de varejo" de Comercial e Contratos, pela via pública:
quanto cada varejista atendeu de carga, mês a mês, por UF e pela distribuidora
à qual a carga está conectada.

A CCEE avisa no catálogo: *"no momento não são considerados os consumidores
migrados no processo de migração simplificada"*. Registrado aqui; quando esses
consumidores entrarem no dataset da CCEE, é o mesmo conector que os recebe,
sem mudança de schema.

## A chave é de cinco colunas

Um varejista atende cargas em várias UFs e distribuidoras no mesmo mês:
(`MES_REFERENCIA`, `COD_PERF_AGENTE`) sozinho **duplica 2.465 vezes** no
arquivo real de 2026. A chave completa —
(`MES_REFERENCIA`, `COD_PERF_AGENTE`, `ESTADO_UF_CARGA`, `SUBMERCADO_CARGA`,
`COD_PERF_AGENTE_CONECTADO`) — tem 0 duplicatas.

`COD_PERF_AGENTE_CONECTADO` é nulo em 1 linha do arquivo real e continua
fazendo parte da chave: o BigQuery agrupa os nulos juntos no `GROUP BY` da
asserção de unicidade, e há exatamente uma linha assim por mês — não é
colisão, é a carga sem distribuidora identificada na origem.

## Confidencialidade

Consumo por cliente vindo da CCEE é classificado como **confidencial (F1)**
pela Alup. O dataset é **interno (F4)** e o acesso é restrito por tipo de
usuário **(F2)**. Este dado é agregado por varejista e UF, não por consumidor
final — mas a classificação vale para a fonte, não só para o dado mais fino
que ela poderia expor, e por isso:

- a Silver mantém a granularidade da origem (varejista, mês, UF,
  distribuidora), mas não é servida diretamente a usuário final;
- a Gold (`gold.consumo_varejista_mensal_uf`) **não desce abaixo de
  (mês, varejista, UF)**: soma as distribuidoras e não expõe
  `codigo_perfil_conectado` como dimensão — distribuidora é detalhe
  operacional da carga, não pergunta de domínio, e mantê-la fora da Gold evita
  que o agregado publicado se aproxime demais do dado confidencial de origem.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, como a CCEE declara |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `COD_PERF_AGENTE` | `codigo_perfil` | STRING | trim — o perfil do varejista |
| `SIGLA_PERFIL_AGENTE` | `sigla_perfil` | STRING | trim |
| `NOME_EMPRESARIAL` | `nome_empresarial` | STRING | trim |
| `ESTADO_UF_CARGA` | `uf_carga` | STRING | trim, maiúsculas, 2 letras |
| `SUBMERCADO_CARGA` | `submercado` | STRING | por extenso → sigla (`SUL` → `S`) |
| `COD_PERF_AGENTE_CONECTADO` | `codigo_perfil_conectado` | STRING | trim; vazio → NULL (1 linha em 2026) |
| `SIGLA_PERFIL_AGENTE_CONECTADO` | `sigla_perfil_conectado` | STRING | trim; vazio → NULL, acompanha o campo acima |
| `QTD_PARCELA_CARGA` | `quantidade_parcelas_carga` | INT64 | vazio → NULL na origem; tipado pelo Pydantic |
| `CONSUMO_TOTAL` | `consumo_total` | NUMERIC | vazio → NULL na origem; **unidade não documentada pela CCEE** |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

Dez campos de origem. A ordem de grandeza de `CONSUMO_TOTAL` sugere energia
(MWh), mas o catálogo da CCEE não afirma a unidade, e este documento também
não afirma o que a origem não afirma.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | **sim** | o submercado **da carga**, não do agente — por extenso na origem, sigla na Silver |
| `codigo_usina` | não | carga, não ativo de geração |
| `agente_ccee` | **não, na Silver** | a origem traz o perfil do varejista, não a sigla do agente; a Gold traz a sigla juntando com `gold.agentes_ccee` por `codigo_perfil` |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | sim | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `codigo_perfil`, `uf_carga`,
`submercado`, `codigo_perfil_conectado`) — as cinco colunas da seção acima.
Vence a **publicação mais recente** (`versao_publicacao`), e a hora da leitura
só desempata leituras da mesma publicação — mesma opção B da ADR 016 usada nas
demais entidades mensais desta fonte.

## Gold

`gold.consumo_varejista_mensal_uf` — quanto cada varejista atendeu de carga em
cada UF, mês a mês: parcelas de carga e consumo somados sobre as
distribuidoras, com a contagem de distribuidoras distintas
(`distribuidoras`) e a sigla do agente via `LEFT JOIN` com
`gold.agentes_ccee` por `codigo_perfil`. Não desce abaixo de
(mês, varejista, UF) — ver "Confidencialidade" acima.

`COUNT(DISTINCT codigo_perfil_conectado)` não conta a linha em que essa coluna
vem `NULL` (a carga sem distribuidora identificada, ver "A chave é de cinco
colunas" acima) — `distribuidoras` fica uma unidade abaixo do número real de
linhas somadas nesse caso, enquanto `consumo_total` e `parcelas_de_carga`
somam a linha normalmente (`SUM` não descarta `NULL` do jeito que
`COUNT(DISTINCT ...)` descarta).

## Qualidade e observações

- A CCEE não considera, por ora, os consumidores migrados pela migração
  simplificada — nota do próprio catálogo. Quando entrarem, é o mesmo
  conector, sem mudança de schema.
- `(periodo_apuracao_ccee, codigo_perfil, uf_carga, submercado,
  codigo_perfil_conectado)` é único na origem; `(periodo_apuracao_ccee,
  codigo_perfil)` sozinho duplica 2.465 vezes.
- `CONSUMO_TOTAL` e `QTD_PARCELA_CARGA` vazios viram NULL, nunca zero:
  ausência de valor não é consumo zero.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → varejista_consumidor_{ano}.csv
  → gs://<bucket>-raw/ccee/varejista_consumidor/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_varejista_consumidor      (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_varejista_consumidor    (vigente; QUALIFY pelas 5 colunas da chave, versao_publicacao DESC)
        → gold.consumo_varejista_mensal_uf
```
