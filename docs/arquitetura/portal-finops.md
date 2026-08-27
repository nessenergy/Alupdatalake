# Plano — Portal de FinOps do custo de nuvem

**Status**: proposta · **Data**: 2026-08-27 · **Não é escopo contratado**

---

## 1. O que se pede e o que o contrato diz

O pedido: uma tela que responda *quanto o DataLake está custando, em que, e se
isso está saindo do controle*.

O contrato precisa ser lido antes de estimar. A cláusula 5ª exclui do escopo
"custos de infra GCP" e "painéis/relatórios de BI, exceto o Portal MVP da Onda
0". A cláusula 10ª inclui **monitoramento** na sustentação e exclui
**relatórios BI** dela.

Isso não mata a ideia, mas separa três coisas que normalmente vêm embrulhadas
juntas, e que têm enquadramentos contratuais diferentes:

| | O que é | Onde cabe |
|---|---|---|
| **Higiene de custo** | rotular recurso, rotular query, particionar, medir o que já se gasta | dentro do trabalho já contratado — é boa prática de engenharia, não entrega nova |
| **Observabilidade de custo** | uma tela que mostra o gasto do próprio pipeline, como o painel de saúde mostra a execução dele | mesma abertura da [ADR 006](decisoes/006-painel-de-saude.md): sustentação, cláusula 10ª |
| **Gestão de FinOps** | rateio por centro de custo, previsão, detecção de anomalia, recomendação de economia | **aditivo** — é produto novo, com público fora do time técnico |

A recomendação deste plano é fazer as duas primeiras e propor a terceira como
aditivo, se a Alup quiser. Empacotar tudo como "portal de FinOps" e entregar de
graça criaria um precedente ruim: vira BI, o escopo cresce, e a franquia de
sustentação some dentro dele.

---

## 2. A janela que fecha: rotular antes de gastar

O item mais urgente deste plano não é a tela. É que **custo que já foi gasto
não pode ser rateado depois.** O rateio do Google se apoia em rótulos aplicados
no momento do consumo; recurso sem rótulo entra na fatura como massa
indistinta, e nenhum relatório recupera isso retroativamente.

O ambiente GCP ainda não existe (pendência A3). Ou seja: **estamos exatamente
no único momento em que dá para acertar isso de graça.** Se o primeiro
`terraform apply` subir sem a taxonomia definida, o primeiro mês de fatura
nasce sem atribuição.

Estado atual do repositório: `bigquery`, `storage`, `scheduler` e `secrets` já
aplicam `projeto`, `ambiente` e (no BigQuery) `camada`. Falta o eixo que
interessa para FinOps — **por fonte de dado** — e ele tem uma dificuldade real
descrita em §4.

---

## 3. De onde vem o número

Três origens, com custo de obtenção muito diferente:

| Origem | O que dá | Precisa de quê | Latência |
|---|---|---|---|
| `INFORMATION_SCHEMA.JOBS` | bytes faturados por query, por usuário, por rótulo de job; slot-ms | só o projeto existir | minutos |
| **Billing export** para BigQuery | a fatura inteira: todo serviço, com rótulos, créditos e descontos | conta de faturamento e permissão para configurar o export | ~24h |
| `google_billing_budget` | alerta de estouro contra um valor | `billing_account` | — |

Duas leituras que mudam o plano:

- **A parte cara do BigQuery é query, não carga.** Job de load em lote é
  gratuito; o que se paga é byte varrido em consulta e armazenamento. Como as
  views Gold e o Portal são quem consulta, o `INFORMATION_SCHEMA.JOBS` já
  responde a maior parte da pergunta **sem depender da conta de faturamento**.
- **O `google_billing_budget` já está escrito** no módulo `monitoramento`, com
  faixas em 50% e 90% do realizado e 100% do previsto. Ele está inerte só
  porque `billing_account` está vazio — a mesma pendência que trava o export.

---

## 4. A limitação honesta: compute não é atribuível hoje

Hoje existe **um** Cloud Run Job para todas as fontes; a fonte entra como
argumento de execução, não como recurso separado. Rótulo de recurso é fixo por
recurso — logo, o custo de compute sai correto no total e **não** se separa por
fonte.

Três saídas, e a escolha muda o desenho:

1. **Aceitar.** Compute de ingestão é a menor parcela da conta (job de minutos,
   algumas vezes por dia). Ratear o que é irrelevante custa mais do que informa.
2. **Um job por fonte** no Terraform, cada um com `labels = { fonte = ... }`.
   Atribuição exata, ao preço de multiplicar recursos e complicar o deploy.
3. **Rotular a execução, não o recurso** — rótulo no *job* do BigQuery
   (`fonte`, `camada`, `ingestao_id`), que o cliente Python define em tempo de
   execução. Não resolve compute, mas resolve o que importa: **byte varrido por
   fonte**.

