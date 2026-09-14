# Os 8 domínios analíticos

**Item 0.10 do plano de execução** · Elaborado em 2026-09-14, a partir das
respostas da Alup ao [Questionário de Gaps](../questionario-gaps.md) de 11/09.

Este documento diz **o que o lake precisa responder**, e é o alvo contra o qual
as views Gold são escritas. Sem ele, cada Gold nasce de uma suposição
diferente.

---

## 1. Uma ressalva que precisa vir antes de tudo

O item **A1** do questionário pedia "as 8 perguntas de negócio que este DataLake
precisa responder no primeiro ano, em linguagem de negócio". A Alup respondeu
com oito itens:

> (1) base única e integrada; (2) automação de processos operacionais;
> (3) relatórios e dashboards atualizados, quase em tempo real; (4) qualidade e
> rastreabilidade do dado; (5) decisão orientada por dados; (6) escalar o
> negócio; (7) novos produtos, serviços e negócios; (8) base preparada para IA
> no futuro.

**Esses oito são objetivos do programa, não domínios analíticos.** São
legítimos e úteis — dizem para que o lake existe —, mas nenhum deles nomeia um
assunto sobre o qual se possa escrever uma tabela. "Escalar o negócio" não
define chave, granularidade nem fonte.

Registrar isso importa por dois motivos: a resposta **não está errada**, apenas
responde outra pergunta; e derivar os domínios em silêncio, como se A1 os
tivesse entregue, criaria um documento que parece acordado e não é.

**O que este documento faz, então**: propõe os oito domínios a partir do que de
fato é respondível hoje —

| Insumo | O que ele determina |
|---|---|
| **A2** — as 3 prioridades | a ordem de entrega |
| **A3** — como se responde hoje | o que já existe em planilha e dashboard, e que o lake substitui |
| **A4** — quem consome e com que frequência | a cadência de atualização de cada domínio |
| **A7** — granularidade | usina para dado de portfólio; usina, estado ou submercado para dado do SIN |
| **Bloco D** — regras de negócio | chave, calendário, versionamento e arredondamento |
| **As 9 fontes já conectadas** | o que se pode responder **hoje**, e não em tese |

**Isto é proposta da ness., para confirmação da Alup.** Cada domínio traz a
pergunta que ele responde; se a pergunta não for a certa, é barato trocar agora
e caro trocar depois da Gold escrita.

---

## 2. Os oito domínios

Ordenados por prontidão: os que já têm fonte no lake vêm primeiro.

### D1 · Preço de energia

> **Quanto vale a energia, hoje e no futuro contratado?**

| | |
|---|---|
| **Fontes** | `ccee_pld` (à vista, horário) · `bbce_curva_forward` (futuro negociado) |
| **Granularidade** | submercado e hora, para o PLD; vértice de entrega, para a curva |
| **Cadência** | PLD mensal (a CCEE publica por fechamento); curva por pregão |
| **Gold hoje** | `pld_mensal_submercado`, `curva_forward_vigente` |
| **Situação** | **pronto** — as duas fontes verificadas contra a API real |

É o domínio mais maduro e o que sustenta os demais: quase toda pergunta
comercial termina comparada a um preço.

### D2 · Carga e operação do SIN

> **Quanta energia o sistema consumiu, onde e quando?**

| | |
|---|---|
| **Fontes** | `ons_carga` · (candidatas: `consumo_horario_submercado` e `consumo_mensal_perfil_agente`, da CCEE) |
| **Granularidade** | submercado e dia |
| **Cadência** | diária |
| **Gold hoje** | `carga_mensal_submercado` |
| **Situação** | **pronto** para carga; o consumo por perfil depende de escolher entre os 204 conjuntos públicos da CCEE |

Cruza com D1 pela dimensão `submercado` — é esse cruzamento que explica preço
por escassez.

### D3 · Portfólio de geração

> **Quais ativos a Alupar tem, com que capacidade e onde?**

