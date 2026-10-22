# Análise global, visão consolidada e preparação para auditoria — plano

> **Para agentes:** executar tarefa a tarefa, na ordem. Cada tarefa termina com uma evidência (comando, run ou arquivo) e um commit.

**Goal:** medir o estágio real do AlupData em 22/10/2026, atualizar todos os documentos de acompanhamento com o que foi medido, criar uma visão consolidada e um relatório atual, e deixar o repositório pronto para uma auditoria de projeto.

**Architecture:** só documentação e conferência. Cada afirmação do relatório vem de uma medição datada (workflow de leitura, comando local ou documento citado). Nada de infraestrutura nova, nenhum conector novo.

**Tech Stack:** Markdown, `scripts/painel.py` (valida `painel/marcos.toml`), workflow `Conferir cargas`, `uv` e `pytest` para os números de teste, Edge headless para o PDF.

**Spec:** `docs/contrato/resumo-contrato.md`, `docs/plano-execucao.md`, `AGENTS.md`. Pedido do Ricardo em 22/10/2026: "análise global do estágio, atualizar todos os documentos de acompanhamento, visão consolidada, relatório atual, README para auditoria".

## Global Constraints

- **Regra 6:** nenhuma atribuição de ferramenta de IA em commit, PR ou documento; validar a mensagem com `python scripts/verifica_atribuicao.py`.
- **Sem faturamento:** os documentos de acompanhamento trazem dado técnico e de andamento. Nenhum valor em reais, marco faturado ou horas contratadas como medida de faturamento (decisão do Ricardo em 19/10).
- **Sem dado novo sensível:** o repositório é visível a terceiros. Não acrescentar IP, nome de equipamento, credencial nem nome de segredo que já não esteja documentado.
- **Fato, não opinião:** cada número leva a data e a fonte (run, comando ou arquivo). O que não foi medido é dito como "não medido".
- Documentos em português, commits convencionais, branch `docs/…`, PR para `main`, mesclar só com CI verde e todos os checks concluídos, adicionar arquivos por nome.
- Canal da equipe: publicar o resumo no canal Alup Datalake do Teams depois de mesclar.

## Fatos de entrada (medidos em 22/10)

| Fato | Fonte |
|---|---|
| Hubspot carrega em dev e hml e saiu da lista de fontes fora do OK | runs `39776552963`, `39776564873` e a conferência seguinte |
| DB Alup (MySQL) e DB Comercialização (MySQL) conectam; FMB (Oracle) ainda expira | testes de conexão de 19 e 22/10 |
| TempoOK sai integralmente do escopo como fonte do lake | resposta do Leonardo registrada pelo Gabriel no canal, 20/10 |
| ONS: usuário e senha; CCEE: usuário, senha e certificado, ou token de API; RM/TOTVS: só webservice | idem, e mensagem do Thiago, 20/10 |
| BBCE: segredo ainda sem versão; o e-mail com o formato não foi enviado | conferência de 22/10; caixa de enviados |
| Saúde: dev 56 OK, 1 ATRASADA, 1 SEM_SUCESSO; hml 55 OK, 1 SEM_SUCESSO | `Conferir cargas`, 22/10 |

## Tarefa 1: Números de teste e de código, medidos agora

**Files:**
- Create (temporário, fora do repositório): saída dos comandos no scratchpad.

- [ ] **Passo 1:** instalar as dependências completas: `uv sync --frozen --extra dev --extra bancos`.
- [ ] **Passo 2:** `uv run pytest tests/ -q --cov=src --cov-report=term | tail -5`. Anotar testes aprovados, ignorados e a cobertura.
- [ ] **Passo 3:** contar conectores com os 7 componentes pelo script do registro (stub de `shapefile` se faltar) e ADRs, dicionários e runbooks por `ls`.
- [ ] **Passo 4:** gravar os números no relatório da Tarefa 2 com a data e o comando.

**Pronto quando:** cada número do relatório tem um comando que o reproduz.

## Tarefa 2: Relatório atual e visão consolidada

**Files:**
- Create: `docs/relatorios/2026-10-22-situacao-consolidada.md`
- Create: `docs/visao-consolidada.md`

