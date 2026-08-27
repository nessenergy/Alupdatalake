# AlupData — contexto para agentes

Arquivo canônico de contexto deste repositório. Vale para qualquer agente
(Claude Code, Codex, Cursor, Gemini, Cline, Copilot); `CLAUDE.md` só aponta
para cá. Se você é humano, `README.md` e `docs/onboarding.md` continuam sendo
o caminho.

## O projeto em cinco linhas

DataLake do Grupo Alupar (6 coligadas geradoras), arquitetura Medallion
(Bronze → Silver → Gold) em BigQuery/GCP. Fase 1 do contrato CPS-01025/2026:
580h em 5 ondas, 19 semanas, 13 conectores de fonte de dados. Executado pela
**ness.** para a Alup. Regime de horas — prioridade pode mudar; o padrão de
entrega não.

Plano detalhado: `docs/plano-execucao.md`. Contrato resumido:
`docs/contrato/resumo-contrato.md`.

## As cinco regras que não se negociam

1. **Toda fonte entrega 7 componentes** (cláusula 2ª): conector Python, tabela
   Bronze, view Silver, view Gold, testes, agendamento, documentação com
   linhagem. Fonte com 5 de 7 não é entrega parcial — é retrabalho na medição.
2. **Credencial só via Secret Manager.** Nunca em código, `.env` versionado,
   fixture, log ou mensagem de erro. Nem "temporariamente".
3. **Ingestão sempre por janela de datas.** Nenhum conector decide "hoje"
   sozinho; reprocessar é passar outra janela.
4. **Bronze é append-only; a deduplicação vive na Silver** (`QUALIFY
   ROW_NUMBER()`). Toda tabela Bronze é particionada e clusterizada — sem isso
   o custo de BigQuery, que é da Alup, cresce por varredura completa.
5. **Recurso GCP que não está em `infra/` não existe.** Nada de console.

## Como escrever um conector

O runner em `src/core/conector.py` já faz: particionar a janela, gravar o raw
no GCS antes do parsing, validar por Pydantic, acrescentar colunas técnicas,
carregar no Bronze e registrar a execução. **Um conector novo implementa apenas
`extrair()` e `transformar()`.**

```bash
make novo-conector fonte=ons entidade=carga   # esqueleto dos 7 componentes
```

Referência viva: `src/conectores/bcb_cambio.py`.

## Comandos

```bash
make all              # lint + testes + Bandit + pip-audit — rode antes de todo PR
make test             # pytest
make lint             # ruff check + format --check
make novo-conector fonte=X entidade=Y
make deploy-views     # aplica o SQL de sql/ no BigQuery (idempotente)
make sync-skills      # atualiza as skills vendorizadas do Google

alupdata listar
alupdata ingerir bcb_cambio_ptax --de 2026-01-01 --ate 2026-01-31 --dry-run
```

## Mapa do repositório

| Caminho | O quê |
|---|---|
| `src/core/` | framework de ingestão — runner, janela, registry, GCS, BigQuery, secrets, HTTP |
| `src/conectores/` | um módulo por fonte |
| `src/cli.py` | CLI única: laptop, Cloud Run Job e DAG usam o mesmo comando |
| `sql/{bronze,silver,gold}/` | DDL e views versionadas, aplicadas por `make deploy-views` |
| `infra/` | Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM |
| `dags/` | vazio até a Onda 3 (ADR 004) |
| `docs/arquitetura/decisoes/` | ADRs — leia antes de propor mudança estrutural |
| `docs/dicionario-dados/` | componente 07 de cada fonte |
| `docs/runbook/` | deploy e operação |
| `scripts/` | deploy de views, scaffolding, sync de skills |

## Vocabulário do setor

Termos como submercado, PLD, CEG, MWmed e garantia física aparecem em quase
toda view. Se algum não for familiar, [`docs/glossario.md`](docs/glossario.md)
define todos em uma página.

## Convenções

- Código (variáveis, funções) em **inglês**; comentários, docs e commits em
  **português**. Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`.
- Branches `feat/`, `fix/`, `docs/`, `chore/`; PR para `main`.
- TDD: teste antes do código.
- Nomes de objeto e coluna em `snake_case`, sem acento. Colunas técnicas com
  prefixo `_`.
- Nada de dado real de cliente no repositório — nem em fixture, nem em exemplo.

## Skills (funcionam em qualquer agente)

São arquivos Markdown com frontmatter, sem dependência de runtime. O Claude Code
carrega automaticamente de `.claude/skills/`; **qualquer outro agente pode
simplesmente ler o arquivo** indicado abaixo quando o assunto aparecer.

| Assunto | Arquivo |
|---|---|
| Adicionar/alterar uma fonte de dados | `.claude/skills/conector-alupdata/SKILL.md` |
| BigQuery, GCS, Secret Manager, Terraform, IAM | `.claude/skills/gcp-alupdata/SKILL.md` |
| Credenciais, dependências, Bandit/pip-audit/Gitleaks | `.claude/skills/ssdlc-alupdata/SKILL.md` |
| Fechar uma onda, medição, dependência da Alup | `.claude/skills/homologacao-onda/SKILL.md` |
| Mecânica dos produtos Google (BigQuery, GCS, Cloud Run, gcloud) | `.claude/skills/google/*/SKILL.md` |

**Precedência**: as skills do projeto (`*-alupdata`, `homologacao-onda`) vencem
as do Google onde houver conflito. As do Google ensinam o produto; as do projeto
dizem como *este contrato* usa o produto.

## Onde as decisões estão registradas

| ADR | Decisão |
|---|---|
| 001 | Stack Python + Terraform |
| 002 | Monorepo |
| 003 | Framework de conectores com runner único; janela; append-only; GCS antes do BigQuery |
| 004 | SQL versionado sem dbt; Cloud Run Jobs + Scheduler antes de Composer |
| 005 | Escopo do Portal MVP cravado — o que ele é e o que não é |
| 006 | Painel de saúde `/lake`: monitoramento não é BI |
| 007 | *(proposta)* painel de saúde como entrega faturável — revê a 006 |

Se você for propor algo que contraria um ADR, escreva um ADR novo — não um
remendo. Em particular: o framework em `src/core/` é mais estrutura do que 13
scripts soltos **de propósito** (ADR 003, 13 fontes / 19 semanas / handoff).

## Estado atual (2026-08-25)

> Quadro completo, com pendências e dono de cada uma, em
> [`docs/status.md`](docs/status.md).

Concluído: framework, CLI, **quatro conectores completos** — BCB/PTAX (diário),
IBGE/IPCA (mensal, aninhado), ANEEL/SIGA (cadastro paginado, ~25 mil registros)
e ONS/carga (CSV anual por subsistema) —, Terraform, CI/CD, scaffolding,
ADRs 003–004, runbook de deploy e plano de execução.

As dimensões comuns já têm dono: `codigo_usina` vem do ANEEL/SIGA e
`submercado` vem do ONS.

Bloqueado por insumo da Alup: 8 domínios analíticos, RACI, ambiente GCP real,
todas as fontes das Ondas 2 e 3 (token, VPN, credencial read-only) e a **CCEE
InfoMercado**, cujo portal responde 403 a acesso automatizado — ver
`docs/plano-execucao.md` §3.1.

Próximo passo técnico: com a Onda 1 fechada no que não depende de terceiros, o
trabalho útil é preparar o contrato de dados das fontes das Ondas 2 e 3 (schema
Pydantic + fixture a partir da documentação, teste de integração com `skipif`),
para que a chegada do token seja "ligar e ajustar", não "começar".
