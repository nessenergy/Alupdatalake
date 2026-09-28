# CCEE — TRC de segurança energética

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `energia_reserva_consumo_referencia` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=energia_reserva_consumo_referencia` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 24, [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Volume verificado | 2 linhas de exemplo na fixture; a origem trouxe 7 linhas em 2026 (série desde 2023) — perfilado em 28/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia |
| Credencial | nenhuma |

O total de referência de consumo (TRC) de segurança energética, usado no rateio do encargo de energia de reserva. Não é o EER (`ccee_energia_reserva`, dataset `energia_reserva_liquidacao`) — datasets e finalidades diferentes; a entidade leva o nome completo para não colidir. Pedido pela Alup em 28/09/2026.

## Particularidades

- **A CCEE não documenta a unidade** nem o que `TRC_SEG_ENER_SUC` distingue de `TRC_SEG_ENER`; perfilado em 28/09/2026, `_SUC` veio sempre vazio nos 7 meses de 2026 — entra como `NULL`, sem inventar o porquê.
- Delimitado por `;`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo |
|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE, primeiro dia do mês |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING, AAAA-MM |
| `TRC_SEG_ENER` | `trc_seguranca_energetica` | NUMERIC, unidade não documentada |
| `TRC_SEG_ENER_SUC` | `trc_seguranca_energetica_suc` | NUMERIC, unidade não documentada; vazio → NULL |

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

Chave natural: (`periodo_apuracao_ccee`). Vence a publicação mais recente (`versao_publicacao`,
`last_modified` do recurso no CKAN — ADR 016, opção B).

## Gold

`gold.consumo_referencia_energia_reserva_mensal` — passa o TRC do mês e acrescenta a variação absoluta contra o mês anterior (`LAG`). Sem KPI (ADR 012); só a diferença, nunca a razão entre os dois meses (ADR 012, adendo de 27/09) — a razão fica reservada a `indicadores_mensais`.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → energia_reserva_consumo_referencia_<ano>
  → gs://<bucket>-raw/ccee/energia_reserva_consumo_referencia/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_energia_reserva_consumo_referencia     (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_energia_reserva_consumo_referencia   (vigente; QUALIFY pela chave natural, versão + _ingestao_timestamp DESC)
        → gold.consumo_referencia_energia_reserva_mensal
```