| | |
|---|---|
| **Fontes** | `aneel_siga` (cadastro público) · **Oracle FMB** (Onda 3, interno) |
| **Granularidade** | **usina** — é a granularidade que A7 fixa para dado de portfólio |
| **Cadência** | semanal para o cadastro público |
| **Gold hoje** | `parque_gerador` |
| **Situação** | **parcial** — o lado público está pronto; o lado interno depende de A7 |

**Tem um bloqueio nomeado**: o item D1 do questionário informa que a Alup
identifica os ativos por **sigla interna** (FGE, FOZ, IJU, QLZ, LVR, VD8, EAP I
e II, PTB, EDV I a IV e X, ALP, ALUP) e que **o CEG não é usado hoje**. CCEE e
ONS usam ainda outros nomes para os mesmos conjuntos. Ver §3.

### D4 · Cadastro de agentes e contrapartes

> **Quem são os participantes do mercado, e qual é o nosso perfil entre eles?**

| | |
|---|---|
| **Fontes** | `ccee_perfil` (60 mil perfis) · códigos das coligadas, que a Alup enviará (D2) |
| **Granularidade** | perfil de agente |
| **Cadência** | semanal |
| **Gold hoje** | `agentes_ccee` |
| **Situação** | **pronto** do lado público |

É a tabela de dimensão que dá nome a tudo que hoje é código. O item D2 informa
que os códigos **não são só das 6 coligadas** — incluem todos os ativos e os
clientes varejistas —, e que estão nos bancos da Alup.

### D5 · Posição comercial e contratos

> **O que foi comprado e vendido, com quem, a que preço e para quando?**

| | |
|---|---|
| **Fontes** | **MySQL RDS de Comercialização** · **Portal Alup** (ambos Onda 3) · `hubspot_negocios` (funil, não contrato) |
| **Granularidade** | contrato e perfil de agente |
| **Cadência** | diária (janela das 22h às 6h, item C9) |
| **Gold hoje** | `funil_comercial` apenas |
| **Situação** | **bloqueado** — depende de credencial (A7) |

É o domínio de maior valor e o menos pronto. É ele que a prioridade 1 de A2
("base única e integrada") mais cobra, porque hoje vive em planilha (A3).

### D6 · Contabilização e liquidação

> **Quanto se apurou no mercado de curto prazo, e como isso muda quando a CCEE recontabiliza?**

| | |
|---|---|
| **Fontes** | conjuntos de contabilização da CCEE (públicos) · **Balanço Energético**, no MySQL RDS (Onda 3) |
| **Granularidade** | perfil de agente e mês de apuração |
| **Cadência** | mensal, por fechamento |
| **Gold hoje** | — |
| **Situação** | **não iniciado**; a via pública existe e falta escolher os conjuntos |

O item D5 do questionário já definiu a regra mais difícil deste domínio:
**recontabilização se versiona, não se sobrescreve** — registrado na
[ADR 016](decisoes/016-versionamento-de-recontabilizacao.md).

### D7 · Conjuntura e indicadores macro

> **Que contexto econômico explica o preço e corrige o valor no tempo?**

