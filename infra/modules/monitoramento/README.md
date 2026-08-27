# Monitoramento

Alertas do AlupData: o que avisa quando ninguém está olhando o painel `/lake`.

Três políticas:

| Alerta | Dispara quando | Por que existe separado |
|---|---|---|
| Ingestão falhou | qualquer tarefa do Cloud Run Job falha | erro explícito |
| Fonte sem sucesso | passa 2× a cadência esperada sem sucesso | **silêncio não é erro** — job que não disparou não gera falha |
| Inválidos em alta | > 100 descartes por validação em 1h | schema da origem mudou; a ingestão segue "verde" e o dado para de chegar |

Os três dependem do log estruturado (`src/core/observabilidade.py`): é o campo
`fonte` no `jsonPayload` que permite contar por conector.

## Painel

`google_monitoring_dashboard` cria "AlupData <ambiente> — plataforma": ingestões
bem-sucedidas por fonte, registros descartados, tarefas do Cloud Run por
resultado, e um painel de log com os erros.

É o par do `/lake`, não um concorrente. O `/lake` responde "as fontes estão em
dia?" para quem opera o dado; este responde "a plataforma está saudável?" para
quem opera a infraestrutura — e fica no mesmo console onde o alerta chega, que é
onde a pessoa já está quando é acordada.

Duração p95 por conector fica só no `/lake`: o número exato está em
`bronze._execucoes`, não numa métrica derivada.

## Alerta de custo

`google_billing_budget` avisa em 50% e 90% do gasto, e em 100% da **projeção** —
esse último é o que pega a curva antes de virar fatura.

Orçamento não impede gasto: o Google não desliga nada sozinho. Ele avisa, que é
a diferença entre corrigir em um dia e descobrir no fim do mês. Importa mais a
partir da Onda 3, quando o Composer entra e a conta salta de ~US$ 15 para
~US$ 450/mês (issue #55).

Requer `billing_account`, que é da Alup. Vazio, o recurso não é criado —
orçamento com número inventado é pior que nenhum.

## Antes de aplicar

`emails_alerta` vem vazio de propósito. Alerta sem destinatário é alerta que
ninguém lê — e pior, dá sensação de cobertura. Preencher exige antes combinar
**quem recebe, em que canal, e o que se espera que a pessoa faça**. Isso é
acordo operacional com a Alup, não configuração.

Com a lista vazia, as políticas são criadas e ficam sem notificação: aparecem no
console do Cloud Monitoring, mas não avisam ninguém.
