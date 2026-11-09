# Guia de auditoria do projeto

Para quem audita o AlupData: o que o projeto promete, onde está a evidência e **o comando que a reproduz**. Posição em
**22/10/2026**. A visão de uma página está em [`visao-consolidada.md`](visao-consolidada.md); o relatório com os números de hoje, em
[`relatorios/2026-10-22-situacao-consolidada.md`](relatorios/2026-10-22-situacao-consolidada.md).

Os comandos supõem `uv sync --frozen --extra dev --extra bancos` já executado. Os workflows de leitura (`Conferir cargas`, `Testar conexão`)
rodam no GitHub e mostram o resultado no resumo da execução.

## 1. Mapa de controles

| # | Controle | O que se verifica | Evidência no repositório | Como reproduzir |
|---|---|---|---|---|
| 1 | **Padrão de entrega, 7 componentes por fonte** (cláusula 2ª) | conector, Bronze, Silver, Gold, teste, agendamento e dicionário com linhagem, para cada fonte | [`scripts/conferir_componentes.py`](../scripts/conferir_componentes.py); [`dicionario-dados/`](dicionario-dados/README.md) | `make componentes` |
| 2 | **Dado carregado e conferido** | a carga existe no BigQuery e bate com a origem | workflow `Conferir cargas` ([`scripts/conferir_cargas.py`](../scripts/conferir_cargas.py)), somente leitura | `gh workflow run "Conferir cargas" -f environment=dev` |
| 3 | **Análise estática de segurança** (SAST, cláusula 8.4) | sem achado de severidade média ou alta | job "SAST (Bandit)" em [`ci.yml`](../.github/workflows/ci.yml) | `make ci-sast` |
| 4 | **Vulnerabilidades em dependências** (SCA, cláusula 8.4) | `pip-audit` sem achado | [`sca.yml`](../.github/workflows/sca.yml) e `uv.lock` | `make ci-sca` |
| 5 | **Segredos fora do código** (cláusula 8.5) | nenhuma credencial no repositório nem no histórico | job "Detecção de Secrets" (Gitleaks); [`runbook/credenciais.md`](runbook/credenciais.md) | `make ci-segredos` |
| 6 | **Credencial só no Secret Manager** | segredos criados vazios pelo Terraform; valor gravado por grupo, sem ler | [`infra/modules/secrets/`](../infra/modules/secrets/); [ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md) | `uv run pytest tests/unit/test_infra.py -q` |
| 7 | **Sem chave de conta de serviço** | o deploy usa identidade federada, não chave JSON | [`infra/bootstrap/main.tf`](../infra/bootstrap/main.tf); [`runbook/deploy.md`](runbook/deploy.md) | `uv run pytest tests/unit/test_bootstrap.py -q` |
| 8 | **Menor privilégio e acesso por grupo** | nenhum papel básico; pessoa entra por grupo, nunca individual; Bronze só leitura para a Alupar | [`infra/main.tf`](../infra/main.tf); [`lgpd/ripd.md`](lgpd/ripd.md) | `uv run pytest tests/unit/test_infra.py -q` |
| 9 | **Infraestrutura como código** (regra 5) | todo recurso GCP está em `infra/` | [`infra/`](../infra/) (12 módulos) | `make ci-terraform` |
| 10 | **Controle de mudança** | PR para `main`, commits convencionais, 30 decisões registradas | [`arquitetura/decisoes/`](arquitetura/decisoes/); [`CONTRIBUTING.md`](../CONTRIBUTING.md); [`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) | `git log --oneline` |
| 11 | **Autoria e conformidade de commits** (regra 6) | nenhum commit, PR ou issue com atribuição de ferramenta | [`scripts/verifica_atribuicao.py`](../scripts/verifica_atribuicao.py); job "Commits sem atribuição" | `make ci-atribuicao` |
| 12 | **Qualidade dos testes** | suíte unitária sem rede, cobertura medida | `tests/` (113 arquivos) | `uv run pytest tests/ --cov=src` |
| 13 | **Camadas e linhagem** | Bronze append-only, particionada e clusterizada; Silver deduplicada; Gold por pergunta de negócio; execução registrada | [`definitions/`](../definitions/); [`arquitetura/visao-geral.md`](arquitetura/visao-geral.md); `bronze._execucoes` | `make dataform-compile` |
| 14 | **Operação e monitoramento** | alertas por fonte, saúde por fonte, runbooks | [`runbook/`](runbook/); [`gold.saude_ingestao`](../definitions/gold/saude_ingestao.sqlx) | `Conferir cargas` (itens `saude_*`) |
| 15 | **Proteção de dados pessoais** (LGPD) | RIPD, RoPA, DPA e política de retenção | [`lgpd/`](lgpd/) | leitura dos documentos |
| 16 | **Acompanhamento do projeto** | estado, plano, painel e relatórios datados | [`status.md`](status.md); [`plano-execucao.md`](plano-execucao.md); [`relatorios/`](relatorios/); `painel/marcos.toml` | `python -c "import scripts.painel as p; p.carregar_marcos()"` |

## 2. Os 7 componentes, na prática

A cláusula 2ª exige, por fonte: **(1)** conector Python, **(2)** tabela Bronze, **(3)** view Silver, **(4)** view Gold, **(5)** testes,
**(6)** agendamento e **(7)** dicionário com linhagem. O `make componentes` percorre o registro de conectores (`src/core/registry.py`) e
confere a existência de cada artefato. Em 06/11/2026: **56 fontes, 56 com todos os componentes de arquivo** (eram 58 em 22/10; o TempoOK saiu do registro em 30/10, #444).

Duas ressalvas, ditas de frente:

- É verificação de **existência**. Que a carga seja correta é conferido por `Conferir cargas` e pelos testes.
- Hubspot e BBCE foram escritos contra a documentação pública, e o teste de integração só roda com credencial. O Hubspot passou a carregar
  dado real em 22/10; o BBCE ainda não tem credencial.

## 3. Segurança no ciclo de desenvolvimento (SSDLC)

O CI roda em todo PR e no push para `main`: lint, testes, SAST (Bandit), segredos (Gitleaks), validação do Terraform, compilação do
Dataform, checagem de atribuição e, em separado, a SCA semanal e por PR. Vulnerabilidade de severidade alta ou crítica é corrigida antes
da homologação (cláusula 8.6): o último caso, a `werkzeug` (CVE-2026-102598), foi corrigido em 14/10 com a atualização da dependência.

As etapas do CI são alvos do `Makefile` (`make ci`), o que permite reproduzi-las fora da plataforma de CI. Detalhe em
[`arquitetura/seguranca.md`](arquitetura/seguranca.md) e na [ADR 030](arquitetura/decisoes/030-cicd-fora-do-github-actions.md).

## 4. Rastreabilidade de uma carga

1. O agendamento (Cloud Scheduler) dispara o Cloud Run Job do conector com uma **janela de datas** (regra 3).
2. O runner grava o bruto no bucket raw, valida, acrescenta as colunas técnicas (`_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`)
   e carrega a Bronze (regra 4: append-only).
3. Cada execução deixa uma linha em `bronze._execucoes` (início, fim, linhas, erro).
4. A Silver deduplica por chave natural; a Gold responde a uma pergunta de negócio.
5. `gold.saude_ingestao` resume a frescura e o erro por fonte, e o Portal a exibe.

## 5. Limitações conhecidas

Registradas para que a auditoria as encontre aqui e não por descoberta:

| Limitação | Situação |
|---|---|
| **Produção não existe** | só `dev` e `hml` estão aplicados; o plano do bootstrap está em [`superpowers/plans/2026-10-14-bootstrap-producao.md`](superpowers/plans/2026-10-14-bootstrap-producao.md) |
| **`main` sem proteção de branch** | decisão consciente, [ADR 010](arquitetura/decisoes/010-aceite-risco-main-sem-protecao.md); a revisão é por PR e CI |
| **Alguns itens da Onda 1 sem entrega** | IPDO e ACOMPH, com as decisões em [ADR 027](arquitetura/decisoes/027-ons-operacional-ipdo-acomph.md). O CPTEC saiu do escopo em 23/10/2026 ([ADR 028](arquitetura/decisoes/028-cptec-acesso.md) e [029](arquitetura/decisoes/029-previsao-do-tempo-fonte.md)) |
| **Fontes da Onda 3 dependem de rede e de esquema** | FMB (Oracle) depende de caminho de rede via terceiro; os bancos MySQL conectam, mas faltam os esquemas |
| **558 testes ignorados** | cerca de 96% são regras SQL parametrizadas que não se aplicam à camada testada, por desenho; o resto exige contêiner de banco ou chamada real opt-in |
| **Eliminação de dados de teste** (cláusula 8.3) | a executar na homologação final de cada etapa |
| **Revogação dos papéis de bootstrap** | obrigatória na homologação final e no handoff ([ADR 015](arquitetura/decisoes/015-fundacao-do-ambiente.md)) |
| **Visibilidade do repositório** | o repositório não deve conter dado real de cliente (regra do projeto); a visibilidade é decisão da coordenação |

## 6. Onde está cada coisa

| Quero ver | Vá para |
|---|---|
| as regras do projeto | [`AGENTS.md`](../AGENTS.md) |
| o contrato resumido | [`contrato/resumo-contrato.md`](contrato/resumo-contrato.md) |
| a arquitetura | [`arquitetura/visao-geral.md`](arquitetura/visao-geral.md) |
| as decisões e o porquê | [`arquitetura/decisoes/`](arquitetura/decisoes/) |
| o que cada campo significa | [`dicionario-dados/`](dicionario-dados/README.md) |
| como operar | [`runbook/`](runbook/) |
| o estado hoje | [`status.md`](status.md) e [`visao-consolidada.md`](visao-consolidada.md) |
| quem faz o quê | [`raci.md`](raci.md) e [`interlocutores.md`](interlocutores.md) |
