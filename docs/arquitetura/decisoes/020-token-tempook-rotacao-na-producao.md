# ADR 020 — O token do TempoOK é mantido até a virada de produção

**Status**: aceito · **Data**: 2026-09-14 · **Complementa** a
[ADR 019](019-boletim-do-tempook-como-arquivo.md) · **Encerra-se** na virada de
produção ou num dos gatilhos da seção 5

## 1. Contexto

O token do TempoOK chegou em **14/09/2026 em texto claro no corpo de um
e-mail**, com seis destinatários entre remetente, cópia e destinatários
diretos. Um segredo que trafega assim permanece nas caixas postais, nos
servidores de trânsito e em qualquer cópia local — e não há como auditar onde
parou. Apagar a mensagem não desfaz nada.

O [registro de 14/09](../../relatorios/2026-09-14-documentacao-de-apis-recebida.md)
recomendou rotacioná-lo. Esta ADR registra a decisão de **não rotacionar
agora**, e por quê.

## 2. Decisão

**O token atual é mantido em uso até a virada de produção.** A rotação acontece
nesse momento, não antes.

Quem assume: **ness.**, pelo responsável técnico do contrato, **Ricardo Esper**
(`resper@ness.com.br`).

Até lá o token vive no cofre local descrito em
[`runbook/credenciais.md`](../../runbook/credenciais.md) — fora do repositório,
com as três travas que impedem que ele chegue a um commit ou a produção.

## 3. Por que adiar é melhor que rotacionar agora

O argumento decisivo não é custo nem conveniência:

> **Rotacionar hoje reproduziria exatamente a mesma exposição.** O Secret
> Manager não existe (pendência A3). O token novo teria de ser entregue pelo
> mesmo canal que se está tentando abandonar — e-mail —, e o resultado seria
> duas credenciais expostas em vez de uma.

Rotacionar **na virada de produção** significa rotacionar quando já existe
destino próprio: a Alup grava o valor novo direto no Secret Manager, e ele
**nunca trafega por e-mail**. Uma rotação, feita uma vez, que de fato encerra a
exposição em vez de renová-la.

Três fatos sustentam que a espera é segura:

1. **O alcance do token é pequeno e está medido.** Ele permite baixar boletins
   diários em PDF, somente leitura, e — como a ADR 019 verificou — **apenas até
   26/10/2022**. Não há escrita, não há dado pessoal, não há sistema
   transacional atrás. Quem o obtivesse teria um acervo de 2022 de um boletim de
   mercado que a Alupar assina.
2. **Não há nada em produção para proteger.** Sem projeto GCP, sem ambiente e
   sem carga real, o token não dá acesso a nenhum ativo do contrato — só ao
   acervo do próprio fornecedor.
3. **A conversa com o TempoOK já é necessária por outro motivo.** A pendência
   A10 pergunta por que o acervo para em 2022. Rotação e acervo são a mesma
   conversa com o mesmo fornecedor; separá-las custaria dois ciclos para
   resolver o que um resolve.

## 4. O que esta ADR **não** decide

- **Não vale para as credenciais seguintes.** BBCE, Hubspot e as bases da Onda
  3 devem ir **direto ao Secret Manager** assim que ele existir, sem passar por
  e-mail. A recomendação de canal do registro de 14/09 segue integralmente de
  pé — ela é sobre o futuro, e não foi adiada.
- **Não dispensa a rotação; move a data.** A exposição existe e continua
  existindo até a virada. O que muda é que ela passa a ter fim marcado, em vez
  de ser renovada.
- **Não altera as travas do cofre local.** Elas continuam sendo o que impede o
  token de chegar ao repositório ou ao Cloud Run.

## 5. Gatilhos que encerram o aceite antes da produção

O aceite vale enquanto valerem as condições que o justificam. Qualquer um
destes o encerra, e a rotação passa a ser imediata:

| # | Gatilho | Por quê |
|---|---|---|
| 1 | **O acervo recente passa a ser alcançável** (A10 resolvida) | o token deixa de dar acesso a um arquivo de 2022 e passa a dar acesso ao dado corrente de mercado da Alupar. A sensibilidade muda de patamar |
| 2 | **A Alup pedir a rotação** | é dela a relação com o fornecedor e o dado; a decisão da ness. não se sobrepõe |
| 3 | **Indício de uso indevido** — cobrança, volume ou acesso que a Alupar não reconheça | não se espera prazo diante de evidência |
| 4 | **O token passar a valer para outro produto do TempoOK** que não o boletim | o alcance medido no item 3.1 deixaria de descrever a realidade |

## 6. Como isso é cobrado no momento certo

