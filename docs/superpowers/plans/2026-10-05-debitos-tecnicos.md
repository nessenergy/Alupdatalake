# Débitos técnicos da Onda 1 — Plano de Implementação e matriz RACI

> **Para agentes de execução:** use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans. Os passos usam checkbox (`- [ ]`).

**Goal:** tirar os débitos técnicos que escondem falha real ou geram ruído (causa de falha ilegível, "origem fora do ar" confundida com erro nosso, 672 linhas inválidas do INMET sem explicação, testes ignorados sem motivo registrado, listas de conferência sem rede de segurança) e dizer quem decide, quem faz e quem é avisado em cada passo.

**Architecture:** a coluna `erro` já existe em `bronze._execucoes` (`src/core/execucao.py`) e a conta de deploy lê o BigQuery (é como o workflow `Conferir cargas` funciona). Então a causa de uma falha passa a ser mostrada **pela conferência**, sem dar leitura de logs à conta de deploy e sem mudança de IAM. Todo o resto é teste, conector e documentação.

**Tech Stack:** Python 3.13, pytest, BigQuery, GitHub Actions (`Conferir cargas`), Dataform.

**Spec:** achados da sessão de 05/10/2026: (a) a última execução de `aneel_tarifas` em dev, em 05/10, terminou em `ERRO` com 0 linhas e a causa é desconhecida; (b) `bcb_igpm` e `bcb_juros` tiveram 12 e 9 erros em 3 dias por queda do BCB; (c) `inmet_precipitacao` marca 672 linhas inválidas em toda execução; (d) 554 de 2.538 testes estão ignorados; (e) listas fixas em `scripts/conferir_cargas.py`.

## Global Constraints

- **Regra 6:** nenhuma atribuição de ferramenta de IA em commit, PR, issue, comentário ou documento; validar a mensagem com `python scripts/verifica_atribuicao.py`. Este plano e a matriz RACI nomeiam **papéis**, não ferramentas.
- Nenhum recurso GCP fora de `infra/`; credencial só via Secret Manager; sem mudança de IAM neste plano.
- Ingestão por janela de datas; Bronze append-only; Silver deduplica; falha de layout falha alto; hora ou dia sem medição é nulo, nunca zero.
- O resumo do GitHub nunca recebe segredo: todo texto de erro passa por `sanitizar` (já usado em `scripts/conferir_cargas.py`) e é truncado.
- Os dois mapas de silêncio (`includes/silencio.js` e `infra/modules/monitoramento/main.tf`) continuam iguais.
- Testes não dependem de CRLF/LF: use `splitlines()`.
- Adicionar arquivos por nome (nunca `git add -A`). Docs e comentários em português; commits convencionais; branches `feat/`, `fix/`, `docs/`, `chore/`; PR para `main`; mesclar só com CI verde.
- Decisão comercial (estado "entregue" da Onda 1 no painel, aceite da Alup, prazos, multa) **não** é tomada por este plano: fica registrada na matriz como decisão do decisor.

## Matriz RACI

R = executa · A = responde pelo resultado e decide (um só por linha) · C = consultado antes · I = informado depois.

**Papéis**
- **Decisor ness.**: Ricardo Esper (CEO).
- **Execução técnica ness.**: quem implementa, testa e abre os PRs.
- **Equipe ness.**: pessoas da ness. em cópia do fio com a Alup.
- **Alup, comercialização**: Eduardo Pires, aprovador contratual.
- **Alup, nuvem e faturamento**: quem administra os projetos e a conta de faturamento da Alup (permissões que a ness. não tem).
- **Origem externa**: BCB, INPE/CPTEC, INMET (só consultadas, nunca responsáveis).

