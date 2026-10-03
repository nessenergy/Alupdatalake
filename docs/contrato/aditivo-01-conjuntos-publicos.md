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
| 26 | `consumo_horario_perfil_agente` | ~~6~~ ver nota | ver §4.1 |
| | **Subtotal CCEE (20–25)** | **24** |

**Total estimado (itens 1–25): 162 horas** — 28% das 580h do contrato. Item
26 fica fora do subtotal, tratado a seguir.

### 4.1 Item 26 — achado que revisa a estimativa

Perfilado contra o recurso real da CCEE em 28/09/2026
(`consumo_horario_perfil_agente_202607`): **34,9 milhões de linhas, ~7,7 GB de
texto por mês**, 46.890 cargas distintas — granularidade por carga e hora, não
por agregado mensal como os outros seis itens da CCEE (que somam poucas
centenas de linhas por mês cada). Vinte e quatro meses de histórico são cerca
de **185 GB** de texto de origem.

As 6h estimadas seguiam o padrão dos outros conjuntos CKAN da CCEE (4-6h cada)
e não previam esse volume. Fica **fora desta entrega**, com dimensionamento
próprio a fazer antes de estimar — inclusive quanto histórico carregar em
`dev` e o custo de BigQuery esperado (regra 4 do contrato: o custo de
varredura é da Alup). Não bloqueia os itens 1–25.

## 5. Controle de horas

Uma linha por conjunto entregue. "Horas apontadas" segue o mesmo critério do
painel do projeto: a hora estimada do item, reconhecida quando os 7
componentes estão entregues e a carga roda em `dev`.

