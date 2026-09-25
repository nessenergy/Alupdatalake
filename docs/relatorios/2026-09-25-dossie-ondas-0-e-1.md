---
titulo: Dossiê de homologação — Ondas 0 e 1 — 25/09/2026
documento: Dossiê de homologação
referencia: REL-2026-09-25-D · AlupData Fase 1
emitido_em: 25 de setembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup — Leonardo Guiel Marques, Taina Ulhoa Mota, Mauricio Cardoso e Saulo Rodrigues
contrato: CPS-01025/2026 — AlupData Fase 1: DataLake
marco: Ondas 0 e 1 — aceite
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 25 de setembro de 2026
---

# Dossiê de homologação das Ondas 0 e 1

Este dossiê reúne, critério por critério, a evidência de que as Ondas 0 e 1
estão prontas para aceite. É a base da reunião de aceite proposta na
[pauta de 25/09](2026-09-25-alinhamento.md): a reunião confere o que está
aqui, e não começa do zero.

**Em uma frase:** as **23 entidades públicas** estão carregadas com sucesso
nos ambientes de desenvolvimento e de homologação, cada uma com os sete
componentes do contrato. **Dois itens fecham depois desta emissão, em data
conhecida:** o terceiro dia seguido de carga agendada (26/09) e a demonstração
do Portal com login da Alup (na reunião, depende do pedido 6 da pauta).

Os números são de **25/09/2026, às 15h**, lidos diretamente do registro de
execuções (`bronze._execucoes`) e das tabelas Gold de cada ambiente.

## 1. Resumo dos critérios

| Critério | Onda 0 | Onda 1 | Evidência |
|---|---|---|---|
| Sete componentes por fonte | atendido | atendido — 23 de 23 | §3 |
| Carga real com sucesso | atendido | atendido — 23 de 23, nos dois ambientes | §3 |
| Portões de segurança do CI | atendido | atendido | §4.1 |
| Infraestrutura versionada e aplicada, sem pendência | atendido | atendido | §4.2 |
| Dicionário de dados e linhagem | atendido | atendido | §4.3 |
| Reprocessamento sem chamar a origem | atendido (câmbio, em dev) | atendido (carga do ONS, em hml) | §4.4 |
| Agendamento em funcionamento | 2 de 3 dias — o 3º em 26/09 | agendado; as mensais rodam no 1º ciclo de outubro | §4.5 |
| Portal com consulta real na camada Gold | publicado; demonstração na reunião | — | §4.6 |
| De-para das fontes do contrato | — | atendido | §5 |

## 2. Onda 0 — Fundação

| Item do escopo | Onde está | Situação |
|---|---|---|
| Mapeamento de fontes | [`dicionario-dados/README.md`](../dicionario-dados/README.md), com o de-para do §5 | entregue |
| 8 domínios analíticos | [`arquitetura/dominios-analiticos.md`](../arquitetura/dominios-analiticos.md), a partir da resposta da Alup ao item B1 | entregue |
| Dimensões comuns | seis dimensões em toda view Silver (`data_referencia`, `submercado`, `codigo_usina`, `agente_ccee`, `periodo_apuracao`, `periodo_apuracao_ccee`), cobradas por teste | entregue |
| CI/CD | CI a cada mudança; deploy e ingestão manual por workflow, com identidade federada e sem chave de serviço guardada | entregue |
| Portal base | publicado em dev e em hml, atrás do login corporativo (IAP) | entregue; demonstração na reunião (§4.6) |
| Fonte de referência | câmbio PTAX do Banco Central (`bcb_cambio_ptax`) | carregada nos dois ambientes |

A Onda 0 também entrega os dois registros técnicos que sustentam a operação:
o log de execução (`_execucoes`), base das visões `saude_ingestao` e
`volumetria_lake`, e o custo de consulta (`custo_consultas`), que o Portal lê.

## 3. Onda 1 — as 23 entidades públicas

Cada linha tem conector, tabela Bronze, view Silver, tabela Gold, testes,
agendamento e documentação com linhagem — os sete componentes da cláusula 2ª,
conferidos arquivo a arquivo em 25/09. As colunas de linhas são da **última
carga com sucesso** de cada ambiente.