**Recomendado: 1 + 3.** Compute fica no agregado, BigQuery fica atribuído por
fonte. A opção 2 fica registrada para o dia em que o compute crescer o
suficiente para pagar a complexidade — e não é hoje.

---

## 5. Entrega em quatro camadas

Cada camada é útil sozinha e não pressupõe a seguinte.

### F0 · Higiene de custo — 6h · **não depende de nada**

Pode começar hoje, e é a única parte que **perde valor se esperar**.

- Taxonomia de rótulos escrita e aplicada em todos os módulos do Terraform:
  `projeto`, `ambiente`, `camada`, `componente`.
- Rótulo de job do BigQuery em tempo de execução: `fonte`, `camada`,
  `ingestao_id` — no cliente, junto das colunas técnicas que já existem.
- Teste que falha se um recurso novo do Terraform subir sem os rótulos
  obrigatórios. Sem isso a convenção envelhece na primeira PR distraída.
- Documentar em `gcp-alupdata` para que valha para quem vier depois.

**Aceite**: `terraform plan` mostra os rótulos em todo recurso faturável, e uma
query de teste aparece no `INFORMATION_SCHEMA.JOBS` com os rótulos preenchidos.

### F1 · Observabilidade de custo — 16h · depende de A3

A tela, na sua forma sustentável: **uma rota a mais no Portal que já existe**,
alimentada por uma view Gold, do mesmo jeito que `/lake` é alimentada por
`gold.saude_ingestao`.

- `gold.custo_consultas`: sobre `INFORMATION_SCHEMA.JOBS`, agregando bytes
  faturados por dia, por fonte e por camada, com o custo convertido pela tarifa
  vigente declarada como constante única na view.
- Rota `/custo` no Portal: gasto do mês, tendência diária, as consultas mais
  caras, e armazenamento por dataset (ativo × longo prazo).
- Alerta de consulta anômala reaproveitando o módulo `monitoramento` que já
  está montado — não é componente novo.

**Aceite**: a tela bate com o console de faturamento do Google dentro de uma
margem declarada, verificada em dois dias distintos. Um painel de custo que não
bate com a fatura é pior que nenhum.

**Enquadramento**: cabe na cláusula 10ª pelo mesmo argumento da ADR 006 — não
mostra dado de cliente, mostra o comportamento do próprio pipeline. Serve para
decidir se uma view precisa ser reescrita, que é trabalho de sustentação.

### F2 · Fatura completa — 30h · depende de A3 e da conta de faturamento

- Billing export habilitado; ingestão do dataset de export pelo mesmo framework
  de conectores, com os 7 componentes de sempre.
- Gold com custo por serviço, por rótulo e por dia, incluindo créditos e
  descontos por uso comprometido — que o `INFORMATION_SCHEMA` não enxerga.
- Orçamento realizado × previsto na tela, ligado ao `google_billing_budget` que
  já está escrito.

**Enquadramento**: fronteira. Se o consumidor for o time técnico, ainda é
monitoramento. Se virar relatório para a diretoria, é BI — e aí é aditivo.
Decidir isso **antes** de construir, não depois.

### F3 · Gestão de FinOps — 40h+ · **aditivo**

Rateio por centro de custo, previsão de gasto, detecção de anomalia com linha
de base móvel, recomendação de otimização (partição faltando, dado quente que
devia ser frio, view que varre a tabela inteira), relatório mensal exportável.

Isto é produto, tem público fora do time técnico e não cabe em franquia de
sustentação. Vira proposta separada, com escopo próprio e horas próprias.

---

## 5-A. Quem lê o número — as três visões

Definido pela Alup em 27/08: o custo é lido em três níveis, terminando na
diretoria. Isso não é detalhe de tela — **decide o enquadramento contratual de
metade deste plano**, e por isso vem antes da estimativa.

### ▸ Operacional — "o que eu mudo hoje"

Quem lê: quem opera o pipeline, diariamente ou quando um alerta toca.

| Pergunta | Vem de |
|---|---|
| Qual consulta varreu mais byte ontem? | `INFORMATION_SCHEMA.JOBS` |
| Alguma view começou a varrer a tabela inteira? | comparação com a média móvel da própria view |
| Que dataset está crescendo mais rápido? | armazenamento ativo × longo prazo |
| Alguma fonte está reprocessando janela à toa? | `bronze._execucoes` cruzado com bytes |

Granularidade fina, janela curta (7 a 30 dias), sem nenhum valor agregado por
área. Cada linha existe porque leva a uma ação técnica concreta: reescrever a
view, particionar, mudar a janela de ingestão, apagar dado de teste esquecido.

**É a camada F1**, e é a única das três que se sustenta como monitoramento pela
cláusula 10ª — pelo mesmo argumento da ADR 006: mostra o comportamento do
pipeline, não dado de cliente, e serve para decidir trabalho de sustentação.