Decisão adiada que ninguém carrega vira decisão esquecida. O aceite está
amarrado em três lugares, de propósito:

- **checklist de virada de produção**, em
  [`runbook/credenciais.md`](../../runbook/credenciais.md) — é onde a ação
  acontece;
- **fila de execução**, item 2.7 de
  [`proximos-passos.md`](../../proximos-passos.md);
- **`status.md`**, junto da pendência A10, que é a conversa em que a rotação
  deve entrar.

## 7. Consequências

- O `dicionario-dados/tempook_boletins.md` e a ADR 019 deixam de dizer
  "rotacionar antes do primeiro uso" e passam a apontar para cá.
- O registro de 14/09 à contratante — **ainda não emitido** — passa a pedir a
  rotação **para a virada de produção**, explicando por que não antes. O pedido
  de mudança de canal para as próximas credenciais continua no mesmo lugar.
- Na homologação, esta ADR é a resposta auditável à pergunta "havia credencial
  exposta e o que foi feito": houve, foi identificada no mesmo dia, o alcance
  foi medido, a decisão foi registrada com dono e a rotação tem data e
  gatilhos.

## Referências

- [ADR 019](019-boletim-do-tempook-como-arquivo.md) — alcance do token, medido em 14/09
- [`runbook/credenciais.md`](../../runbook/credenciais.md) — cofre local e travessia
- [Registro de 14/09](../../relatorios/2026-09-14-documentacao-de-apis-recebida.md) — §4.1 e §5
- Contrato CPS-01025/2026, cláusula 8ª

---

## Adendo de 21/09/2026 — os gatilhos 1 e 4 foram acionados

**Fato.** O token de 14/09 baixa a **previsão de ENA do TempoOK com a data de
hoje** (`Comercializadora/Arquivos/ENA-PREVS/…`, arquivo de 20/09 presente, série
diária desde ~17/11/2024). O caminho veio da Alup em 18/09 e foi conferido em
21/09 ([ADR 019](019-boletim-do-tempook-como-arquivo.md), adendo).

**O que isso faz com esta ADR:**

| Item da ADR | Situação em 21/09 |
|---|---|
| Fato 1 da seção 3 — *"o alcance é pequeno: só boletins, só até 26/10/2022"* | **Deixou de ser verdade.** O token dá acesso a produto do fornecedor com dado corrente |
| Gatilho 1 — *"o acervo recente passa a ser alcançável"* | **Acionado** no espírito: o token alcança dado corrente do fornecedor, embora não o boletim |
| Gatilho 4 — *"o token passar a valer para outro produto que não o boletim"* | **Acionado** na letra: o alcance medido no item 3.1 não descreve mais a realidade |
| Argumento decisivo da seção 3 — *rotacionar hoje reproduziria a exposição, porque o Secret Manager não existe* | **Continua de pé** enquanto A3 não chegar |

**O que continua verdadeiro:** o acesso é somente leitura, não há dado pessoal e
não há sistema transacional atrás — é dado comercial de previsão que a Alup
contrata do TempoOK.

A seção 5 diz que, acionado um gatilho, **a rotação passa a ser imediata**. A
seção 3 diz que rotacionar antes de existir Secret Manager renova a exposição em
vez de encerrá-la. As duas não cabiam juntas, e a ADR não dizia qual vence.

**Decisão de 21/09/2026 — Ricardo Esper, responsável nomeado na seção 2:** a ADR
foi aceita com este adendo. A tensão se resolve pela **seção 3**: o argumento
decisivo — rotacionar sem Secret Manager reproduz a exposição — continua de pé, e
o token de 14/09 é mantido até o Secret Manager existir. O que muda é a data: a
rotação deixa de estar amarrada à virada de produção e passa a ser a **primeira
ação depois de A3**, com o valor novo gravado pela Alup direto no Secret Manager.
Os gatilhos 1 e 4 seguem registrados como acionados; não há prazo próprio além
de A3.

**Duas coisas que não dependem de decisão e foram feitas:**

- o dicionário e o `status.md` deixam de repetir o alcance de 2022 como o alcance
  do token;
- a dúvida sobre **a natureza do token** entra como pergunta em aberto: a função
  da Alup obtém o token por `get_tok_token()`, o que sugere credencial renovável,
  enquanto o nosso é o valor estático de 14/09 — que **continua válido sete dias
  depois**.

**Consequência para o pedido à Alup.** A rotação, quando acontecer, deve ser
pedida já com destino: o valor novo gravado direto no Secret Manager, sem e-mail
(seção 3). O momento natural é o dia em que A3 chegar.

