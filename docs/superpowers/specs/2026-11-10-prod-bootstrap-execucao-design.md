# Bootstrap de produção, execução do plano de 14/10 — especificação

Data: 10/11/2026. Base: [plano de 14/10](../plans/2026-10-14-bootstrap-producao.md), ADR [015](../../arquitetura/decisoes/015-fundacao-do-ambiente.md), [023](../../arquitetura/decisoes/023-regiao-us-central1.md) e [030](../../arquitetura/decisoes/030-cicd-fora-do-github-actions.md).

## 1. Objetivo

Deixar tudo pronto em `infra/` e na documentação para que `prod-alupdata` exista, sem aplicar nada. A aplicação é de quem tem conta nominal na ness.

## 2. Decisões já tomadas (seguidas, não reabertas)

| Tema | Decisão | Origem |
|---|---|---|
| Região | `us-central1`. A ADR 011 (`us-east1`) foi substituída pela 023: a política da organização só admite `us-central1`, `us` e `global`. | ADR 023, plano 30/10 |
| Acesso | Grupos iguais aos de hml, sem `grupo_bronze`; sempre grupo, nunca pessoa. | plano 30/10, R01 |
| Agendamento | Desligado até decisão de ligar. Fontes sem credencial em `conectores_sem_agendamento`. | plano, itens 2.4 e 4 |
| Token do TempoOK | Perdeu o objeto (fora do escopo desde 20/10). | plano 30/10 |
| Rede | A sub-rede compartilhada da ADR 024 é da Alupar; `prod` não cria rede. | ADR 024 |
| CI/CD no Cloud Build | Não liga em `prod` agora (ADR 030: gatilhos só em `dev` até D3). | ADR 030 |

## 3. Mudanças

1. `infra/environments/prod.tfvars`: `agendamentos_ativos = false`.
2. `tests/unit/test_infra.py`: o teste que proibia a variável em `prod` passa a exigir `false`; `dev` segue sem declará-la.
3. `docs/runbook/bootstrap-producao.md`: ordem exata, quem executa, verificação, custo.

Sem mudança em módulos nem no bootstrap: o plano de 30/10 já deixou `infra/bootstrap/environments/prod.tfvars` pronto, e os módulos aceitam `agendar = false`.

## 4. Fora do escopo (perguntas no PR)

Orçamento no Terraform (valor, moeda, papel na conta de faturamento), janela de aceite com fontes públicas ou completa, e acesso de operação da ness. depois do handoff.

## 5. Verificação

`terraform fmt -recursive infra`, `terraform init -backend=false` e `validate` nos três ambientes, `pytest` dos testes de infra e bootstrap, `ruff`. Nada contra a nuvem.