### ▸ Orçamento — "estamos dentro do previsto"

Quem lê: quem responde pelo orçamento de nuvem, mensalmente.

| Pergunta | Vem de |
|---|---|
| Quanto gastamos no mês, contra o orçado? | billing export + `google_billing_budget` |
| A curva do mês projeta estouro? | realizado acumulado contra a mesma curva do mês anterior |
| Onde o dinheiro está: query, armazenamento, compute, terceiros? | billing export por serviço |
| Quanto custa cada fonte de dado? | rótulos aplicados em F0 |

Granularidade mensal, com um nível de quebra. Aqui entra o que o
`INFORMATION_SCHEMA` não enxerga: créditos, descontos por uso comprometido, e
todo serviço que não seja BigQuery.

**É a camada F2**, e depende inteiramente de F0 ter sido feito antes. Sem os
rótulos, "quanto custa cada fonte" não tem resposta — nem retroativa.

### ▸ Diretoria — "vale o que custa"

Quem lê: a diretoria, trimestralmente ou quando decide renovar.

| Pergunta | Vem de |
|---|---|
| Custo por unidade de negócio, não por serviço técnico | rateio sobre os rótulos |
| A tendência é de crescimento sustentável ou de descontrole? | série longa, 12 meses |
| Qual o custo de uma fonte nova antes de contratá-la? | modelo de projeção sobre o histórico |
| O que dá para economizar sem perder capacidade? | recomendações de otimização |

Granularidade grossa, série longa, linguagem de negócio. Poucos números, cada
um defensável em reunião.

**É a camada F3 — e é BI, pela cláusula 5ª.** Público fora do time técnico,
métrica de negócio, periodicidade de relatório executivo. Não cabe em
sustentação e não deve ser embutido de graça no Portal MVP: vira aditivo com
escopo e horas próprios.

Dizer isso agora é mais barato que dizer depois. Uma tela de diretoria
construída dentro da franquia de 20h/mês consome a franquia inteira e ainda
gera a expectativa de que a próxima também sai assim.

### O que muda no plano

Nada é jogado fora, mas a ordem fica obrigatória — cada visão depende do
alicerce da anterior:

| | Visão | Camada | Enquadramento | Pré-requisito real |
|---|---|---|---|---|
| 1º | Operacional | F1 | sustentação | A3 |
| 2º | Orçamento | F2 | fronteira, a decidir por escrito | F0 feito **antes** de gastar + conta de faturamento |
| 3º | Diretoria | F3 | **aditivo** | F2 rodando com histórico suficiente para ter tendência |

E reforça o item urgente: **F0 não é preparação, é pré-requisito das duas
visões de cima.** Rótulo que não foi aplicado no momento do gasto não vira
rateio por fonte depois, e sem rateio por fonte a visão de orçamento responde
"gastamos X" sem conseguir dizer em quê — que é exatamente a pergunta que a
diretoria vai fazer em seguida.

---

## 6. O que trava o quê

| Camada | Depende de | Se não vier |
|---|---|---|
| F0 | nada | **perde valor a cada dia** — custo já gasto não se rateia depois |
| F1 | A3 (projeto GCP) | sem projeto não há `INFORMATION_SCHEMA` para consultar |
| F2 | A3 + `billing_account` + permissão de configurar export | fica-se com a visão de BigQuery, sem o resto da fatura |
| F3 | decisão comercial | — |

A permissão para configurar o billing export **não é a mesma** que criar o
projeto: exige papel na conta de faturamento, não no projeto. Vale pedir junto
de A3, ou vira uma segunda espera depois da primeira.

---

## 7. Recomendação

Fazer **F0 agora**, ainda esta semana, porque é a única parte com prazo
biológico — depende de decisão de rotulagem tomada antes do primeiro recurso
subir, e o ambiente ainda não existe.

Fazer **F1 quando o ambiente sair**, dentro de sustentação, como rota adicional
do Portal existente. É pouca coisa nova: uma view e uma tela burra, no mesmo
padrão da ADR 006.

**Não construir F2 e F3 por iniciativa própria.** Perguntar primeiro quem vai
ler o número. Se a resposta for "a diretoria", é BI, e BI é aditivo — o que é
uma resposta perfeitamente boa, desde que dita antes de gastar as horas.

## 8. O que este plano não resolve

O custo de nuvem do AlupData é **da Alup**, por cláusula 5ª. Uma tela mostra o
gasto; ela não decide profundidade de histórico do ONS, não escolhe entre
tarifa por demanda e capacidade reservada, e não autoriza ninguém a apagar
dado. Essas três decisões continuam sendo da contratante, e a maior delas — a
profundidade do histórico do ONS — precisa sair **antes da primeira carga**,
não depois de a fatura chegar.
