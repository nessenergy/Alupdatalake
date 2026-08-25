# BCB — Cotação PTAX do dólar

| Item | Valor |
|---|---|
| Fonte | Olinda / Banco Central do Brasil, serviço PTAX (`CotacaoDolarPeriodo`) |
| Onda | 1 — API pública, sem credencial |
| Frequência | Diária (dia útil; o BCB não publica em fim de semana e feriado) |
| Limite da fonte | 90 dias por requisição — o runner particiona a janela |
| Dono do dado (Alup) | a definir na Onda 0 |
| Credencial | nenhuma |

## Campos

| Origem (API) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| `dataHoraCotacao` | `data_hora_cotacao` | `data_hora_cotacao` | TIMESTAMP | direto |
| `dataHoraCotacao[:10]` | `data_referencia` | `data_referencia` | DATE | data do boletim |
| `tipoBoletim` | `tipo_boletim` | `tipo_boletim` | STRING | trim; vazio é rejeitado |
| `cotacaoCompra` | `cotacao_compra` | `cotacao_compra` | NUMERIC | ≥ 0 |
| `cotacaoVenda` | `cotacao_venda` | `cotacao_venda` | NUMERIC | ≥ 0 |
| — | — | `cotacao_media` | NUMERIC | `(compra + venda) / 2` |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`,
`_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | data do boletim |
| `submercado` | não | câmbio não é dado de submercado |
| `codigo_usina` | não | idem |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` derivado de `data_referencia` |

## Deduplicação

Chave natural: (`data_referencia`, `tipo_boletim`). Vence a ingestão mais
recente por `_ingestao_timestamp`. Reprocessar a mesma janela não duplica na
Silver.

## Gold

`gold.cambio_mensal` — câmbio médio, mínimo, máximo e de fechamento por mês,
sobre o boletim de Fechamento. Insumo para conversão de contratos indexados
em dólar.

## Qualidade e observações

- Janela sem dia útil devolve `value: []` — execução de sucesso com zero linhas.
- A API rejeita intervalos longos; o limite de 90 dias está no conector.
- Datas na URL vão em `MM-DD-YYYY` (formato do serviço), não ISO.