| # | Entrega ou decisão | Decisor ness. | Execução técnica ness. | Equipe ness. | Alup, comercialização | Alup, nuvem e faturamento | Origem externa |
|---|---|---|---|---|---|---|---|
| T1 | Mostrar a causa do erro na conferência e diagnosticar o `aneel_tarifas` | I | A/R | I | | | |
| T2 | Corrigir a causa do `aneel_tarifas` | A | R | I | I | | |
| T3 | Separar "origem fora do ar" de erro nosso | A | R | C | | | |
| T4 | Explicar as 672 linhas inválidas do INMET | I | A/R | | | | C (INMET) |
| T5 | Registrar o motivo dos 554 testes ignorados | I | A/R | C | | | |
| T6 | Rede de segurança das listas da conferência e runbook da sonda | I | A/R | I | | | |
| T7 | Fechamento: relatório e status | A | R | I | | | |
| D1 | Corte de distância da bacia mais próxima | A | C | | C | | |
| D2 | Aceitar ou trocar a regra da média por bacia (ADR 026) | I | C | | A | | |
| D3 | Decisão sobre IPDO e ACOMPH (ADR 027) | I | C | | A | | |
| D4 | Resposta do INPE sobre o 403 do CPTEC (ADR 028 e 029) | A | C | I | C | | C (INPE) |
| D5 | Estado "entregue" da Onda 1 no painel | A | C | | I | | |
| D6 | Alerta de orçamento do Terraform (R$ 500 contra a referência de US$ 20/400) | A | R | I | C | C (permissão na conta de faturamento) | |

Regras de uso da matriz: (1) quem é A não delega a decisão, só a execução; (2) nada de linha D entra em código antes de o A decidir; (3) toda linha D registra a decisão e a data no relatório de fechamento (T7); (4) T2 só começa depois do diagnóstico de T1.

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `scripts/conferir_cargas.py` | mostra `erro` da última execução e das execuções com erro dos últimos 3 dias |
| `tests/unit/test_conferir_cargas.py` | testes da conferência, incluindo a rede de segurança das listas |
| `src/core/conector.py` | marca erro de origem indisponível (T3) |
| `tests/unit/test_conector_runner.py` (ou o arquivo de testes do runner que já existe) | teste do marcador (T3) |
| `docs/qualidade/testes-ignorados.md` (novo) | motivo dos testes ignorados (T5) |
| `docs/runbook/deploy.md` | seção da sonda (T6) |
| `docs/relatorios/2026-10-03-fechamento-onda-1.md`, `docs/status.md` | fechamento (T7) |

---

### Tarefa 1: Mostrar a causa do erro na conferência e diagnosticar o `aneel_tarifas`

**Files:**
- Modify: `scripts/conferir_cargas.py` (itens `ultima_execucao` e `erros_3_dias`)
- Test: `tests/unit/test_conferir_cargas.py`

**Interfaces:**
- Consumes: coluna `erro` (STRING, anulável) de `bronze._execucoes`; `sanitizar(texto, limite=200)` já importado em `scripts/conferir_cargas.py`.
- Produces: item novo `ultimo_erro` na seção "Última execução por conector": `conector`, `data_execucao`, `erro` (até 200 caracteres, sanitizado), uma linha por conector cuja última execução com erro caiu nos últimos 3 dias.

- [ ] **Passo 1: teste que falha.** Em `tests/unit/test_conferir_cargas.py`, junto aos testes das consultas:

```python
def test_conferencia_mostra_o_erro_da_ultima_execucao_com_falha() -> None:
    """A conta de deploy não lê o Cloud Logging, mas lê `_execucoes.erro`: a causa de uma falha tem de aparecer aqui."""
    consultas = {item.rotulo: item.sql for _, itens in montar_conjuntos("proj", "bronze", "silver", "gold") for item in itens}
    sql = consultas["ultimo_erro"]
    assert sql.lstrip().upper().startswith("SELECT")
    assert "erro IS NOT NULL" in sql
    assert "INTERVAL 3 DAY" in sql
    assert "`proj.bronze._execucoes`" in sql
    validar_sql(sql)
```

