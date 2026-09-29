# CCEE — CVU conjuntural revisado

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_conjuntural_revisado` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=custo_variavel_unitario_conjuntural_revisado` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 22, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 2 linhas de exemplo na fixture; a origem trouxe 573 linhas em 2026, 44 agentes vendedores — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O CVU conjuntural depois da revisão do custo de combustível do mês — publicado pela CCEE como dataset próprio, não como nova versão do item 21. O mesmo modelo/agente pode aparecer nos dois com valores diferentes. Pedido pela Alup em 28/09/2026.

## Particularidades

- **Mesmo layout de colunas do item 21** (`custo_variavel_unitario_conjuntural`): schema (`CvuConjuntural`) e `transformar()` vêm de `ccee_cvu_conjuntural.py`, reaproveitados aqui — este módulo só define `dataset`/`entidade`.
- É dataset **separado**, não um replay do item 21: a revisão de um modelo/mês pode chegar antes, depois ou nunca (a Gold trata isso com `FULL OUTER JOIN`, ver abaixo).

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

Chave natural: (`periodo_apuracao_ccee`, `sigla_parcela`, `leilao`, `produto`). O código de modelo de preço se repete no mês (28 casos em 2025 e em 2026) e não identifica a linha; o arquivo de 2025 o publica como `CODIGO_MODELO_PREÇO` e traz CNPJ sem o zero à esquerda (13 dígitos, completado). Vence a publicação mais recente (`versao_publicacao`,
`last_modified` do recurso no CKAN — ADR 016, opção B).

## Gold

`gold.cvu_conjuntural_revisao_mensal` — cruza este item com o 21 (`FULL OUTER JOIN` por mês, parcela, leilão e produto): CVU conjuntural, CVU revisado, e a diferença em R$/MWh (nunca a razão entre os dois — ADR 012, adendo de 27/09). Sem KPI (ADR 012).

A Gold **não é a mesma forma** dos demais itens deste lote: em vez de agregar entre agentes, ela cruza este dataset com o item 21 na granularidade de mês + modelo de preço, porque a pergunta de negócio é "quanto a revisão mudou", não "qual a média do mês". `FULL OUTER JOIN` pelo mesmo motivo de `encargos_setoriais_mensal`: as duas fontes fecham em datas diferentes, e um modelo sem revisão publicada não pode sumir.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → custo_variavel_unitario_conjuntural_revisado_<ano>
  → gs://<bucket>-raw/ccee/cvu_conjuntural_revisado/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_cvu_conjuntural_revisado     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_cvu_conjuntural_revisado   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.cvu_conjuntural_revisao_mensal
```
