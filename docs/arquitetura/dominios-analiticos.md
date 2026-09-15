# Os 8 domínios analíticos

**Item 0.10 do plano de execução** · Elaborado em 2026-09-14 a partir da
**resposta da Alup ao item B1** do [Questionário de Gaps](../questionario-gaps.md),
de 11/09. Revisto em 14/09 para corrigir a origem: a primeira versão derivava os
domínios de A1, que responde outra pergunta.

Este documento diz **o que o lake precisa responder**, e é o alvo contra o qual
as views Gold são escritas. Sem ele, cada Gold nasce de uma suposição diferente.

---

## 1. De onde vêm os domínios

Os domínios são os da **resposta ao B1**. Não são proposta da ness. — são a
divisão que a própria Alup usa, com dono nomeado para cada uma.

O quadro do B1 tem **11 linhas para 8 domínios**. A diferença não é
inconsistência: **um domínio aparece em mais de uma linha quando responsáveis
distintos tratam subtemas dele**. Três domínios se dividem assim, e 8 + 3 = 11.

| # | Domínio | Subtemas | Data owner |
|---|---|---|---|
| 1 | **Mercado de Energia** | PLD, EAR, ENA, CCEE (CVU, ESS, EER), ONS (carga, térmicas, geração) | Taina Mota · Inteligência de Mercado |
| | | BBCE e prêmio | Gabriel Barreto · Trading |
| 2 | **Geração e Operacional** | usinas do SIN e DESSEM | Taina Mota · Inteligência de Mercado |
| | | usinas da Alupar e medição | Letícia Ferreira · Gestão de Portfólio e Back-Office |
| 3 | **Meteorologia** | precipitação, vento, clima | Taina Mota · Inteligência de Mercado |
| 4 | **Comercial e Contratos** | book, sazonalização, garantias | Letícia Ferreira · Gestão de Portfólio e Back-Office |
| | | contratos de varejo e Hubspot | Tahigo Santos · Comercial |
| 5 | **CRM e Marketing** | leads, campanhas, documentos | Tahigo Santos · Comercial |
| 6 | **Risco e Compliance** | exposição, GSF, Proinfa | Letícia Ferreira · Gestão de Portfólio e Back-Office |
| 7 | **Econômico** | IPCA, Selic, câmbio, CDI | Letícia Ferreira · Gestão de Portfólio e Back-Office |
| 8 | **Planejamento** | orçamento, premissas | gestores da Comercialização: Letícia Ferreira, Tahigo Santos e Taina Mota |

Contato de cada dono em [`interlocutores.md`](../interlocutores.md). O prazo do
B3 — **3 dias úteis** para dúvida de regra de negócio — vale por domínio.

### O que A1 responde, e por que não é isto

O item **A1** perguntou o que o DataLake precisa responder **como um todo**, e a
Alup respondeu com oito objetivos de programa: base única e integrada; automação
de processos operacionais; relatórios e dashboards atualizados; qualidade e
rastreabilidade do dado; decisão orientada por dados; escalar o negócio; novos
produtos e negócios; base preparada para IA.

São a finalidade do lake, não seus assuntos — não nomeiam chave, granularidade
nem fonte. **A2** ordena esses objetivos (1, 2 e 3 primeiro) e é dele que sai a
ordem de entrega da §4. Os domínios, esses, vêm do B1.

---

## 2. Abrangência do dado

As **6 coligadas contratantes** (FGE, IJUI, FOZ, QUELUZ, LAVRINHAS, VERDE 08)
respondem pelo **faturamento** do contrato, com rateio igualitário (cláusula 5ª).
**Elas não delimitam o dado.**

O escopo de dado é o que já estava mapeado na **planilha da proposta**, desde
antes dela — a mesma que o G4 cita como fonte de periodicidade e manutenção de
cada planilha. Dentro dele:

| O que | Fonte de dados |
|---|---|
| Usinas — todos os ativos do grupo, não só os das coligadas | **CCEE** |
| Clientes varejistas | **Portal Alup** |
| Demais itens mapeados na planilha | as fontes que a planilha já nomeia |

Tudo isso é **Fase 1**. A resposta ao **D2** diz o mesmo pelo outro lado: os
códigos de agente CCEE "não são só das 6 coligadas — são todos os ativos e
também os clientes varejistas".

---

## 3. Os domínios, um a um

Cada um traz a pergunta que responde, as fontes que o alimentam e o que já
existe em Gold. Ordenados pelo B1.

### 1 · Mercado de Energia

> **Quanto vale a energia, e o que o sistema está fazendo com ela — no curto prazo, no histórico e no futuro negociado?**