Ajuste `montar_conjuntos` ao nome real da função que monta os conjuntos (leia `scripts/conferir_cargas.py` acima de `silver_itens = [`; o teste existente `test_toda_consulta_...` mostra como ela é chamada e reaproveite a mesma chamada).

- [ ] **Passo 2:** `uv run pytest tests/unit/test_conferir_cargas.py -q -k ultima_execucao_com_falha` → FAIL (`KeyError: 'ultimo_erro'`).

- [ ] **Passo 3: implementar.** Em `execucao_itens`, depois do item `erros_3_dias`:

```python
        Item(
            "ultimo_erro",
            _sql(
                "SELECT CONCAT(fonte, '_', entidade) AS conector, DATE(encerrada_em) AS data_execucao, "
                "SUBSTR(erro, 1, 200) AS erro "
                "FROM $e WHERE CONCAT(fonte, '_', entidade) IN ($c) AND erro IS NOT NULL "
                "AND encerrada_em >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 3 DAY) "
                "QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY encerrada_em DESC) = 1 "
                "ORDER BY conector",
                e=execucoes,
                c=conectores,
            ),
        ),
```

No ponto em que `rodar` monta a linha de resultado, a coluna `erro` já passa pelo mesmo `sanitizar` das mensagens de falha; confirme lendo a função e, se o valor das células não passa por `sanitizar`, aplique-o às células de texto desta seção.

- [ ] **Passo 4:** `uv run pytest tests -q` e `uv run ruff check src tests scripts` → PASS.
- [ ] **Passo 5: commit** `feat: conferência de cargas mostra a causa do último erro por conector`; PR; CI verde; mesclar.
- [ ] **Passo 6: diagnóstico (execução, não código).** `gh workflow run "Conferir cargas" -f environment=dev`, ler a linha `ultimo_erro` do `aneel_tarifas` e escrever o achado (causa, data, ambiente) em uma nota curta no PR de T7. **Regra de decisão:** (a) erro de origem (ANEEL fora do ar, 5xx, timeout): vira T3, sem correção de código; (b) erro de layout (coluna nova, formato): T2 com teste a partir do arquivo real; (c) erro de memória ou tempo do job: T2 aumenta o recurso em `infra/modules/` com validação; (d) erro não reproduzível: reexecutar uma vez com `Executar ingestão` e registrar o resultado.

### Tarefa 2: Corrigir a causa do `aneel_tarifas` (só depois do diagnóstico de T1)

**Files:** definidos pelo diagnóstico de T1, nunca antes. Teste primeiro, a partir da amostra real do erro.

- [ ] **Passo 1:** escrever o teste que reproduz a causa (fixture mínima em `tests/fixtures/`, sem dado de cliente).
- [ ] **Passo 2:** `uv run pytest <teste> -q` → FAIL com a mensagem do erro real.
- [ ] **Passo 3:** a correção mínima; `uv run pytest tests -q`; ruff.
- [ ] **Passo 4:** commit `fix(aneel): <causa em uma frase>`; PR; mesclar com CI verde; deploy do ambiente afetado; `Executar ingestão` para a mesma janela; `Conferir cargas` mostra `SUCESSO` e as 327.763 linhas (ou mais) na Silver.
- [ ] **Passo 5:** se a decisão de T1 for (a) ou (d), esta tarefa termina com o registro "sem correção de código", a causa e a data.

### Tarefa 3: Separar "origem fora do ar" de erro nosso

**Files:**
- Modify: `src/core/conector.py` (o ponto onde o runner captura a exceção da extração e chama `execucao.encerrar(erro=...)`)
- Test: `tests/unit/test_conector_runner.py` (use o arquivo de testes do runner que já existe; leia `tests/unit/` para achar o nome)

