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

## Decisão — visual do shadcn, paleta do alup.io, sem React

O painel adota o **sistema visual** do shadcn/ui — os mesmos tokens
(`--background`, `--card`, `--muted-foreground`, `--border`, `--radius`), o
mesmo desenho de cartão e a mesma escala tipográfica — implementado em CSS puro.
A biblioteca em si é React: adotá-la significaria build, bundler e deploy
separado, contra a ADR 005, para desenhar cartões e uma área de 30 pontos.

A paleta vem do site institucional da Alup (`alup.io`): roxo `#520042`, azul
`#1863dc`, cinzas `#f4f4f4`/`#e6e3ea`, texto `#212121`, com Zilla Slab nos
títulos e Hanken Grotesk no corpo — as mesmas fontes do site.

As cores de **série** (`#8B2A78 #1863dc #0E8A6B #B26A00 #C2185B`) passaram nos
seis checks do validador de paleta: banda de luminosidade, croma, separação para
daltonismo (ΔE 9,5 no pior par adjacente), piso de visão normal e contraste com
a superfície. A cor segue o conector, atribuída em ordem alfabética estável —
filtrar não repinta quem sobrou.

As cores de **estado** (em dia / atrasada / falha / sem sucesso) são reservadas e
nunca reaproveitadas como cor de série, e sempre acompanham um rótulo em texto:
a situação nunca é comunicada só por cor.

## Decisão — série temporal em SVG do servidor

Linhas carregadas por dia, 30 dias, uma área por conector, gerada no servidor.
Cinco séries de 30 pontos não justificam biblioteca de gráficos, bundler e build.
Cada dia carrega um `<title>` — que o navegador mostra no hover e o leitor de
tela anuncia — e a página traz a mesma informação em tabela, que é a exigência
de acessibilidade de qualquer gráfico. A área tem baseline em zero: área com
eixo truncado mente sobre a proporção.

## Consequências

- Não é escopo faturado da Fase 1: é ferramenta da ness. para tornar a
  sustentação viável dentro da franquia de 20h/mês. Não vira item de medição
  nem estende o item 0.15.
- Enquanto o ambiente GCP não existir (pendência A3), o painel roda com o mesmo
  provedor simulado do Portal, rotulado na tela.
- O painel **não substitui alerta**. Ele responde quando alguém olha; quem
  avisa às 3 da manhã é o alerta do Cloud Scheduler/Cloud Run. Se a Alup quiser
  alerta ativo (e-mail, Slack), isso é escopo novo.
