# Visão consolidada do AlupData

Posição em **12/11/2026**. Uma página para quem chega ao projeto agora. O detalhe e as evidências estão em
[`relatorios/2026-10-22-situacao-consolidada.md`](relatorios/2026-10-22-situacao-consolidada.md).

## O que é

Um data lake do Grupo Alupar na Google Cloud, em camadas **Bronze → Silver → Gold** (BigQuery, Dataform), alimentado por conectores Python que rodam como Cloud Run Jobs. Contrato CPS-01025/2026, entregue pela ness. em **5 ondas**, de 31/08/2026 a 08/01/2027.

Cada fonte só está entregue com os **7 componentes** da cláusula 2ª: conector, tabela Bronze, view Silver, view Gold, testes, agendamento e dicionário com linhagem.

## Onde estamos, por onda

| Onda | Tema | Janela | Estado |
|---|---|---|---|
| 0 | Fundação e arquitetura | 31/08 a 11/09 | **Aprovada** (05/10) |
| 1 | Mercado: APIs públicas | 14/09 a 16/10 | **Aprovada** (05/10), com IPDO e ACOMPH sem entrega |
| 2 | APIs com credenciais | 19/10 a 13/11 | **Em andamento**: Hubspot, BBCE e a medição da CCEE carregam em dev e hml; resta a ONS autenticada (IPDO e ACOMPH); TempoOK fora do escopo |
| 3 | Sistemas internos | 16/11 a 18/12 | **Em andamento**: MySQL Alup com código pronto e sem carga real; FMB depende da DCIDE; faltam esquemas |
| 4 | Planilhas, governança e handoff | 21/12 a 08/01/2027 | **Em andamento**: motor pronto; Drive aceito; faltam modelos de planilha |

## Em números

| | |
|---|---|
| Conectores | **64** registrados, todos com os 7 componentes presentes; Aditivo 01 com 25 de 25 itens entregues e o 26 em validação |
| Testes | **2.292 aprovados**, 607 ignorados por desenho (medido em 12/11); cobertura **96%** (medida em 22/10) |
| Ambientes | `dev` e `hml` aplicados; **produção ainda não existe**, com `prod.tfvars` e runbook de bootstrap prontos (agendamentos desligados) |
| Documentação | 30 ADRs, 64 dicionários, 11 runbooks |

## Como o projeto é organizado

| Pasta | Conteúdo |
|---|---|
| `src/` | conectores e o framework de ingestão (`src/core/`) |
| `definitions/` | Dataform: Bronze, Silver, Gold e asserções |
| `infra/` | Terraform de tudo que existe na GCP |
| `tests/` | testes unitários e de integração |
| `docs/` | contrato, arquitetura, decisões, runbooks, relatórios e planos |
| `painel/` | dados do painel público de acompanhamento |

## Depende de quem

| De | O quê |
|---|---|
| Alupar | valores da ONS; cadastro de pontos da CCEE (perfil negado) e a unidade e a regra da hora da medição; tabelas do MySQL Comercialização e datas das renomeações; negócio do Hubspot; RM/TOTVS; chamado com a DCIDE; pasta do Drive e planilhas modelo |
| ness. | bootstrap de produção (passos 1 a 9 do runbook, na conta da ness.); orçamento por ambiente; janela de aceite de prod; decidir sobre DECOMP e NEWAVE |

## Para auditar

- Regras do projeto e do contrato: [`AGENTS.md`](../AGENTS.md).
- Mapa de evidências por controle, com o comando que reproduz cada uma: [`auditoria.md`](auditoria.md).
- Estado atual e histórico: [`status.md`](status.md). Plano: [`plano-execucao.md`](plano-execucao.md).
