# Estado do projeto

Atualizado em **2026-09-14** · **A3 completa hoje o 5º dia útil de atraso** —
vencido em 04/09, previsão da Alup para 18/09, contagem da cláusula 3ª em
curso. Em 14/09 a Alup entregou a documentação das APIs: **A2 encerrada e A8
atendida**, e as 32h da CCEE voltaram a andar sem depender da contratante
(ADR 018)

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
| Runner de ingestão (janela, raw no GCS, validação, colunas técnicas, carga, log) | `src/core/` | 257 testes aprovados, 92% de cobertura (suíte inteira) |
| Caminho de banco relacional (Oracle/MySQL/**SQL Server**) para a Onda 3 | `src/core/banco.py` | ADR 008 e adendo de 04/09; 20 testes sem rede; **nenhuma conexão real** — depende de VPN (A7). Compose e testes de integração prontos em `tests/integration/` |
| Replay do raw sem nova chamada à fonte | `alupdata reprocessar-raw`, `src/core/storage.py` | testes locais com JSONL gzip; falta validar contra GCS real |
| CLI única (`alupdata listar` / `ingerir`) | `src/cli.py` | executada contra as 4 fontes |
| Scaffolding dos 7 componentes | `make novo-conector` | usado nas fontes novas |
| Deploy de views idempotente | `make deploy-views` | `--dry-run` conferido |
| Motor S2 Data Intake (planilha CSV/XLSX sob template) | `src/core/planilha.py`, `src/conectores/planilha.py` | 19 testes; templates concretos dependem de A4 |
| Painel de saúde do lake (frescor, confiabilidade, volumetria) | `sql/gold/saude_ingestao.sql`, rota `/lake` | ADR 006; ferramenta de sustentação, não escopo faturado |
| Portal falha fechado sem identidade do IAP | `src/portal/app.py` | 7 testes; deploy sem autenticação ou IAP mal configurado devolve 403 em vez de servir dado |
| Log estruturado com correlação por execução | `src/core/observabilidade.py` | 8 testes; verificado contra a API do BCB |
| Alertas (falha, silêncio, inválidos em alta) | `infra/modules/monitoramento` | `terraform validate` limpo; **sem destinatário** — ver runbook |
| Painel no Cloud Monitoring e orçamento com alerta de custo | `infra/modules/monitoramento` | orçamento precisa do `billing_account` da Alup (A3) |
| Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM | `infra/` | IAM restringido por recurso; Terraform 1.15.8 `fmt` e `validate` limpos |
| CI/CD: lint, testes, Bandit, pip-audit, Gitleaks, Terraform | `.github/workflows/` | workflow de deploy ordenado; 7 jobs verdes no Actions |
| Imagem da CLI | `Dockerfile` | build local não executado: Docker Desktop sem daemon ativo |
| Campos de acompanhamento semanal do GitHub Projects | `scripts/campos_projeto.py`, `runbook/acompanhamento-semanal.md` | 12 testes; script idempotente. **Os cinco campos criados no quadro em 04/09** — Horas, Semana, Validado, Correções e Atraso |
| **FinOps F0** — rótulo de custo por fonte no job do BigQuery | `src/core/bigquery.py` (`rotulos()`) | 6 testes; precisa existir **antes** do 1º apply, custo gasto não se rateia depois |
| **8 domínios analíticos** e dimensões comuns fechadas (plano 0.10 e 0.11) | `docs/arquitetura/dominios-analiticos.md`, `visao-geral.md` | Itens de Onda 0 que estavam desbloqueados desde 11/09. Duas lacunas nomeadas: de-para de usina (Alup) e mês CCEE (ness.) |
| Domínios corrigidos para os do **B1**, e a abrangência do dado escrita | `docs/arquitetura/dominios-analiticos.md`, `src/portal/custo.py` | A primeira versão derivava os domínios de A1. São os do B1 — 8 domínios em 11 linhas, três com responsáveis distintos por subtema. As 6 coligadas respondem pelo faturamento e não delimitam o dado |

### Conectores (7 componentes cada, exceto onde indicado)

| Fonte | Formato | Volume verificado | Agendamento |
|---|---|---|---|
| **BCB/PTAX** | JSON diário | 3 registros / 3 dias | diário 9h, janela 3 dias |
| **IBGE/IPCA** | JSON aninhado, mensal | 12 registros / 6 meses | dia 12, janela 90 dias |
| **ANEEL/SIGA** | cadastro paginado | **25.263 registros**, 0 inválidos, 28s | semanal, segunda 7h |
| **ONS/carga** | CSV anual remoto | 28 registros / 7 dias | diário 8h, janela 30 dias |
| **CCEE/PLD** | CSV anual remoto (ISO-8859-1), descoberto via CKAN | **288 registros / 3 dias**, 0 inválidos, contra a API real | mensal, dia 5 às 9h, janela 120 dias |
| **CCEE/perfil** | cadastro CSV (ISO-8859-1), via CKAN | **60.509 registros**, 0 inválidos, contra a API real | semanal, terça 7h |
| **Hubspot/negócios** | JSON paginado, CRM | **não executado** — sem token (A9) | a cada 6h, janela 2 dias |
| **BBCE/curva forward** | JSON por pregão, sessão JWT | **não executado** — sem acesso (A7) | dia útil 20h, janela 7 dias |
| **TempoOK/boletins** | PDF por download, catálogo no Bronze | **contrato verificado contra a API real**; 0 boletins ingeríveis — o acervo alcançável para em 26/10/2022 (ADR 019, adendo) | diário 11h, janela 5 dias |

**Seis das nove falaram com a API real** em dry-run. Hubspot e BBCE são as
exceções: os 7 componentes existem, escritos contra a documentação, e o teste
de integração está `skipif` até a credencial chegar (A9 e A7). No BBCE falta
inclusive o **host**, que não consta da documentação pública e vem junto com o
acesso.

O TempoOK é um caso à parte: **falou com a API e o contrato de dados está
verificado** — caminho, ausência por 404, TLS, estabilidade do `sha256` —, mas
o acervo alcançável termina em 26/10/2022, então não há boletim para ingerir
(A10).

Nenhuma linha chegou a um BigQuery de verdade — o projeto GCP ainda não existe.

### Dimensões comuns

| Dimensão | Fonte | Situação |
|---|---|---|
| `data_referencia` | todas | ok |
| `periodo_apuracao` | todas | ok |
| `codigo_usina` | ANEEL/SIGA (CodCEG) | ok |
| `submercado` | ONS (N, NE, S, SE) | ok |
| `agente_ccee` | CCEE (`lista_perfil_v1`) | **ok desde 14/09** — `ccee_perfil` entregue, 60.509 perfis verificados contra a API real. **As cinco dimensões comuns têm fonte** |

### Documentação

ADRs 001–020 · 11 dicionários de dados com [índice e linhagem](dicionario-dados/README.md) · plano de execução · runbook de deploy,
de primeiro deploy e de acompanhamento semanal ·
[`proximos-passos.md`](proximos-passos.md) como fila de execução ·
`AGENTS.md` como contexto canônico · skills do projeto e shortlist do Google.

Material de reunião: baralho de kickoff e **baralho de revisão arquitetural em
GCP** (`apresentacoes/revisao-arquitetural-gcp.html`) — origem, tratamento e
destino, com os oito invariantes e a pauta de perguntas. **Enviado ao Google em
04/09**; a resposta é a pendência G1 do painel §6.

---

## 2. Aberto — ação da ness.

| # | Item | Bloqueado por |
|---|---|---|
| N1 | Preparar contrato de dados das fontes das Ondas 2 e 3 | **destravado em 14/09** — com a documentação recebida, o TempoOK foi entregue e o **BBCE é o próximo a escrever**, antes do token. Restam as fontes da Onda 3, que dependem de A7 |
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
| A3 | **Projeto GCP `dev`**: criar, habilitar APIs, IAM, Artifact Registry, bucket de state — criação e `billing_account` são da Alup, esclarecido em 09/09 | nada sobe; Onda 0 não homologa | plano 2.2 (0.13), [registro de 09/09](relatorios/2026-09-09-esclarecimento-e1-e2.md) |
| ~~A4~~ | ~~**Questionário de Gaps** (47 perguntas)~~ | **Respondido em 11/09.** Definir os 8 domínios a partir das respostas é tarefa da ness. (plano 0.10), não insumo pendente | [`questionario-gaps.md`](questionario-gaps.md) |
| ~~A5~~ | ~~**RACI e data owners** por domínio~~ | **Respondido em 11/09** (item B1 do questionário) | [`interlocutores.md`](interlocutores.md) |
| ~~A6~~ | ~~**Ferramenta de BI** definida~~ | **Respondido em 11/09**: Power BI hoje; Looker Studio ou fronts internos na Fase 2 (item G1) | [`questionario-gaps.md`](questionario-gaps.md) |
| A7 | Abrir **já** os pedidos de token (Onda 2) e VPN/credencial (Onda 3) | é o maior risco do contrato: atraso dispara ociosidade de 4h/dia | plano §7 |
| ~~A8~~ | ~~**Documentação técnica de BBCE e TempoOK**~~ | **Atendida em 14/09** — BBCE documentado em Postman; TempoOK sem documentação publicada, mas com exemplo suficiente. Resta só a credencial do BBCE, que é A7 | [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) |
| A9 | **Token do Hubspot** (private app) no secret `alupdata-hubspot-api-token` | o conector está pronto e parado; nenhuma linha de CRM entra no lake | plano 2.3 (2.3) |
| A10 | **Verificar com o TempoOK o acesso ao acervo recente** — o token entregue em 14/09 alcança boletins só até 26/10/2022 | o conector está pronto e verificado, mas ingere zero boletins; a fonte não fecha na Onda 2. **Resolver isto antecipa a rotação do token** (gatilho 1 da [ADR 020](arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md)): com acervo corrente, o alcance da credencial muda de patamar | [ADR 019](arquitetura/decisoes/019-boletim-do-tempook-como-arquivo.md), [registro de 14/09](relatorios/2026-09-14-documentacao-de-apis-recebida.md) §4.1 |

> **Cláusula 3ª**: atraso > 5 dias úteis posterga o cronograma; > 5 dias úteis em
> VPN/credencial gera taxa de ociosidade de 4h/dia (R$ 256/h); > 20 dias
> corridos suspende os serviços. Registrar a data de cada pedido **no dia em que
> o atraso começa**, não quando vira problema.

---

## 4. Onde estamos no contrato

| Onda | Escopo | Situação |
|---|---|---|
| 0 — Fundação | 90h · marco 15,52% | Técnico concluído; **falta o que depende da Alup** (A3–A6) para homologar |
| 1 — Mercado base | 120h · marco 20,69% | **5 de 5 fontes com entrega**: as 4 públicas verificadas contra as APIs reais e a CCEE destravada em 14/09, com `ccee_pld` entregue pela via de dados abertos (ADR 018). As demais entidades da CCEE entram por demanda dos domínios analíticos (A4) |
| 2 — APIs credenciadas | 110h · marco 18,97% | **Hubspot, TempoOK e BBCE com os 7 componentes**, os três escritos antes da credencial; falta rodar contra a API real (A9, A7). **A onda deixou de estar bloqueada por documentação** e depende só de credencial. Resta a CCEE credenciada, que é escopo candidato e não foi pedida em A7 ([ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)) |
| 3 — Sistemas internos | 155h · marco 26,72% | Caminho de banco pronto (ADR 008: Oracle, MySQL e SQL Server); **nenhuma fonte iniciada** — bloqueada por VPN e credencial (A7) |
| 4 — Planilhas e handoff | 105h · marco 18,10% | **Motor S2 Data Intake pronto** (item 4.1), adiantado por não depender de insumo; templates concretos dependem de A4. Governança e handoff não iniciados |

> **Leitura da tabela.** Quatro das cinco ondas já têm entrega, no quinto dia
> da primeira. O que nenhuma linha acima mede é homologação: onda fecha por
> aceitação e carga real, não por volume de código. O projeto está
> simultaneamente adiantado em entrega e parado em homologação — e o segundo
> é o que define o marco.

---

## 5. Preparar as fontes bloqueadas: o que a sondagem mostrou

O plano previa escrever schema e fixture das fontes das Ondas 2 e 3 a partir da
documentação pública, para que a chegada do token fosse "ligar e ajustar". A
sondagem de 2026-08-25 mostra que isso **só se sustenta para uma delas**:

| Fonte | Documentação/API alcançável? | Dá para escrever o contrato hoje? |
|---|---|---|
| CCEE InfoMercado | **sim, desde 14/09** — o 403 era filtro de cliente não identificado; o CKAN de dados abertos expõe 204 conjuntos, sem credencial | **sim, e sem depender de token** — ADR 018 |
| BBCE | **sim, desde 14/09** — coleção Postman completa | sim; falta só a credencial (A7) |
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
| A3 | Projetos GCP (`dev` primeiro, depois `hml` e `prod`) criados, vinculados ao faturamento e com os papéis de bootstrap concedidos à ness. — APIs, IAM, WIF, Artifact Registry e state passaram à ness. em 11/09 (ADR 015) | Alup | **04/09 — vencido** | **Não entregue. Atraso registrado em 04/09**; 1º dia útil de atraso em 08/09, 5º em 14/09. A Alup condicionou A3 à resposta do Google (G1). Em 09/09 a Alup levantou dúvida sobre quem cria o projeto (E1) e de quem é a `billing_account` (E2); **ambas são da Alup, esclarecido no mesmo dia** — ver [registro de 09/09](relatorios/2026-09-09-esclarecimento-e1-e2.md). S2 e S3 escorregam inteiras; Onda 0 não homologa; > 5 dias úteis posterga o cronograma |
| A9 | Token Hubspot no secret `alupdata-hubspot-api-token` | Alup | 11/09 | conector pronto segue parado; item 2.3 não fecha |
| ~~A4~~ | ~~Questionário de Gaps respondido~~ | Alup | 11/09 | **Respondido no prazo** |
| ~~A5~~ | ~~Matriz RACI e data owners~~ | Alup | 11/09 | **Respondido no prazo** |
| ~~A6~~ | ~~Ferramenta de BI definida~~ | Alup | 11/09 | **Respondido no prazo**: Power BI |
| [#87](https://github.com/nessenergy/Alupdatalake/issues/87) | Destinatários de alerta e `billing_account` | Alup | 11/09 | alertas e orçamento existem mas não notificam ninguém |
| — | Variáveis do GitHub (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`) | ness. | depende de A3 | deploy não autentica. **Branch protection resolvida em 11/09**: a organização passou ao GitHub Enterprise e a `main` exige PR e seis verificações, com force push e exclusão bloqueados (ADR 010, encerrada) |
| ~~A2~~ | ~~Decisão sobre a CCEE~~ | Alup | ~~18/09~~ | **Encerrada em 14/09, antes do prazo.** As 32h voltaram a andar; nenhuma das quatro alternativas foi necessária ([ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)) |
| G1 | **Resposta do Google à revisão arquitetural** (enviada em 04/09) | Google | **a definir** | **Precede A3 por decisão da Alup**, e portanto precede todo o cronograma técnico. Sem data pactuada, a postergação passa a depender de terceiro sem prazo acordado — ver `plano-semanal.md`, S1 |
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

**O que ele destrava**: sete conectores — quase toda a Onda 2 e a Onda 3
inteira. BBCE ([#23](https://github.com/nessenergy/Alupdatalake/issues/23)),
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
