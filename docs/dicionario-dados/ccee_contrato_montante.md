# CCEE — montantes contratados por perfil

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `contrato_montante_compra_venda_perfil_agente` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=contrato_montante_compra_venda_perfil_agente` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2024` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal por perfil**: uma linha por (`MES_REFERENCIA`, `CODIGO_PERFIL_AGENTE`) |
| Volume verificado | 183.893 linhas em 2026 (jan–jul), 18,5 MB, em 14/09/2026 |
| Encoding | **UTF-8 e ISO-8859-1 misturados linha a linha** (1.052 linhas ISO-8859-1) — decodificação por linha na base `CceeCsvCkan` |
| Dono do dado (Alup) | Letícia Ferreira — book — e Tahigo Santos — varejo — Comercial e Contratos (B1) |
| Credencial | nenhuma |

Ordem 4 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
É a **via pública de Comercial e Contratos**: quanto cada perfil vendeu e
comprou em contratos registrados na CCEE, mês a mês — a visão que a Câmara tem
da Alupar, não o book interno, que segue preso ao A7.

## Atenção aos nomes de coluna

Esta fonte usa `CODIGO_AGENTE` e `CODIGO_PERFIL_AGENTE`. A contabilização
(`ccee_contabilizacao_perfil`) usa `COD_AGENTE` e `COD_PERF_AGENTE` para o
mesmo conceito — datasets diferentes da mesma câmara, convenções de nome
diferentes. O teste do `transformar()` existe por causa dessa diferença.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `CODIGO_AGENTE` | `codigo_agente` | STRING | trim |
| `CODIGO_PERFIL_AGENTE` | `codigo_perfil` | STRING | trim — o perfil é quem transaciona |
| `SIGLA_PERFIL_AGENTE` | `sigla_perfil` | STRING | trim |
| `NOME_EMPRESARIAL` | `nome_empresarial` | STRING | trim |
| `CNPJ` | `cnpj` | STRING | só dígitos; 14 obrigatórios |
| `CONTRATACAO_VENDA` | `contratacao_venda` | NUMERIC | vazio → NULL; **unidade não documentada pela CCEE** |
| `CONTRATACAO_COMPRA` | `contratacao_compra` | NUMERIC | vazio → NULL; idem |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

Valores chegam com até 14 casas decimais (`766.21345206586`). Pela ordem de
grandeza é energia (MWmed ou MWh), não R$ — mas o catálogo da CCEE não afirma
a unidade, e este documento também não afirma o que a origem não afirma.

### Frequência de vazio (lida em 14/09/2026)

| Coluna | % de linhas vazias | O que significa |
|---|---|---|
| `CONTRATACAO_VENDA` | 80% | a maioria dos perfis só compra |
| `CONTRATACAO_COMPRA` | 8,5% | perfil sem contrato de compra no mês |

Vazio vira NULL, nunca zero: ausência de contrato não é contrato de montante zero.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | o contrato é do perfil; quem carrega submercado é `ccee_perfil` |
| `codigo_usina` | não | não é dado de ativo |
| `agente_ccee` | **não, na Silver** | a origem traz código, não sigla; a Gold traz a sigla juntando com `gold.agentes_ccee` por `codigo_perfil` |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `codigo_perfil`). Vence a
**publicação mais recente** (`versao_publicacao`), e a hora da leitura só
desempata leituras da mesma publicação — mesma opção B da ADR 016 usada nas
demais entidades mensais desta fonte.

## Gold

`gold.posicao_contratual_mensal_perfil` — o que cada perfil comprou e vendeu
em contrato, mês a mês, com o saldo (`saldo_compra_menos_venda` = compra menos
venda, aritmética de leitura, sem unidade afirmada) e a sigla do agente via
`LEFT JOIN` com `gold.agentes_ccee` por `codigo_perfil` — mesma razão da
contabilização: perfil encerrado sai da dimensão mas ainda tem posição
registrada aqui.

## O que este dado não é

Este dado **não é o book interno** de Comercial e Contratos. O book tem preço,
contraparte e vigência de cada contrato; isto tem só o montante mensal
agregado por perfil, sem essas três coisas. A via pública mostra *quanto*
cada perfil contratou — a posição que a Câmara enxerga — não *com quem*, *a
que preço* nem *até quando*. Quem precisa de preço, contraparte ou vigência
segue dependendo do A7 e do book interno; este dado não substitui essa
necessidade, só deixa de zerar a leitura enquanto ela não chega.

## Qualidade e observações

- Encoding misto no arquivo real: 1.052 linhas em ISO-8859-1 no recurso de
  2026. Decodificação por linha, como em toda fonte da CCEE.
- Os nomes de coluna diferem da contabilização por perfil (`CODIGO_*` aqui,
  `COD_*` lá) — mesma câmara, dataset diferente, convenção diferente.
- `(periodo_apuracao_ccee, codigo_perfil)` é único na origem.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → contrato_montante_compra_venda_perfil_agente_{ano}.csv
  → gs://<bucket>-raw/ccee/contrato_montante/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_contrato_montante      (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_contrato_montante    (vigente; QUALIFY por perfil+mês, versao_publicacao DESC)
        → gold.posicao_contratual_mensal_perfil
```
