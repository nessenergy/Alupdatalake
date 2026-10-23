# Débitos que se resolvem sem terceiros — plano de execução

> **Para agentes:** executar tarefa a tarefa, na ordem, com TDD. Os passos usam caixas `- [ ]`.

**Meta:** fechar os cinco débitos da especificação, em dois PRs.

**Arquitetura:** tudo é código de repositório e documentação. Nenhum recurso de nuvem nasce, e nenhum IAM muda. A conferência de cargas continua somente leitura.

**Spec:** [`../specs/2026-10-23-debitos-resolvidos-ja-design.md`](../specs/2026-10-23-debitos-resolvidos-ja-design.md)

## Restrições globais

- Regra 6: nenhuma atribuição a ferramenta de IA em commit, PR, issue ou documento (validar com `python scripts/verifica_atribuicao.py`).
- Nada de dado real de cliente no repositório nem no resumo da conferência: só `negocio_id`, nunca valor, nome ou e-mail.
- Commit por nome de arquivo (nunca `git add -A`). Docs e comentários em português; commits convencionais; PR para `main`; mesclar só com todos os checks verdes.

## PR 1 — `fix/debitos-conferencia-hubspot-e-api-core`

### Tarefa 1: diagnóstico do Hubspot na conferência

**Arquivos:** alterar `scripts/conferir_cargas.py` e `tests/unit/test_conferir_cargas.py`.

- [x] **Passo 1: teste que falha.** Em `tests/unit/test_conferir_cargas.py`:

```python
def test_conferencia_mostra_os_negocios_do_hubspot_fora_da_regra_sem_vazar_valor():
    itens = {item.rotulo: item.sql for _, lista in conjuntos() for item in lista}

    contagem = itens["hubspot_negocios_fora_da_regra"]
    assert "valor < 0" in contagem
    assert "data_fechamento < DATE(criado_em)" in contagem

    lista = itens["hubspot_negocios_reprovados"]
    assert "negocio_id" in lista and "LIMIT 50" in lista
    colunas_escolhidas = lista.split(" FROM ")[0]
    for dado_do_cliente in ("valor,", "nome", "email", "proprietario"):
        assert dado_do_cliente not in colunas_escolhidas
```

- [x] **Passo 2:** `uv run pytest tests/unit/test_conferir_cargas.py -q`. Esperado: FALHA com `KeyError` (itens ainda não existem).
- [x] **Passo 3: implementação.** Em `montar_conjuntos`, acrescentar a `silver_itens`:

```python
    silver_itens.append(
        Item(
            "hubspot_negocios_fora_da_regra",
            _sql(
                "SELECT COUNT(*) AS negocios, COUNTIF(valor < 0) AS valor_negativo, "
                "COUNTIF(data_fechamento IS NOT NULL AND data_fechamento < DATE(criado_em)) "
                "AS fechamento_antes_da_criacao FROM $t",
                t=tabela(silver, "hubspot_negocios"),
            ),
        )
    )
    silver_itens.append(
        Item(
            "hubspot_negocios_reprovados",
            _sql(
                "SELECT negocio_id, IF(valor < 0, 'valor_negativo', 'fechamento_antes_da_criacao') AS regra "
                "FROM $t WHERE valor < 0 OR (data_fechamento IS NOT NULL AND data_fechamento < DATE(criado_em)) "
                "ORDER BY regra, negocio_id LIMIT 50",
                t=tabela(silver, "hubspot_negocios"),
            ),
        )
    )
```

- [x] **Passo 4:** o teste do passo 1 passa, e `test_toda_consulta_e_leitura` continua passando (as consultas só têm `SELECT`).
- [x] **Passo 5:** commit `feat: a conferência mostra os negócios do Hubspot que violam a regra de qualidade`.

### Tarefa 2: `google-api-core` estável

**Arquivos:** alterar `uv.lock`.

- [x] **Passo 1:** `uv lock --upgrade-package google-api-core` (2.35.0 para 2.43.0).
- [x] **Passo 2:** `uv sync --frozen --extra dev --extra bancos`, depois `uv run pytest tests -q`. Esperado: tudo passa.
- [x] **Passo 3:** `make ci-sca` equivalente: `uv export --no-emit-project --no-hashes --extra dev -o .requirements.txt -q` e `uv run pip-audit --strict --desc --no-deps --disable-pip -r .requirements.txt`. Esperado: sem vulnerabilidade.
- [x] **Passo 3b (achado na execução):** o `pip-audit` reprovou `filelock` 3.32.4 (CVE-2026-112940, correção na 4.2.1), advisório novo que já estava no lock da `main` e reprovaria o SCA em qualquer PR. `uv lock --upgrade-package filelock` (3.32.4 para 4.2.4); o `pip-audit` passa e a suíte também.
- [x] **Passo 4:** commit `chore: google-api-core 2.43.0 e filelock 4.2.4`.
- [x] **Passo 5:** PR, checks verdes, mesclar. Depois, disparar `Conferir cargas` em dev e hml e ler os dois itens novos.