**Interfaces:**
- Produces: `erro` de `_execucoes` começa com `origem_indisponivel: ` quando a exceção é `requests.ConnectionError`, `requests.Timeout` ou HTTP 5xx; todo o resto mantém a mensagem atual. O status continua `ERRO` e o alerta continua disparando (a ness. não perde o aviso: ganha a causa).

- [ ] **Passo 1: teste que falha.** Conector falso cuja `extrair` levanta `requests.ConnectionError("dns")`; assertar que `execucao.erro.startswith("origem_indisponivel: ")` e que o status é `ERRO`. Outro com `ValueError("layout")`; assertar que `erro` **não** tem o prefixo.
- [ ] **Passo 2:** rodar → FAIL.
- [ ] **Passo 3:** no runner, onde hoje se faz `execucao.encerrar(str(exc))` (leia o trecho antes de editar), trocar por uma função pura `_descrever_erro(exc: Exception) -> str` que devolve `"origem_indisponivel: " + texto` para as três classes acima e `texto` para o resto, com o texto passando por `sanitizar` se o runner já o faz.
- [ ] **Passo 4:** suíte e ruff → PASS; commit `feat: runner marca erro de origem indisponível`; PR; mesclar. **Não** altera alerta, silêncio nem painel (decisão do A, linha T3: Ricardo).

### Tarefa 4: Explicar as 672 linhas inválidas do INMET

**Files:** Modify: `src/conectores/inmet_precipitacao.py` (só se o diagnóstico exigir); `docs/dicionario-dados/inmet_precipitacao.md`.

- [ ] **Passo 1: diagnóstico.** Com a rede da máquina de desenvolvimento (o INMET responde daqui), baixar o zip de 2025 e rodar a extração de uma estação, contando as linhas recusadas por motivo. Registrar a distribuição (motivo → quantidade) em uma nota.
- [ ] **Passo 2: regra de decisão.** (a) as 672 vêm de uma linha por estação sem medição ou de sentinela `-9999` tratada como inválida: ajustar o conector para contar como "sem medição" e não como inválida, com teste que fixa a regra; (b) vêm de uma coluna que falha a validação por layout: corrigir o modelo, com teste a partir de uma linha real anonimizada; (c) são legítimas: documentar no dicionário o motivo exato e o número esperado, sem mudar código.
- [ ] **Passo 3:** o teste vem antes da correção; suíte e ruff; commit; PR; mesclar; recarregar uma janela curta em dev e conferir `linhas_invalidas` na conferência.

### Tarefa 5: Registrar o motivo dos 554 testes ignorados

**Files:** Create: `docs/qualidade/testes-ignorados.md`.

- [ ] **Passo 1:** `uv run pytest tests -q -rs 2>&1 | tail -n 600 > <scratchpad>/skips.txt`.
- [ ] **Passo 2:** agrupar por motivo (`SKIPPED [n] arquivo:linha: motivo`) e escrever a tabela motivo → quantidade → exemplo no documento novo.
- [ ] **Passo 3: regra de decisão.** Motivo "falta credencial ou ambiente da Alup" (esperado): só documentar. Motivo diferente (por exemplo "não implementado" ou "lento"): abrir uma issue por grupo com o nome do arquivo e o motivo, **sem** dado de cliente e sem atribuição de ferramenta, e citar o número no documento. Nenhum teste é apagado neste plano.
- [ ] **Passo 4:** commit `docs: motivo dos testes ignorados`; PR; mesclar.

### Tarefa 6: Rede de segurança das listas da conferência e runbook da sonda

**Files:**
- Modify: `tests/unit/test_conferir_cargas.py`, `scripts/conferir_cargas.py` (só se faltar nome), `docs/runbook/deploy.md`

- [ ] **Passo 1: teste que falha.** Toda Silver de fonte nova tem de estar na lista ou numa lista explícita de exceções:

