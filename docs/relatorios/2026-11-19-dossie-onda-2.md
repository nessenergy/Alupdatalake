---
titulo: Dossiê de homologação — Onda 2 — 19/11/2026 (rascunho)
documento: Dossiê de homologação
referencia: REL-2026-11-19-D · AlupData Fase 1
emitido_em: 19 de novembro de 2026
emitente: ness. Processos e Tecnologia Ltda.
destinatario: Alup — Leonardo Guiel Marques, Taina Ulhoa Mota, Mauricio Cardoso e Saulo Rodrigues
contrato: "CPS-01025/2026 — AlupData Fase 1: DataLake"
marco: Onda 2 — aceite (marco 3)
responsavel: Ricardo Esper
classificacao: Confidencial — uso restrito das partes
local_data: 19 de novembro de 2026
---

# Dossiê de homologação da Onda 2

As Ondas 0 e 1 foram aceitas por escrito em 05/10/2026 e faturadas (marcos 1 e 2).
Este dossiê reúne a evidência da Onda 2, cuja janela contratual terminou em 13/11,
fonte por fonte, **dizendo o que está pronto e o que não está**. Os números são de
19/11/2026, lidos pela conferência de cargas (workflow *Conferir cargas*) em dev e hml.

## 1. Resumo por item do escopo

| Item | Fonte | Situação em 19/11 | Evidência |
|---|---|---|---|
| 2.1 | CCEE agente credenciado | **parcial**: leitura real em 09/11 e medição carregada; o cadastro de pontos segue negado ao perfil 6166 (erro `4001`) | §3.1 |
| 2.2 | BBCE | **entregue**: carga real e agendamento ligados em dev e hml | §3.2 |
| 2.3 | Hubspot | **carregado** em 22/10 (dev e hml); sem agendamento até a Alup confirmar a periodicidade | §3.3 |
| 2.4 | TempoOK | **fora do escopo** (retorno da Alupar de 20/10, validado em 23/10); as 14,4 h já executadas ficam contabilizadas | — |
| 2.5 | Gold de preço e posição comercial | **entregue** para BBCE e Hubspot; o que falta depende do item 2.1 | §3.2, §3.3 |

Credenciais: Hubspot gravada em 20/10, BBCE em uso em 28/10 e CCEE em 09/11. As da ONS
(IPDO editável e ACOMPH) não têm registro de entrega.

## 2. Critérios

| Critério | Situação |
|---|---|
| Sete componentes por fonte | atendido em BBCE e Hubspot; CCEE com conector, Bronze, Silver, Gold e dicionário, e o cadastro de pontos bloqueado pela permissão |
| Carga real com sucesso | BBCE e Hubspot nos dois ambientes; CCEE: medição sim, cadastro não |
| Reprocessamento sem chamar a origem | atendido nas Ondas 0 e 1 e no item 26; não repetido para BBCE nem Hubspot |
| Agendamento em funcionamento | BBCE em dev e hml (última execução 18/11, `SUCESSO`); Hubspot e CCEE sem agendamento |

## 3. Fontes

### 3.1 CCEE — agente credenciado (2.1)

Leitura real em 09/11 com o usuário dedicado (24 medidas de um ponto, produção da CCEE).
O cadastro de pontos de medição (`ccee_pi_ponto_medicao`) segue sem sucesso em hml:
`Fault Server.4001`, perfil sem permissão (#462). Depende da Alupar ajustar o perfil.

### 3.2 BBCE (2.2)

| Medida | dev | hml |
|---|---:|---:|
| Linhas na Silver `bbce_curva_forward` (27/10 a 17/11) | 3.548 | 3.040 |
| Linhas na Gold `curva_forward_vigente` | 253 | 253 |
| Última execução (18/11) | `SUCESSO`: 1.524 extraídas, 6 inválidas, 1.518 carregadas | igual |

### 3.3 Hubspot (2.3)

Carga real em 22/10 nos dois ambientes. A Silver recusa negócio fora da regra e o envia à
quarentena: hoje há 1 (fechamento anterior à criação). A saúde aparece como `ATRASADA`
porque o conector está em `conectores_sem_agendamento`, por decisão registrada.
〔a conferir: linhas da Silver e da Gold `funil_comercial` em cada ambiente〕

## 4. O que fica para depois da emissão

| Pendência | Quem | Efeito |
|---|---|---|
| Perfil 6166 sem permissão para o cadastro de pontos da CCEE (#462) | Alupar | bloqueia o fechamento do item 2.1 e da Gold de posição comercial |
| Credenciais da ONS para IPDO editável e ACOMPH | Alupar | fontes seguem sem entrega |
| Periodicidade do Hubspot | Alupar | agendamento desligado |
| Conferência das linhas do Hubspot | ness. | preenche a §3.3 |

Os prazos e efeitos da cláusula 3ª ficam registrados como fato, sem decisão neste documento.
