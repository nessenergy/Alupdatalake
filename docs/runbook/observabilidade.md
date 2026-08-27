# Observabilidade

Três camadas, e cada uma responde uma pergunta diferente.

| Camada | Onde | Responde |
|---|---|---|
| Registro durável | `bronze._execucoes` (BigQuery) | o que aconteceu em cada execução, para sempre |
| Painel | `/lake` no Portal | está tudo em dia agora? |
| Alerta | Cloud Monitoring (`infra/modules/monitoramento`) | avisa quando ninguém está olhando |

O log do Cloud Logging é a quarta peça, e serve para o detalhe: **por que**
aquela execução falhou.

## Log estruturado

No Cloud Run o log sai como uma linha JSON por registro, que o Cloud Logging lê
nativamente. No laptop sai em texto, que é onde alguém lê com os olhos. A troca
é automática (`K_SERVICE`/`CLOUD_RUN_JOB`) e forçável com `LOG_FORMATO=json|texto`.

```json
{"severity": "WARNING", "message": "[bcb_cambio_ptax] registro inválido descartado: ...",
 "logger": "src.core.conector", "ingestao_id": "fb0ffa76...", "fonte": "bcb",
 "entidade": "cambio_ptax", "janela": "2026-08-25..2026-08-26"}
```

Por que JSON e não texto: `severity` deixa filtrar erro de verdade, e os campos
viram consulta. Texto corrido vira `textPayload` — um blob sem severidade, em
que "me mostra os erros da ONS ontem" é `grep`, não filtro.

### Correlação

Toda linha emitida durante uma ingestão carrega `ingestao_id`, o mesmo que está
em `bronze._execucoes`. Do cartão vermelho no painel até as linhas daquela
execução:

```
jsonPayload.ingestao_id="fb0ffa76fe91483ca6cf893b0dff4a20"
```

Sem isso, achar o log de uma execução é caçar por horário aproximado e torcer
para não haver duas rodando junto.

### Erro agrupado

Exceção é logada com `exc_info`, o que põe `stack_trace` no payload — é o campo
pelo qual o Error Reporting agrupa por assinatura. Sem ele, 400 falhas iguais
são 400 linhas; com ele, são um problema com contador.

## Consultas que resolvem a maioria dos casos

```
# tudo de uma execução
jsonPayload.ingestao_id="<id>"

# erros de uma fonte nas últimas 24h
jsonPayload.fonte="ons" severity>=ERROR

# registros descartados por validação, por fonte
jsonPayload.message=~"registro inválido" jsonPayload.fonte="aneel"
```

## Alertas

Ver [`infra/modules/monitoramento/README.md`](../../infra/modules/monitoramento/README.md).
Resumo: falha explícita, **silêncio** (fonte sem sucesso além da cadência) e
salto de registros inválidos.

O segundo é o que costuma faltar em projeto de dados: job que não dispara não
gera erro, e sem alerta de ausência ninguém percebe até alguém reclamar do
número.

## O que ainda não existe

- **Destinatário de alerta.** `emails_alerta` está vazio de propósito: quem
  recebe, em que canal e o que faz ao receber é acordo operacional com a Alup.
- **Métrica de custo.** Budget alert na conta de faturamento — depende do
  faturamento estar vinculado (pendência A3, issue #55).
- **Retenção.** O Cloud Logging guarda 30 dias por padrão. O registro durável é
  `bronze._execucoes`, que não expira; se o log precisar durar mais, é sink para
  bucket, e aí é decisão de custo.
