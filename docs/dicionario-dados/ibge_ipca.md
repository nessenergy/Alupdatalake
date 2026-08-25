# IBGE — IPCA

| Item | Valor |
|---|---|
| Fonte | SIDRA / IBGE, agregado 1737 (IPCA, Brasil) |
| Endpoint | `servicodados.ibge.gov.br/api/v3/agregados/1737/periodos/{AAAAMM-AAAAMM}/variaveis/63\|69` |
| Onda | 1 — API pública, sem credencial |
| Frequência | Mensal, com defasagem (publicação por volta do dia 10) |
| Dono do dado (Alup) | a definir na Onda 0 |
| Credencial | nenhuma |

## Particularidades

- **Período mensal**, não diário: a janela de datas do runner é convertida para
  um intervalo `AAAAMM-AAAAMM` em `_intervalo_mensal()`.
- **Payload aninhado**: uma série por variável, com os períodos como chaves de
  um objeto. O achatamento acontece em `extrair()`, que devolve um registro por
  (período, variável) — por isso o raw gravado no GCS já vem achatado.
- **Mês sem publicação** vem com o sentinela `...` e **não vira linha**, em vez
  de virar linha com valor nulo.
- **O IBGE revisa série publicada.** Por isso o agendamento reprocessa uma
  janela larga (90 dias) e a Silver fica com a ingestão mais recente.

## Campos

| Origem (API) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| chave da `serie` | `periodo` | `periodo` | STRING | `AAAAMM`, como o IBGE devolve |
| chave da `serie` | `data_referencia` | `data_referencia` | DATE | primeiro dia do mês |
| `id` da variável | `variavel_id` | `variavel_id` | STRING | `63` mensal, `69` acumulada no ano |
| `variavel` | `variavel` | `variavel` | STRING | direto |
| `unidade` | `unidade` | `unidade` | STRING | normalmente `%` |
| valor da `serie` | `valor` | `valor` | NUMERIC | direto |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`,
`_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês |
| `submercado` | não | índice nacional |
| `codigo_usina` | não | idem |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |

## Deduplicação

Chave natural: (`data_referencia`, `variavel_id`). Vence a ingestão mais recente
por `_ingestao_timestamp` — que é justamente o que absorve a revisão do IBGE.

## Gold

`gold.inflacao_mensal` — IPCA do mês e acumulado no ano, uma linha por mês.
Insumo de reajuste de contrato e de deflacionamento de série de preço.
