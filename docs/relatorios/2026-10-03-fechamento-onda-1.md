# Fechamento da Onda 1 frente à cláusula 4ª — 03/10/2026

Contrato CPS-01025/2026 · AlupData Fase 1: DataLake · referência: `main` em `191ae00`.

Relatório interno da equipe da ness. Não é comunicação ao cliente e não promete nada à Alup. Separa três coisas
que costumam se misturar: **o que existe no repositório** (arquivos, citados), **o que rodou no GitHub** e **o que foi
conferido no BigQuery** (com data e contagem). Onde a conferência não foi feita, está dito.

## 1. O que a cláusula 4ª prevê para a Onda 1

| # | Item da cláusula | Fontes no projeto | Estado em 03/10 |
|---|---|---|---|
| 1 | ONS Core (EAR, ENA, PLD horário, Carga) | `ons_ear`, `ons_ena`, `ccee_pld`, `ons_carga` | 7 componentes no repositório (matriz, §2) |
| 2 | ONS Operacional (IPDO e ACOMPH) | `ons_demanda_maxima` (seção 7 do IPDO); IPDO em si e ACOMPH sem fonte | decisão proposta no ADR 027, depende de aceite da Alup; IPDO e ACOMPH **não entregues** |
| 3 | ANEEL (tarifas homologadas e referência, PRC) | `aneel_tarifas`, `ace_prc` | 7 componentes; Bronze e Silver conferidos em `dev` e `hml` |
| 4 | INMET (precipitação histórica por bacia) | `inmet_precipitacao`, `ons_bacia_contorno` | 7 componentes; carga e recorte por bacia **não conferidos** no BigQuery |
| 5 | CPTEC (previsão de 7 dias) | nenhuma | **não entregue**: bloqueado (ADR 028) |
| — | IGP-M (proposta de 28/05, minuta PDF de 23/07) | `bcb_igpm` | conferido em `hml`; `dev` pendente |

## 2. Matriz dos 7 componentes por fonte

Colunas 1 a 7 verificadas pela existência dos arquivos no `main` (caminhos abaixo da tabela). "Presente" quer dizer
que o arquivo existe; não quer dizer que a carga em ambiente foi conferida: isso está nas duas últimas colunas.

Legenda da conferência: `conferido (data, contagem)` = consultado no BigQuery; `rodou no GitHub, não conferido` =
workflow terminou com sucesso, sem consulta ao BigQuery; `pendente (motivo)`.

| Fonte | Conector | Bronze | Silver | Gold | Testes | Agendamento | Dicionário | Conferência `hml` | Conferência `dev` |
|---|---|---|---|---|---|---|---|---|---|
| `ons_ear` | presente | presente | presente | presente (`armazenamento_e_afluencia_mensal`) | presente | presente | presente | não consta neste relatório (entregue antes; ver relatório de 02/10) | idem |
| `ons_ena` | presente | presente | presente | presente (idem) | presente | presente | presente | idem | idem |
| `ccee_pld` | presente | presente | presente | presente (`pld_mensal_submercado`) | presente | presente | presente | idem | idem |
| `ons_carga` | presente | presente | presente | presente (`carga_mensal_submercado`) | presente | presente | presente | idem | idem |
| `ons_demanda_maxima` | presente | presente | presente | presente (`demanda_maxima_mensal_subsistema`) | presente | presente | presente | não conferido (execução não verificada) | não conferido (execução não verificada) |
| `aneel_tarifas` | presente | presente | presente | presente (`tarifa_vigente_distribuidora`) | presente | presente | presente | conferido (03/10, 328.293 linhas na Bronze e na Silver; Gold 10.366) | conferido (03/10, 328.293 linhas; Gold 10.366) |
| `ace_prc` | presente | presente | presente | presente (`prc_vigente_comercializadora`) | presente | presente | presente | Bronze e Silver conferidos (03/10, 24 preços); Gold foi atualizada depois com o Dataform rerodado, contagem **não reconferida** | conferido (03/10, 24 preços; Gold 24) |
| `inmet_precipitacao` | presente | presente | presente | presente (`precipitacao_diaria_estacao`) | presente | presente | presente | histórico de 09/2024 a 02/10/2026 em 9 janelas de 3 meses, todas `success` no GitHub; **contagens não conferidas** (o `gcloud` pediu reautenticação) | pendente (carga em andamento) |
| `ons_bacia_contorno` | presente | presente | presente | usada na Gold `precipitacao_diaria_estacao` (colunas `bacia` e `bacia_chave`, `ST_COVERS`) | presente | presente | presente | carregada e Dataform `SUCCEEDED` depois da carga; o cruzamento (quantas estações caem em bacia) **não conferido**. Uma execução anterior do SQL espacial, em 03/10, também `SUCCEEDED`, mas com a Bronze vazia | pendente (não consta carga conferida) |
| `bcb_igpm` | presente | presente | presente | presente (`igpm_mensal`) | presente | presente | presente | conferido (03/10, 25 meses; Gold 25 linhas) | pendente: `api.bcb.gov.br` não resolve a partir de nenhum lugar desde 03/10 ~03:40Z (queda externa) |

