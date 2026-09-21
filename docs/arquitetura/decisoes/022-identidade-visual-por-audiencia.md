# ADR 022 — A identidade visual segue quem fala, não quem produz

**Status**: aceito · **Data**: 2026-09-21 · **Complementa** a
[ADR 005](005-escopo-do-portal-mvp.md) (escopo do Portal)

## 1. Contexto

A ness. desenvolve o AlupData e tem uma identidade visual própria, obrigatória em
todo material que emite. A Alup é dona do produto (cláusula 7ª), e quem vai usá-lo
e mantê-lo depois do handoff é a equipe dela.

Sem uma regra, as duas identidades se misturavam. Em 21/09 o Portal tinha três
mundos visuais ao mesmo tempo: as telas `/lake` e `/custo` com uma paleta derivada
do site da Alup, a tela `/` com fonte do sistema e o azul da ness. (`#00ADE8`), e
um texto na tela de custo dizendo que os domínios eram "proposta da ness." — que,
além de pôr o fornecedor dentro do produto, deixara de ser verdade em 14/09, quando
os domínios passaram a vir da resposta B1 da própria Alup.

## 2. Decisão

**A identidade visual segue quem fala e quem é dono, não quem produziu.**

| Quem fala / quem é dono | Identidade | Exemplos |
|---|---|---|
| **A ness. falando com a Alup** | ness. | Relatórios (`docs/relatorios/`), propostas, apresentações (`docs/apresentacoes/`), registros e e-mails da contratada |
| **O produto da Alup, usado pelo pessoal da Alup** | **Alup** | Portal (`src/portal/`), painéis de BI alimentados pelas Gold, e-mails de alerta que o usuário recebe, catálogo de dados |
| **Documentação técnica do repositório** | Neutra, sem marca | Runbooks, dicionário de dados, ADRs, README — Markdown no GitHub, que segue no handoff |

**O produto não leva crédito da ness.** — nem em tela, nem em rodapé. Se a Alup
quiser o crédito, ele cabe na documentação de handoff, não nas telas.

## 3. De onde vem a identidade da Alup

Do **design system da Alup**, construído pela ness. a partir do brandbook da Alup
e validado por ela. Até ele chegar ao repositório, o Portal usa a paleta derivada
do site da Alup que já estava nas telas `/lake` e `/custo` — é provisória, e está
concentrada num lugar só (item 4) para ser trocada de uma vez.

## 4. Como isso vale no código

- **O visual do Portal vive em tokens**, no bloco `:root` de `ESTILO`
  (`src/portal/app.py`), no formato do shadcn/ui. É ali que o design system da Alup
  entra: trocar o tema é trocar valores, não reescrever telas.
- **Todas as telas do Portal usam o mesmo `ESTILO`.** Tela com estilo próprio é como
  a divergência começa — foi o que aconteceu com a `/`.
- **Nenhuma cor, fonte ou menção da ness. no Portal.** Vale para o que um agente
  gerar também: a regra de marca da ness. se aplica ao que a ness. emite, não ao
  produto que ela entrega.
- **Painéis de BI** (Power BI na Fase 1, resposta A6) recebem um tema com os tokens
  do mesmo design system, quando ele existir.
- **Relatórios** continuam no gerador `scripts/gerar_documento.py`, com a
  identidade da ness.

## 5. Consequências

- A tela `/` passa a usar o `ESTILO` compartilhado; sai o azul da ness.
- O texto sobre os domínios na tela de custo é corrigido: eles vêm da resposta B1
  da Alup, com dono nomeado por domínio.
- Aplicar o design system da Alup vira uma tarefa rastreada
  ([#177](https://github.com/nessenergy/Alupdatalake/issues/177)), dependente de o
  design system ser concluído e validado pela Alup.
- A regra entra em `AGENTS.md`, para que qualquer pessoa ou agente que trabalhe no
  repositório a encontre antes de desenhar uma tela.
