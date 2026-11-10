# Revisão completa: higienização, documentação e quadro de acompanhamento — plano

> **Para quem executa:** usar superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans. Passos com caixa de seleção.

**Objetivo:** deixar o repositório, a documentação e o quadro que a Alupar acompanha (Project 2 e `painel.alupdata.ness.com.br`) coerentes com o estado real de 05/11/2026, sem apagar nada que não esteja comprovado.

**Arquitetura:** o trabalho tem três frentes que não dependem uma da outra, nesta ordem de risco: (1) documentos e mapas versionados (`docs/`, `painel/marcos.toml`, `scripts/quadro.toml`), que viram PR; (2) o que mora só no GitHub (issues, branches remotas, alertas), que é visível para a contratante e exige confirmação; (3) a sincronização do quadro, que roda os scripts que já existem (`scripts/quadro.py`, `scripts/painel.py`) em vez de editar o Project 2 à mão.

**Stack:** git, `gh`, `uv`, pytest, ruff, `scripts/quadro.py`, `scripts/painel.py`.

**Spec:** não há spec formal. O pedido é o de 05/11/2026 do Ricardo ("revisão completa, higienização, atualização de documentação, atualização dos projetos no painel do GitHub que a ness acompanha"). Fatos de partida, medidos em 05/11:

| Item | Medido |
|---|---|
| PRs abertos | #450 (sessão SOAP da CCEE) e #398 (Dependabot, 4 ações de CI) |
| Alerta Dependabot | #1, alta, `virtualenv` (ativador Bash) |
| Branches remotas | 165; `git branch -r --merged` acha 0 porque o repositório usa squash, então a limpeza tem de olhar o estado do PR |
| Arquivos soltos | `.claude/settings.json` e `.impeccable/` sem rastreio |
| `docs/status.md` e `docs/proximos-passos.md` | "Atualizado em 2026-10-29"; sem o que houve de 03 a 05/11 |
| Project 2 | 78 itens: 49 Done, 10 In Progress, 19 Todo |
| Issues abertas sem etiqueta de onda | #294, #188, #111 |
| Issue aberta de fonte fora do escopo | #25 (TempoOK, retirado em 20/10 e 27/10) |

## Restrições globais

- Regra 6: nada com atribuição, coautoria ou assinatura de ferramenta de IA em commit, PR, issue, comentário ou documento. A checagem automática só cobre commit; conferir à mão o que for publicado no GitHub.
- Credencial só pelo Secret Manager. **Nenhum documento, issue ou comentário cita usuário, senha, login pessoal ou valor de segredo da CCEE**; falar em "usuário de acesso" e "perfil de agente".
- Texto em pt-BR; commits em conventional commits (`docs:`, `chore:`); branches `docs/…` e `chore/…`; PR para `main`.
- **Pedir confirmação do Ricardo antes de cada ação irreversível ou visível para a Alupar:** mesclar PR, apagar branch remota, fechar issue, rodar `scripts.quadro --aplicar`.
- Só se fecha issue com evidência escrita no comentário. O que não está provado fica aberto.
- Nada de dado real de cliente no repositório.

## Review Focus

1. **Branch apagada com trabalho que ninguém mesclou.** Squash faz o git achar que nada foi mesclado, e o inverso também engana. Esperado: só entra na lista de exclusão a branch cujo PR está `MERGED` ou `CLOSED` sem commits fora da `main`; o resto vira lista para o Ricardo decidir.
2. **Issue fechada sem prova, visível para a Alupar.** Esperado: cada fechamento tem comentário com fato e fonte no repositório.
3. **`--aplicar` sobrescrevendo decisão humana ou comentando atraso errado.** Esperado: simular primeiro, ler a saída inteira, aplicar só depois do "sim".
4. **Número de dias e contagem desatualizados nos documentos** ("dia 59 de 130", "restam 71 dias"). Esperado: recalculados pela mesma regra do status de 29/10, e iguais em `status.md`, `proximos-passos.md`, `visao-consolidada.md` e `painel/marcos.toml`.
5. **Segredo ou usuário da CCEE vazando em doc ou comentário.** Esperado: `git grep` e `scripts/verifica_atribuicao.py` limpos antes de cada push.

---

### Tarefa 1: linha de base (só leitura)

**Arquivos:** nenhum alterado.

- [ ] **Passo 1:** `git switch main && git pull --ff-only`, depois `uv run ruff check src tests`, `uv run ruff format --check src tests` e `uv run pytest -q`. Esperado: tudo verde (2095 passam, 534 pulados em 05/11).
- [ ] **Passo 2:** `uv run python -m scripts.conferir_componentes`. Esperado: lista de fontes com os 7 componentes; anotar qualquer fonte incompleta, porque documento nenhum pode dizer "56 fontes com os 7 componentes" se o número mudou.
- [ ] **Passo 3:** guardar em `scratchpad/baseline-05-11.txt` a contagem de testes, de fontes e dos itens do Project 2 por status. Esse arquivo não entra no repositório.