| | |
|---|---|
| **Fontes hoje** | `ccee_pld` (à vista, horário) · `ons_carga` · `ons_ear` · `ons_ena` · `bbce_curva_forward` (futuro negociado) · `ccee_perfil` (60 mil perfis) · `ccee_agente` · `ccee_encargo_ess` · `ccee_energia_reserva` · `ccee_cvu_estrutural` |
| **Fontes a conectar** | — a hidrologia (EAR e ENA) entrou em 15/09 |
| **Granularidade** | submercado e hora, para o PLD; submercado e dia, para a carga; vértice de entrega, para a curva |
| **Cadência** | PLD mensal, por fechamento da CCEE; carga diária; curva por pregão |
| **Gold hoje** | `pld_mensal_submercado`, `carga_mensal_submercado`, `mercado_mensal_submercado`, `armazenamento_e_afluencia_mensal`, `curva_forward_vigente`, `agentes_ccee`, `agentes_por_classe_mensal`, `encargos_setoriais_mensal`, `cvu_estrutural_vigente_usina` |
| **Situação** | **pronto do lado da CCEE** — faltam EAR e ENA, que são do ONS |

É o domínio mais maduro e o que sustenta os demais: quase toda pergunta
comercial termina comparada a um preço.

`ccee_perfil` fica aqui porque é o cadastro do mercado — é ele que dá nome ao
que em toda outra fonte é código, e alimenta a dimensão comum `agente_ccee`
([`visao-geral.md`](visao-geral.md)).

**O subtema de Trading tem uma regra em aberto**: o prêmio sobre o PLD não tem
fórmula definida, e inventá-la seria escolher pelo cliente
([`bbce_curva_forward.md`](../dicionario-dados/bbce_curva_forward.md)). Depende
do Gabriel Barreto.

### 2 · Geração e Operacional

> **Quais ativos existem, quanto cada um gerou, quanto foi medido — e quanto
> deixaram de gerar porque o sistema os limitou?**

