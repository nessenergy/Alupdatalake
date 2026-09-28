# CCEE — CVU merchant

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_merchant` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=custo_variavel_unitario_merchant` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 20, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 4 linhas de exemplo na fixture; a origem trouxe 153 linhas em 2026, 23 empreendimentos — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O CVU de usinas térmicas que vendem no mercado livre (merchant), com e sem a parcela de recuperação de custo fixo — o custo que baliza o preço bilateral, diferente do CVU estrutural (fixado por leilão) e do conjuntural (calculado do custo real de combustível). Pedido pela Alup em 28/09/2026.

## Particularidades

- **`CVU_CF` vem com `"-"`** em parte das linhas (32 de 153 em 2026), não vazio — tratado como nulo, igual a vazio.
- **`RECUPERACAO_CUSTO_FIXO`** só trouxe `"Não"` na amostra perfilada; o validador aceita "Sim"/"Não" e rejeita qualquer outro texto, para não inventar um terceiro valor que a origem não mostrou.
- Delimitado por **vírgula**, como o CVU estrutural — não por `;`.
- `MES_REFERENCIA_COTACAO` é um mês de referência secundário (o mês da cotação de combustível), não filtrado pela janela como `MES_REFERENCIA`; a conversão para `periodo_cotacao` vive num `field_validator`, não em `transformar()` — uma linha malformada nesse campo descarta só ela, não a execução inteira.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE, primeiro dia do mês |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `CODIGO_MODELO_PRECO` | `codigo_modelo_preco` | STRING |
| `EMPREENDIMENTO` | `empreendimento` | STRING |
| `DESPACHO` | `despacho` | STRING, número da resolução |
| `TIPO_COMBUSTIVEL` | `tipo_combustivel` | STRING |
| `CVU_SCF` | `cvu_sem_custo_fixo` | NUMERIC, R$/MWh |
| `CVU_CF` | `cvu_com_custo_fixo` | NUMERIC, R$/MWh; "-" e vazio → NULL |
| `RECUPERACAO_CUSTO_FIXO` | `recupera_custo_fixo` | BOOL, "Sim"/"Não" |
| `DATA_INICIO` | `inicio_suprimento` | DATE, dd/mm/aaaa |
| `DATA_FIM` | `termino_suprimento` | DATE, dd/mm/aaaa |
| `ORIGEM_DA_COTACAO` | `origem_cotacao` | STRING, ANP ou Platts |
| `MES_REFERENCIA_COTACAO` | `periodo_cotacao` | STRING, AAAA-MM |

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

`gold.cvu_mensal_merchant` — por mês, agregado entre os empreendimentos: quantidade, e média/mínimo/máximo das duas parcelas de CVU. Sem KPI (ADR 012).

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → custo_variavel_unitario_merchant_<ano>
  → gs://<bucket>-raw/ccee/cvu_merchant/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_cvu_merchant     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_cvu_merchant   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.cvu_mensal_merchant
```
