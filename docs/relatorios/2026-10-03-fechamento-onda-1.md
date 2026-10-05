# Fechamento da Onda 1 frente à cláusula 4ª — 03/10/2026

Contrato CPS-01025/2026 · AlupData Fase 1: DataLake · referência: `main` em `191ae00`.

Relatório interno da equipe da ness. Não é comunicação ao cliente e não promete nada à Alup. Separa três coisas
que costumam se misturar: **o que existe no repositório** (arquivos, citados), **o que rodou no GitHub** e **o que foi
conferido no BigQuery** (com data e contagem). Onde a conferência não foi feita, está dito.

## 1. O que a cláusula 4ª prevê para a Onda 1

| # | Item da cláusula | Fontes no projeto | Estado em 03/10 |
|---|---|---|---|
| 1 | ONS Core (EAR, ENA, PLD horário, Carga) | `ons_ear`, `ons_ena`, `ccee_pld`, `ons_carga` | 7 componentes no repositório (matriz, §2) |
| 2 | ONS Operacional (IPDO e ACOMPH) | `ons_demanda_maxima` (seção 7 do IPDO); IPDO em si e ACOMPH sem fonte | carga da demanda máxima conferida em `hml` e `dev` (03/10, Gold com 116 linhas nos dois); decisão proposta no ADR 027, depende de aceite da Alup; IPDO e ACOMPH **não entregues** |
| 3 | ANEEL (tarifas homologadas e referência, PRC) | `aneel_tarifas`, `ace_prc` | 7 componentes; Silver e Gold conferidas em `dev` e `hml` em 03/10 |
| 4 | INMET (precipitação histórica por bacia) | `inmet_precipitacao`, `ons_bacia_contorno` | 7 componentes; carga e recorte por bacia conferidos em `hml` e `dev` em 03/10 (398 de 653 estações com bacia nos dois) |
| 5 | CPTEC (previsão de 7 dias) | nenhuma | **não entregue**: bloqueado também de dentro do GCP (ADR 028 e 029) |
| — | IGP-M (proposta de 28/05, minuta PDF de 23/07) | `bcb_igpm` | conferido em `hml` (03/10); `dev` pendente |

## 2. Matriz dos 7 componentes por fonte

Colunas 1 a 7 verificadas pela existência dos arquivos no `main` (caminhos abaixo da tabela). "Presente" quer dizer
que o arquivo existe; não quer dizer que a carga em ambiente foi conferida: isso está nas duas últimas colunas.

Legenda da conferência: `conferido (data, contagem, run)` = consultado no BigQuery pelo workflow `Conferir cargas` (somente leitura); `rodou no GitHub, não conferido` =
workflow terminou com sucesso, sem consulta ao BigQuery; `pendente (motivo)`.

