# Dicionário de dados — índice e linhagem

O **componente 07** do contrato: cada fonte entrega, junto do conector e das
views, a documentação de campos e a linhagem origem → Bronze → Silver → Gold.
Este índice diz o que já existe, o que falta e — importante — **por que falta**.

Em **03/10/2026**, o índice cobre **57 fontes em 56 dicionários de fonte**
(eólico e fotovoltaico compartilham um documento), além de **2 dicionários
técnicos**. Bases reutilizáveis não entram nessa contagem. O contrato mantém
**13 fontes**; entidade implementada não cria uma fonte contratual nova.

## O que existe

| Fonte | Documento | Onda | Dimensão comum que alimenta | Gold que sustenta |
|---|---|---|---|---|
| ONS — carga | [`ons_carga.md`](ons_carga.md) | 1 | **`submercado`** | `carga_mensal_submercado` |
| ONS — EAR (armazenamento) | [`ons_ear.md`](ons_ear.md) | 1 | `submercado` | `armazenamento_e_afluencia_mensal` |
| ONS — ENA (afluência) | [`ons_ena.md`](ons_ena.md) | 1 | `submercado` | `armazenamento_e_afluencia_mensal` |
| ONS — EAR por bacia | [`ons_ear_bacia.md`](ons_ear_bacia.md) | Aditivo 01 | — | `armazenamento_mensal_bacia` |
| ONS — ENA por bacia | [`ons_ena_bacia.md`](ons_ena_bacia.md) | Aditivo 01 | — | `afluencia_mensal_bacia` |
| ONS — EAR por reservatório | [`ons_ear_reservatorio.md`](ons_ear_reservatorio.md) | Aditivo 01 | `submercado` | `armazenamento_mensal_reservatorio` |
| ONS — ENA por reservatório | [`ons_ena_reservatorio.md`](ons_ena_reservatorio.md) | Aditivo 01 | `submercado` | `afluencia_mensal_reservatorio` |
| ONS — intercâmbio entre subsistemas | [`ons_intercambio_nacional.md`](ons_intercambio_nacional.md) | Aditivo 01 | — | `intercambio_mensal_subsistemas` |
| ONS — intercâmbio internacional | [`ons_intercambio_internacional.md`](ons_intercambio_internacional.md) | Aditivo 01 | — | `intercambio_internacional_mensal` |
| ONS — geração para exportação | [`ons_geracao_exportacao.md`](ons_geracao_exportacao.md) | Aditivo 01 | — | `exportacao_mensal` |
| ONS — balanço de energia | [`ons_balanco_energia.md`](ons_balanco_energia.md) | Aditivo 01 | `submercado` | `balanco_energia_mensal_subsistema` |
| ONS — CMO semi-horário | [`ons_cmo_semi_horario.md`](ons_cmo_semi_horario.md) | Aditivo 01 | `submercado` | `cmo_mensal_submercado` |
| ONS — carga programada (API) | [`ons_carga_programada.md`](ons_carga_programada.md) | Aditivo 01 | `submercado` (só nos 4 subsistemas) | `desvio_carga_programada_verificada_mensal` |
| ONS — carga verificada (API) | [`ons_carga_verificada.md`](ons_carga_verificada.md) | Aditivo 01 | `submercado` (só nos 4 subsistemas) | `desvio_carga_programada_verificada_mensal` |
| ONS — volume de espera recomendado | [`ons_volume_espera.md`](ons_volume_espera.md) | Aditivo 01 | `submercado` | `volume_espera_mensal_reservatorio` |
| ONS — CVU das térmicas | [`ons_cvu_termica.md`](ons_cvu_termica.md) | Aditivo 01 | `submercado` | `cvu_mensal_termica` |
| ONS — previsão versus programado (eólicas e solares) | [`ons_programacao_previsao.md`](ons_programacao_previsao.md) | Aditivo 01 | — | `previsao_x_programado_mensal_usina` |
| ONS — DESSEM, balanço de energia | [`ons_balanco_dessem.md`](ons_balanco_dessem.md) | Aditivo 01 | `submercado` | `balanco_dessem_mensal_subsistema` |
| CCEE — PLD | [`ccee_pld.md`](ccee_pld.md) | 1 | `submercado` | `pld_mensal_submercado` |
| CCEE — perfis de agente | [`ccee_perfil.md`](ccee_perfil.md) | 1 | **`agente_ccee`** | `agentes_ccee` |
| CCEE — lista mensal de agentes | [`ccee_agente.md`](ccee_agente.md) | 1 | `agente_ccee` | `agentes_por_classe_mensal` |
| CCEE — exposição financeira mensal | [`ccee_exposicao_financeira.md`](ccee_exposicao_financeira.md) | 1 | — | `exposicao_mercado_mensal` |
| CCEE — contabilização por perfil | [`ccee_contabilizacao_perfil.md`](ccee_contabilizacao_perfil.md) | 1 | — | `resultado_contabilizacao_mensal_perfil` |
| CCEE — geração horária por usina | [`ccee_geracao_usina.md`](ccee_geracao_usina.md) | 1 | `submercado` | `geracao_mensal_usina` |
| CCEE — montantes contratados por perfil | [`ccee_contrato_montante.md`](ccee_contrato_montante.md) | 1 | — | `posicao_contratual_mensal_perfil` |
| CCEE — consumo de varejo | [`ccee_varejista_consumidor.md`](ccee_varejista_consumidor.md) | 1 | `submercado` | `consumo_varejista_mensal_uf` |
| CCEE — ESS e serviços ancilares | [`ccee_encargo_ess.md`](ccee_encargo_ess.md) | 1 | — | `encargos_setoriais_mensal` |
| CCEE — energia de reserva (EER) | [`ccee_energia_reserva.md`](ccee_energia_reserva.md) | 1 | — | `encargos_setoriais_mensal` |
| CCEE — CVU estrutural | [`ccee_cvu_estrutural.md`](ccee_cvu_estrutural.md) | 1 | — | `cvu_estrutural_vigente_usina` |
| CCEE — CVU merchant | [`ccee_cvu_merchant.md`](ccee_cvu_merchant.md) | Aditivo 01 | — | `cvu_mensal_merchant` |
| CCEE — CVU conjuntural | [`ccee_cvu_conjuntural.md`](ccee_cvu_conjuntural.md) | Aditivo 01 | `agente_ccee` | `cvu_mensal_conjuntural` |
| CCEE — CVU conjuntural revisado | [`ccee_cvu_conjuntural_revisado.md`](ccee_cvu_conjuntural_revisado.md) | Aditivo 01 | `agente_ccee` | `cvu_conjuntural_revisao_mensal` |
| CCEE — encargo de reserva (CONER) | [`ccee_reserva_encargo.md`](ccee_reserva_encargo.md) | Aditivo 01 | — | `reserva_encargo_mensal` |
| CCEE — TRC de segurança energética | [`ccee_energia_reserva_consumo_referencia.md`](ccee_energia_reserva_consumo_referencia.md) | Aditivo 01 | — | `consumo_referencia_energia_reserva_mensal` |
| CCEE — consumo por classe de agente | [`ccee_consumo_classe_agente.md`](ccee_consumo_classe_agente.md) | Aditivo 01 | — | `consumo_classe_agente_mensal` |
| ANEEL — SIGA | [`aneel_siga.md`](aneel_siga.md) | 1 | **`codigo_usina`** | `parque_gerador` |
| ACE Comercializadora — PRC | [`ace_prc.md`](ace_prc.md) | 1 | `submercado` | `prc_vigente_comercializadora` |
| ANEEL — tarifas homologadas das distribuidoras | [`aneel_tarifas.md`](aneel_tarifas.md) | 1 | — | `tarifa_vigente_distribuidora` |
| INMET — precipitação horária por estação | [`inmet_precipitacao.md`](inmet_precipitacao.md) | 1 | — | `precipitacao_diaria_estacao` |
| ONS — contornos das bacias (CC-BY) | [`ons_bacia_contorno.md`](ons_bacia_contorno.md) | 1 | — | `precipitacao_diaria_estacao` (coluna `bacia`) |
| ONS — geração horária por usina | [`ons_geracao_usina.md`](ons_geracao_usina.md) | 1 | `submercado`, `codigo_usina` | `geracao_mensal_usina_ons` |
| ONS — capacidade instalada | [`ons_capacidade.md`](ons_capacidade.md) | 1 | `submercado`, `codigo_usina` | `capacidade_instalada_vigente_usina` |
| ONS — disponibilidade horária por usina | [`ons_disponibilidade_usina.md`](ons_disponibilidade_usina.md) | 1 | `submercado`, `codigo_usina` | `disponibilidade_mensal_usina` |
| ONS — constrained-off eólico | [`ons_restricao_coff.md`](ons_restricao_coff.md) | 1 | `submercado` | `restricao_coff_mensal_usina` |
| ONS — constrained-off fotovoltaico | [`ons_restricao_coff.md`](ons_restricao_coff.md) | 1 | `submercado` | `restricao_coff_mensal_usina` |
| ONS — dados hidrológicos por reservatório (horário) | [`ons_dados_hidrologicos.md`](ons_dados_hidrologicos.md) | Aditivo 01 | `submercado` | `operacao_hidraulica_mensal_reservatorio` |
| ONS — energia vertida turbinável | [`ons_energia_vertida_turbinavel.md`](ons_energia_vertida_turbinavel.md) | Aditivo 01 | `submercado` | `vertimento_turbinavel_mensal_usina` |
| ONS — geração térmica por motivo de despacho | [`ons_geracao_termica_despacho.md`](ons_geracao_termica_despacho.md) | Aditivo 01 | `submercado`, `codigo_usina` | `despacho_termico_mensal_usina` |
| ONS — fator de capacidade de eólicas e solares | [`ons_fator_capacidade.md`](ons_fator_capacidade.md) | Aditivo 01 | `submercado`, `codigo_usina` | `fator_capacidade_mensal_usina` |
| BCB — PTAX | [`bcb_cambio_ptax.md`](bcb_cambio_ptax.md) | 0 | — | `cambio_mensal` |
| BCB — Selic e CDI | [`bcb_juros.md`](bcb_juros.md) | 1 | — | `juros_mensal` |
| BCB — IGP-M | [`bcb_igpm.md`](bcb_igpm.md) | 1 | — | `igpm_mensal` |
| IBGE — IPCA | [`ibge_ipca.md`](ibge_ipca.md) | 1 | — | `inflacao_mensal` |
| Hubspot — negócios | [`hubspot_negocios.md`](hubspot_negocios.md) | 2 | — | `funil_comercial` |
| TempoOK — boletins | [`tempook_boletins.md`](tempook_boletins.md) | 2 | — | `cobertura_boletins_tempook` |
| TempoOK — previsão de ENA (ENA-PREVS) | [`tempook_ena_prevs.md`](tempook_ena_prevs.md) | 2 | — | `cobertura_ena_prevs_tempook` |
| BBCE — curva forward | [`bbce_curva_forward.md`](bbce_curva_forward.md) | 2 | — | `curva_forward_vigente` |
| Log de execução | [`_execucoes.md`](_execucoes.md) | 0 | — | `saude_ingestao`, `volumetria_lake` |
| Custo de nuvem | [`_custo_consultas.md`](_custo_consultas.md) | 0 | — | `custo_consultas` |