```python
def test_toda_silver_esta_na_conferencia_ou_na_lista_de_excecoes() -> None:
    """Fonte nova sem entrada na conferência passaria despercebida; a exceção tem de ser escrita."""
    silvers = {p.stem for p in (RAIZ / "definitions" / "silver").glob("*.sqlx")}
    cobertas = set(SILVER)
    assert silvers - cobertas - EXCECOES_DA_CONFERENCIA == set()
```

- [ ] **Passo 2:** rodar → FAIL listando as Silvers fora da conferência.
- [ ] **Passo 3:** para cada Silver listada, decidir pela fonte: entra em `SILVER` (se é Onda 1 ou Aditivo) ou vai para `EXCECOES_DA_CONFERENCIA` (constante nova em `tests/unit/test_conferir_cargas.py`, com comentário de uma linha dizendo por quê). Silver de Onda 0, Onda 2 ou Onda 3 que já tem conferência própria fica na exceção com esse motivo.
- [ ] **Passo 4:** em `docs/runbook/deploy.md`, seção curta "Sondar rede": como disparar (`gh workflow run "Sondar rede" -f environment=hml -f sonda=cptec`), que ela usa o job `ingestao-bcb-cambio-ptax` só como casca de execução, que grava o resultado em `sondas/<nome>/` do bucket raw e sai sempre com 0, e que a lista de endereços é constante em `src/core/sonda.py`.
- [ ] **Passo 5:** suíte e ruff; commit `test: conferência cobre toda Silver ou declara a exceção`; PR; mesclar.

### Tarefa 7: Fechamento

**Files:** Modify: `docs/relatorios/2026-10-03-fechamento-onda-1.md`, `docs/status.md`.

- [ ] **Passo 1:** seção "Débitos técnicos" no relatório: para T1 a T6, o resultado, o PR e a data; para cada linha D da matriz, a decisão do A e a data, ou "sem decisão ainda".
- [ ] **Passo 2:** `docs/status.md` reflete o mesmo. O painel não é alterado por este plano (D5 é decisão do Decisor ness.).
- [ ] **Passo 3:** suíte (inclui os testes do painel), ruff, commit `docs: fechamento dos débitos técnicos`; PR; mesclar.

---

## Autoavaliação

**Cobertura:** causa de falha ilegível = T1 (e T2 para corrigir); origem fora do ar confundida com erro nosso = T3; 672 inválidas do INMET = T4; testes ignorados = T5; listas da conferência e sonda = T6; registro = T7. Ficaram de fora de propósito: o atrito de fim de linha (configuração local do git) e as pendências antigas que dependem de terceiros (`usinas.csv` na #141, a pergunta da QI sobre o item 12), que não têm entrega técnica própria; entram na matriz só D6.

**Placeholders:** T1, T3 e T6 trazem teste e código. T2 e T4 **dependem de um diagnóstico que ainda não existe** (a causa do erro do `aneel_tarifas` e o motivo das 672 inválidas); escrever a correção antes seria inventar a causa. Por isso cada uma começa pelo diagnóstico e traz uma regra objetiva de decisão. T5 é inventário.

**Consistência:** o item `ultimo_erro` (T1) usa a coluna `erro` que `execucao.py` já grava; o prefixo `origem_indisponivel: ` (T3) é o que a conferência passa a mostrar em T1; `EXCECOES_DA_CONFERENCIA` é definida e usada só em T6.

**Riscos assumidos:** o texto de `erro` pode conter detalhe de infraestrutura: por isso só 200 caracteres, sanitizados, e só no resumo do GitHub (acessível à equipe com acesso ao repositório); T3 não muda o alerta; este plano não dá leitura de logs à conta de deploy.

## Estimativa (não é medição)

| Tarefa | Horas |
|---|---:|
| T1 | 2 |
| T2 | 1 a 4 |
| T3 | 2 |
| T4 | 2 a 4 |
| T5 | 1 |
| T6 | 2 |
| T7 | 1 |
| **Total** | **11 a 16** |