| Fonte | Conector | Bronze | Silver | Gold | Testes | Agendamento | Dicionário | Conferência `hml` | Conferência `dev` |
|---|---|---|---|---|---|---|---|---|---|
| `ons_ear` | presente | presente | presente | presente (`armazenamento_e_afluencia_mensal`) | presente | presente | presente | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) |
| `ons_ena` | presente | presente | presente | presente (idem) | presente | presente | presente | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) |
| `ccee_pld` | presente | presente | presente | presente (`pld_mensal_submercado`) | presente | presente | presente | conferido (02/10, PLD real com 24 meses, segundo a auditoria de 02/10) | conferido (02/10, PLD real com 24 meses, segundo a auditoria de 02/10) |
| `ons_carga` | presente | presente | presente | presente (`carga_mensal_submercado`) | presente | presente | presente | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) | pendente (conferência não refeita neste relatório; evidência de 02/10 em `2026-10-02-auditoria-de-ponta-a-ponta.md`) |
| `ons_demanda_maxima` | presente | presente | presente | presente (`demanda_maxima_mensal_subsistema`) | presente | presente | presente | conferido (03/10/2026, Silver 3.480 linhas, de 2024-01-01 a 2026-05-19, run `37103149215`); Gold `demanda_maxima_mensal_subsistema`: 116 linhas | conferido (03/10/2026, Silver 3.480 linhas, mesmo intervalo; Gold `demanda_maxima_mensal_subsistema` 116 linhas, igual a `hml`; run `37107071613`, depois do Dataform de `dev` `37106857432`) |
| `aneel_tarifas` | presente | presente | presente | presente (`tarifa_vigente_distribuidora`) | presente | presente | presente | conferido (03/10/2026, Silver 327.763 linhas, de 2010-02-03 a 2026-09-22; Bronze extraiu 328.293; Gold 10.366 linhas; run `37103149215`) | conferido (03/10/2026, Silver 327.763 linhas, mesmo intervalo; Gold 10.366 linhas; run `37103208999`) |
| `ace_prc` | presente | presente | presente | presente (`prc_vigente_comercializadora`) | presente | presente | presente | conferido (03/10/2026, Silver 24 linhas, Gold `prc_vigente_comercializadora` 24 linhas, run `37103149215`) | conferido (03/10/2026, Silver 24 linhas, Gold 24 linhas, run `37103208999`) |
| `inmet_precipitacao` | presente | presente | presente | presente (`precipitacao_diaria_estacao`) | presente | presente | presente | conferido (03/10/2026, Silver 10.327.440 linhas, de 2024-09-01 a 2026-08-31; Gold `precipitacao_diaria_estacao` 430.310 linhas, 653 estações, run `37103149215`). A última execução (2026-09-01 a 2026-10-02) extraiu 0 linhas e terminou `SUCESSO`: o zip de 2026 do INMET só vai até agosto | conferido (03/10/2026, Silver 10.327.440 linhas, de 2024-09-01 a 2026-08-31; Gold `precipitacao_diaria_estacao` 430.310 linhas, 653 estações, 398 com bacia, 25 bacias; run `37107071613`). Igual a `hml` em todos os números. A última execução extraiu 0 linhas e terminou `SUCESSO`, como em `hml` |
| `ons_bacia_contorno` | presente | presente | presente | usada na Gold `precipitacao_diaria_estacao` (colunas `bacia` e `bacia_chave`, `ST_COVERS`) | presente | presente | presente | conferido (03/10/2026, 31 polígonos, run `37103149215`). Na Gold da chuva, 398 de 653 estações com bacia (61%) e 25 bacias distintas; 19 dos 23 `nomecurto` do EAR casam com as bacias | conferido (03/10/2026, 31 polígonos, run `37107071613`). Na Gold da chuva em `dev`, 398 de 653 estações com bacia e 25 bacias distintas, igual a `hml`; 19 dos 23 `nomecurto` do EAR casam |
| `bcb_igpm` | presente | presente | presente | presente (`igpm_mensal`) | presente | presente | presente | conferido (03/10/2026, Silver 25 linhas, de 2024-09-01 a 2026-09-01; Gold `igpm_mensal` 25 linhas, run `37103149215`) | pendente (0 linhas na Silver e na Gold, runs `37103208999` e `37107071613`; `api.bcb.gov.br` não resolve desde 03/10 ~03:40Z, a tentativa final de ingestão em `dev`, run `37106480778`, falhou; 12 execuções com erro nos últimos 3 dias) |

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
carga por ambiente não foi refeita aqui** (as quatro vieram de entregas anteriores, cuja evidência está na auditoria de 02/10).

Aditivo 01 (itens 12 a 19, fora da Onda 1): conferido em `dev` em 03/10/2026 (run `37103208999`), com as contagens da Silver na seção 7 e Dataform de `dev` `SUCCEEDED` sobre os dados. Em `hml` os oito têm 0 linhas (run `37103149215`): nunca foram carregados lá.

Ordem dos eventos em 03/10 (contexto das cargas; as contagens conferidas estão na seção 7): em `hml`, Dataform `37100814775` (05:47Z), depois as cargas de
`ons_bacia_contorno` e `ons_demanda_maxima`, depois Dataform `37101436318` (05:58Z, `SUCCEEDED`). Em `dev`, Dataform
`37101539114` (06:01Z, `SUCCEEDED`), depois as cargas das duas fontes (06:07Z e 06:11Z); **o Dataform de `dev` ainda não tinha rodado
depois delas**. As contagens foram conferidas depois, pelo workflow `Conferir cargas` (seção 7).

## 3. O que não foi entregue e por quê

- **IPDO (documento) e ACOMPH.** O IPDO público é um PDF preliminar de uso interno, só do dia, sem histórico; o conteúdo
  já está no lake, exceto a demanda máxima, que agora é a fonte `ons_demanda_maxima`. Para o ACOMPH não se encontrou
  origem pública; a hipótese de distribuição por cadastro **não foi verificada**. Proposta no ADR 027, sem aceite.
- **CPTEC.** 403 em todo caminho do webservice e a API nova sem DNS; causa desconhecida. Fora da Onda 1 até haver resposta
  do INPE, como decisão provisória (ADR 028). Em 03/10 a sonda de dentro do GCP (dev e hml) também recebeu 403, então o
  bloqueio não é do IP da máquina de desenvolvimento. Alternativas públicas avaliadas e descartadas (ADR 029): INMET
  previsão tem 5 dias e não traz chuva; Open-Meteo é gratuito só para uso não comercial.
- **Conferência no BigQuery:** feita em 03/10 (seção 7). A conferência final de `dev` (seção 7) fechou INMET, bacia e demanda máxima, com as Golds. Seguem pendentes o IGP-M em `dev` e o `bcb_juros`.
- **IGP-M em `dev`:** pendente por queda externa do BCB (0 linhas; 12 execuções com erro nos últimos 3 dias; a tentativa final, run `37106480778`, falhou).

