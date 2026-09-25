# Plano semanal — próximas 4 semanas

Emitido em **2026-08-27** · S1 revisada em **2026-08-31** e em **2026-09-04** · S4 registrada em **2026-09-24** e fechada em **2026-09-25**, com a S5 ·
Escopo e estimativa por onda: [`plano-execucao.md`](plano-execucao.md) ·
Situação atual: [`status.md`](status.md)

---

## O quadro em uma frase

Em **25/09/2026**, as **23 entidades públicas estão carregadas em `dev` e em
`hml`**, com os sete componentes, e o **dossiê de homologação das Ondas 0 e 1
foi emitido e enviado** ([`relatorios/2026-09-25-dossie-ondas-0-e-1.md`](relatorios/2026-09-25-dossie-ondas-0-e-1.md)).
A reunião de aceite está proposta para 01/10. A Onda 2 está com o dossiê
preparado, à espera de credenciais, e a Onda 3 tem o caminho de rede pronto
do lado da GCP ([ADR 024](arquitetura/decisoes/024-rede-das-fontes-internas.md)),
à espera da rede local e das credenciais da Alupar.

S1 e S2 abaixo preservam o **registro histórico e o plano então vigente**,
inclusive decisões posteriormente substituídas. A região atual é `us-central1`
(ADR 023, que substituiu a 011 em 23/09), Dataform substitui o deploy SQL
(ADR 012), o bootstrap é da ness.
em três projetos da Alup (ADR 015) e Workflows orquestra a Onda 3 (ADR 017).
A organização passou ao GitHub Enterprise em 11/09. As tabelas históricas
não comprovam execução, horas realizadas ou aceite.

Por isso este plano tem duas trilhas por semana:

- **Entregamos** — o que a ness. produz mesmo sem resposta da Alup.
- **Destrava** — o insumo que precisa chegar naquela semana para a semana
  seguinte não virar hora ociosa.

Semanas contadas de segunda a sexta. S1 começa em **2026-08-31**.

---

## S1 · registro histórico · 31/08 – 04/09 · Ambiente e contrato de dados