## Das 13 fontes do contrato às 27 entidades

O de-para que o dossiê das Ondas 0 e 1 usa para conferir escopo: cada fonte
contratual e as entidades que a entregam. Entidade implementada não cria fonte
nova; fonte sem entidade diz por quê.

| Fonte contratual | Onda | Entidades |
|---|---|---|
| BCB | 0/1 | `bcb_cambio_ptax`, `bcb_juros`, `bcb_igpm` |
| IBGE | 1 | `ibge_ipca` |
| ANEEL | 1 | `aneel_siga`, `aneel_tarifas` |
| ACE Comercializadora (Alup) | 1 | `ace_prc` |
| INMET | 1 | `inmet_precipitacao` |
| ONS | 1 | `ons_bacia_contorno`, `ons_carga`, `ons_ear`, `ons_ena`, `ons_geracao_usina`, `ons_capacidade`, `ons_disponibilidade_usina`, `ons_restricao_coff_eolica`, `ons_restricao_coff_fotovoltaica` |
| CCEE InfoMercado | 1 | `ccee_pld`, `ccee_perfil`, `ccee_agente`, `ccee_exposicao_financeira`, `ccee_contabilizacao_perfil`, `ccee_geracao_usina`, `ccee_contrato_montante`, `ccee_varejista_consumidor`, `ccee_encargo_ess`, `ccee_energia_reserva`, `ccee_cvu_estrutural` |
| CCEE agente credenciado | 2 | nenhuma — depende de credencial de agente (item 2.1) |
| BBCE | 2 | `bbce_curva_forward` |
| Hubspot | 2 | `hubspot_negocios` |
| TempoOK | 2 | `tempook_boletins`, `tempook_ena_prevs` |
| Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | 3 | nenhuma — dependem de VPN e credenciais (A7) |

