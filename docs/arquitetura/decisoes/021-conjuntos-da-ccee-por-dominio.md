# ADR 021 — Quais conjuntos do InfoMercado entram, e por qual domínio

**Status**: aceito · **Data**: 2026-09-14 · **Complementa** a
[ADR 018](018-vias-de-acesso-a-ccee.md) · **Depende** dos domínios do B1
([`dominios-analiticos.md`](../dominios-analiticos.md), item 0.10)

## 1. Contexto

A ADR 018 destravou a via pública da CCEE e entregou a primeira entidade,
`pld_horario_submercado`. Ela deixou a fila em aberto de propósito:

> As demais entram por demanda dos domínios analíticos, uma entidade por vez,
> cada uma com os 7 componentes.

Naquele momento os domínios não existiam. Agora existem — são os da resposta ao
**B1**, fechados em 14/09 — e a frase acima passou a ser executável.

O catálogo foi conferido contra a API real em **14/09**: `package_list` devolve
**204 conjuntos**. Esta ADR escolhe, entre eles, os que respondem às perguntas
dos oito domínios, e em que ordem.

## 2. Decisão

Entram os conjuntos abaixo, **por demanda do domínio que os pede**. Os títulos
e as descrições foram lidos do próprio catálogo em 14/09; o schema de cada um
só se escreve ao ler o arquivo, conforme a regra do projeto — *schema por
adivinhação continua proibido*.

### Mercado de Energia — Taina Mota · Gabriel Barreto (BBCE e prêmio)

| Conjunto | O que responde | Estado |
|---|---|---|
| `pld_horario_submercado` | preço à vista por submercado e hora | **entregue** (ADR 018) |
| `lista_perfil_v1` | cadastro de perfis; alimenta `agente_ccee` | **entregue** |
| `lista_agente_associado` | lista mensal de agentes — classe, situação de comercializador e de varejista, UF, categoria — com histórico por mês. **Não traz perfil**: o elo agente ↔ perfil já está em `lista_perfil_v1` | **entregue** |
| `consumo_horario_submercado` | consumo reconciliado usado na contabilização do MCP | a entrar |
| `custo_variavel_unitario_estrutural` | **CVU** por usina, combustível, leilão e produto | **entregue em 14/09** |
| `custo_variavel_unitario_conjuntural` e `_conjuntural_revisado` | CVU conjuntural e a sua revisão — o par revisado é caso de versionamento ([ADR 016](016-versionamento-de-recontabilizacao.md)) | a entrar |
| `encargo_ess_ancilar` | **ESS** — encargos de serviço do sistema | **entregue em 14/09** |
| `encargo_horario_submercado` | **ESS** — encargos de serviço do sistema, por submercado | a entrar |
| `energia_reserva_liquidacao` | **EER** — encargo de energia de reserva | **entregue em 14/09** |
| `energia_reserva_mensal_leilao` | **EER** — encargo de energia de reserva, mensal por leilão | a entrar |

O B1 nomeia PLD, EAR, ENA, CCEE (CVU, ESS, EER) e ONS. **EAR e ENA não são da
CCEE** — são do ONS, e entram por lá.

### Geração e Operacional — Taina Mota · Letícia Ferreira

| Conjunto | O que responde | Por quê |
|---|---|---|
| `geracao_horaria_usina` | geração individualizada por agente e período de comercialização | é a **granularidade de usina** que o A7 fixa para dado de portfólio |
| `geracao_horaria_submercado` · `geracao_fonte_primaria` | geração do SIN por submercado e por fonte | o subtema "usinas do SIN" |
| `garantia_fisica_fonte` · `garantia_fisica_lastro` | garantia física por fonte e lastro | base do GSF e do MRE |
| `mre_gf_modulada_usina` · `mre_mensal` | Mecanismo de Realocação de Energia | por usina, de novo na granularidade do A7 |

### Comercial e Contratos — Letícia Ferreira · Tahigo Santos