| # | Entidade | Linhas — dev | Linhas — hml | Gold, em hml (linhas) |
|---|---|---:|---:|---|
| 1 | BCB — PTAX<br>`bcb_cambio_ptax` | 3 | 3 | `cambio_mensal` (1) |
| 2 | BCB — Selic e CDI<br>`bcb_juros` | 8 | 8 | `juros_mensal` (2) |
| 3 | IBGE — IPCA<br>`ibge_ipca` | 6 | 6 | `inflacao_mensal` (3) |
| 4 | ANEEL — SIGA<br>`aneel_siga` | 25.133 | 25.133 | `parque_gerador` (151) |
| 5 | ONS — carga<br>`ons_carga` | 116 | 116 | `carga_mensal_submercado` (8) |
| 6 | ONS — EAR (armazenamento)<br>`ons_ear` | 116 | 116 | `armazenamento_e_afluencia_mensal` (8) |
| 7 | ONS — ENA (afluência)<br>`ons_ena` | 116 | 116 | `armazenamento_e_afluencia_mensal` (8) |
| 8 | ONS — geração horária por usina<br>`ons_geracao_usina` | 693.120 | 675.816 | `geracao_mensal_usina_ons` (1.447) |
| 9 | ONS — capacidade instalada<br>`ons_capacidade` | 5.686 | 5.686 | `capacidade_instalada_vigente_usina` (2.062) |
| 10 | ONS — disponibilidade horária por usina<br>`ons_disponibilidade_usina` | 152.232 | 151.620 | `disponibilidade_mensal_usina` (317) |
| 11 | ONS — constrained-off eólico<br>`ons_restricao_coff_eolica` | 293.040 | 285.696 | `restricao_coff_mensal_usina` (475) |
| 12 | ONS — constrained-off fotovoltaico<br>`ons_restricao_coff_fotovoltaica` | 158.688 | 154.800 | `restricao_coff_mensal_usina` (475) |
| 13 | CCEE — PLD<br>`ccee_pld` | 6.336 | 6.240 | `pld_mensal_submercado` (12) |
| 14 | CCEE — perfis de agente<br>`ccee_perfil` | 60.509 | 60.509 | `agentes_ccee` (47.358) |
| 15 | CCEE — lista mensal de agentes<br>`ccee_agente` | 82.154 | 82.154 | `agentes_por_classe_mensal` (35) |
| 16 | CCEE — exposição financeira mensal<br>`ccee_exposicao_financeira` | 3 | 3 | `exposicao_mercado_mensal` (3) |
| 17 | CCEE — contabilização por perfil<br>`ccee_contabilizacao_perfil` | 141.889 | 141.889 | `resultado_contabilizacao_mensal_perfil` (141.889) |
| 18 | CCEE — geração horária por usina<br>`ccee_geracao_usina` | 2.964.096 | 5.821.056 | `geracao_mensal_usina` (7.958) |
| 19 | CCEE — montantes contratados por perfil<br>`ccee_contrato_montante` | 79.736 | 79.736 | `posicao_contratual_mensal_perfil` (79.736) |
| 20 | CCEE — consumo de varejo<br>`ccee_varejista_consumidor` | 10.007 | 10.007 | `consumo_varejista_mensal_uf` (6.805) |
| 21 | CCEE — ESS e serviços ancilares<br>`ccee_encargo_ess` | 3 | 3 | `encargos_setoriais_mensal` (3) |
| 22 | CCEE — energia de reserva (EER)<br>`ccee_energia_reserva` | 3 | 3 | `encargos_setoriais_mensal` (3) |
| 23 | CCEE — CVU estrutural<br>`ccee_cvu_estrutural` | 3.150 | 3.150 | `cvu_estrutural_vigente_usina` (1.335) |

Três leituras da tabela:

- **Linhas diferentes entre dev e hml** (geração e disponibilidade por usina,
  constrained-off, PLD) refletem a data de cada carga: hml carregou em 25/09 e
  dev em 24/09, com janelas que alcançam meses diferentes da publicação.
- **Gold pequena não é Gold vazia.** Câmbio, juros, encargos e exposição são
  mensais e resumidos: 1 a 3 linhas significam os meses publicados na janela.
- A entidade 1 (câmbio) abriu a Onda 0 como fonte de referência; o escopo da
  Onda 1 inclui o câmbio do BCB, e por isso ela conta nas 23.

## 4. Evidências

### 4.1 Portões de segurança

Na `main`, em 25/09, o CI e a análise de código passaram. A execução local
dos mesmos portões, na mesma data:

| Portão | Resultado |
|---|---|
| Lint e formatação | sem apontamento |
| Testes | 1.085 aprovados, cobertura de 94%; os pulados são os que dependem das credenciais das Ondas 2 e 3 ou não se aplicam ao caso |
| Análise estática de segurança (bandit) | sem apontamento |
| Auditoria de dependências (pip-audit) | nenhuma vulnerabilidade conhecida |
| Segredos no código | nenhum |

### 4.2 Infraestrutura

Todo recurso de nuvem está declarado no repositório e é aplicado pelo
workflow de deploy. Em 25/09, o `terraform plan` dos dois ambientes voltou
**sem nenhuma mudança** — o que está na nuvem é exatamente o que está no
código:

