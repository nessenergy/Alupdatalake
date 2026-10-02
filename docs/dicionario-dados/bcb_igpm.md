# BCB — IGP-M mensal

| Item | Valor |
|---|---|
| Fonte | SGS / Banco Central do Brasil, série **189** (IGP-M, variação mensal em %) |
| Onda | 1 — API pública, sem credencial |
| Frequência | Mensal; o valor do mês sai perto do fim do próprio mês |
| Limite da fonte | série curta (um ponto por mês): uma chamada cobre qualquer janela |
| Dono do dado (Alup) | domínio **Econômico** (B1) |
| Credencial | nenhuma |

O IGP-M é o índice de reajuste de boa parte dos contratos de energia e foi cobrado como
pendência da Onda 1 pela Alup em 02/10/2026 (a proposta de 28/05 o cita em "BCB completo
(IPCA, SELIC, PTAX, IGP-M, CDI)"). Entra pelo mesmo BCB do PTAX e da Selic: é entidade nova de
fonte que já existe, não fonte nova para a cláusula 2ª.

## Campos

| Origem (SGS) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| `data` | `data_referencia` | `data_referencia` | DATE | `dd/mm/aaaa` → ISO; o SGS data o mês no **dia 1** |
| `valor` | `variacao_percentual_mes` | `variacao_percentual_mes` | NUMERIC | variação do mês, em percentual; pode ser negativa; −20 ≤ x ≤ 100 |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês do índice |
| `submercado` | não | índice de preços não é dado de submercado |
| `codigo_usina` | não | idem |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` derivado de `data_referencia` |

## Deduplicação

Chave natural: `data_referencia`. Vence a ingestão mais recente por `_ingestao_timestamp`.
Reprocessar a mesma janela não duplica na Silver.

## Gold

`gold.igpm_mensal` — por mês: `igpm_mes` (a variação publicada) e `igpm_acumulado_12m`, o
produto dos fatores `(1 + variação/100)` dos 12 meses até o corrente, `(∏ − 1) × 100`. É o número
que reajusta contrato. O acumulado só existe quando os **12 meses consecutivos** estão no lake; com
menos ou com buraco fica NULL, em vez de subestimado. Não é KPI da Alup: a Gold desta fase é
descritiva (ADR 012).

## Qualidade e observações

- **Janela e dia 1.** O SGS data setembro como `01/09`. Uma janela que começa em `15/09` perderia
  o próprio mês, então o conector pede a partir do dia 1 do mês inicial (há teste).
- A FGV não revisa o IGP-M publicado: a janela larga do agendamento (90 dias) serve só para cobrir
  execução perdida.
- Valores **negativos** existem e são legítimos (deflação do atacado). Em 02/10/2026 a série tinha
  −1,16% em julho/2026 e +1,57% em setembro/2026.
- Teto/piso de −20% a +100% ao mês no schema e na Silver: a década de 1990 teve meses de dois dígitos
  altos, e o que passa disso é erro de origem.
- **Verificado em 02/10/2026:** payload real de 09/2024 a 09/2026, 25 meses, todos no schema.
  **Não verificado:** o acumulado de 12 meses contra o número divulgado pela FGV (conferido só por
  conta independente sobre a mesma série) e a execução no Cloud Run e no Dataform.

## Linhagem

```
api.bcb.gov.br/dados/serie/bcdata.sgs.189
  → gs://<projeto>-raw/bcb/igpm/dt=…/<ingestao_id>.json.gz
  → bronze.bcb_igpm       (append-only, particionada por _ingestao_timestamp)
  → silver.bcb_igpm       (dedup por QUALIFY, dimensões comuns)
  → gold.igpm_mensal      (mês, acumulado em 12 meses)
```
