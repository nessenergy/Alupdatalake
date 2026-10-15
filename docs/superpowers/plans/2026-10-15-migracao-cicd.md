# Migração do CI, deploy e operação para fora do GitHub Actions — plano

> **Para agentes:** executar fase a fase, na ordem. Cada fase termina com o Actions ainda funcionando; só a Fase 4 o desliga.

**Objetivo:** tirar do GitHub Actions o CI, o deploy, as operações sob demanda e os agendados, para o plano pago do GitHub (por assento) deixar de ser necessário.

**Decisão:** [ADR 030](../../arquitetura/decisoes/030-cicd-fora-do-github-actions.md).

**Arquitetura:** a lógica vai para `make` e scripts; o Cloud Build chama `make` com a conta de serviço do ambiente; operações viram gatilhos manuais; agendados viram Cloud Scheduler. O GitHub fica como repositório.

## Restrições

- Regra 5: tudo que existe na GCP está em `infra/`. Gatilhos, contas e agendamentos entram por Terraform.
- Regra 2: credencial só no Secret Manager. O build usa a conta de serviço do projeto, sem chave.
- Regra 6: nenhuma atribuição a ferramenta de IA em commit, PR ou documento.
- Operação sem depender de gente de fora da ness. (memória do projeto): o disparo das operações é por grupo, em `infra/`.
- Custo de GCP é da Alup (cláusula 5ª): registrar a estimativa e conferir na primeira fatura.
- `main` continua sem proteção (ADR 010).

## Fase 0 — Pipeline portátil (esta etapa)

- [x] ADR 030 e este plano.
- [x] `Makefile`: alvos `ci-lint`, `ci-testes`, `ci-atribuicao`, `ci-sast`, `ci-segredos`, `ci-terraform`, `ci-dataform`, `ci-sca` e o agregado `ci`, com teste em `tests/unit/test_infra.py`.
- [x] Medidas de transição no Actions: `concurrency` no CI (um push novo cancela a execução anterior do PR) e o Painel de 3 em 3 horas.
- [ ] Fazer os workflows `ci.yml`, `sca.yml` e `atribuicao.yml` chamarem os alvos do `Makefile` (fica para a Fase 1, junto do arquivo do Cloud Build, para os dois caminhos usarem exatamente o mesmo comando).

**Pronto quando:** `make ci` roda as oito etapas na ordem em uma máquina com `uv`, `node` e `terraform`.

## Fase 1 — CI de PR no Cloud Build

**Pré-requisito humano:** o dono da organização `nessenergy` instala o aplicativo do Cloud Build no GitHub e conecta o repositório ao projeto `alupar-dev-alupdata`. Sem isso, nada abaixo funciona.

- [ ] `cloudbuild/ci.yaml`: um passo por alvo `ci-*`, rodando em paralelo onde não há dependência; imagem com `uv`, `node` e `terraform`.
- [ ] `infra/modules/cicd`: API `cloudbuild`, conta de serviço do CI (leitura do repositório e escrita de log, sem papel de dado), gatilho de PR para `main` com a Checks API, e o gatilho de push em `main`.
- [ ] Executar em paralelo ao Actions por uma semana e comparar o resultado dos dois.

**Pronto quando:** um PR mostra os checks do Cloud Build, com o mesmo veredito do Actions em ao menos cinco PRs.

## Fase 2 — Deploy e operações sob demanda

- [ ] `cloudbuild/deploy.yaml` (imagem, Terraform, Dataform) com a variável `_AMBIENTE`; um gatilho manual por ambiente, executando como a conta de deploy daquele ambiente.
- [ ] Gatilhos manuais `executar-ingestao`, `conferir-cargas`, `sondar-rede` e `testar-conexao`, com as mesmas entradas dos workflows de hoje (`_CONECTOR`, `_DE`, `_ATE`, `_URI`, `_SONDA`, `_FONTE`).
- [ ] Papel para disparar gatilho concedido ao grupo de operação em `infra/` (R01).
- [ ] Runbooks (`deploy.md`, `incidentes.md`, `conferencia-e-sondas.md`) passam a mostrar `gcloud builds triggers run ...`.

**Pronto quando:** um deploy completo de dev e uma conferência de cargas em hml rodam pelo Cloud Build, com o mesmo resultado do Actions.

## Fase 3 — Agendados

- [ ] Painel, Quadro e Atribuição como Cloud Run Job (mesma imagem da CLI), chamados por Cloud Scheduler; SCA semanal como gatilho do Cloud Build chamado por Scheduler. Tudo em `infra/`.
- [ ] A chave do GitHub App do quadro continua no Secret Manager (passo humano pendente, `acoes-humanas.md` §2b).

**Pronto quando:** cada agendado rodou ao menos três vezes sem o Actions.

## Fase 4 — Desligar o Actions

- [ ] Uma semana estável das Fases 1 a 3.
- [ ] Remover `.github/workflows/`, o provedor de WIF e a condição por `environment` em `infra/bootstrap`, e os ambientes `dev`, `hml` e `prod` do GitHub.
- [ ] Atualizar `AGENTS.md`, `CLAUDE.md`, `docs/runbook/deploy.md` e a ADR 015 (adendo).
- [ ] Decisão do Ricardo, separada: tornar o repositório privado.

## Riscos

- O aplicativo do Cloud Build precisa de um dono de organização, e o resultado dos checks depende dele.
- O Cloud Build roda no projeto da Alup; a franquia (2.500 minutos de build por mês) cobre o uso esperado, mas é preciso conferir.
- O CodeQL sai; o SAST contratual continua com Bandit, a SCA com `pip-audit` e os segredos com Gitleaks.
- Quem opera perde o formulário do GitHub; o comando exige permissão no projeto GCP.
