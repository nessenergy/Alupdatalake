# CCEE — consumo por classe de agente

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `consumo_classe_agente` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=consumo_classe_agente` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 25, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 3 linhas de exemplo na fixture; a origem trouxe 42 linhas em 2026, 7 classes — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O consumo mensal por classe de agente (Distribuidor, Consumidor Livre, Autoprodutor e outras), com a repartição entre ambiente regulado (ACR) e livre (ACL) no ponto de conexão — a base para medir quanto o mercado livre já representa do consumo total. Pedido pela Alup em 28/09/2026.

## Particularidades

- **A CCEE não publica lista fechada de classes**: `classe_agente` fica como texto livre validado só contra vazio, não como enum — evita travar a ingestão se a origem incluir uma classe nova.
- **A CCEE não documenta a unidade** de `CONSUMO` (a ordem de grandeza sugere GWh/mês, mas isso não está afirmado pela origem).
- Delimitado por `;`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE, primeiro dia do mês |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `CLASSE_AGENTE` | `classe_agente` | STRING |
| `CONSUMO` | `consumo` | NUMERIC, unidade não documentada |
| `CONSUMO_PONTO_CONEXAO_CLASSE_ACR` | `consumo_ponto_conexao_classe_acr` | NUMERIC, unidade não documentada |
| `CONSUMO_PONTO_CONEXAO_CLASSE_ACL` | `consumo_ponto_conexao_classe_acl` | NUMERIC, unidade não documentada |

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

Chave natural: (`periodo_apuracao_ccee`, `classe_agente`). Vence a publicação mais recente (`versao_publicacao`,
`last_modified` do recurso no CKAN — ADR 016, opção B).

## Gold

`gold.consumo_classe_agente_mensal` — passa o consumo de cada classe no mês ao lado do consumo total do mês (`SUM(...) OVER`), numerador e denominador na linha, sem calcular a participação percentual. Sem KPI (ADR 012); dividir série por série fica reservado a `indicadores_mensais` (ADR 012, adendo de 27/09).

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → consumo_classe_agente_<ano>
  → gs://<bucket>-raw/ccee/consumo_classe_agente/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_consumo_classe_agente     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_consumo_classe_agente   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.consumo_classe_agente_mensal
```
