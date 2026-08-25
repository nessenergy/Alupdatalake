---
name: conector-alupdata
description: Implementa um conector de fonte de dados do AlupData de ponta a ponta, com os 7 componentes obrigatórios do contrato (conector Python, tabela Bronze, view Silver, view Gold, testes pytest, agendamento GCP, documentação e linhagem). Use sempre que a tarefa envolver adicionar, alterar ou revisar uma fonte de dados — CCEE, ONS, ANEEL, IBGE, BCB, BBCE, Hubspot, TempoOK, Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS, planilhas S2 Data Intake — ou quando alguém pedir "novo conector", "ingestão de <fonte>", "camada Bronze/Silver/Gold de <fonte>".
---

# Conector AlupData — padrão de entrega

Cláusula 2ª do CPS-01025/2026: **uma fonte só está entregue quando os 7
componentes existem e passam na homologação**. Entregar 5 de 7 não é entrega
parcial — é retrabalho na medição.

## Antes de escrever código

1. Leia `docs/contrato/resumo-contrato.md` (onda a que a fonte pertence) e
   `docs/arquitetura/visao-geral.md` (dimensões comuns Silver).
2. Confirme a credencial: se a fonte é de Onda 2/3, ela depende de token ou VPN
   da Alup. **Não invente credencial nem mock silencioso** — se o acesso não
   existe, implemente contra contrato de dados documentado, marque o teste de
   integração com `@pytest.mark.skipif` e registre a pendência.
3. TDD: teste primeiro (`docs/onboarding.md`).

## Os 7 componentes

| # | Onde vive | Critério de pronto |
|---|-----------|--------------------|
| 01 | `src/conectores/<fonte>/` | extração + transporte, sem lógica de negócio |
| 02 | `sql/bronze/<fonte>.sql` | append-only, schema versionado, log de ingestão |
| 03 | `sql/silver/<fonte>.sql` | tipado, deduplicado, com as dimensões comuns |
| 04 | `sql/gold/<fonte>.sql` | regra de negócio / KPI, não repete Silver |
| 05 | `tests/unit/conectores/` + `tests/integration/` | unitário sem rede; e2e marcado |
| 06 | `dags/<fonte>_dag.py` ou Cloud Scheduler via `infra/` | idempotente e reexecutável |
| 07 | `docs/dicionario-dados/<fonte>.md` | campos, tipos, origem→destino, linhagem |

## Estrutura do conector (componente 01)

```
src/conectores/<fonte>/
├── __init__.py
├── client.py      # acesso à fonte: HTTP, driver de banco, leitura de arquivo
├── extract.py     # extrai um período/lote e devolve registros brutos
└── load.py        # grava em GCS raw e/ou insere na tabela Bronze
```

Regras que valem para todo conector:

- Use `src/core/config.py` para projeto, datasets e bucket; use
  `src/core/logging.py::get_logger` — nunca `print`.
- Credencial **só** via Secret Manager (ver skill `ssdlc-alupdata`). Nada de
  token em código, em `.env` versionado ou em default de função.
- Extração **parametrizada por período** (`data_inicio`, `data_fim`) para
  permitir reprocessamento; nunca "sempre hoje".
- Idempotência: reexecutar a mesma janela não pode duplicar em Silver — a
  deduplicação é responsabilidade da view Silver, mas o Bronze precisa carregar
  as colunas que a tornam possível.
- Falha de rede: `requests` com timeout explícito e retry com backoff. Sem
  timeout, um pipeline pendura o Composer.
- Valide o payload com Pydantic antes de gravar; dado que não valida vai para
  log com o motivo, não é descartado em silêncio.

## Bronze (02)

Append-only e fiel à origem. Toda tabela Bronze carrega, além dos campos da
fonte:

| Coluna | Tipo | Para quê |
|---|---|---|
| `_ingestao_timestamp` | TIMESTAMP | quando o registro entrou |
| `_ingestao_id` | STRING | id da execução (rastreia o lote) |
| `_fonte` | STRING | identificador da fonte |
| `_schema_versao` | STRING | versão do schema lido na origem |

Particione por data de ingestão e clusterize pelo campo mais filtrado
(normalmente `data_referencia` ou `codigo_usina`). Sem partição, o custo de
BigQuery cresce por varredura completa.

## Silver (03)

Higieniza: tipa, deduplica (janela por chave natural + `_ingestao_timestamp`
mais recente) e expõe **as dimensões comuns**, que são o que permite cruzar
fontes:

`data_referencia` · `submercado` · `codigo_usina` · `agente_ccee` ·
`periodo_apuracao`

Se a fonte não tem uma dimensão, deixe `NULL` explícito e diga por quê no
dicionário — não invente valor nem omita a coluna.

## Gold (04)

Só regra de negócio e KPI consolidado. Se a view Gold é um `SELECT *` da
Silver, ela não deveria existir. Nomeie pela pergunta que responde
(`gold_preco_medio_submercado`), não pela fonte.

## Testes (05)

- Unitário: parsing, validação e transformação com payload fixo em
  `tests/fixtures/` — **sem rede**.
- Integração: chamada real marcada, pulada quando falta credencial.
- Um teste de idempotência: carregar o mesmo lote duas vezes e verificar que a
  Silver não duplica.

Rode `make all` (lint + testes + Bandit + pip-audit) antes de abrir PR.

## Agendamento (06)

DAG em `dags/` ou Cloud Scheduler via Terraform em `infra/modules/scheduler`.
Frequência acompanha a fonte (CCEE/ONS diário, cadastros ANEEL/IBGE mensal).
Retry configurado; alerta em falha. Toda execução loga `_ingestao_id`.

## Documentação e linhagem (07)

`docs/dicionario-dados/<fonte>.md` com: descrição da fonte, endpoint/objeto de
origem, tabela de campos (origem → Bronze → Silver → Gold, com tipo e regra de
transformação), frequência, dono do dado e observações de qualidade. Sem isso o
componente 07 não existe e a onda não homologa.

## Checklist final

- [ ] 7 componentes presentes
- [ ] `make all` verde
- [ ] Nenhum secret no diff (Gitleaks)
- [ ] Dimensões comuns preenchidas ou justificadas
- [ ] Reprocessamento testado
- [ ] Dicionário de dados atualizado
