# Estado do projeto

Atualizado em **2026-08-26** · `main` em `55cb686`

Este arquivo responde "onde estamos e o que trava o próximo passo". Detalhe de
escopo e estimativa fica em [`plano-execucao.md`](plano-execucao.md); contexto
para agentes, em [`../AGENTS.md`](../AGENTS.md).

---

## 1. Entregue e verificado

### Framework e ferramental

| Item | Onde | Verificação |
|---|---|---|
| Runner de ingestão (janela, raw no GCS, validação, colunas técnicas, carga, log) | `src/core/` | 117 testes, 91% de cobertura |
| CLI única (`alupdata listar` / `ingerir`) | `src/cli.py` | executada contra as 4 fontes |
| Scaffolding dos 7 componentes | `make novo-conector` | usado nas fontes novas |
| Deploy de views idempotente | `make deploy-views` | `--dry-run` conferido |
| Motor S2 Data Intake (planilha CSV/XLSX sob template) | `src/core/planilha.py`, `src/conectores/planilha.py` | 19 testes; templates concretos dependem de A4 |
| Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM | `infra/` | `fmt` e `validate` limpos |
| CI/CD: lint, testes, Bandit, pip-audit, Gitleaks, Terraform | `.github/workflows/` | verde |
| Imagem da CLI | `Dockerfile` | build não executado (sem Artifact Registry ainda) |

### Conectores (7 componentes cada, exceto onde indicado)

| Fonte | Formato | Volume verificado | Agendamento |
|---|---|---|---|
| **BCB/PTAX** | JSON diário | 3 registros / 3 dias | diário 9h, janela 3 dias |
| **IBGE/IPCA** | JSON aninhado, mensal | 12 registros / 6 meses | dia 12, janela 90 dias |
| **ANEEL/SIGA** | cadastro paginado | **25.263 registros**, 0 inválidos, 28s | semanal, segunda 7h |
| **ONS/carga** | CSV anual remoto | 28 registros / 7 dias | diário 8h, janela 30 dias |
| **Hubspot/negócios** | JSON paginado, CRM | **não executado** — sem token (A9) | a cada 6h, janela 2 dias |

As quatro primeiras foram verificadas **em dry-run contra as APIs reais**. O
Hubspot é a exceção: os 7 componentes existem, mas foram escritos contra a
documentação pública e **nunca falaram com a API** — o teste de integração está
`skipif` até o token chegar. Nenhuma linha chegou a um
BigQuery de verdade — o projeto GCP ainda não existe.

### Dimensões comuns

| Dimensão | Fonte | Situação |
|---|---|---|
| `data_referencia` | todas | ok |
| `periodo_apuracao` | todas | ok |
| `codigo_usina` | ANEEL/SIGA (CodCEG) | ok |
| `submercado` | ONS (N, NE, S, SE) | ok |
| `agente_ccee` | CCEE | **sem fonte** — depende do desbloqueio da CCEE |

### Documentação

ADRs 001–004 · 4 dicionários de dados · plano de execução · runbook de deploy ·
`AGENTS.md` como contexto canônico · skills do projeto e shortlist do Google.

---

## 2. Aberto — ação da ness.

| # | Item | Bloqueado por |
|---|---|---|
| N1 | Preparar contrato de dados das fontes das Ondas 2 e 3 | **inviável para 3 das 4 fontes** — ver §6 |
| N2 | Portal MVP: ligar contra o BigQuery e publicar no Cloud Run | escopo cravado na ADR 005; a tela existe e roda com provedor simulado — falta o ambiente GCP (A3) |
| N3 | Primeiro `terraform apply` real e primeiro deploy da imagem | ambiente GCP (A3) |

---

## 3. Aberto — ação da Alup

