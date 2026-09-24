# CCEE — geração horária por usina

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `geracao_horaria_usina` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=geracao_horaria_usina` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por mês, **gzip** (`_202403` … `_202607`, 29 recursos em 14/09/2026) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série horária por parcela de usina**: uma linha por (`DATA`, `PERIODO_COMERCIALIZACAO`, `CODIGO_PARCELA_USINA`) |
| Volume verificado | 2.964.096 linhas, 3.984 parcelas de usina, 31 dias, 61 MB comprimidos / ~800 MB de texto — recurso de julho/2026, em 14/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — usinas do SIN; Letícia Ferreira — usinas da Alupar — Geração e Operacional (B1) |
| Credencial | nenhuma |

Ordem 3 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
É a maior fonte do lake: ~3 milhões de linhas por mês, 3.984 parcelas de usina
vezes 744 horas, na granularidade de usina que o A7 fixa para dado de
portfólio.

## Particularidades

- **Gzip mensal**, detectado pelos dois primeiros bytes do fluxo — a base
  `CceeCsvCkan` lê em fluxo; o arquivo não cabe em memória de uma vez.
- `PERIODO_COMERCIALIZACAO` é o índice da hora **no mês** (1..744), a mesma
  regra do `ccee_pld`: o período 1 é a hora 0 do dia 1, e o período 25 é a
  hora 0 do dia 2.
- **Diferença do PLD: aqui há coluna `DATA` explícita.** O conector deriva o
  dia do período e confere com a `DATA` publicada; se discordarem, a origem
  mudou a regra, e a linha é rejeitada (não corrigida) — o `model_validator`
  do schema, não `transformar()`, para que a linha discordante vire
  `linhas_invalidas`, não derrube a execução inteira.
- `CODIGO_PARCELA_USINA` **não é o CEG**: é o código interno da CCEE.
  `codigo_usina` fica nulo na Silver até o de-para da Lacuna 1
  ([#141](https://github.com/nessenergy/Alupdatalake/issues/141)).
- `TIPO_USINA` tem 6 valores: Hidráulicas MRE, Hidráulicas não MRE, Usinas com
  CVU, Biomassa, Eólicas, Demais usinas.
- **A unidade de `GERACAO_CENTRO_GRAVIDADE` não está documentada pela CCEE no
  catálogo.** Os nomes ficam próximos da origem por isso; a Gold soma sem
  afirmar MWh.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação | % vazio (14/09/2026) |
|---|---|---|---|---|
| `MES_REFERENCIA` | — | — | usado só para derivar `data_referencia` e `periodo_apuracao_ccee` | sempre |
| `DATA` | `data_publicada` | DATE | `dd/mm/aaaa`; tem de bater com o dia derivado do período | sempre |
| `PERIODO_COMERCIALIZACAO` | `periodo_comercializacao` | INT64 | índice da hora no mês, 1..744 | sempre |
| — | `data_referencia` | DATE | dia derivado do período (`ccee_pld._data_e_hora`) | derivado |
| — | `hora` | INT64 | 0–23, derivada do período | derivado |
| — | `periodo_apuracao_ccee` | STRING | `AAAA-MM`, como a CCEE declara | derivado |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) | — |
| `CODIGO_PARCELA_USINA` | `codigo_parcela_usina` | STRING | trim; **não é CEG** | sempre |
| `SIGLA_USINA` | `sigla_usina` | STRING | trim | sempre |
| `FONTE_PRIMARIA` | `fonte_primaria` | STRING | trim | sempre |
| `SUBMERCADO` | `submercado` | STRING | por extenso → sigla (`SUDESTE` → `SE`) | sempre |
| `TIPO_USINA` | `tipo_usina` | STRING | trim; 6 valores fechados | sempre |
| `GERACAO_CENTRO_GRAVIDADE` | `geracao_centro_gravidade` | NUMERIC | vazio é registro **inválido**, não zero | sempre |
| `FATOR_PERDA_INTERNA` | `fator_perda_interna` | NUMERIC | vazio é registro inválido | sempre |
| `FATOR_RATEIO_PERDA_GERACAO` | `fator_rateio_perda_geracao` | NUMERIC | vazio é registro inválido | sempre |
| `GERACAO_SEGURANCA_ENERGETICA` | `geracao_seguranca_energetica` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_RESTRICAO_OPERATIVA_CONST_ON` | `geracao_restricao_operativa_constrained_on` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `ENERGIA_AJUSTADA_ENCARGO_RESTRICAO_OPERATIVA` | `energia_ajustada_encargo_restricao_operativa` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `INDISPONIBILIDADE_UTE_ORDEM_MERITO_ECONOMICO` | `indisponibilidade_ute_ordem_merito` | NUMERIC | vazio → NULL | 70% |
| `CUSTO_DECLARADO_PARCELA_USINA` | `custo_declarado_parcela_usina` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `FATOR_DESLOCAMENTO_HIDRAULICO` | `fator_deslocamento_hidraulico` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_VERIFICADA_ONS` | `geracao_verificada_ons` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DISPONIBILIDADE_VERIFICADA_UG` | `disponibilidade_verificada_ug` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_INFLEXIVEL` | `geracao_inflexivel` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_SUBSTITUTA_COMPENSACAO_INDISPONIBILIDADE` | `geracao_substituta_compensacao_indisponibilidade` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESPACHO_RESTRICAO_ENERGETICA_EX_ANTE` | `despacho_restricao_energetica_ex_ante` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESPACHO_PAGAMENTO_ENCARGO_RESTRICAO_OPERACAO` | `despacho_pagamento_encargo_restricao_operacao` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_FORA_ORDEM_MERITO` | `geracao_fora_ordem_merito` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESPACHO_ORDEM_MERITO_DECK_ONS` | `despacho_ordem_merito_deck_ons` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESPACHO_ORDEM_MERITO_PRECO` | `despacho_ordem_merito_preco` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESPACHO_ORDEM_MERITO` | `despacho_ordem_merito` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_RESERVA_POTENCIA` | `geracao_reserva_potencia` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `PRECO_ENCARGO_RESERVA_POTENCIA` | `preco_encargo_reserva_potencia` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_UNIT_COMMITMENT` | `geracao_unit_commitment` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `GERACAO_FINAL_ORDEM_MERITO` | `geracao_final_ordem_merito` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |
| `DESLOCAMENTO_HIDRAULICO_ENERGETICO_PRELIMINAR` | `deslocamento_hidraulico_energetico_preliminar` | NUMERIC | vazio → NULL | 21,6% (hidráulicas MRE) |
| `GARANTIA_FISICA_AJUSTADA_FATOR_DISPONIBILIDADE` | `garantia_fisica_ajustada_fator_disponibilidade` | NUMERIC | vazio → NULL | 21,6% (hidráulicas MRE) |
| `GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_2` | `garantia_fisica_rrh_modulada_ajustada_2` | NUMERIC | vazio → NULL | 21,6% (hidráulicas MRE) |
| `GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_3` | `garantia_fisica_rrh_modulada_ajustada_3` | NUMERIC | vazio → NULL | 21,6% (hidráulicas MRE) |
| `FATOR_RISCO_HIDROLOGICO` | `fator_risco_hidrologico` | NUMERIC | vazio → NULL | 0%–4,4% (CVU) |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

