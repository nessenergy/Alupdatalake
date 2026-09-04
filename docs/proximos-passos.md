# Próximos passos — fila de execução

Documento **vivo**: é para riscar linha, não para arquivar. Atualizado em
**2026-09-04**.

Ele existe para responder uma pergunta que os outros três não respondem em uma
tela: **qual é a próxima ação, de quem é, e qual comando a executa.**

- [`status.md`](status.md) — onde estamos e o que trava o quê (fonte da verdade)
- [`plano-semanal.md`](plano-semanal.md) — o que sai em cada semana
- [`plano-execucao.md`](plano-execucao.md) — escopo e estimativa por onda
- **este arquivo** — a fila, com dono e comando

Quando um item aqui fecha, ele sai daqui e o efeito aparece no `status.md`.

---

## 1. Hoje — o que não pode esperar

Hoje é **04/09**, prazo de dois insumos. Ambos vencem *hoje*, não amanhã.

| # | Ação | Dono | Se passar do prazo |
|---|---|---|---|
| 1.1 | **Cobrar o projeto GCP `dev`** (A3): projeto criado, APIs habilitadas, IAM, WIF, Artifact Registry, bucket de state | Alup — cobrança da ness. | É o gargalo mestre: S2 e S3 escorregam inteiras e a Onda 0 não homologa. > 5 dias úteis posterga o cronograma |
| 1.2 | **Branch protection na `main`** + variáveis `GCP_WIF_PROVIDER` e `GCP_DEPLOY_SA` | ness./Alup | O workflow de deploy não autentica, e a `main` segue aceitando push direto |

> **Registre a data da cobrança hoje**, não quando virar problema. É o que
> sustenta postergação, ociosidade ou suspensão numa medição (cláusula 3ª).

---

## 2. Sua fila — ações suas, agora

| # | Ação | Como | Pronto quando |
|---|---|---|---|
| 2.1 | **Criar os 5 campos no GitHub Projects** | PAT clássico com escopo `project`, depois `make campos-projeto owner=nessenergy numero=<n>` — ver [runbook](runbook/acompanhamento-semanal.md) | Horas, Semana, Validado, Correções e Atraso visíveis e preenchíveis no quadro |
| 2.2 | **Passar o baralho do Google uma vez**, em tela cheia (`F`) | `docs/apresentacoes/revisao-arquitetural-gcp.html` | Você sabe onde está cada uma das 8 perguntas da pauta |
| 2.3 | **Marcar a sessão com o Google** | — | Data na agenda, antes do primeiro `terraform apply` |

### Por que 2.3 tem pressa

O argumento do baralho é que o modelo está completo em código **e ainda não foi
instanciado** — recomendação que chega agora se aplica como reprojeto, não como
migração. Essa janela fecha no dia em que o A3 destravar e o primeiro `apply`
subir. Se o GCP vier antes da reunião, o baralho continua correto, mas perde a
melhor parte do argumento.

---

## 3. Decisões que dependem de você

| # | Decisão | Opções | Efeito |
|---|---|---|---|
| 3.1 | **Campo Semana** | (a) manter seleção `S1`–`S19`, gerenciada pelo script; (b) campo de iteração com datas reais, criado à mão na interface | Iteração não é criável por API. Escolhendo (b), o script deixa de gerenciar esse campo |
| 3.2 | **Nome do branch de trabalho** | manter o atual ou renomear por assunto (`feat/campos-acompanhamento-semanal`) | A regra 6 do `AGENTS.md` pede branch nomeado pelo assunto; o branch em uso não atende à regra e já não descreve o conteúdo |
| 3.3 | **Idioma do baralho** | português (atual) ou inglês | Só importa se a sessão for com time do Google fora do Brasil |
| 3.4 | **Redação da exclusão de escopo no baralho de kickoff** (slide de fora de escopo, Fase 3) | manter como está ou trocar por "modelos preditivos avançados" | É exclusão de escopo legítima, não atribuição de autoria — mas é material que vai ao cliente |

---

## 4. Minha fila — o que faço quando você disser

| # | Ação | Depende de |
|---|---|---|
| 4.1 | Renomear o branch e reabrir o PR | decisão 3.2 |
| 4.2 | Versão em inglês do baralho | decisão 3.3 |
| 4.3 | Emitir o relatório de situação da semana em `docs/relatorios/` | fechamento da S2 (11/09) |

---

## 5. Depois que o A3 destravar

Sequência, não lista — cada item depende do anterior. Detalhe em
[`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md).

1. **Rótulos de custo antes do `apply`.** Custo já gasto não se rateia depois;
   a taxonomia tem de entrar *no* primeiro apply, não no segundo.
2. `terraform apply` no ambiente `dev` — datasets, bucket, secrets, IAM.
3. `make deploy-views` — DDL do Bronze e views Silver/Gold.
4. Publicar a imagem e subir o Cloud Run Job + Scheduler.
5. **Três dias consecutivos com `status = SUCESSO`** em `bronze._execucoes`.
   É o critério de aceite do item 0.14 do plano.
6. Validar o replay do raw contra objeto real no GCS.
7. Ligar o Portal MVP no BigQuery e publicar.

Só depois disso a Onda 0 pode ser declarada homologada — entrega técnica não é
homologação, e é o primeiro `apply` que revela IAM insuficiente, cota de API e
formato que o BigQuery recusa.

---

## 6. Prazos da Alup, em ordem de custo

Fonte: [`status.md` §6](status.md). Repetido aqui só como calendário; a tabela
lá é a que vale.

| Prazo | Insumo | Efeito de passar |
|---|---|---|
| **04/09** | A3 · projeto GCP | posterga o cronograma |
| 11/09 | A9 token Hubspot · A4 Questionário · A5 RACI · A6 ferramenta de BI · destinatários de alerta e `billing_account` | Gold sem alvo, Portal sem consumidor, alertas sem quem notificar |
| 18/09 | A2 · decisão sobre a CCEE | 32h da Onda 1 seguem paradas |
| 25/09 | A7 tokens e VPN · A8 documentação BBCE/TempoOK | **ociosidade de 4h/dia** — o maior risco financeiro do contrato |

---

## Como manter isto vivo

Item que fecha sai da tabela; o que ele destravou aparece no `status.md`. Se uma
linha aqui sobrevive a duas semanas sem se mexer, ou ela não era próxima ação,
ou está bloqueada por algo que ainda não foi nomeado — nos dois casos, vale
reescrevê-la em vez de deixá-la envelhecer.
