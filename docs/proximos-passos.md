# Próximos passos — fila de execução

Documento **vivo**: é para riscar linha, não para arquivar. Atualizado em
**2026-09-09**.

Ele existe para responder uma pergunta que os outros três não respondem em uma
tela: **qual é a próxima ação, de quem é, e qual comando a executa.**

- [`status.md`](status.md) — onde estamos e o que trava o quê (fonte da verdade)
- [`plano-semanal.md`](plano-semanal.md) — o que sai em cada semana
- [`plano-execucao.md`](plano-execucao.md) — escopo e estimativa por onda
- **este arquivo** — a fila, com dono e comando

Quando um item aqui fecha, ele sai daqui e o efeito aparece no `status.md`.

---

## 1. O que está travando tudo

A cadeia hoje é **em série**, e a ponta dela é a única sem prazo:

    G1 (Google responde) → A3 (ambiente GCP) → 1º apply → Onda 0 homologada

| # | Ação | Dono | Situação |
|---|---|---|---|
| 1.1 | **Obter uma data para a resposta do Google** — [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77) | Alup / Google | **sem prazo acordado.** É o item que precede todo o resto |
| 1.2 | **Projeto GCP `dev`** (A3) | Alup | **vencido em 04/09**, atraso registrado, condicionado a G1. Quem cria (E1) e de quem é a `billing_account` (E2) foi perguntado pela Alup em 09/09 e **esclarecido no mesmo dia**: ambos são da Alup |
| 1.3 | **Branch protection na `main`** + variáveis `GCP_WIF_PROVIDER` e `GCP_DEPLOY_SA` (A1) | ness./Alup | impossível no plano GitHub Free — decidir entre Team pago ou risco assumido por escrito |

> O atraso de A3 está registrado em
> [`relatorios/2026-09-04-a3-nao-entregue.md`](relatorios/2026-09-04-a3-nao-entregue.md),
> emitido no dia em que a situação se configurou. Condicionar A3 a G1 não
> interrompe a contagem da cláusula 3ª — o contrato conta o atraso do insumo,
> não o motivo.

---

## 2. Sua fila