| Conjunto | O que responde | Subtema |
|---|---|---|
| `contrato_montante_compra_venda_perfil_agente` | montantes modulados de compra e venda por perfil de agente | book |
| `contrato_montante_mensal_tipo` · `contrato_montante_periodo` | montantes por tipo de contrato e por período | book |
| `sazonalizacao_contrato_ccearq` · `sazonalizacao_ccgf` | montantes sazonalizados | **sazonalização**, nomeada no B1 |
| `varejista_consumidor` · `varejista_subclasse` | consumo das parcelas de carga dos varejistas | **varejo** (Tahigo) |

### Risco e Compliance — Letícia Ferreira

| Conjunto | O que responde | Subtema |
|---|---|---|
| `exposicao_financeira_mensal` | exposição financeira no mês | **exposição**, nomeada no B1 |
| `contabilizacao_montante_perfil_agente` | resultados consolidados da contabilização por perfil | apuração |
| `montante_mensal_mcp_agente` · `sumario_mensal_liquidacao` | mercado de curto prazo e liquidação | apuração |
| `fator_ajuste_gf` · `premio_risco_hidrologico` · `repasse_risco_hidrologico` | ajuste de garantia física e risco hidrológico | **GSF** |
| `proinfa_usina` · `contrato_montante_mod_proinfa_agente` | Proinfa por usina e por agente | **Proinfa** |
| `penalidade_preco_mensal` | penalidades | compliance |

### Os quatro domínios que não bebem da CCEE

**Meteorologia** (TempoOK), **Econômico** (BCB e IBGE), **CRM e Marketing**
(Hubspot) e **Planejamento** (RM/TOTVS e planilhas) não têm conjunto no
InfoMercado. Registrar isso vale tanto quanto a lista: evita que alguém volte
aos 204 procurando o que não está lá.

## 2.1 O que a leitura dos arquivos corrigiu

Esta ADR foi escrita a partir do catálogo do CKAN — títulos e descrições de
`package_show`, sem abrir arquivo. A construção da fila leu os arquivos, e
quatro coisas só o arquivo (e a execução real) mostraram:

- **`lista_agente_associado` não tem coluna de perfil.** É a lista mensal de
  agentes — classe, situação de comercializador e de varejista, UF, categoria
  — com histórico por mês. O elo agente ↔ perfil está em `lista_perfil_v1`, já
  entregue.
- **`geracao_horaria_usina` é publicada em gzip mensal** — um recurso por mês
  (`_202403` … `_202607`), não um recurso corrente único.
- **`custo_variavel_unitario_estrutural` usa vírgula como delimitador** — o
  único CSV desta fonte que não usa `;`.
- **A leitura em fluxo termina no `extrair()`; o runner materializa o mês.**
  `CceeCsvCkan.extrair()` lê o gzip mensal em fluxo, mas
  `src/core/conector.py` (`_ingerir`) junta tudo numa lista antes de gravar o
  raw e validar — com `ccee_geracao_usina` e a janela de agendamento antiga
  (70 dias) isso abria 3-4 meses de uma vez (~9-12 milhões de linhas), acima
  do padrão de memória do Cloud Run Job. A janela caiu para 40 dias e o job
  ganhou `memoria`/`cpu` maiores como premissa a confirmar no 1º apply; lote
  por fatia no runner é mudança de framework, fora desta fila.

A ADR foi escrita do catálogo; o dicionário de cada entidade é a fonte a
partir daqui.

## 3. Ordem de entrada

Cada entidade custa os 7 componentes. Esta é uma **fila priorizada, não um
compromisso de escopo** — o contrato é por regime de horas e a prioridade pode
mudar; o padrão de entrega, não.

| Ordem | Conjunto | Por quê primeiro | Estado |
|---|---|---|---|
| 1 | `lista_agente_associado` | é dimensão, é barato, e completa o cadastro que dá nome a todo código das entidades seguintes | **entregue em 14/09** |
| 2 | `exposicao_financeira_mensal` · `contabilizacao_montante_perfil_agente` | **Risco e Compliance não tem nenhuma fonte hoje.** Sair de zero vale mais do que adensar um domínio já pronto | **entregue em 14/09** |
| 3 | `geracao_horaria_usina` | põe Geração e Operacional na granularidade de usina que o A7 pede | **entregue em 14/09** |
| 4 | `contrato_montante_compra_venda_perfil_agente` · `varejista_consumidor` | ver §4 | **entregue em 14/09** |
| 5 | CVU, ESS e EER | completam o que o B1 nomeia em Mercado de Energia, que já é o domínio mais maduro | **entregue em 14/09** |

