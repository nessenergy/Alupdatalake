# BCB — Selic e CDI diários

| Item | Valor |
|---|---|
| Fonte | SGS / Banco Central do Brasil, séries **11** (Selic) e **12** (CDI) |
| Onda | 1 — API pública, sem credencial |
| Frequência | Diária (dia útil; o SGS não publica em fim de semana e feriado) |
| Limite da fonte | 10 anos por requisição em série diária — o runner particiona a janela |
| Dono do dado (Alup) | Letícia Ferreira — domínio **Econômico** (B1) |
| Credencial | nenhuma |

Selic e CDI foram nomeadas no B1 junto de IPCA e câmbio, e são as duas que
faltavam para fechar o domínio Econômico. Entram pelo mesmo BCB do PTAX: não
são fonte nova para efeito da cláusula 2ª, são entidade nova de fonte que já
existe.

## Por que uma entidade só para duas séries

As duas têm exatamente a mesma forma (`data`, `valor`), o mesmo calendário e o
mesmo regime de publicação, e quase nunca são lidas em separado. Uma tabela com
a coluna `serie` custa menos do que duas tabelas idênticas — e responde "Selic
contra CDI no mesmo mês" sem JOIN.

## Campos

| Origem (SGS) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| `data` | `data_referencia` | `data_referencia` | DATE | `dd/mm/aaaa` → ISO |
| — (código pedido) | `serie` | `serie` | STRING | `selic` para a série 11, `cdi` para a 12 |
| `valor` | `taxa_percentual_dia` | `taxa_percentual_dia` | NUMERIC | taxa **ao dia**, em percentual; 0 ≤ x ≤ 1 |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`,
`_schema_versao`.

**O `serie` não vem no payload.** O SGS devolve só `data` e `valor`; qual série
é aquilo está no código da URL. O conector grava o rótulo no registro bruto,
antes do raw — sem isso o arquivo no GCS não seria reprocessável, porque
ninguém saberia de qual série ele é.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia útil da taxa |
| `submercado` | não | juro não é dado de submercado |
| `codigo_usina` | não | idem |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` derivado de `data_referencia` |

## Deduplicação

Chave natural: (`data_referencia`, `serie`). Vence a ingestão mais recente por
`_ingestao_timestamp`. Reprocessar a mesma janela não duplica na Silver.

## Gold

`gold.juros_mensal` — por mês e série: dias úteis, taxa média ao dia e
**taxa acumulada no mês**.

A taxa acumulada é a capitalização composta dos dias úteis,
`(∏(1 + taxa/100) − 1) × 100`. É como o mercado lê estas séries: a taxa
publicada é ao dia, e somá-la daria um número errado com aparência de certo.
Não é KPI da Alup — a Gold desta fase é descritiva (ADR 012) e nenhum indicador
foi formalizado (A5).

## Qualidade e observações

- **Selic e CDI coincidem em quase todo o histórico recente.** Nas janelas
  conferidas contra a API real em 14/09 (janeiro de 2026, janeiro de 2024,
  setembro de 2026) os valores das séries 11 e 12 são idênticos até a sexta
  casa. Guardar as duas em separado é justamente o que permite ver o dia em que
  divergirem — e é por isso que os testes conferem o rótulo da série, não o
  valor: trocar 11 por 12 no código não mudaria um único número.
- Janela sem dia útil devolve `[]` — execução de sucesso com zero linhas.
- Datas na querystring vão em `dd/mm/aaaa`, não ISO. Trocar dia por mês daria
  data válida em metade dos casos e erro silencioso na outra metade; há teste
  para isso.
- O `valor` vem como **string**. Série sem valor publicado vem vazia e o
  registro é descartado e contado como inválido.
- Teto de 1% ao dia na Silver e no schema: acima disso não é juro, é erro da
  origem. Passaria despercebido depois de capitalizado na Gold.

## Linhagem

```
api.bcb.gov.br/dados/serie/bcdata.sgs.{11,12}
  → gs://<projeto>-raw/bcb/juros/dt=…/<ingestao_id>.json.gz
  → bronze.bcb_juros      (append-only, particionada por _ingestao_timestamp)
  → silver.bcb_juros      (dedup por QUALIFY, dimensões comuns)
  → gold.juros_mensal     (mês × série)
```
