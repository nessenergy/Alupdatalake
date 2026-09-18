# Dicionário de dados — índice e linhagem

O **componente 07** do contrato: cada fonte entrega, junto do conector e das
views, a documentação de campos e a linhagem origem → Bronze → Silver → Gold.
Este índice diz o que já existe, o que falta e — importante — **por que falta**.

Em **18/09/2026**, o índice cobre **26 entidades em 25 dicionários de fonte**
(eólico e fotovoltaico compartilham um documento), além de **2 dicionários
técnicos**. Bases reutilizáveis não entram nessa contagem. O contrato mantém
**13 fontes**; entidade implementada não cria uma fonte contratual nova.

## O que existe

| Fonte | Documento | Onda | Dimensão comum que alimenta | Gold que sustenta |
|---|---|---|---|---|
| ONS — carga | [`ons_carga.md`](ons_carga.md) | 1 | **`submercado`** | `carga_mensal_submercado` |
| ONS — EAR (armazenamento) | [`ons_ear.md`](ons_ear.md) | 1 | `submercado` | `armazenamento_e_afluencia_mensal` |
| ONS — ENA (afluência) | [`ons_ena.md`](ons_ena.md) | 1 | `submercado` | `armazenamento_e_afluencia_mensal` |
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
| ANEEL — SIGA | [`aneel_siga.md`](aneel_siga.md) | 1 | **`codigo_usina`** | `parque_gerador` |
| ONS — geração horária por usina | [`ons_geracao_usina.md`](ons_geracao_usina.md) | 1 | `submercado`, `codigo_usina` | `geracao_mensal_usina_ons` |
| ONS — capacidade instalada | [`ons_capacidade.md`](ons_capacidade.md) | 1 | `submercado`, `codigo_usina` | `capacidade_instalada_vigente_usina` |
| ONS — disponibilidade horária por usina | [`ons_disponibilidade_usina.md`](ons_disponibilidade_usina.md) | 1 | `submercado`, `codigo_usina` | `disponibilidade_mensal_usina` |
| ONS — constrained-off eólico | [`ons_restricao_coff.md`](ons_restricao_coff.md) | 1 | `submercado` | `restricao_coff_mensal_usina` |
| ONS — constrained-off fotovoltaico | [`ons_restricao_coff.md`](ons_restricao_coff.md) | 1 | `submercado` | `restricao_coff_mensal_usina` |
| BCB — PTAX | [`bcb_cambio_ptax.md`](bcb_cambio_ptax.md) | 0 | — | `cambio_mensal` |
| BCB — Selic e CDI | [`bcb_juros.md`](bcb_juros.md) | 1 | — | `juros_mensal` |
| IBGE — IPCA | [`ibge_ipca.md`](ibge_ipca.md) | 1 | — | `inflacao_mensal` |
| Hubspot — negócios | [`hubspot_negocios.md`](hubspot_negocios.md) | 2 | — | `funil_comercial` |
| TempoOK — boletins | [`tempook_boletins.md`](tempook_boletins.md) | 2 | — | `cobertura_boletins_tempook` |
| BBCE — curva forward | [`bbce_curva_forward.md`](bbce_curva_forward.md) | 2 | — | `curva_forward_vigente` |
| Log de execução | [`_execucoes.md`](_execucoes.md) | 0 | — | `saude_ingestao`, `volumetria_lake` |
| Custo de nuvem | [`_custo_consultas.md`](_custo_consultas.md) | 0 | — | `custo_consultas` |

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
