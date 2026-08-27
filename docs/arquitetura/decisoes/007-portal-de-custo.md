# ADR 007 — Painel de custo de nuvem no Portal

**Status**: aceito · **Data**: 2026-08-27

## Contexto

A [ADR 005](005-escopo-do-portal-mvp.md) cravou o escopo do Portal MVP; a
[ADR 006](006-painel-de-saude.md) abriu o painel de saúde usando o argumento de
que ele mostra o **comportamento do pipeline**, não dado de cliente.

Esta ADR estende a mesma linha ao custo, e registra uma decisão comercial que
não é técnica: **o painel de saúde e o de custo são contribuição da ness., não
escopo faturado.** A cláusula 5ª exclui "custos de infra GCP" e "painéis de BI"
do contrato; a 10ª inclui monitoramento na sustentação. Nada disso obriga a
ness. a entregar as três visões — a decisão de entregá-las mesmo assim é
deliberada, e precisa estar escrita para não virar precedente silencioso.

O que **não** muda com isso: pedido novo sobre estas telas continua sendo
avaliado como escopo. Cortesia declarada é diferente de escopo aberto.

## Decisão — uma rota, três recortes

`/custo` mostra a mesma conta em três leituras, definidas com a Alup em 27/08:

| Visão | Para quem | Pergunta |
|---|---|---|
| Operacional | quem opera o pipeline | o que eu mudo hoje |
| Orçamento | quem responde pelo orçamento | estamos dentro do previsto |
| Diretoria | quem decide renovar | vale o que custa |

Uma rota, não três: são o mesmo número lido de três alturas, e três telas
divergiriam na primeira mudança de tarifa. Quem lê sabe descer até a sua seção.

## Decisão — a fonte é o log do BigQuery, não a fatura

`gold.custo_consultas` lê `INFORMATION_SCHEMA.JOBS_BY_PROJECT` e
`TABLE_STORAGE`. Isso cobre byte varrido e armazenamento — a maior parcela da
conta do lake — **sem depender da conta de faturamento**, que é uma pendência
separada de A3 e exige papel que criar o projeto não dá.

Consequência aceita e dita na tela: crédito, desconto por uso comprometido e
serviço de terceiros **não aparecem**. Isso só chega com o billing export
(camada F2 do plano). Um painel de custo que não avisa o que não enxerga é pior
que nenhum.

## Decisão — mínimo faturado por consulta entra na conta

O BigQuery cobra um mínimo por consulta independente do quanto ela varreu.
Ignorar isso subestimaria justamente o caso do lake pequeno com muita consulta,
que é o nosso hoje.

O mock provou o ponto: com as cinco fontes atuais, **92% do gasto é custo fixo
por execução** — job de ingestão e mínimo por consulta — e não volume. A
consulta que varre 61 MiB custa menos que a que varre 864 bytes, porque as duas
batem no mínimo e a segunda roda mais vezes.

Isso inverte a recomendação óbvia: hoje **reduzir número de execuções rende
mais que otimizar varredura**. A inversão vale enquanto o volume for este; a
Onda 3 muda o regime, e a tela diz isso.

## Decisão — não arredondar antes da hora

Custo é acumulado em `Decimal` exato e só arredondado na formatação. Arredondar
a cada dia zerava a conta inteira: trinta parcelas de meio centavo viravam
trinta zeros, e o total mentia. Há teste para isso.

Pelo mesmo motivo, a formatação usa quatro casas abaixo de US$ 1 — duas casas
transformariam a tela em uma coluna de `US$ 0,00`.

## Decisão — o que a tela não pode atribuir, ela declara

Existe **um** Cloud Run Job para todas as fontes, com a fonte entrando como
argumento. Rótulo de recurso é fixo por recurso, então compute sai correto no
total e não se separa por fonte. A tela mostra compute no agregado e diz por
quê, em vez de ratear por uma chave inventada.

A alternativa — um job por fonte — fica registrada para quando o compute
crescer o bastante para pagar a complexidade. Não é hoje.

## Consequências

- O custo por fonte só existe porque o job do BigQuery é rotulado em execução
  (camada F0 do plano). **Sem isso a tela funciona, mas responde "gastamos X"
  sem conseguir dizer em quê** — e rótulo não se aplica retroativamente.
- O agrupamento por domínio de negócio é provisório até o Questionário de Gaps
  (A4) definir os 8 domínios. A tela marca isso como provisório.
- A tarifa vive em dois lugares — na view e em `src/portal/custo.py`, para o
  provedor simulado. Divergirão se alguém mudar só um. Quando o billing export
  entrar, a view passa a ser a única fonte e o módulo perde as constantes.