| # | Conjunto | Estimado | Apontado | Entregue em | PR |
|---|---|---|---|---|---|
| 1 | `intercambio-nacional` | 6 | 6 | 28/09/2026 | [#298](https://github.com/nessenergy/Alupdatalake/pull/298), fix [#305](https://github.com/nessenergy/Alupdatalake/pull/305) |
| 2 | `intercambio-internacional` | 5 | 5 | 28/09/2026 | [#298](https://github.com/nessenergy/Alupdatalake/pull/298), fix [#305](https://github.com/nessenergy/Alupdatalake/pull/305) |
| 3 | `balanco-energia-subsistema` | 6 | 6 | 28/09/2026 | [#298](https://github.com/nessenergy/Alupdatalake/pull/298) |
| 4 | `cmo-semi-horario` | 6 | 6 | 28/09/2026 | [#299](https://github.com/nessenergy/Alupdatalake/pull/299) |
| 5 | `cvu-usitermica` | 8 | 8 | 28/09/2026 | [#299](https://github.com/nessenergy/Alupdatalake/pull/299) |
| 6 | `res_volumeespera` | 5 | 5 | 28/09/2026 | [#299](https://github.com/nessenergy/Alupdatalake/pull/299) |
| 7 | `ear-diario-por-bacia` | 4 | 4 | 28/09/2026 | [#295](https://github.com/nessenergy/Alupdatalake/pull/295) |
| 8 | `ear-diario-por-reservatorio` | 5 | 5 | 28/09/2026 | [#297](https://github.com/nessenergy/Alupdatalake/pull/297) |
| 9 | `ena-diario-por-bacia` | 4 | 4 | 28/09/2026 | [#297](https://github.com/nessenergy/Alupdatalake/pull/297) |
| 10 | `ena-diario-por-reservatorio` | 5 | 5 | 28/09/2026 | [#297](https://github.com/nessenergy/Alupdatalake/pull/297) |
| 11 | `geracao-exportacao-internacional` | 5 | 5 | 28/09/2026 | [#298](https://github.com/nessenergy/Alupdatalake/pull/298) |
| 12 | `ons_dados_hidrologicos` | 10 | 10 | 03/10/2026 | [#346](https://github.com/nessenergy/Alupdatalake/pull/346) |
| 13 | `ons_energia_vertida_turbinavel` | 9 | 9 | 03/10/2026 | [#346](https://github.com/nessenergy/Alupdatalake/pull/346) |
| 14 | `ons_geracao_termica_despacho` | 10 | 10 | 03/10/2026 | [#346](https://github.com/nessenergy/Alupdatalake/pull/346) |
| 15 | `ons_fator_capacidade` | 10 | 10 | 03/10/2026 | [#346](https://github.com/nessenergy/Alupdatalake/pull/346) |
| 16 | `ons_programacao_previsao` | 12 | 12 | 03/10/2026 | [#344](https://github.com/nessenergy/Alupdatalake/pull/344) |
| 17 | `ons_balanco_dessem` | 10 | 10 | 03/10/2026 | [#344](https://github.com/nessenergy/Alupdatalake/pull/344) |
| 18 | `ons_carga_programada` | 12 | 12 | 03/10/2026 | [#345](https://github.com/nessenergy/Alupdatalake/pull/345) |
| 19 | `ons_carga_verificada` | 6 | 6 | 03/10/2026 | [#345](https://github.com/nessenergy/Alupdatalake/pull/345) |
| 20 | `custo_variavel_unitario_merchant` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |
| 21 | `custo_variavel_unitario_conjuntural` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |
| 22 | `custo_variavel_unitario_conjuntural_revisado` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |
| 23 | `reserva_encargo` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |
| 24 | `energia_reserva_consumo_referencia` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |
| 25 | `consumo_classe_agente` | 4 | 4 | 28/09/2026 | [#301](https://github.com/nessenergy/Alupdatalake/pull/301) |

**Apontado até agora: 162h de 162h** (itens 1–25; item 26 tratado em §4.1): 83h dos itens 1–11 e 20–25, mais 79h dos itens 12–19, entregues em 03/10/2026.

Evidência do item 7: carga em `dev` de 28/09, 14.976 linhas de 01/09/2024 a
27/09/2026, 23 bacias, zero inválidas; `gold.armazenamento_mensal_bacia`
recalculada pelo Dataform.

Evidência dos itens 1–6, 8–11 e 20–25: carga de 24 meses em `dev`, com
execução SUCESSO e Dataform recalculado. Linhas na Silver (vigente, já
deduplicada), contadas em 29/09/2026:

| # | Conector | Linhas | De | Até |
|---|---|---:|---|---|
| 1 | `ons_intercambio_nacional` | 72.672 | 01/09/2024 | 27/09/2026 |
| 2 | `ons_intercambio_internacional` | 35.688 | 01/09/2024 | 27/09/2026 |
| 3 | `ons_balanco_energia` | 90.720 | 01/09/2024 | 26/09/2026 |
| 4 | `ons_cmo_semi_horario` | 143.860 | 01/09/2024 | 28/09/2026 |
| 5 | `ons_cvu_termica` | 10.453 | 31/08/2024 | 19/09/2026 |
| 6 | `ons_volume_espera` | 21.224 | 01/09/2024 | 28/09/2026 |
| 8 | `ons_ear_reservatorio` | 57.259 | 01/09/2024 | 26/09/2026 |
| 9 | `ons_ena_bacia` | 17.411 | 01/09/2024 | 27/09/2026 |
| 10 | `ons_ena_reservatorio` | 117.167 | 01/09/2024 | 26/09/2026 |
| 11 | `ons_geracao_exportacao` | 18.024 | 01/09/2024 | 27/09/2026 |
| 20 | `ccee_cvu_merchant` | 349 | 02/2025 | 09/2026 |
| 21 | `ccee_cvu_conjuntural` | 1.229 | 03/2025 | 09/2026 |
| 22 | `ccee_cvu_conjuntural_revisado` | 1.125 | 02/2025 | 09/2026 |
| 23 | `ccee_reserva_encargo` | 24 | 09/2024 | 08/2026 |
| 24 | `ccee_energia_reserva_consumo_referencia` | 23 | 09/2024 | 07/2026 |
| 25 | `ccee_consumo_classe_agente` | 138 | 09/2024 | 07/2026 |

Os três CVU da CCEE começam em 2025 porque a própria CCEE só publica esses
conjuntos a partir de 2025. As datas finais seguem a defasagem de publicação
de cada origem.

Correções que a carga real exigiu: nos itens 1 e 2,
`intercambio_programado_mwmed` só existe na origem a partir de 2026, e o
acesso direto ao campo derrubava a execução de 2024/2025 (#305), achado pelo
log do contêiner (#303/#304, com `roles/logging.viewer` na SA de deploy). Nos
itens 21 e 22, o arquivo de 2025 publica o cabeçalho `CODIGO_MODELO_PREÇO`
(com cedilha) e CNPJ sem o zero à esquerda, e o código de modelo de preço se
repete no mês: a chave passou a ser (mês, parcela, leilão, produto) (#317).

### Evidência dos itens 12 a 19 (carga em `dev`, conferida em 03/10/2026)

Os oito itens têm os 7 componentes no repositório (conector, Bronze, Silver, Gold, testes, agendamento e dicionário) e a
carga rodou em **`dev`**. A conferência foi feita em 03/10/2026 pelo workflow `Conferir cargas`, que lê o BigQuery
somente para leitura com a conta de serviço de deploy (run `37103208999`, ambiente `dev`). Linhas na Silver:

| # | Conector | Linhas | De | Até |
|---|---|---:|---|---|
| 12 | `ons_dados_hidrologicos` | 3.009.821 | 01/09/2024 | 02/10/2026 |
| 13 | `ons_energia_vertida_turbinavel` | 2.774.427 | 01/09/2024 | 30/09/2026 |
| 14 | `ons_geracao_termica_despacho` | 2.363.064 | 01/09/2024 | 30/09/2026 |
| 15 | `ons_fator_capacidade` | 4.101.336 | 01/09/2024 | 30/09/2026 |
| 16 | `ons_programacao_previsao` | 18.998.832 | 01/10/2024 | 02/10/2026 |
| 17 | `ons_balanco_dessem` | 94.656 | 23/05/2025 | 02/10/2026 |
| 18 | `ons_carga_programada` | 1.206.288 | 01/09/2024 | 02/10/2026 |
| 19 | `ons_carga_verificada` | 1.207.008 | 01/09/2024 | 02/10/2026 |

A última execução de cada um dos oito em `bronze._execucoes` é `SUCESSO`, com zero linhas inválidas. O Dataform de `dev`
já tinha rodado `SUCCEEDED` sobre esses dados (deploys `37087604338` e `37094436585`), então as asserções das Silvers
passaram com dado real. A conferência desta rodada contou linhas na Silver; as Golds destes itens existem no
repositório, mas suas contagens em `dev` não foram feitas aqui.

**Ressalva de ambiente:** a carga conferida é a de `dev`. Em `hml` os oito têm **0 linhas** (run `37103149215`, de
03/10/2026): nunca foram carregados lá, e o critério do painel é a carga em `dev`.

Limitações de cada origem, conforme os dicionários de dados:

- **Item 16:** o ONS não publica arquivo anterior a 01/10/2024, um mês depois do início dos demais. A recarga não cabe numa
  execução do Cloud Run e segue o runbook, em janelas de até 3 meses.
- **Item 17:** o DESSEM só existe desde 23/05/2025; o histórico tem cerca de 16 meses, menor que os 24 do restante, por
  limite da origem.
- **Item 13:** o conector lê a série mensal, que começa em 2024-01, e recusa janela anterior.
- **Item 12:** a origem publica volume útil e vazões negativos e fora de faixa; Bronze e Silver guardam o que vem, e a
  Gold aplica a faixa de 0 a 100% ao volume útil (decisão que o dicionário deixa para o dono do domínio confirmar).
- **Item 14:** seis colunas entraram no arquivo do ONS ao longo da série e ficam nulas (nunca zero) nos meses anteriores.
- **Item 15:** a origem publica fator de capacidade negativo e acima de 1; o dado é guardado como publicado.
- **Item 18:** há dias sem publicação em algumas áreas; é lacuna da origem e o conector não preenche.
- **Item 19:** a origem publica carga negativa em algumas áreas (MMGD maior que a carga, áreas de perdas); aceita sem
  validação por sinal.

## 6. Fora desta estimativa

- **Decks da CCEE** (DESSEM diário, DECOMP semanal, NEWAVE mensal, do acervo,
  nunca o processo sombra): arquivos de entrada de modelo de otimização, não
  tabela de dados. Exigem desenho próprio — o que extrair de cada deck — antes
  de estimar.
- **Gold de negócio cruzando estes conjuntos:** cada conjunto sai com a sua
  Gold. Tabelas que cruzem vários deles dependem de regra de negócio a definir
  com a Alup.