### Tarefa 2: fila de PRs e alerta de dependência

**Arquivos:** `uv.lock` (se o alerta pedir); nenhum outro.

**Consome:** o PR #450 já aberto.

- [ ] **Passo 1:** `gh pr checks 450`. Quando os 9 checks estiverem verdes, **pedir o "sim" do Ricardo** e mesclar com `gh pr merge 450 --squash --delete-branch`.
- [ ] **Passo 2:** revisar o #398: `gh pr view 398 --json files,body` e conferir que as ações continuam fixadas por SHA, pois `tests/unit/test_acoes_fixadas.py` exige. Se os checks passarem, pedir o "sim" e mesclar; se não, fechar com comentário do motivo.
- [ ] **Passo 3:** alerta #1 (`virtualenv`, alta). Verificar se a branch `chore/deps-urllib3-virtualenv` já o resolve: `git log origin/main..origin/chore/deps-urllib3-virtualenv --oneline`. Se sim, abrir PR dela; se não, `uv lock --upgrade-package virtualenv`, rodar `uv run pytest -q` e abrir PR `chore: atualiza virtualenv`.
- [ ] **Passo 4:** depois do merge, `gh api repos/nessenergy/Alupdatalake/dependabot/alerts --jq '[.[]|select(.state=="open")]|length'`. Esperado: `0`.

### Tarefa 3: higienizar o repositório

**Arquivos:** `.gitignore`; possivelmente `.claude/settings.json`; nenhum código.

- [ ] **Passo 1:** ler `.claude/settings.json`. O `AGENTS.md` trata `.claude/` como versionado, então decidir: se tiver só permissões do projeto e nada pessoal, adicionar; se for local da máquina do Ricardo, ignorar. Registrar a decisão no commit.
- [ ] **Passo 2:** `.impeccable/` é contexto de ferramenta local: adicionar `.impeccable/` ao `.gitignore`.
- [ ] **Passo 3:** montar a lista de branches remotas por estado do PR, sem apagar nada:
  `gh pr list --state all --limit 400 --json number,headRefName,state --jq '.[]|"\(.state) \(.headRefName)"' | sort`.
  Classificar: `MERGED` (apagável), `CLOSED` (apagável se sem commit fora da `main`), sem PR (decisão do Ricardo, incluindo `chore/laptop-wip-2026-10-06` e `feat/alup-grava-credenciais`).
