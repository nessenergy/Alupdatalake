# Plano semanal — próximas 4 semanas

Emitido em **2026-08-27** · S1 revisada em **2026-08-31** e em **2026-09-04** ·
Escopo e estimativa por onda: [`plano-execucao.md`](plano-execucao.md) ·
Situação atual: [`status.md`](status.md)

---

## O quadro em uma frase

Em **18/09/2026**, há 26 entidades implementadas: 23 com dados reais em
dry-run, TempoOK com contrato de API verificado e acervo recente pendente,
BBCE e Hubspot sem credencial. **Não há carga em GCP nem homologação
registrada**. G1 encerrou em 10/09; GCP, billing e planilhas têm previsão de
18/09, sem confirmação de entrega na conferência desta data.

S1 e S2 abaixo preservam o **registro histórico e o plano então vigente**,
inclusive decisões posteriormente substituídas. A região atual é `us-east1`
(ADR 011), Dataform substitui o deploy SQL (ADR 012), o bootstrap é da ness.
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
| A7 · tokens e VPN | 25/09 | Onda 3 dispara ociosidade de 4h/dia (R$ 256/h) |
| A8 · docs BBCE/TempoOK | 25/09 | atendida em 14/09; conectores implementados |

---

## Ressalva atual

A operação e a homologação de S2 em diante seguem **condicionadas a A3**.
O trabalho sem ambiente avançou na S3, como registrado acima, mas não substitui
carga real e aceite. Datas-alvo contratuais, execução e previsão revisada
permanecem separadas; o estado corrente está em [`status.md`](status.md).
