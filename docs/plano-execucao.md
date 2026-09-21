# Plano de Execução — AlupData Fase 1: DataLake

Contrato CPS-01025/2026 · 580h · 19 semanas · 5 ondas
Linha de base: 2026-08-25 · referências e situação revisadas em 2026-09-18

Situação de execução, atualizada a cada entrega: [`status.md`](status.md).

Este plano detalha **como** as 580h contratadas serão gastas. Ele não substitui
o contrato (`docs/contrato/resumo-contrato.md`); traduz o escopo em tarefas com
estimativa, dependência e critério de aceite.

> **Linha de base:** S1 começou em 31/08/2026, após o kickoff de 27/08.
> As 580h, as cinco ondas e as datas contratuais permanecem como referência.
> Atrasos de insumo e previsões revisadas são registrados em `status.md`;
> não alteram silenciosamente a linha de base nem comprovam homologação.

---

## 1. Como o plano se organiza

- **Onda** = marco de faturamento (cláusula 6ª) e início de 30 dias de garantia.
- **Fonte entregue** = os 7 componentes da cláusula 2ª homologados. Não existe
  entrega parcial de fonte: 5 de 7 é retrabalho na medição.
- **Estimativa** em horas técnicas. Onde a estimativa tem risco alto (fonte sem
  documentação, banco interno desconhecido), está marcado com **⚠**.
- **Ordem dentro da onda**: fonte por fonte, ponta a ponta. Fazer 5 conectores
  pela metade em paralelo esconde problema de framework até o fim da onda.

Papéis usados abaixo: **ness.** (contratada), **Alup** (contratante),
**data owner** (pessoa da Alup responsável por uma fonte).

---

## 2. Onda 0 — Fundação & Arquitetura · S1–S2 · 90h

Marco 1 — 15,52% · R$ 23.040,00

### 2.1 Implementação inicial (peso orçado de ~40h; não horas realizadas)

| # | Entrega | Onde |
|---|---|---|
| 0.1 | Framework de ingestão: runner, janela, registry, GCS, BigQuery, secrets, HTTP | `src/core/` · ADR 003 |
| 0.2 | CLI única (`alupdata listar` / `ingerir`) | `src/cli.py` |
| 0.3 | Conector de referência BCB/PTAX com os 7 componentes | `src/conectores/bcb_cambio.py` |
| 0.4 | Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM | `infra/` |
| 0.5 | CI/CD: lint, testes, Bandit, pip-audit, Gitleaks, Terraform validate | `.github/workflows/` |
| 0.6 | Scaffolding dos 7 componentes (`make novo-conector`) | `scripts/` |
| 0.7 | Decisões registradas: framework, Dataform nas três camadas e Workflows na Onda 3 | ADR 003, 012, 017 |
| 0.8 | Runbook de deploy | `docs/runbook/deploy.md` |

### 2.2 Complemento da Onda 0 (peso orçado de ~50h; situação por item)

| # | Tarefa | Est. | Depende de | Critério de aceite |
|---|---|---|---|---|
| 0.9 | Questionário de Gaps (47 perguntas): enviar, conduzir e consolidar respostas | 10h | **Alup** responder | Respostas consolidadas em `docs/` e lacunas nomeadas |
| 0.10 | Definir os **8 domínios analíticos** a partir das respostas | 8h | 0.9 | **Concluído em 14/09** — [`arquitetura/dominios-analiticos.md`](arquitetura/dominios-analiticos.md). Os domínios são os da resposta ao B1: 8 domínios em 11 linhas, porque três têm responsáveis distintos por subtemas. A1 respondeu outra pergunta — o que o lake responde como um todo — e é dele, via A2, que sai a ordem de entrega |
| 0.11 | Fechar as **dimensões comuns Silver** contra fontes reais | 6h | 0.9, 0.10 | **Concluído em 14/09** — regra por dimensão em [`arquitetura/visao-geral.md`](arquitetura/visao-geral.md), com as regras D3 a D7 do questionário e **duas lacunas nomeadas**: o de-para de usina (Alup) e o mês CCEE (ness.) |
| 0.12 | Matriz RACI e data owners por domínio | 4h | **Alup** nomear | RACI publicada; cada fonte com dono nomeado |
| 0.13 | Provisionar o ambiente GCP `dev`: projeto, APIs, WIF, Artifact Registry, backend do state | 8h | **Alup** criar `dev` primeiro, vincular billing e conceder papéis; **ness.** executar bootstrap (ADR 015). `hml` e `prod` seguem sem bloquear o primeiro apply em `dev` | `terraform apply` limpo; Dataform executado pelo deploy (`make dataform-compile` confere compilação local) |
| 0.14 | Primeiro deploy real: imagem publicada, job agendado, BCB rodando diariamente | 6h | 0.13 | 3 dias consecutivos com `status = SUCESSO` em `bronze._execucoes` |
| 0.15 | Portal MVP com autenticação (escopo mínimo da cláusula 4ª) | 8h → **tela pronta**, falta ligar no BigQuery e publicar | 0.13 | Login funcionando; uma tabela Gold visível. Escopo cravado na ADR 005; roda hoje com provedor simulado |
| — | **Homologação da Onda 0** | — | tudo acima | Evidências reunidas (ver `homologacao-onda`) |

