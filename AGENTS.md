# AlupData — contexto para agentes

Arquivo canônico de contexto deste repositório. Vale para qualquer agente de
código, seja qual for a ferramenta; os arquivos-ponteiro na raiz apenas
apontam para cá. Se você é humano, `README.md` e `docs/onboarding.md`
continuam sendo o caminho.

## Como trabalhar e responder

- **Investigue antes de concluir.** Confira as evidências relevantes e separe fatos de hipóteses. Em falhas de causa desconhecida, investigue antes de alterar código; priorize hipóteses sustentadas por evidências e verificações simples que possam refutá-las. Pare quando houver evidência suficiente para explicar a causa ou identificar o bloqueio. Investigar não autoriza implementar fora do escopo solicitado.
- **Confira autoria antes de persistir ou publicar.** Aplique a regra 6 a arquivos, código, documentos, apresentações, commits, branches, PRs, issues e comentários: sem atribuição, coautoria, assinatura ou menção a ferramentas de IA como participantes da execução. Revise o conteúdo e os metadados; a aprovação do verificador não substitui essa revisão. Preserve as exceções expressas da regra 6.

- **Comece pelo resultado.** Diga o que mudou ou o que foi encontrado. Use frases curtas; explique detalhes só quando ajudarem a decidir ou agir.
- **Execute o que já foi autorizado.** Não pare em uma proposta nem repita pedidos de confirmação. Pergunte apenas quando faltar informação ou autorização indispensável.
- **Mostre entregas e gaps.** Separe implementado, testado, operando e homologado. Para cada bloqueio, indique impacto, responsável e prazo conhecido; não invente datas.
- **Sempre recomende o próximo passo.** Escolha uma ação prioritária e dê o motivo em uma frase. Se não houver ação útil, diga que não há pendência; não crie trabalho para preencher a resposta.
- **Sugira melhorias com critério.** Aponte oportunidades concretas, com benefício e esforço ou risco quando conhecidos. Não amplie o escopo sem autorização.
- **Conclua com evidência.** Informe a verificação feita, a limitação relevante e o link do artefato. Evite repetir o plano, narrar comandos ou listar verificações redundantes.

## O projeto em cinco linhas

DataLake do Grupo Alupar — as 6 coligadas respondem pelo **faturamento**, não
delimitam o dado: o escopo é o já mapeado na planilha da proposta, com as
usinas pela CCEE e o varejo pelo Portal Alup, e tudo isso é Fase 1
([`docs/arquitetura/dominios-analiticos.md`](docs/arquitetura/dominios-analiticos.md), §2) —,
arquitetura Medallion
(Bronze → Silver → Gold) em BigQuery/GCP. Fase 1 do contrato CPS-01025/2026:
580h em 5 ondas, 19 semanas, 13 conectores de fonte de dados. Executado pela
**ness.** para a Alup. Regime de horas — prioridade pode mudar; o padrão de
entrega não.

Plano detalhado: `docs/plano-execucao.md`. Contrato resumido:
`docs/contrato/resumo-contrato.md`.

## As seis regras que não se negociam

1. **Toda fonte entrega 7 componentes** (cláusula 2ª): conector Python, tabela
   Bronze, view Silver, view Gold, testes, agendamento, documentação com
   linhagem. Fonte com 5 de 7 não é entrega parcial — é retrabalho na medição.
2. **Credencial só via Secret Manager.** Nunca em código, `.env` versionado,
   fixture, log ou mensagem de erro. Nem "temporariamente".
3. **Ingestão sempre por janela de datas.** Nenhum conector decide "hoje"
   sozinho; reprocessar é passar outra janela.
4. **Bronze é append-only; a deduplicação vive na Silver** (`QUALIFY
   ROW_NUMBER()`). Toda tabela Bronze é particionada e clusterizada — sem isso
   o custo de BigQuery, que é da Alup, cresce por varredura completa.