**Bronze guarda as 36 colunas.** As 25 medidas opcionais são nulas na maior
parte das linhas — coluna nula custa quase nada no armazenamento colunar do
BigQuery, e reler 61 MB por mês para acrescentar uma coluna depois custa mais
do que guardá-la agora.

**A Silver expõe as 3 medidas obrigatórias e 5 das 25 opcionais** —
`geracao_verificada_ons`, `custo_declarado_parcela_usina`,
`despacho_ordem_merito`, `garantia_fisica_rrh_modulada_ajustada_2` e
`fator_risco_hidrologico` — as que têm preenchimento acima de 2% no arquivo
real. As outras 20 ficam na Bronze; se um domínio pedir, entram na Silver com
uma linha.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `submercado` | sim | por extenso na origem, sigla na Silver |
| `codigo_usina` | **não** | `CODIGO_PARCELA_USINA` é código interno da CCEE, não o CEG que o `aneel_siga` usa — Lacuna 1, [#141](https://github.com/nessenergy/Alupdatalake/issues/141). `codigo_parcela_usina` e `sigla_usina` ficam prontos para o de-para |
| `agente_ccee` | não | a usina não é agente; a parcela pertence a um perfil |

## Deduplicação e versão

Chave natural: (`data_referencia`, `hora`, `codigo_parcela_usina`). Vence a
**publicação mais recente** (`versao_publicacao`), e a hora da leitura só
desempata leituras da mesma publicação — opção B da ADR 016.

## Gold

`gold.geracao_mensal_usina` — soma, média e máximo horário de
`geracao_centro_gravidade` por mês, parcela de usina, submercado, fonte
primária e tipo de usina. Sem KPI (ADR 012); a unidade não confirmada mantém
o nome da coluna descritivo, não `_mwh`.

## Qualidade e observações

- **Dry-run contra a API real de julho/2026 (14/09/2026)**: 2.964.096
  extraídos, 0 inválidos, `SUCESSO` em **177,7s** (~3 minutos) — **um mês, em
  dry-run, com gravação do raw e carga no Bronze puladas**. Não é o tempo (nem
  o pico de memória) de uma execução real: `extrair()` lê em fluxo, mas
  `src/core/conector.py` (`_ingerir`) materializa a janela inteira numa lista
  antes de gravar o raw e validar — com a janela de agendamento antiga (70
  dias) isso abria 3-4 recursos mensais de uma vez (~9-12 milhões de linhas,
  ~4 GB de dicts), acima do limite padrão de 512Mi do Cloud Run Job. Batching
  por fatia no runner resolveria de vez, mas é mudança de framework, fora
  desta fila (`docs/proximos-passos.md` §4).
- A CCEE publica o mês com cerca de dois meses de defasagem: em 24/09/2026 o
  recurso mensal mais recente no CKAN era `202607`. Com `ultimos_dias = 40` a
  execução de 24/09 extraiu zero linhas com status `SUCESSO` — a janela nunca
  alcançava um mês publicado. Por isso a janela de agendamento passou para
  **100 dias** (o mês publicado mais recente e o anterior, recontabilização
  ADR 016 — em geral três recursos mensais), dentro do `timeout` de 1800s do
  job (cada mês leva cerca de 3 minutos só na extração, medido em dry-run).
- Se a CCEE republicar um mês, a janela de agendamento de 100 dias (cobrindo o
  mês fechado e o anterior) alcança a nova publicação sem intervenção manual.
- `PERIODO_COMERCIALIZACAO` não numérico ou fora do mês, e `DATA` em formato
  diferente de `dd/mm/aaaa`, contam como `linhas_invalidas` — nunca derrubam a
  execução inteira (a conversão e a checagem vivem no schema, não em
  `transformar()`, exatamente para isso).
- `(data_referencia, hora, codigo_parcela_usina)` é único na origem.
- A unidade de `GERACAO_CENTRO_GRAVIDADE` não está documentada pela CCEE no
  catálogo; a dúvida vai ao dono do domínio (B3: 3 dias úteis).

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → geracao_horaria_usina_{AAAAMM}.gz
  → gs://<bucket>-raw/ccee/geracao_usina/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_geracao_usina    (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_geracao_usina  (vigente; QUALIFY por data+hora+parcela, versao_publicacao DESC)
        → gold.geracao_mensal_usina
```