**Riscos da onda**
- 0.9 e 0.12 dependiam da Alup: questionário respondido em 11/09 e matriz RACI
  recebida em 15/09. Domínios definidos; restam duas questões de governança (#150).
- 0.13 depende de o projeto GCP existir. Atraso > 5 dias úteis posterga tudo.
- 0.15 é o único item de front-end do contrato; escopo precisa ficar cravado
  por escrito antes de começar, ou vira poço sem fundo.

---

## 3. Onda 1 — Inteligência de Mercado Base · S3–S7 · 120h

Marco 2 — 20,69% · R$ 30.720,00 · **APIs públicas, sem dependência da Alup**

Esta é a única onda que pode rodar inteira sem insumo da contratante — por isso
ela é o colchão do cronograma.

| # | Fonte | Est. | Complexidade | Observações |
|---|---|---|---|---|
| 1.1 | **CCEE InfoMercado** | 32h | alta | **Destravada em 14/09** ([ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)): era filtro de cliente não identificado, não bloqueio de IP. `pld_horario_submercado` e `lista_perfil_v1` entregues; a fila das demais entidades está na [ADR 021](arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md) — 24 conjuntos escolhidos por demanda dos domínios do B1 |
| 1.2 | **ONS carga** | 28h ⚠ | alta | **Concluído.** CSV anual por subsistema; primeira fonte a preencher `submercado` |
| 1.3 | **ANEEL SIGA** | 20h | média | **Concluído.** Cadastro de ~25 mil empreendimentos; alimenta `codigo_usina` |
| 1.4 | **IBGE IPCA** | 12h | baixa | **Concluído.** Período mensal, payload aninhado |
| 1.5 | **BCB câmbio** | — | — | **Concluído na Onda 0** como conector de referência |
| 1.6 | Tabelas Gold do domínio de mercado (ADR 012) | 16h | — | Depende dos 8 domínios (0.10) |
| 1.7 | Agendamento e monitoramento das 4 fontes | 8h | — | Job + Scheduler por fonte; alerta em falha |
| 1.8 | Ajustes no framework revelados pelas fontes reais | 4h | — | Reserva deliberada: a 2ª fonte é quem testa o framework de verdade |

**Ordem executada**: BCB → IBGE → ANEEL → ONS. Cada uma exercitou um formato
diferente (diário, mensal aninhado, cadastro paginado, CSV anual) e o framework
absorveu as quatro sem alteração — só `extrair()` e `transformar()` mudaram.

### 3.1 CCEE InfoMercado — destravada em 14/09

Por três semanas esta linha registrou um bloqueio: `www.ccee.org.br` e
`dadosabertos.ccee.org.br` respondiam **HTTP 403** a requisição automatizada, e
três caminhos estavam sobre a mesa — liberação de IP junto à CCEE, credencial
de agente, ou download manual pelo S2 Data Intake. Todos dependiam da
contratante.

**Nenhum foi necessário.** O 403 era filtro de cliente não identificado, não
bloqueio de origem: com o cabeçalho de identificação em `src/core/http.py`, a
API CKAN, o portal e os arquivos respondem normalmente
([ADR 018](arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)). A pendência A2
foi encerrada e as 32h voltaram a andar **sem insumo da Alup**.

O que sobrou não é técnico nem contratual: é escolha. São 204 conjuntos
públicos, e ingerir todos seria pagar 7 componentes por arquivo que ninguém
pediu. A [ADR 021](arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md)
escolhe **24**, por demanda dos domínios do B1, com fila nomeada. Em 18/09,
há 11 entidades CCEE implementadas e verificadas em dry-run; a cobertura
atual está no índice de dicionários e em `status.md`. Conjuntos selecionados,
entidades implementadas e as 13 fontes contratuais são contagens distintas.

O cabeçalho é a única dependência frágil: o filtro é da CCEE e pode mudar. Se o
403 voltar, a investigação começa pelo que a origem passou a exigir, não pelo
conector.

**Riscos**
- CCEE e ONS não têm contrato de API estável; mudança de layout entre períodos
  é normal. A validação Pydantic é o que transforma isso em erro visível em vez
  de dado silenciosamente errado.
- Se a granularidade do ONS for semi-horária com histórico longo, o volume e o
  custo de BigQuery mudam de ordem de grandeza — decidir profundidade de
  histórico **antes** de carregar.

---

## 4. Onda 2 — APIs com Credenciais · S8–S11 · 110h

Marco 3 — 18,97% · R$ 28.160,00 · **Bloqueada por credencial da Alup**

| # | Fonte | Est. | Credencial necessária |
|---|---|---|---|
| 2.1 | **CCEE agente credenciado** | 32h ⚠ | Certificado/credencial de agente |
| 2.2 | **BBCE** | 28h ⚠ | Implementado no PR #131; faltam acesso e host (#23) |
| 2.3 | **Hubspot** | 20h → **~4h restantes** | Token de API (private app). Os 7 componentes foram escritos contra documentação pública em 2026-08-26, sem acesso real; falta rodar contra a API real e ajustar |
| 2.4 | **TempoOK** | 18h | Implementado, **dois produtos**: o boletim tem contrato verificado mas acervo só até 26/10/2022 (#129); a **previsão de ENA** (`tempook_ena_prevs`) responde para a data de hoje, verificada em 21/09 — só o caminho de exemplo é conhecido, a Alup vai indicar os demais |
| 2.5 | Tabelas Gold de preço e posição comercial | 12h | — |

**Estratégia contra o bloqueio** (decidida no brainstorm): para cada fonte
travada, escrever **antes** o schema Pydantic e os fixtures a partir da
documentação pública, com o teste de integração marcado como `skipif`. Quando o
token chegar, a tarefa é ligar e ajustar — não começar. Isso tira a Onda 2 do
caminho crítico de *desenvolvimento*, mas **não** do de homologação: sem
credencial não há dado real, e sem dado real não há medição.

**Riscos**
- Atraso > 5 dias úteis na entrega de token: cronograma posterga.
- Atraso > 20 dias corridos: suspensão automática dos serviços (cláusula 3ª).
- Registrar por escrito a data de cada pedido e de cada cobrança, **no dia em
  que o atraso começa** — não quando vira problema.

---

## 5. Onda 3 — Sistemas Internos · S12–S16 · 155h

Marco 4 — 26,72% · R$ 39.680,00 · **A maior onda; bloqueada por VPN e credencial**

| # | Fonte | Est. | Acesso necessário |
|---|---|---|---|
| 3.1 | **Oracle FMB** | 45h ⚠ | VPN + usuário read-only + schema documentado |
| 3.2 | **Portal Alup** (MySQL/NoSQL/Storage) | 40h ⚠ | VPN + credenciais read-only |
| 3.3 | **MySQL RDS Comercialização** | 30h ⚠ | Usuário read-only e conectividade; C8 dispensa VPN e peering |
| 3.4 | **RM/TOTVS** | 25h ⚠ | Endpoints e credencial |
| 3.5 | Orquestração em Cloud Workflows | 10h | — |
| 3.6 | Tabelas Gold que cruzam interno × mercado | 5h | — |

**Marcos técnicos desta onda**
- É aqui que o framework encontra fontes **não-HTTP**: `extrair()` passa a falar
  com driver de banco. O contrato do conector não muda; só a implementação.
- 3.5 é o gatilho combinado no ADR 004 — dependência real entre pipelines —,
  atendido por Cloud Workflows em vez de Composer desde o [ADR 017](arquitetura/decisoes/017-orquestracao-sem-composer.md):
  o teto de US$ 400/mês informado pela Alup em E2 não comporta um ambiente
  Composer ligado 24×7. A orquestração chama a mesma CLI, como previsto.

**Riscos**
- Estimativas ⚠ em todas as fontes: schema de sistema legado só se conhece
  depois de olhar. Se um schema for muito pior que o previsto, a realocação sai
  das horas de outra fonte — o regime é de horas, não de empreitada.
- VPN é o item de maior risco do contrato inteiro: atraso aqui dispara a taxa
  de ociosidade de 4h/dia.

---

## 6. Onda 4 — Planilhas, Governança & Handoff · S17–S19 · 105h

Marco 5 — 18,10% · R$ 26.880,00

| # | Tarefa | Est. | Depende de |
|---|---|---|---|
| 4.1 | Motor **S2 Data Intake** (CSV/XLSX): ingestão de planilha sob template | 30h → **motor pronto**; resta declarar os templates | Templates dependem dos exemplos de planilha G3/#142; A4 foi respondido em 11/09. O motor não dependia de nada e foi adiantado em 2026-08-26 — `docs/arquitetura/s2-data-intake.md` |
| 4.2 | Fontes pendentes que ficaram de ondas anteriores | 20h | — |
| 4.3 | **Knowledge Catalog**: catálogo e linhagem (ADR 014) | 20h | Todas as fontes carregadas |
| 4.4 | Tabelas Gold consolidadas, sem KPI nesta fase (ADR 012) | 15h | 0.10 (8 domínios) |
| 4.5 | Documentação final e dicionário completo | 10h | Todas as fontes |
| 4.6 | **Handoff técnico**: repasse ao time que vai operar | 10h | 4.5 |

**Sobre 4.1**: o motor de planilha é o único componente que aceita dado
humano-editado. Ele precisa rejeitar arquivo fora do template com erro claro —
planilha "quase certa" carregada em silêncio é o modo de falha clássico aqui.

**Sobre 4.6**: o handoff é técnico (cláusula 5ª exclui treinamento de usuário
final). O material é o repositório: runbook, dicionário, ADRs e as skills em
`.claude/skills/`.

---

## 7. Dependências da Alup — resumo acionável

| Quando | O que | Bloqueia | Efeito do atraso |
|---|---|---|---|
| Onda 0 | Questionário de Gaps, RACI, data owners, ferramenta de BI | 0.10, 0.11, 0.12 | Respostas recebidas; questões residuais de RACI na #150 |
| Onda 0 | Projeto GCP, IAM, WIF | 0.13, 0.14, 0.15 | Nada sobe; > 5 dias úteis posterga o cronograma |
| Até Onda 2 | Tokens: CCEE credenciado, BBCE, Hubspot, TempoOK | 2.1–2.4 | > 5 dias úteis posterga; > 20 dias suspende |
| Até Onda 3 | VPN + credenciais read-only: Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | 3.1–3.4 | Ociosidade de 4h/dia (R$ 256/h) |
| Até Onda 4 | Planilhas nos templates definidos | 4.1 | Motor de intake sem insumo para validar |

**Recomendação**: abrir os pedidos das Ondas 2 e 3 **na Onda 0**, não na véspera
de cada onda. O prazo interno da Alup para VPN e credencial de sistema legado é
historicamente o maior risco deste tipo de projeto, e é o único que dispara
cláusula financeira.

---

## 8. Como cada entidade de uma fonte é desenvolvida

1. `make novo-conector fonte=X entidade=Y` — gera os 7 componentes esqueletados
2. Ler a documentação da fonte; escrever o **schema Pydantic** e o fixture
3. Teste unitário primeiro (TDD, `docs/onboarding.md`)
4. Implementar `extrair()` e `transformar()` — só isso; o runner faz o resto
5. DDL Bronze com partição e clustering
6. View Silver com dedup e dimensões comuns
7. View Gold respondendo a uma pergunta de negócio nomeada
8. Teste de idempotência: carregar a mesma janela duas vezes
9. Agendamento no Terraform
10. Dicionário de dados com linhagem origem → Bronze → Silver → Gold
11. `make all` verde, PR, review, merge

Detalhe operacional em `.claude/skills/conector-alupdata`.

---

## 9. Riscos do projeto, priorizados

| # | Risco | Impacto | Mitigação |
|---|---|---|---|
| R1 | VPN/credencial da Onda 3 atrasa | Alto — 155h paradas, ociosidade | Pedir na Onda 0; registrar data de pedido e cobrança |
| R2 | Layout de CCEE/ONS muda ou é mal documentado | Alto — 60h em risco | Validação Pydantic; raw no GCS permite reprocessar sem rebater na fonte |
| R3 | Schema de sistema legado pior que o previsto | Médio-alto | Regime de horas permite realocar; comunicar antes de estourar |
| R4 | Volume do ONS estoura o custo de BigQuery | Médio — custo é da Alup | Particionar sempre; decidir profundidade de histórico antes de carregar |
| R5 | Escopo do Portal MVP cresce | Médio | Cravar o escopo por escrito na Onda 0 |
| R6 | 8 domínios analíticos ficam indefinidos | Médio | Sem eles a Gold não tem alvo; travar na Onda 0 |
| R7 | Fonte entregue com 5 de 7 componentes | Médio | Scaffolding + checklist de homologação |

---

## 10. O que está fora (cláusula 5ª)

Custos de infra GCP · painéis de BI, exceto o Portal MVP da Onda 0 ·
treinamento de usuário final · modelos de IA/ML avançados (Fase 3).

Pedido que caia nesses itens vira proposta de aditivo, não commit.

---

## 11. Sustentação pós-garantia (opcional, cláusulas 9ª e 10ª)

Garantia de 30 dias por onda homologada. Depois disso, franquia de 20h/mês por
R$ 5.120,00/mês cobre monitoramento, correção, patches e ajustes menores em
conectores — **não** cobre pipeline novo, fonte nova, regra de negócio nova ou
relatório de BI.
