# Estado do projeto

Atualizado em **2026-09-18** · **A3 chega ao 9º dia útil de atraso sem confirmação de entrega** —
vencido em 04/09, previsão da Alup para 18/09, contagem da cláusula 3ª em
curso; **passou dos 5 dias úteis, o cronograma está postergado**. Em 16/09 a
ness. enviou à Alup **as contas que devem receber os papéis no projeto GCP**
(ver A3 abaixo): o lado da ness. de A3 está entregue, e o que falta é o
provisionamento — que a Alup informou, no mesmo dia, estar **em processo de
liberação**. Em 14/09 a Alup entregou a documentação das APIs (**A2
encerrada e A8 atendida**) e em 15/09 a **matriz RACI do projeto**
([`raci.md`](raci.md)), que não altera prazo nem desbloqueia frente de
trabalho. A conferência de 18/09 não encontrou confirmação posterior de entrega
do GCP, billing ou planilhas. Referência do código: `main` em `2d0f7c6`, de
16/09. O feriado de 07/09 não entra na contagem: primeiro dia útil de atraso
em 08/09. G1 encerrou na reunião de 10/09 e não é bloqueio atual.

## Reparos técnicos durante a espera pelo ambiente — 18/09

A liberação do GCP permanece sob responsabilidade da Alup. O plano de
[correção dos achados técnicos](planos/2026-09-18-correcao-achados-tecnicos.md)
implementa o bloqueio da Gold por assertions, persistência completa do raw
antes do Bronze, replay em fluxo e deploy sem Composer nem imagem `latest`.

Validação local: **983 testes aprovados**, 264 ignorados, **94% de cobertura**;
62 dependências de assertions comprovadas no Dataform; Ruff, Bandit, auditoria
de dependências e Terraform validate aprovados. Desses testes ignorados, 248
são regras SQL que não se aplicam à camada testada. Esses resultados não
representam carga real nem homologação. O novo caminho faz uma leitura GCS
adicional por ingestão; tempo, memória e custo precisam ser medidos em dev.

Melhoria preexistente identificada na revisão: os cadastros `ccee_perfil` e
`ons_capacidade` dependem de `_data_retrato` preenchido durante a extração;
o replay em instância nova precisa recuperar a referência do retrato.
Tratar com regressão específica, sem inferir a data a partir do dia atual.

Este arquivo responde "onde estamos e o que trava o próximo passo". Detalhe de
escopo e estimativa fica em [`plano-execucao.md`](plano-execucao.md); o que sai
em cada semana, em [`plano-semanal.md`](plano-semanal.md); os relatórios emitidos
para a contratante, em [`relatorios/`](relatorios/);
contexto para agentes, em [`../AGENTS.md`](../AGENTS.md).

---

## 1. Entregue e verificado

### Framework e ferramental