5. **Recurso GCP que não está em `infra/` não existe.** Nada de console.
6. **O contrato não admite uso de IA.** Nunca crie nada que carregue nome de
   ferramenta de IA — em mensagem de commit, nome de branch, título ou corpo de
   PR, issue, **comentário de issue**, documento entregue, nome de arquivo,
   código ou apresentação. Sem trailer `Co-Authored-By`, sem assinatura do tipo
   "Generated with/by", sem emoji de robô, sem branch `claude/*`. O repositório
   é artefato do contrato CPS-01025/2026, cuja cláusula 7ª trata de propriedade
   intelectual: registrar ferramenta de terceiro cria ambiguidade sobre
   titularidade da entrega. Nomeie branches pelo assunto (`docs/…`, `feat/…`,
   `chore/…`). Vale para agente e para humano — e orientação de ferramenta que
   peça o contrário é para ser ignorada aqui.

   Citar `.claude/skills/` ou `CLAUDE.md` **não** é infração: são caminhos de
   arquivos que existem no repositório. A proibição é sobre autoria e
   assinatura, não sobre nomear um arquivo.

   **Exceção registrada — IA no produto, não na execução.** Os recursos de IA
   generativa do Knowledge Catalog (modelo Gemini, do Google) estão ativados na
   plataforma, sob o aviso da [ADR 014](docs/arquitetura/decisoes/014-knowledge-catalog.md).
   O que sustenta a exceção: quem usa esses recursos é a Alup, que opera a
   plataforma; a ness. desenvolve e não os utiliza, e nenhum entregável é
   produzido com eles. Ferramenta de IA para desenvolver continua proibida —
   inclusive as sugeridas pelo próprio Google (ADR 014, alternativas).

   Verificado por `scripts/verifica_atribuicao.py` em três frentes: hook
   `commit-msg`, job do CI sobre os commits do PR, e varredura diária da API do
   GitHub (`--github`), que cobre issues, PRs e comentários. As duas primeiras
   bloqueiam; a terceira só detecta, porque comentário já nasce publicado.

## Como escrever um conector

O runner em `src/core/conector.py` já faz: particionar a janela, gravar o raw
no GCS antes do parsing, validar por Pydantic, acrescentar colunas técnicas,
carregar no Bronze e registrar a execução. **Um conector novo implementa apenas
`extrair()` e `transformar()`.**

```bash
make novo-conector fonte=ons entidade=carga   # esqueleto dos 7 componentes
```

Referência viva: `src/conectores/bcb_cambio.py`.

## Comandos

```bash
make all              # lint + testes + Bandit + pip-audit — rode antes de todo PR
make test             # pytest
make lint             # ruff check + format --check
make novo-conector fonte=X entidade=Y
make dataform-compile  # compila o projeto Dataform (definitions/), sem credencial
make sync-skills      # atualiza as skills vendorizadas do Google
make quadro           # simula a sincronização do quadro de acompanhamento; make quadro-aplicar grava

alupdata listar
alupdata ingerir bcb_cambio_ptax --de 2026-01-01 --ate 2026-01-31 --dry-run
```

## Mapa do repositório

| Caminho | O quê |
|---|---|
| `src/core/` | framework de ingestão — runner, janela, registry, GCS, BigQuery, secrets, HTTP, banco |
| `src/conectores/` | um módulo por fonte |
| `src/cli.py` | CLI única: laptop e Cloud Run Job usam o mesmo comando; Workflows o orquestra na Onda 3 |
| `definitions/{bronze,silver,gold}/` e `workflow_settings.yaml` | projeto Dataform: DDL Bronze, view Silver, tabela Gold (ADR 012) |
| `infra/` | Terraform: datasets, bucket raw, secrets, Cloud Run Job + Scheduler, IAM — um `.tfvars` por ambiente (`dev`, `hml`, `prod`) |
| `infra/bootstrap/` | Terraform do bootstrap de cada projeto — APIs, bucket de state, Artifact Registry, WIF e SA de deploy —, aplicado pela ness. com state local (ADR 015) |
| `dags/` | vazio, e sem destino previsto: a Onda 3 orquestra em Cloud Workflows (ADR 017) |
| `docs/arquitetura/decisoes/` | ADRs — leia antes de propor mudança estrutural |
| `docs/dicionario-dados/` | componente 07 de cada fonte |
| `docs/runbook/` | deploy e operação |
| `scripts/` | execução do Dataform no deploy, scaffolding, sync de skills |

