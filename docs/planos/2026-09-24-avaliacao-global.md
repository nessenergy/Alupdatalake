# Avaliação global do projeto e próximos passos

**Data:** 24/09/2026, fim do dia · **Referência:** `main` em `96fd35e` e o
ambiente `dev` consultado diretamente (BigQuery, Cloud Run, Cloud Scheduler,
Cloud Monitoring, Dataform e IAM).

**Como foi feita:** quatro leituras independentes do repositório (conectores
e dados; infraestrutura, segurança e operação; contrato, ondas e medição;
documentação, governança e produto), guiadas pelas skills do projeto
(`conector-alupdata`, `ssdlc-alupdata`, `gcp-alupdata` e `homologacao-onda`).
A elas se somou a consulta ao ambiente real. Cada achado abaixo tem evidência
no repositório ou no GCP. Onde algo é hipótese, o texto diz.

**Escopo do texto:** fatos, lacunas e um plano. Prazos da Alup aparecem como
registro de data. Efeito contratual e cobrança ficam com a coordenação.

---

## 1. Em uma tela

- **A infraestrutura existe, e os dados ainda não.** O `dev` tem 159
  recursos, o Dataform roda inteiro (141 ações, zero falhas às 11h de 24/09)
  e o Portal está no ar. Mas **só 3 das 28 tabelas Bronze têm linha, com 16
  linhas no total**. A Onda 0 fecha com três dias de carga. A Onda 1 depende
  de rodar os 23 jobs públicos.
- **Se algo quebrar hoje, ninguém é avisado.** Há 8 políticas de alerta em
  `dev` e **nenhum canal de notificação**: `emails_alerta` e
  `billing_account` estão vazios nos três `.tfvars`. Em 24/09 quatro jobs
  falharam e o Hubspot errou 36 vezes, sem nenhum aviso.
- **O código está sólido e dois pontos de falha apareceram na primeira
  carga.** As 27 entidades têm os 7 componentes, e toda Silver tem asserção.
  O primeiro contato com o GCP revelou duas coisas: uma falha ao gravar o log
  de execução derruba o job sem deixar rastro, e uma mudança de formato na
  origem zera a carga sem alarme.
- **Nenhuma onda está homologada, e a medição tem lacunas.** No Project,
  **nenhum** dos 71 itens tem `Validado = Sim`. Das 580h, **480h não têm
  apontamento**, e as 100h lançadas têm origem a conferir.
- **O que falta da Alup está concentrado.** São credenciais das Ondas 2 e 3
  (A7 vence em 25/09), exemplos de planilha, orçamento, grupos do IAP e o
  billing export. Nada disso impede fechar as Ondas 0 e 1.

## 2. Placar por onda

| Onda | Prazo contratual | Pronto em código | Em dado real | O que separa do dossiê |
|---|---|---|---|---|
| 0 — Fundação | 11/09 (postergado por A3) | tudo | `bcb_juros` desde 24/09 | 3 dias de `SUCESSO`, replay no GCS real, Portal com uma Gold (dossiê previsto para 30/09) |
| 1 — Mercado base | 16/10 | 23 entidades públicas | nenhuma | carga dos 23 jobs, Gold com linha, janela em `hml` (dossiê previsto para 07/10) |
| 2 — APIs credenciadas | 13/11 | 4 conectores | TempoOK ENA em dia | Hubspot e BBCE; acervo do TempoOK; destino das 32h do item 2.1 |
| 3 — Sistemas internos | 18/12 | caminho de banco e orquestração | — | VPN e credenciais das quatro fontes (A7) |
| 4 — Planilhas e handoff | 08/01/2027 | motor S2, catálogo, plano do glossário | — | exemplos de planilha, glossário, runbook de incidente, handoff |

**Das 13 fontes contratuais, 8 já têm pelo menos uma entidade escrita**:
BCB, IBGE, ANEEL, ONS, CCEE dados abertos, BBCE, Hubspot e TempoOK — BBCE e
Hubspot ainda sem credencial. **As 5 restantes não têm nenhuma, todas por
falta de insumo**: CCEE credenciada, Oracle FMB, Portal Alup, MySQL RDS e
RM/TOTVS. As planilhas da Onda 4 correm à parte: o motor está pronto e falta
o template. Juntas, as Ondas 2 e 3 somam 265h, ou 45,7% do contrato.