| Item | Onde | Verificação |
|---|---|---|
| Runner de ingestão (janela, raw no GCS, validação, colunas técnicas, carga, log) | `src/core/` | Suíte local de 18/09: 956 aprovados, 264 pulados, 93% de cobertura; [registro da verificação](relatorios/2026-09-18-reconciliacao-acompanhamento.md). Integrações puladas não comprovam operação real |
| Caminho de banco relacional (Oracle/MySQL/**SQL Server**) para a Onda 3 | `src/core/banco.py` | ADR 008 e adendo de 04/09; 20 testes sem rede; **nenhuma conexão real** — depende de VPN (A7). Compose e testes de integração prontos em `tests/integration/` |
| Replay do raw sem nova chamada à fonte | `alupdata reprocessar-raw`, `src/core/storage.py` | testes locais com JSONL gzip; falta validar contra GCS real |
| CLI única (`alupdata listar` / `ingerir`) | `src/cli.py` | 23 entidades verificadas com dados reais em dry-run; TempoOK com contrato da API verificado |
| Scaffolding dos 7 componentes | `make novo-conector` | usado nas fontes novas |
| Transformações Dataform | `definitions/`, `make dataform-compile` | DDL Bronze, views Silver e tabelas Gold; execução no GCP ainda pendente |
| Motor S2 Data Intake (planilha CSV/XLSX sob template) | `src/core/planilha.py`, `src/conectores/planilha.py` | 19 testes; templates concretos dependem de G3/#142 |
| Painel de saúde do lake (frescor, confiabilidade, volumetria) | `definitions/gold/saude_ingestao.sqlx`, rota `/lake` | ADR 006; ferramenta de sustentação, não escopo faturado |
| Portal falha fechado sem identidade do IAP | `src/portal/app.py` | 7 testes; deploy sem autenticação ou IAP mal configurado devolve 403 em vez de servir dado |
| Log estruturado com correlação por execução | `src/core/observabilidade.py` | 8 testes; verificado contra a API do BCB |
| Alertas (falha, silêncio, inválidos em alta) | `infra/modules/monitoramento` | `terraform validate` limpo; destinatários recebidos em 11/09; ativação depende de A3/#87 |
| Painel no Cloud Monitoring e orçamento com alerta de custo | `infra/modules/monitoramento` | orçamento precisa do `billing_account` da Alup (A3) |
| Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM | `infra/` | IAM restringido por recurso; Terraform 1.15.8 `fmt` e `validate` limpos |
| CI/CD: lint, testes, Bandit, pip-audit, Gitleaks, Terraform | `.github/workflows/` | workflow de deploy ordenado; consultar execução datada de CI; workflow de acompanhamento verde não comprova sincronização (§7) |
| Imagem da CLI | `Dockerfile` | build local não executado: Docker Desktop sem daemon ativo |
| Campos de acompanhamento semanal do GitHub Projects | `scripts/campos_projeto.py`, `runbook/acompanhamento-semanal.md` | 12 testes; script idempotente. **Os cinco campos criados no quadro em 04/09** — Horas, Semana, Validado, Correções e Atraso |
| **FinOps F0** — rótulo de custo por fonte no job do BigQuery | `src/core/bigquery.py` (`rotulos()`) | 6 testes; precisa existir **antes** do 1º apply, custo gasto não se rateia depois |
| **8 domínios analíticos** e dimensões comuns fechadas (plano 0.10 e 0.11) | `docs/arquitetura/dominios-analiticos.md`, `visao-geral.md` | Itens de Onda 0 que estavam desbloqueados desde 11/09. Duas lacunas nomeadas: de-para de usina (Alup — encolhida em 15/09 para só a sigla interna) e mês CCEE (ness.) |
| Domínios corrigidos para os do **B1**, e a abrangência do dado escrita | `docs/arquitetura/dominios-analiticos.md`, `src/portal/custo.py` | A primeira versão derivava os domínios de A1. São os do B1 — 8 domínios em 11 linhas, três com responsáveis distintos por subtema. As 6 coligadas respondem pelo faturamento e não delimitam o dado |
| Base `CceeCsvCkan`: CKAN, fluxo, gzip, decodificação por linha, janela por mês | `src/conectores/ccee_ckan.py` | 20 testes; lida dos arquivos reais em 14/09 — encoding misto, gzip mensal, vírgula no CVU. Corrigida duas vezes durante a fila: gzip de transporte da CDN (`_SemErroAoFechar`) e estreitamento do `except ValueError` ao fluxo fechado |
| ADR 016 **aceita**: `versao_publicacao` do CKAN (`last_modified`, opção B) em toda entidade mensal; Silver vigente + view `_historico` | `definitions/silver/ccee_contabilizacao_perfil*.sqlx` | replay de raw antigo deixa de rebaixar a vigente |
| Parsing que pode falhar mora no schema, não no conector | Silver das entidades novas (Tasks 6–8) | linha malformada conta como inválida em vez de derrubar o mês inteiro; aprendido na Task 5, aplicado nas Tasks 6–8 |
| **CEG canônico** e o de-para de usina que o lake monta sozinho | `src/core/ceg.py`, `definitions/gold/de_para_usina.sqlx` | Medido contra as origens reais em 15/09: a ANEEL publica o sufixo do CEG com um dígito e o ONS com dois, e o JOIN devolvia **zero** de 2.047 usinas. Normalizado na ingestão, casam **1.946 (95,1%)** do cadastro de capacidade e **369 de 375 (98,4%)** da geração horária; 8 testes, 0 inválidos nas três fontes |

### Conectores (7 componentes cada, exceto onde indicado)

| Fonte | Formato | Volume verificado | Agendamento |
|---|---|---|---|
| **BCB/PTAX** | JSON diário | 3 registros / 3 dias | diário 9h, janela 3 dias |
| **BCB/Selic e CDI** | JSON diário, SGS séries 11 e 12 | **16 registros / 12 dias** (8 dias úteis × 2 séries), 0 inválidos, contra a API real | diário 9h30, janela 5 dias |
| **IBGE/IPCA** | JSON aninhado, mensal | 12 registros / 6 meses | dia 12, janela 90 dias |
| **ANEEL/SIGA** | cadastro paginado | **25.263 registros**, 0 inválidos, 28s | semanal, segunda 7h |
| **ONS/carga** | CSV anual remoto | 28 registros / 7 dias | diário 8h, janela 30 dias |
| **CCEE/PLD** | CSV anual remoto (ISO-8859-1), descoberto via CKAN | **288 registros / 3 dias**, 0 inválidos, contra a API real | mensal, dia 5 às 9h, janela 120 dias |
| **CCEE/perfil** | cadastro CSV (ISO-8859-1), via CKAN | **60.509 registros**, 0 inválidos, contra a API real | semanal, terça 7h |
| **Hubspot/negócios** | JSON paginado, CRM | **não executado** — sem token (A9) | a cada 6h, janela 2 dias |
| **BBCE/curva forward** | JSON por pregão, sessão JWT | **não executado** — sem acesso (A7) | dia útil 20h, janela 7 dias |
| **TempoOK/boletins** | PDF por download, catálogo no Bronze | **contrato verificado contra a API real**; 0 boletins ingeríveis — o acervo alcançável para em 26/10/2022 (ADR 019, adendo) | diário 11h, janela 5 dias |
| **CCEE/agente** | CSV anual, UTF-8 e ISO-8859-1 misturados por linha, via CKAN | **32.886 registros / 2 meses**, 0 inválidos, 4,2 s, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/exposição financeira** | CSV anual, ASCII, série mensal sem agente, via CKAN | **7 registros / 7 meses**, 0 inválidos, 0,9 s, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/contabilização por perfil** | CSV anual, UTF-8 e ISO-8859-1 misturados por linha, com recontabilização (ADR 016), via CKAN | **94.710 registros / 2 meses**, 0 inválidos, 11,8 s, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/geração por usina** | CSV mensal, gzip, via CKAN | **2.964.096 registros / 1 mês**, 0 inválidos, 177,7 s **em dry-run** (raw e carga pulados; não é o tempo da execução real), contra a API real | mensal, dia 7 às 3h, janela **40 dias** (cobre o mês fechado com folga sem abrir um quarto recurso mensal), **1Gi/2 vCPU medidos**, não mais premissa: com o runner em fatias o pico é de 225 MiB (#152) |
| **CCEE/montantes contratados** | CSV anual, UTF-8 e ISO-8859-1 misturados por linha, via CKAN | **53.267 registros / 2 meses**, 0 inválidos, 4,8 s, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/consumo varejista** | CSV anual, via CKAN | **6.664 registros / 2 meses**, 0 inválidos, 1,2 s, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/ESS** | CSV anual, série mensal sem agente, via CKAN | **7 registros / 7 meses**, 0 inválidos, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/energia de reserva (EER)** | CSV anual, série mensal sem agente, via CKAN | **7 registros / 7 meses**, 0 inválidos, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **CCEE/CVU estrutural** | CSV anual, delimitador vírgula, via CKAN | **805 registros / 2 meses**, 0 inválidos, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
| **ONS/EAR** | CSV por ano, reservatório por submercado, via CKAN | **0 inválidos**, contra a API real | diário, janela 30 dias |
| **ONS/ENA** | CSV por ano, afluência por submercado, via CKAN | **0 inválidos**, contra a API real | diário, janela 30 dias |
| **ONS/geração por usina** | CSV mensal, horário, por usina | **533.832 linhas / 1 mês**, 0 inválidos; `val_geracao` vem vazio em ~12% das linhas (usina sem medição na hora) e vira NULL em vez de zero; **pico de 440 MiB medido** | mensal, dia 7 às 4h, janela 40 dias, 1Gi |
| **ONS/capacidade instalada** | CSV de cadastro, por unidade geradora, via S3 | **5.688 registros**, 0 inválidos; aceitar `PY` (Itaipu/Paraguai, 10 unidades) fez o cadastro ganhar **7.000 MW**, de 200.233 para 207.233 MW | semanal, segunda 8h |
| **ONS/disponibilidade por usina** | CSV mensal, horário, por usina | **117.480 registros / 1 mês**, 0 inválidos, 29,8 s; **pico de 226 MiB medido**; CEG em 100% das linhas, 98,1% casando com a ANEEL | mensal, dia 7 às 5h, janela 40 dias, 1Gi |
| **ONS/constrained-off eólico** | CSV mensal, **passo de 30 min**, por usina ou conjunto | **227.664 registros / 1 mês**, 0 inválidos, 60,1 s; **pico de 389 MiB medido**; 47,5% das meias-horas sem restrição (usina gerando livre) | mensal, dia 7 às 6h, janela 40 dias, 1Gi |
| **ONS/constrained-off fotovoltaico** | mesmo schema da eólica, 24 colunas | **121.536 registros / 1 mês**, 0 inválidos, 36,1 s; **pico de 275 MiB medido** | mensal, dia 7 às 6h30, janela 40 dias, 1Gi |

**Vinte e três das vinte e seis falaram com a API real** em dry-run: as
dezesseis de 14/09 — as seis originais, as nove entidades novas da CCEE
(ADR 021) e o `bcb_juros` — somadas às **sete fontes do ONS de 15/09** (EAR,
ENA, geração horária, capacidade instalada, disponibilidade por usina e o
constrained-off de eólica e de fotovoltaica). Hubspot e BBCE seguem as exceções: os 7 componentes
existem, escritos contra a documentação, e o teste de integração está `skipif`
até a credencial chegar (A9 e A7). No BBCE falta inclusive o **host**, que não
consta da documentação pública e vem junto com o acesso.

O TempoOK é um caso à parte: **falou com a API e o contrato de dados está
verificado** — caminho, ausência por 404, TLS, estabilidade do `sha256` —, mas
o acervo alcançável termina em 26/10/2022, então não há boletim para ingerir
(A10).

Não há carga em BigQuery real registrada nem confirmação de entrega do ambiente GCP até esta conferência.

### Dimensões comuns

| Dimensão | Fonte | Situação |
|---|---|---|
| `data_referencia` | todas | ok |
| `periodo_apuracao` | todas | ok |
| `codigo_usina` | ANEEL/SIGA (CodCEG) | ok |
| `submercado` | ONS (N, NE, S, SE) | ok |
| `agente_ccee` | CCEE (`lista_perfil_v1`) | **ok desde 14/09** — `ccee_perfil` entregue, 60.509 perfis verificados contra a API real. **As cinco dimensões comuns têm fonte** |
| `periodo_apuracao_ccee` | a origem, onde ela declara | **nova em 14/09** — sexta dimensão. Hoje só o `ccee_pld` a preenche, pelo `MES_REFERENCIA`; nas demais é nula. A Silver do PLD exige que ela coincida com o calendário civil, e é essa asserção que avisa no dia em que os dois calendários divergirem |

### Documentação

ADRs 001–021 · 25 dicionários de fonte para 26 entidades e 2 dicionários técnicos com [índice e linhagem](dicionario-dados/README.md) · plano de execução · runbook de deploy,
de primeiro deploy e de acompanhamento semanal ·
[`proximos-passos.md`](proximos-passos.md) como fila de execução ·
`AGENTS.md` como contexto canônico · skills do projeto e shortlist do Google.

**Matriz RACI do projeto recebida da Alup em 15/09** e transcrita em
[`raci.md`](raci.md) — governança por atividade e por fase. Não reabre nem
fecha pendência: A5 segue encerrada e a lacuna 2 de
[`interlocutores.md`](interlocutores.md) (RACI **por domínio de dado**)
continua aberta. O documento **corrobora por escrito que landing zone, IAM,
rede e segurança são A/R da TI da Alup** — sustenta o registro de atraso de A1
e A3. Três divergências a conciliar: camada "Core" por Gold, "Fase" por Onda e
um **Comitê** sem membros como accountable da passagem de fase e da sustentação
— além do Google como accountable da arquitetura, que a ness. recomenda
rebaixar a consultado. Os dois pontos que precisam de resposta da Alup estão na
[issue #150](https://github.com/nessenergy/Alupdatalake/issues/150); o de-para
Fase↔Onda e Core↔Gold está resolvido em [`raci.md`](raci.md) §5.

Material de reunião: baralho de kickoff e **baralho de revisão arquitetural em
GCP** (`apresentacoes/revisao-arquitetural-gcp.html`) — origem, tratamento e
destino, com os oito invariantes e a pauta de perguntas. **Enviado ao Google em
04/09**; G1 foi encerrada pela revisão de 10/09, cujas decisões estão nas ADRs vigentes.

---

## 2. Aberto — ação da ness.

| # | Item | Bloqueado por |
|---|---|---|
| N1 | Preparar contrato de dados das fontes das Ondas 2 e 3 | TempoOK e **BBCE já implementados** (BBCE: [PR #131](https://github.com/nessenergy/Alupdatalake/pull/131)); faltam acervo recente (#129), acesso/host BBCE (#23) e documentação/acessos das fontes internas (A7) |
| N2 | Portal MVP: ligar contra o BigQuery e publicar no Cloud Run | escopo cravado na ADR 005; a tela existe e roda com provedor simulado — falta o ambiente GCP (A3) |
| N3 | Primeiro `terraform apply` real e primeiro deploy da imagem | ambiente GCP (A3) |
| N4 | Validar replay contra objeto real no GCS e conferir linhagem no BigQuery | ambiente GCP (A3) |
| N5 | Construir e executar a imagem no ambiente de desenvolvimento | Docker Desktop não disponibilizou o daemon nesta estação |

---

## 3. Aberto — ação da Alup

| # | Item | Efeito enquanto não vier | Referência |
|---|---|---|---|
| A1 | **Conceder à ness. os papéis de bootstrap** em cada projeto (ADR 015, revista em 11/09): com eles a ness. configura o WIF (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`), o bucket de state, o Artifact Registry e a SA de deploy | o bootstrap não roda e o workflow de deploy não autentica | ADR 015, `runbook/primeiro-deploy.md` §0 |
| ~~A2~~ | ~~**Decidir sobre a CCEE InfoMercado**~~ | **Encerrada em 14/09** — era filtro de cliente não identificado, não bloqueio de IP nem credencial. Resolvido por cabeçalho no `src/core/http.py` | [ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md), [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) |
| A3 | **Projetos GCP `dev`, `hml` e `prod`**: a Alup cria, vincula faturamento e concede papéis; a ness. executa APIs, WIF, Artifact Registry, state e demais recursos do bootstrap (ADR 015). **Em 16/09 a ness. enviou as quatro contas que devem receber os papéis** (`gptorres@`, `resper@`, `bertuzzi@`, `gpaz@`, todas `@ness.com.br`), pelo Google Chat, fechando a única parte do pedido que dependia de nós. **Liberação em processo do lado da Alup, informado em 16/09** — saiu de "não iniciado" para "em andamento", o que é o que sustenta a previsão de 18/09 | nada sobe; Onda 0 não homologa | plano 2.2 (0.13), [registro de 09/09](relatorios/2026-09-09-esclarecimento-e1-e2.md), [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| ~~A4~~ | ~~**Questionário de Gaps** (47 perguntas)~~ | **Respondido em 11/09.** Definir os 8 domínios a partir das respostas é tarefa da ness. (plano 0.10), não insumo pendente | [`questionario-gaps.md`](questionario-gaps.md) |
| ~~A5~~ | ~~**RACI e data owners** por domínio~~ | **Respondido em 11/09** (item B1 do questionário) | [`interlocutores.md`](interlocutores.md) |
| ~~A6~~ | ~~**Ferramenta de BI** definida~~ | **Respondido em 11/09**: Power BI hoje; Looker Studio ou fronts internos na Fase 2 (item G1) | [`questionario-gaps.md`](questionario-gaps.md) |
| A7 | Abrir **já** os pedidos de token (Onda 2) e VPN/credencial (Onda 3) | é o maior risco do contrato: atraso dispara ociosidade de 4h/dia | plano §7 |
| ~~A8~~ | ~~**Documentação técnica de BBCE e TempoOK**~~ | **Atendida em 14/09** — BBCE documentado em Postman; TempoOK sem documentação publicada, mas com exemplo suficiente. Resta só a credencial do BBCE, que é A7 | [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) |
| A9 | **Token do Hubspot** (private app) no secret `alupdata-hubspot-api-token` | o conector está pronto e parado; nenhuma linha de CRM entra no lake | plano 2.3 (2.3) |
| A10 | **Verificar com o TempoOK o acesso ao acervo recente** — o token entregue em 14/09 alcança boletins só até 26/10/2022 | o conector está pronto e verificado, mas ingere zero boletins; a fonte não fecha na Onda 2. **Resolver isto antecipa a rotação do token** (gatilho 1 da [ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md)): com acervo corrente, o alcance da credencial muda de patamar | [ADR 019](arquitetura/decisoes/019-boletim-do-tempook-como-arquivo.md), [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §4.1 |
| A11 | **De-para de usina** — falta só **sigla interna ↔ CEG** | Encolheu em 15/09: o lado CEG ↔ nome ANEEL ↔ nome ONS está em `gold.de_para_usina`, montado do dado público (95,1% do cadastro de capacidade do ONS casa com a ANEEL; 98,4% da geração horária). Segue bloqueando `ccee_geracao_usina` e `ccee_cvu_estrutural`, que guardam `codigo_parcela_usina` com `codigo_usina` nulo | Lacuna 1 (`dominios-analiticos.md` §5.1), [#141](https://github.com/nessenergy/Alupdatalake/issues/141) |
| A12 | **Exemplos reais das planilhas** (G3, prometidos até 18/09) | além do item 4.1 da Onda 4, é o que permite conferir o escopo de dado item a item contra os 13 conectores. O escopo declarado é "o mapeado na planilha da proposta"; se a planilha nomear algo fora dos 13, é aditivo, e a distinção precisa ser feita antes da medição | [#142](https://github.com/nessenergy/Alupdatalake/issues/142), [`questionario-gaps.md`](questionario-gaps.md) G3, [`arquitetura/dominios-analiticos.md`](arquitetura/dominios-analiticos.md) §2 |

> **Cláusula 3ª**: atraso > 5 dias úteis posterga o cronograma; > 5 dias úteis em
> VPN/credencial gera taxa de ociosidade de 4h/dia (R$ 256/h); > 20 dias
> corridos suspende os serviços. Registrar a data de cada pedido **no dia em que
> o atraso começa**, não quando vira problema.

---

## 4. Onde estamos no contrato

Faturamento é por **homologação da Onda** (cláusula 6ª) — carga real em BigQuery
e aceitação da Alup, não volume de código. **Nenhuma onda homologou ainda.** A
coluna "técnico" abaixo é a nossa leitura de prontidão de trabalho, calculada
sobre as horas do plano de execução; não é métrica rastreada formalmente no
quadro. Na consulta de 18/09, os sete lançamentos de `Horas` somam 100h,
com **origem a conferir**; não são horas realizadas comprovadas. As estimativas
abaixo usam os pesos orçados dos itens tecnicamente prontos, não apontamento
de tempo, quantidade de cartões ou PRs.

| Onda | Escopo | Técnico | Situação |
|---|---|---|---|
| 0 — Fundação | 90h · marco 15,52% | **~82%** | Framework, CI/CD, domínios, dimensões comuns e RACI entregues (peso estimado de ~74h do plano, não horas realizadas). Restam itens com peso estimado de ~16h — provisionar o GCP, 1º deploy, ligar o portal — **100% bloqueados por A3**, em liberação desde 16/09 |
| 1 — Mercado base | 120h · marco 20,69% | **escopo original 100%** | As 4 fontes públicas + CCEE planejadas estão entregues. As sete novas entidades do ONS (15/09) e as nove entidades da ADR 021 (14/09) ampliam a cobertura técnica considerada na estimativa original; a conciliação com as **120h orçadas** e as 13 fontes continua pendente — por demanda dos domínios do B1, não porque a onda pedisse |
| 2 — APIs credenciadas | 110h · marco 18,97% | **~50% escrito, 0% executável** | Hubspot, TempoOK e BBCE têm os 7 componentes escritos contra documentação, não contra API real credenciada. Só o TempoOK de fato conversou com a origem — e está travado por outro motivo, o acervo (#129). Esse indicador não representa horas realizadas nem percentual de homologação |
| 3 — Sistemas internos | 155h · marco 26,72% | **0%** | Caminho de banco pronto (ADR 008: Oracle, MySQL e SQL Server, drivers puro-Python, testado sem rede); **nenhuma fonte iniciada** — bloqueada por VPN e credencial (A7, vence 25/09). VPN também depende de A3: mesmo com credencial em mãos, a rota de rede pode continuar bloqueada até o ambiente existir |
| 4 — Planilhas e handoff | 105h · marco 18,10% | **~29%** | Motor S2 Data Intake pronto (peso estimado de ~30h de 105h, não horas realizadas), adiantado por não depender de insumo. O resto é sequencial — Knowledge Catalog e handoff dependem das outras ondas; Gold sem KPI nesta fase (ADR 012), templates dependem da G3 (#142, vence 18/09) |

> **Leitura da tabela.** Quatro das cinco ondas já têm entrega técnica. O que
> nenhuma linha acima mede é homologação: onda fecha por aceitação e carga
> real, não por volume de código nem por percentual de horas. O projeto está
> simultaneamente adiantado em entrega e parado em homologação — e o segundo
> é o que define o marco de faturamento (cláusula 6ª).

---

## 5. Preparar as fontes bloqueadas: o que a sondagem mostrou

O plano previa escrever schema e fixture das fontes das Ondas 2 e 3 a partir da
documentação pública, para que a chegada do token fosse "ligar e ajustar". A
sondagem de 2026-08-25 mostra que isso **só se sustenta para uma delas**:

| Fonte | Documentação/API alcançável? | Dá para escrever o contrato hoje? |
|---|---|---|
| CCEE InfoMercado | **sim, desde 14/09** — o 403 era filtro de cliente não identificado; o CKAN de dados abertos expõe 204 conjuntos, sem credencial | **sim, e sem depender de token** — ADR 018 |
| BBCE | **sim, desde 14/09** — coleção Postman completa | implementado no PR #131; faltam acesso e host (A7) |
| TempoOK | **sem documentação publicada**, mas com exemplo de consulta e token entregues em 14/09 | **feito** em 14/09 — ADR 019 |
| Hubspot | sim — API e docs públicas | **feito** em 2026-08-26 — ver abaixo |

O Hubspot foi entregue nesse regime em 2026-08-26: conector, Bronze, Silver,
Gold, testes (unitário sem rede + integração `skipif`), agendamento e
dicionário. Quando o token de A9 chegar, a tarefa é rodar e conferir, não
começar. O que **não** foi possível verificar sem credencial está listado no
fim de `dicionario-dados/hubspot_negocios.md`.

Escrever schema por adivinhação seria pior que não escrever: cria retrabalho
com aparência de progresso. **O que destravava era a documentação**, e ela
chegou em 14/09 — três das quatro linhas acima mudaram de lado no mesmo dia.
Restam bloqueadas por credencial, não por desconhecimento: BBCE (A7) e Hubspot
(A9).

## 5.1 Ressalva importante

Tudo foi validado **localmente e em dry-run**. O primeiro `terraform apply` e a
primeira carga real são onde aparecem os erros que teste local não pega: IAM
insuficiente, cota de API, permissão de bucket, formato que o BigQuery recusa.
**A Onda 0 não deve ser declarada homologada antes disso rodar** — o critério
está na skill `homologacao-onda`.

O replay do raw, a restrição de IAM e a nova ordem do deploy foram validados
por testes locais e inspeção estática. Ainda não foram exercitados pelas APIs
reais do GCS, IAM, Cloud Run ou BigQuery. O registro detalhado da rodada está em
[`relatorios/2026-08-30-preparacao-local-sem-gcp.md`](relatorios/2026-08-30-preparacao-local-sem-gcp.md).

---

## 6. Painel de dependências — prazo e efeito

Ordenado por data em que o atraso passa a custar. Prazos derivados do
[`plano-semanal.md`](plano-semanal.md); efeitos, da cláusula 3ª do contrato.

| # | Insumo | Responsável | Prazo útil | Efeito de passar do prazo |
|---|---|---|---|---|
| A3 | Projetos GCP (`dev` primeiro, depois `hml` e `prod`) criados, vinculados ao faturamento e com os papéis de bootstrap concedidos à ness. — APIs, IAM, WIF, Artifact Registry e state passaram à ness. em 11/09 (ADR 015) | Alup | **04/09 — vencido** | **Entrega não confirmada nesta conferência. Atraso registrado em 04/09**; 1º dia útil de atraso em 08/09, 5º em 14/09. Historicamente a Alup condicionou A3 a G1, encerrada em 10/09; esse elo não é mais bloqueio. Previsão de A3: 18/09, sem confirmação até a conferência. Em 09/09 a Alup levantou dúvida sobre quem cria o projeto (E1) e de quem é a `billing_account` (E2); **ambas são da Alup, esclarecido no mesmo dia** — ver [registro de 09/09](relatorios/2026-09-09-esclarecimento-e1-e2.md). S2 e S3 escorregam inteiras; Onda 0 não homologa; > 5 dias úteis posterga o cronograma |
| A9 | Token Hubspot no secret `alupdata-hubspot-api-token` | Alup | 11/09 | conector pronto segue parado; item 2.3 não fecha |
| ~~A4~~ | ~~Questionário de Gaps respondido~~ | Alup | 11/09 | **Respondido no prazo** |
| ~~A5~~ | ~~Matriz RACI e data owners~~ | Alup | 11/09 | **Respondido no prazo** |
| ~~A6~~ | ~~Ferramenta de BI definida~~ | Alup | 11/09 | **Respondido no prazo**: Power BI |
| [#87](https://github.com/nessenergy/Alupdatalake/issues/87) | Destinatários de alerta e `billing_account` | Alup | destinatários: 11/09, atendido; billing: 18/09 | destinatários recebidos em 11/09; billing previsto para 18/09, sem confirmação de entrega; ativação depende de A3 |
| — | Variáveis do GitHub (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`) | ness. | depende de A3 | deploy não autentica. **Branch protection resolvida em 11/09**: a organização passou ao GitHub Enterprise e a `main` exige PR e seis verificações, com force push e exclusão bloqueados (ADR 010, encerrada) |
| ~~A2~~ | ~~Decisão sobre a CCEE~~ | Alup | ~~18/09~~ | **Encerrada em 14/09, antes do prazo.** As 32h voltaram a andar; nenhuma das quatro alternativas foi necessária ([ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)) |
| ~~G1~~ | ~~Resposta do Google à revisão arquitetural~~ | Google | **10/09 — encerrada** | Reunião realizada e recomendações incorporadas às ADRs; preservado o registro histórico do atraso na S1 |
| A7 | Pedidos de token (Onda 2) e VPN/credencial (Onda 3) **abertos** | Alup | 25/09 | maior risco financeiro: ociosidade de 4h/dia (R$ 256/h) |
| ~~A8~~ | ~~Documentação técnica de BBCE e TempoOK~~ | Alup | ~~25/09~~ | **Atendida em 14/09, onze dias antes do prazo.** A Onda 2 pode ser escrita antes do token, como o plano previa |

Acompanhamento consolidado destas linhas na [issue #57](https://github.com/nessenergy/Alupdatalake/issues/57).

**Registro de atraso**: a data de cada pedido deve ser anotada no dia em que o
atraso começa, não quando vira problema. É o que sustenta postergação,
ociosidade ou suspensão numa medição.

### A7 em detalhe — o insumo que custa por dia parado

Ele aparece no painel como uma linha, e a linha não diz o tamanho do que está
pendurado nela.

> **Atenção à sigla.** Este A7 é a **pendência nº 7 deste painel**. Existe um
> **outro A7**, no bloco A do [Questionário de Gaps](questionario-gaps.md), que
> pergunta a granularidade mínima de decisão e foi respondido em 11/09. Mesma
> sigla, assuntos diferentes, e os dois convivem na documentação.

| | |
|---|---|
| **O que se pede** | a Alup abrir os chamados internos de **token** (Onda 2) e de **VPN/credencial read-only** (Onda 3) |
| **Prazo** | 25/09 |
| **Estado** | em 11/09 (item C1) a Alup informou que os pedidos **ainda não tinham sido abertos**, e que seriam a partir de 14/09. Faltam os números de chamado |
| **Exposição** | ociosidade de **4h/dia a R$ 256/h — R$ 1.024 por dia parado** acima de 5 dias úteis |

**O que ele destrava**: acesso ao BBCE e às quatro fontes internas. O TempoOK
já recebeu token; a pendência atual é acervo recente (A10/#129), e o Hubspot
está separado em A9. Referências: BBCE ([#23](https://github.com/nessenergy/Alupdatalake/issues/23)),
TempoOK ([#25](https://github.com/nessenergy/Alupdatalake/issues/25)), Oracle
FMB ([#27](https://github.com/nessenergy/Alupdatalake/issues/27)), Portal Alup
([#29](https://github.com/nessenergy/Alupdatalake/issues/29)), MySQL RDS
([#31](https://github.com/nessenergy/Alupdatalake/issues/31)) e RM/TOTVS
([#32](https://github.com/nessenergy/Alupdatalake/issues/32)). O Hubspot saiu
desta linha e virou A9, porque é só um token.

**Por que é o maior risco financeiro do contrato, e não o A3.** O A3 posterga
prazo; o A7 gera cobrança por dia parado. É a única parte da cláusula 3ª com
dinheiro corrente.

Duas respostas de 11/09 o deixaram mais barato do que parecia: o banco de
produção da Comercialização é liberado assim que solicitado (C2), e o MySQL RDS
não precisa de VPN nem de peering (C8). O que sobrou é pedido administrativo —
e é justamente por ser barato de atender que o atraso nele fica caro de
justificar.

**Registro de esclarecimento**: dúvida da contratante também tem data. A
consulta sobre E1 e E2 chegou em 09/09 e foi respondida em 09/09; sem esse
registro, a espera por A3 poderia ser lida depois como decisão pendente de
alguém, quando parte dela era atribuição a esclarecer — e a resposta da ness.
não consumiu dia útil.

---

## 7. Higiene do backlog

O backlog do GitHub foi semeado duas vezes em 2026-08-24, gerando 15 issues
duplicadas (mesma tarefa, dois números). Elas foram fechadas em 2026-08-27,
mantendo sempre o número mais baixo de cada par. As issues das quatro fontes
públicas concluídas e das tarefas de fundação já entregues também foram
fechadas, com a ressalva de que **entrega técnica não é homologação** — esta
depende do primeiro `apply` real (§5.1).


Na conferência de **18/09**, antes da reconciliação, o Project 2 tinha 69 itens:
30 `Done`, 1 `In Progress` e 38 `Todo`. Essa contagem não mede homologação nem
horas. Os sete lançamentos de horas (100h) têm origem a conferir. O workflow de
[17/09, nº 35240311826](https://github.com/nessenergy/Alupdatalake/actions/runs/35240311826)
terminou verde com passos pulados pela guarda de configuração; a sincronização
automática ainda não tem execução efetiva comprovada. O resultado da
reconciliação está no [relatório de 18/09](relatorios/2026-09-18-reconciliacao-acompanhamento.md).
