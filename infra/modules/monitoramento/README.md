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

## Antes de aplicar

`emails_alerta` vem vazio de propósito. Alerta sem destinatário é alerta que
ninguém lê — e pior, dá sensação de cobertura. Preencher exige antes combinar
**quem recebe, em que canal, e o que se espera que a pessoa faça**. Isso é
acordo operacional com a Alup, não configuração.

Com a lista vazia, as políticas são criadas e ficam sem notificação: aparecem no
console do Cloud Monitoring, mas não avisam ninguém.
