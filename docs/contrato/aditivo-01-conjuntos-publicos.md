# Aditivo 01 — conjuntos públicos do ONS e da CCEE pedidos em 28/09/2026

**Classificação:** aditivo ao escopo dimensionado do contrato CPS-01025/2026.
Classificado pela coordenação da ness. em 28/09/2026. Este documento registra
o fundamento técnico e o controle de horas; a formalização contratual (valor,
prazo, aceite) é da coordenação com a Alup.

**Origem do pedido:** mensagem da Alup (Taina Mota) de 28/09/2026, com os
Dados Abertos do ONS marcados "a ser desenvolvido — ness." e uma lista de
datasets da CCEE. Cruzamento item a item em
[`planos/2026-09-28-fontes-pedidas-pela-alup.md`](../planos/2026-09-28-fontes-pedidas-pela-alup.md).

**Controle de horas:** toda hora gasta nestes itens é apontada contra este
aditivo, separada das 580h do contrato. Etiqueta `aditivo` no GitHub; tabela
da §5 atualizada a cada entrega.

---

## 1. O que está sendo pedido

26 conjuntos de dados públicos, nenhum lido hoje por conector do lake:

- **19 do ONS** — os 16 marcados no print, mais Carga de Energia Programada,
  Carga de Energia Verificada e Fator de Capacidade Eólica e Solar;
- **7 da CCEE** — CVU merchant, conjuntural e conjuntural revisado, encargo de
  reserva, consumo de referência da energia de reserva, consumo por classe de
  agente e consumo horário por perfil de agente.

Os **decks de rodadas oficiais da CCEE** (DESSEM, DECOMP, NEWAVE) também foram
pedidos. São arquivos de modelo, não tabelas, e ficam fora desta estimativa até
ter desenho próprio (§6).

## 2. Por que é aditivo — fundamento técnico

### 2.1 O contrato define fontes; o plano dimensionou as horas por fonte