## A linhagem, em uma figura

O caminho é o mesmo para todas as fontes — é essa uniformidade que faz o
componente 07 ser barato de manter:

```
origem                       o que muda por fonte
  │
  ├─ extrair()               HTTP, arquivo, driver de banco ou planilha
  ├─ raw no GCS              gs://<projeto>-raw/{fonte}/{entidade}/dt=…/{id}.json.gz
  ├─ transformar()           renomeia campo, normaliza número, achata aninhado
  ├─ schema Pydantic         registro inválido é descartado e contado
  │
  ▼                          daqui em diante, mesmo fluxo para cada entidade
bronze.<fonte>_<entidade>    tabela append-only, particionada e clusterizada
  ▼
silver.<fonte>_<entidade>    view: tipagem, dedup por QUALIFY, 6 dimensões comuns
  ▼
gold.<pergunta_de_negocio>   tabela: uma pergunta nomeada por tabela, recarregada a cada execução
```

## O que falta, e por quê

As fontes abaixo **não têm dicionário, e não deveriam ter ainda**. A regra do
projeto é explícita: *schema por adivinhação continua proibido*. Documentar
campo que ninguém viu produz retrabalho com aparência de progresso — e o
dicionário é justamente o artefato que não pode mentir.

Em **14/09** a documentação recebida da Alup tirou quatro linhas desta tabela —
BBCE incluído, escrito no mesmo dia.

