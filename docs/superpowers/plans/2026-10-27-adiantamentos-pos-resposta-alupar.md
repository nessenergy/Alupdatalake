# Adiantamentos pós-resposta da Alupar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adiantar o que não depende de terceiros depois da resposta da Alupar de 27/10/2026: janela de um dia na ingestão manual, documentação alinhada à resposta e imagem corrigida em hml.

**Architecture:** Três tarefas independentes. A 1 troca `--de,X,--ate,X` por `--de=X,--ate=X` na lista de `--args` do `gcloud` (o `gcloud` recusa valor repetido; a CLI usa `argparse`, que aceita `--opcao=valor`). A 2 só edita documentos. A 3 dispara o deploy já existente.

**Tech Stack:** Python 3.12, pytest, GitHub Actions (`workflow_dispatch`), `gcloud run jobs execute`.

**Spec:** nenhum documento de design; a origem é a lista de adiantamentos apresentada ao Ricardo em 27/10/2026 e a resposta do Leonardo (27/10).

## Global Constraints

- Regra 6 do AGENTS.md: sem trailer `Co-Authored-By`, sem "Generated with", sem emoji de robô, branches pelo assunto (`fix/`, `docs/`).
- Código em inglês, comentários, docs e commits em português; conventional commits.
- TDD: teste antes do código.
- Nenhum dado real de cliente no repositório.
- Mesclar PR só com todos os checks verdes.

---

### Task 1: Janela de um dia na ingestão manual

**Files:**
- Modify: `scripts/operacoes.py:47-50`
- Modify: `.github/workflows/executar-ingestao.yml:95,98`
- Test: `tests/unit/test_operacoes.py`

**Interfaces:**
- Consumes: `ingestao(conector, de, ate, uri) -> (job, args, descricao)` existente.
- Produces: o mesmo contrato; `args` passa a ter um único item `--args=ingerir,<conector>,--de=<de>,--ate=<ate>` (e `reprocessar-raw` análogo).

- [ ] **Step 1: Write the failing test**

```python
def test_janela_de_um_dia_nao_repete_valor_na_lista_do_gcloud() -> None:
    """O gcloud recusa --args com valores repetidos; de == ate repetia a data."""
    _, args, _ = ingestao("ons_carga", "2026-10-20", "2026-10-20")

    itens = args[0].removeprefix("--args=").split(",")
    assert len(itens) == len(set(itens))
    assert "--de=2026-10-20" in itens
    assert "--ate=2026-10-20" in itens
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/unit/test_operacoes.py -q -k um_dia`
Expected: FAIL.

- [ ] **Step 3: Write minimal implementation**

Em `scripts/operacoes.py`, as duas linhas de `args` viram:

```python
args = [f"--args=reprocessar-raw,{conector},--uri,{uri},--de={de},--ate={ate}"]
...
return job, [f"--args=ingerir,{conector},--de={de},--ate={ate}"], f"{de} a {ate}"
```

No workflow, as duas linhas de `ARGS=(...)` viram `--de=$DE,--ate=$ATE`. Atualizar os testes antigos que comparam a string `--de,X,--ate,Y`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/unit/test_operacoes.py -q`
Expected: PASS.

- [ ] **Step 5: Prova real e commit**

Rodar o workflow `Executar ingestão` em dev com `de == ate` (conector `bcb_cambio_ptax`) e conferir que o job executa. Branch `fix/janela-de-um-dia-na-ingestao-manual`; commit `fix: ingestão manual aceita janela de um dia`.

### Task 2: Documentar a resposta da Alupar de 27/10/2026

**Files:**
- Modify: `docs/status.md`, `docs/proximos-passos.md`, `painel/marcos.toml`, `docs/arquitetura/decisoes/027-*.md` (adendo)

**Interfaces:**
- Consumes: resposta do Leonardo de 27/10/2026 (itens: ONS autenticada, CCEE por SOAP com certificado, MySQL com 7 tabelas, RM/TOTVS sem endpoints, TempoOK e CPTEC com saída confirmada, FMB aguardando a DCIDE).
- Produces: documentos coerentes entre si.

- [ ] **Step 1: Ler os documentos e localizar as afirmações que a resposta contradiz** (`grep -n "IPDO\|ACOMPH\|CCEE credenciada\|RM/TOTVS"`).
- [ ] **Step 2: Editar** cada documento com a nova situação e a data, sem inventar nada além da resposta.
- [ ] **Step 3: Rodar a suíte de testes de documentos** (`uv run pytest tests/unit -q -k "docs or painel or marcos"`) e conferir a regra 6 (`python scripts/verifica_atribuicao.py`).
- [ ] **Step 4: Commit** em `docs/resposta-da-alupar-de-27-10`; mensagem `docs: registra a resposta da Alupar de 27/10`.

### Task 3: Propagar as correções para o hml

**Files:** nenhum.

- [ ] **Step 1:** depois de mesclar as Tarefas 1 e 2, rodar `gh workflow run "Deploy GCP" -f environment=hml -f module=all`.
- [ ] **Step 2:** conferir que a imagem foi publicada e o Terraform aplicado; a falha na asserção do Hubspot é conhecida e não conta.
- [ ] **Step 3:** reexecutar o `ace_prc` em hml e confirmar sucesso.

## Review Focus

- `de == ate` (um dia) no `ingerir` e no `reprocessar-raw`.
- Janela com datas diferentes continua funcionando.
- Documentos não afirmam mais que o IPDO e o ACOMPH dispensam autenticação.
