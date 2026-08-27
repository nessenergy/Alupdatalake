# ADR 007 — Painel de saúde como entrega faturável

**Status**: proposto · **Data**: 2026-08-27 · **Revê**: [ADR 006](006-painel-de-saude.md)

> **Proposto, não aceito.** As ADRs anteriores registram decisões técnicas, que
> a ness. toma sozinha. Esta tem efeito comercial sobre um contrato assinado, e
> só passa a "aceito" com aceite interno da ness. e formalização com a Alup.
> Enquanto estiver como proposta, **vale a ADR 006**: o painel segue sem
> cobrança.

## Contexto

A [ADR 006](006-painel-de-saude.md) construiu o painel `/lake` e fechou com
esta frase, hoje commitada no repositório:

> Não é escopo faturado da Fase 1: é ferramenta da ness. para tornar a
> sustentação viável dentro da franquia de 20h/mês. Não vira item de medição
> nem estende o item 0.15.

A pergunta que abre esta ADR é se essa classificação foi correta. Ela merece ser
feita, mas a resposta precisa começar reconhecendo a força do argumento original
— senão isto vira racionalização de cobrança, que é pior que não cobrar.

**O que a ADR 006 acertou.** A cláusula 10ª inclui *monitoramento* no escopo de
sustentação. Um painel que serve para a própria ness. monitorar dentro da
franquia é ferramenta de trabalho, não entrega — do mesmo modo que o
`make novo-conector` não é item de medição. E o painel não mostra dado de
cliente: mostra `bronze._execucoes`, o log do próprio pipeline.

**O que mudou.** Nada nos fatos técnicos. O que mudou é que a classificação foi
feita no momento de construir, quando a pergunta era "isto cabe na sustentação?",
e não no momento de medir, quando a pergunta é "quem recebeu o quê?". São
perguntas diferentes e podem ter respostas diferentes sem contradição.

## A distinção que sustenta a revisão

A ADR 006 tratou "ferramenta de sustentação" e "entrega ao cliente" como
mutuamente exclusivas. Não são. O painel é as duas coisas ao mesmo tempo:

| Dimensão | Ferramenta interna | Entrega |
|---|---|---|
| Quem usa | a ness., para caber em 20h/mês | a Alup, para saber se o lake está confiável |
| Onde roda | ambiente da Alup | ambiente da Alup |
| De quem é o código | da Alup — **cláusula 7ª, propriedade intelectual** | idem |
| Quem paga a infra que o serve | a Alup — cláusula 5ª | idem |

As três últimas linhas são o ponto. Um `Makefile` fica na máquina de quem
desenvolve; o `/lake` roda no Cloud Run **da Alup**, consumindo infra **paga
pela Alup**, e o código é propriedade **da Alup** pela cláusula 7ª. Isso não é
ferramenta interna — é software entregue que por acaso também usamos.

O teste prático: se a ness. saísse do contrato amanhã, o `make novo-conector`
não faria falta a ninguém; o `/lake` continuaria sendo a única resposta à
pergunta "a ingestão de ontem funcionou?" para quem ficasse. O que sobrevive à
saída do fornecedor é entrega.

## Decisão

Reclassificar o painel de saúde — `gold.saude_ingestao`,
`gold.volumetria_lake`, a rota `/lake` e o painel do Cloud Monitoring — como
**entrega de valor não prevista no contrato**, reconhecida e precificada.

## Decisão — o mecanismo: aditivo, não remedição

O mecanismo importa mais que a classificação, e aqui a ADR 006 continua certa
num ponto específico: **"não vira item de medição nem estende o item 0.15"
permanece válido.**

Reabrir a medição da Onda 0 seria mexer em marcos e percentuais já acordados
(90h, 15,52%), a partir de trabalho já feito e sem pedido prévio. Isso é o pior
formato possível — tem cara de conta que aparece depois — e coloca em risco uma
homologação que já está travada por A3–A6.

O painel entra, então, como **item de um aditivo**, junto do FinOps
([`../../contrato/aditivo-finops.md`](../../contrato/aditivo-finops.md)),
apresentado com o esforço real que consumiu, não com preço inventado depois.

Três formatos possíveis, em ordem de preferência:

1. **Reconhecido e não cobrado, com registro escrito.** Entra na medição como
   entrega adicional a custo zero, explicitamente nomeada. Não gera receita,
   gera credibilidade — e cria o precedente de que valor fora de escopo é
   *nomeado* em vez de absorvido em silêncio. É o que preserva melhor a relação.
2. **Cobrado dentro do aditivo de FinOps**, como observabilidade já entregue que
   reduz o esforço da camada A (o `/lake` já resolveu o padrão de tela, o SVG do
   servidor e a exceção de teste que o `/custo` vai reusar). Tecnicamente
   honesto e comercialmente defensável.
3. **Cobrado isoladamente.** Não recomendado: é a versão com pior relação entre
   receita e atrito.

**Recomendação: formato 1 se o aditivo de FinOps for adiante; formato 2 se não
for.** O painel vale mais como demonstração do que a ness. entrega além do
pedido do que como linha de fatura — e essa demonstração é o que sustenta a
conversa do aditivo.

## Riscos

- **A Alup pode ter lido a ADR 006.** O repositório é dela (cláusula 7ª) e o
  texto diz "não é escopo faturado" sem ressalva. Chegar depois cobrando o mesmo
  item é o cenário ruim. Mitigação: esta ADR não apaga a 006 — declara a revisão
  e a data, e o formato 1 torna a conversa uma cortesia registrada, não uma
  cobrança retroativa.
- **Precedente de escopo elástico.** Se "ferramenta interna" pode virar entrega
  faturável depois, a ADR 005 perde força — ela existe justamente para conter o
  crescimento silencioso do Portal (risco R5 do plano). Mitigação: a
  reclassificação vale para este item, com a justificativa da tabela acima, e
  **não** estabelece regra geral. Ferramenta que roda na máquina de quem
  desenvolve continua sendo ferramenta.
- **Momento ruim.** A Onda 0 está travada por A3–A6, todas pendências da Alup.
  Levantar cobrança nova enquanto se cobra insumo pode ler como pressão. O
  formato 1 é o que menos sofre desse risco.

## Consequências

- A ADR 006 **não é revogada**: sua decisão técnica (o que o painel mostra, como
  o atraso é medido, lógica no SQL, visual sem React) continua íntegra. Só a
  frase de classificação comercial da seção "Consequências" é revista aqui.
- Enquanto esta ADR estiver como **proposta**, nada muda na prática. Se for
  recusada, ela permanece no repositório como registro de que a questão foi
  levantada e decidida — que é para isso que servem ADRs.
- Se aceita, `docs/status.md` passa a listar o painel como entrega reconhecida,
  e não como "ferramenta de sustentação, não escopo faturado".
