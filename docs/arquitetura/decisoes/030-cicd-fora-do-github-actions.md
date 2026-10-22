# ADR 030 — CI, deploy e operação fora do GitHub Actions

**Status**: aceito · **Data**: 2026-10-15 · **Substitui em parte** a [ADR 015](015-fundacao-do-ambiente.md)
(WIF com token do GitHub e ambientes do GitHub) e **complementa** a [ADR 017](017-orquestracao-sem-composer.md)

## 1. Contexto

Todo o CI, o deploy e a operação sob demanda do AlupData rodam no GitHub Actions: 10 workflows, a identidade na GCP por
Workload Identity Federation com o token do GitHub (a condição do provedor exige o repositório e a *claim* `environment`) e os
ambientes `dev`, `hml` e `prod` do GitHub.

O Ricardo decidiu, em 15/10/2026, sair do Actions pelo **custo**: manter Actions com ambientes em repositório privado exige o plano
pago do GitHub, cobrado **por assento**, e a cota de minutos é **compartilhada** com outros projetos da ness.

Fatos medidos em 15/10/2026, que delimitam a decisão:

- Em 15/10/2026 o repositório `nessenergy/Alupdatalake` era **público** e a organização estava no plano Free (`gh api`). Por isso o
  custo líquido de Actions era zero: setembro teve 1.508 minutos na organização (585 no AlupData, o resto sobretudo no
  `sitealupar`) e US$ 9,05 de custo bruto, todos descontados.
- O consumo do AlupData em 7 dias foi de 444 minutos: CI de PR 43%, CodeQL a cada push 10%, Painel (de hora em hora) 18%.
- O CI é pesado porque cada PR roda tudo, inclusive PR só de documentação.
- **Histórico:** o repositório público expunha detalhes do cliente (faixas de rede, nome do FortiGate, IDs de projeto e e-mails de
  contas de serviço). No plano Free, tornar o repositório privado **desligaria os ambientes do GitHub** (recurso de plano pago em
  repositório privado) e quebraria o deploy atual. Esse ponto foi resolvido pela migração para o Cloud Build (§2 e §5).

## 2. Decisão

O GitHub fica só como **repositório, PRs, issues, Projects e Dependabot**. Nenhum workflow roda lá.

1. **CI de PR e deploy no Cloud Build**, em cada projeto GCP, com gatilho do GitHub e **conta de serviço do próprio ambiente**
   (a de deploy da ADR 015). Sem WIF e sem ambiente do GitHub: a identidade passa a ser a conta de serviço do build. O resultado
   aparece nos checks do PR pela Checks API do Cloud Build.
2. **Operações sob demanda** (executar ingestão, conferir cargas, sondar rede, testar conexão) viram **gatilhos manuais** do Cloud
   Build, chamados por `gcloud builds triggers run <nome> --substitutions=...`, com as mesmas entradas dos workflows de hoje.
3. **Agendados** (Painel, Quadro, Atribuição, SCA semanal) viram **Cloud Scheduler chamando Cloud Run Job ou gatilho do Cloud
   Build**, declarados em `infra/` (regra 5).
4. **A lógica sai dos arquivos de pipeline** para `make` e scripts do repositório. O arquivo do Cloud Build só chama `make`.
   Isso torna o pipeline portátil e é o primeiro passo, porque não depende de nada externo.
5. **CodeQL sai.** O SAST contratual (cláusula 8ª) continua com Bandit, a SCA com `pip-audit` e o segredo com Gitleaks, todos no
   CI. O Dependabot continua, porque é recurso do repositório, não do Actions.

## 3. Alternativas descartadas

- **GitHub Team por assento:** é o custo que se quer evitar.
- **Runner próprio do Actions:** resolve a cota, mas mantém a dependência do Actions e dos ambientes.
- **GitLab, Azure DevOps ou Jenkins:** obrigam a mover o repositório, e o cliente acompanha o projeto pelo GitHub.
- **Só reduzir minutos** (pular CI em PR de documentação, Painel de 3 em 3 horas): barato e útil, **mas não elimina o plano pago**
  se o repositório for privado. Entra como medida de transição na Fase 0.

## 4. Consequências

- **Passo humano único:** o dono da organização instala o aplicativo do Cloud Build no GitHub e conecta o repositório. Sem isso,
  nenhum gatilho de PR existe.
- **Custo de build é da Alup** (cláusula 5ª, infra GCP). A franquia do Cloud Build é de 2.500 minutos de build por mês, e o AlupData
  usa cerca de 800 minutos de Actions por mês, então o custo esperado é nulo. Confirmar com a primeira fatura.
- **Perdemos o botão de dispatch** com formulário do GitHub. O substituto é o comando acima, e o runbook passa a documentá-lo.
  Quem opera precisa de permissão para disparar gatilho (papel no projeto), concedida por grupo em `infra/` (R01).
- **WIF e ambientes do GitHub deixam de ser usados.** Só se removem depois da Fase 4, para o deploy nunca ficar sem caminho.
- **A ADR 010** (`main` sem proteção) segue valendo: a proteção de branch continua indisponível no plano Free.
- **Sobre tornar o repositório privado:** fora desta ADR. Esta decisão **permite** fazê-lo sem pagar assento, porque tira do GitHub o
  que dependia do plano pago.

### Adendo de 22/10/2026 (repositório já privado)

O repositório foi tornado privado e isso muda três pontos desta seção:

- **(a)** O build do Cloud Build não tem credencial do GitHub nas etapas. A `main` e as APIs do GitHub exigem um token de leitura
  vindo do Secret Manager (decisão D1 do plano de CI/CD completo, `docs/superpowers/plans/2026-10-22-cicd-completo-sem-actions.md`).
- **(b)** O CI deixa de ser "só escreve log" e passa a ler **um** segredo: o do App de leitura do GitHub. Nenhum outro segredo
  entra no pipeline, e o segredo nunca aparece em código, log ou fixture (regra 2).
- **(c)** Custo estimado do CI/CD completo no Cloud Build: cerca de 1.260 minutos por mês, abaixo da franquia de 2.500 minutos
  (seção Custo do plano). É estimativa, não medição. A primeira fatura confirma. O Painel é o maior consumidor; se apertar, volta
  para a cadência de 6 em 6 horas.

## 5. Fases

Cada fase termina com o caminho antigo ainda funcionando, e só a Fase 4 o desliga. O detalhe está em
[`superpowers/plans/2026-10-15-migracao-cicd.md`](../../superpowers/plans/2026-10-15-migracao-cicd.md).

| Fase | O quê | Pré-requisito humano |
|---|---|---|
| 0 | Pipeline portátil: `make ci` e alvos por etapa; reduzir minutos do Actions | nenhum |
| 1 | CI de PR no Cloud Build, em paralelo ao Actions | instalar o app do Cloud Build no GitHub |
| 2 | Deploy e operações sob demanda no Cloud Build | Fase 1 |
| 3 | Agendados no Cloud Scheduler | Fase 2 |
| 4 | Desligar o Actions, remover WIF e ambientes do GitHub | Fases 1 a 3 estáveis por uma semana |
