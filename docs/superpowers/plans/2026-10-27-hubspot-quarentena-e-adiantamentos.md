# Quarentena do Hubspot e adiantamentos da Onda 3 e 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tirar o Dataform do vermelho pelo Hubspot sem esconder o dado ruim, e adiantar o que não depende da Alupar: leitor do Drive, esquema dos MySQL e esqueleto do conector SOAP da CCEE.

**Architecture:** A Silver `hubspot_negocios` passa a excluir, depois da deduplicação, o negócio que viola as duas `rowConditions`; uma view `hubspot_negocios_quarentena` expõe o que foi excluído, com a regra violada, e a conferência lê dela. As demais tarefas seguem o padrão de conector do contrato (contrato de dados, fixtures, teste de integração `skipif`).

**Tech Stack:** Dataform (SQLX), BigQuery, Python 3.12, pytest, SQLAlchemy (MySQL), zeep ou requests (SOAP).

**Spec:** sem documento de design; a origem é a conversa de 27/10/2026 (autorização do Ricardo para executar as tarefas A a D e apagar o CPTEC) e a ADR 027 e o `docs/status.md`.

## Global Constraints

- Regra 6 do AGENTS.md: sem trailer `Co-Authored-By`, sem "Generated with", sem emoji de robô, branches pelo assunto.
- Credencial só pelo Secret Manager; nada de dado real de cliente no repositório (fixture, exemplo, log).
- Código em inglês; comentários, docs e commits em português; conventional commits; TDD.
- Não alterar dado do cliente no Hubspot nem relaxar a asserção: o que viola a regra vai para a quarentena, e a regra continua valendo na Silver.
- Mesclar PR só com todos os checks verdes.

---

### Task A: Quarentena dos negócios do Hubspot fora da regra

**Files:**
- Create: `definitions/silver/hubspot_negocios_quarentena.sqlx`
- Modify: `definitions/silver/hubspot_negocios.sqlx`, `scripts/conferir_cargas.py` (itens `hubspot_negocios_fora_da_regra` e `hubspot_negocios_reprovados`), `tests/unit/test_conferir_cargas.py`, `docs/dicionario-dados/hubspot_negocios.md`
- Test: `tests/unit/test_conferir_cargas.py` e os testes de definições existentes

**Interfaces:**
- Consumes: `bronze.hubspot_negocios`; `tabela(silver, nome)` de `scripts/conferir_cargas.py`.
- Produces: view `silver.hubspot_negocios_quarentena` com `negocio_id`, `regra` (`valor_negativo` ou `fechamento_antes_da_criacao`), `modificado_em`, `_ingestao_timestamp`.

- [ ] **Step 1:** ajustar o teste da conferência para ler da quarentena (falha primeiro).
- [ ] **Step 2:** rodar `uv run pytest tests/unit/test_conferir_cargas.py -q` e ver falhar.
- [ ] **Step 3:** escrever as duas views (CTE de deduplicação, depois `WHERE` válido na Silver e `WHERE` inválido na quarentena) e apontar a conferência para a quarentena.
- [ ] **Step 4:** rodar `uv run pytest tests/unit -q` e `dataform compile` pelo CI.
- [ ] **Step 5:** commit `fix: negócios do Hubspot fora da regra vão para a quarentena`, PR, deploy em dev e hml, e conferir que o Dataform termina verde.

### Task B: Leitor do Drive para as planilhas da Onda 4

**Files:** ler primeiro `src/conectores/planilha_prc.py`, `src/core/planilha.py` e os testes existentes; criar o leitor em `src/core/drive.py` com teste em `tests/unit/test_drive.py`.

- [ ] **Step 1:** mapear o que já existe (leitura de planilha local, `PrecoReferencia`) e o que falta para ler de uma pasta do Drive.
- [ ] **Step 2:** teste primeiro: listar e baixar arquivos de uma pasta com um cliente falso; credencial só pelo Secret Manager.
- [ ] **Step 3:** implementar o mínimo, com teste de integração `skipif` sem a pasta.
- [ ] **Step 4:** commit `feat: leitor de pasta do Drive para as planilhas da Onda 4`, PR e merge.

### Task C: Esquema dos MySQL (somente leitura de metadados)

**Files:** reaproveitar `teste-conexao-*` e `scripts/operacoes.py`; criar a sonda de esquema em `src/core/sonda.py` com teste em `tests/unit/test_sonda.py`.

- [ ] **Step 1:** ler `src/core/sonda.py` e o job `teste-conexao-<fonte>`.
- [ ] **Step 2:** teste primeiro: a consulta lê só `information_schema.columns` das 7 tabelas pedidas (`uc`, `client`, `invoice`, `medicao_cinco_minutos_api`, `medicao_cinco_minutos_xml`, `faturas_processadas`, `bandeira`) e devolve nomes e tipos de coluna, sem nenhuma linha de dado.
- [ ] **Step 3:** implementar, rodar em dev, registrar as colunas em `docs/` sem valor de dado.
- [ ] **Step 4:** commit, PR e merge.

### Task D: Esqueleto do conector SOAP da CCEE

**Files:** ler `docs/arquitetura/decisoes/018-vias-de-acesso-a-ccee.md`; criar `src/conectores/ccee_soap.py` e `tests/unit/conectores/test_ccee_soap.py`.

- [ ] **Step 1:** ler a ADR 018 e o segredo `alupdata-ccee-credenciais` (JSON `usuario`, `senha`, `senha_certificado`) e `alupdata-ccee-certificado`.
- [ ] **Step 2:** teste primeiro: a sessão SOAP monta autenticação com certificado de cliente, sem ler credencial fora do Secret Manager.
- [ ] **Step 3:** implementar só o cliente e a leitura de credenciais; sem o formato do certificado nem acesso real, parar aí e marcar a integração `skipif`.
- [ ] **Step 4:** commit, PR e merge.

### Task E: Resíduos do CPTEC (passo humano)

Não há ferramenta com escrita no BigQuery nem no Cloud Storage nesta sessão. Passo a passo pelo console para o Ricardo: apagar as tabelas `cptec_previsao` (Bronze), a Silver e a Gold `previsao_tempo_capitais`, e a pasta `cptec/previsao/` do bucket raw, em dev e hml.

## Review Focus

- Negócio violador ausente da Silver e presente na quarentena; versão antiga válida não ressuscita depois de uma versão nova inválida.
- A conferência continua listando o `negocio_id` e nunca valor, nome ou e-mail.
- Credencial do Drive e da CCEE só pelo Secret Manager.
