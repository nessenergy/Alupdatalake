# CCEE — PLD horário por submercado

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `pld_horario_submercado` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=pld_horario_submercado` |
| Endpoint do arquivo | **descoberto pelo CKAN**, não fixo — ver particularidades |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Publicação mensal, com defasagem de 1 a 2 meses |
| Granularidade | Horária, por submercado |
| Histórico | Desde 2023 no CKAN, um arquivo por ano |
| Encoding | **ISO-8859-1** |
| Credencial | **nenhuma** |

## Particularidades

- **O 403 que bloqueava esta fonte não era credencial.** Era filtro de cliente
  não identificado. Resolvido pelo `User-Agent` que `src/core/http.py` passou a
  enviar em toda requisição ([ADR 018](../arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)).
  Se o 403 voltar, a investigação começa pelo que a origem passou a exigir.
- **O endereço do arquivo é opaco e muda.** Cada recurso do CKAN tem um
  identificador do tipo `/e-qPA419SneVTnOQ04kEYA/content`, que a CCEE troca ao
  republicar o ano. O conector resolve o ano pelo `package_show` a cada
  execução; URL escrita à mão quebraria em silêncio.
- **Não há coluna de data.** O CSV traz `MES_REFERENCIA` (`AAAAMM`) e
  `PERIODO_COMERCIALIZACAO`, que é o **índice da hora dentro do mês, 1-based**:
  o período 1 é a hora 0 do dia 1, e o 25 é a hora 0 do dia 2. Um mês de 31
  dias tem 744 períodos; fevereiro de 2026, 672. Data e hora são derivadas
  daí, e é a parte mais testada do conector — um off-by-one desloca a série
  inteira em uma hora.
- **O Brasil não observa horário de verão desde 2019**, e por isso todo mês tem
  exatamente `dias × 24` períodos. Se o horário de verão voltar, este é o ponto
  que quebra.
- **O submercado vem por extenso** (`NORDESTE`) e é convertido para a sigla que
  o ONS publica (`NE`), para que a dimensão `submercado` cruze entre as duas
  fontes sem tradução na Silver. `SUDESTE` da CCEE e `SE` do ONS são o mesmo
  Sudeste/Centro-Oeste.
- **O ano corrente só aparece depois do primeiro fechamento.** Janela que cruza
  o ano não falha por isso: o ano ausente vira aviso no log, e o que existe é
  ingerido.
- A CCEE recontabiliza período já publicado
  ([ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md));
  por isso a janela agendada é de 120 dias e a Silver fica com a ingestão mais
  recente.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` + `PERIODO_COMERCIALIZACAO` | `data_referencia` | DATE | dia derivado: `(período − 1) ÷ 24 + 1` |
| `MES_REFERENCIA` + `PERIODO_COMERCIALIZACAO` | `hora` | INT64 | hora derivada: `(período − 1) mod 24` |
| `SUBMERCADO` | `submercado` | STRING | nome por extenso → sigla; validado contra a lista |
| `MES_REFERENCIA` | `periodo_apuracao` | STRING | `AAAAMM` → `AAAA-MM` |
| `PERIODO_COMERCIALIZACAO` | `periodo_comercializacao` | INT64 | preservado para rastrear até a origem |
| `PLD` | `pld_reais_mwh` | NUMERIC | R$/MWh; negativo é rejeitado (há piso regulatório positivo) |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da apuração, derivado |
| `submercado` | **sim** | N, NE, S, SE — mesma sigla do ONS, o que permite cruzar preço com carga |
| `periodo_apuracao` | sim | `AAAA-MM`, o mês de referência da CCEE |
| `codigo_usina` | não | o PLD é do submercado, não da usina |
| `agente_ccee` | não | é preço de mercado, não posição de agente. A dimensão vem de `lista_perfil` / `lista_agente_associado`, também públicos — próxima entidade da fila |

## Deduplicação

Chave natural: (`data_referencia`, `hora`, `submercado`). Vence a ingestão mais
recente, porque a CCEE recontabiliza.

## Gold

`gold.pld_mensal_submercado` — média, máxima, mínima e amplitude por mês e
submercado.

**Uma ressalva que precisa acompanhar o número**: a média aritmética das horas
é o que o mercado usa para comparar meses e submercados, mas **não** é o preço
de liquidação de um contrato. Liquidação pondera preço por montante horário, e
o montante não está nesta fonte — ele vive nas APIs credenciadas da CCEE, fora
do escopo desta onda (ADR 018). Quem ler `pld_medio_reais_mwh` como valor
financeiro vai errar.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN)
  → pld_horario_submercado_{ano}.csv (ISO-8859-1)
    → gs://<bucket>-raw/ccee/pld/dt=.../<ingestao_id>.json.gz
      → bronze.ccee_pld        (append-only, particionado por _ingestao_timestamp)
        → silver.ccee_pld      (QUALIFY ROW_NUMBER por data+hora+submercado)
          → gold.pld_mensal_submercado
```

## O que ainda não foi verificado

O conector foi exercitado **em dry-run contra a API real** em 14/09/2026 — 288
registros em 3 dias, 0 inválidos, que é exatamente `3 × 24 × 4`. Não foi
exercitado contra um BigQuery real, porque o projeto GCP ainda não existe
(pendência A3). O que só a primeira carga revela: tipo que o BigQuery recusa,
`NUMERIC` com escala além da esperada e volume de uma janela de 120 dias
(≈ 11.500 linhas) no Cloud Run Job.
