# Relatório de situação — 27/08/2026

AlupData Fase 1 · DataLake · Contrato CPS-01025/2026 · 580h · 19 semanas · 5 ondas
Emitido por ness. Processos e Tecnologia · `main` em `129f579`

Plano por onda: [`plano-execucao.md`](plano-execucao.md) ·
Plano por semana: [`plano-semanal.md`](plano-semanal.md) ·
Situação corrente: [`status.md`](status.md)

---

## Sumário

Todo o trabalho técnico que não depende de insumo da Alup está entregue e
testado. O que falta para homologar a Onda 0 **não é código** — são onze
decisões e provisionamentos que só a contratante pode fazer, e a primeira
delas vence em **04/09**.

| | |
|---|---|
| **5** | conectores com os 7 componentes da cláusula 2ª escritos e testados |
| **170** | testes automatizados passando, 92% de cobertura, CI verde |
| **0** | linhas carregadas em produção — o ambiente Google Cloud ainda não existe |

---

## 1. Onde o projeto está

Fundação construída: framework de ingestão, CLI, Terraform completo, CI/CD com
os portões da cláusula 8ª (Bandit, pip-audit, Gitleaks), log estruturado com
correlação por execução, alertas, painel de saúde do lake e Portal MVP. Cinco
fontes com os sete componentes — BCB, IBGE, ANEEL, ONS e Hubspot.

Quatro foram verificadas em dry-run contra as APIs reais; a ANEEL trouxe 25.263
registros sem nenhum inválido em 28 segundos. O Hubspot é a exceção declarada:
escrito contra a documentação pública, **nunca falou com a API**.

> **A ressalva que governa o resto.** Nada foi validado contra um Google Cloud
> real — nenhum `terraform apply`, nenhuma linha em BigQuery, nenhum job em
> nuvem. É no primeiro apply que aparecem os erros que teste local não pega:
> IAM insuficiente, cota de API, permissão de bucket, formato que o BigQuery
> recusa. **A Onda 0 não deve ser declarada homologada antes disso rodar.**

---

## 2. As onze questões abertas

Ordenadas pela data em que o atraso passa a custar.

| # | A questão | Quem responde | Prazo | Se passar do prazo |
|---|---|---|---|---|
| A3 | O projeto GCP `dev` vai existir quando? Criado, com 10 APIs, IAM, WIF, Artifact Registry e bucket de state | Alup | **04/09** | Duas semanas escorregam; Onda 0 não homologa; passa a contar a cláusula 3ª |
| — | Quem ativa a proteção da `main` e cadastra as 4 variáveis do GitHub do deploy | ness./Alup | **04/09** | Deploy falha na autenticação; `main` aceita push direto |
| A9 | O token do Hubspot sai desta semana? Vai no secret `alupdata-hubspot-api-token` | Alup | 11/09 | Conector pronto segue parado; nenhuma linha de CRM entra |
| A4 | Quem responde as 47 perguntas do Questionário de Gaps, e até quando | Alup | 11/09 | Os 8 domínios não se definem; a Gold fica sem alvo |
| A5 | Quem é o data owner de cada domínio | Alup | 11/09 | Dúvida de regra de negócio sem destinatário |
| A6 | Qual é a ferramenta de BI definitiva | Alup | 11/09 | Gold modelada sem consumidor definido |
| — | Para quais e-mails os alertas tocam, e qual é a `billing_account` | Alup | 11/09 | Alertas e orçamento existem mas não notificam ninguém |
| A2 | CCEE: liberar o IP de saída, usar credencial de agente, ou remanejar as 32h por escrito | Alup | 18/09 | 32h paradas; `agente_ccee` sem origem |
| A7 | Os pedidos de token (Onda 2) e VPN read-only (Onda 3) já foram abertos? Em que data | Alup | 25/09 | Único item que dispara cláusula financeira: 4h/dia a R$ 256/h |
| A8 | A documentação técnica de BBCE e TempoOK pode vir antes do token | Alup | 25/09 | Onda 2 só começa depois do token, em vez de chegar pronta |
| — | Qual profundidade de histórico do ONS vamos carregar | Alup/ness. | antes da 1ª carga | Decidir depois de carregar significa recarregar |

