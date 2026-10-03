# ACE Comercializadora — PRC (Preço de Referência Comparável)

| Item | Valor |
|---|---|
| Fonte | Página pública `https://alup.io/valores-de-energia/` (ACE Comercializadora de Energia LTDA, do grupo Alup) |
| Onda | 1 — página pública, sem credencial (cláusula 4ª, item "ANEEL — tarifas homologadas e **referência (PRC)**") |
| Formato | HTML: uma tabela do TablePress, mais o parágrafo "Atualizado em: dd/mm/aaaa" |
| Frequência | Retrato lido toda segunda às 11h; a tabela muda raramente (a data que a página declara era 01/10/2025 em 02/10/2026) |
| Janela | **não se aplica**: a página é um retrato, como o cadastro da ANEEL. A data que vale é a que ela declara |
| Dono do dado (Alup) | domínio **Mercado de Energia** |
| Credencial | nenhuma |

## O que é o PRC

Preço de Referência Comparável é a tabela que cada comercializadora varejista é obrigada a divulgar (Procedimentos de
Comercialização da CCEE, submódulo 1.6; REN ANEEL 1.011/22, art. 13, XI). É **indicativo, não proposta comercial**:
o preço de contratação depende de garantias, flexibilidade, risco de crédito, encargos e prazo. A ACE o publica
com premissas padrão: montante sem flexibilidade, sazonalização e modulação uniformes, pagamento no 6º dia útil do
mês seguinte (MS+6du), todos os tributos exceto o ICMS, sem garantias, sem risco de crédito do consumidor e sem
encargos setoriais (ESS, EER, ERCAP).

Não há base pública única de PRC: cada comercializadora publica o seu, com layout próprio. Este conector lê só o
da ACE. Para outras comercializadoras, ou se a página sair do ar, o caminho é a planilha
(`docs/modelos/modelo-prc.md`, `src/conectores/planilha_prc.py`), que usa o mesmo schema.

## Campos

| Origem (página) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| — | `comercializadora` | `comercializadora` | STRING | fixo: `ACE Comercializadora` |
| "Atualizado em" | `data_atualizacao` | `data_atualizacao`, `data_referencia` | DATE | `dd/mm/aaaa` → ISO |
| Submercado | `submercado` | `submercado` | STRING | `SE/CO` → `SE`; `S`, `NE`, `N` |
| Tipo de Energia | `tipo_energia` | `tipo_energia` | STRING | `convencional` ou `incentivada_50` (50% de desconto na TUSD) |
| cabeçalho "Anual (1 ano)", "Trianual (3 anos)", "Quinquenal (5 anos)" | `prazo_meses` | `prazo_meses` | INT64 | 12, 36 e 60, lidos do cabeçalho |
| célula `R$ 280,00/MWh` | `preco_rs_mwh` | `preco_rs_mwh` | NUMERIC | número brasileiro → decimal; 1 a 2.000 |
| — | `ano`, `indexador`, `premissas` | idem | — | nulos: a ACE publica por prazo e não traz indexador nem premissas na tabela |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | a data de atualização que a página declara, não a da leitura |
| `submercado` | sim | `SE`, `S`, `NE` ou `N` |
| `codigo_usina` | não | preço de comercialização não é dado de usina |
| `agente_ccee` | não | a ACE é a vendedora; o consumidor não está na tabela |
| `periodo_apuracao` | sim | `YYYY-MM` de `data_referencia` |

## Deduplicação

Chave natural: comercializadora, `data_atualizacao`, submercado, tipo de energia e prazo. Vence a ingestão mais
recente. Como a página é lida toda semana, o mesmo retrato entra várias vezes no Bronze e a Silver o reduz a um.
Quando a ACE republicar com outra data, a Silver guarda as duas versões.

## Gold

`gold.prc_vigente_comercializadora` — a tabela publicada na data de atualização mais recente de cada
comercializadora, com `dias_desde_atualizacao`. Esse número é a idade da **tabela**, não da carga: um PRC de um
ano de idade é informação, e é o que a Gold expõe. Sem KPI nem comparação entre comercializadoras (ADR 012).

## Qualidade e observações

- **Falha alta, não silenciosa.** Se a tabela sumir, ganhar prazo diferente de 1, 3 e 5 anos, ou a página perder o
  "Atualizado em", o conector levanta erro. Carregar zero linhas como sucesso passaria despercebido até o alerta de
  silêncio, dias depois.
- **Erro de digitação na origem.** Em 02/10/2026 a linha do Norte dizia "Convecional". O conector aceita qualquer
  tipo que comece com "conve"; tipo que não seja convencional nem incentivada vira linha inválida, contada.
- **Aviso, não erro.** Se a tabela tiver número de preços diferente de 24 (4 submercados × 2 tipos × 3 prazos), o
  conector registra um aviso: pode ser linha nova e legítima.
- **Data de 01/10/2025 confirmada.** A página dizia "Atualizado em: 01/10/2025" quase um ano depois. Em 02/10/2026 a
  ness. confirmou que o PRC não mudou e que essa é a tabela oficial vigente. A Gold segue mostrando a idade da
  tabela (`dias_desde_atualizacao`); um número alto aqui é esperado, não sinal de falha.
- **Verificado em 02/10/2026:** a página real, com a verificação de TLS ligada, trouxe 24 preços, todos válidos
  no schema; os valores conferem com o texto da página. O repositório de certificados do Python do Windows não
  conhece a nova raiz da Let's Encrypt (falha local de verificação); com `requests` e `certifi` a página responde 200.
- **Não verificado:** a execução no Cloud Run e no Dataform; se a ACE publica o PRC em outro endereço ou formato
  além da página.

## Linhagem

```
alup.io/valores-de-energia (HTML)
  → gs://<projeto>-raw/ace/prc/dt=…/<ingestao_id>.json.gz
  → bronze.ace_prc                       (append-only, particionada por _ingestao_timestamp)
  → silver.ace_prc                       (dedup por QUALIFY, dimensões comuns)
  → gold.prc_vigente_comercializadora    (tabela mais recente, com a idade dela)
```
