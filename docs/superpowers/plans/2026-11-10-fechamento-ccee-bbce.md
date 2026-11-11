# Plano — fechamento da CCEE e do BBCE

Spec: [`2026-11-10-fechamento-ccee-bbce-design.md`](../specs/2026-11-10-fechamento-ccee-bbce-design.md). TDD: teste antes do código.

1. `fix/ccee-cadastro-sem-permissao` (D1)
   - Testes: `CceeError.codigo`; `Execucao.status == SEM_PERMISSAO`; runner devolve a execução sem levantar; CLI sai 0; conector
     do cadastro converte `4001`, mas não outro código.
   - Código: `execucao.py`, `conector.py` (`SemPermissaoNaOrigem`), `ccee_pi_sessao.py`, `ccee_pi_ponto_medicao.py`, `cli.py`,
     `saude_ingestao.sqlx`, descrição de `_execucoes.status`.
   - Docs: dicionário do cadastro.
2. `docs/dicionario-ccee-medida` (D2): dicionário da medição.
3. `fix/bbce-silver-gold` (D3): conferir e corrigir o que faltar; registrar no PR o que depende do ambiente.
4. `make all` (pytest e ruff) antes de cada commit; mensagem validada com `scripts/verifica_atribuicao.py`; PR sem merge.
