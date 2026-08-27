# ADR 006 — Painel de saúde do DataLake

**Status**: aceito · **Data**: 2026-08-27

## Contexto

A [ADR 005](005-escopo-do-portal-mvp.md) cravou o escopo do Portal MVP e listou
o que ele não é — entre outras coisas, painel com gráficos e filtros, que é
trabalho de ferramenta de BI. Ao mesmo tempo, ela previu que o Portal "continua
fazendo sentido como prova de acesso e como **página de status da ingestão**".

Esta ADR usa exatamente essa abertura, e explica por que ela não contradiz a
anterior.

A distinção que sustenta as duas decisões: **o painel de saúde não mostra dado
de cliente, mostra o log de execução do próprio pipeline.** Um relatório de BI
responde "quanto vendemos"; este painel responde "a ingestão rodou, e dá para
confiar no que ela trouxe". São públicos, dados e propósitos diferentes.

Isso também é o que o encaixa na cláusula 10ª: o escopo de sustentação inclui
**monitoramento** e exclui **relatórios BI**. Sem uma tela de saúde, monitorar
20h/mês significa alguém abrindo o BigQuery e escrevendo SQL à mão toda semana
— o que consome a franquia com trabalho que uma view resolve uma vez.

## Decisão — o que o painel mostra

Rota `/lake`, um cartão por conector, alimentado por `gold.saude_ingestao`:

| Indicador | Pergunta que responde |
|---|---|
| Situação (semáforo) | está em dia, atrasada, falhando, ou nunca funcionou? |
| Último sucesso | o dado está velho? |
| Taxa de sucesso 30d | dá para confiar nesta fonte? |
| Taxa de inválidas | o schema da origem mudou? |
| Linhas carregadas | volumetria acumulada |
| Duração p95 | está degradando antes de virar timeout? |
| Último erro | o que quebrou, sem abrir log |

O indicador que justifica o painel sozinho é o **frescor**. Os outros seis vêm
de graça, porque `bronze._execucoes` já registra tudo isso desde a Onda 0 — não
foi preciso instrumentar nada.

## Decisão — atraso é medido contra a cadência da própria fonte

Uma fonte está atrasada quando o tempo desde o último sucesso passa de **duas
vezes o intervalo típico entre execuções bem-sucedidas dela**, calculado como a
mediana do histórico. Sem histórico suficiente, o limite cai para 26 horas.

A alternativa seria declarar o intervalo esperado por fonte. Rejeitada: o
agendamento já está no Terraform, e uma segunda cópia divergiria na primeira vez
que alguém mudasse o cron sem lembrar da view. Inferir do histórico não tem
configuração para envelhecer, e acompanha sozinho quando a cadência muda.

Consequência aceita: uma fonte que sempre falhou nunca terá cadência inferida —
por isso o estado `SEM_SUCESSO` existe separado de `ATRASADA`.

## Decisão — a lógica fica no SQL, a tela é burra

`gold.saude_ingestao` e `gold.volumetria_lake` carregam toda a regra; o Portal
só renderiza. Duas razões:

- Mantém a convenção do projeto ([ADR 004](004-sql-puro-e-orquestracao.md)):
  transformação é SQL versionado, testado pelo `tests/unit/test_sql.py`.
- Permite ligar Looker Studio nas mesmas views depois, sem reescrever nada. Se
  a Alup definir uma ferramenta de BI (pendência A6) e quiser o painel lá, a
  migração é apontar a ferramenta para a view.

Essas duas views são as únicas do Gold que leem `bronze._execucoes` em vez da
Silver. O teste que garante "Gold lê da Silver" foi ajustado para permitir
exatamente esse caso e proibir a mistura: uma view de monitoramento não pode
juntar log de execução com dado de negócio.

## Consequências

- Não é escopo faturado da Fase 1: é ferramenta da ness. para tornar a
  sustentação viável dentro da franquia de 20h/mês. Não vira item de medição
  nem estende o item 0.15.
- Enquanto o ambiente GCP não existir (pendência A3), o painel roda com o mesmo
  provedor simulado do Portal, rotulado na tela.
- O painel **não substitui alerta**. Ele responde quando alguém olha; quem
  avisa às 3 da manhã é o alerta do Cloud Scheduler/Cloud Run. Se a Alup quiser
  alerta ativo (e-mail, Slack), isso é escopo novo.