- [ ] **Passo 4:** para cada branch candidata, `git log origin/main..origin/<branch> --oneline | wc -l`. Esperado para as apagáveis: `0` commits que a `main` não tenha por conteúdo; qualquer branch com commits próprios sai da lista.
- [ ] **Passo 5:** mostrar a lista final ao Ricardo e, **com o "sim"**, `git push origin --delete <branch>` uma por uma, depois `git fetch --prune`. Esperado: `git branch -r | wc -l` bem abaixo de 165 e todas as ativas preservadas.
- [ ] **Passo 6:** `git worktree prune` e remover do disco as worktrees órfãs de `C:\Users\resper\worktrees\` que não estejam em uso (confirmar com `git worktree list`).
- [ ] **Passo 7:** commit `chore: ignora contexto local de ferramenta` e PR com os 9 checks.

### Tarefa 4: higienizar issues e o mapa do quadro

**Arquivos:** `scripts/quadro.toml`; `tests/unit/test_quadro.py` se existir teste do mapa.

- [ ] **Passo 1:** #25 (conector TempoOK, aberta). Comentar com a evidência (TempoOK fora do escopo em 20/10, confirmado em 27/10, `docs/status.md`) e fechar com `gh issue close 25 --reason "not planned"`. **Pedir o "sim" antes.**
- [ ] **Passo 2:** classificar as sem onda: #294 (Aditivo 01), #188 (alerta de silêncio), #111 (minutas DPA/RoPA/RIPD). Para cada uma, aplicar a etiqueta `onda/…` e `tipo/…` coerentes com o conteúdo, e incluir o número no mapa `[ondas]` de `scripts/quadro.toml` (e em `alup = […]` quando a próxima ação for da Alupar).
- [ ] **Passo 3:** conferir os blocos das fontes em andamento: #22 (conector CCEE) e #260 (posição sobre as 32 h). Comentar em cada um o estado de 05/11, sem usuário nem senha: conexão mTLS validada, envelope confirmado com o modelo de produção da Alupar, falta usuário de acesso dedicado e perfil de agente por ponto; link do PR #450.
- [ ] **Passo 4:** `uv run pytest tests/unit -q -k "quadro or painel"`. Esperado: passa. Commit `chore: mapeia issues novas no quadro`.

### Tarefa 5: atualizar a documentação

**Arquivos:** `docs/status.md`, `docs/proximos-passos.md`, `docs/visao-consolidada.md`, `docs/arquitetura/decisoes/018-vias-de-acesso-a-ccee.md`, `painel/marcos.toml`.

- [ ] **Passo 1:** recalcular os contadores. Abrir a seção de 29/10 do `status.md`, identificar a regra ("dia 59 de 130", "restam 71") e aplicá-la a 05/11. Escrever o resultado e a conta no commit, para ficar conferível.
- [ ] **Passo 2:** `docs/status.md`: nova seção "Atualização de 05/11/2026" acima da de 29/10, com só o que houve: CCEE (spec e plano mesclados em #448, correção do `pyasn1` em #449, sessão SOAP com mTLS em #450, certificado e credenciais gravados em hml e dev, primeira chamada real recusada com "Acesso Negado" por falta de usuário dedicado), higienização feita (números reais de branches, alertas e issues). Atualizar a linha "Atualizado em" do cabeçalho.
- [ ] **Passo 3:** `docs/proximos-passos.md`: riscar o que foi feito e registrar a próxima ação da CCEE (reunião de 06/11 com a Alupar para receber o usuário dedicado, perfil por ponto e um ponto de exemplo; depois gravar a versão nova do segredo e fazer uma tentativa única em hml). Atualizar a data do cabeçalho.
- [ ] **Passo 4:** `docs/arquitetura/decisoes/018-vias-de-acesso-a-ccee.md`: adendo datado de 05/11 com o fato confirmado (certificado na conexão HTTPS, usuário e senha no envelope SOAP, endpoint `ListarMedidaBSv1`, cada endpoint com XML próprio) e a decisão de primeira entidade ser a medição de 5 minutos, a confirmar na reunião.
- [ ] **Passo 5:** `docs/visao-consolidada.md`: corrigir números e datas que mudaram desde 29/10.
- [ ] **Passo 6:** `painel/marcos.toml`: marcos de 03 a 06/11 (spec e plano da CCEE, sessão SOAP, reunião de 06/11), `estado` entre os valores aceitos por `carregar_marcos` em `scripts/painel.py`.
- [ ] **Passo 7:** `git grep -n -i -E "senha|password|usuario" -- docs painel | grep -i ccee` revisado à mão: nenhum valor, só nomes de campo. Depois `git grep -n -i -E "co-authored|generated (with|by)" -- docs painel` (esperado: nenhuma linha nova) e `uv run pytest tests/unit/test_painel.py -q`. Esperado: tudo limpo e verde.
- [ ] **Passo 8:** commit `docs: atualiza estado do projeto em 05/11` e PR com os 9 checks.

### Tarefa 6: sincronizar o quadro e conferir

**Arquivos:** nenhum.

- [ ] **Passo 1:** com o PR da Tarefa 5 mesclado, `export GITHUB_TOKEN=$(gh auth token)` e `uv run python -m scripts.quadro` (simula). Ler a saída inteira e classificar: itens que passam a Done, atrasos novos que seriam comentados, itens "sem onda". Esperado: nenhum item "sem onda" e nenhuma decisão humana alterada.
- [ ] **Passo 2:** mostrar ao Ricardo o resumo da simulação e, **com o "sim"**, `uv run python -m scripts.quadro --aplicar`.
- [ ] **Passo 3:** `gh workflow run Painel` e acompanhar até `success` (`gh run watch`).
- [ ] **Passo 4:** conferir o publicado: `https://painel.alupdata.ness.com.br/dados.json` sem pendência já resolvida (#25 fora) e com os marcos novos; `gh project item-list 2 --owner nessenergy --limit 200 --format json --jq '[.items[].status]|group_by(.)|map("\(.[0]): \(length)")'` e comparar com a linha de base da Tarefa 1.
- [ ] **Passo 5:** registrar o resultado no `docs/status.md` (uma linha com as contagens finais) em um commit `docs: registra o quadro sincronizado`.

## Fora do plano

- Resíduos de CPTEC e TempoOK no BigQuery de dev e hml: exigem conta com `bigquery.tables.delete`, que o Ricardo não tem hoje. Fica como ação humana em `docs/acoes-humanas.md`.
- Bootstrap de produção (`prod-alupdata`): só preparado, não aplicado.
- Execução das Tarefas 2 a 4 da CCEE (conector `ccee_pi_*`): depende do usuário dedicado da reunião de 06/11.

## Revisão do plano

- **Cobertura:** higienização do repositório (T2, T3), das issues (T4), documentação (T5), quadro e painel (T6), com linha de base antes (T1).
- **Risco principal:** ações visíveis para a Alupar (fechar issue, `--aplicar`). Por isso o "sim" antes de cada uma, e a simulação antes de gravar.
- **Ordem:** documentos primeiro, porque `scripts/quadro.py` e `scripts/painel.py` leem `quadro.toml` e `marcos.toml` do `main`.
