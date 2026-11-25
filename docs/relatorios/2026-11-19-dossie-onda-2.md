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

## 1. Escopo: o contrato e as mudanças de curso

O contrato prevê para a Onda 2 as fontes CCEE (agente credenciado), BBCE, Hubspot e TempoOK, mais as tabelas Gold de
preço e posição comercial. Três mudanças de curso alteram o que se mede:

- **TempoOK saiu do escopo** (retorno da Alupar de 20/10, validado em 23/10); as 14,4 h já executadas ficam contabilizadas.
- **A CCEE passou a entrar por SOAP**, com usuário dedicado, senha e certificado, e não por token (retorno de 20/10; reunião de 06/11).
- **O cadastro de pontos de medição da CCEE depende de permissão da Alupar** ao perfil 6166 (erro `4001`, #462). É uma
  dependência da contratante (cláusula 3ª), não um componente a construir; o conector trata o erro como `SEM_PERMISSAO`.

As credenciais da ONS (IPDO editável e ACOMPH) pertencem à Onda 1 e seguem registradas lá.

## 2. Resumo por item

| Item | Fonte | Situação em 19/11 | Evidência |
|---|---|---|---|
| 2.1 | CCEE agente credenciado | **entregue**: leitura real em 09/11 e medição carregada em dev e hml. Ressalva: cadastro de pontos aguarda a permissão da Alupar | §3.1 |
| 2.2 | BBCE | **entregue**: carga real e agendamento em dev e hml | §3.2 |
| 2.3 | Hubspot | **entregue**: carga real em 22/10 nos dois ambientes; agendamento criado em 19/11 (#482) | §3.3 |
| 2.4 | TempoOK | **fora do escopo**, com horas contabilizadas | — |
| 2.5 | Gold de preço e posição comercial | **entregue** para BBCE e Hubspot | §3.2, §3.3 |

Credenciais: Hubspot gravada em 20/10, BBCE em uso em 28/10 e CCEE em 09/11.

## 3. Fontes

### 3.1 CCEE — agente credenciado (2.1)

Leitura real em 09/11 com o usuário dedicado (24 medidas de um ponto, produção da CCEE) e medição carregada em dev e hml.
O cadastro de pontos (`ccee_pi_ponto_medicao`) segue sem sucesso em hml: `Fault Server.4001`, perfil sem permissão (#462).
Fica registrado como dependência da Alupar, sem prejuízo da entrega da medição.

### 3.2 BBCE (2.2)

| Medida | dev | hml |
|---|---:|---:|
| Linhas na Silver `bbce_curva_forward` (27/10 a 17/11) | 3.548 | 3.040 |
| Linhas na Gold `curva_forward_vigente` | 253 | 253 |
| Última execução (18/11) | `SUCESSO`: 1.524 extraídas, 6 inválidas, 1.518 carregadas | igual |

### 3.3 Hubspot (2.3)

Carga real em 22/10 nos dois ambientes. A Silver recusa negócio fora da regra e o envia à quarentena: hoje há 1
(fechamento anterior à criação), à espera de correção na origem. O agendamento estava fora por um registro antigo
("sem credencial") e foi corrigido no #482, aplicado em dev e hml em 19/11; a primeira execução agendada foi observada em 24/11 e confirma o componente.
Conferido em 19/11 nos dois ambientes: Silver `hubspot_negocios` com 208 negócios (criados de 20 a 21/10), Gold `funil_comercial` com 7 linhas e 1 negócio em quarentena.

## 4. O que fecha depois da emissão

| Pendência | Quem | Efeito |
|---|---|---|
| Permissão do perfil 6166 para o cadastro de pontos da CCEE (#462) | Alupar | complementa o item 2.1; não bloqueia a medição |
| Correção do negócio em quarentena | Alupar | a carga seguinte o traz de volta |

Prazos e efeitos da cláusula 3ª ficam registrados como fato, sem decisão neste documento.