**Cláusula 3ª**: atraso > 5 dias úteis posterga o cronograma; > 5 dias úteis em
VPN/credencial gera ociosidade de 4h/dia (R$ 256/h); > 20 dias corridos
suspende os serviços. A data de cada pedido precisa ser anotada **no dia em que
o atraso começa**, não quando vira problema.

---

## 3. O que esperamos entregar

Detalhe em [`plano-semanal.md`](plano-semanal.md). Da S2 em diante, tudo é
condicional a A3.

| Semana | O que sai | Marco |
|---|---|---|
| **S1** 31/08–04/09 | Repositório pronto para o apply; runbook do dia-1; roteiro do Questionário | — |
| **S2** 07/09–11/09 | `apply` real; imagem publicada; primeira execução com `SUCESSO`; views em BigQuery; Hubspot contra a API | — |
| **S3** 14/09–18/09 | 8 domínios; dimensões contra dado real; Portal publicado com autenticação; BCB 3 dias sozinho | **Onda 0 · 15,52%** |
| **S4** 21/09–25/09 | Gold de mercado; 4 fontes agendadas em produção; dossiê de homologação | **Onda 1 · 20,69%** |

---

## 4. O que não depende de ninguém

A ness. já adiantou tudo o que era possível adiantar sem ambiente e sem
credencial. O motor de planilhas da Onda 4 foi construído antes da hora porque
não dependia de nada. O conector do Hubspot foi escrito às cegas, com o teste
de integração desligado até o token chegar — quando vier, a tarefa é rodar e
conferir, não começar.

O mesmo tratamento foi tentado com BBCE, TempoOK e CCEE e **não se sustenta**:
a CCEE responde 403 até na página de documentação, a BBCE não tem endpoint
público e a TempoOK não publica contrato de API. Escrever schema por
adivinhação seria pior que não escrever — cria retrabalho com aparência de
progresso. É o que torna A8 tão útil quanto o token.

Entregues fora do escopo faturado, dentro da possibilidade de sustentação: o
painel de saúde do lake e a observabilidade com alertas de falha, silêncio e
registros inválidos em alta.

---

## 5. Riscos, na ordem em que preocupam

| Risco | Impacto | O que estamos fazendo |
|---|---|---|
| VPN e credenciais da Onda 3 atrasam | Alto — 155h paradas e ociosidade | Pedir na Onda 0; registrar data de pedido e cobrança |
| O ambiente GCP não sai a tempo | Alto — nenhuma onda homologa | Issue #55 com detalhamento e custo; prazo em 04/09 |
| Layout de CCEE ou ONS muda sem aviso | Alto — 60h em risco | Validação Pydantic; bruto no GCS permite reprocessar |
| Schema legado pior que o previsto | Médio-alto | Regime de horas permite realocar; comunicar antes de estourar |
| Volume do ONS estoura o custo de BigQuery | Médio — custo recorrente da Alup | Particionar sempre; decidir histórico antes de carregar |
| Escopo do Portal MVP cresce | Médio | Cravado na ADR 005; pedido novo vira aditivo |

---

## 6. O que pedimos de decisão agora

Três coisas, nenhuma delas técnica:

1. **Uma data para o projeto GCP**, com nome de quem provisiona. Não uma
   estimativa — uma data. Todo o cronograma pendura nela.
2. **Uma data para o Questionário de Gaps** e quem responde cada bloco. Não
   trava o deploy, mas trava a modelagem da Gold — que é o que a Alup vai
   efetivamente consumir.
3. **Abrir hoje os pedidos de token e VPN** das Ondas 2 e 3, mesmo que só sejam
   usados em outubro. Maior risco financeiro do contrato e o único cujo prazo
   interno não controlamos.

**O que gostaríamos de dizer na próxima reunião**: que a Onda 0 está homologada
com evidência de execução real, que a Onda 1 fechou com quatro fontes
carregando sozinhas todo dia, e que a Onda 2 já tem conector escrito esperando
credencial. Os três dependem de decisões desta semana, não de linhas de código.