As demais entidades desta ADR não entraram nesta fila. Cada uma entra pelo
mesmo caminho: subclasse de `CceeCsvCkan`, arquivo lido antes do schema:
`geracao_horaria_submercado`, `geracao_fonte_primaria`,
`garantia_fisica_*`, `mre_*`, `contrato_montante_mensal_tipo`,
`contrato_montante_periodo`, `sazonalizacao_*`, `varejista_subclasse`,
`montante_mensal_mcp_agente`, `sumario_mensal_liquidacao`, `fator_ajuste_gf`,
`premio_risco_hidrologico`, `repasse_risco_hidrologico`, `proinfa_*`,
`penalidade_preco_mensal`, `custo_variavel_unitario_conjuntural*`,
`encargo_horario_submercado`, `energia_reserva_mensal_leilao`,
`consumo_horario_submercado`.

## 4. O achado: parte de Comercial e Contratos tem via pública

O documento de domínios classifica **Comercial e Contratos** como *bloqueado —
depende de credencial (A7)*. Isso continua verdade para o book interno, que
vive no MySQL RDS e no Portal Alup.

Mas a CCEE publica, sem credencial, **montantes de compra e venda por perfil de
agente**, a sazonalização de CCEAR-Q e o consumo das parcelas de carga dos
varejistas. Não é o mesmo dado — é a visão que a Câmara tem da Alupar, não o
contrato como a Alup o registra —, e não substitui o interno.

Ainda assim muda uma frase do plano: **o domínio de maior valor deixa de estar
100% parado à espera de A7.** Dá para começar por fora e cruzar por dentro
quando a credencial chegar.

**Uma ressalva de confidencialidade**: a resposta F1 classifica como
confidencial o consumo por cliente vindo da CCEE. `varejista_consumidor` cai
nessa categoria e o dataset é interno (F4), com acesso restrito por tipo de
usuário (F2). Não muda a decisão; muda quem lê.

## 5. O que fica de fora, e por quê

- **As derivadas do PLD** — `pld_media_diaria`, `pld_media_semanal`,
  `pld_media_mensal`, `pld_final_medio`. Todas se obtêm agregando a série
  horária que já está no lake. Ingerir a média publicada seria guardar duas
  vezes o mesmo fato, e criar a chance de os dois discordarem.
- **Os conjuntos `*_sandbox`** (`rd_disp_*`) — são ambiente de teste da
  própria CCEE.
- **Fundos e encargos setoriais** — CCC, CDE, RGR, Itaipu, cota nuclear. São
  dado de distribuidora e de fundo setorial; nenhum dos oito domínios pergunta
  por eles. Entram se alguém perguntar, não por completude.
- **`pld_sombra` e `pldx_valor_anual`** — não há pergunta de domínio que os
  peça hoje.

Dos 204, esta ADR escolhe **24**. Os outros 180 não estão descartados: estão
sem demanda. A diferença importa, porque o critério de entrada é a pergunta do
domínio, e não a existência do arquivo.

## 6. Consequências

- O item **1.1 do plano** (CCEE InfoMercado, 32h) deixa de ser "bloqueada" e
  passa a ter fila nomeada.
- O `README.md` do dicionário de dados perde a linha "CCEE — demais conjuntos
  do InfoMercado: falta decidir quais". A decisão é esta.
- **Risco e Compliance** deixa de ser o único domínio sem caminho: tem fonte
  pública identificada e é o segundo da fila.
- A lacuna do **mês CCEE**
  ([`visao-geral.md`](../visao-geral.md), Lacuna 2) passa a bloquear de verdade.
  Enquanto só havia dado do ONS e do BCB, ela era teórica; com contabilização
  no lake, agregação mensal que cruze CCEE com dado interno soma períodos
  diferentes sem avisar. **Vira o próximo item técnico da ness.**
- Cada entidade continua entregando os 7 componentes, uma por vez, como a
  ADR 018 estabeleceu.