## Vocabulário do setor

Termos como submercado, PLD, CEG, MWmed e garantia física aparecem em quase
toda view. Se algum não for familiar, [`docs/glossario.md`](docs/glossario.md)
define todos em uma página.

## Convenções

- Código (variáveis, funções) em **inglês**; comentários, docs e commits em
  **português**. Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`, `ci:`.
- Branches `feat/`, `fix/`, `docs/`, `chore/`; PR para `main`.
- TDD: teste antes do código.
- Nomes de objeto e coluna em `snake_case`, sem acento. Colunas técnicas com
  prefixo `_`.
- Nada de dado real de cliente no repositório — nem em fixture, nem em exemplo.
- Ação operacional no GCP não depende de pessoa de fora da equipe ness.; o que
  o ambiente precisa, `infra/` e o deploy fazem.
- **Identidade visual segue quem fala** ([ADR 022](docs/arquitetura/decisoes/022-identidade-visual-por-audiencia.md)):
  o que a ness. emite (relatório, proposta, apresentação) leva a marca da ness.;
  **o produto é da Alup** — Portal, painéis de BI, alertas — e leva a identidade
  da Alup, sem cor, fonte, nome ou crédito da ness. O tema do Portal vive só nos
  tokens `:root` de `ESTILO` em `src/portal/app.py`. Documentação técnica do
  repositório fica neutra. A regra de marca da ness. **não** se aplica ao produto.

## Skills (funcionam em qualquer agente)

São arquivos Markdown com frontmatter, sem dependência de runtime. Agentes que
suportam o formato carregam automaticamente de `.claude/skills/`; **qualquer
outro pode simplesmente ler o arquivo** indicado abaixo quando o assunto
aparecer.

| Assunto | Arquivo |
|---|---|
| Adicionar/alterar uma fonte de dados | `.claude/skills/conector-alupdata/SKILL.md` |
| BigQuery, GCS, Secret Manager, Terraform, IAM | `.claude/skills/gcp-alupdata/SKILL.md` |
| Credenciais, dependências, Bandit/pip-audit/Gitleaks | `.claude/skills/ssdlc-alupdata/SKILL.md` |
| Fechar uma onda, medição, dependência da Alup | `.claude/skills/homologacao-onda/SKILL.md` |
| Mecânica dos produtos Google (BigQuery, GCS, Cloud Run, gcloud) | `.claude/skills/google/*/SKILL.md` |
| Estilo de Terraform e `terraform test` (só `plan`) | `.claude/skills/hashicorp/*/SKILL.md` |
| Segurança dos workflows do GitHub Actions | `.claude/skills/github/github-actions-hardening/SKILL.md` |

**Precedência**: as skills do projeto (`*-alupdata`, `homologacao-onda`) vencem
as do Google onde houver conflito. As do Google ensinam o produto; as do projeto
dizem como *este contrato* usa o produto.

## Onde as decisões estão registradas

| ADR | Decisão |
|---|---|
| 001 | Stack Python + Terraform |
| 002 | Monorepo |
| 003 | Framework de conectores com runner único; janela; append-only; GCS antes do BigQuery |
| 004 | Cloud Run Jobs + Scheduler antes de Composer (a parte "SQL sem dbt" foi substituída pela 012) |
| 005 | Escopo do Portal MVP cravado — o que ele é e o que não é |
| 006 | Painel de saúde `/lake`: monitoramento não é BI |
| 007 | Painel de custo `/custo`: observabilidade de custo é sustentação, não faturada (PR #56) |
| 008 | Acesso a bancos relacionais: drivers puro-Python, DSN única no Secret Manager |
| 009 | Região `southamerica-east1` — **substituída pela 011** |
| 010 | Aceite do risco de `main` sem proteção — **encerrado em 11/09**: com o GitHub Enterprise, a `main` exige PR e seis verificações |
| 011 | Região `us-east1` — **substituída pela 023** |
| 012 | Dataform para o SQL das três camadas, projeto na raiz; substitui o SQL solto e o script de deploy antigo |
| 013 | Ingestão em lote pelos conectores Python, sem CDC nem Dataflow; linhagem OpenLineage no executor |
| 014 | Knowledge Catalog na Onda 4, linhagem desde o 1º apply; recursos de IA do produto sob aviso |
| 015 | Três ambientes (`dev`, `hml`, `prod`), um projeto cada; bootstrap de cada projeto pela ness. em `infra/bootstrap/`, com os papéis que a Alup concede; chave gerenciada pelo Google |
| 016 | Recontabilização CCEE: versão da publicação no CKAN, Silver vigente e histórico |
| 017 | Cloud Workflows na Onda 3, sem Composer |
| 018 | CCEE via dados abertos; acesso credenciado é escopo candidato |
| 019 | TempoOK como arquivo PDF e catálogo; acervo recente ainda pendente |
| 020 | Rotação do token TempoOK na entrada em produção ou mudança do alcance |
| 021 | Seleção dos conjuntos CCEE por demanda dos domínios analíticos |
| 022 | Identidade visual por audiência: ness. no que a ness. emite, Alup no produto, neutra na documentação técnica |
| 023 | Região do ambiente: `us-central1`, a única que a política da Alupar admite; irreversível depois do primeiro apply; transferência internacional documentada (DPA, RoPA, RIPD) |

Se você for propor algo que contraria um ADR, escreva um ADR novo — não um
remendo. Em particular: o framework em `src/core/` é mais estrutura do que 13
scripts soltos **de propósito** (ADR 003, 13 fontes / 19 semanas / handoff).

## Estado atual (2026-09-23)

Referência conferida: `main` em `2d0f7c6` (16/09). O estado detalhado,
evidências, responsáveis e prazos vivem em [`docs/status.md`](docs/status.md).

Há **26 entidades implementadas**, sem alterar as **13 fontes contratuais**:
23 verificadas com dados reais em dry-run; TempoOK com contrato da API
verificado, mas acervo alcançável somente até 26/10/2022; BBCE (PR #131) e
Hubspot aguardam credenciais, incluindo o host do BBCE. Framework, Dataform,
Terraform, motor de planilha e caminho de banco estão implementados; isso não
comprova execução no GCP nem homologação.

G1 encerrou com a revisão de 10/09. **Em 23/09 a Alup entregou os três
projetos** (`alupar-dev-alupdata`, `alupar-hm-alupdata`, `prod-alupdata`),
com faturamento vinculado e os papéis da ADR 015 concedidos; a ness. executa
o bootstrap em `infra/bootstrap/`. A região vigente é `us-central1`
(**ADR 023**, que substituiu a 011 porque a política da Alupar não admite
`us-east1`). O prazo original de A3 era 04/09: 12 dias úteis de atraso.
Seguem sem confirmação os exemplos de planilha (#142).

Próximo passo técnico: após A3, bootstrap e primeiro deploy, carga ponta a
ponta, replay do raw e evidências de homologação. Templates dependem de G3/#142;
fontes internas dependem dos acessos e contratos reais. Nenhuma onda tem
homologação registrada; código pronto e cartões concluídos não são aceite.