| # | Ação | Como | Pronto quando |
|---|---|---|---|
| 2.1 | **Cobrar a data do Google** | [issue #77](https://github.com/nessenergy/Alupdatalake/issues/77) tem o texto pronto para a conversa | Data registrada na issue |
| 2.2 | **Enviar o relatório de 04/09 à Alup** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.3 | ~~Decidir a região com a Alup~~ | resposta à pergunta E7 do questionário | **Decidido em 10/09**: `us-east1` ([ADR 011](arquitetura/decisoes/011-regiao-us-east1.md)) |
| 2.4 | **Enviar à Alup o registro de 09/09 sobre E1 e E2** | `.md` e `.html` prontos em [`relatorios/`](relatorios/) | Registro na mão da contratante |
| 2.5 | **Obter a data e o nome do responsável por A3** | a atribuição já está esclarecida; falta a data — [issue #55](https://github.com/nessenergy/Alupdatalake/issues/55) | E1 respondido com data e nome |
| 2.6 | **Obter a `billing_account` e o teto do alerta** | sugestão de R$ 500/mês em `dev` — [issue #87](https://github.com/nessenergy/Alupdatalake/issues/87) | E2 e E3 respondidos |

### Por que 2.1 tem pressa

O baralho argumenta que o modelo está completo em código **e ainda não foi
instanciado** — por isso a recomendação entra como reprojeto, não como
migração. Como o `apply` agora espera pela resposta, a janela está garantida;
o que falta é ela ter fim. Sem data, o cronograma não fica com previsão ruim:
fica sem previsão.

---

## 3. Decisões que dependem de você

| # | Decisão | Opções | Efeito |
|---|---|---|---|
| 3.1 | **Campo Semana** | (a) manter seleção `S1`–`S19`, gerenciada pelo script; (b) iteração com datas reais, criada à mão | Iteração não é criável por API. Em (b), o script deixa de gerenciar o campo |
| 3.2 | **Idioma do baralho** | português (atual) ou inglês | Só importa se a plateia do Google não for do Brasil |
| 3.3 | **Redação da exclusão de escopo no baralho de kickoff** | manter ou trocar por "modelos preditivos avançados" | Exclusão legítima da Fase 3; é preferência, não correção |
| 3.4 | **Paralelos restantes** | dicionário de dados das fontes que faltam · endurecer o Portal MVP · outra coisa | São as duas frentes úteis que sobraram sem GCP |
| 3.5 | **Branch protection** | GitHub Team pago por usuário, ou assumir o risco por escrito | Hoje a `main` aceita push direto, o que contraria o SSDLC da cláusula 8ª |

Decisões já tomadas hoje: **região** `southamerica-east1` ([ADR 009](arquitetura/decisoes/009-regiao-do-ambiente.md)),
substituída em 10/09 por **região** `us-east1` ([ADR 011](arquitetura/decisoes/011-regiao-us-east1.md)), e **tom cordial**
nos relatórios (convenção no [README](relatorios/README.md) do diretório).

---

## 4. Minha fila

| # | Ação | Depende de |
|---|---|---|
| 4.1 | Dicionário de dados e linhagem das fontes que faltam | decisão 3.4 |
| 4.2 | Endurecer o Portal MVP enquanto roda com provedor simulado | decisão 3.4 |
| 4.3 | Versão em inglês do baralho | decisão 3.2 |
| 4.4 | Apagar `docs/fluxo-execucao` e o branch de trabalho, já mesclados; arquivar os dois `backup/*` como tag | permissão — daqui o `git push --delete` e a API respondem 403 |
| 4.5 | Emitir o relatório de situação da semana | fechamento da S2 (11/09) |
| 4.6 | Conferir as tarifas-premissa de `us-east1` na tabela oficial de preços do BigQuery e atualizar `src/portal/custo.py` e `sql/gold/custo_consultas.sql` se diferirem de US$ 6,25 por TiB varrido e US$ 0,02 por GiB·mês | acesso à tabela oficial de preços |

### Uma pendência técnica do próprio repositório

O CI **não dispara em PR deste branch**: `ci.yml` reage a `pull_request` para
`main` e a `push` na `main`, e os eventos de sincronização não estão gerando
execução. O contorno tem sido validar localmente antes de cada push — `ruff`,
suíte completa, Bandit, links — e deixar o merge disparar o CI pelo gatilho de
`push`. Funciona, mas inverte a ordem: o CI vira conferência posterior em vez
de portão. Vale investigar quando houver folga.

---

## 5. Depois que G1 e A3 destravarem

Sequência, não lista — cada item depende do anterior. Detalhe em
[`runbook/primeiro-deploy.md`](runbook/primeiro-deploy.md).

1. **Recomendações do Google viram ADR** — novo ou revisão de existente. É o
   que justifica ter esperado.
2. **Rótulos de custo** já estão prontos (FinOps F0, implementado em 04/09) —
   conferir que entraram no `apply`, não depois dele.
3. `terraform apply` no ambiente `dev` — datasets, bucket, secrets, IAM.
4. `make deploy-views` — DDL do Bronze e views Silver/Gold.
5. Publicar a imagem e subir o Cloud Run Job + Scheduler.
6. **Três dias consecutivos com `status = SUCESSO`** em `bronze._execucoes`.
7. Validar o replay do raw contra objeto real no GCS.
8. Ligar o Portal MVP no BigQuery e publicar.

Só depois disso a Onda 0 pode ser declarada homologada — entrega técnica não é
homologação, e é o primeiro `apply` que revela IAM insuficiente, cota de API e
formato que o BigQuery recusa.

---

## 6. Prazos, em ordem de custo

Fonte: [`status.md` §6](status.md). Repetido aqui como calendário; a tabela lá
é a que vale.

| Prazo | Insumo | Situação |
|---|---|---|
| **sem data** | **G1 · resposta do Google** | precede A3 por decisão da Alup — é o gargalo atual |
| **04/09 — vencido** | A3 · projeto GCP | atraso registrado; S2 e S3 escorregam |
| 11/09 | A9 token Hubspot · A4 Questionário (com eles desde 31/08) · A5 RACI · A6 ferramenta de BI · destinatários de alerta e `billing_account` | Gold sem alvo, Portal sem consumidor, alertas sem quem notificar |
| 18/09 | A2 · decisão sobre a CCEE — a via (c) já não tem custo técnico desconhecido (driver SQL Server pronto) | 32h da Onda 1 paradas |
| 25/09 | A7 tokens e VPN · A8 documentação BBCE/TempoOK | **ociosidade de 4h/dia** — maior risco financeiro do contrato |

---

## Como manter isto vivo

Item que fecha sai da tabela; o que ele destravou aparece no `status.md`. Se uma
linha aqui sobrevive a duas semanas sem se mexer, ou ela não era próxima ação,
ou está bloqueada por algo que ainda não foi nomeado — nos dois casos, vale
reescrevê-la em vez de deixá-la envelhecer.