| | |
|---|---|
| **Fontes hoje** | `aneel_siga` (cadastro público) · `ccee_geracao_usina` · `ons_geracao_usina` · `ons_capacidade` · `ons_disponibilidade_usina` · `ons_restricao_coff_eolica` · `ons_restricao_coff_fotovoltaica` |
| **Fontes a conectar** | térmicas do ONS (`cvu-usitermica`, `geracao-termica-despacho-2`) · `fator-capacidade-2` · DESSEM · **Oracle FMB** (Onda 3, medição do portfólio) — o constrained-off de eólica e solar entrou em 15/09 |
| **Granularidade** | **usina** — a granularidade que A7 fixa para dado de portfólio |
| **Cadência** | semanal para o cadastro público; mensal para a geração da CCEE; diária para medição, na janela das 22h às 6h (C9) |
| **Gold hoje** | `parque_gerador`, `geracao_mensal_usina`, `geracao_mensal_usina_ons`, `capacidade_instalada_vigente_usina`, `disponibilidade_mensal_usina`, `restricao_coff_mensal_usina`, `de_para_usina` |
| **Situação** | **parcial** — geração na granularidade de usina entregue; `codigo_usina` cruza ANEEL↔ONS desde 15/09 (`gold.de_para_usina`); falta a sigla interna (#141) |

**Tem um bloqueio nomeado**: o item D1 informa que a Alup identifica os ativos
por **sigla interna** (FGE, FOZ, IJU, QLZ, LVR, VD8, EAP I e II, PTB, EDV I a IV
e X, ALP, ALUP) e que **o CEG não é usado hoje**. CCEE e ONS usam ainda outros
nomes para os mesmos conjuntos. Ver §5.1.

### 3 · Meteorologia

> **Que chuva, vento e clima explicam a oferta que vem?**

| | |
|---|---|
| **Fontes hoje** | `tempook_boletins` — boletim guardado como arquivo ([ADR 019](decisoes/019-boletim-do-tempook-como-arquivo.md)) |
| **Granularidade** | boletim |
| **Cadência** | por publicação |
| **Gold hoje** | `cobertura_boletins_tempook` |
| **Situação** | **pronto como arquivo** — a extração do conteúdo do boletim é escopo futuro ([#129](https://github.com/nessenergy/Alupdatalake/issues/129)) |

Enquanto o conteúdo não for extraído, o domínio responde "o boletim de tal dia
chegou", não "choveu quanto". A diferença é grande e está registrada.

### 4 · Comercial e Contratos

> **O que foi comprado e vendido, com quem, a que preço e para quando — e como está sazonalizado e garantido?**

| | |
|---|---|
| **Fontes hoje** | `hubspot_negocios` (funil, não contrato) · `ccee_contrato_montante` · `ccee_varejista_consumidor` |
| **Fontes a conectar** | **MySQL RDS de Comercialização** · **Portal Alup** — contratos de varejo (ambos Onda 3) |
| **Granularidade** | contrato e perfil de agente |
| **Cadência** | diária, na janela das 22h às 6h (C9); mensal para os conjuntos públicos da CCEE |
| **Gold hoje** | `funil_comercial`, `posicao_contratual_mensal_perfil`, `consumo_varejista_mensal_uf` |
| **Situação** | **parcial pela via pública** — o book interno segue em A7 |

É o domínio de maior valor e o menos pronto. É ele que a prioridade 1 de A2
("base única e integrada") mais cobra, porque hoje vive em planilha (A3).

Os dois subtemas têm donos diferentes e fontes próprias: book, sazonalização e
garantias vêm do MySQL RDS; o varejo, do Portal Alup.

### 5 · CRM e Marketing

> **De onde vem o lead, o que a campanha gerou, e onde está o documento do negócio?**

| | |
|---|---|
| **Fontes hoje** | `hubspot_negocios` |
| **Granularidade** | negócio |
| **Cadência** | diária |
| **Gold hoje** | `funil_comercial` |
| **Situação** | **parcial, com limite de escopo declarado** |

**Contatos e empresas do Hubspot ficam fora do escopo**, por decisão da Alup de
11/09 (item F1): o que a plataforma não lê não faz parte do escopo, e CPF e
endereço não são tratados. Leads e campanhas, portanto, entram pelo que o objeto
de negócio carrega — não pelo cadastro de pessoa.

O conector segue parado à espera do token (A9, chamado a partir de 14/09).

### 6 · Risco e Compliance

> **Qual a exposição, e quanto o GSF e o Proinfa mudam o resultado?**

| | |
|---|---|
| **Fontes hoje** | `ccee_exposicao_financeira` · `ccee_contabilizacao_perfil` (com histórico de recontabilização) |
| **Fontes a conectar** | **Balanço Energético**, no MySQL RDS (Onda 3) |
| **Granularidade** | perfil de agente e mês de apuração |
| **Cadência** | mensal, por fechamento |
| **Gold hoje** | `exposicao_mercado_mensal`, `resultado_contabilizacao_mensal_perfil` |
| **Situação** | **iniciado** — saiu de zero sem credencial |

O item D5 já definiu a regra mais difícil deste domínio: **recontabilização se
versiona, não se sobrescreve** — registrado na
[ADR 016](decisoes/016-versionamento-de-recontabilizacao.md). A lacuna do mês
CCEE (§5.2) deixou de ser risco silencioso para este domínio: os dois
calendários convivem em colunas separadas, com asserção que avisa se divergirem.

### 7 · Econômico

> **Que indicador corrige valor no tempo, e que contexto macro explica o preço?**

| | |
|---|---|
| **Fontes hoje** | `bcb_cambio_ptax` · `bcb_juros` (Selic e CDI) · `ibge_ipca` |
| **Granularidade** | diária para câmbio, Selic e CDI; mensal para IPCA |
| **Cadência** | diária e mensal |
| **Gold hoje** | `cambio_mensal`, `juros_mensal`, `inflacao_mensal` |
| **Situação** | **pronto** — os quatro itens nomeados no B1 estão no lake |

Selic e CDI entraram em 14/09 pelas séries 11 e 12 do SGS, mesmo BCB do PTAX:
não são fonte nova para a cláusula 2ª, são entidade nova de fonte existente
([`bcb_juros.md`](../dicionario-dados/bcb_juros.md)).

O item D6 **não cita conversão para US$** — então câmbio entra como contexto, e
não como conversão obrigatória, até que alguém peça.

### 8 · Planejamento

> **Qual o orçamento, quais as premissas, e o realizado bate com elas?**

| | |
|---|---|
| **Fontes a conectar** | **RM/TOTVS** (C7, forma de integração pendente até 25/09) · planilhas pelo **S2 Data Intake** (Onda 4) |
| **Granularidade** | a definir com os donos |
| **Cadência** | mensal |
| **Gold hoje** | — |
| **Situação** | **não iniciado** — é o último em prontidão e o de dono mais distribuído |

É o único domínio com três donos ao mesmo tempo (os gestores da
Comercialização). Vale confirmar, antes de escrever a primeira Gold, quem
arbitra divergência de premissa.

---

## 4. Ordem de entrega

A prioridade de **A2** é "base única e integrada, automação e dashboards
atualizados". Traduzida para os domínios do B1 e cruzada com o que está
bloqueado:

| Ordem | Domínio | Por quê |
|---|---|---|
| 1 | **Mercado de Energia**, **Econômico**, **Meteorologia** | já têm fonte no lake; é o que dá dashboard atualizado sem depender de ninguém |
| 2 | **Geração e Operacional** (lado público) | cadastro pronto; o de-para público está em `gold.de_para_usina`, falta só a sigla interna (§5.1) |
| 3 | **CRM e Marketing** | destrava com o token do Hubspot, insumo pequeno |
| 4 | **Comercial e Contratos**, **Risco e Compliance** | maior valor, bloqueados em credencial (A7) |
| 5 | **Planejamento** | depende do RM/TOTVS (25/09) e dos templates da Onda 4 |

O item 1 **não depende da Alup**. É o que dá para avançar hoje.

---

## 5. Três lacunas que este documento nomeia

Duas seguem abertas; a 5.2 foi encerrada em 14/09 e fica registrada com o que se
aprendeu no caminho.

Não são pendências novas — são consequências das respostas de 11/09 que ainda
não tinham sido escritas em lugar nenhum.

### 5.1 A dimensão de usina precisa de um de-para — três quartos dele já existem

O item **D1** informa que a Alup identifica ativos por sigla interna e que o CEG
não é usado. A CCEE e o ONS usam nomes próprios. Hoje `codigo_usina` é
preenchido **só** pelo `aneel_siga`, com o CodCEG.

Sem uma tabela de correspondência entre **sigla interna ↔ CEG ↔ nome CCEE ↔ nome
ONS**, Geração e Operacional não cruza com Comercial e Contratos nem com Risco e
Compliance — e é justamente esse cruzamento que a prioridade 1 de A2 pede.

**O que mudou em 15/09**: o ONS publica o CEG junto do nome da usina, nas duas
fontes conectadas naquele dia (`ons_geracao_usina` e `ons_capacidade`). Três das
quatro colunas do de-para — **CEG ↔ nome ANEEL ↔ nome ONS** — passam a existir
dentro do próprio lake, materializadas em `gold.de_para_usina`.

Para que casassem foi preciso corrigir a chave: a ANEEL publica o último
segmento do CEG com um dígito e o ONS com dois, e o JOIN devolvia **zero** linha
em 2.047 usinas. Com o sufixo normalizado na ingestão (`src/core/ceg.py`),
**1.946 (95,1%)** casam.

**O que ainda destrava**: a Alup fornecer a lista de **siglas internas com o CEG
correspondente** — uma coluna, não quatro. É insumo pequeno e de efeito grande.

### 5.2 Os dois calendários — encerrada em 14/09

O item **D4** diz que valem **os dois calendários**: mês civil e mês CCEE.

O registro original desta lacuna dizia que todas as Silver derivavam
`periodo_apuracao` com `FORMAT_DATE`. **Não era verdade**: o `ccee_pld` trazia o
`MES_REFERENCIA` declarado pela CCEE sob o mesmo nome de coluna que nas outras
views guarda um valor derivado — duas proveniências, um nome, nenhum sinal.

Desde 14/09 são **duas colunas**: `periodo_apuracao`, derivado da data em todas
as views, e `periodo_apuracao_ccee`, o período que a origem declara, nulo onde
ela não declara nada. E uma asserção na Silver do PLD exige que os dois
coincidam.

Não definimos a regra do mês CCEE — seria inventar calendário do cliente. **No
dia em que os dois divergirem, a asserção falha e a regra se aprende do dado
real.** Detalhe em [`visao-geral.md`](visao-geral.md), Lacuna 2.

### 5.3 "Quase em tempo real" não é alcançável para fonte interna

O item A1 pede dashboards "quase em tempo real"; o item **C9** informa que os
sistemas internos só podem ser lidos das **22h às 6h**. São incompatíveis.

Para fonte interna, o máximo é **atualização diária**, com o dado da leitura da
noite anterior. Já está registrado na
[ADR 013](decisoes/013-ingestao-em-lote.md), e é expectativa a alinhar com a
Alup antes que um dashboard prometa outra coisa.

---

## 6. O que este documento não decide

**Não há KPI aqui, de propósito.** Os itens A5 e A6 informam que não existem
indicadores formalizados e que **defini-los não é objetivo desta fase** — eles
vêm no projeto de front, na Fase 2. A Gold desta fase é descritiva, conforme a
[ADR 012](decisoes/012-dataform.md).

Uma Gold sem KPI não é Gold incompleta: é Gold que não inventou a regra do
cliente.