---

## 3. Achados

Severidade: **Alta** trava onda ou esconde falha; **Média** custa retrabalho
ou medição; **Baixa** é higiene.

### 3.1 Operação e observabilidade

| # | Sev. | Achado | Evidência |
|---|---|---|---|
| O1 | Alta | Alertas sem destinatário. As 8 políticas existem e têm zero canais. O destinatário da Alup foi informado em 11/09 (E3), mas não entrou nos `.tfvars` | Cloud Monitoring de `dev`; `infra/environments/*.tfvars` |
| O2 | Alta | Ninguém consegue disparar um job à mão. `run.jobs.run` só está com a SA de deploy. As Tarefas 1.2, 3.1 e 3.3 do plano de fechamento supõem uma pessoa rodando `gcloud run jobs execute` | 403 ao tentar em 24/09 |
| O3 | Alta | Fontes sem credencial geram erro contínuo. O Hubspot falha a cada 6h (36 erros em 24/09), e o BBCE vai falhar em todo dia útil. Quando o alerta ligar, vira ruído, e o aviso real se perde | Cloud Logging de 24/09 |
| O4 | Média | As 18 entidades semanais e mensais não têm alerta de silêncio, por causa do teto de janela do Cloud Monitoring ([#188](https://github.com/nessenergy/Alupdatalake/issues/188), sem decisão) | `infra/modules/monitoramento/main.tf`, output `fontes_sem_alerta_de_silencio` |
| O5 | Média | A sincronização automática do quadro falha desde 24/09: o secret `alupdata-github-quadro-app-key` não tem versão. O runbook ainda descreve o comportamento antigo, que terminava em aviso | run `36022283872`; `docs/runbook/acompanhamento-semanal.md` |
| O6 | Média | Nenhum orçamento ativo. Falta o valor por ambiente ([#87](https://github.com/nessenergy/Alupdatalake/issues/87)), e o teto da E2 é US$ 20/mês até novembro | `infra/modules/monitoramento/custo.tf` |

### 3.2 Conectores e dados

| # | Sev. | Achado | Evidência |
|---|---|---|---|
| D1 | Alta | Uma falha ao gravar `bronze._execucoes` derruba o job com `exit 1`, e **não fica nenhuma linha de `ERRO`**. Foi o que escondeu os 4 jobs de 24/09 | `src/core/conector.py:119`; `src/core/bigquery.py:96-115` |
| D2 | Alta | Uma mudança de formato na origem zera a carga sem alarme. Em 24/09 o BCB parou de enviar `tipoBoletim` ([#215](https://github.com/nessenergy/Alupdatalake/pull/215) corrigiu), e 100% das linhas viraram inválidas. Nenhuma regra dispara quando uma execução com linhas extraídas termina com `linhas_carregadas = 0` | `src/core/conector.py:152-166` |
| D3 | Média | 22 das 27 entidades não têm teste contra a API real que possa ser repetido. A evidência de que "fala com a origem" vem de dry-run manual, e mudanças como a do BCB só aparecem na carga de produção | `tests/integration/` |
| D4 | Média | Não há um de-para publicado entre as 13 fontes contratuais e as 27 entidades. A medição é por onda e fonte, e o relatório pode confundir as duas contagens | `docs/plano-execucao.md` §3.1; `docs/dicionario-dados/README.md` |
| D5 | Baixa | O checklist da skill pede teste de idempotência por entidade, e nenhuma tem. Na prática, a garantia vem da asserção `uniqueKey` da Silver: o controle existe, só é outro | `.claude/skills/conector-alupdata` |
| D6 | Baixa | O índice do dicionário ainda fala em 26 entidades e na data de 18/09 | `docs/dicionario-dados/README.md` |

**Pontos confirmados como bons:** as 27 entidades têm os 7 componentes; toda
Bronze é particionada; toda Silver tem asserção; a Gold depende das
asserções, com teste de grafo no CI; o HTTP tem retry; o raw permite replay.

### 3.3 Infraestrutura e segurança

| # | Sev. | Achado | Evidência |
|---|---|---|---|
| S1 | Média | A rotação do token do TempoOK está vencida pelo critério da própria ADR 020, que a queria logo depois de A3 (atendida em 23/09) | ADR 020; `acoes-humanas.md` §2 |
| S2 | Média | O RIPD tem pendências da ness.: R02 (procedimento de eliminação), R08 (revogação de acesso no handoff) e **R09 (envio semanal do SAST/SCA à Alup, ainda não implementado)**. R01 e R06 dependem da Alup ou da Onda 3 | `docs/lgpd/ripd.md` |
| S3 | Média | O `deploy.yml` roda só por `workflow_dispatch` e não repete os testes. As ações novas de autenticação (v3), atualizadas em 24/09, ainda não rodaram num deploy real | `.github/workflows/deploy.yml` |
| S4 | Baixa | O log de auditoria de acesso a dados retém 30 dias; o RIPD propõe 1 ano. Depende de a política de retenção ser aprovada | `docs/runbook/deploy.md`; R07 |
| S5 | Baixa | `prod` não tem bootstrap. É o previsto (virada depois das Ondas 0 e 1), mas depende do orçamento (#87) | `infra/bootstrap/terraform.tfstate.d/` |
| S6 | Baixa, **corrigido nesta avaliação** | Os arquivos de plano do Terraform sem extensão (`tfplan`, `tfplan-dev`) e o PDF do brand book da Alup não estavam no `.gitignore` | `.gitignore` |

**Pontos confirmados como bons:** todas as ações do CI estão pinadas por SHA,
com `permissions` mínimas; o WIF é sem chave; o IAM é por recurso e o acesso
de pessoas é por grupo; o Portal falha fechado sem IAP; o bucket raw tem
versionamento e bloqueio público; o state do bootstrap está protegido pelo
`.gitignore`.

### 3.4 Contrato e medição (registro de fato)

| # | Sev. | Achado | Evidência |
|---|---|---|---|
| C1 | Alta | Zero itens com `Validado = Sim` no Project. O campo que separa entrega de aceite nunca foi usado | `gh project item-list 2`, 71 itens, 33 `Done` |
| C2 | Alta | 480h das 580h não têm apontamento em `Horas`. As 100h lançadas (7 itens, em 08/09) seguem a regra antiga de atribuir o orçamento à entrega, e a origem está marcada "a conferir" | Project; `status.md` §4 |
| C3 | Alta | O item 2.1 (CCEE credenciado, 32h) está `Todo` e sem destino. A decisão só está prevista para 07/10, e o dossiê da Onda 2 sai em 23/10 | Project; plano de fechamento D2 |
| C4 | Média | 27 entidades para 13 fontes contratuais. A conciliação com a planilha da proposta depende dos exemplos (A12/G3) | `status.md` §3 |
| C5 | Registro | A7 vence em 25/09 sem número de chamado registrado. A9 (Hubspot) venceu em 11/09 | `status.md` §6 |

### 3.5 Documentação, governança e produto

| # | Sev. | Achado | Evidência |
|---|---|---|---|
| G1 | Alta | O `README.md` parou em 18/09 e diz que "não há carga real em GCP", quando o `dev` está no ar desde 23/09. É a porta de entrada do repositório para a Alup e para o time do handoff | `README.md:138-142` |
| G2 | Média | O `plano-semanal.md` parou na S4, sem fechamento, e não registra a virada de 23 e 24/09. Os três documentos de acompanhamento estão desalinhados | `docs/plano-semanal.md` |
| G3 | Média | Não há runbook de incidente, só de diagnóstico: falta dizer quem é avisado, com que severidade e o que reprocessar primeiro. O próprio `observabilidade.md` registra a falta | `docs/runbook/observabilidade.md:82-88` |
| G4 | Média | A RACI por domínio (lacuna 2) está aberta e sem data | `docs/interlocutores.md:95` |
| G5 | Média | O domínio Planejamento não tem fonte nem Gold. Depende de RM/TOTVS e das planilhas | `docs/arquitetura/dominios-analiticos.md:219-233` |
| G6 | Baixa | O cabeçalho "Estado atual" do `AGENTS.md` diz 18/09, e o texto abaixo dele já é de 23/09. A issue #95 e o item #1 do Project não refletem 23 e 24/09 | `AGENTS.md:195`; Project |

---

## 4. Plano sugerido

Ordem por efeito: primeiro o que esconde falha ou trava onda, depois medição,
depois handoff. As horas são estimativa de trabalho da ness.

### Horizonte 1 — esta semana, até 26/09

| # | Ação | Resolve | Dono | Esforço |
|---|---|---|---|---|
| 1 | **Ligar os alertas em `dev` para o grupo da ness.** (`emails_alerta = ["operacao-datalake@ness.com.br"]`). O e-mail da Alup entra em `hml` e `prod`, depois de o ruído sair | O1 | ness. | 0,5h |
| 2 | **Tirar o agendamento das fontes sem credencial em `dev`**: Hubspot, BBCE e, enquanto não houver acervo, o boletim do TempoOK. Uma variável de exclusão no módulo `scheduler`, com teste. O job continua existindo e roda à mão quando a credencial chegar | O3 | ness. | 2h |
| 3 | **Criar um workflow `Executar ingestão`** (`workflow_dispatch`, com conector e janela como entrada), que roda o job com a SA de deploy por WIF. Fica auditável no GitHub e não amplia o IAM de pessoas. Destrava as Tarefas 1.2, 3.1 e 3.3 do plano de fechamento | O2 | ness. | 3h |
| 4 | **Tornar visível a falha de `registrar_execucao`**: um retry curto e, se ainda falhar, log `ERROR` estruturado com o `ingestao_id` e as contagens antes de sair. Com teste que simula o 404 de 24/09 | D1 | ness. | 3h |
| 5 | **Alerta de "extraiu, mas não carregou nada"**: uma métrica de log para `linhas_extraidas > 0` e `linhas_carregadas = 0`, com o mesmo canal do item 1. Pega a próxima mudança de formato como a do BCB | D2 | ness. | 2h |
| 6 | **Registrar A7 em 26/09**, com chamado e responsável se houver. É só o fato e a data | C5 | ness. | 0,5h |
| 7 | **Gravar a chave do GitHub App do quadro no Secret Manager** e corrigir o runbook. A alternativa é desligar o agendamento até a chave existir | O5 | Ricardo | 0,5h |

### Horizonte 2 — até 09/10: fechar as Ondas 0 e 1

| # | Ação | Resolve | Dono | Esforço |
|---|---|---|---|---|
| 8 | Seguir as Fases 0 a 3 do [plano de fechamento](2026-09-24-fechamento-das-ondas.md), com o workflow do item 3 no lugar do `gcloud` manual: 3 dias de carga, replay, Portal com dado real e deploy do #216, dossiê da Onda 0 em 30/09, carga dos 23 jobs públicos, janela em `hml` e dossiê da Onda 1 em 07/10 | ondas 0 e 1 | ness. | já estimado no plano |
| 9 | **Publicar o de-para entre as 13 fontes e as 27 entidades**, uma tabela em `docs/dicionario-dados/README.md` e no dossiê. A medição passa a falar a língua do contrato | D4, C4 | ness. | 1h |
| 10 | **Definir a fonte das horas**: quem aponta, onde e com que periodicidade. Conferir a origem das 100h antes do dossiê da Onda 0 | C2 | coordenação | decisão |
| 11 | **Usar `Validado = Sim`** no aceite de cada dossiê, item a item | C1 | coordenação | contínuo |
| 12 | **Antecipar a decisão das 32h do item 2.1 para 30/09**, junto do dossiê da Onda 0, em vez de 07/10 | C3 | coordenação com a Alup | decisão |
| 13 | **Pôr a documentação em dia em uma passada**: `README.md`, fechamento da S4 no `plano-semanal.md`, cabeçalho do `AGENTS.md`, índice do dicionário, issue #95 e item #1 do Project | G1, G2, G6, D6 | ness. | 2h |
| 14 | **Rotacionar o token do TempoOK** com o fornecedor, gravando direto no Secret Manager | S1 | ness. com o fornecedor | 1h |

### Horizonte 3 — até o dossiê da Onda 2 (23/10)

| # | Ação | Resolve | Esforço |
|---|---|---|---|
| 15 | **Decidir e implementar o #188**, com a opção (a) recomendada: um vigia diário que lê `gold.saude_ingestao` e avisa quando uma fonte semanal ou mensal passa do prazo | O4 | 4h |
| 16 | **Canário semanal contra a origem real** para as fontes públicas: dry-run de um dia por entidade, em job agendado, com alerta se o schema recusar. Troca a descoberta em produção por uma em teste | D3 | 6h |
| 17 | **Hubspot e BBCE**: quando a credencial chegar, religar o agendamento (item 2), rodar a integração e ajustar | Onda 2 | 4h + 6h |
| 18 | **Implementar o R09 do RIPD**: um resumo semanal de SAST e SCA gerado pelo CI, pronto para envio à Alup | S2 | 3h |
| 19 | **Glossário como código**, pelo [plano pronto](2026-09-24-glossario-como-codigo.md) | Onda 4 | 4h |

### Horizonte 4 — Ondas 3 e 4, e handoff

| # | Ação | Resolve |
|---|---|---|
| 20 | Uma fonte interna por plano, na ordem em que o acesso chegar. O MySQL RDS dispensa VPN e vem primeiro | Onda 3 |
| 21 | Runbook de incidente: severidade, quem é avisado, o que reprocessar primeiro. Parte do que o `observabilidade.md` já descreve | G3 |
| 22 | R02 (eliminação) e R08 (revogação de acesso no handoff) escritos como procedimento | S2 |
| 23 | Um passo de teste no `deploy.yml` antes do `apply`, ou a exigência de CI verde no commit do deploy | S3 |
| 24 | Retenção de 1 ano do log de auditoria, quando a política for aprovada | S4 |
| 25 | Virada de `prod` depois do aceite das Ondas 0 e 1, com o orçamento definido | S5 |

**Esforço dos Horizontes 1 e 3 (itens da ness.):** cerca de 11h e 27h. Nenhum
depende da Alup.

---

## 5. Decisões

**Todas as recomendações foram aceitas pelo Ricardo em 24/09**, inclusive a
opção (a) do #188 (item 15).

| # | Decisão | Recomendação aceita | Onde está |
|---|---|---|---|
| 1 | Para onde vão os alertas agora | o grupo `operacao-datalake@ness.com.br` em `dev`; o endereço da Alup só em `hml` e `prod`, depois do item 2 | [#220](https://github.com/nessenergy/Alupdatalake/pull/220) |
| 2 | Como disparar um job à mão | o workflow `Executar ingestão`, com a SA de deploy, sem ampliar o IAM de pessoas | [#221](https://github.com/nessenergy/Alupdatalake/pull/221); o plano de fechamento já usa o workflow |
| 3 | Pausar o agendamento das fontes sem credencial | sim, até a credencial chegar: Hubspot, BBCE e o boletim do TempoOK em `dev` | [#220](https://github.com/nessenergy/Alupdatalake/pull/220) |
| 4 | Antecipar a decisão das 32h do item 2.1 | pedir a posição da Alup em 30/09, junto do dossiê da Onda 0 | D2 do plano de fechamento; coordenação com a Alup |
| 5 | Fonte e regra das horas | definir quem aponta, onde e com que periodicidade, e conferir as 100h, antes do dossiê da Onda 0 (30/09) | coordenação |
| 6 | Extrair o conteúdo da previsão de ENA do TempoOK (domínio Meteorologia) | conferir primeiro se está no escopo da proposta; fora dele, é aditivo | coordenação, antes de qualquer código |

Os itens 4 e 5 do Horizonte 1 (falha de registro visível e alerta de carga
zerada) estão em [#222](https://github.com/nessenergy/Alupdatalake/pull/222).

## 6. O que já foi feito junto com esta avaliação

- `.gitignore`: passam a ser ignorados os arquivos de plano do Terraform sem
  extensão e os PDFs fora de `docs/`, como o brand book da Alup, que não pode
  ser versionado.
