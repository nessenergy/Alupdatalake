# `gold.custo_consultas` — custo de nuvem por dia, fonte e camada

Responde **"quanto o lake custou, em quê, e o que mudou"**.

Como o [`_execucoes`](_execucoes.md), não documenta uma fonte de negócio: a
matéria-prima é o log de jobs do próprio BigQuery. É a plataforma se
observando. Por isso o nome começa com `_` neste índice, embora a view em si
seja nomeada pela pergunta que responde, como manda a convenção da camada Gold.

| Item | Valor |
|---|---|
| Origem | `INFORMATION_SCHEMA.JOBS_BY_PROJECT` e `INFORMATION_SCHEMA.TABLE_STORAGE` |
| Camada | Gold (não passa por Bronze nem Silver) |
| Janela | 90 dias corridos |
| Enquadramento | camada F1 do plano de FinOps — sustentação, cláusula 10ª |

## Particularidades

**Não é dado de negócio, e não passa pelo framework.** Não há conector, tabela
Bronze nem view Silver: o BigQuery já mantém o log. A view lê direto do
`INFORMATION_SCHEMA`, que é por natureza um retrato do próprio ambiente.

**A região é parte da correção, não detalhe.** O `INFORMATION_SCHEMA` do
BigQuery é escopado por região, e consultar a região errada **não dá erro —
devolve zero linhas**. O painel mostraria custo zero para sempre, parecendo
funcionar. Por isso a região vem de `${regiao}`, que acompanha a configuração
do ambiente (ADR 009), e há teste que reprova região fixa no SQL.

**As tarifas são premissa declarada, não preço contratado.** Ficam num `WITH`
no topo da view, num lugar só: US$ 6,25 por TiB varrido e US$ 0,020 por GiB-mês
de armazenamento ativo, com mínimo de 10 MB faturados por job. Quando a Alup
fechar preço com desconto por uso comprometido, muda-se a constante — não a
lógica.

**O que esta view não enxerga.** Compute do Cloud Run, serviços de terceiros e
descontos reais só aparecem com o billing export, que é a camada F2. A view não
os cobre **e não finge cobrir**: o número que ela dá é de consulta e
armazenamento, que são a maior parcela da conta do lake, não a conta inteira.

## Campos

| Campo | Tipo | Regra |
|---|---|---|
| `dia` | DATE | data de criação do job |
| `fonte` | STRING | rótulo `fonte` do job; `'não rotulado'` quando ausente |
| `camada` | STRING | rótulo `camada` do job; `'não rotulado'` quando ausente |
| `consulta` | STRING | rótulo `consulta`, ou o tipo de instrução quando não houver |
| `execucoes` | INT64 | quantidade de jobs no dia, por fonte, camada e consulta |
| `bytes_varridos` | INT64 | soma de bytes processados — o que se lê, não o que se cobra |
| `custo_query_usd` | FLOAT64 | bytes **faturados** convertidos pela tarifa; respeita o mínimo por job |
| `custo_armazenamento_usd` | FLOAT64 | rateio diário do custo mensal de armazenamento ativo do Bronze |
| `linhas_carregadas` | INT64 | do `_execucoes`; é o denominador que separa "fonte cara" de "fonte cara à toa" |
| `variacao_vs_media` | FLOAT64 | desvio contra a média móvel de 7 dias da própria consulta |

### Duas escolhas que precisam estar explícitas

**`bytes_varridos` e `custo_query_usd` não são proporcionais.** O custo usa
bytes *faturados*, que respeitam o mínimo de 10 MB por job; o varrido é o
número real. Consulta pequena e frequente custa mais do que o varrido sugere —
e é exatamente esse o caso que o campo separado revela.

**`variacao_vs_media` separa "é cara" de "ficou cara".** Só a segunda é
acionável. Uma consulta consistentemente cara é um fato conhecido; uma que
dobrou ontem é um incidente.

## Linhagem

```
BigQuery INFORMATION_SCHEMA          bronze._execucoes
  ├─ JOBS_BY_PROJECT (rótulos)         └─ linhas_carregadas
  └─ TABLE_STORAGE                            │
             │                                │
             ▼                                ▼
      gold.custo_consultas  ◄─────────────────┘
             │
             ▼
      rota /custo do Portal
```

A atribuição por fonte depende de o job carregar rótulo, o que é feito em
tempo de execução por `rotulos()` em `src/core/bigquery.py` — a camada F0.
**Custo já gasto não se rateia depois**: o rateio se apoia no rótulo aplicado
no momento do consumo, e job sem rótulo aparece como `'não rotulado'`, que é a
única forma honesta de mostrá-lo.

O armazenamento é a exceção: `TABLE_STORAGE` não carrega rótulo, então a
atribuição vem do nome da tabela, que é o nome da fonte por convenção do
`make novo-conector`. Se essa convenção mudar, esta é a linha que quebra — de
propósito.
