# Visão consolidada do AlupData

Posição em **29/10/2026**. Uma página para quem chega ao projeto agora. O detalhe e as evidências estão em
[`relatorios/2026-10-22-situacao-consolidada.md`](relatorios/2026-10-22-situacao-consolidada.md).

## O que é

Um data lake do Grupo Alupar na Google Cloud, em camadas **Bronze → Silver → Gold** (BigQuery, Dataform), alimentado por conectores Python que rodam como Cloud Run Jobs. Contrato CPS-01025/2026, entregue pela ness. em **5 ondas**, de 31/08/2026 a 08/01/2027.

Cada fonte só está entregue com os **7 componentes** da cláusula 2ª: conector, tabela Bronze, view Silver, view Gold, testes, agendamento e dicionário com linhagem.

## Onde estamos, por onda

| Onda | Tema | Janela | Estado |
|---|---|---|---|
| 0 | Fundação e arquitetura | 31/08 a 11/09 | **Aprovada** (05/10) |
| 1 | Mercado: APIs públicas | 14/09 a 16/10 | **Aprovada** (05/10), com IPDO e ACOMPH sem entrega |
| 2 | APIs com credenciais | 19/10 a 13/11 | **Em andamento**: Hubspot e BBCE carregam em dev e hml; CCEE aguarda a Alupar; TempoOK fora do escopo |
| 3 | Sistemas internos | 16/11 a 18/12 | **Em andamento**: 2 de 3 bancos conectam; FMB depende da DCIDE; faltam esquemas |
| 4 | Planilhas, governança e handoff | 21/12 a 08/01/2027 | **Em andamento**: motor pronto; Drive aceito; faltam modelos de planilha |

## Em números

| | |
|---|---|
| Conectores | **58**, todos com os 7 componentes presentes |
| Testes | **2.138 aprovados**, 537 ignorados por desenho (medido em 29/10); cobertura **96%** (medida em 22/10) |
| Ambientes | `dev` e `hml` aplicados; **produção ainda não existe** |
| Saúde da ingestão | dev: 56 OK; hml: 55 OK |
| Documentação | 30 ADRs, 60 dicionários, 9 runbooks |

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
| Alupar | gravar os valores da ONS e da CCEE e informar o formato do certificado; tabelas do MySQL Comercialização e datas das renomeações; negócio do Hubspot; RM/TOTVS; chamado com a DCIDE; pasta do Drive e planilhas modelo |
| ness. | reaplicar o bootstrap em dev e hml; decidir a produção; decidir sobre DECOMP e NEWAVE |

## Para auditar

- Regras do projeto e do contrato: [`AGENTS.md`](../AGENTS.md).
- Mapa de evidências por controle, com o comando que reproduz cada uma: [`auditoria.md`](auditoria.md).
- Estado atual e histórico: [`status.md`](status.md). Plano: [`plano-execucao.md`](plano-execucao.md).
