# MySQL Alup (Onda 3): plano de execução

**Spec:** [`2026-11-10-mysql-alup-onda3-design.md`](../specs/2026-11-10-mysql-alup-onda3-design.md). Branch `feat/mysql-alup-onda3`, PR para `main`. TDD: o teste de cada tarefa vem antes do código. Commits convencionais em português, sem atribuição de ferramenta (regra 6), validados com `scripts/verifica_atribuicao.py`.

Cada tabela entrega os 7 componentes: conector, Bronze, Silver, Gold, testes, agendamento, dicionário com linhagem.

- [ ] **T1. Base `mysql_alup`.** Teste: `SELECT` montado só com constantes, janela por parâmetro `[inicio, fim+1)`, retrato ignora a janela e carimba `data_referencia = janela.fim`, DSN lida de `portal-alup`, erro sem a DSN. Código: `src/conectores/mysql_alup.py` (base `MysqlAlupConector`).
- [ ] **T2. `portal_alup_client`.** Modelo, Bronze, Silver, teste de transformação com fixture sintética, dicionário.
- [ ] **T3. `portal_alup_uc`.** Idem; sem `address` nem `vendedor` no `SELECT` (teste confere). Gold `cadastro_uc_cliente`.
- [ ] **T4. `portal_alup_bandeira`.** Idem; `mes` lido como texto, `valor` como `Decimal`.
- [ ] **T5. `portal_alup_invoice`.** Janela por `COALESCE(updated_at, created_at)`; sem `nfe`, `jsonInfo`, `barcode`, `s3_key*` (teste confere). Silver ordena por `atualizado_em`. Gold `fatura_mensal_cliente`.
- [ ] **T6. `portal_alup_faturas_processadas`.** Janela por `COALESCE(updatedAt, createdAt)`; `parcelas` como texto. Gold `faturamento_mensal_contrato`.
- [ ] **T7. Agendamento.** `infra/modules/scheduler`, limites de silêncio (`monitoramento` e `includes/silencio.js`), `conectores_rede_interna` em `dev.tfvars`, domínio em `src/portal/custo.py`.
- [ ] **T8. Integração.** `tests/integration/test_portal_alup.py`, pulado sem `ALUPDATA_INTEGRACAO_PORTAL_ALUP`.
- [ ] **T9. Fecho.** `make all`, `dataform-compile`, `conferir_componentes`; rebase na `main`; PR.

Fora do plano (spec, "Escopo"): as duas tabelas de medição, até a Alupar informar a data da renomeação.
