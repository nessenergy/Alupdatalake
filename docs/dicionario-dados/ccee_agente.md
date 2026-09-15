# CCEE — lista mensal de agentes

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `lista_agente_associado` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=lista_agente_associado` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2025`, `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal de retratos**: um por `MES_REFERENCIA`, ~16.400 agentes cada |
| Volume verificado | 147.801 linhas em 2026 (jan–set), 16 MB, em 14/09/2026 |
| Encoding | **UTF-8 e ISO-8859-1 misturados linha a linha** — decodificação por linha na base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia (B1) |
| Credencial | nenhuma |

Ordem 1 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
**Não há coluna de perfil**: o elo agente ↔ perfil vive em
[`ccee_perfil.md`](ccee_perfil.md). Esta fonte enriquece o agente — classe,
situação como comercializador e como varejista, UF — com histórico mensal.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `CNPJ` | `cnpj` | STRING | só dígitos; 14 obrigatórios |
| `SIGLA_AGENTE` | `agente_ccee` | STRING | trim — **dimensão comum** |
| `RAZAO_SOCIAL` | `razao_social` | STRING | trim |
| `CLASSE_AGENTE` | `classe_agente` | STRING | uma das 7 publicadas; outra é rejeitada |
| `SITUACAO_COMERCIALIZADOR` | `situacao_comercializador` | STRING | vazio → NULL |
| `SITUACAO_VAREJISTA` | `situacao_varejista` | STRING | vazio → NULL |
| `ESTADO` | `uf` | STRING | maiúsculo, 2 letras |
| `CATEGORIA_AGENTE` | `categoria_agente` | STRING | uma das 4 publicadas |
| `INDICADOR_VAREJISTA` | `varejista` | BOOL | `Sim` → true |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | o agente não tem submercado; o perfil tem |
| `codigo_usina` | não | cadastro de agente, não de ativo |
| `agente_ccee` | **sim** | `SIGLA_AGENTE` |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `cnpj`). Vence a **publicação mais
recente** (`versao_publicacao`), e a hora da leitura só desempata leituras da
mesma publicação — opção B da ADR 016. Replay de raw antigo não rebaixa o
retrato vigente.

## Gold

`gold.agentes_por_classe_mensal` — agentes por classe e categoria, mês a mês,
com quantos são varejistas e comercializadores autorizados. Contagem descritiva
(ADR 012).

## Qualidade e observações

- **Encoding misto no arquivo real**: 49.269 linhas UTF-8 e 98.532 ISO-8859-1
  no recurso de 2026. Decodificar tudo num encoding só mutila metade das
  razões sociais em silêncio.
- Valores de classe, categoria e situação foram lidos do arquivo em 14/09. Valor
  novo é rejeitado e contado em `linhas_invalidas` — é o sinal de que a CCEE
  mudou o contrato.
- `SITUACAO_COMERCIALIZADOR` vazio em 97% das linhas: só comercializadores têm
  situação. Vazio é NULL, não "sem situação".

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → lista_agente_associado_{ano}.csv
  → gs://<bucket>-raw/ccee/agente/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_agente          (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_agente        (QUALIFY por mês+cnpj, versao_publicacao DESC)
        → gold.agentes_por_classe_mensal
```
