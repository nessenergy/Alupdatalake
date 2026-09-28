# CCEE — CVU conjuntural

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_conjuntural` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=custo_variavel_unitario_conjuntural` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 21, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 3 linhas de exemplo na fixture; a origem trouxe 741 linhas em 2026, 48 agentes vendedores — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O CVU conjuntural: calculado do custo real de combustível do mês, por agente vendedor, leilão e produto — diferente do CVU estrutural (fixado por leilão) e revisado ao fim do mês pelo item 22 (`custo_variavel_unitario_conjuntural_revisado`). Pedido pela Alup em 28/09/2026.

## Particularidades

- Delimitado por **vírgula**.
- `CNPJ_AGENTE_VENDEDOR` segue o mesmo validador de 14 dígitos do cadastro de agentes (`ccee_agente.py`).
- Schema e `transformar()` vivem neste módulo e são reaproveitados pelo item 22 (`ccee_cvu_conjuntural_revisado.py`), que tem o mesmo layout de colunas.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE, primeiro dia do mês |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `AGENTE_VENDEDOR` | `agente_vendedor` | STRING |
| `CNPJ_AGENTE_VENDEDOR` | `cnpj_agente_vendedor` | STRING, 14 dígitos |
| `SIGLA_PARCELA` | `sigla_parcela` | STRING |
| `TIPO_COMBUSTIVEL` | `tipo_combustivel` | STRING |
| `LEILAO` | `leilao` | STRING |
| `PRODUTO` | `produto` | STRING |
| `CUSTO_COMBUSTIVEL` | `custo_combustivel` | NUMERIC, R$/MWh |
| `CVU_CONJUNTURAL` | `cvu_conjuntural` | NUMERIC, R$/MWh |
| `CODIGO_MODELO_PRECO` | `codigo_modelo_preco` | STRING |
| `TERMINO_SUPRIMENTO` | `termino_suprimento` | DATE, dd/mm/aaaa |
| `INICIO_SUPRIMENTO` | `inicio_suprimento` | DATE, dd/mm/aaaa |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do `MES_REFERENCIA` |
| `submercado` | não | a origem não publica submercado |
| `codigo_usina` | não | ver campos acima |
| `agente_ccee` | ver campos | |
| `periodo_apuracao` | sim | derivado de `data_referencia` na Silver |
| `periodo_apuracao_ccee` | sim | `AAAA-MM`, como a CCEE declara |

## Deduplicação

Chave natural: (`periodo_apuracao_ccee`, `codigo_modelo_preco`). Vence a publicação mais recente (`versao_publicacao`,
`last_modified` do recurso no CKAN — ADR 016, opção B).

## Gold

`gold.cvu_mensal_conjuntural` — por mês, agregado entre os agentes vendedores: quantidade de agentes, custo de combustível médio e CVU médio/mínimo/máximo. Sem KPI (ADR 012).

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → custo_variavel_unitario_conjuntural_<ano>
  → gs://<bucket>-raw/ccee/cvu_conjuntural/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_cvu_conjuntural     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_cvu_conjuntural   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.cvu_mensal_conjuntural
```