| Ambiente | Resultado do plan | Execução |
|---|---|---|
| dev (`alupar-dev-alupdata`) | No changes | [36152867077](https://github.com/nessenergy/Alupdatalake/actions/runs/36152867077) |
| hml (`alupar-hm-alupdata`) | No changes | [36152874459](https://github.com/nessenergy/Alupdatalake/actions/runs/36152874459) |

Para chegar a isso, uma diferença recorrente e sem efeito no Portal foi
eliminada no mesmo dia (#245).

### 4.3 Dicionário de dados e linhagem

Um documento por fonte em [`dicionario-dados/`](../dicionario-dados/README.md):
campos, tipos, regras de qualidade e o caminho origem → dado bruto → Bronze →
Silver → Gold. O índice traz o de-para do §5.

### 4.4 Reprocessamento

O dado bruto de cada carga fica guardado como veio. Reprocessar é ler esse
arquivo de novo, sem chamar a origem — útil quando uma regra muda ou uma
fonte sai do ar.

| Ambiente | Entidade | Data | Linhas | Execução de origem | Resultado |
|---|---|---|---:|---|---|
| dev | `bcb_cambio_ptax` | 24/09 17:21 | 3 | `d3b3429e…` | sucesso, registrado como `REPLAY` |
| hml | `ons_carga` | 25/09 11:15 | 116 | `3be4c275…` | sucesso, registrado como `REPLAY` |

### 4.5 Agendamento

O Cloud Scheduler tem **24 agendamentos em dev e 23 em hml**, todos ativos.
A diferença é o TempoOK, que é Onda 2 e só tem credencial em dev. Cada
entidade roda na cadência da sua publicação: diária (câmbio, juros, carga,
EAR, ENA), semanal (cadastros) ou mensal (CCEE e geração por usina).

A fonte de referência, o câmbio, em dev:

| Dia | Como rodou | Resultado |
|---|---|---|
| 24/09 | primeira carga, disparada pelo workflow | sucesso |
| 25/09 | agendamento das 09h | sucesso, 3 linhas |
| 26/09 | agendamento das 09h | **a conferir em 26/09** — registrado no `status.md` e mostrado na reunião |

As outras quatro diárias (juros, carga, EAR e ENA) também rodaram pelo
agendamento em 25/09, todas com sucesso. As mensais rodam no primeiro ciclo
de outubro (dias 5 a 7); até lá, a carga delas é a do workflow, na tabela do §3.

**Defeitos encontrados na primeira carga, todos corrigidos:** a geração por
usina da CCEE, a maior fonte (quase 6 milhões de linhas), exigiu janela, lote
e tempo limite próprios, e uma regra de qualidade que aceita geração líquida
levemente negativa (#229, #231, #232 e #233). A carga e a ENA do ONS tiveram
um erro de leitura em 24/09, corrigido no mesmo dia. Desde então, nenhuma
entidade pública falhou.

### 4.6 Portal

O Portal está publicado nos dois ambientes e lê as tabelas Gold. O acesso
passa pelo login corporativo do Google (IAP), que, na configuração adotada,
**só admite contas da organização da Alup** — contas da ness. são recusadas,
como deve ser. Por isso a evidência do Portal é a **demonstração na reunião
de aceite, com o login de alguém da Alup**. Para isso, a Alup indica os
grupos que terão acesso (pedido 6 da pauta), e a ness. os libera antes da
reunião.

Um exemplo do que o Portal mostra, a tabela `gold.juros_mensal` em dev:

| Mês | Série | Dias úteis | Taxa média ao dia (%) | Acumulada no mês (%) |
|---|---|---:|---:|---:|
| 2026-09 | Selic | 4 | 0,050788 | 0,2033068 |
| 2026-09 | CDI | 4 | 0,050788 | 0,2033068 |

## 5. Das 13 fontes do contrato às entidades

| Fonte contratual | Onda | Entidades | Situação em 25/09 |
|---|---|---|---|
| BCB | 0/1 | `bcb_cambio_ptax`, `bcb_juros` | entregue |
| IBGE | 1 | `ibge_ipca` | entregue |
| ANEEL | 1 | `aneel_siga` | entregue |
| ONS | 1 | 8 entidades (§3, linhas 5 a 12) | entregue |
| CCEE InfoMercado | 1 | 11 entidades (§3, linhas 13 a 23) | entregue |
| CCEE agente credenciado | 2 | nenhuma | depende de credencial de agente — pedido 4 da pauta |
| BBCE | 2 | `bbce_curva_forward` | conector pronto; aguarda acesso (pedido 3) |
| Hubspot | 2 | `hubspot_negocios` | conector pronto; aguarda token (pedido 3) |
| TempoOK | 2 | `tempook_boletins`, `tempook_ena_prevs` | carregando em dev; entra no dossiê da Onda 2 |
| Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | 3 | nenhuma | dependem de VPN e credenciais (pedido 7) |

As fontes das Ondas 2 e 3 **não fazem parte deste aceite** e estão listadas
para que nenhuma saia do escopo em silêncio.

## 6. O que fica para depois desta emissão

| Item | Quando | Depende de |
|---|---|---|
| Terceiro dia seguido de carga agendada do câmbio | 26/09 | nada — roda sozinho |
| Demonstração do Portal com login da Alup | reunião de aceite | grupos de acesso da Alup (pedido 6) |
| Quem assina o aceite | antes da reunião | Alup (pedido 1) |

## 7. Como conferir

Qualquer pessoa com leitura no projeto confere a §3 com uma consulta:

```sql
SELECT fonte, entidade, status, linhas_carregadas, iniciada_em
FROM bronze._execucoes
WHERE modo = 'FONTE'
QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY iniciada_em DESC) = 1
ORDER BY fonte, entidade
```

E o reprocessamento, com `WHERE modo = 'REPLAY'`.

Ricardo Esper — ness.