- [ ] **Passo 1:** escrever `docs/visao-consolidada.md`, uma página que responde: o que é o projeto, as cinco ondas, o estado de cada onda e fonte, os ambientes, os prazos, o que depende de quem. É o documento que um auditor lê primeiro.
- [ ] **Passo 2:** escrever o relatório de 22/10 com: avaliação por onda e item em quatro níveis de evidência (aceita, conferida, escrita sem carga, não entregue); a matriz de credenciais e conexões; o estado da saúde por ambiente; mudanças de escopo (TempoOK); riscos; decisões pendentes por dono; e a seção "Como foi medido".
- [ ] **Passo 3:** conferir que nenhum valor financeiro entrou: `grep -nE "R\$|faturament|marco [0-9]" docs/visao-consolidada.md docs/relatorios/2026-10-22-situacao-consolidada.md` deve voltar vazio.

**Pronto quando:** os dois arquivos existem, citam só números medidos e passam no `grep`.

## Tarefa 3: Documentos de acompanhamento

**Files:**
- Modify: `docs/status.md`, `docs/plano-execucao.md`, `docs/proximos-passos.md`, `docs/acoes-humanas.md`, `painel/marcos.toml`

- [ ] **Passo 1:** `status.md`: nova seção "Atualização de 22/10/2026" no topo, apontando para a visão consolidada e o relatório; corrigir o que ficou desatualizado (contagens, credenciais, TempoOK).
- [ ] **Passo 2:** `plano-execucao.md`: itens 2.3 (Hubspot com carga real), 2.4 (TempoOK retirada do escopo pela Alupar, confirmação por escrito pendente) e 3.2, 3.3, 3.1 (credenciais e conexões).
- [ ] **Passo 3:** `proximos-passos.md`: acrescentar o quadro do dia e marcar o que foi superado.
- [ ] **Passo 4:** `acoes-humanas.md`: lista curta das ações que dependem de pessoa (bootstrap de dev e hml, envio do e-mail ao Leonardo, confirmações).
- [ ] **Passo 5:** `painel/marcos.toml`: notas e marcos de 19 a 22/10, sem mudar a fração de nenhum item sem evidência; validar com `python -c "import scripts.painel as p; p.carregar_marcos()"`.

**Pronto quando:** os cinco arquivos citam a mesma situação e o painel valida.

## Tarefa 4: README e guia de auditoria

**Files:**
- Modify: `README.md`
- Create: `docs/auditoria.md`

- [ ] **Passo 1:** `README.md`: o que é o projeto, estado atual em uma tabela, como navegar (mapa de documentos), como reproduzir a evidência (`make ci`, `Conferir cargas`), regras do projeto, ambientes, segurança (SSDLC), e como contribuir.
- [ ] **Passo 2:** `docs/auditoria.md`: mapa de evidências, requisito por requisito: os 7 componentes por fonte, SSDLC (SAST, SCA, segredos), controle de mudança (PR, ADR), controle de acesso (por grupo), tratamento de dado (Bronze, Silver, Gold), operação (runbooks), com o comando que reproduz cada evidência e as limitações conhecidas.
- [ ] **Passo 3:** checar que todo link relativo dos dois arquivos aponta para arquivo existente (script em Python no scratchpad).

**Pronto quando:** nenhum link quebrado e cada controle tem arquivo e comando de evidência.

## Tarefa 5: Entrega

- [ ] **Passo 1:** PR único, CI verde com todos os checks concluídos, merge.
- [ ] **Passo 2:** PDF do relatório, na marca ness., em `Downloads` (fora do repositório).
- [ ] **Passo 3:** resumo no canal do Teams, sem valores.
- [ ] **Passo 4:** reler a lista de decisões pendentes e entregá-la ao Ricardo.

## Riscos

- O número de testes local pode diferir do CI por dependência de plataforma: registrar os dois e a origem de cada um.
- A fração dos itens do painel é avaliação nossa: só muda com evidência nova (Hubspot com carga real é a única).
- O TempoOK saiu do escopo só por relato; os documentos dizem "retirada comunicada em 20/10, confirmação por escrito pendente".
