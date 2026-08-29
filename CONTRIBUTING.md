# Como contribuir

Este repositório entrega a Fase 1 do AlupData sob o contrato CPS-01025/2026.
Antes de escrever código, leia [`AGENTS.md`](AGENTS.md) — as regras que valem
para todo mundo, humano ou agente — e [`docs/status.md`](docs/status.md), para
saber onde o projeto está.

Se você não é do setor elétrico, comece pelo
[glossário](docs/glossario.md): submercado, PLD, CEG e garantia física
aparecem em quase toda view.

## Setup

```bash
uv sync --extra dev      # dependências
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg
# Ruff, Bandit e Gitleaks a cada commit; regra 6 na mensagem do commit
cp .env.example .env      # ajuste os valores locais
make test                 # deve passar do zero
```

Pré-requisitos e versões em [`docs/onboarding.md`](docs/onboarding.md).

## O ciclo de uma mudança

1. Branch a partir de `main`: `feat/`, `fix/`, `docs/` ou `chore/`
2. **Teste antes do código.** Testes unitários não tocam a rede
3. `make all` — lint, testes, Bandit e pip-audit. Verde antes de abrir PR
4. PR para `main` usando o template; CI roda sozinho
5. Review de um code owner; merge após aprovação

Conventional commits, em português: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`.
Código (variáveis, funções) em inglês; comentários e documentação em PT-BR.

## Adicionando uma fonte de dados

```bash
make novo-conector fonte=ons entidade=geracao
```

Gera o esqueleto dos 7 componentes obrigatórios (cláusula 2ª do contrato).
**Uma fonte só está pronta com os 7** — conector, tabela Bronze, view Silver,
view Gold, testes, agendamento e dicionário de dados com linhagem.

O framework em `src/core/` já cuida de janela, raw no GCS, validação, colunas
técnicas, carga no Bronze e log de execução. **Seu conector implementa apenas
`extrair()` e `transformar()`.** Use `src/conectores/bcb_cambio.py` como
referência; o passo a passo está em
[`.claude/skills/conector-alupdata/SKILL.md`](.claude/skills/conector-alupdata/SKILL.md).

## O que trava uma review

| Situação | Por quê |
|---|---|
| Credencial em código, `.env` versionado, fixture ou log | Cláusula 8.5 — só Secret Manager |
| Tabela Bronze sem `PARTITION BY` / `CLUSTER BY` | Custo de BigQuery é da contratante (cláusula 5ª) |
| Conector que decide "hoje" em vez de receber janela | Impede reprocessamento |
| `MERGE`/`UPDATE` no Bronze | Bronze é append-only; dedup é na Silver |
| View Gold que é `SELECT *` da Silver | Não responde pergunta de negócio nenhuma |
| Recurso GCP criado no console | Some no próximo `terraform apply` |
| Dado real de cliente em fixture ou exemplo | Nunca entra no repositório |
| Fonte com 5 dos 7 componentes | Não é entrega parcial, é retrabalho na medição |

## Decisões estruturais

Antes de propor mudança de arquitetura, leia os ADRs em
[`docs/arquitetura/decisoes/`](docs/arquitetura/decisoes/). Discordar é
bem-vindo — mas a forma de discordar é **escrever um ADR novo**, não abrir uma
exceção pontual no código.

Em particular: o framework em `src/core/` é deliberadamente mais estrutura do
que 13 scripts soltos (ADR 003), e a transformação é SQL puro sem dbt, com
Cloud Run Jobs antes do Composer (ADR 004).

## Segurança

Vulnerabilidade encontrada: veja [`SECURITY.md`](SECURITY.md). Não abra issue
pública com detalhe explorável.