| Fonte | Onda | O que falta para escrever |
|---|---|---|
| CCEE — agente credenciado | 2 | Credencial de agente, que não foi pedida em A7; é escopo candidato, não escopo em curso ([ADR 018](../arquitetura/decisoes/018-vias-de-acesso-a-ccee.md)) |
| CCEE — demais conjuntos do InfoMercado | 1 | **Decidido em 14/09**: dos 204 conjuntos públicos, 24 entram por demanda dos domínios do B1, com fila nomeada ([ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md)). O que falta agora é ler cada arquivo — o schema não se escreve por adivinhação |
| Oracle FMB | 3 | VPN e schema documentado (A7 / [#12](https://github.com/nessenergy/Alupdatalake/issues/12)) |
| Portal Alup | 3 | Credenciais read-only; quais bases exatamente (A7 / [#13](https://github.com/nessenergy/Alupdatalake/issues/13)) |
| MySQL RDS — comercialização | 3 | Conectividade e usuário read-only (A7 / [#14](https://github.com/nessenergy/Alupdatalake/issues/14)) |
| RM / TOTVS | 3 | Definição de integração: API, view ou exportação (A7 / [#15](https://github.com/nessenergy/Alupdatalake/issues/15)) |

O **Hubspot** é a exceção que mostra a regra: a documentação era pública, então
o dicionário foi escrito antes do token — e o que não se pôde verificar sem
credencial está listado no fim do próprio documento, em vez de omitido. O
**TempoOK** seguiu o mesmo regime em 14/09, com uma diferença: lá o contrato foi
depois **verificado contra a API real**, e o que sobrou em aberto não é
conhecimento da origem, é acesso ao acervo ([#129](https://github.com/nessenergy/Alupdatalake/issues/129)).

O **motor de planilha** (S2 Data Intake) também não aparece na primeira tabela,
e por outro motivo: ele é uma *base* de conector, não uma fonte. Ganha
dicionário quando os templates concretos forem declarados, o que depende das
exemplos de planilha G3 ([#142](https://github.com/nessenergy/Alupdatalake/issues/142));
A4 já foi respondido em 11/09.

## Convenção

- Um arquivo por fonte, nomeado como o rótulo do conector (`fonte_entidade.md`).
- Sempre com: cabeçalho de identificação, particularidades que explicam decisões
  do conector, tabela de campos com a transformação aplicada, e a linhagem.
- **Sem dado real de cliente** — nem em exemplo. Vale a mesma regra do resto do
  repositório.