O contrato lista **13 fontes** (cláusula 4ª, Onda 1: "conectores para APIs
públicas"). Não lista conjuntos de dados. O que traduz fonte em horas é o
[plano de execução](../plano-execucao.md), linha de base de **25/08/2026**,
anterior a qualquer entrega:

| Item | Fonte | Horas orçadas |
|---|---|---|
| 1.1 | CCEE InfoMercado | 32h |
| 1.2 | **ONS carga** | **28h** |

O item 1.2 nomeia **carga**. Dentro dele a ness. entregou **8 conjuntos do
ONS** (carga, EAR, ENA, geração por usina, capacidade, disponibilidade,
constrained-off eólico e fotovoltaico), e o item foi dado como concluído na
entrega da Onda 1, em 25/09. O dimensionamento da fonte ONS já absorveu sete
conjuntos além do que nomeava; os 19 pedidos agora vão além disso.

### 2.2 Precedente no próprio projeto: fonte pública não é "tudo o que ela publica"

A CCEE publica **204** conjuntos. A
[ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md), de
setembro, registrou que ingerir todos "seria pagar 7 componentes por arquivo
que ninguém pediu" e escolheu **24**, por demanda dos domínios. O ONS publica
**85**. Ler "ONS" no contrato como "os 85 conjuntos do ONS" não se sustenta
técnica nem financeiramente — e o projeto já tratou a questão assim, por
escrito, antes deste pedido.

### 2.3 Cada conjunto é um entregável completo, não um ajuste

Pela cláusula 2ª, toda fonte entrega **7 componentes**: conector, tabela
Bronze, view Silver, view Gold, testes, agendamento e documentação com
linhagem. Um conjunto novo não é uma coluna a mais num conector existente: é
um schema novo, uma tabela Bronze particionada, deduplicação própria na Silver,
Gold, testes, job agendado, alerta de silêncio e dicionário. A estimativa
está item a item na §4.

### 2.4 Quatro dos 26 exigem padrões técnicos que o projeto não tinha

Levantado no catálogo oficial em 28/09/2026 (API CKAN do ONS):

- **arquivo diário** — `programacao_x_previsao` (717 arquivos) e
  `balanco_dessem_geral` (490 arquivos): descoberta e download por dia;
- **API em vez de arquivo** — `carga-energia-programada` e
  `carga-energia-verificada`: o ONS não publica CSV, só API;
- **volume mensal alto** — `fator-capacidade-2` (34 MB/mês),
  `geracao-termica-despacho-2` (30 MB/mês), `dados_hidrologicos_ho` (20 MB/mês),
  `energia-vertida-turbinavel` (14 MB/mês): dimensionamento de memória e troca
  de nome do arquivo no meio da série.

### 2.5 O pedido é posterior à entrega

A Onda 1 foi entregue e o dossiê enviado em **25/09/2026**. O pedido chegou em
**28/09/2026**. É demanda nova sobre escopo entregue, e fica datada.

## 3. Os argumentos contrários, e a resposta

| Argumento que a Alup pode usar | Resposta |
|---|---|
| "O regime é de alocação de horas e a cláusula 1ª permite redefinir prioridades." | Correto, e é por isso que o controle é por hora. Redefinir prioridade dentro das 580h significa **tirar horas de outro item** — o que precisa ser escolhido pela Alup e registrado. Sem essa escolha, as horas destes conjuntos são adicionais às 580h. |
| "ONS é uma das 13 fontes contratadas; logo, está no escopo." | A fonte está; o **dimensionamento** dela é o do plano (28h, item 1.2), consumido pelos 8 conjuntos entregues. O mesmo raciocínio foi aplicado à CCEE na ADR 021. |
| "Mencionamos estes scripts na reunião de 18/09." | A menção não trouxe lista nem prioridade, e o plano não mudou. A lista chegou em 28/09, depois da entrega da Onda 1. |
| "O escopo de dado é a planilha da proposta." | Se a planilha nomear estes conjuntos, eles migram para o escopo e este aditivo se reduz. A conferência depende dos exemplos pedidos em G3 ([#142](https://github.com/nessenergy/Alupdatalake/issues/142)), ainda não recebidos. |

## 4. Estimativa item a item

Base: o padrão técnico de cada conjunto (§2.4), comparado com os 8 conjuntos
do ONS e os 11 da CCEE já entregues com os 7 componentes. É estimativa, não
medição; a hora que vale é a apontada na §5, item a item.

**ONS**

| # | Conjunto | Padrão | Horas |
|---|---|---|---|
| 1 | `intercambio-nacional` — Intercâmbios entre Subsistemas | A · CSV anual | 6 |
| 2 | `intercambio-internacional` — Intercâmbio do SIN com Outros Países | A · CSV anual | 5 |
| 3 | `balanco-energia-subsistema` — Balanço de Energia nos Subsistemas | A · CSV anual | 6 |
| 4 | `cmo-semi-horario` — CMO Semi-Horário | A · CSV anual, passo de 30 min | 6 |
| 5 | `cvu-usitermica` — CVU das Usinas Térmicas | A · CSV anual, revisões semanais (ADR 016) | 8 |
| 6 | `res_volumeespera` — Volume de Espera Recomendado | A · CSV anual | 5 |
| 7 | `ear-diario-por-bacia` — EAR Diário por Bacia | A · CSV anual | 4 |
| 8 | `ear-diario-por-reservatorio` — EAR Diário por Reservatório | A · CSV anual | 5 |
| 9 | `ena-diario-por-bacia` — ENA Diário por Bacia | A · CSV anual | 4 |
| 10 | `ena-diario-por-reservatorio` — ENA Diário por Reservatório | A · CSV anual | 5 |
| 11 | `geracao-exportacao-internacional` — Geração Comercial para Exportação | A · CSV anual | 5 |
| 12 | `dados_hidrologicos_ho` — Dados Hidrológicos por Reservatório, horário | B · CSV mensal, 20 MB | 10 |
| 13 | `energia-vertida-turbinavel` — Energia Vertida Turbinável | B · CSV mensal, 14 MB | 9 |
| 14 | `geracao-termica-despacho-2` — Geração Térmica por Motivo de Despacho | B · CSV mensal, 30 MB | 10 |
| 15 | `fator-capacidade-2` — Fator de Capacidade Eólica e Solar | B · CSV mensal, 34 MB | 10 |
| 16 | `programacao_x_previsao` — Previsão vs. Programado Eólicas/Solares | C · arquivo diário | 12 |
| 17 | `balanco_dessem_geral` — DESSEM, Balanço de Energia Geral | C · arquivo diário | 10 |
| 18 | `carga-energia-programada` — Carga de Energia Programada | D · API | 12 |
| 19 | `carga-energia-verificada` — Carga de Energia Verificada | D · API (reaproveita o 18) | 6 |
| | **Subtotal ONS** | | **138** |

**CCEE** — todos no padrão CKAN já usado por 11 conectores (`ccee_ckan.py`).

| # | Conjunto | Horas |
|---|---|---|
| 20 | `custo_variavel_unitario_merchant` | 4 |
| 21 | `custo_variavel_unitario_conjuntural` | 4 |
| 22 | `custo_variavel_unitario_conjuntural_revisado` | 4 |
| 23 | `reserva_encargo` | 4 |
| 24 | `energia_reserva_consumo_referencia` | 4 |
| 25 | `consumo_classe_agente` | 4 |
| 26 | `consumo_horario_perfil_agente` | 6 |
| | **Subtotal CCEE** | **30** |

**Total estimado: 168 horas** — 29% das 580h do contrato.

## 5. Controle de horas

Uma linha por conjunto entregue. "Horas apontadas" segue o mesmo critério do
painel do projeto: a hora estimada do item, reconhecida quando os 7
componentes estão entregues e a carga roda em `dev`.

| # | Conjunto | Estimado | Apontado | Entregue em | PR |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

**Apontado até agora: 0h de 168h.**

## 6. Fora desta estimativa

- **Decks da CCEE** (DESSEM diário, DECOMP semanal, NEWAVE mensal, do acervo,
  nunca o processo sombra): arquivos de entrada de modelo de otimização, não
  tabela de dados. Exigem desenho próprio — o que extrair de cada deck — antes
  de estimar.
- **Gold de negócio cruzando estes conjuntos:** cada conjunto sai com a sua
  Gold. Tabelas que cruzem vários deles dependem de regra de negócio a definir
  com a Alup.