Onde está cada componente (caminhos no repositório):

- Conector: `src/conectores/<fonte>.py`. Para `ons_ear`/`ons_ena` existem também as variantes `_bacia` e `_reservatorio`; para
  `ons_carga`, `_api`, `_programada` e `_verificada`.
- Bronze e Silver: `definitions/bronze/<fonte>.sqlx` e `definitions/silver/<fonte>.sqlx`.
- Gold: `definitions/gold/` nos arquivos citados na própria célula (a `ons_ear` e a `ons_ena` alimentam também outras Golds).
- Testes: `tests/unit/conectores/test_<fonte>.py`.
- Agendamento: entrada da fonte em `infra/modules/scheduler/main.tf`.
- Dicionário: `docs/dicionario-dados/<fonte>.md`.

PRs que introduziram as peças desta rodada: #354 (conector INMET), #358 (camadas, agendamento e dicionário do INMET),
#360 (contornos das bacias e bacia de cada estação), #361 (demanda máxima), #362 (limpeza e teste de retry).
Para `ons_ear`, `ons_ena`, `ccee_pld` e `ons_carga` a existência dos arquivos foi verificada hoje; **a conferência de
carga por ambiente não foi refeita aqui** (as quatro vieram de entregas anteriores).

Aditivo 01 (itens 12 a 19, fora da Onda 1, mesmos ambientes): carga de `dev` concluída em 03/10 e Dataform de `dev`
`SUCCEEDED` com os dados; contagens por conector **não conferidas**.

## 3. O que não foi entregue e por quê

- **IPDO (documento) e ACOMPH.** O IPDO público é um PDF preliminar de uso interno, só do dia, sem histórico; o conteúdo
  já está no lake, exceto a demanda máxima, que agora é a fonte `ons_demanda_maxima`. Para o ACOMPH não se encontrou
  origem pública; a hipótese de distribuição por cadastro **não foi verificada**. Proposta no ADR 027, sem aceite.
- **CPTEC.** 403 em todo caminho do webservice e a API nova sem DNS; causa desconhecida. Fora da Onda 1 até haver resposta
  do INPE, como decisão provisória (ADR 028).
- **Conferência no BigQuery** do INMET (carga e cruzamento por bacia) e das fontes do Aditivo 01 em `dev`: não feita.
- **IGP-M em `dev`:** pendente por queda externa do BCB.

## 4. Decisões que dependem da Alup ou de outras pessoas

1. Aceite dos ADRs 026 (recorte por bacia; 39% das estações sem bacia; 19 de 23 `nomecurto` do EAR casam), 027 e 028.
2. A pergunta sobre transmissão (TUST/RAP) nas tarifas.
3. Qual versão do contrato foi assinada: o .docx v3 (sem IGP-M) ou a minuta PDF de 23/07 (com IGP-M).
4. **Inconsistência a registrar, sem decisão aqui:** o painel mantém a Onda 1 como `estado = "entregue"` desde 25/09, visível
   ao cliente, e este relatório mostra os itens 2 (IPDO/ACOMPH) e 5 (CPTEC) da cláusula 4ª sem entrega, e o item 4
   (INMET por bacia) sem conferência. Se a Onda 1 continua constando como entregue é decisão comercial; o marco não foi alterado.

## 5. Riscos medidos

- **INMET:** 38% das horas vêm vazias (10.340 horas sem medição em março de 2025, conforme o dicionário); a origem não explica.
- **INMET, bacia:** 39% das estações ficam sem bacia (ADR 026).
- **Demanda máxima:** origem atrasada; o CSV de 2026 termina em 19/05/2026 (dicionário `ons_demanda_maxima.md`).
- **INMET, memória:** o 1Gi do Cloud Run é estimativa, o pico não foi medido (comentário em `infra/modules/scheduler/main.tf`).
- **BCB fora do ar** desde 03/10 ~03:40Z: `bcb_igpm` em `dev` pendente e os agendamentos diários de `bcb_juros` e do câmbio falham até voltar.

## 6. Próximo passo recomendado

Reautenticar o `gcloud` e conferir no BigQuery, em `dev` e `hml`: contagens do INMET e da `ons_bacia_contorno`, quantas
estações caem em bacia na Gold, Gold de PRC em `hml` e as fontes do Aditivo 01 em `dev`; repetir o `bcb_igpm` em `dev`
quando o BCB voltar. Só depois dessas conferências os marcos correspondentes do painel podem virar `feito`.
