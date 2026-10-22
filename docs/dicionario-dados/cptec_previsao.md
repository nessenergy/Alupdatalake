# CPTEC — previsão do tempo por capital

| Item | Valor |
|---|---|
| Fonte | Webservice XML do CPTEC/INPE, `https://servicos.cptec.inpe.br/XML/cidade/7dias/{id}/previsao.xml`, uma requisição por capital |
| Onda | 1 ("previsão do tempo" da cláusula 4ª) |
| Frequência | diária, às 11h (Cloud Scheduler); a origem atualiza uma vez por dia |
| Dono do dado (Alup) | Inteligência de Mercado |
| Credencial | nenhuma (dado público); o coletor se identifica no `User-Agent` |
| Cobertura | as 27 capitais, com ids do CPTEC conferidos em 22/10/2026 |

## Como a origem se comporta

- É um **retrato da previsão vigente**: não há histórico nem parâmetro de data. A janela da CLI não se aplica (os dias previstos
  são de hoje em diante e a janela termina ontem). O histórico de previsões nasce do Bronze append-only, uma foto por emissão.
- Apesar do nome `7dias`, a resposta de 22/10/2026 trazia **6 dias** (23 a 28/10). Vale o que a origem devolve.
- Limite de 120 requisições por janela (`x-ratelimit-limit`); são 27 por execução. Em 429 o cliente HTTP espera o `Retry-After`.
- A resposta vem em ISO-8859-1. O XML é lido com `defusedxml`.
- O webservice respondeu 403 a toda requisição em 02 e 03/10/2026 (ADR 028 e 029) e voltou a responder 200 em 22/10/2026. Se voltar
  a bloquear, o conector falha alto (`LayoutInesperadoError` ou erro HTTP) e nunca carrega zero linhas como sucesso.
- **Não traz precipitação em mm.** A cláusula fala também em previsão climática, que este conector não cobre.

## Campos

| Origem | Bronze | Silver | Gold | Tipo | Transformação |
|---|---|---|---|---|---|
| id da cidade (URL) | `cidade_id` | `cidade_id` | `cidade_id` | INT64 | chave do CPTEC |
| `nome` | `cidade` | `cidade` | `cidade` | STRING | nome fixo da tabela de capitais do conector |
| `uf` | `uf` | `uf` | `uf` | STRING | idem |
| `previsao/dia` | `data_referencia` | `data_referencia` | `data_referencia` | DATE | dia previsto, `aaaa-mm-dd` |
| `atualizacao` | `data_emissao` | `data_emissao` | `data_emissao` | DATE | dia em que o CPTEC emitiu |
| `previsao/tempo` | `codigo_tempo` | `codigo_tempo` | `codigo_tempo` | STRING | código do CPTEC, sem tradução |
| `previsao/maxima` | `temperatura_maxima_c` | `temperatura_maxima_c` | `temperatura_maxima_c` | INT64 | °C |
| `previsao/minima` | `temperatura_minima_c` | `temperatura_minima_c` | `temperatura_minima_c` | INT64 | °C |
| `previsao/iuv` | `indice_uv` | `indice_uv` | `indice_uv` | NUMERIC | índice ultravioleta |
| — | — | — | `antecedencia_dias` | INT64 | `data_referencia` menos `data_emissao` |
| — | — | — | `amplitude_termica_c` | INT64 | máxima menos mínima |

Códigos de tempo vistos na origem em 22/10/2026: `c` e `pn`. A tabela completa de códigos é do CPTEC e não foi reproduzida aqui,
porque não foi conferida contra a documentação oficial; o dado guarda o código bruto.

## Linhagem

`cptec_previsao` (Bronze, append-only) → `silver.cptec_previsao` (uma linha por cidade, dia previsto e emissão) →
`gold.previsao_tempo_capitais` (a emissão mais recente de cada cidade e dia previsto).

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | o dia previsto |
| `submercado` | não | a previsão é por cidade; mapear cidade a submercado é regra da Alup |
| `codigo_usina` | não | sem usina |
| `agente_ccee` | não | sem agente |
| `periodo_apuracao` | sim | `aaaa-mm` do dia previsto |

## Qualidade e observações

- Chave natural: `cidade_id`, `data_referencia`, `data_emissao`. Reprocessar a mesma emissão não duplica (vale a ingestão mais recente).
- Capital omitida pela origem ou resposta com campo faltando derruba a execução, em vez de gravar parcial.
- A fixture dos testes é a resposta real de São Paulo em 22/10/2026 (`tests/fixtures/cptec_previsao_244.xml`).