| # | Item | Efeito enquanto não vier | Referência |
|---|---|---|---|
| A1 | **Configurar Workload Identity Federation** (`GCP_WIF_PROVIDER`, `GCP_DEPLOY_SA`) | o workflow de deploy falha na autenticação | `runbook/deploy.md` |
| A2 | **Decidir sobre a CCEE InfoMercado** — portal responde 403 a acesso automatizado | 32h da Onda 1 paradas; `agente_ccee` sem fonte | [issue #52](https://github.com/nessenergy/Alupdatalake/issues/52), plano §3.1 |
| A3 | **Projeto GCP `dev`**: criar, habilitar APIs, IAM, Artifact Registry, bucket de state | nada sobe; Onda 0 não homologa | plano 2.2 (0.13) |
| A4 | **Questionário de Gaps** (47 perguntas) | os 8 domínios analíticos não se definem; a Gold fica sem alvo | plano 2.2 (0.9) |
| A5 | **RACI e data owners** por domínio | sem dono, dúvida de regra de negócio não tem para quem ir | plano 2.2 (0.12) |
| A6 | **Ferramenta de BI** definida | o Portal MVP e as views Gold ficam sem consumidor definido | contrato, cláusula 3ª |
| A7 | Abrir **já** os pedidos de token (Onda 2) e VPN/credencial (Onda 3) | é o maior risco do contrato: atraso dispara ociosidade de 4h/dia | plano §7 |
| A8 | **Documentação técnica de BBCE e TempoOK** (a Alup é contratante desses serviços) | sem ela não dá nem para preparar o contrato de dados antes do token — ver §5 | §5 |
| A9 | **Token do Hubspot** (private app) no secret `alupdata-hubspot-api-token` | o conector está pronto e parado; nenhuma linha de CRM entra no lake | plano 2.3 (2.3) |

> **Cláusula 3ª**: atraso > 5 dias úteis posterga o cronograma; > 5 dias úteis em
> VPN/credencial gera taxa de ociosidade de 4h/dia (R$ 256/h); > 20 dias
> corridos suspende os serviços. Registrar a data de cada pedido **no dia em que
> o atraso começa**, não quando vira problema.

---

## 4. Onde estamos no contrato

| Onda | Escopo | Situação |
|---|---|---|
| 0 — Fundação | 90h · marco 15,52% | Técnico concluído; **falta o que depende da Alup** (A3–A6) para homologar |
| 1 — Mercado base | 120h · marco 20,69% | **4 de 5 fontes concluídas**; CCEE bloqueada (A2) |
| 2 — APIs credenciadas | 110h · marco 18,97% | Não iniciada; bloqueada por token (A7) |
| 3 — Sistemas internos | 155h · marco 26,72% | Não iniciada; bloqueada por VPN (A7) |
| 4 — Planilhas e handoff | 105h · marco 18,10% | Não iniciada |

---

## 5. Preparar as fontes bloqueadas: o que a sondagem mostrou

O plano previa escrever schema e fixture das fontes das Ondas 2 e 3 a partir da
documentação pública, para que a chegada do token fosse "ligar e ajustar". A
sondagem de 2026-08-25 mostra que isso **só se sustenta para uma delas**:

| Fonte | Documentação/API alcançável? | Dá para escrever o contrato hoje? |
|---|---|---|
| CCEE InfoMercado | **não** — 403 em tudo, inclusive na página de documentação | não |
| BBCE | **não** — nenhum endpoint público encontrado | não |
| TempoOK | site público, mas **sem contrato de API discoverable** | não |
| Hubspot | sim — API e docs públicas | **feito** em 2026-08-26 — ver abaixo |

O Hubspot foi entregue nesse regime em 2026-08-26: conector, Bronze, Silver,
Gold, testes (unitário sem rede + integração `skipif`), agendamento e
dicionário. Quando o token de A9 chegar, a tarefa é rodar e conferir, não
começar. O que **não** foi possível verificar sem credencial está listado no
fim de `dicionario-dados/hubspot_negocios.md`.

Escrever schema por adivinhação seria pior que não escrever: cria retrabalho
com aparência de progresso. **O que destrava**: a Alup fornecer a documentação
técnica de BBCE e TempoOK (que ela tem, como contratante desses serviços) —
isso vale tanto quanto o token, e pode vir antes dele.

## 5.1 Ressalva importante

Tudo foi validado **localmente e em dry-run**. O primeiro `terraform apply` e a
primeira carga real são onde aparecem os erros que teste local não pega: IAM
insuficiente, cota de API, permissão de bucket, formato que o BigQuery recusa.
**A Onda 0 não deve ser declarada homologada antes disso rodar** — o critério
está na skill `homologacao-onda`.