## PR 2 — `docs/debitos-t5-t6-e-deploy`

### Tarefa 3: T6, a conferência cobre toda Silver ou declara a exceção

**Arquivos:** alterar `tests/unit/test_conferir_cargas.py`.

- [x] **Passo 1: teste que falha.**

```python
RAIZ = Path(__file__).resolve().parents[2]


def test_toda_silver_esta_na_conferencia_ou_na_lista_de_excecoes() -> None:
    """Fonte nova sem entrada na conferência passaria despercebida; a exceção tem de ser escrita."""
    silvers = {p.stem for p in (RAIZ / "definitions" / "silver").glob("*.sqlx")}
    assert silvers - set(SILVER) - EXCECOES_DA_CONFERENCIA == set()
    assert not EXCECOES_DA_CONFERENCIA & set(SILVER), "fonte na lista e na exceção ao mesmo tempo"
    assert EXCECOES_DA_CONFERENCIA <= silvers, "exceção de Silver que não existe mais"
```

- [x] **Passo 2:** rodar. Esperado: FALHA listando as 45 Silvers fora da conferência.
- [x] **Passo 3:** criar `EXCECOES_DA_CONFERENCIA` (`frozenset`) no arquivo de teste, com as 45, e o comentário: "acompanhadas pela `gold.saude_ingestao` (frescor e erro por fonte); não entram na conferência por contagem de linhas".
- [x] **Passo 4:** o teste passa. Commit `test: a conferência cobre toda Silver ou declara a exceção`.

### Tarefa 4: T5, motivo dos testes ignorados

**Arquivos:** criar `docs/qualidade/testes-ignorados.md`.

- [x] **Passo 1:** `uv run pytest tests -q -rs`, e agrupar as linhas `SKIPPED [n] arquivo:linha: motivo` por motivo.
- [x] **Passo 2:** escrever a tabela motivo, quantidade e exemplo no documento novo, com a data da medição e o comando que a reproduz.
- [x] **Passo 3:** motivo "falta credencial ou ambiente da Alupar" (esperado) só se documenta. Motivo diferente (por exemplo "não implementado"): abrir uma issue por grupo com o nome do arquivo e o motivo, sem corrigir.
- [x] **Passo 4:** commit `docs: motivo dos testes ignorados`.

### Tarefa 5: `deploy.md` com o CI e CD novos

**Arquivos:** alterar `docs/runbook/deploy.md`.

- [x] **Passo 1:** acrescentar a seção "Deploy e operações no Cloud Build" com: o gatilho `alupdata-deploy` e suas substituições (`_AMBIENTE`, `_MODULO`, `_IMAGEM_SHA` e as calculadas pelo Terraform), os quatro gatilhos de operação (já descritos em outros runbooks; só apontar), os agendados (desligados por padrão, com a flag de cada um) e como ligar a atribuição (`github_app_ci_client_id`) e o painel.
- [x] **Passo 2:** conferir os nomes contra `infra/modules/cicd/main.tf` (nada inventado).
- [x] **Passo 3:** commit `docs: deploy.md descreve o CI e o CD no Cloud Build`; PR, checks verdes, mesclar.

## Pronto quando

Os dois PRs mesclados, `Conferir cargas` mostrando os negócios do Hubspot em dev e hml, e a lista (só ids) pronta para ir à Alupar.

## Resultado da execução (23/10/2026)

- **Hubspot:** em dev e hml, dos 209 negócios, 0 têm valor negativo e **1** tem fechamento anterior à criação (`negocio_id` 64929016742). É ele que reprova a asserção e deixa o Dataform vermelho.
- **T6:** 59 Silvers, 14 na conferência, 45 como exceção declarada.
- **T5:** 558 ignorados, 11 motivos, nenhum "não implementado" ou "lento"; 96% são regras SQL que não se aplicam à camada testada. Nenhuma issue a abrir.
- **Dependências:** `google-api-core` 2.43.0 e `filelock` 4.2.4 (o `pip-audit` reprovava a 3.32.4).
