# Bootstrap de produção, execução — plano

**Spec:** [2026-11-10-prod-bootstrap-execucao-design.md](../specs/2026-11-10-prod-bootstrap-execucao-design.md)

- [x] Teste primeiro: `test_hml_nasce_sem_agendamento` exige `agendamentos_ativos = false` em `prod`.
- [x] `infra/environments/prod.tfvars`: `agendamentos_ativos = false`, comentário atualizado.
- [x] `docs/runbook/bootstrap-producao.md`.
- [x] `terraform fmt`, `init -backend=false`, `validate` em dev, hml e prod; `pytest` de infra; `ruff`.
- [x] Commit sem atribuição, validado por `scripts/verifica_atribuicao.py`; PR para `main`, sem merge.