## 4. Decisões que dependem da Alup ou de outras pessoas

1. Aceite dos ADRs 026 (recorte por bacia; 39% das estações sem bacia; 19 de 23 `nomecurto` do EAR casam), 027 e 028.
2. A pergunta sobre transmissão (TUST/RAP) nas tarifas.
3. Qual versão do contrato foi assinada: o .docx v3 (sem IGP-M) ou a minuta PDF de 23/07 (com IGP-M).
4. **Inconsistência a registrar, sem decisão aqui:** o painel mantém a Onda 1 como `estado = "entregue"` desde 25/09, visível
   ao cliente, e este relatório mostra os itens 2 (IPDO/ACOMPH) e 5 (CPTEC) da cláusula 4ª sem entrega, e o item 4
   (INMET por bacia) sem conferência. Se a Onda 1 continua constando como entregue é decisão comercial; o marco não foi alterado.

## 5. Riscos medidos

- **INMET:** 38% das horas vêm vazias (10.340 horas sem medição em março de 2025, conforme o dicionário); a origem não explica.
- **INMET, bacia:** 39% das estações ficam sem bacia (ADR 026); medido em `hml` em 03/10: 398 de 653 estações com bacia (61%).
- **INMET, setembro:** o zip de 2026 do INMET só vai até agosto; a Silver de `hml` termina em 2026-08-31 e a janela de 01/09 a 02/10 extrai 0 linhas.
- **Demanda máxima:** origem atrasada; o CSV de 2026 termina em 19/05/2026 (dicionário `ons_demanda_maxima.md`).
- **INMET, memória:** o 1Gi do Cloud Run é estimativa, o pico não foi medido (comentário em `infra/modules/scheduler/main.tf`).
- **BCB fora do ar** desde 03/10 ~03:40Z: `bcb_igpm` em `dev` pendente (12 execuções com erro em 3 dias) e os agendamentos diários de `bcb_juros` e do câmbio falham até voltar; `bcb_juros` teve 3 execuções com erro em 3 dias nos dois ambientes.

## 6. Próximo passo recomendado

A carga do INMET em `dev` terminou e o Dataform de `dev` rodou depois dela (seção 7, conferência final). Falta repetir o
`bcb_igpm` em `dev` quando o BCB voltar e rodar `Conferir cargas` de novo. Os marcos do painel seguem `previsto`: dependem
do aceite da Alup (ADRs 026 e 027) e das pendências abaixo.

## 7. Conferência de 03/10

