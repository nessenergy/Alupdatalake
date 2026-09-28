# Fontes públicas pedidas pela Alup em 28/09 — cruzamento com o lake

**Origem:** mensagem da Taina (Alup) de 28/09/2026, com prints dos Dados
Abertos do ONS marcados em verde ("script existente", da Alup) e vermelho
("a ser desenvolvido pela ness."), e uma lista de datasets dos Dados Abertos
da CCEE.

**Como foi conferido:** pelo identificador exato de cada dataset nos catálogos
oficiais (API CKAN do ONS e da CCEE, consultada em 28/09/2026), comparado com
o dataset que cada conector do lake lê. Não pelo título da lista, que às vezes
difere do arquivo.

**Estado:** a resposta de 28/09 foi enviada com parte destes itens "a
confirmar". Este documento fecha os que ficaram abertos e registra uma
correção. O próximo e-mail à Alup parte daqui (§4).

## 1. O que o lake já tem

| Pedido | Dataset de origem | Conector |
|---|---|---|
| Restrição por Constrained-off — Eólicas | ONS `restricao_coff_eolica_tm` | `ons_restricao_coff_eolica` |
| Restrição por Constrained-off — Fotovoltaicas | ONS `restricao_coff_fotovoltaica_tm` | `ons_restricao_coff_fotovoltaica` |
| Geração por Usina em Base Horária | ONS `geracao-usina-2` | `ons_geracao_usina` |
| EAR Diário por Subsistema | ONS `ear-diario-por-subsistema` | `ons_ear` |
| ENA Diário por Subsistema | ONS `ena-diario-por-subsistema` | `ons_ena` |
| Capacidade Instalada de Geração (marcada "a desenvolver" no print) | ONS `capacidade-geracao` | `ons_capacidade` |
| PLD_HORARIO | CCEE `pld_horario` | `ccee_pld` (ver §3) |
| ENCARGO_ESS_ANCILAR | CCEE `encargo_ess_ancilar` | `ccee_encargo_ess` |
| CUSTO_VARIAVEL_UNITARIO_ESTRUTURAL | CCEE `custo_variavel_unitario_estrutural` | `ccee_cvu_estrutural` |

Cobertura: cada conector lê o arquivo inteiro que a origem publica. O único
recorte é a janela de datas; não há filtro por usina, coligada ou grupo.

## 2. O que é novo

Nenhum destes é lido por conector do lake hoje. Todos existem no catálogo
oficial com o identificador abaixo.

**CCEE (7)**

| Pedido | Dataset |
|---|---|
| CUSTO_VARIAVEL_UNITARIO_MERCHANT | `custo_variavel_unitario_merchant` |
| CUSTO_VARIAVEL_UNITARIO_CONJUNTURAL | `custo_variavel_unitario_conjuntural` |
| CUSTO_VARIAVEL_UNITARIO_CONJUNTURAL_REVISADO | `custo_variavel_unitario_conjuntural_revisado` |
| RESERVA_ENCARGO | `reserva_encargo` (diferente de `energia_reserva_liquidacao`, que o lake já lê) |
| ENERGIA_RESERVA_CONSUMO_REFERENCIA | `energia_reserva_consumo_referencia` |
| CONSUMO_CLASSE_AGENTE | `consumo_classe_agente` |
| CONSUMO_HORARIO_PERFIL_AGENTE | `consumo_horario_perfil_agente` — "existente" na lista da Alup quer dizer que a Alup tem script próprio; o lake não o lê |

**ONS (3, que estavam "a confirmar")**

| Pedido | Dataset | Por que é novo |
|---|---|---|
| Carga de Energia Programada | `carga-energia-programada` | o lake lê `carga-energia` ("Carga de Energia Diária"), outro dataset |
| Carga de Energia Verificada | `carga-energia-verificada` | idem |
| Fator de Capacidade de Geração Eólica e Solar | `fator-capacidade-2` | o `fator_capacidade` de `gold.indicadores_mensais` é calculado pelo lake, não é este arquivo |

**ONS marcados em vermelho no print (16)**, novos:

1. Intercâmbios entre Subsistemas
2. Intercâmbio do SIN com Outros Países
3. Balanço de Energia nos Subsistemas
4. CMO Semi-Horário
5. CVU das Usinas Térmicas
6. Dados Hidrológicos de Reservatórios — Base Horária
7. Dados Hidrológicos — Volume de Espera Recomendado
8. Previsão versus Programado — Eólicas e Solares
9. DESSEM — Balanço de Energia Geral
10. EAR Diário por Bacia
11. EAR Diário por Reservatório
12. ENA Diário por Bacia
13. ENA Diário por Reservatório
14. Energia Vertida Turbinável
15. Geração Comercial para Exportação Internacional
16. Geração Térmica por Motivo de Despacho

Fora desta lista, também em vermelho no print: Fator de Capacidade (novo,
tabela acima) e Capacidade Instalada (já existe, §1). Os identificadores
exatos entram no plano de cada fonte.

**CCEE — decks de rodadas oficiais** (DESSEM diário, DECOMP semanal, NEWAVE
mensal, do acervo, nunca o processo sombra): não são datasets do CKAN, são
arquivos de modelo. Pedem desenho próprio antes de estimar.

## 3. Correção ao e-mail de 28/09: PLD_HORARIO

O e-mail disse "já temos". Vale para o **dado**, não para a **atualização**:

- a CCEE publica o mesmo PLD horário em dois datasets. O lake lia o
  `pld_horario_submercado`, que só sai depois do fechamento do mês — em 28/09
  ia até julho;
- o `pld_horario`, que a Alup cita, é atualizado todo dia e em 28/09 já tinha
  setembro até o dia 28;
- nas **20.352 horas em comum os valores são idênticos**.

**Já corrigido em 28/09** (PR #290): o conector passou ao `pld_horario`, o
agendamento de mensal para diário e o alerta de silêncio para 26 h. Em `dev`,
a carga de 28/09 trouxe até o próprio dia 28 (8.640 linhas: 90 dias × 24 h ×
4 submercados).

## 4. Para o próximo e-mail à Alup

Não enviar antes da reunião ser marcada; pode ir junto com o convite ou como
material dela. Pontos, na ordem:

1. **Correção do PLD, já resolvida** (§3): o lake passou ao dataset diário;
   o PLD chega com o mês corrente.
2. **Os 10 itens "a confirmar" estão fechados** (§2): os 7 da CCEE e os 3 do
   ONS são novos.
3. **Total de novos pedidos:** **7 CCEE + 19 ONS** (16 do print + Carga Programada, Carga Verificada e Fator de Capacidade) + decks da CCEE. Pedir à Alup
   que marque a **prioridade** e em que **onda** cada um entra (a Taina
   indicou Onda 1 ou 2). Enquadramento contratual — se entra nas horas das
   ondas ou é aditivo — é da coordenação, não deste documento.
4. **Os scripts que a Alup já tem** para os itens em verde: pedir que os
   mande, como a própria Taina ofereceu, para conferir contra os conectores do
   lake e para aproveitar a lógica nos itens novos.
5. **Acesso:** continua dependendo só do e-mail do grupo Google
   ([#261](https://github.com/nessenergy/Alupdatalake/issues/261)).
