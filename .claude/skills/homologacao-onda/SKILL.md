---
name: homologacao-onda
description: Fecha uma onda do AlupData para homologação e medição — checklist de escopo por onda (0 a 4), evidências, dependências pendentes da Alup e os efeitos contratuais de atraso (postergação, ociosidade, suspensão). Use ao planejar, revisar progresso ou declarar concluída uma onda, ao preparar uma medição/marco, ou quando faltar insumo da contratante (token, VPN, credencial, planilha, RACI).
---

# Fechamento de onda — AlupData Fase 1

Cinco ondas, 19 semanas, 580h. Cada onda homologada é um marco de faturamento
(cláusula 6ª) e abre 30 dias de garantia (cláusula 9ª).

| Onda | Escopo | Semanas | Horas | Marco |
|---|---|---|---|---|
| 0 | Fundação: mapeamento de fontes, 8 domínios, dimensões comuns, CI/CD, portal base | 2 | 90h | 15,52% |
| 1 | APIs públicas: CCEE InfoMercado, ONS, ANEEL, IBGE, câmbio BCB | 5 | 120h | 20,69% |
| 2 | APIs credenciadas: CCEE credenciado, BBCE, Hubspot, TempoOK | 4 | 110h | 18,97% |
| 3 | Sistemas internos: Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | 5 | 155h | 26,72% |
| 4 | Planilhas (S2 Data Intake), Dataplex, KPIs Gold, documentação e handoff | 3 | 105h | 18,10% |

## Uma onda está pronta quando

- [ ] Toda fonte da onda tem os **7 componentes** (skill `conector-alupdata`)
- [ ] Portões de segurança verdes (skill `ssdlc-alupdata`)
- [ ] Recursos GCP declarados em `infra/` e aplicados no ambiente da onda
- [ ] Dicionário de dados e linhagem atualizados para cada fonte
- [ ] Reprocessamento demonstrado em pelo menos uma fonte da onda
- [ ] Evidências reunidas: `terraform plan` limpo, saída de `make all`, amostra
      de consulta Gold, prints do agendamento executando

Fonte que ficou de fora **é declarada explicitamente** no fechamento, com motivo
e dependência — nunca somem do escopo em silêncio.

## Dependências da contratante (cláusula 3ª)

| Prazo | Insumo |
|---|---|
| Onda 0 | Questionário de Gaps (47 perguntas), RACI, data owners, ferramenta de BI |
| Até Onda 2 | Tokens: CCEE credenciado, BBCE, Hubspot, TempoOK |
| Até Onda 3 | VPN e credenciais read-only: Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS |
| Até Onda 4 | Planilhas nos templates definidos na Onda 0 |

Efeitos de atraso, que valem a pena registrar **na data em que o atraso começa**,
não quando vira problema:

- **> 5 dias úteis** → cronograma postergado automaticamente
- **> 5 dias úteis em VPN/credenciais** → taxa de ociosidade de 4h/dia
- **> 20 dias corridos** → suspensão automática dos serviços

Quando um insumo atrasa: registre a data do pedido e da cobrança, siga com o que
não depende dele, e sinalize o impacto no cronograma antes que o prazo estoure.

## Fora de escopo (cláusula 5ª)

Custos de infra GCP · painéis de BI (exceto Portal MVP da Onda 0) · treinamento
de usuário final · modelos de IA/ML avançados. Pedido que caia aqui vira
proposta de aditivo, não vira commit.

## Regime

Alocação de horas — prioridade e sequência **podem** ser redefinidas durante a
execução (cláusula 1ª). O que não muda é o total de horas e o padrão dos 7
componentes.