| | |
|---|---|
| **Fontes** | `bcb_cambio_ptax` · `ibge_ipca` · `tempook_boletins` (boletim de mercado) |
| **Granularidade** | diária para câmbio; mensal para IPCA |
| **Cadência** | diária e mensal |
| **Gold hoje** | `cambio_mensal`, `inflacao_mensal`, `cobertura_boletins_tempook` |
| **Situação** | **pronto**, com a ressalva do TempoOK ([#129](https://github.com/nessenergy/Alupdatalake/issues/129)) |

O item D6 do questionário **não cita conversão para US$** — então câmbio entra
como contexto, e não como conversão obrigatória, até que alguém peça.

### D8 · Qualidade e rastreabilidade do dado

> **O dado chegou, está completo, e de onde ele veio?**

| | |
|---|---|
| **Fontes** | `bronze._execucoes` · linhagem do Knowledge Catalog · asserções do Dataform |
| **Granularidade** | execução de ingestão |
| **Cadência** | contínua |
| **Gold hoje** | `saude_ingestao`, `volumetria_lake` |
| **Situação** | **pronto** |

Este é o único domínio que **veio literal de A1** (item 4). Ele não é meio: é
entregável. Um lake que não sabe dizer se o dado de ontem chegou não substitui
a planilha que a pessoa conferia à mão.

---

## 3. Três lacunas que este documento nomeia

Estas não são pendências novas — são consequências das respostas de 11/09 que
ainda não tinham sido escritas em lugar nenhum.

### 3.1 A dimensão de usina precisa de um de-para, e ele não existe

O item **D1** informa que a Alup identifica ativos por sigla interna e que o
CEG não é usado. A CCEE e o ONS usam nomes próprios. Hoje `codigo_usina` é
preenchido **só** pelo `aneel_siga`, com o CodCEG.

Sem uma tabela de correspondência entre **sigla interna ↔ CEG ↔ nome CCEE ↔
nome ONS**, o domínio D3 não cruza com D5 nem com D6 — e é justamente esse
cruzamento que a prioridade 1 de A2 pede.

**O que destrava**: a Alup fornecer o de-para, ou a lista de siglas com o CEG
correspondente. É insumo pequeno e de efeito grande.

### 3.2 `periodo_apuracao` só existe em calendário civil

O item **D4** diz que valem **os dois calendários**: mês civil e mês CCEE.
Hoje todas as views Silver derivam `periodo_apuracao` com
`FORMAT_DATE('%Y-%m', data_referencia)` — que é só o civil.

O mês CCEE não coincide com o civil no fechamento da contabilização. Enquanto
a diferença não for modelada, qualquer agregação mensal que cruze dado da CCEE
com dado interno **soma períodos diferentes sem avisar**.

**O que destrava**: definir a regra do mês CCEE. É trabalho da ness., e entra
como item de 0.11 — ver [`visao-geral.md`](visao-geral.md).

### 3.3 "Quase em tempo real" não é alcançável para fonte interna

O item A1 pede dashboards "quase em tempo real"; o item **C9** informa que os
sistemas internos só podem ser lidos das **22h às 6h**. São incompatíveis.

Para fonte interna, o máximo é **atualização diária**, com o dado da leitura da
noite anterior. Já está registrado na
[ADR 013](decisoes/013-ingestao-em-lote.md), e é expectativa a alinhar com a
Alup antes que um dashboard prometa outra coisa.

---

## 4. Ordem de entrega

A prioridade de **A2** é "base única e integrada, automação e dashboards
atualizados". Traduzida para os domínios acima, e cruzada com o que está
bloqueado:

| Ordem | Domínio | Por quê |
|---|---|---|
| 1 | **D1, D2, D7** | já prontos; é o que dá dashboard atualizado sem depender de ninguém |
| 2 | **D4** | tabela de dimensão — barata, e dá nome a tudo |
| 3 | **D8** | é o que faz a base ser confiável, e a prioridade 1 é "base única e **integrada**" |
| 4 | **D3** | depende do de-para da §3.1 |
| 5 | **D5, D6** | maior valor, mas bloqueados em credencial (A7) |

Os itens 1 a 3 **não dependem da Alup**. São o que dá para avançar hoje.

---

## 5. O que este documento não decide

**Não há KPI aqui, de propósito.** Os itens A5 e A6 informam que não existem
indicadores formalizados e que **defini-los não é objetivo desta fase** — eles
vêm no projeto de front, na Fase 2. A Gold desta fase é descritiva, conforme a
[ADR 012](decisoes/012-dataform.md).

Uma Gold sem KPI não é Gold incompleta: é Gold que não inventou a regra do
cliente.
