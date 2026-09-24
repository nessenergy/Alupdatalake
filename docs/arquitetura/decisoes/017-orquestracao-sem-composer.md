# ADR 017 — Orquestração da Onda 3 em Cloud Workflows, não em Composer

**Status**: aceita · **Data**: 2026-09-11 · **Implementada**: 2026-09-23 ·
**Revê** a decisão de orquestração da
[ADR 004](004-sql-puro-e-orquestracao.md), que segue valendo nas Ondas 1 e 2.

> **Adendo de 23/09 — o mecanismo existe.** `infra/modules/orquestracao`
> declara o fluxo `alupdata-onda3`: executa em paralelo as ingestões da cadeia,
> espera todas, compila a release `main` do Dataform e acompanha a invocação
> até o estado terminal. Falha em qualquer etapa para o fluxo. A cadeia vem da
> variável `cadeia_onda3`, hoje vazia — **com ela vazia, nenhum recurso é
> criado**, porque as fontes internas dependem de VPN e credencial (A7). O que
> a primeira fonte interna vai exigir é acrescentar o rótulo dela à variável;
> o fluxo não muda.
>
> A validação possível hoje é de estrutura: o YAML renderizado é lido e os
> `next` são conferidos contra os passos que existem
> (`tests/unit/test_orquestracao.py`). Semântica de conector e de `parallel` só
> o primeiro deploy com cadeia real responde.

## Contexto

A Alup respondeu **E2** em 11/09: teto de **US$ 20/mês até novembro** e de até
**US$ 400/mês a partir de meados de novembro**.

A estimativa que a ness. apresentou no
[registro de 09/09](../../relatorios/2026-09-09-esclarecimento-e1-e2.md), para
dimensionar esse mesmo teto, foi de **US$ 420 a 500/mês a partir da Onda 3, com
orquestração gerenciada**. O teto ficou abaixo da estimativa — e a Onda 3
começa em S12, depois de novembro.

O custo de infraestrutura é da contratante (cláusula 5ª). Estourar o teto não é
risco financeiro nosso; é risco de credibilidade e de alerta de orçamento
disparando todo mês num ambiente que nós operamos. Pior: o orçamento no GCP
**avisa, mas não interrompe** — o estouro seria descoberto na fatura.

Quase toda a diferença entre as duas faixas está numa linha só. Como a própria
ADR 004 registrou, **o Composer cobra por ambiente ligado, 24×7**, use-se ou
não. Cinco extrações diárias não pagam um scheduler permanente.

## Decisão

A Onda 3 **não migra para Cloud Composer**. A orquestração passa a
**Cloud Workflows disparado por Cloud Scheduler**, executando os mesmos Cloud
Run Jobs pela mesma CLI — o caminho que a ADR 004 deixou aberto ao dizer que
"a CLI única torna a migração barata".

O Composer volta à mesa apenas se aparecer necessidade que o Workflows não
cubra — sensores de arquivo, backfill com janela móvel gerenciada, SLA por
tarefa, ou exigência corporativa de Airflow por parte da Alup. Nesse caso é
**ADR nova, com o custo mensal explícito no texto** e decisão da contratante,
já que a conta é dela.

## Por que Workflows atende o que motivou o Composer

O gatilho combinado na ADR 004 era **dependência real entre pipelines**: fonte
interna alimentando view Gold que cruza fontes. Isso é sequência, paralelismo,
condicional, repetição com espera e tratamento de falha — tudo que o Workflows
expressa, e que é a parte do Airflow que este projeto usaria.

A diferença de custo é estrutural, não de tamanho: o Workflows cobra por passo
executado e o Composer, por ambiente de pé. Num projeto de 13 fontes com
execução diária, o primeiro é ruído na fatura e o segundo é a maior linha dela.

## Consequências

- O item **3.5 do plano de execução** deixa de ser "Migração para Cloud
  Composer" e passa a "Orquestração em Cloud Workflows". **As 10h não mudam** —
  o esforço é o mesmo e a medição do contrato não se altera.
- `dags/` deixa de ter destino previsto. O diretório fica como está, vazio, até
  que uma ADR futura o justifique; a orquestração vive no Terraform, como o
  agendamento das Ondas 1 e 2.
- A estimativa da Onda 3 sai da faixa de US$ 420–500 e volta à ordem de grandeza
  das ondas anteriores, mais o consumo de BigQuery — dentro do teto de US$ 400.
- O handoff da Onda 4 fica com uma peça a menos para a Alup operar. É a mesma
  razão pela qual a ADR 004 recusou dbt.
- A alternativa descartada é pedir à Alup que eleve o teto. Ela foi descartada
  por ser a que pede dinheiro para resolver um problema que o desenho resolve.

## Pendência

Confirmar as tarifas-premissa contra a tabela oficial de preços antes de
publicar qualquer número novo à contratante — a mesma pendência registrada no
item 4.6 da fila, hoje sem acesso à tabela.
