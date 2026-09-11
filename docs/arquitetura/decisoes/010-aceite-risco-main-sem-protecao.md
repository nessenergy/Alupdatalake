# ADR 010 — Aceite formal do risco de `main` sem proteção obrigatória

**Status**: **encerrado** pela revisão de 2026-09-11 — a `main` passou a ser
protegida · **Data**: 2026-09-08

## Contexto

A `main` deste repositório não tem proteção: aceita push direto, sem revisão
obrigatória e sem exigir que o CI passe. Isso está levantado desde 31/08 na
[issue #68](https://github.com/nessenergy/Alupdatalake/issues/68).

Não é configuração esquecida. A organização `nessenergy` está no **GitHub Free**
com repositório privado, e tanto `branch protection` quanto `rulesets` respondem
403:

```
GET /repos/nessenergy/Alupdatalake/branches/main/protection
{"message":"Upgrade to GitHub Pro or make this repository public to enable this feature.","status":"403"}
```

Não há terceira via técnica. Hook local e job de CI rodam **depois** que o commit
já está na branch — nenhum dos dois impede o push. Tornar o repositório público
está descartado: é artefato de contrato, e a cláusula 7ª trata de propriedade
intelectual.

O que está em jogo é a **cláusula 8ª**, que exige SSDLC com SAST e SCA no
CI/CD. O CI existe e roda em toda PR — Ruff, pytest, Bandit, pip-audit, Gitleaks
e Terraform, sete jobs. Mas ele **não impede** nada. Um pipeline que qualquer
pessoa com acesso de escrita pode contornar é verificação, não portão. Isso não
é hipotético: houve force-push na `main` em 29/08 e nada o impediu.

As saídas levantadas na #68 eram três: migrar para GitHub Team, aceitar o risco
por escrito, ou tornar o repositório público.

## Decisão

**A ness. aceita formalmente o risco**, mantendo o plano GitHub Free por ora, em
vez de migrar para o GitHub Team nesta fase.

Quem assume: **ness.**, pelo responsável técnico do contrato, **Ricardo Esper**
(`resper@ness.com.br`).

O aceite vale enquanto durar a condição que o justifica — equipe de um
desenvolvedor e Fase 1 em curso. Ele **não** é permanente e é revisto nos
gatilhos da seção seguinte.

### Por que aceitar em vez de migrar agora

A equipe de desenvolvimento é de uma pessoa. Revisão obrigatória de PR por
terceiro, que é o principal ganho do portão, não tem quem a exerça hoje — a
proteção impediria o push direto, mas a revisão continuaria sendo autorrevisão.
O risco residual real, nesta configuração, é menor do que o controle sugere.

## Consequências

**O que passa a valer, por convenção e não por imposição da plataforma:**

- Toda alteração continua entrando por PR, inclusive as de quem tem acesso de
  escrita. Push direto na `main` não acontece.
- O CI segue rodando em toda PR, com os sete jobs, e PR com job vermelho não é
  mesclada.
- Branches nomeadas pelo assunto, conforme a regra do `AGENTS.md`.

**O que precisa ser dito com honestidade em qualquer documento de homologação:**

O dossiê de homologação da Onda 0 **não pode afirmar que existe portão
preventivo** de SAST/SCA. O que existe é varredura executada em toda PR, sem
bloqueio de bypass. Afirmar conformidade preventiva com a cláusula 8ª seria
declaração falsa. A redação correta descreve o arranjo real: varredura
sistemática em toda PR, mais este aceite de risco registrado.

**Gatilhos que reabrem a decisão — qualquer um deles obriga a reavaliar:**

1. **Entrada de um segundo desenvolvedor** no repositório. A partir daí a
   revisão por terceiro passa a ser exercível, e o argumento desta ADR cai.
2. **Exigência formal da Alup** de portão preventivo, em auditoria ou no aceite
   da Onda 0.
3. **Qualquer push direto na `main`** que venha a ocorrer. Um único evento já
   demonstra que a convenção não se sustenta sozinha.
4. **Início da Onda 3**, quando credencial de sistema interno da Alup passa a
   circular na configuração do projeto e o custo de um vazamento sobe.

**Controle detectivo sugerido, não implementado por esta ADR:**

Auditoria periódica dos commits da `main` para conferir que todos vieram de PR
mesclada, e execução agendada da mesma varredura de SAST e SCA contra a `main`.
Não substitui o portão — detecta em vez de impedir —, mas fecha a lacuna de
não haver nenhuma verificação após um eventual push direto. Fica como item de
fila, não como parte do aceite.

## Revisão de 2026-09-11 — o aceite de risco está encerrado

A condição que justificava o aceite caiu: a organização `nessenergy` passou a
usar **GitHub Enterprise**, e com isso `rulesets` funcionam em repositório
privado. O que respondia 403 em 08/09 hoje responde.

A `main` passou a ser protegida pelo ruleset `main_protect-alupdata`, ativo:

- **pull request obrigatória**, com zero aprovações exigidas — o portão é o CI,
  não a revisão por terceiro, que continua sem quem a exerça;
- **seis verificações obrigatórias**: Testes pytest, Lint & Formatação, SAST
  (Bandit), Detecção de Secrets, Terraform Validate e Dataform Compile;
- **force push e exclusão bloqueados**;
- **lista de exceção vazia**: a regra vale inclusive para administradores.

O que isso muda:

- **Push direto na `main` deixou de ser possível.** O que era convenção virou
  imposição da plataforma, e o gatilho 3 desta ADR perde o objeto.
- **O dossiê de homologação muda de redação.** Passa a existir portão
  preventivo de SAST e SCA para o que entra por PR, e a cláusula 8ª é atendida
  por bloqueio, não só por varredura. A ressalva honesta de 08/09 sobre
  "varredura sem bloqueio" deixa de valer para os seis jobs exigidos.
- **Duas verificações continuam detectivas, não preventivas:** "Commits sem
  atribuição a IA" e "Auditoria de Dependências" ficaram fora da lista de
  obrigatórias porque são puladas em alguns contextos e travariam a fila de PR
  esperando por um resultado que não vem. Elas seguem rodando e reprovando a PR
  quando encontram problema, mas não impedem o merge sozinhas. Torná-las
  obrigatórias exige antes ajustar os workflows para sempre reportar.
- **O gatilho 1 continua valendo:** com um segundo desenvolvedor, cabe revisar
  se a exigência passa a ser de uma aprovação por terceiro.

## Referências

- [issue #68](https://github.com/nessenergy/Alupdatalake/issues/68) — levantamento original
- Contrato CPS-01025/2026, cláusulas 7ª e 8ª
- [`docs/status.md`](../../status.md) — painel de dependências, linha de branch protection
