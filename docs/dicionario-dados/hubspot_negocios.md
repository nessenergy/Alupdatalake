# Hubspot — negócios do CRM

**Onda 2 · bloqueado por credencial (pendência A5).** Implementado contra a
documentação pública da API; nunca executado contra dado real. O contrato
abaixo vale até a primeira execução com token — divergência encontrada ali é
esperada e deve virar `schema_versao = "2"`.

## Fonte

| | |
|---|---|
| Endpoint | `POST https://api.hubapi.com/crm/v3/objects/deals/search` |
| Documentação | https://developers.hubspot.com/docs/api/crm/deals |
| Autenticação | `Authorization: Bearer <token>` — private app, secret `alupdata-hubspot-api-token` |
| Paginação | cursor `paging.next.after`, 100 registros por página |
| Frequência | a cada 6 horas (`infra/modules/scheduler`) |
| Dono do dado | comercial da Alup — a nomear na matriz RACI (pendência A4) |

### Por que a janela filtra por `hs_lastmodifieddate`

Um negócio não é um fato imutável: ele muda de estágio, de valor e de data de
fechamento ao longo da vida. Filtrar por data de criação traria cada negócio
uma vez só, e o funil ficaria congelado na foto do dia em que nasceu. Filtrando
por última modificação, todo negócio que se mexeu na janela é reingerido, e a
Silver fica com a versão mais recente.

Consequência operacional: a janela de recarga é curta (2 dias no agendamento),
porque negócio parado não precisa ser lido de novo.

## Campos

| Origem (`properties.*`) | Bronze | Tipo | Silver | Regra |
|---|---|---|---|---|
| `id` (raiz do objeto) | `negocio_id` | STRING | igual | chave natural; dedup por ele |
| `dealname` | `nome` | STRING | igual | nulo vira `(sem nome)` — não pode quebrar a carga |
| `dealstage` | `estagio` | STRING | igual | **obrigatório**; vazio invalida o registro |
| `pipeline` | `pipeline` | STRING | igual | **obrigatório**; vazio invalida o registro |
| `amount` | `valor` | NUMERIC | igual | string vazia vira `NULL`, não `0` |
| `closedate` | `data_fechamento` | DATE | igual | truncado para data; nulo enquanto aberto |
| `createdate` | `criado_em` | TIMESTAMP | igual | usado na idade do negócio na Gold |
| `hs_lastmodifieddate` | `modificado_em` | TIMESTAMP | igual | filtro da janela e critério de dedup |
| `hubspot_owner_id` | `proprietario_id` | STRING | igual | vazio vira `NULL` |

Colunas técnicas (`_ingestao_id`, `_ingestao_timestamp`, `_fonte`,
`_schema_versao`) são do runner.

### `amount` vazio vira NULL, não zero

`""` no Hubspot significa "não preenchido", e negócio sem valor preenchido não
é negócio de R$ 0,00. Somar zeros numa média de ticket dá um número
silenciosamente errado; `NULL` sai da média sozinho.

## Dimensões comuns

| Dimensão | Valor | Por quê |
|---|---|---|
| `data_referencia` | `DATE(modificado_em)` | o dado é a foto do negócio naquele dia |
| `submercado` | `NULL` | CRM não tem recorte geográfico de submercado |
| `codigo_usina` | `NULL` | negócio comercial não aponta para ativo de geração |
| `agente_ccee` | `NULL` | a contraparte do CRM não é agente CCEE identificado |
| `periodo_apuracao` | `FORMAT_DATE('%Y-%m', ...)` | mês da última modificação |

Se o comercial passar a registrar a contraparte como agente CCEE, `agente_ccee`
deixa de ser nulo e esta fonte cruza com CCEE e BBCE. Hoje não cruza.

## Linhagem

```
Hubspot CRM (deals/search)
  → bronze.hubspot_negocios     append-only, 1 linha por leitura
  → silver.hubspot_negocios     1 linha por negocio_id, versão mais recente
  → gold.funil_comercial        negócios, valor e idade por pipeline × estágio
```

## Qualidade

- **Registro inválido**: estágio ou pipeline vazios — descartado com log e
  contado em `linhas_invalidas`.
- **Reprocessamento**: seguro. Bronze duplica por desenho; a Silver deduplica
  por `negocio_id` ordenando por `modificado_em DESC`.
- **Limite da API**: 100 registros por página; sem limite documentado de
  intervalo, por isso `max_dias_por_requisicao = None`.
- **Não verificado**: paginação além da segunda página, comportamento com
  negócio arquivado, e o formato exato de `amount` em conta com moeda
  diferente de BRL. Tudo isso só se confirma com token.
