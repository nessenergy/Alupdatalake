# `bronze._execucoes` — log de execução da ingestão

| Item | Valor |
|---|---|
| Origem | O próprio runner (`src/core/conector.py`), não uma fonte externa |
| Escrita | Uma linha por execução, ao fim de cada ingestão ou replay |
| Onda | 0 — nasce com o framework |
| Consumidores | `gold.saude_ingestao`, `gold.volumetria_lake`, painel `/lake` |
| Credencial | nenhuma |

Não é dado de negócio: é a evidência operacional do pipeline. Está documentado
aqui porque duas views Gold leem dele, o painel de saúde depende dele, e ele é
o artefato que sustenta a homologação de onda — "o dado de ontem entrou?" se
responde nesta tabela, sem abrir o orquestrador.

## Particularidades

- **Falha ao registrar é falha.** Se a carga funciona mas a linha não é gravada,
  o runner propaga o erro: carga sem evidência operacional não pode ser
  declarada sucesso nem homologada.
- **O erro chega sanitizado.** `src/core/seguranca.sanitizar` remove DSN, Bearer
  e parâmetro sensível antes de a mensagem ser persistida (cláusula 8.5). O
  valor que reprovou na validação nunca entra aqui.
- **Replay não sobrescreve nada.** Reprocessar do raw grava uma execução nova
  com `modo = REPLAY` e `origem_ingestao_id` apontando para a execução cujo raw
  foi lido. O histórico não é reescrito.
- **Particionada por `iniciada_em`, clusterizada por `fonte` e `status`** — as
  duas colunas pelas quais o painel filtra.

## Campos

| Coluna | Tipo | Origem do valor | Observação |
|---|---|---|---|
| `ingestao_id` | STRING | `uuid4().hex` no início da execução | correlaciona a linha com o log estruturado e com o objeto raw no GCS |
| `fonte` | STRING | atributo de classe do conector | `ons`, `bcb`, `aneel`… |
| `entidade` | STRING | atributo de classe do conector | o que foi ingerido: `carga`, `cambio_ptax` |
| `modo` | STRING | runner | `FONTE` na ingestão normal, `REPLAY` no reprocessamento do raw |
| `origem_ingestao_id` | STRING | URI do raw relido | preenchido só em replay; liga o reprocessamento à execução original |
| `janela_inicio` | DATE | parâmetro da execução | nenhum conector decide "hoje" sozinho |
| `janela_fim` | DATE | parâmetro da execução | |
| `status` | STRING | runner | `EM_EXECUCAO`, `SUCESSO` ou `ERRO` |
| `linhas_extraidas` | INT64 | contagem após `extrair()` | o que a fonte devolveu |
| `linhas_invalidas` | INT64 | contagem de reprovações do schema | **é o sinal de mudança de layout na origem**; alerta dispara quando sobe |
| `linhas_carregadas` | INT64 | retorno do load job | diferença para `extraidas` é o que foi descartado |
| `iniciada_em` | TIMESTAMP | início da execução | chave de partição |
| `encerrada_em` | TIMESTAMP | fim da execução | nulo enquanto `EM_EXECUCAO` |
| `duracao_segundos` | FLOAT64 | derivado | alimenta a leitura de degradação de desempenho |
| `erro` | STRING | exceção sanitizada | nulo em `SUCESSO` |

## Linhagem

```
runner (src/core/conector.py)
  → bronze._execucoes                      tabela append-only
      → gold.saude_ingestao                frescor, confiabilidade, volumetria por fonte
      → gold.volumetria_lake               quanto entrou por conector e a tendência
          → portal /lake                   painel de saúde (ADR 006)
```

É a única exceção, junto de `INFORMATION_SCHEMA`, à regra de CI que exige que
toda view Gold leia da Silver — e a exceção é estreita de propósito: view de
monitoramento não pode juntar log de execução com dado de negócio.