Método: workflow `Conferir cargas` (PR #364), somente leitura no BigQuery, com a conta de serviço de deploy. `hml`: run
`37103149215`. `dev`: run `37103208999`, **com a carga do INMET em `dev` ainda em andamento naquele instante**; a coluna `dev` da tabela abaixo é essa primeira conferência e a final de `dev` (run `37107071613`) está na subseção seguinte. Os dois em 03/10/2026.
Contagens da Silver, salvo onde indicado.

| Fonte | `hml` | `dev` |
|---|---|---|
| `inmet_precipitacao` | 10.327.440 linhas, 2024-09-01 a 2026-08-31; Gold 430.310 linhas, 653 estações, 398 com bacia (61%), 25 bacias | 2.328.164 linhas, 2024-09-01 a 2025-02-28 (em andamento); Gold 0 |
| `ons_bacia_contorno` | 31 polígonos; 19 dos 23 `nomecurto` do EAR casam | 31 polígonos; mesmo cruzamento com o EAR |
| `ons_demanda_maxima` | 3.480 linhas, 2024-01-01 a 2026-05-19; Gold 116 | 3.480 linhas, mesmo intervalo; Gold 0 |
| `aneel_tarifas` | 327.763 linhas (Bronze extraiu 328.293); Gold 10.366 | 327.763 linhas; Gold 10.366 |
| `ace_prc` | 24; Gold 24 | 24; Gold 24 |
| `bcb_igpm` | 25 linhas, 2024-09-01 a 2026-09-01; Gold 25 | 0 linhas; 9 execuções com erro em 3 dias |
| Aditivo 01, itens 12 a 19 | 0 linhas nos oito | 3.009.821; 2.774.427; 2.363.064; 4.101.336; 18.998.832; 94.656; 1.206.288; 1.207.008 (ordem dos itens 12 a 19) |

Saúde da ingestão: `hml` com 45 fontes `OK`, 1 `SEM_SUCESSO` e 1 `FALHA_RECENTE`; `dev` com 53 `OK`, 2 `SEM_SUCESSO`,
1 `ATRASADA` e 1 `FALHA_RECENTE`. `bcb_juros` com erros nos dois ambientes (queda do BCB).

Pendente, com o motivo: IGP-M em `dev` (BCB fora do ar); `bcb_juros` (queda do BCB). As fontes
`ons_ear`, `ons_ena` e `ons_carga` seguem com a evidência da auditoria de 02/10, sem nova conferência.

### Conferência final de `dev`

Depois da carga do INMET em `dev` (9 janelas `success`) e do Dataform de `dev` `SUCCEEDED` (deploy `37106857432`, 03/10
07:38Z), o workflow `Conferir cargas` rodou de novo em `dev`: run `37107071613`. A tabela substitui, para estes itens, a
coluna `dev` acima. `hml` é a run `37103149215`.

| Item | `dev` (run `37107071613`) | `hml` (run `37103149215`) | Situação |
|---|---|---|---|
| `inmet_precipitacao`, Silver | 10.327.440 linhas, 2024-09-01 a 2026-08-31 | idem | conferido, igual |
| Gold `precipitacao_diaria_estacao` | 430.310 linhas, 653 estações, 398 com bacia, 25 bacias | idem | conferido, igual |
| `ons_bacia_contorno` | 31 polígonos; 19 dos 23 `nomecurto` do EAR casam | idem | conferido, igual |
| Gold `demanda_maxima_mensal_subsistema` | 116 linhas | 116 linhas | conferido, igual |
| `bcb_igpm` | 0 linhas (Silver e Gold) | 25 linhas | **pendente** (BCB fora do ar; 12 execuções com erro em 3 dias; tentativa final, run `37106480778`, falhou) |
| `bcb_juros` | 3 execuções com erro em 3 dias | 3 | **pendente** (queda do BCB) |
| Saúde da ingestão | 53 `OK`, 2 `SEM_SUCESSO`, 1 `ATRASADA`, 1 `FALHA_RECENTE` | 45 `OK`, 1 `SEM_SUCESSO`, 1 `FALHA_RECENTE` | sem mudança em `dev` desde a run `37103208999` |

Não contadas pela conferência: as Golds dos oito itens do Aditivo 01. Segue pendente a decisão de aceite da Alup sobre os
ADRs 026, 027 e 028. O estado da Onda 1 no painel (`entregue`) não muda.

## 8. Chuva por bacia e bacia mais próxima (conferido em 03/10/2026)

Método: workflow `Conferir cargas` (somente leitura), runs `37123673126` (hml) e `37123677588` (dev), depois do deploy
e do Dataform dos dois ambientes. Os números são **iguais em dev e hml**.

| Gold | Resultado conferido |
|---|---|
| `precipitacao_diaria_estacao` | 430.310 linhas, 653 estações, 398 com bacia exata, 25 bacias |
| bacia mais próxima (só sem bacia exata) | 255 estações (653 menos 398, como esperado); distância mediana **62,0 km**, máxima **690,6 km** |
| `precipitacao_diaria_bacia` | 17.727 linhas (bacia e dia), 25 bacias, de 2024-09-01 a 2026-08-31; **1.216 dias de bacia sem nenhuma estação completa** (média nula) |

Leitura honesta: a bacia mais próxima é aproximação **sem limite de distância**; a mediana de 62 km é razoável, mas a
máxima de 690 km mostra estações que não deveriam ser atribuídas a nenhuma bacia sem um corte. Quem usa filtra por
`distancia_bacia_km`; o corte é decisão da Alup. A média por bacia é **regra provisória** (ADR 026).

## 9. As três cargas pedidas em 02/10 (concluídas e conferidas em 05/10/2026)

Pedido do e-mail de 02/10: concluir os carregamentos de IGP-M, Tarifas Homologadas e PRC até 05/10. Método: `Conferir cargas`
(somente leitura). Runs de 05/10: `37306309196` (dev, contagens) e `37307339177` (dev) e `37307344159` (hml), com os valores do IGP-M.

| Carga | dev | hml |
|---|---|---|
| Tarifas Homologadas (`aneel_tarifas`) | 327.763 linhas; Gold `tarifa_vigente_distribuidora` 10.366 | igual |
| PRC (`ace_prc`) | 24 preços; Gold `prc_vigente_comercializadora` 24 | igual |
| IGP-M (`bcb_igpm`) | 25 meses (2024-09 a 2026-09); Gold `igpm_mensal` 25 | igual |

IGP-M em dev: o BCB voltou em 04/10; o vigia disparou a carga às 16:15 (execução `SUCESSO`, 25 extraídas, 0 inválidas, 25
carregadas) e o deploy de dev gerou a Gold. Valores conferidos contra a API do BCB (série 189): jul/2026 = -1,16,
ago/2026 = -0,22, set/2026 = 1,57, iguais em dev e hml. O plano B (reprocessar o raw do hml em dev) não foi necessário.