> Revisado em **31/08**, primeiro dia da semana, e de novo em **04/09**, no
> último. Dois itens previstos aqui já tinham sido entregues antes de a semana
> começar (PRs #61 a #65): o runbook do primeiro deploy e o Questionário de
> Gaps. Ao longo da semana entraram três entregas não previstas — a revisão
> arquitetural para o Google e o instrumental de acompanhamento semanal — e
> apareceram dois bloqueios novos; ver "Descobertas".

### Já entregue, antes do prazo

| Item | Onde |
|---|---|
| Runbook do primeiro deploy | [`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md) |
| Questionário de Gaps: 47 perguntas, 7 blocos, prazos escalonados | [`questionario-gaps.md`](questionario-gaps.md) · PDF em `envio/` |
| Caminho de banco relacional da Onda 3 | `src/core/banco.py` (ADR 008) |
| Replay de raw, sanitização de credencial, IAM por recurso | PR #64 |
| **Questionário de Gaps enviado à Alup** — 47 perguntas, emitido em 31/08 | `envio/Questionario-de-Gaps-AlupData.pdf` · issue [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| **Revisão arquitetural para o Google: baralho confeccionado e enviado** | [`apresentacoes/revisao-arquitetural-gcp.html`](apresentacoes/revisao-arquitetural-gcp.html) · PR #74 |
| Campos de acompanhamento semanal versionados (Horas, Semana, Validado, Correções, Atraso) | `scripts/campos_projeto.py` · [runbook](runbook/acompanhamento-semanal.md) · PR #75 |
| Fila de execução com dono e comando por item | [`proximos-passos.md`](proximos-passos.md) · PR #75 |
| **Região do ambiente decidida**: `southamerica-east1` | [ADR 009](arquitetura/decisoes/009-regiao-do-ambiente.md) · `dev.tfvars`, `prod.tfvars` e `variables.tf` coerentes |

### O que esta semana precisa produzir

| Dia | Item | Entregável verificável |
|---|---|---|
| **Seg 31/08** | Cobrar A3 por escrito, pedindo **data com responsável nomeado** | registro na issue [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| Ter–Qua | Build da imagem da CLI e execução local do job | `docker run` da imagem executando `alupdata listar` |
| Ter–Qua | `banco.py` exercitado contra Oracle XE e MySQL em contêiner | uma consulta real por driver, com paginação verificada |
| Qui–Sex | Variáveis do GitHub preenchidas assim que A3 der os valores | `gh api .../actions/variables` devolvendo as quatro |
| Qui–Sex | Issues das lacunas de rastreamento criadas e ligadas ao Project | trabalho das PRs #62–#65 rastreável na medição |

### Destrava (ação de terceiro)

| Insumo | Responsável | Prazo | Issue |
|---|---|---|---|
| **A3** — projeto GCP `dev`, 10 APIs, IAM, WIF, Artifact Registry, bucket de state | Alup | **04/09** | [#55](https://github.com/nessenergy/Alupdatalake/issues/55), [#1](https://github.com/nessenergy/Alupdatalake/issues/1) |
| **A9** — token Hubspot no secret `alupdata-hubspot-api-token` | Alup | 11/09 | [#24](https://github.com/nessenergy/Alupdatalake/issues/24) |
| **A4** — Questionário de Gaps **respondido** (enviado em 31/08, está com eles) | Alup | 11/09 | [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| **G1** — **resposta do Google à revisão arquitetural** (enviada em 04/09) | Google | a definir — ver abaixo | — |

> Se A3 não chegar até **04/09**, começa a contagem da cláusula 3ª (atraso > 5
> dias úteis posterga o cronograma). Registrar a data do pedido no dia em que o
> atraso começa.

#### Registro de 04/09: A3 não chegou, e agora depende de G1

**A3 venceu hoje e não foi entregue.** A contagem da cláusula 3ª começa nesta
data. Enquanto o insumo não chegar, os prazos que dependem dele ficam
postergados: a ness. segue executando o que independe do ambiente, mas **não
responde por marcos cujo insumo não foi disponibilizado** — S2 (primeiro deploy
real) e S3 (fechar a Onda 0) escorregam pelo tempo que A3 demorar.

**A Alup informou que condicionou A3 à resposta do Google.** Isso muda a forma
da dependência: G1 e A3 não estão em corrida, estão **em série**.

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

Três consequências que precisam estar escritas:

1. **O gargalo mestre deixou de ser a Alup e passou a ser um terceiro sem
   prazo acordado.** A3 ao menos tinha data; G1 não tem. Enquanto G1 não tiver
   data, o cronograma inteiro não tem previsão — e isso não é uma estimativa
   pessimista, é a ausência de um prazo.
2. **Condicionar A3 a G1 não pausa a cláusula 3ª.** O contrato conta o atraso
   do insumo, não o motivo do atraso. A decisão de esperar o Google é legítima
   e pode ser boa tecnicamente, mas o efeito contratual do atraso continua
   correndo — e é por isso que fica registrado por escrito, hoje.
3. **O argumento do baralho ganhou força.** Ele dizia que a crítica chegaria
   antes do `apply`; agora é certo que sim, porque o `apply` espera por ela. A
   recomendação do Google entra como reprojeto, não como migração — inclusive
   sobre a região, que a ADR 009 fixou em `southamerica-east1` justamente por
   ser irreversível depois do primeiro `apply`.

**O que a ness. faz enquanto isso**: tudo que não depende do ambiente. A lista
viva está em [`proximos-passos.md`](proximos-passos.md); o que sobra sem GCP é
documentação, contrato de dados das fontes ainda não integradas, instrumental
de acompanhamento e preparação do primeiro deploy. Trabalho útil, mas nenhum
deles fecha onda — fechar onda exige carga real.

### Descobertas de 31/08

**A região está divergente e a decisão é irreversível.** `dev.tfvars` aponta
`us-east1`; a pergunta E7 do questionário assume `southamerica-east1`. Dataset
do BigQuery **não muda de região depois de criado** — corrigir mais tarde é
recriar tudo e recarregar. Precisa ser decidido antes do primeiro `apply`, e
tem efeito de residência de dado sob a LGPD, não só de latência.

**Branch protection é impossível no plano atual.** A organização está no
GitHub Free com repositório privado; tanto `branch protection` quanto
`rulesets` respondem 403 pedindo upgrade. Hoje a `main` aceita push direto sem
revisão obrigatória — o que contraria o SSDLC da cláusula 8ª. As saídas são
GitHub Team (pago por usuário) ou assumir formalmente o risco por escrito.
Enquanto isso, o CI roda em toda PR mas **não impede** um push direto.

**Docker está ativo** (29.6.1), ao contrário do que `status.md` registrava. O
build da imagem deixa de depender de ambiente e vira tarefa desta semana.

---

## S2 · plano histórico · 07/09 – 11/09 · Primeiro deploy real

Esta semana **só existe se A3 chegou**. Sem projeto GCP, o conteúdo abaixo
escorrega inteiro e a semana vira ociosidade.

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | `terraform apply` real: datasets Bronze/Silver/Gold, bucket raw, secrets, IAM, Cloud Run Job, Scheduler, monitoramento | `apply` limpo; recursos listados no console |
| Entregamos | Imagem da CLI publicada no Artifact Registry e job executado à mão contra o BCB | uma linha real em `bronze._execucoes` com `status = SUCESSO` |
| Entregamos | `make deploy-views` aplicado: as views Silver e Gold das 5 fontes existindo de verdade | `bq ls` mostrando as views; `SELECT` de sanidade em cada uma |
| Entregamos | Hubspot rodado contra a API real (se A9 chegou) e ajustado | teste de integração deixa de ser `skipif` |
| Entregamos | Destinatários dos alertas e `billing_account` do orçamento preenchidos | alerta de teste recebido por e-mail |
| Destrava | **A4** respondido (Questionário de Gaps) | sem ele, S3 não tem alvo |
| Destrava | **A5** (RACI e data owners) e **A6** (ferramenta de BI) | |
| Destrava | **G1** — resposta do Google à revisão arquitetural | idealmente **antes** do `apply` desta semana; depois dele, a crítica passa a custar migração |

---

## S3 · 14/09 – 18/09 · Fechar a Onda 0

### Plano original da S3 (não realizado integralmente; fechamento abaixo)

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | Os **8 domínios analíticos** definidos a partir das respostas de A4 (item 0.10) | documento com pergunta de negócio e fontes por domínio |
| Entregamos | Dimensões comuns Silver fechadas contra dado real, não contra fixture (item 0.11) | `arquitetura/visao-geral.md` atualizado, regra por dimensão |
| Entregamos | Portal MVP ligado no BigQuery e publicado no Cloud Run com IAP (item N2/0.15) | URL autenticada mostrando uma view Gold real — **nunca** com `--allow-unauthenticated` |
| Entregamos | BCB rodando sozinho por 3 dias consecutivos (item 0.14) | 3 execuções `SUCESSO` seguidas, sem intervenção |
| Entregamos | **Dossiê de homologação da Onda 0** | checklist da skill `homologacao-onda` com evidência por linha |
| Destrava | **A2** — decisão sobre a CCEE (liberar IP, credencial de agente, ou remanejar as 32h) | issue [#52](https://github.com/nessenergy/Alupdatalake/issues/52) |

**Marco**: Onda 0 homologada → 15,52% · R$ 23.040,00.

### Fechamento da S3 — 18/09/2026

- **Realizado:** domínios e dimensões documentados; RACI recebida em 15/09;
  CCEE via dados abertos, BBCE (PR #131), TempoOK e novas entidades ONS
  implementados; runner em fatias e de-para público de usinas entregues.
- **Verificado:** 23 das 26 entidades em dry-run com dados reais; TempoOK
  com contrato da API verificado e acervo alcançável até 26/10/2022. Não há
  evidência de carga em BigQuery, três dias de execução ou aceite da Alup.
- **Bloqueios:** A3/#55, billing/#87 e planilhas/#142 sem confirmação de
  entrega em 18/09. A3 conserva o prazo original de 04/09 e chega ao 9º dia
  útil de atraso (primeiro em 08/09, excluído o feriado de 07/09).
- **Próximas ações:** Alup confirma projetos, billing, papéis e exemplos;
  ness. executa bootstrap/deploy após A3 e reúne carga, replay e evidências
  em `hml`. Acessos BBCE/Hubspot e acervo TempoOK seguem #23/#24/#129.

**O marco acima não foi atingido.** A previsão de 18/09 não substitui prazo
original nem comprova entrega. Horas realizadas exigem apontamento: os sete
lançamentos existentes no Project têm origem a conferir.


---

## S4 · 21/09 – 25/09 · Próximas ações, condicionadas ao ambiente

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | Tabelas Gold do domínio de mercado em Dataform (item 1.6), com os 8 domínios como alvo | tabelas executadas no GCP, sem KPI nesta fase (ADR 012) |
| Entregamos | Agendamento e monitoramento das 4 fontes públicas em produção (item 1.7) | 4 jobs no Scheduler; alerta disparando em falha simulada |
| Entregamos | Ajustes de framework revelados pela carga real (item 1.8 — reserva já prevista) | o que aparecer no primeiro contato com BigQuery de verdade |
| Entregamos | Dossiê de homologação da Onda 1, com CCEE via dados abertos (ADR 018; A2 encerrada em 14/09) | evidências de carga, replay e aceite; nenhuma homologação presumida |
| Destrava | **A7** — confirmar pedidos de acesso e host BBCE e de credencial read-only/conectividade dos sistemas internos (Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS); MySQL RDS dispensa VPN conforme C8 | chamados e responsáveis registrados; Hubspot segue A9, TempoOK segue acervo A10/#129; CCEE pública independe de credencial |
| Destrava | **A8 atendida em 14/09** — BBCE e TempoOK implementados | documentação deixou de ser bloqueio; restam acesso BBCE e acervo TempoOK |

**Marco**: Onda 1 homologada → 20,69% · R$ 30.720,00.

### Registro de 24/09 — o ambiente chegou no meio da S4

A S4 foi escrita condicionada ao ambiente, e o ambiente chegou nela: a Alup
liberou o GCP em 23/09. O que a semana produziu, até 24/09:

| Trilha | Item | Situação em 24/09 |
|---|---|---|
| Entregamos | Bootstrap e primeiro `apply` em `dev` | **feito em 23/09**: 159 recursos; `hml` com bootstrap |
| Entregamos | Dataform executado no GCP (Bronze, Silver, Gold e asserções) | **feito em 24/09**: 141 ações, zero falhas |
| Entregamos | Agendamento e monitoramento (item 1.7) | **aplicado em 24/09**: 24 disparos, 9 alertas com destinatário |
| Entregamos | Primeira carga real | **24/09**: BCB (câmbio e juros), ONS (carga, EAR e ENA) e a previsão de ENA do TempoOK |
| Entregamos | Ajustes revelados pela carga real (item 1.8) | três defeitos corrigidos no mesmo dia (#215, #222, #223) |
| Entregamos | Dossiê de homologação da Onda 1 | **não nesta semana**: previsto para 07/10, antes do prazo de 16/10 |
| Destrava | A7 — pedidos de acesso da Onda 3 e tokens da Onda 2 | vence em 25/09; registro do que a Alup confirmar em 26/09 |

### Fechamento da S4 — 25/09/2026

| Trilha | Item | Situação em 25/09 |
|---|---|---|
| Entregamos | Carga das 23 entidades públicas | **feita** em `dev` (24/09) e em `hml` (25/09), todas com sucesso |
| Entregamos | Reprocessamento | **demonstrado** em `dev` (câmbio, 24/09) e em `hml` (carga do ONS, 25/09) |
| Entregamos | `hml` no ar | **25/09**: 174 recursos, Dataform em `SUCCEEDED`, `TABLE_STORAGE` ligado pelo próprio deploy |
| Entregamos | Dossiê de homologação das Ondas 0 e 1 | **emitido e enviado em 25/09**, antes dos 29–30/09 previstos, com `terraform plan` sem mudança nos dois ambientes |
| Entregamos | Pauta de alinhamento com a Alup | [`relatorios/2026-09-25-alinhamento.md`](relatorios/2026-09-25-alinhamento.md), com os oito pedidos |
| Entregamos | Onda 2 preparada | roteiro e rascunho do dossiê em [`planos/2026-09-25-dossie-onda-2-preparado.md`](planos/2026-09-25-dossie-onda-2-preparado.md) |
| Entregamos | Rede da Onda 3, lado GCP | **feita em 25/09**: sub-rede na VPC compartilhada da Alupar, `dev` e `hml` ligados, teste de conexão rodando dentro da sub-rede (ADR 024) |
| Entregamos | TLS obrigatório no MySQL | #249, item da ADR 013 para o RDS |
| Destrava | A7 — acessos e credenciais da Onda 3 e tokens da Onda 2 | **25/09: não entregues.** Pedido reiterado em 25/09, por e-mail: IP e rede do FMB, FortiGate e datacenter, e a credencial do FMB no Secret Manager |

---

## S5 · 28/09 – 02/10 · Aceite das Ondas 0 e 1

A sequência vem do [plano de aceleração do faturamento](planos/2026-09-24-aceleracao-do-faturamento.md),
que substituiu as datas do [plano de fechamento](planos/2026-09-24-fechamento-das-ondas.md)
para as Ondas 0 e 1.

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | Terceiro dia seguido de carga agendada do câmbio (26/09) | linha no `status.md` com a execução de 26/09 |
| Entregamos | Grupos da Alup no Portal de `hml`, assim que informados | `portal_acesso` no `hml.tfvars`, deploy e acesso confirmado por alguém da Alup |
| Entregamos | Reunião de aceite (01/10, alternativa 02/10) | Portal demonstrado com login da Alup; dúvidas do dossiê respondidas |
| Entregamos | Rota até o FMB (G6), assim que a faixa chegar | `route-alupdata-to-fmb` aplicada e conferida |
| Entregamos | Teste de conexão do FMB, assim que a rede local e a credencial chegarem | **Testar conexão** em `dev` respondendo `SELECT 1` |
| Destrava | **Quem assina o aceite** (pedido 1 da pauta) | nome confirmado antes da reunião |
| Destrava | **Grupos da Alup** para o Portal (pedido 6) | grupos informados antes da reunião |
| Destrava | **Posição sobre as 32h do item 2.1** (pedido 4) | resposta até 30/09 |
| Destrava | **Onda 3**: IP e rede do FMB, FortiGate e datacenter, credencial do FMB | itens L1 a L6 e N3 do [`runbook/rede-onda3.md`](runbook/rede-onda3.md) |

**Marco**: Ondas 0 e 1 aceitas → 15,52% + 20,69%.

Da S6 em diante: Onda 2 assim que as credenciais chegarem (dossiê em dias,
pelo roteiro preparado), Onda 3 assim que o teste de conexão passar, e `prod`
depois do aceite das Ondas 0 e 1.

---

## Dependências — linha de base e situação em 18/09

| Insumo | Prazo útil | Se não vier |
|---|---|---|
| A3 · projeto GCP | 04/09 | S2 e S3 inteiras escorregam; Onda 0 não homologa |
| A9 · token Hubspot | 11/09 | conector pronto fica parado; item 2.3 não fecha |
| A4 · Questionário de Gaps | 11/09 | respondido; domínios documentados |
| A5/A6 · RACI e BI | 11/09 | respostas recebidas; matriz RACI em 15/09, duas questões residuais na #150 |
| G1 · resposta do Google | encerrada em 10/09 | não é bloqueio atual |
| A2 · decisão CCEE | 18/09 | encerrada em 14/09; acesso público destravado |
| A7 · tokens e VPN | 25/09 | Onda 3 dispara ociosidade de 4h/dia (R$ 256/h). **25/09: não entregue**; o caminho de rede do lado GCP foi preparado pela ness. no mesmo dia, e ficam a rede local e as credenciais |
| A8 · docs BBCE/TempoOK | 25/09 | atendida em 14/09; conectores implementados |

---

## Ressalva atual

A operação e a homologação de S2 em diante seguem **condicionadas a A3**.
O trabalho sem ambiente avançou na S3, como registrado acima, mas não substitui
carga real e aceite. Datas-alvo contratuais, execução e previsão revisada
permanecem separadas; o estado corrente está em [`status.md`](status.md).
