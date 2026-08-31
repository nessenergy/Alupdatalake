# Plano semanal — próximas 4 semanas

Emitido em **2026-08-27** · S1 revisada em **2026-08-31** · `main` em `db94412` ·
Escopo e estimativa por onda: [`plano-execucao.md`](plano-execucao.md) ·
Situação atual: [`status.md`](status.md)

---

## O quadro em uma frase

Todo o trabalho técnico que **não** depende da Alup já está entregue: framework,
5 conectores, motor de planilha, Portal MVP, observabilidade e Terraform — 170
testes, 92% de cobertura, CI verde. O que resta na Onda 0 e na Onda 1 está
parado em insumo da contratante (A3, A4, A9, A2). **Nada foi validado contra um
GCP real**, porque ele ainda não existe.

Por isso este plano tem duas trilhas por semana:

- **Entregamos** — o que a ness. produz mesmo sem resposta da Alup.
- **Destrava** — o insumo que precisa chegar naquela semana para a semana
  seguinte não virar hora ociosa.

Semanas contadas de segunda a sexta. S1 começa em **2026-08-31**.

---

## S1 · 31/08 – 04/09 · Ambiente e contrato de dados

> Revisado em **31/08**, primeiro dia da semana. Dois itens previstos aqui já
> foram entregues antes de a semana começar (PRs #61 a #65): o runbook do
> primeiro deploy e o Questionário de Gaps. Em compensação, dois bloqueios
> novos apareceram — ver "Descobertas" abaixo.

### Já entregue, antes do prazo

| Item | Onde |
|---|---|
| Runbook do primeiro deploy | [`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md) |
| Questionário de Gaps: 47 perguntas, 7 blocos, prazos escalonados | [`questionario-gaps.md`](questionario-gaps.md) · PDF em `envio/` |
| Caminho de banco relacional da Onda 3 | `src/core/banco.py` (ADR 008) |
| Replay de raw, sanitização de credencial, IAM por recurso | PR #64 |

### O que esta semana precisa produzir

| Dia | Item | Entregável verificável |
|---|---|---|
| **Seg 31/08** | **Enviar o Questionário de Gaps à Alup** | e-mail enviado, com data, hora e destinatários registrados na issue [#8](https://github.com/nessenergy/Alupdatalake/issues/8) |
| **Seg 31/08** | Cobrar A3 por escrito, pedindo **data com responsável nomeado** | registro na issue [#55](https://github.com/nessenergy/Alupdatalake/issues/55) |
| **Seg 31/08** | **Decidir a região** do ambiente: `us-east1` (valor atual em `dev.tfvars`) ou `southamerica-east1` (o que a pergunta E7 assume) | `dev.tfvars` e `prod.tfvars` coerentes com a decisão |
| Ter–Qua | Build da imagem da CLI e execução local do job | `docker run` da imagem executando `alupdata listar` |
| Ter–Qua | `banco.py` exercitado contra Oracle XE e MySQL em contêiner | uma consulta real por driver, com paginação verificada |
| Qui–Sex | Variáveis do GitHub preenchidas assim que A3 der os valores | `gh api .../actions/variables` devolvendo as quatro |
| Qui–Sex | Issues das lacunas de rastreamento criadas e ligadas ao Project | trabalho das PRs #62–#65 rastreável na medição |

### Destrava (ação da Alup)

| Insumo | Prazo | Issue |
|---|---|---|
| **A3** — projeto GCP `dev`, 10 APIs, IAM, WIF, Artifact Registry, bucket de state | **04/09** | [#55](https://github.com/nessenergy/Alupdatalake/issues/55), [#1](https://github.com/nessenergy/Alupdatalake/issues/1) |
| **A9** — token Hubspot no secret `alupdata-hubspot-api-token` | 11/09 | [#24](https://github.com/nessenergy/Alupdatalake/issues/24) |

> Se A3 não chegar até **04/09**, começa a contagem da cláusula 3ª (atraso > 5
> dias úteis posterga o cronograma). Registrar a data do pedido no dia em que o
> atraso começa.

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

## S2 · 07/09 – 11/09 · Primeiro deploy real

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

---

## S3 · 14/09 – 18/09 · Fechar a Onda 0

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | Os **8 domínios analíticos** definidos a partir das respostas de A4 (item 0.10) | documento com pergunta de negócio e fontes por domínio |
| Entregamos | Dimensões comuns Silver fechadas contra dado real, não contra fixture (item 0.11) | `arquitetura/visao-geral.md` atualizado, regra por dimensão |
| Entregamos | Portal MVP ligado no BigQuery e publicado no Cloud Run com IAP (item N2/0.15) | URL autenticada mostrando uma view Gold real — **nunca** com `--allow-unauthenticated` |
| Entregamos | BCB rodando sozinho por 3 dias consecutivos (item 0.14) | 3 execuções `SUCESSO` seguidas, sem intervenção |
| Entregamos | **Dossiê de homologação da Onda 0** | checklist da skill `homologacao-onda` com evidência por linha |
| Destrava | **A2** — decisão sobre a CCEE (liberar IP, credencial de agente, ou remanejar as 32h) | issue [#52](https://github.com/nessenergy/Alupdatalake/issues/52) |

**Marco**: Onda 0 homologada → 15,52% · R$ 23.040,00.

---

## S4 · 21/09 – 25/09 · Fechar a Onda 1 e abrir a 2

| Trilha | Item | Entregável verificável |
|---|---|---|
| Entregamos | Views Gold do domínio de mercado (item 1.6), agora com os 8 domínios como alvo | uma view por pergunta de negócio nomeada |
| Entregamos | Agendamento e monitoramento das 4 fontes públicas em produção (item 1.7) | 4 jobs no Scheduler; alerta disparando em falha simulada |
| Entregamos | Ajustes de framework revelados pela carga real (item 1.8 — reserva já prevista) | o que aparecer no primeiro contato com BigQuery de verdade |
| Entregamos | Dossiê de homologação da Onda 1, com a CCEE tratada conforme a decisão de A2 | |
| Destrava | **A7** — pedidos de token (BBCE, TempoOK, CCEE credenciado) e de VPN/credencial read-only (Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS) **abertos agora**, não na véspera da onda | é o maior risco financeiro do contrato |
| Destrava | **A8** — documentação técnica de BBCE e TempoOK | permite escrever o conector antes do token, como foi feito no Hubspot |

**Marco**: Onda 1 homologada → 20,69% · R$ 30.720,00.

---

## O que trava o quê — resumo de uma linha cada

| Insumo | Prazo útil | Se não vier |
|---|---|---|
| A3 · projeto GCP | 04/09 | S2 e S3 inteiras escorregam; Onda 0 não homologa |
| A9 · token Hubspot | 11/09 | conector pronto fica parado; item 2.3 não fecha |
| A4 · Questionário de Gaps | 11/09 | sem os 8 domínios, a Gold da Onda 1 fica sem alvo |
| A5/A6 · RACI e BI | 11/09 | dúvida de regra de negócio sem dono; Portal sem consumidor definido |
| A2 · decisão CCEE | 18/09 | 32h da Onda 1 seguem paradas |
| A7 · tokens e VPN | 25/09 | Onda 3 dispara ociosidade de 4h/dia (R$ 256/h) |
| A8 · docs BBCE/TempoOK | 25/09 | Onda 2 só começa depois do token, em vez de antes |

---

## Ressalva

S2 em diante é **condicional a A3**. Se o ambiente GCP não existir, o que
sobra de trabalho não-bloqueado são horas de documentação e preparo — que já
foram, em boa parte, adiantadas. A partir daí o projeto não avança por esforço
da ness.; avança por decisão da Alup. Isso precisa estar dito na reunião
semanal, não descoberto na medição.
