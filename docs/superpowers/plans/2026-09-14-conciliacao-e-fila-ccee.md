# Conciliação de 14/09 e fila de construção da CCEE — Plano de Implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deixar escrito, numa página só, o que está pronto, o que pode ser construído hoje sem insumo da Alup, e o que está travado e por qual insumo — e entregar, com os 7 componentes cada, as nove entidades da CCEE que a ADR 021 pôs na fila.

**Architecture:** Uma base `CceeCsvCkan` que resolve o recurso pelo catálogo CKAN, lê em *streaming* (arquivos de até 800 MB descomprimidos), decodifica linha a linha (os CSVs da CCEE misturam UTF-8 e ISO-8859-1 no mesmo arquivo) e recorta pela janela usando `MES_REFERENCIA`. Cada entidade nova é uma subclasse de ~40 linhas: dataset, schema Pydantic e `transformar()`. Bronze append-only particionada; Silver com dedup, seis dimensões comuns e asserções de faixa; Gold descritiva por domínio (ADR 012); agendamento no Terraform; dicionário com linhagem. A primeira fonte com recontabilização (`contabilizacao_montante_perfil_agente`) fecha a ADR 016 na opção B, com `versao_publicacao` vinda do `last_modified` do CKAN.

**Tech Stack:** Python 3.13 · uv · pydantic v2 · requests · pytest · Dataform (`.sqlx`) sobre BigQuery · Terraform (Cloud Run Job + Cloud Scheduler + Monitoring) · sqlglot nos testes de SQL.

**Spec:** [`docs/arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md`](../../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md) (a fila e a ordem) · [`docs/arquitetura/dominios-analiticos.md`](../../arquitetura/dominios-analiticos.md) (a pergunta de cada domínio) · [`docs/arquitetura/decisoes/016-versionamento-de-recontabilizacao.md`](../../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) (o que a Silver faz com recontabilização) · [`.claude/skills/conector-alupdata/SKILL.md`](../../../.claude/skills/conector-alupdata/SKILL.md) (os 7 componentes).

## Global Constraints

Copiadas de `AGENTS.md` e das ADRs. Valem para toda tarefa.

- **Toda fonte entrega 7 componentes** (cláusula 2ª): conector Python, tabela Bronze, view Silver, view Gold, testes, agendamento, documentação com linhagem. 5 de 7 é retrabalho na medição.
- **Credencial só via Secret Manager.** Nenhuma tarefa deste plano usa credencial: toda fonte aqui é pública.
- **Ingestão sempre por janela de datas.** O conector nunca decide "hoje".
- **Bronze é append-only**, particionada por `DATE(_ingestao_timestamp)` e clusterizada; **a deduplicação vive na Silver** com `QUALIFY ROW_NUMBER()`.
- **Recurso GCP que não está em `infra/` não existe.** Agendamento entra em `infra/modules/scheduler/main.tf`; alerta de silêncio em `infra/modules/monitoramento/main.tf`.
- **Sem atribuição de IA em nada publicado**: commit, branch, PR, issue, comentário. Branch nomeada pelo assunto (`feat/…`). Valide a mensagem antes de commitar: `uv run python scripts/verifica_atribuicao.py <arquivo-da-mensagem>`. O hook `commit-msg` reprova o que passar.
- **Código em inglês; comentários, docs e commits em português.** Commits sem acento na primeira linha, como o histórico faz (`feat(ccee): …`). Conventional commits: `feat:`, `fix:`, `docs:`, `chore:`.
- **Nomes de objeto e coluna em `snake_case`, sem acento; colunas técnicas com prefixo `_`.**
- **Nada de dado real de cliente no repositório.** Fixture da CCEE usa linhas **sintéticas** com o formato real (a convenção de `tests/fixtures/ccee_perfil_2026.csv`: CNPJ `11111111000111`, nomes inventados). Dado público de mercado não é dado de cliente, mas a fixture continua sintética para não carregar 40 MB.
- **Schema por adivinhação continua proibido.** Todo schema deste plano foi lido do arquivo real em 14/09/2026; onde a leitura foi parcial (só os primeiros 64 KB), a tarefa diz e manda perfilar antes de fechar a chave.
- **TDD**: o teste vem antes do código, e cada tarefa termina com `uv run pytest tests/unit -q` verde e `uv run ruff check src tests` limpo.
- **Gold na Fase 1 é descritiva** (ADR 012, "Gold na Fase 1"): `type: "table"`, sem KPI com fórmula de negócio, na granularidade do A7 (usina para portfólio; usina, estado ou submercado para o SIN). Nomeada pela pergunta, não pela fonte.
- **Seis dimensões comuns em toda Silver**, `CAST(NULL AS STRING)` explícito onde a fonte não responde: `data_referencia`, `submercado`, `codigo_usina`, `agente_ccee`, `periodo_apuracao` (derivado da data), `periodo_apuracao_ccee` (o que a origem declara). O teste `test_silver_deduplica_e_expoe_as_dimensoes_comuns` cobra as seis depois do merge do [#146](https://github.com/nessenergy/Alupdatalake/pull/146).
- **Todo conector registrado precisa de domínio em `src/portal/custo.py::DOMINIO_ANALITICO`** — `test_todo_conector_registrado_tem_dominio_na_visao_de_diretoria` falha sem isso.
- **`User-Agent` de identificação** já é enviado por `src/core/http.py::criar_sessao`; a CCEE devolve 403 sem ele (ADR 018). Não reimplementar.
- **Ambiente**: Windows 11, PowerShell; `uv run` para tudo; `terraform fmt -check -recursive infra/` antes de commitar Terraform. Caminho com acento (`Área de Trabalho`) quebra o `pip-audit` local — o CI cobre.
- **Outra sessão pode estar trabalhando no mesmo worktree.** Antes de commitar, confira `git branch --show-current`. Em 14/09 um commit caiu na branch errada por isso.

---

## Parte 1 — Conciliação: onde o projeto está em 14/09/2026

Fonte: `docs/status.md`, `docs/proximos-passos.md`, `gh pr list`, `gh issue list`, `uv run python -m src.cli listar`, e o catálogo da CCEE lido na data.

### 1.1 Pronto e verificado

| O quê | Evidência | Onde |
|---|---|---|
| Framework de ingestão (janela, raw no GCS, validação, colunas técnicas, carga, log, replay, linhagem) | 535 testes unitários, 101 skipped | `src/core/` |
| 9 conectores registrados, 7 componentes cada | `alupdata listar`: `aneel_siga`, `bbce_curva_forward`, `bcb_cambio_ptax`, `ccee_perfil`, `ccee_pld`, `hubspot_negocios`, `ibge_ipca`, `ons_carga`, `tempook_boletins` | `src/conectores/`, `definitions/`, `docs/dicionario-dados/` |
| 7 dos 9 falaram com a API real em dry-run | `status.md` §1, tabela de conectores | Hubspot e BBCE esperam credencial (A9, A7) |
| Dimensões comuns: as cinco originais com fonte; a sexta (`periodo_apuracao_ccee`) no #146 | `visao-geral.md`, Lacuna 2 encerrada | `definitions/silver/*.sqlx` |
| 8 domínios analíticos, os do B1, com dono nomeado | `dominios-analiticos.md` | domínio Econômico completo com o #143 |
| ADRs 001–021 | `docs/arquitetura/decisoes/` | ADR 016 segue **proposta** — este plano a torna aceita (Task 4) |
| Terraform: datasets, bucket, secrets, Cloud Run Job + Scheduler, IAM, alertas | `terraform fmt` e `validate` limpos; nunca aplicado | depende de A3 |
| CI: 8 jobs verdes em todo PR | `.github/workflows/` | inclui `Commits sem atribuição a IA` e `Dataform Compile` |
| Portal MVP com três telas, provedor simulado | 46 testes | `src/portal/` |

### 1.2 Aberto em revisão — depende só de merge (Ricardo)

Seis PRs, todos `CLEAN`, 8/8 verificações. A `main` é protegida: o merge é humano.

| PR | Assunto | Dependência entre eles |
|---|---|---|
| [#143](https://github.com/nessenergy/Alupdatalake/pull/143) | Selic e CDI (`bcb_juros`) | ver #146 |
| [#144](https://github.com/nessenergy/Alupdatalake/pull/144) | A7 em detalhe no painel | independente |
| [#145](https://github.com/nessenergy/Alupdatalake/pull/145) | ADR 021 — fila da CCEE | **é a spec deste plano**; mesclar antes de começar a Task 2 |
| [#146](https://github.com/nessenergy/Alupdatalake/pull/146) | `periodo_apuracao_ccee`, sexta dimensão | **mesclar antes da Task 1**: as Silver deste plano já nascem com seis dimensões |
| [#147](https://github.com/nessenergy/Alupdatalake/pull/147) | camada gratuita no modelo de custo | independente |
| [#148](https://github.com/nessenergy/Alupdatalake/pull/148) | fila de 14/09 em `proximos-passos.md` | independente |

O que entrar por último entre #143 e #146 precisa de `periodo_apuracao_ccee` em `definitions/silver/bcb_juros.sqlx` — **Task 7.4** deste plano faz isso.

### 1.3 Em condições de seguir para construção — sem insumo da Alup

Tudo público, catálogo lido em 14/09, arquivos baixados e perfilados. É o que este plano constrói.

| Ordem (ADR 021) | Entidade nova | Dataset CKAN | Domínio | Grão verificado | Volume verificado (arquivo mais recente) | Formato |
|---|---|---|---|---|---|---|
| 1 | `ccee_agente` | `lista_agente_associado` | Mercado de Energia (dimensão) | (`MES_REFERENCIA`, `CNPJ`) — 0 duplicatas | 147.801 linhas, 16 MB, 9 meses de 2026 (~16.400 agentes/mês) | CSV `;` anual, **UTF-8 e ISO-8859-1 misturados por linha** |
| 2 | `ccee_exposicao_financeira` | `exposicao_financeira_mensal` | Risco e Compliance | (`MES_REFERENCIA`) | 7 linhas, 968 bytes | CSV `;` anual |
| 2 | `ccee_contabilizacao_perfil` | `contabilizacao_montante_perfil_agente` | Risco e Compliance | (`MES_REFERENCIA`, `COD_PERF_AGENTE`) — 0 duplicatas | 329.080 linhas, 43 MB, 7 meses | CSV `;` anual; 7 colunas com vazio |
| 3 | `ccee_geracao_usina` | `geracao_horaria_usina` | Geração e Operacional | (`DATA`, `PERIODO_COMERCIALIZACAO`, `CODIGO_PARCELA_USINA`) — 0 duplicatas | 2.964.096 linhas/mês, 61 MB **gzip** → ~800 MB texto; 3.984 usinas; 36 colunas, 25 delas quase sempre vazias | **GZIP mensal** (`_202607`), `;` |
| 4 | `ccee_contrato_montante` | `contrato_montante_compra_venda_perfil_agente` | Comercial e Contratos | (`MES_REFERENCIA`, `CODIGO_PERFIL_AGENTE`) — 0 duplicatas | 183.893 linhas, 18,5 MB, 7 meses | CSV `;` anual; `CONTRATACAO_VENDA` vazia em 80% |
| 4 | `ccee_varejista_consumidor` | `varejista_consumidor` | Comercial e Contratos (varejo) | (`MES_REFERENCIA`, `COD_PERF_AGENTE`, `ESTADO_UF_CARGA`, `SUBMERCADO_CARGA`, `COD_PERF_AGENTE_CONECTADO`) — 0 duplicatas; **(mês, perfil) sozinho duplica 2.465×** | 23.478 linhas, 2,6 MB | CSV `;` anual |
| 5 | `ccee_cvu_estrutural` | `custo_variavel_unitario_estrutural` | Mercado de Energia | candidata (`MES_REFERENCIA`, `ANO_HORIZONTE`, `CODIGO_PARCELA_USINA`, `LEILAO`, `PRODUTO`) — **só 64 KB lidos; perfilar na Task 8** | desconhecido | CSV **vírgula** anual; datas `dd/mm/aaaa` |
| 5 | `ccee_encargo_ess` | `encargo_ess_ancilar` | Mercado de Energia | (`MES_REFERENCIA`) | uma linha por mês, 16 colunas | CSV `;` anual |
| 5 | `ccee_energia_reserva` | `energia_reserva_liquidacao` | Mercado de Energia | (`MES_REFERENCIA`) | uma linha por mês, 5 colunas | CSV `;` anual |

**Três correções à ADR 021 que a leitura dos arquivos impôs** (Task 7.1):
1. `lista_agente_associado` **não é** "agente ↔ perfil". Não há coluna de perfil. É a lista mensal de agentes com classe, situação de comercializador e de varejista, UF e categoria — um retrato por mês, com histórico. O elo agente↔perfil já está em `lista_perfil_v1` (`COD_AGENTE` + `COD_PERF_AGENTE`).
2. `geracao_horaria_usina` é publicado **por mês e em gzip**, não por ano em CSV. A base precisa saber os dois formatos.
3. `custo_variavel_unitario_estrutural` usa **vírgula** como delimitador. Todos os outros usam `;`.

Também em condições, fora da CCEE (não neste plano, para não misturar subsistemas): `EAR` e `ENA` do ONS (Mercado de Energia) e geração/térmicas do ONS (Geração e Operacional). Precisam da mesma leitura de arquivo real antes de virar plano.

### 1.4 Bloqueado — e por qual insumo

Cada linha diz o insumo, o dono, a issue, e **o que fazer no dia em que chegar**, para que ninguém precise reler o projeto.

| # | Insumo que falta | Dono | Issue / referência | Trava o quê | O que fazer quando chegar |
|---|---|---|---|---|---|
| A3 | Projeto GCP `dev` criado, vinculado ao faturamento, com papéis de bootstrap à ness. (ADR 015) | Alup (TI); prazo dado pela Alup: 18/09 | `status.md` §3 A1 e A3, [#55](https://github.com/nessenergy/Alupdatalake/issues/55) | N2 portal contra BigQuery, N3 primeiro `terraform apply`, N4 replay contra GCS, N5 imagem no Cloud Run; **homologação da Onda 0** | seguir `docs/runbook/primeiro-deploy.md` §0 em diante e a sequência da §5 de `proximos-passos.md`; conferir que os rótulos FinOps F0 entram no primeiro apply |
| A7 | Chamados de token (Onda 2) e VPN/credencial read-only (Onda 3) abertos, com número | Alup (Leonardo Marques; substituto Mauricio Cardoso) | `status.md` §6 "A7 em detalhe" (#144) | 7 conectores: BBCE [#23](https://github.com/nessenergy/Alupdatalake/issues/23), TempoOK [#25](https://github.com/nessenergy/Alupdatalake/issues/25), Oracle FMB [#27](https://github.com/nessenergy/Alupdatalake/issues/27), Portal Alup [#29](https://github.com/nessenergy/Alupdatalake/issues/29), MySQL RDS [#31](https://github.com/nessenergy/Alupdatalake/issues/31), RM/TOTVS [#32](https://github.com/nessenergy/Alupdatalake/issues/32) | BBCE: gravar credencial e **host** no Secret Manager e rodar `ALUPDATA_INTEGRACAO_BBCE=1 uv run pytest tests/integration -q`; Onda 3: `docs/runbook/credenciais.md` e ADR 008 |
| A9 | Token da private app do Hubspot no secret `alupdata-hubspot-api-token` | Alup | [#24](https://github.com/nessenergy/Alupdatalake/issues/24) | `hubspot_negocios` está escrito e parado | `ALUPDATA_INTEGRACAO_HUBSPOT=1 uv run pytest tests/integration -q`; primeiro dry-run com `--ultimos-dias 2` |
| A10 | Acesso do TempoOK ao acervo posterior a 26/10/2022 | Alup junto ao fornecedor | [#129](https://github.com/nessenergy/Alupdatalake/issues/129), ADR 019/020 | `tempook_boletins` ingere zero boletins | rodar `uv run python -m src.cli ingerir tempook_boletins --ultimos-dias 5 --dry-run`; se vier boletim, o conector já está pronto |
| #87 | `billing_account` e destinatários de alerta (`alup.alertas@alupar.com.br` já informado; falta a conta) | Alup | [#87](https://github.com/nessenergy/Alupdatalake/issues/87) | orçamento e alertas configurados sem quem receba | preencher `emails_alerta` e a conta no `tfvars` do ambiente; nada de código |
| #141 | De-para de usina: sigla interna ↔ CEG ↔ nome CCEE ↔ nome ONS | Alup (Taina Mota / Letícia Ferreira) | [#141](https://github.com/nessenergy/Alupdatalake/issues/141), Lacuna 1 | cruzar Geração e Operacional com Comercial e Contratos e Risco e Compliance; `codigo_usina` só vem do `aneel_siga` | criar `bronze.alup_usinas_depara` pelo S2 Data Intake (`src/conectores/planilha.py`) e preencher `codigo_usina` nas Silver de `ccee_geracao_usina` e `ccee_cvu_estrutural` por junção |
| #142 | Exemplos reais das planilhas (G3) | Alup, cada área; prazo 18/09 | [#142](https://github.com/nessenergy/Alupdatalake/issues/142) | conferir o escopo de dado contra os 13 conectores; templates do S2 Data Intake (item 4.1) | bater item a item; o que ficar fora dos 13 é aditivo, e a distinção precisa estar escrita antes da medição |
| C7 | Forma de integração do RM/TOTVS (API, view ou exportação) e ambiente de homologação | Alup (TI); prazo 25/09 | [#32](https://github.com/nessenergy/Alupdatalake/issues/32) | dicionário e conector do RM/TOTVS | escolher o caminho conforme ADR 008 (banco) ou conector HTTP |
| C5 | Versão do Oracle FMB e existência de réplica de leitura | Alup (TI) | [#27](https://github.com/nessenergy/Alupdatalake/issues/27) | driver e janela de leitura (C9: 22h–6h) | ajustar `src/core/banco.py` se a versão exigir; nada antes |
| — | Regra do **prêmio sobre o PLD** (BBCE) | Alup (Gabriel Barreto, Trading) | `bbce_curva_forward.md` | Gold de prêmio no subtema de Trading | escrever a Gold com a fórmula dada, não antes |
| — | Confirmação de que o **mês CCEE** difere do civil, e como | Alup (dono do domínio) | `visao-geral.md`, Lacuna 2 | nada hoje; a asserção da Silver do PLD avisa se divergir | se a asserção falhar, aprender a regra do dado e escrever ADR |
| — | Merge dos seis PRs da §1.2 | Ricardo | — | este plano (Task 1 depende de #146; Task 2 de #145) | mesclar |
| 3.2 | Idioma do baralho de revisão arquitetural | Ricardo | `proximos-passos.md` §3 | item 4.3 | só se a plateia do Google não for do Brasil |
| 4.4 | Permissão para apagar branches mescladas e arquivar `backup/*` | Ricardo / GitHub Enterprise | `proximos-passos.md` §4 | higiene; nada funcional | testar `git push origin --delete docs/dominios-do-b1` (PR #139 fechado, conteúdo na main pelo #138) |

**Contratual, fora deste plano:** questão financeira de multa (cláusula 3ª — postergação, ociosidade, suspensão) não é gerida pelo agente. Registrar data e fato, sim; decidir efeito, não.

---
## Parte 2 — Plano de construção

### Estrutura de arquivos

Um arquivo novo compartilhado, e para cada entidade os seis arquivos que `make novo-conector` também geraria (mais a entrada no Terraform):

```
src/conectores/ccee_ckan.py                         # NOVO — base: CKAN, streaming, gzip, decode por linha, janela por mês
tests/unit/conectores/test_ccee_ckan.py             # NOVO — a base, sem rede
src/conectores/ccee_<entidade>.py                   # um por entidade (Tasks 2–8)
definitions/bronze/ccee_<entidade>.sqlx
definitions/silver/ccee_<entidade>.sqlx
definitions/silver/ccee_contabilizacao_perfil_historico.sqlx   # só a Task 4 (ADR 016, opção B)
definitions/gold/<pergunta>.sqlx
tests/unit/conectores/test_ccee_<entidade>.py
tests/fixtures/ccee_<entidade>_2026.csv             # sintética, formato real
docs/dicionario-dados/ccee_<entidade>.md
infra/modules/scheduler/main.tf                     # entrada por entidade
infra/modules/monitoramento/main.tf                 # limiar por entidade
src/portal/custo.py                                 # DOMINIO_ANALITICO por entidade
docs/dicionario-dados/README.md · docs/status.md · docs/arquitetura/decisoes/021-…md · 016-…md
```

`ccee_pld.py` **não muda**. Ele tem 17 testes com seams próprios (`_baixar_ano`, `_pacote`) e um recorte por dia que nenhuma entidade nova usa. Migrá-lo para a base é tarefa opcional depois deste plano — deixar duas descobertas CKAN no repositório por algumas semanas custa menos do que reabrir um conector verificado.

**Decisões de modelagem que valem para todas as entidades mensais** (Tasks 2–4, 6–8):

- `data_referencia` = **primeiro dia do `MES_REFERENCIA`**. A origem publica por mês; o dia 1 é a convenção, e o dicionário diz isso.
- `periodo_apuracao_ccee` = `AAAA-MM` do `MES_REFERENCIA` (o que a origem declara). `periodo_apuracao` = `FORMAT_DATE('%Y-%m', data_referencia)` na Silver. Os dois coincidem por construção; a asserção `periodo_apuracao = periodo_apuracao_ccee` fica em toda Silver da CCEE, pelo mesmo motivo do PLD (#146).
- `versao_publicacao` = data `last_modified` do recurso no CKAN, capturada em `extrair()`. É o identificador de versão da ADR 016 (item 2 da ordem de preferência: *data de publicação do arquivo, informada pela fonte*). Toda entidade mensal a carrega; só a Task 4 cria a view `_historico`, porque só ela tem recontabilização declarada (`AJUSTE_RECONTAB`).
- Valor numérico vazio na origem vira **`None` → `NULL`**, nunca zero. Zero é valor; vazio é ausência, e a CCEE usa os dois.
- Recorte da janela por **mês**: uma linha entra se `(ano, mês)` do `MES_REFERENCIA` está entre `(janela.inicio.year, janela.inicio.month)` e `(janela.fim.year, janela.fim.month)`, inclusive. Uma janela de 120 dias cobre a recontabilização (ADR 016) — o mesmo `ultimos_dias` do `ccee_pld`.

---

### Task 1: A base `CceeCsvCkan`

**Files:**
- Create: `src/conectores/ccee_ckan.py`
- Test: `tests/unit/conectores/test_ccee_ckan.py`

**Interfaces:**
- Consumes: `src.core.conector.Conector`, `src.core.http.criar_sessao`, `src.core.config.get_settings`, `src.core.execucao.Janela` (`.inicio: date`, `.fim: date`).
- Produces (o que as Tasks 2–8 usam):
  - `class CceeCsvCkan(Conector)` com atributos de classe `dataset: str`, `delimitador: str = ";"`, `recurso_por: Literal["ano", "mes"] = "ano"`, `fonte = "ccee"`, `max_dias_por_requisicao = None`.
  - `def _abrir(self, sufixo: str) -> IO[bytes]` — **o seam de teste**: devolve um fluxo binário do recurso; os testes o substituem por `io.BytesIO(...)`.
  - `def publicado_em(self, sufixo: str) -> date` — `last_modified` do recurso; hoje, com aviso, se ausente.
  - `def extrair(self, janela)` — itera os sufixos da janela, abre cada recurso, decodifica linha a linha, filtra por `MES_REFERENCIA` e injeta `_versao_publicacao` (ISO) e `_sufixo` no bruto.
  - Helpers de módulo: `decodificar(linha: bytes) -> str`, `primeiro_dia(mes_referencia: str) -> date`, `periodo_ccee(mes_referencia: str) -> str`, `numero_ou_nulo(valor: str | None) -> str | None`, `limpar(valor: str | None) -> str`.

- [ ] **Step 1: Escrever os testes da base (falham: módulo não existe)**

```python
# tests/unit/conectores/test_ccee_ckan.py
"""Base dos conectores CSV da CCEE via CKAN — descoberta, streaming e decodificação, sem rede.

O que estes testes protegem, e que a leitura dos arquivos reais em 14/09 mostrou:

- os CSVs da CCEE misturam UTF-8 e ISO-8859-1 **no mesmo arquivo**: em
  `lista_agente_associado_2026`, 49.269 linhas decodificam como UTF-8 e 98.532
  só como ISO-8859-1. Decodificar o arquivo inteiro num encoding só mutila
  metade dele em silêncio;
- `geracao_horaria_usina` vem gzip e por mês (`_202607`); os outros, CSV por ano;
- a janela recorta pelo `MES_REFERENCIA`, não por dia;
- `versao_publicacao` vem do `last_modified` do CKAN (ADR 016, opção B).
"""

from __future__ import annotations

import gzip
import io
from datetime import date

import pytest
from src.conectores.ccee_ckan import (
    CceeCsvCkan,
    decodificar,
    numero_ou_nulo,
    periodo_ccee,
    primeiro_dia,
)
from src.core.execucao import Janela

CSV = (
    "MES_REFERENCIA;SIGLA;VALOR\n"
    "202601;ALFA;1.5\n"
    "202602;BETA;\n"
    "202603;GAMA;3\n"
)


class Dummy(CceeCsvCkan):
    """Subclasse mínima: só o que a base exige."""

    dataset = "dummy_mensal"
    entidade = "dummy"
    schema = None  # não passa pelo runner nestes testes

    def transformar(self, bruto):  # pragma: no cover — não usado aqui
        return bruto


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Dummy()
    pacote = {
        "resources": [
            {"name": "dummy_mensal_2025", "url": "https://exemplo/2025", "format": "CSV", "last_modified": "2026-02-02T17:36:17"},
            {"name": "dummy_mensal_2026", "url": "https://exemplo/2026", "format": "CSV", "last_modified": "2026-09-01T14:50:45"},
        ]
    }
    monkeypatch.setattr(conector, "_pacote", lambda: pacote)
    monkeypatch.setattr(conector, "_abrir", lambda _sufixo: io.BytesIO(CSV.encode("iso-8859-1")))
    return conector


# ------------------------------------------------------------ decodificação


def test_linha_utf8_e_linha_latin1_no_mesmo_arquivo_decodificam_as_duas():
    assert decodificar("Comercialização".encode("utf-8")) == "Comercialização"
    assert decodificar("Comercialização".encode("iso-8859-1")) == "Comercialização"


def test_linha_ascii_passa_intacta():
    assert decodificar(b"202601;ALFA;1.5") == "202601;ALFA;1.5"


# ------------------------------------------------------------- utilitários


def test_primeiro_dia_do_mes_de_referencia():
    assert primeiro_dia("202607") == date(2026, 7, 1)


def test_mes_de_referencia_vira_periodo_ccee():
    assert periodo_ccee("202607") == "2026-07"


def test_mes_de_referencia_invalido_e_recusado():
    with pytest.raises(ValueError):
        primeiro_dia("2026-07")


def test_vazio_vira_nulo_e_zero_continua_zero():
    assert numero_ou_nulo("") is None
    assert numero_ou_nulo(None) is None
    assert numero_ou_nulo("0") == "0"
    assert numero_ou_nulo(" 1.5 ") == "1.5"


# ------------------------------------------------------------ janela e recorte


def test_extrai_so_os_meses_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-02-01", "2026-02-28")))

    assert [r["SIGLA"] for r in registros] == ["BETA"]


def test_janela_no_meio_do_mes_ainda_alcanca_o_mes_inteiro(conector):
    """A CCEE publica por mês; uma janela de 15/01 a 20/02 pede janeiro e fevereiro inteiros."""
    registros = list(conector.extrair(Janela.de_texto("2026-01-15", "2026-02-20")))

    assert [r["SIGLA"] for r in registros] == ["ALFA", "BETA"]


def test_cada_bruto_carrega_a_versao_de_publicacao_e_o_sufixo(conector):
    registro = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))

    assert registro["_versao_publicacao"] == "2026-09-01"
    assert registro["_sufixo"] == "2026"


def test_janela_que_cruza_o_ano_abre_cada_ano(conector, monkeypatch):
    abertos = []
    monkeypatch.setattr(conector, "_abrir", lambda s: abertos.append(s) or io.BytesIO(b"MES_REFERENCIA;SIGLA;VALOR\n"))

    list(conector.extrair(Janela.de_texto("2025-12-01", "2026-01-31")))

    assert abertos == ["2025", "2026"]


def test_recurso_mensal_usa_sufixo_aaaamm(monkeypatch):
    class Mensal(Dummy):
        recurso_por = "mes"

    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Mensal()
    abertos = []
    monkeypatch.setattr(conector, "_abrir", lambda s: abertos.append(s) or io.BytesIO(b"MES_REFERENCIA;SIGLA;VALOR\n"))

    list(conector.extrair(Janela.de_texto("2026-06-10", "2026-08-01")))

    assert abertos == ["202606", "202607", "202608"]


def test_recurso_ausente_vira_aviso_e_nao_derruba(conector, monkeypatch, caplog):
    def abrir(sufixo):
        if sufixo == "2025":
            raise FileNotFoundError("dummy_mensal_2025 não publicado")
        return io.BytesIO(CSV.encode("iso-8859-1"))

    monkeypatch.setattr(conector, "_abrir", abrir)

    registros = list(conector.extrair(Janela.de_texto("2025-12-01", "2026-01-31")))

    assert [r["SIGLA"] for r in registros] == ["ALFA"]
    assert "2025" in caplog.text


# ------------------------------------------------------------------- gzip


def test_recurso_gzip_e_descomprimido_em_fluxo(conector, monkeypatch):
    comprimido = gzip.compress(CSV.encode("iso-8859-1"))
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(comprimido))

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-03-31")))

    assert len(registros) == 3


# --------------------------------------------------------------- descoberta


def test_url_do_recurso_vem_do_ckan_pelo_sufixo(conector):
    assert conector._recurso("2026")["url"] == "https://exemplo/2026"


def test_sufixo_sem_recurso_levanta_erro_nomeado(conector):
    with pytest.raises(FileNotFoundError, match="2027"):
        conector._recurso("2027")


def test_publicado_em_le_o_last_modified(conector):
    assert conector.publicado_em("2026") == date(2026, 9, 1)


def test_publicado_em_sem_last_modified_assume_hoje_e_avisa(conector, monkeypatch, caplog):
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "dummy_mensal_2026", "url": "u"}]})

    assert conector.publicado_em("2026") == date.today()
    assert "last_modified" in caplog.text


def test_delimitador_virgula_e_respeitado(monkeypatch):
    class Virgula(Dummy):
        delimitador = ","

    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Virgula()
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "dummy_mensal_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]})
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(b"MES_REFERENCIA,SIGLA,VALOR\n202601,ALFA,1.5\n"))

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31")))

    assert registros[0]["SIGLA"] == "ALFA"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/unit/conectores/test_ccee_ckan.py -q`
Expected: `ModuleNotFoundError: No module named 'src.conectores.ccee_ckan'`

- [ ] **Step 3: Escrever a base**

```python
# src/conectores/ccee_ckan.py
"""Base dos conectores de CSV da CCEE publicados no CKAN (dados abertos).

A ADR 018 destravou a via pública; a ADR 021 escolheu 24 conjuntos e a ordem.
Cada conjunto vira uma subclasse desta base com três coisas: o nome do dataset,
o schema Pydantic e o `transformar()`. O resto — descobrir o recurso no CKAN,
baixar em fluxo, descomprimir, decodificar e recortar pela janela — é o mesmo
para todos, e foi lido dos arquivos reais em 14/09/2026.

## O que a leitura dos arquivos impôs

1. **Encoding misto no mesmo arquivo.** `lista_agente_associado_2026` tem
   49.269 linhas em UTF-8 e 98.532 em ISO-8859-1. Um `resposta.encoding` só
   mutila metade em silêncio; por isso a decodificação é **por linha**.
2. **Gzip mensal.** `geracao_horaria_usina` vem em recursos `_AAAAMM` de 61 MB
   comprimidos (~800 MB de texto). O arquivo não cabe em `resposta.text`; a
   leitura é em fluxo, e o gzip é detectado pelos dois primeiros bytes.
3. **Delimitador não é sempre `;`.** `custo_variavel_unitario_estrutural` usa
   vírgula.
4. **A janela recorta por mês.** A CCEE publica por `MES_REFERENCIA`; uma
   janela de 120 dias cobre a recontabilização (ADR 016) sem baixar o histórico
   inteiro a cada execução.

`ccee_pld` continua com a própria descoberta: tem 17 testes e um recorte por
dia que nenhuma entidade mensal usa. Migrá-lo é tarefa à parte.
"""

from __future__ import annotations

import csv
import gzip
import io
import logging
from datetime import date, datetime
from typing import IO, TYPE_CHECKING, Any, ClassVar, Literal

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

CKAN_PACOTE = "https://dadosabertos.ccee.org.br/api/3/action/package_show"
_GZIP_MAGIC = b"\x1f\x8b"


def decodificar(linha: bytes) -> str:
    """UTF-8 quando a linha é UTF-8 válido; ISO-8859-1 no resto.

    Uma sequência ISO-8859-1 raramente é UTF-8 válido por acaso (precisaria de
    dois acentos consecutivos com bytes específicos); o custo desse caso raro é
    um caractere trocado numa razão social, não uma linha perdida.
    """
    try:
        return linha.decode("utf-8")
    except UnicodeDecodeError:
        return linha.decode("iso-8859-1")


def limpar(valor: str | None) -> str:
    """Texto da CCEE sem espaço em volta, inclusive o não separável (`\\xa0`)."""
    return (valor or "").replace("\xa0", " ").strip()


def numero_ou_nulo(valor: str | None) -> str | None:
    """Vazio na origem é ausência, não zero. Zero continua zero."""
    texto = limpar(valor)
    return texto if texto else None


def primeiro_dia(mes_referencia: str) -> date:
    """`AAAAMM` → primeiro dia do mês. É a `data_referencia` das entidades mensais."""
    mes = limpar(mes_referencia)
    if len(mes) != 6 or not mes.isdigit():
        raise ValueError(f"MES_REFERENCIA inválido: {mes_referencia!r}")
    return date(int(mes[:4]), int(mes[4:6]), 1)


def periodo_ccee(mes_referencia: str) -> str:
    """`AAAAMM` → `AAAA-MM`, o `periodo_apuracao_ccee` (o que a origem declara)."""
    dia = primeiro_dia(mes_referencia)
    return f"{dia.year:04d}-{dia.month:02d}"


def _meses(inicio: date, fim: date) -> list[str]:
    """`AAAAMM` de cada mês entre inicio e fim, inclusive."""
    meses = []
    ano, mes = inicio.year, inicio.month
    while (ano, mes) <= (fim.year, fim.month):
        meses.append(f"{ano:04d}{mes:02d}")
        ano, mes = (ano + 1, 1) if mes == 12 else (ano, mes + 1)
    return meses


class CceeCsvCkan(Conector):
    """Um conjunto do CKAN da CCEE, CSV por ano ou gzip por mês.

    A subclasse define `dataset`, `entidade`, `schema`, opcionalmente
    `delimitador` e `recurso_por`, e implementa `transformar()`. O bruto que
    chega em `transformar()` traz as colunas do CSV e mais duas chaves
    técnicas: `_versao_publicacao` (ISO, do CKAN) e `_sufixo` (o recurso).
    """

    dataset: ClassVar[str]
    delimitador: ClassVar[str] = ";"
    recurso_por: ClassVar[Literal["ano", "mes"]] = "ano"

    fonte = "ccee"
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por recurso, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()
        self._cache_pacote: dict[str, Any] | None = None

    # ------------------------------------------------------------- descoberta

    def _pacote(self) -> dict[str, Any]:
        """Metadados do dataset no CKAN. Uma chamada por execução."""
        if self._cache_pacote is None:
            cfg = get_settings()
            resposta = self._sessao.get(CKAN_PACOTE, params={"id": self.dataset}, timeout=cfg.http_timeout)
            resposta.raise_for_status()
            self._cache_pacote = resposta.json()["result"]
        return self._cache_pacote

    def _recurso(self, sufixo: str) -> dict[str, Any]:
        """O recurso cujo nome termina em `_<sufixo>`, como o CKAN o publica hoje."""
        alvo = f"_{sufixo}"
        for recurso in self._pacote().get("resources", []):
            if str(recurso.get("name", "")).endswith(alvo):
                return recurso
        raise FileNotFoundError(f"a CCEE não publica o recurso {self.dataset}_{sufixo}")

    def publicado_em(self, sufixo: str) -> date:
        """`last_modified` do recurso: o identificador de versão da ADR 016 (opção B)."""
        publicado = str(self._recurso(sufixo).get("last_modified") or "")[:10]
        try:
            return date.fromisoformat(publicado)
        except ValueError:
            hoje = datetime.now().date()
            logger.warning("CCEE %s: recurso %s sem last_modified; versao_publicacao assumida como %s", self.dataset, sufixo, hoje)
            return hoje

    # ---------------------------------------------------------------- leitura

    def _abrir(self, sufixo: str) -> IO[bytes]:
        """Fluxo binário do recurso. É o seam dos testes: eles devolvem um BytesIO."""
        resposta = self._sessao.get(self._recurso(sufixo)["url"], stream=True, timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return io.BufferedReader(resposta.raw)  # type: ignore[arg-type]

    def _linhas(self, sufixo: str) -> Iterator[dict[str, str]]:
        fluxo = self._abrir(sufixo)
        if not hasattr(fluxo, "peek"):
            fluxo = io.BufferedReader(fluxo)  # o BytesIO dos testes não tem peek
        if fluxo.peek(2)[:2] == _GZIP_MAGIC:
            fluxo = gzip.GzipFile(fileobj=fluxo)  # type: ignore[assignment]
        texto = (decodificar(linha).rstrip("\r\n") for linha in fluxo)
        yield from csv.DictReader(texto, delimiter=self.delimitador)

    def _sufixos(self, janela: Janela) -> list[str]:
        if self.recurso_por == "mes":
            return _meses(janela.inicio, janela.fim)
        return [str(ano) for ano in range(janela.inicio.year, janela.fim.year + 1)]

    @staticmethod
    def _dentro(mes_referencia: str, janela: Janela) -> bool:
        mes = limpar(mes_referencia)
        if len(mes) != 6 or not mes.isdigit():
            return False  # linha em branco ou rodapé; a validação conta o resto
        chave = (int(mes[:4]), int(mes[4:6]))
        return (janela.inicio.year, janela.inicio.month) <= chave <= (janela.fim.year, janela.fim.month)

    # ---------------------------------------------------------------- extração

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for sufixo in self._sufixos(janela):
            try:
                versao = self.publicado_em(sufixo).isoformat()
                linhas = self._linhas(sufixo)
            except FileNotFoundError:
                # O período corrente só aparece depois do fechamento. Janela que
                # o alcança não pode falhar por isso.
                logger.warning("CCEE %s: recurso %s ainda não publicado, ignorado", self.dataset, sufixo)
                continue

            logger.info("CCEE %s: lendo %s (publicado em %s)", self.dataset, sufixo, versao)
            for linha in linhas:
                if self._dentro(linha.get("MES_REFERENCIA", ""), janela):
                    # As duas chaves técnicas viajam no bruto para chegar ao raw:
                    # sem elas o arquivo no GCS não diria de qual publicação é.
                    yield linha | {"_versao_publicacao": versao, "_sufixo": sufixo}
```

Três detalhes de implementação que não são óbvios:

- `io.BytesIO` não tem `peek`; `io.BufferedReader` tem. A primeira linha de
  `_linhas` embrulha o que não tiver — é o que deixa os testes usarem `BytesIO`
  e a produção usar `resposta.raw`.
- Iterar um `BufferedReader` ou um `GzipFile` devolve **linhas em bytes**; o
  `csv.DictReader` aceita qualquer iterável de `str`, então o gerador
  `decodificar(...)` é o único ponto de decodificação.
- `stream=True` + `resposta.raw` evita carregar 800 MB em memória. O
  `Content-Type` do gzip da CCEE é `application/x-gzip` **sem**
  `Content-Encoding`, por isso o `requests` não descomprime sozinho e a base
  detecta pelos bytes.

- [ ] **Step 4: Rodar até ficar verde**

Run: `uv run pytest tests/unit/conectores/test_ccee_ckan.py -q`
Expected: `18 passed`

Se `test_recurso_ausente_vira_aviso_e_nao_derruba` falhar por não achar "2025" no log: o `publicado_em` é chamado **antes** de `_abrir` e levanta `FileNotFoundError` pelo `_recurso` — o teste monkeypatcha só `_abrir`, então o `_pacote` do fixture precisa ter o recurso 2025. Ele tem. Se ainda falhar, o `caplog` está no nível WARNING? Use `caplog.set_level(logging.WARNING)` no teste.

- [ ] **Step 5: Lint e suíte inteira**

Run: `uv run ruff check src tests && uv run ruff format --check src tests && uv run pytest tests/unit -q`
Expected: tudo limpo; contagem anterior + 18.

- [ ] **Step 6: Commit**

```bash
git checkout -b feat/ccee-base-ckan main
git add src/conectores/ccee_ckan.py tests/unit/conectores/test_ccee_ckan.py
```

Mensagem (num arquivo, validada por `uv run python scripts/verifica_atribuicao.py <arquivo>`):

```
feat(ccee): base dos conectores CSV do CKAN, lida dos arquivos reais

Tres coisas que a leitura dos 204 conjuntos em 14/09 impos, e que nenhuma
adivinhacao teria previsto: os CSVs misturam UTF-8 e ISO-8859-1 no mesmo
arquivo (49 mil linhas de um, 98 mil do outro em lista_agente_associado),
geracao_horaria_usina vem em gzip mensal de 61 MB, e o CVU estrutural usa
virgula onde todos os outros usam ponto-e-virgula.

A base decodifica por linha, le em fluxo, detecta gzip pelos dois primeiros
bytes e recorta a janela por MES_REFERENCIA. Cada entidade nova vira uma
subclasse com dataset, schema e transformar(). O last_modified do CKAN entra
no bruto como versao_publicacao -- e o identificador da ADR 016.

ccee_pld nao muda: tem 17 testes e recorte por dia que ninguem mais usa.
```

```bash
git commit -F <arquivo>
```

---
### Task 2: `ccee_agente` — a lista mensal de agentes (ordem 1 da ADR 021)

**Files:**
- Create: `src/conectores/ccee_agente.py`
- Create: `definitions/bronze/ccee_agente.sqlx`
- Create: `definitions/silver/ccee_agente.sqlx`
- Create: `definitions/gold/agentes_por_classe_mensal.sqlx`
- Test: `tests/unit/conectores/test_ccee_agente.py`
- Create: `docs/dicionario-dados/ccee_agente.md`
- Modify: `infra/modules/scheduler/main.tf` (bloco `default` de `var.conectores`)
- Modify: `infra/modules/monitoramento/main.tf` (`conectores_criticos`)
- Modify: `src/portal/custo.py` (`DOMINIO_ANALITICO`)
- Modify: `docs/dicionario-dados/README.md` (tabela "O que existe")

**Interfaces:**
- Consumes: `CceeCsvCkan`, `decodificar`, `limpar`, `primeiro_dia`, `periodo_ccee` da Task 1.
- Produces: conector registrado como `ccee_agente`; `silver.ccee_agente` com as colunas listadas no Bronze abaixo mais as seis dimensões; `gold.agentes_por_classe_mensal`.

**O dado, lido em 14/09.** Dataset `lista_agente_associado`, recursos `_2025` e `_2026`. Colunas, na ordem do arquivo: `CNPJ`, `MES_REFERENCIA`, `SIGLA_AGENTE`, `RAZAO_SOCIAL`, `CLASSE_AGENTE`, `SITUACAO_COMERCIALIZADOR`, `SITUACAO_VAREJISTA`, `ESTADO`, `CATEGORIA_AGENTE`, `INDICADOR_VAREJISTA`. Um retrato por mês (~16.400 agentes), `(MES_REFERENCIA, CNPJ)` único, `(MES_REFERENCIA, SIGLA_AGENTE)` também. Domínios observados: `CLASSE_AGENTE` ∈ {Autoprodutor, Comercializador, Consumidor Especial, Consumidor Livre, Distribuidor, Gerador, Produtor Independente}; `CATEGORIA_AGENTE` ∈ {Comercialização, Consumo, Distribuição, Geração}; `SITUACAO_COMERCIALIZADOR` ∈ {vazio, Autorizado, Em análise da documentação}; `SITUACAO_VAREJISTA` ∈ {vazio, Aprovada, Em análise da documentação}; `INDICADOR_VAREJISTA` ∈ {Sim, Não}. **Não há coluna de perfil** — a ADR 021 dizia "agente ↔ perfil", e está errada (Task 9 corrige).

- [ ] **Step 1: Escrever o teste (falha: módulo não existe)**

A fixture é **bytes dentro do teste**, não arquivo: precisa misturar UTF-8 e ISO-8859-1 no mesmo CSV, e um arquivo salvo tem um encoding só.

```python
# tests/unit/conectores/test_ccee_agente.py
"""Conector CCEE/agente — lista mensal de agentes, sem rede.

Linhas sintéticas no formato real (lido em 14/09). A fixture é montada em bytes
porque o arquivo verdadeiro mistura UTF-8 e ISO-8859-1 linha a linha, e é isso
que o teste de acentuação protege.
"""

from __future__ import annotations

import io
from datetime import date

import pytest
from src.conectores.ccee_agente import AgenteCcee, CceeAgente
from src.core.execucao import Janela

CABECALHO = b"CNPJ;MES_REFERENCIA;SIGLA_AGENTE;RAZAO_SOCIAL;CLASSE_AGENTE;SITUACAO_COMERCIALIZADOR;SITUACAO_VAREJISTA;ESTADO;CATEGORIA_AGENTE;INDICADOR_VAREJISTA\n"
LINHAS = [
    "11111111000111;202601;ALFA;ALFA COMERCIALIZADORA LTDA;Comercializador;Autorizado;Aprovada;SP;Comercialização;Sim".encode("utf-8"),
    "22222222000122;202601;BETA;BETA ENERGIA S.A.;Gerador;;;MG;Geração;Não".encode("iso-8859-1"),
    "33333333000133;202601;GAMA;GAMA INDÚSTRIA LTDA;Consumidor Livre;;;PR;Consumo;Não".encode("iso-8859-1"),
    "11111111000111;202602;ALFA;ALFA COMERCIALIZADORA LTDA;Comercializador;Autorizado;Aprovada;SP;Comercialização;Sim".encode("utf-8"),
    "44444444000144;202602;DELTA;DELTA DISTRIBUIÇÃO S.A.;Distribuidor;;;RS;Distribuição;Não".encode("utf-8"),
]
CSV = CABECALHO + b"\n".join(LINHAS) + b"\n"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeAgente()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "lista_agente_associado_2026", "url": "u", "last_modified": "2026-09-03T18:27:55"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(CSV))
    return conector


def test_registrado_como_ccee_agente():
    assert CceeAgente.fonte == "ccee" and CceeAgente.entidade == "agente"


def test_extrai_o_mes_pedido(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-02-01", "2026-02-28")))

    assert [r["SIGLA_AGENTE"] for r in registros] == ["ALFA", "DELTA"]


def test_acentuacao_sobrevive_nos_dois_encodings(conector):
    registros = {r["SIGLA_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-01-01", "2026-02-28"))}

    assert registros["ALFA"]["CATEGORIA_AGENTE"] == "Comercialização"  # veio UTF-8
    assert registros["BETA"]["CATEGORIA_AGENTE"] == "Geração"  # veio ISO-8859-1
    assert registros["DELTA"]["RAZAO_SOCIAL"] == "DELTA DISTRIBUIÇÃO S.A."


def test_transformar_produz_o_registro_do_lake(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))
    registro = AgenteCcee.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.periodo_apuracao_ccee == "2026-01"
    assert registro.versao_publicacao == date(2026, 9, 3)
    assert registro.cnpj == "11111111000111"
    assert registro.agente_ccee == "ALFA"
    assert registro.classe_agente == "Comercializador"
    assert registro.situacao_comercializador == "Autorizado"
    assert registro.situacao_varejista == "Aprovada"
    assert registro.uf == "SP"
    assert registro.categoria_agente == "Comercialização"
    assert registro.varejista is True


def test_situacao_vazia_vira_nulo_e_nao_string_vazia(conector):
    registros = [AgenteCcee.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))]
    beta = next(r for r in registros if r.agente_ccee == "BETA")

    assert beta.situacao_comercializador is None
    assert beta.situacao_varejista is None
    assert beta.varejista is False


def test_classe_desconhecida_e_rejeitada():
    with pytest.raises(ValueError):
        AgenteCcee.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-03",
                "cnpj": "11111111000111",
                "agente_ccee": "X",
                "razao_social": "X",
                "classe_agente": "Transmissor",  # não está entre as 7 publicadas
                "uf": "SP",
                "categoria_agente": "Consumo",
                "varejista": False,
            }
        )


def test_cnpj_com_menos_de_14_digitos_e_rejeitado():
    with pytest.raises(ValueError, match="14"):
        AgenteCcee.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-03",
                "cnpj": "123",
                "agente_ccee": "X",
                "razao_social": "X",
                "classe_agente": "Gerador",
                "uf": "SP",
                "categoria_agente": "Geração",
                "varejista": False,
            }
        )


def test_ingerir_em_dry_run_conta_as_linhas(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-02-28"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0
    assert execucao.linhas_carregadas == 0  # dry-run
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `uv run pytest tests/unit/conectores/test_ccee_agente.py -q`
Expected: `ModuleNotFoundError: No module named 'src.conectores.ccee_agente'`

- [ ] **Step 3: Escrever o conector**

```python
# src/conectores/ccee_agente.py
"""Conector CCEE — lista mensal de agentes (Onda 1, público). Ordem 1 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `lista_agente_associado`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/lista_agente_associado

Um retrato por mês de todos os agentes da CCEE — cerca de 16.400 — com classe,
situação como comercializador e como varejista, UF e categoria. Diferente do
`ccee_perfil`, aqui **há histórico**: cada `MES_REFERENCIA` é um retrato, e a
Silver guarda todos.

**Não há coluna de perfil.** O elo agente ↔ perfil está em `lista_perfil_v1`
(`COD_AGENTE` + `COD_PERF_AGENTE`). Esta fonte enriquece o agente; não o liga
a nada.

Este é o arquivo que misturava UTF-8 e ISO-8859-1 linha a linha; a base
`CceeCsvCkan` decodifica por linha por causa dele.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Os valores que a CCEE publicava em 14/09/2026. Valor novo sem revisão do
# contrato de dados entraria como dado silenciosamente errado.
CLASSES = ("Autoprodutor", "Comercializador", "Consumidor Especial", "Consumidor Livre", "Distribuidor", "Gerador", "Produtor Independente")
CATEGORIAS = ("Comercialização", "Consumo", "Distribuição", "Geração")


class AgenteCcee(BaseModel):
    """Um agente da CCEE, como estava no mês de referência."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    cnpj: str
    agente_ccee: str  # SIGLA_AGENTE — dimensão comum do projeto
    razao_social: str
    classe_agente: Literal[CLASSES]  # type: ignore[valid-type]
    situacao_comercializador: str | None = None
    situacao_varejista: str | None = None
    uf: str
    categoria_agente: Literal[CATEGORIAS]  # type: ignore[valid-type]
    varejista: bool = False

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("uf")
    @classmethod
    def _uf_com_duas_letras(cls, valor: str) -> str:
        uf = valor.strip().upper()
        if len(uf) != 2 or not uf.isalpha():
            raise ValueError(f"UF inválida: {valor!r}")
        return uf


@registrar
class CceeAgente(CceeCsvCkan):
    """Lista mensal de agentes. CSV por ano; um retrato por mês."""

    dataset = "lista_agente_associado"
    entidade = "agente"
    schema = AgenteCcee

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "cnpj": limpar(bruto.get("CNPJ")),
            "agente_ccee": limpar(bruto.get("SIGLA_AGENTE")),
            "razao_social": limpar(bruto.get("RAZAO_SOCIAL")),
            "classe_agente": limpar(bruto.get("CLASSE_AGENTE")),
            "situacao_comercializador": limpar(bruto.get("SITUACAO_COMERCIALIZADOR")) or None,
            "situacao_varejista": limpar(bruto.get("SITUACAO_VAREJISTA")) or None,
            "uf": limpar(bruto.get("ESTADO")),
            "categoria_agente": limpar(bruto.get("CATEGORIA_AGENTE")),
            "varejista": limpar(bruto.get("INDICADOR_VAREJISTA")).lower().startswith("s"),
        }
```

Se o `Literal[CLASSES]` reclamar no pydantic (tupla como argumento de `Literal` exige `Literal[*CLASSES]` no 3.11+; se o ruff/pyright acusar), troque por `field_validator` no mesmo molde do `_uf_com_duas_letras`, com `if valor not in CLASSES: raise ValueError(...)`. O teste `test_classe_desconhecida_e_rejeitada` cobre qualquer uma das duas formas.

- [ ] **Step 4: Rodar até ficar verde**

Run: `uv run pytest tests/unit/conectores/test_ccee_agente.py -q`
Expected: `8 passed`

- [ ] **Step 5: Bronze**

```sql
-- definitions/bronze/ccee_agente.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: lista mensal de agentes da CCEE (dados abertos, `lista_agente_associado`).
-- Append-only: um retrato por mês, reprocessar insere de novo; a Silver deduplica.
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia          DATE      NOT NULL OPTIONS(description="Primeiro dia do mês de referência"),
  periodo_apuracao_ccee    STRING    NOT NULL OPTIONS(description="AAAA-MM do MES_REFERENCIA, como a CCEE declara"),
  versao_publicacao        DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN — a publicação que originou a linha (ADR 016)"),
  cnpj                     STRING    NOT NULL OPTIONS(description="14 dígitos, sem máscara"),
  agente_ccee              STRING    NOT NULL OPTIONS(description="Sigla do agente — dimensão comum"),
  razao_social             STRING    NOT NULL,
  classe_agente            STRING    NOT NULL OPTIONS(description="Autoprodutor, Comercializador, Consumidor Especial, Consumidor Livre, Distribuidor, Gerador, Produtor Independente"),
  situacao_comercializador STRING             OPTIONS(description="Autorizado ou Em análise da documentação; nulo quando não é comercializador"),
  situacao_varejista       STRING             OPTIONS(description="Aprovada ou Em análise da documentação; nulo quando não é varejista"),
  uf                       STRING    NOT NULL,
  categoria_agente         STRING    NOT NULL OPTIONS(description="Comercialização, Consumo, Distribuição, Geração"),
  varejista                BOOL      NOT NULL,

  _ingestao_id             STRING    NOT NULL,
  _ingestao_timestamp      TIMESTAMP NOT NULL,
  _fonte                   STRING    NOT NULL,
  _schema_versao           STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, agente_ccee
OPTIONS(description="Lista mensal de agentes da CCEE — camada Bronze, append-only");
```

- [ ] **Step 6: Silver**

```sql
-- definitions/silver/ccee_agente.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee", "cnpj"],
    nonNull: ["data_referencia", "periodo_apuracao_ccee", "cnpj", "agente_ccee", "classe_agente", "uf"],
    rowConditions: [
      "periodo_apuracao = periodo_apuracao_ccee",
      "LENGTH(cnpj) = 14",
      "LENGTH(uf) = 2",
      "classe_agente IN ('Autoprodutor','Comercializador','Consumidor Especial','Consumidor Livre','Distribuidor','Gerador','Produtor Independente')"
    ]
  }
}

-- Silver: um agente por mês, deduplicado pela publicação mais recente da CCEE
-- (ADR 016, opção B): vence `versao_publicacao`, e a hora da leitura só
-- desempata leituras da mesma publicação. É o que impede o replay de um raw
-- antigo de rebaixar o retrato vigente.
-- Faixas (issue #110): classe fora das sete publicadas é mudança de contrato de
-- dados na origem, não um agente novo.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,    -- o agente não tem submercado; o perfil tem (ccee_perfil)
  CAST(NULL AS STRING) AS codigo_usina,  -- cadastro de agente, não de ativo
  agente_ccee,
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  cnpj,
  razao_social,
  classe_agente,
  situacao_comercializador,
  situacao_varejista,
  uf,
  categoria_agente,
  varejista,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_agente")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee, cnpj
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

- [ ] **Step 7: Gold**

```sql
-- definitions/gold/agentes_por_classe_mensal.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: quantos agentes existem em cada classe e categoria, mês a mês — e
-- quantos deles atuam como varejista ou comercializador autorizado.
--
-- É a leitura de mercado que `agentes_ccee` (retrato de perfis) não dá: o
-- movimento de entrada e saída de agentes ao longo do tempo. Sem KPI (ADR 012):
-- contagem descritiva, sem meta nem fórmula de negócio.
SELECT
  periodo_apuracao,
  classe_agente,
  categoria_agente,
  COUNT(*)                                                       AS agentes,
  COUNTIF(varejista)                                             AS varejistas,
  COUNTIF(situacao_comercializador = 'Autorizado')               AS comercializadores_autorizados,
  COUNTIF(situacao_varejista = 'Aprovada')                       AS varejistas_aprovados,
  COUNT(DISTINCT uf)                                             AS ufs
FROM ${ref("silver", "ccee_agente")}
GROUP BY periodo_apuracao, classe_agente, categoria_agente
```

- [ ] **Step 8: Rodar os testes de SQL**

Run: `uv run pytest tests/unit/test_sql.py -q`
Expected: os três arquivos novos entram na parametrização e passam (sintaxe BigQuery, camadas, partição, dimensões comuns, `uniqueKey`/`nonNull`, Silver lê Bronze e Gold lê Silver, `test_toda_camada_tem_o_mesmo_conjunto_de_fontes`).

- [ ] **Step 9: Agendamento e alerta**

Em `infra/modules/scheduler/main.tf`, dentro de `default = { … }` de `variable "conectores"`, depois do bloco `ccee_perfil`:

```hcl
    ccee_agente = {
      # Retrato mensal; a CCEE republica meses fechados (ADR 016). Dia 6, depois
      # do PLD (dia 5), para não disputar a mesma janela.
      cron         = "0 10 6 * *"
      ultimos_dias = 120 # cobre a recontabilização e a defasagem de publicação
    }
```

Em `infra/modules/monitoramento/main.tf`, em `conectores_criticos`:

```hcl
    ccee_agente     = 780 # mensal + folga
```

Run: `terraform fmt -check -recursive infra/ && uv run pytest tests/unit/test_infra.py -q`
Expected: limpo; testes verdes.

- [ ] **Step 10: Domínio no portal**

Em `src/portal/custo.py`, no dicionário `DOMINIO_ANALITICO`, depois de `"ccee_perfil": "Mercado de Energia",`:

```python
    "ccee_agente": "Mercado de Energia",
```

Run: `uv run pytest tests/unit/test_portal.py -q`
Expected: verde — `test_todo_conector_registrado_tem_dominio_na_visao_de_diretoria` passa a enxergar o conector novo.

- [ ] **Step 11: Dicionário e índice**

```markdown
<!-- docs/dicionario-dados/ccee_agente.md -->
# CCEE — lista mensal de agentes

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `lista_agente_associado` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=lista_agente_associado` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2025`, `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal de retratos**: um por `MES_REFERENCIA`, ~16.400 agentes cada |
| Volume verificado | 147.801 linhas em 2026 (jan–set), 16 MB, em 14/09/2026 |
| Encoding | **UTF-8 e ISO-8859-1 misturados linha a linha** — decodificação por linha na base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia (B1) |
| Credencial | nenhuma |

Ordem 1 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
**Não há coluna de perfil**: o elo agente ↔ perfil vive em
[`ccee_perfil.md`](ccee_perfil.md). Esta fonte enriquece o agente — classe,
situação como comercializador e como varejista, UF — com histórico mensal.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `CNPJ` | `cnpj` | STRING | só dígitos; 14 obrigatórios |
| `SIGLA_AGENTE` | `agente_ccee` | STRING | trim — **dimensão comum** |
| `RAZAO_SOCIAL` | `razao_social` | STRING | trim |
| `CLASSE_AGENTE` | `classe_agente` | STRING | uma das 7 publicadas; outra é rejeitada |
| `SITUACAO_COMERCIALIZADOR` | `situacao_comercializador` | STRING | vazio → NULL |
| `SITUACAO_VAREJISTA` | `situacao_varejista` | STRING | vazio → NULL |
| `ESTADO` | `uf` | STRING | maiúsculo, 2 letras |
| `CATEGORIA_AGENTE` | `categoria_agente` | STRING | uma das 4 publicadas |
| `INDICADOR_VAREJISTA` | `varejista` | BOOL | `Sim` → true |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | o agente não tem submercado; o perfil tem |
| `codigo_usina` | não | cadastro de agente, não de ativo |
| `agente_ccee` | **sim** | `SIGLA_AGENTE` |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `cnpj`). Vence a **publicação mais
recente** (`versao_publicacao`), e a hora da leitura só desempata leituras da
mesma publicação — opção B da ADR 016. Replay de raw antigo não rebaixa o
retrato vigente.

## Gold

`gold.agentes_por_classe_mensal` — agentes por classe e categoria, mês a mês,
com quantos são varejistas e comercializadores autorizados. Contagem descritiva
(ADR 012).

## Qualidade e observações

- **Encoding misto no arquivo real**: 49.269 linhas UTF-8 e 98.532 ISO-8859-1
  no recurso de 2026. Decodificar tudo num encoding só mutila metade das
  razões sociais em silêncio.
- Valores de classe, categoria e situação foram lidos do arquivo em 14/09. Valor
  novo é rejeitado e contado em `linhas_invalidas` — é o sinal de que a CCEE
  mudou o contrato.
- `SITUACAO_COMERCIALIZADOR` vazio em 97% das linhas: só comercializadores têm
  situação. Vazio é NULL, não "sem situação".

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → lista_agente_associado_{ano}.csv
  → gs://<bucket>-raw/ccee/agente/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_agente          (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_agente        (QUALIFY por mês+cnpj, versao_publicacao DESC)
        → gold.agentes_por_classe_mensal
```
```

Em `docs/dicionario-dados/README.md`, na tabela "O que existe", depois da linha de `ccee_perfil`:

```markdown
| CCEE — lista mensal de agentes | [`ccee_agente.md`](ccee_agente.md) | 1 | `agente_ccee` | `agentes_por_classe_mensal` |
```

- [ ] **Step 12: Dry-run contra a API real** (é o padrão de evidência do projeto)

Run: `uv run python -m src.cli ingerir ccee_agente --de 2026-08-01 --ate 2026-09-30 --dry-run`
Expected: `SUCESSO`, ~32.900 extraídos (dois meses × ~16.400), `0 inválidos`. Anote os números — vão para a tabela de conectores de `docs/status.md` na Task 9. Se aparecerem inválidos, leia o primeiro aviso do log: é um valor de classe/categoria/situação que não estava na lista de 14/09, e a lista no conector precisa dele.

- [ ] **Step 13: Suíte inteira, lint e commit**

Run: `uv run ruff check src tests && uv run ruff format --check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_agente.py definitions/bronze/ccee_agente.sqlx definitions/silver/ccee_agente.sqlx definitions/gold/agentes_por_classe_mensal.sqlx tests/unit/conectores/test_ccee_agente.py docs/dicionario-dados/ccee_agente.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): lista mensal de agentes, primeira entidade da fila da ADR 021

Um retrato por mes de todos os agentes da CCEE, com classe, situacao de
comercializador e de varejista, UF e categoria. Diferente do ccee_perfil, aqui
ha historico: cada MES_REFERENCIA e um retrato, e a Silver guarda todos.

Nao ha coluna de perfil. A ADR 021 dizia "agente <-> perfil", e esta errada: o
elo esta em lista_perfil_v1. Esta fonte enriquece o agente, nao o liga a nada.

E a primeira Silver com a opcao B da ADR 016: vence versao_publicacao (o
last_modified do CKAN), e a hora da leitura so desempata. Replay de raw antigo
deixa de rebaixar o retrato vigente.

Dry-run contra a API real: <N> registros em agosto e setembro, 0 invalidos.
```

```bash
git commit -F <arquivo>
```

---

### Task 3: `ccee_exposicao_financeira` — a exposição do mercado, mês a mês (ordem 2)

**Files:**
- Create: `src/conectores/ccee_exposicao_financeira.py`
- Create: `definitions/bronze/ccee_exposicao_financeira.sqlx`
- Create: `definitions/silver/ccee_exposicao_financeira.sqlx`
- Create: `definitions/gold/exposicao_mercado_mensal.sqlx`
- Test: `tests/unit/conectores/test_ccee_exposicao_financeira.py`
- Create: `tests/fixtures/ccee_exposicao_financeira_2026.csv`
- Create: `docs/dicionario-dados/ccee_exposicao_financeira.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan`, `numero_ou_nulo`, `primeiro_dia`, `periodo_ccee`.
- Produces: `silver.ccee_exposicao_financeira` (uma linha por mês); `gold.exposicao_mercado_mensal`.

**O dado, lido em 14/09.** Dataset `exposicao_financeira_mensal`, recursos `_2023` a `_2026`. Uma linha por `MES_REFERENCIA`, valores de mercado inteiro (sem agente), em R$ com ponto decimal. Colunas: `MES_REFERENCIA`, `EXCEDENTE_FINANCEIRO`, `EXCEDENTE_FINANCEIRO_POSITIVO`, `TOTAL_RECURSO_DISPONIVEL`, `TOTAL_EXPOSICAO_NEGATIVA`, `COBERTURA_EXPOSICAO_NEGATIVA`, `TOTAL_EXPOSICAO_NEGATIVA_REM`, `TOTAL_EXPOSICAO_NEGATIVA_LIQ`, `TOTAL_RECURSO_DISPONIVEL_EF_ANT`, `TOTAL_RECURSO_COMPENSACAO_EF_N`, `RESERVA_ALIVIO_ESS`. É o que o B1 nomeia como **exposição** em Risco e Compliance, e o domínio sai de zero com 968 bytes.

- [ ] **Step 1: Fixture sintética e teste (falha)**

```csv
MES_REFERENCIA;EXCEDENTE_FINANCEIRO;EXCEDENTE_FINANCEIRO_POSITIVO;TOTAL_RECURSO_DISPONIVEL;TOTAL_EXPOSICAO_NEGATIVA;COBERTURA_EXPOSICAO_NEGATIVA;TOTAL_EXPOSICAO_NEGATIVA_REM;TOTAL_EXPOSICAO_NEGATIVA_LIQ;TOTAL_RECURSO_DISPONIVEL_EF_ANT;TOTAL_RECURSO_COMPENSACAO_EF_N;RESERVA_ALIVIO_ESS
202607;3410635.09;871785.17;4282420.26;516305.12;516305.12;0;0;3766115.14;0;3766115.14
202606;54320599.04;10033204.82;64353803.86;4067206.7;4067206.7;0;0;60286597.16;0;60286597.16
202605;1000.5;;1000.5;0;0;0;0;1000.5;0;1000.5
```

(Salve como `tests/fixtures/ccee_exposicao_financeira_2026.csv`, UTF-8 sem BOM. A terceira linha tem um campo vazio de propósito.)

```python
# tests/unit/conectores/test_ccee_exposicao_financeira.py
"""Conector CCEE/exposição financeira — uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_exposicao_financeira import CceeExposicaoFinanceira, ExposicaoFinanceira
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_exposicao_financeira_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeExposicaoFinanceira()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "exposicao_financeira_mensal_2026", "url": "u", "last_modified": "2026-09-01T14:54:27"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_os_meses_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-06-01", "2026-07-31")))

    assert sorted(r["MES_REFERENCIA"] for r in registros) == ["202606", "202607"]


def test_transformar_tipa_os_valores_e_data_o_mes(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = ExposicaoFinanceira.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.versao_publicacao == date(2026, 9, 1)
    assert registro.excedente_financeiro == Decimal("3410635.09")
    assert registro.total_exposicao_negativa == Decimal("516305.12")
    assert registro.reserva_alivio_ess == Decimal("3766115.14")


def test_campo_vazio_vira_nulo(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-05-01", "2026-05-31")))
    registro = ExposicaoFinanceira.model_validate(conector.transformar(bruto))

    assert registro.excedente_financeiro_positivo is None


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-05-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 3
    assert execucao.linhas_invalidas == 0
```

Run: `uv run pytest tests/unit/conectores/test_ccee_exposicao_financeira.py -q` → `ModuleNotFoundError`.

- [ ] **Step 2: Conector**

```python
# src/conectores/ccee_exposicao_financeira.py
"""Conector CCEE — exposição financeira do mercado, por mês (Onda 1, público). Ordem 2 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `exposicao_financeira_mensal`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/exposicao_financeira_mensal

Uma linha por mês, valores do mercado inteiro em R$. É a "exposição" que o B1
nomeia em Risco e Compliance — e a menor fonte do lake: 968 bytes em 2026.
Sem agente, sem submercado; o que ela responde é quanto o MCP ficou exposto
e quanto disso foi coberto.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Coluna da origem → coluna do lake. A ordem é a do arquivo.
CAMPOS = {
    "EXCEDENTE_FINANCEIRO": "excedente_financeiro",
    "EXCEDENTE_FINANCEIRO_POSITIVO": "excedente_financeiro_positivo",
    "TOTAL_RECURSO_DISPONIVEL": "total_recurso_disponivel",
    "TOTAL_EXPOSICAO_NEGATIVA": "total_exposicao_negativa",
    "COBERTURA_EXPOSICAO_NEGATIVA": "cobertura_exposicao_negativa",
    "TOTAL_EXPOSICAO_NEGATIVA_REM": "total_exposicao_negativa_remanescente",
    "TOTAL_EXPOSICAO_NEGATIVA_LIQ": "total_exposicao_negativa_liquidada",
    "TOTAL_RECURSO_DISPONIVEL_EF_ANT": "total_recurso_disponivel_ef_anterior",
    "TOTAL_RECURSO_COMPENSACAO_EF_N": "total_recurso_compensacao_ef",
    "RESERVA_ALIVIO_ESS": "reserva_alivio_ess",
}


class ExposicaoFinanceira(BaseModel):
    """A exposição financeira do MCP em um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    excedente_financeiro: Decimal | None = None
    excedente_financeiro_positivo: Decimal | None = None
    total_recurso_disponivel: Decimal | None = None
    total_exposicao_negativa: Decimal | None = None
    cobertura_exposicao_negativa: Decimal | None = None
    total_exposicao_negativa_remanescente: Decimal | None = None
    total_exposicao_negativa_liquidada: Decimal | None = None
    total_recurso_disponivel_ef_anterior: Decimal | None = None
    total_recurso_compensacao_ef: Decimal | None = None
    reserva_alivio_ess: Decimal | None = None


@registrar
class CceeExposicaoFinanceira(CceeCsvCkan):
    """Exposição financeira mensal. CSV por ano, uma linha por mês."""

    dataset = "exposicao_financeira_mensal"
    entidade = "exposicao_financeira"
    schema = ExposicaoFinanceira

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
        }
        for origem, destino in CAMPOS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
```

Run: `uv run pytest tests/unit/conectores/test_ccee_exposicao_financeira.py -q` → `4 passed`.

- [ ] **Step 3: Bronze, Silver, Gold**

```sql
-- definitions/bronze/ccee_exposicao_financeira.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: exposição financeira mensal do MCP (CCEE, dados abertos). Uma linha
-- por mês e por publicação; a Silver fica com a publicação mais recente.
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia                        DATE      NOT NULL OPTIONS(description="Primeiro dia do mês de referência"),
  periodo_apuracao_ccee                  STRING    NOT NULL OPTIONS(description="AAAA-MM, como a CCEE declara"),
  versao_publicacao                      DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN (ADR 016)"),
  excedente_financeiro                   NUMERIC            OPTIONS(description="R$"),
  excedente_financeiro_positivo          NUMERIC            OPTIONS(description="R$"),
  total_recurso_disponivel               NUMERIC            OPTIONS(description="R$"),
  total_exposicao_negativa               NUMERIC            OPTIONS(description="R$"),
  cobertura_exposicao_negativa           NUMERIC            OPTIONS(description="R$"),
  total_exposicao_negativa_remanescente  NUMERIC            OPTIONS(description="R$"),
  total_exposicao_negativa_liquidada     NUMERIC            OPTIONS(description="R$"),
  total_recurso_disponivel_ef_anterior   NUMERIC            OPTIONS(description="R$"),
  total_recurso_compensacao_ef           NUMERIC            OPTIONS(description="R$"),
  reserva_alivio_ess                     NUMERIC            OPTIONS(description="R$"),

  _ingestao_id                           STRING    NOT NULL,
  _ingestao_timestamp                    TIMESTAMP NOT NULL,
  _fonte                                 STRING    NOT NULL,
  _schema_versao                         STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia
OPTIONS(description="Exposição financeira mensal do MCP — camada Bronze, append-only");
```

```sql
-- definitions/silver/ccee_exposicao_financeira.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee"],
    nonNull: ["data_referencia", "periodo_apuracao_ccee", "versao_publicacao"],
    rowConditions: [
      "periodo_apuracao = periodo_apuracao_ccee",
      "total_exposicao_negativa IS NULL OR total_exposicao_negativa >= 0",
      "cobertura_exposicao_negativa IS NULL OR total_exposicao_negativa IS NULL OR cobertura_exposicao_negativa <= total_exposicao_negativa"
    ]
  }
}

-- Silver: uma linha por mês, pela publicação mais recente (ADR 016, opção B).
-- Faixas (issue #110): exposição negativa é um total, não pode ser negativa;
-- cobertura maior que a exposição é troca de coluna na origem.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,    -- total do mercado
  CAST(NULL AS STRING) AS codigo_usina,  -- idem
  CAST(NULL AS STRING) AS agente_ccee,   -- idem
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  excedente_financeiro,
  excedente_financeiro_positivo,
  total_recurso_disponivel,
  total_exposicao_negativa,
  cobertura_exposicao_negativa,
  total_exposicao_negativa_remanescente,
  total_exposicao_negativa_liquidada,
  total_recurso_disponivel_ef_anterior,
  total_recurso_compensacao_ef,
  reserva_alivio_ess,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_exposicao_financeira")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

```sql
-- definitions/gold/exposicao_mercado_mensal.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: quanto o mercado de curto prazo ficou exposto, quanto foi coberto e
-- quanto sobrou, mês a mês — em R$ e em fração coberta.
--
-- Primeira tabela do domínio Risco e Compliance. A fração é aritmética de
-- leitura, não indicador de negócio (ADR 012): ninguém definiu meta para ela.
SELECT
  periodo_apuracao,
  versao_publicacao,
  total_exposicao_negativa                 AS exposicao_negativa_reais,
  cobertura_exposicao_negativa             AS cobertura_reais,
  total_exposicao_negativa_remanescente    AS exposicao_remanescente_reais,
  total_exposicao_negativa_liquidada       AS exposicao_liquidada_reais,
  SAFE_DIVIDE(cobertura_exposicao_negativa, total_exposicao_negativa) AS fracao_coberta,
  excedente_financeiro                     AS excedente_financeiro_reais,
  reserva_alivio_ess                       AS reserva_alivio_ess_reais
FROM ${ref("silver", "ccee_exposicao_financeira")}
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde.

- [ ] **Step 4: Agendamento, alerta, domínio, dicionário**

`infra/modules/scheduler/main.tf`, depois de `ccee_agente`:

```hcl
    ccee_exposicao_financeira = {
      cron         = "0 10 6 * *" # publicação mensal; dia 6, depois do PLD
      ultimos_dias = 120          # recontabilização (ADR 016)
    }
```

`infra/modules/monitoramento/main.tf`: `ccee_exposicao_financeira = 780`.

`src/portal/custo.py`: `"ccee_exposicao_financeira": "Risco e Compliance",`.

`docs/dicionario-dados/ccee_exposicao_financeira.md` — mesmas seções do dicionário da Task 2 (cabeçalho, Campos, Dimensões comuns, Deduplicação e versão, Gold, Qualidade, Linhagem), com este conteúdo específico:

- cabeçalho: dataset `exposicao_financeira_mensal`; recursos `_2023`…`_2026`; natureza **série mensal, mercado inteiro**; volume 7 linhas / 968 bytes em 2026; encoding ASCII (não há texto); dono Letícia Ferreira — Risco e Compliance (B1);
- Campos: as dez colunas da origem → nomes do lake conforme `CAMPOS` do conector, todas `NUMERIC` nulas quando vazias; `MES_REFERENCIA` → `data_referencia`, `periodo_apuracao_ccee`; `last_modified` → `versao_publicacao`;
- Dimensões comuns: só `data_referencia`, `periodo_apuracao` e `periodo_apuracao_ccee`; as outras três nulas porque é total do mercado;
- Deduplicação: chave (`periodo_apuracao_ccee`), vence `versao_publicacao`;
- Gold: `exposicao_mercado_mensal`, com a ressalva de que `fracao_coberta` é aritmética de leitura, não KPI;
- Qualidade: valores em R$ com ponto decimal; o significado exato de cada coluna (`EF_ANT`, `EF_N`) **não está documentado pela CCEE no catálogo** — nomes preservados de perto por isso, e a dúvida vai ao dono do domínio (B3: 3 dias úteis);
- Linhagem: `exposicao_financeira_mensal_{ano}.csv → raw/ccee/exposicao_financeira → bronze → silver → gold.exposicao_mercado_mensal`.

`docs/dicionario-dados/README.md`: `| CCEE — exposição financeira mensal | [`ccee_exposicao_financeira.md`](ccee_exposicao_financeira.md) | 1 | — | `exposicao_mercado_mensal` |`.

- [ ] **Step 5: Dry-run real, suíte, commit**

Run: `uv run python -m src.cli ingerir ccee_exposicao_financeira --de 2026-01-01 --ate 2026-07-31 --dry-run`
Expected: `SUCESSO`, 7 extraídos, 0 inválidos.

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_exposicao_financeira.py definitions/bronze/ccee_exposicao_financeira.sqlx definitions/silver/ccee_exposicao_financeira.sqlx definitions/gold/exposicao_mercado_mensal.sqlx tests/unit/conectores/test_ccee_exposicao_financeira.py tests/fixtures/ccee_exposicao_financeira_2026.csv docs/dicionario-dados/ccee_exposicao_financeira.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): exposicao financeira mensal -- Risco e Compliance sai do zero

Uma linha por mes, valores do mercado inteiro em R$: quanto o MCP ficou
exposto, quanto foi coberto e quanto sobrou. E a "exposicao" que o B1 nomeia
em Risco e Compliance, e a menor fonte do lake: 968 bytes em 2026.

Primeira Gold do dominio. A fracao coberta e aritmetica de leitura, nao KPI:
ninguem definiu meta para ela (ADR 012).

O significado exato de duas colunas (EF_ANT, EF_N) nao esta documentado pela
CCEE no catalogo; os nomes ficam proximos da origem e a duvida vai ao dono do
dominio.

Dry-run contra a API real: 7 registros, 0 invalidos.
```

---
### Task 4: `ccee_contabilizacao_perfil` — o resultado da contabilização por perfil, e a ADR 016 aceita (ordem 2)

**Files:**
- Create: `src/conectores/ccee_contabilizacao_perfil.py`
- Create: `definitions/bronze/ccee_contabilizacao_perfil.sqlx`
- Create: `definitions/silver/ccee_contabilizacao_perfil.sqlx` (vigente)
- Create: `definitions/silver/ccee_contabilizacao_perfil_historico.sqlx` (uma linha por chave e versão — ADR 016, opção B)
- Create: `definitions/gold/resultado_contabilizacao_mensal_perfil.sqlx`
- Test: `tests/unit/conectores/test_ccee_contabilizacao_perfil.py`
- Modify: `tests/unit/test_sql.py:148-152` (`test_toda_camada_tem_o_mesmo_conjunto_de_fontes` passa a ignorar o sufixo `_historico`)
- Create: `tests/fixtures/ccee_contabilizacao_perfil_2026.csv`
- Create: `docs/dicionario-dados/ccee_contabilizacao_perfil.md`
- Modify: `docs/arquitetura/decisoes/016-versionamento-de-recontabilizacao.md` (status `proposto` → `aceito`, com o identificador registrado)
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan`, `limpar`, `numero_ou_nulo`, `primeiro_dia`, `periodo_ccee`; `gold.agentes_ccee` (existente: `codigo_perfil`, `agente_ccee`, `sigla_perfil`) para a junção na Gold.
- Produces: `silver.ccee_contabilizacao_perfil` (vigente), `silver.ccee_contabilizacao_perfil_historico`, `gold.resultado_contabilizacao_mensal_perfil`.

**O dado, lido em 14/09.** Dataset `contabilizacao_montante_perfil_agente`, recursos `_2024`…`_2026`. 329.080 linhas em 2026 (jan–jul, ~47.000 perfis/mês), 43 MB. `(MES_REFERENCIA, COD_PERF_AGENTE)` único. Colunas: `MES_REFERENCIA`, `COD_AGENTE`, `NOME_EMPRESARIAL`, `COD_PERF_AGENTE`, `SIGLA_PERFIL_AGENTE`, `CNPJ`, e 16 valores em R$: `VALOR_TM_MCP`, `COMPENSACAO_MRE`, `VALOR_ENCARGO`, `VALOR_AJUSTE_EXPOSICAO`, `VALOR_AJUSTE_ALIVIO_RET`, `EFEITO_CONTRAT_DISP`, `EFEITO_CONTRAT_COTA_GF`, `EFEITO_CONTRAT_NUCLEAR`, `AJUSTE_RECONTAB`, `AJUSTE_MCSD_EX`, `RESULTADO_FINANCEIRO_ER`, `EFEITO_CCEARQ`, `EFEITO_CONTRAT_ITAIPU`, `EFEITO_REPASSE_RISCO_HIDRO`, `EFEITO_DESLOC_PLD_CMO`, `RESULTADO_FINAL`. Vazios (→ NULL): `COMPENSACAO_MRE` em 98%, `AJUSTE_MCSD_EX` e `EFEITO_CCEARQ` em ~100%, `VALOR_TM_MCP` em 43%, `EFEITO_CONTRAT_DISP` em 14%, `AJUSTE_RECONTAB` em 2%, `VALOR_AJUSTE_ALIVIO_RET` em 0,2%. Encoding misto (760 linhas UTF-8, 1.001 ISO-8859-1).

**Por que esta é a fonte que aceita a ADR 016.** Ela traz `AJUSTE_RECONTAB` — a recontabilização está no dado — e a CCEE republica o recurso do ano (o `last_modified` de `_2025` é 02/02/2026: o ano inteiro foi reescrito). O identificador de versão é `versao_publicacao` = `last_modified` do recurso (item 2 da ordem de preferência da ADR). O que a ADR pedia para decidir — *"verificar se o arquivo ou o seu metadado trazem versão ou data de publicação"* — está respondido: o arquivo não, o metadado sim.

**Sobre `agente_ccee`.** O arquivo traz `COD_AGENTE` e `SIGLA_PERFIL_AGENTE`, mas **não** a sigla do agente. A Silver expõe `codigo_agente`, `codigo_perfil` e `sigla_perfil`, e deixa `agente_ccee` nulo com o motivo escrito; a Gold junta com `gold.agentes_ccee` por `codigo_perfil` para trazer a sigla — é exatamente o uso para o qual aquela tabela de dimensão foi escrita.

- [ ] **Step 1: Ajustar o teste de SQL que não sabe de `_historico` (falha primeiro com a view nova; faça o ajuste já)**

Em `tests/unit/test_sql.py`, substitua a função `test_toda_camada_tem_o_mesmo_conjunto_de_fontes` por:

```python
def test_toda_camada_tem_o_mesmo_conjunto_de_fontes():
    """Uma fonte com Bronze mas sem Silver é entrega incompleta (7 componentes).

    A view `_historico` (ADR 016, opção B) é a segunda Silver da mesma fonte,
    não uma fonte: fica fora da comparação.
    """
    bronze = {c.stem for c in (DEFINICOES / "bronze").glob("*.sqlx") if not c.stem.startswith("_")}
    silver = {c.stem for c in (DEFINICOES / "silver").glob("*.sqlx") if not c.stem.endswith("_historico")}
    assert bronze == silver, f"Bronze e Silver divergem: só em Bronze {bronze - silver}, só em Silver {silver - bronze}"
```

E acrescente, logo abaixo:

```python
def test_view_de_historico_tem_bronze_e_silver_vigente():
    """`x_historico` só existe ao lado de `x`: histórico sem vigente é meia ADR 016."""
    for historico in (DEFINICOES / "silver").glob("*_historico.sqlx"):
        base = historico.stem.removesuffix("_historico")
        assert (DEFINICOES / "silver" / f"{base}.sqlx").exists(), f"{historico.name} sem a Silver vigente {base}"
        assert (DEFINICOES / "bronze" / f"{base}.sqlx").exists(), f"{historico.name} sem Bronze {base}"
        bloco = config(historico)
        assert "uniqueKey:" in bloco and "versao_publicacao" in bloco, "histórico sem assertion em (chave, versão)"
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde (ainda não há `_historico`; o teste novo itera zero arquivos).

- [ ] **Step 2: Fixture sintética e teste do conector (falha)**

`tests/fixtures/ccee_contabilizacao_perfil_2026.csv` (UTF-8; vazios de propósito):

```csv
MES_REFERENCIA;COD_AGENTE;NOME_EMPRESARIAL;COD_PERF_AGENTE;SIGLA_PERFIL_AGENTE;CNPJ;VALOR_TM_MCP;COMPENSACAO_MRE;VALOR_ENCARGO;VALOR_AJUSTE_EXPOSICAO;VALOR_AJUSTE_ALIVIO_RET;EFEITO_CONTRAT_DISP;EFEITO_CONTRAT_COTA_GF;EFEITO_CONTRAT_NUCLEAR;AJUSTE_RECONTAB;AJUSTE_MCSD_EX;RESULTADO_FINANCEIRO_ER;EFEITO_CCEARQ;EFEITO_CONTRAT_ITAIPU;EFEITO_REPASSE_RISCO_HIDRO;EFEITO_DESLOC_PLD_CMO;RESULTADO_FINAL
202607;100;ALFA DISTRIBUIÇÃO S.A.;100;ALFA DIST;11111111000111;8815202.25;;9302.75;241283.86;0;-9693912.17;-1487611.51;355556.34;-484932.82;;0;;-4840714.04;-5887769.15;-55304.76;-13028903.59
202607;100;ALFA DISTRIBUIÇÃO S.A.;83729;ALFA SUL;11111111000111;-11834429.39;;11341.94;193980.74;0;-12756553.03;-1589959.04;433495.38;;;0;;-4529340.36;-7178386.26;-61487.48;-38178938.04
202607;200;BETA GERAÇÃO LTDA;200;BETA;22222222000122;;1500.5;0;0;0;;0;0;0;;0;;0;0;0;1500.5
202606;100;ALFA DISTRIBUIÇÃO S.A.;100;ALFA DIST;11111111000111;1000;;0;0;0;0;0;0;0;;0;;0;0;0;1000
```

```python
# tests/unit/conectores/test_ccee_contabilizacao_perfil.py
"""Conector CCEE/contabilização por perfil — a fonte que aceita a ADR 016, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_contabilizacao_perfil import CceeContabilizacaoPerfil, ContabilizacaoPerfil
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_contabilizacao_perfil_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeContabilizacaoPerfil()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "contabilizacao_montante_perfil_agente_2026", "url": "u", "last_modified": "2026-09-01T14:50:45"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_o_mes_pedido(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert [r["COD_PERF_AGENTE"] for r in registros] == ["100", "83729", "200"]


def test_transformar_tipa_valores_e_preserva_os_codigos(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ContabilizacaoPerfil.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.versao_publicacao == date(2026, 9, 1)
    assert registro.codigo_agente == "100"
    assert registro.codigo_perfil == "100"
    assert registro.sigla_perfil == "ALFA DIST"
    assert registro.cnpj == "11111111000111"
    assert registro.valor_tm_mcp == Decimal("8815202.25")
    assert registro.resultado_final == Decimal("-13028903.59")
    assert registro.ajuste_recontab == Decimal("-484932.82")


def test_vazio_vira_nulo_e_zero_continua_zero(conector):
    registros = {r["COD_PERF_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))}
    beta = ContabilizacaoPerfil.model_validate(conector.transformar(registros["200"]))
    alfa_sul = ContabilizacaoPerfil.model_validate(conector.transformar(registros["83729"]))

    assert beta.valor_tm_mcp is None  # vazio na origem
    assert beta.compensacao_mre == Decimal("1500.5")
    assert beta.valor_encargo == Decimal("0")  # zero é valor
    assert alfa_sul.ajuste_recontab is None


def test_dois_perfis_do_mesmo_agente_no_mesmo_mes_sao_linhas_distintas(conector):
    registros = [ContabilizacaoPerfil.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))]
    alfa = [r for r in registros if r.codigo_agente == "100"]

    assert {r.codigo_perfil for r in alfa} == {"100", "83729"}


def test_cnpj_invalido_e_rejeitado():
    with pytest.raises(ValueError, match="14"):
        ContabilizacaoPerfil.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_agente": "1",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "cnpj": "12",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
```

Run: `uv run pytest tests/unit/conectores/test_ccee_contabilizacao_perfil.py -q` → `ModuleNotFoundError`.

- [ ] **Step 3: Conector**

```python
# src/conectores/ccee_contabilizacao_perfil.py
"""Conector CCEE — resultado da contabilização por perfil de agente (Onda 1, público). Ordem 2 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `contabilizacao_montante_perfil_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/contabilizacao_montante_perfil_agente

Uma linha por perfil de agente e mês, com os 16 componentes do resultado
financeiro no MCP e o `RESULTADO_FINAL`. ~47.000 perfis por mês.

**É a fonte que aceita a ADR 016.** A recontabilização está no dado
(`AJUSTE_RECONTAB`) e a CCEE reescreve o recurso do ano inteiro ao republicar.
O identificador de versão é o `last_modified` do recurso no CKAN, que a base
`CceeCsvCkan` injeta como `_versao_publicacao`. A Silver vigente ordena por
ele; a Silver `_historico` guarda uma linha por chave e versão.

O arquivo traz `COD_AGENTE`, não a sigla do agente: `agente_ccee` fica nulo na
Silver, e a Gold traz a sigla juntando com `gold.agentes_ccee` por
`codigo_perfil`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

# Coluna da origem → coluna do lake, na ordem do arquivo. Todos em R$.
VALORES = {
    "VALOR_TM_MCP": "valor_tm_mcp",
    "COMPENSACAO_MRE": "compensacao_mre",
    "VALOR_ENCARGO": "valor_encargo",
    "VALOR_AJUSTE_EXPOSICAO": "valor_ajuste_exposicao",
    "VALOR_AJUSTE_ALIVIO_RET": "valor_ajuste_alivio_retroativo",
    "EFEITO_CONTRAT_DISP": "efeito_contratos_disponibilidade",
    "EFEITO_CONTRAT_COTA_GF": "efeito_contratos_cota_gf",
    "EFEITO_CONTRAT_NUCLEAR": "efeito_contratos_nuclear",
    "AJUSTE_RECONTAB": "ajuste_recontab",
    "AJUSTE_MCSD_EX": "ajuste_mcsd_ex",
    "RESULTADO_FINANCEIRO_ER": "resultado_financeiro_energia_reserva",
    "EFEITO_CCEARQ": "efeito_ccearq",
    "EFEITO_CONTRAT_ITAIPU": "efeito_contratos_itaipu",
    "EFEITO_REPASSE_RISCO_HIDRO": "efeito_repasse_risco_hidrologico",
    "EFEITO_DESLOC_PLD_CMO": "efeito_deslocamento_pld_cmo",
    "RESULTADO_FINAL": "resultado_final",
}


class ContabilizacaoPerfil(BaseModel):
    """O resultado financeiro de um perfil de agente em um mês de apuração."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_agente: str
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    cnpj: str
    valor_tm_mcp: Decimal | None = None
    compensacao_mre: Decimal | None = None
    valor_encargo: Decimal | None = None
    valor_ajuste_exposicao: Decimal | None = None
    valor_ajuste_alivio_retroativo: Decimal | None = None
    efeito_contratos_disponibilidade: Decimal | None = None
    efeito_contratos_cota_gf: Decimal | None = None
    efeito_contratos_nuclear: Decimal | None = None
    ajuste_recontab: Decimal | None = None
    ajuste_mcsd_ex: Decimal | None = None
    resultado_financeiro_energia_reserva: Decimal | None = None
    efeito_ccearq: Decimal | None = None
    efeito_contratos_itaipu: Decimal | None = None
    efeito_repasse_risco_hidrologico: Decimal | None = None
    efeito_deslocamento_pld_cmo: Decimal | None = None
    resultado_final: Decimal | None = None

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("codigo_agente", "codigo_perfil")
    @classmethod
    def _codigo_numerico(cls, valor: str) -> str:
        codigo = valor.strip()
        if not codigo.isdigit():
            raise ValueError(f"código deve ser numérico: {valor!r}")
        return codigo


@registrar
class CceeContabilizacaoPerfil(CceeCsvCkan):
    """Contabilização por perfil. CSV por ano, uma linha por perfil e mês."""

    dataset = "contabilizacao_montante_perfil_agente"
    entidade = "contabilizacao_perfil"
    schema = ContabilizacaoPerfil

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_agente": limpar(bruto.get("COD_AGENTE")),
            "codigo_perfil": limpar(bruto.get("COD_PERF_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "cnpj": limpar(bruto.get("CNPJ")),
        }
        for origem, destino in VALORES.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
```

Run: `uv run pytest tests/unit/conectores/test_ccee_contabilizacao_perfil.py -q` → `6 passed`.

- [ ] **Step 4: Bronze**

```sql
-- definitions/bronze/ccee_contabilizacao_perfil.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: resultado da contabilização por perfil de agente (CCEE, dados abertos).
-- Append-only. A CCEE recontabiliza e reescreve o recurso do ano: cada
-- publicação é uma leitura nova, e todas ficam aqui (ADR 016).
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia                        DATE      NOT NULL OPTIONS(description="Primeiro dia do mês de apuração"),
  periodo_apuracao_ccee                  STRING    NOT NULL OPTIONS(description="AAAA-MM, como a CCEE declara"),
  versao_publicacao                      DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN — identificador de versão da ADR 016"),
  codigo_agente                          STRING    NOT NULL,
  codigo_perfil                          STRING    NOT NULL OPTIONS(description="COD_PERF_AGENTE — o perfil é quem transaciona"),
  sigla_perfil                           STRING    NOT NULL,
  nome_empresarial                       STRING    NOT NULL,
  cnpj                                   STRING    NOT NULL OPTIONS(description="14 dígitos"),
  valor_tm_mcp                           NUMERIC            OPTIONS(description="R$"),
  compensacao_mre                        NUMERIC            OPTIONS(description="R$"),
  valor_encargo                          NUMERIC            OPTIONS(description="R$"),
  valor_ajuste_exposicao                 NUMERIC            OPTIONS(description="R$"),
  valor_ajuste_alivio_retroativo         NUMERIC            OPTIONS(description="R$"),
  efeito_contratos_disponibilidade       NUMERIC            OPTIONS(description="R$"),
  efeito_contratos_cota_gf               NUMERIC            OPTIONS(description="R$"),
  efeito_contratos_nuclear               NUMERIC            OPTIONS(description="R$"),
  ajuste_recontab                        NUMERIC            OPTIONS(description="R$ — a recontabilização, quando houve"),
  ajuste_mcsd_ex                         NUMERIC            OPTIONS(description="R$"),
  resultado_financeiro_energia_reserva   NUMERIC            OPTIONS(description="R$"),
  efeito_ccearq                          NUMERIC            OPTIONS(description="R$"),
  efeito_contratos_itaipu                NUMERIC            OPTIONS(description="R$"),
  efeito_repasse_risco_hidrologico       NUMERIC            OPTIONS(description="R$"),
  efeito_deslocamento_pld_cmo            NUMERIC            OPTIONS(description="R$"),
  resultado_final                        NUMERIC            OPTIONS(description="R$ — o número que o perfil liquida"),

  _ingestao_id                           STRING    NOT NULL,
  _ingestao_timestamp                    TIMESTAMP NOT NULL,
  _fonte                                 STRING    NOT NULL,
  _schema_versao                         STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, codigo_perfil
OPTIONS(description="Contabilização por perfil de agente — camada Bronze, append-only, todas as publicações");
```

- [ ] **Step 5: Silver vigente e Silver histórico**

```sql
-- definitions/silver/ccee_contabilizacao_perfil.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee", "codigo_perfil"],
    nonNull: ["data_referencia", "periodo_apuracao_ccee", "versao_publicacao", "codigo_agente", "codigo_perfil", "cnpj"],
    rowConditions: [
      "periodo_apuracao = periodo_apuracao_ccee",
      "LENGTH(cnpj) = 14"
    ]
  }
}

-- Silver vigente (ADR 016, opção B): uma linha por perfil e mês, da publicação
-- mais recente da CCEE. Vence `versao_publicacao`; a hora da leitura só
-- desempata leituras da mesma publicação. O replay de um raw antigo não
-- rebaixa a vigente, porque a ordem vem da fonte.
--
-- `agente_ccee` é nulo de propósito: a origem traz o código do agente, não a
-- sigla. A sigla entra na Gold pela junção com `gold.agentes_ccee`.
-- Sem faixa em valor: resultado financeiro é positivo ou negativo por natureza.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,    -- o resultado é do perfil, não do submercado
  CAST(NULL AS STRING) AS codigo_usina,  -- idem
  CAST(NULL AS STRING) AS agente_ccee,   -- a origem traz código, não sigla; ver Gold
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  codigo_agente,
  codigo_perfil,
  sigla_perfil,
  nome_empresarial,
  cnpj,
  valor_tm_mcp,
  compensacao_mre,
  valor_encargo,
  valor_ajuste_exposicao,
  valor_ajuste_alivio_retroativo,
  efeito_contratos_disponibilidade,
  efeito_contratos_cota_gf,
  efeito_contratos_nuclear,
  ajuste_recontab,
  ajuste_mcsd_ex,
  resultado_financeiro_energia_reserva,
  efeito_ccearq,
  efeito_contratos_itaipu,
  efeito_repasse_risco_hidrologico,
  efeito_deslocamento_pld_cmo,
  resultado_final,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_contabilizacao_perfil")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee, codigo_perfil
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

```sql
-- definitions/silver/ccee_contabilizacao_perfil_historico.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee", "codigo_perfil", "versao_publicacao"],
    nonNull: ["periodo_apuracao_ccee", "codigo_perfil", "versao_publicacao"]
  }
}

-- Silver de histórico (ADR 016, opção B): uma linha por perfil, mês **e
-- publicação**. Leituras repetidas da mesma publicação colapsam; publicações
-- diferentes ficam lado a lado. É o que responde "qual era o resultado de
-- março antes da recontabilização de junho" sem ler coluna técnica.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,
  CAST(NULL AS STRING) AS codigo_usina,
  CAST(NULL AS STRING) AS agente_ccee,
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  codigo_agente,
  codigo_perfil,
  sigla_perfil,
  cnpj,
  ajuste_recontab,
  resultado_final,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_contabilizacao_perfil")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee, codigo_perfil, versao_publicacao
  ORDER BY _ingestao_timestamp DESC
) = 1
```

- [ ] **Step 6: Gold**

```sql
-- definitions/gold/resultado_contabilizacao_mensal_perfil.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: o resultado financeiro de cada perfil de agente no MCP, mês a mês, com
-- a sigla do agente que a origem não traz — junção com a dimensão
-- `gold.agentes_ccee` por `codigo_perfil`, que é o uso para o qual ela existe.
--
-- LEFT JOIN, não INNER: perfil encerrado sai de `agentes_ccee` (só ATIVO) mas
-- ainda tem resultado no mês; sumir com ele seria lacuna silenciosa.
-- Lê só a Silver vigente (ADR 016). Sem KPI (ADR 012).
SELECT
  c.periodo_apuracao,
  c.versao_publicacao,
  c.codigo_perfil,
  c.sigla_perfil,
  a.agente_ccee,
  c.codigo_agente,
  c.cnpj,
  c.resultado_final                        AS resultado_final_reais,
  c.valor_tm_mcp                           AS mcp_reais,
  c.valor_encargo                          AS encargos_reais,
  c.ajuste_recontab                        AS recontabilizacao_reais,
  c.efeito_repasse_risco_hidrologico       AS risco_hidrologico_reais,
  c.resultado_financeiro_energia_reserva   AS energia_reserva_reais
FROM ${ref("silver", "ccee_contabilizacao_perfil")} AS c
LEFT JOIN ${ref("gold", "agentes_ccee")} AS a
  ON a.codigo_perfil = c.codigo_perfil
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde, incluindo o novo `test_view_de_historico_tem_bronze_e_silver_vigente`. Se `test_view_referencia_a_camada_anterior` reclamar da Gold, é porque ela procura `.silver.` entre as tabelas — está lá (`c`); o `.gold.` adicional não invalida.

- [ ] **Step 7: ADR 016 passa a aceita**

Em `docs/arquitetura/decisoes/016-versionamento-de-recontabilizacao.md`, linha 3, `**Status**: proposto` → `**Status**: aceito · **Aceita em**: 2026-09-XX (data desta tarefa)`. Ao fim da seção "O que falta para decidir", acrescente:

```markdown
**Decidido com o dado na mão.** A primeira fonte da CCEE com recontabilização
declarada é `contabilizacao_montante_perfil_agente` (Silver
`ccee_contabilizacao_perfil`). O arquivo **não** traz número de versão; o
metadado traz: o `last_modified` do recurso no CKAN, que muda quando a CCEE
reescreve o ano. É o item 2 da ordem de preferência, e vira a coluna
`versao_publicacao` em toda entidade mensal da CCEE — registrado em
[`ccee_contabilizacao_perfil.md`](../../dicionario-dados/ccee_contabilizacao_perfil.md).
A opção B está implementada: Silver vigente ordena por `versao_publicacao`;
`silver.ccee_contabilizacao_perfil_historico` guarda uma linha por chave e
versão. O Balanço Energético (MySQL RDS) segue por decidir quando houver acesso.
```

- [ ] **Step 8: Agendamento, alerta, domínio, dicionário**

Scheduler (depois de `ccee_exposicao_financeira`):

```hcl
    ccee_contabilizacao_perfil = {
      # 43 MB por ano, ~47 mil perfis por mês. A janela de 120 dias lê o ano
      # corrente inteiro (o arquivo é anual), o que é o custo de ver a
      # recontabilização (ADR 016).
      cron         = "0 10 6 * *"
      ultimos_dias = 120
    }
```

Monitoramento: `ccee_contabilizacao_perfil = 780`. Portal: `"ccee_contabilizacao_perfil": "Risco e Compliance",`.

`docs/dicionario-dados/ccee_contabilizacao_perfil.md` — as seções do dicionário da Task 2, com:

- cabeçalho: dataset `contabilizacao_montante_perfil_agente`; recursos `_2024`…`_2026`; natureza **série mensal por perfil, com recontabilização**; volume 329.080 linhas / 43 MB em 2026; encoding misto; dono Letícia Ferreira — Risco e Compliance (B1);
- uma seção **"Versão — a ADR 016 na prática"**: `versao_publicacao` = `last_modified` do recurso; o que a Silver vigente faz; o que a `_historico` responde; que o `_2025` foi reescrito em 02/02/2026 (evidência de que a republicação é do ano inteiro);
- Campos: as 6 colunas de identificação e as 16 de valor, com o nome do lake conforme `VALORES`; todas as de valor `NUMERIC` nulas quando vazias, e a tabela de **frequência de vazio** lida em 14/09 (`COMPENSACAO_MRE` 98%, `AJUSTE_MCSD_EX` e `EFEITO_CCEARQ` ~100%, `VALOR_TM_MCP` 43%, `EFEITO_CONTRAT_DISP` 14%, `AJUSTE_RECONTAB` 2%);
- Dimensões comuns: `agente_ccee` **não** na Silver (a origem traz código), com o motivo e o caminho pela Gold;
- Deduplicação: chave (`periodo_apuracao_ccee`, `codigo_perfil`); histórico com `versao_publicacao` na chave;
- Gold: `resultado_contabilizacao_mensal_perfil`, LEFT JOIN com `agentes_ccee` e o porquê;
- Qualidade: significado de cada componente **não documentado no catálogo da CCEE** — nomes do lake ficam próximos da origem; dúvida vai ao dono do domínio (B3);
- Linhagem: `…_{ano}.csv → raw/ccee/contabilizacao_perfil → bronze → silver (vigente e _historico) → gold`.

README: `| CCEE — contabilização por perfil | [`ccee_contabilizacao_perfil.md`](ccee_contabilizacao_perfil.md) | 1 | — | `resultado_contabilizacao_mensal_perfil` |`.

- [ ] **Step 9: Dry-run real, suíte, commit**

Run: `uv run python -m src.cli ingerir ccee_contabilizacao_perfil --de 2026-06-01 --ate 2026-07-31 --dry-run`
Expected: `SUCESSO`, ~94.700 extraídos (dois meses × ~47.300), 0 inválidos. **Anote a duração**: é a primeira entidade com dezenas de milhares de linhas por mês, e o tempo aqui calibra o `timeout` do Cloud Run Job (1800 s) para a Task 5.

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_contabilizacao_perfil.py definitions/bronze/ccee_contabilizacao_perfil.sqlx definitions/silver/ccee_contabilizacao_perfil.sqlx definitions/silver/ccee_contabilizacao_perfil_historico.sqlx definitions/gold/resultado_contabilizacao_mensal_perfil.sqlx tests/unit/conectores/test_ccee_contabilizacao_perfil.py tests/unit/test_sql.py tests/fixtures/ccee_contabilizacao_perfil_2026.csv docs/dicionario-dados/ccee_contabilizacao_perfil.md docs/dicionario-dados/README.md docs/arquitetura/decisoes/016-versionamento-de-recontabilizacao.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): contabilizacao por perfil, e a ADR 016 passa a aceita

Uma linha por perfil de agente e mes, com os 16 componentes do resultado no
MCP e o RESULTADO_FINAL. ~47 mil perfis por mes, 43 MB por ano.

E a fonte que a ADR 016 esperava para decidir. A recontabilizacao esta no dado
(AJUSTE_RECONTAB) e a CCEE reescreve o recurso do ano ao republicar -- o de
2025 foi reescrito em 02/02/2026. O arquivo nao traz versao; o metadado traz:
last_modified do recurso no CKAN. Vira versao_publicacao, a Silver vigente
ordena por ele, e a Silver _historico guarda uma linha por chave e versao.
Replay de raw antigo deixa de rebaixar a vigente.

agente_ccee fica nulo na Silver de proposito: a origem traz o codigo do
agente, nao a sigla. A Gold junta com agentes_ccee por codigo_perfil -- o uso
para o qual aquela dimensao foi escrita. LEFT JOIN, porque perfil encerrado
ainda tem resultado no mes.

Vazio vira NULL, nunca zero: COMPENSACAO_MRE esta vazio em 98% das linhas e
zero em nenhuma delas.

Dry-run contra a API real: <N> registros em junho e julho, 0 invalidos, <T>s.
```

---
### Task 5: `ccee_geracao_usina` — geração horária por usina, na granularidade do A7 (ordem 3)

**Files:**
- Create: `src/conectores/ccee_geracao_usina.py`
- Create: `definitions/bronze/ccee_geracao_usina.sqlx`
- Create: `definitions/silver/ccee_geracao_usina.sqlx`
- Create: `definitions/gold/geracao_mensal_usina.sqlx`
- Test: `tests/unit/conectores/test_ccee_geracao_usina.py`
- Create: `tests/fixtures/ccee_geracao_usina_202607.csv`
- Create: `docs/dicionario-dados/ccee_geracao_usina.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan` com `recurso_por = "mes"`; `_data_e_hora` e `SIGLA_SUBMERCADO` de `src.conectores.ccee_pld` (reuso: mesma regra de período dentro do mês).
- Produces: `silver.ccee_geracao_usina` (grão hora × parcela de usina); `gold.geracao_mensal_usina`.

**O dado, lido em 14/09.** Dataset `geracao_horaria_usina`, **29 recursos mensais** `_202403`…`_202607`, cada um **gzip** (`format: GZIP`, `Content-Type: application/x-gzip` sem `Content-Encoding`). O de julho/2026: 61 MB comprimidos, 2.964.096 linhas, 3.984 parcelas de usina, 31 dias, `PERIODO_COMERCIALIZACAO` de 1 a 744 (**índice da hora dentro do mês**, como no PLD) e `DATA` explícita em `dd/mm/aaaa`. `(DATA, PERIODO_COMERCIALIZACAO, CODIGO_PARCELA_USINA)` único. 36 colunas; preenchimento: 11 sempre (`MES_REFERENCIA`, `DATA`, `PERIODO_COMERCIALIZACAO`, `CODIGO_PARCELA_USINA`, `SIGLA_USINA`, `FONTE_PRIMARIA`, `SUBMERCADO`, `TIPO_USINA`, `GERACAO_CENTRO_GRAVIDADE`, `FATOR_PERDA_INTERNA`, `FATOR_RATEIO_PERDA_GERACAO`), 4 em 21,6% (as de garantia física e deslocamento hidráulico — só hidráulicas MRE), `INDISPONIBILIDADE_UTE_ORDEM_MERITO_ECONOMICO` em 70%, e as outras 20 entre 0% e 4,4% (só usinas com CVU). `SUBMERCADO` por extenso; `TIPO_USINA` ∈ {Hidráulicas MRE, Hidráulicas não MRE, Usinas com CVU, Biomassa, Eólicas, Demais usinas}.

**Duas decisões que o volume impõe.**
1. **Bronze guarda as 36 colunas**, as 25 raras como `NUMERIC` nulo. Coluna nula custa quase nada no armazenamento colunar do BigQuery; escolher "as importantes" agora seria adivinhar o que o dono do domínio quer, e reler 29 recursos de 61 MB para acrescentar uma coluna depois custa mais.
2. **`codigo_usina` fica nulo.** `CODIGO_PARCELA_USINA` é o código interno da CCEE, **não** o CEG que o `aneel_siga` usa na dimensão comum. Preencher exige o de-para da Lacuna 1 ([#141](https://github.com/nessenergy/Alupdatalake/issues/141)). A Silver guarda `codigo_parcela_usina` e `sigla_usina` para o dia em que ele chegar.

**Risco nomeado: tempo de execução.** ~3 milhões de registros validados um a um pelo Pydantic por mês. O dry-run do Step 9 mede; se passar de 20 minutos por mês, o `timeout` do Cloud Run Job (1800 s em `infra/modules/scheduler/main.tf`) precisa subir para esta entidade, e o agendamento passa a `ultimos_dias = 35` (um recurso por execução). A Task 4 já terá dado a primeira medida de escala.

- [ ] **Step 1: Fixture sintética e teste (falha)**

`tests/fixtures/ccee_geracao_usina_202607.csv` — 36 colunas na ordem do arquivo real; três usinas, duas horas, e a virada do dia (período 25 = 02/07 00h):

```csv
MES_REFERENCIA;DATA;PERIODO_COMERCIALIZACAO;CODIGO_PARCELA_USINA;SIGLA_USINA;FONTE_PRIMARIA;SUBMERCADO;TIPO_USINA;GERACAO_CENTRO_GRAVIDADE;FATOR_PERDA_INTERNA;FATOR_RATEIO_PERDA_GERACAO;GERACAO_SEGURANCA_ENERGETICA;GERACAO_RESTRICAO_OPERATIVA_CONST_ON;ENERGIA_AJUSTADA_ENCARGO_RESTRICAO_OPERATIVA;INDISPONIBILIDADE_UTE_ORDEM_MERITO_ECONOMICO;CUSTO_DECLARADO_PARCELA_USINA;FATOR_DESLOCAMENTO_HIDRAULICO;GERACAO_VERIFICADA_ONS;DISPONIBILIDADE_VERIFICADA_UG;GERACAO_INFLEXIVEL;GERACAO_SUBSTITUTA_COMPENSACAO_INDISPONIBILIDADE;DESPACHO_RESTRICAO_ENERGETICA_EX_ANTE;DESPACHO_PAGAMENTO_ENCARGO_RESTRICAO_OPERACAO;GERACAO_FORA_ORDEM_MERITO;DESPACHO_ORDEM_MERITO_DECK_ONS;DESPACHO_ORDEM_MERITO_PRECO;DESPACHO_ORDEM_MERITO;GERACAO_RESERVA_POTENCIA;PRECO_ENCARGO_RESERVA_POTENCIA;GERACAO_UNIT_COMMITMENT;GERACAO_FINAL_ORDEM_MERITO;DESLOCAMENTO_HIDRAULICO_ENERGETICO_PRELIMINAR;GARANTIA_FISICA_AJUSTADA_FATOR_DISPONIBILIDADE;GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_2;GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_3;FATOR_RISCO_HIDROLOGICO
202607;01/07/2026;001;201;UHE ALFA;Hidráulica;SUDESTE;Hidráulicas MRE;22.702357;0.97539742866;0.97632522359;;;;;;;;;;;;;;;;;;;;;0;121.172201;126.399655;93.409465;
202607;01/07/2026;001;302;EOL BETA;Eólica;NORDESTE;Eólicas;15.5;1;1;;;;;;;;;;;;;;;;;;;;;;;;;
202607;01/07/2026;001;403;UTE GAMA;Gás natural;SUL;Usinas com CVU;0;1;1;;;;0;350.75;;0;;0;0;;;0;;;0;;;;0;;;;;
202607;01/07/2026;002;201;UHE ALFA;Hidráulica;SUDESTE;Hidráulicas MRE;23.1;0.97539742866;0.97632522359;;;;;;;;;;;;;;;;;;;;;0;121.172201;126.399655;93.409465;
202607;02/07/2026;025;201;UHE ALFA;Hidráulica;SUDESTE;Hidráulicas MRE;20.0;0.97539742866;0.97632522359;;;;;;;;;;;;;;;;;;;;;0;121.172201;126.399655;93.409465;
202607;01/07/2026;002;302;EOL BETA;Eólica;NORDESTE;Eólicas;;1;1;;;;;;;;;;;;;;;;;;;;;;;;;
```

(A última linha tem `GERACAO_CENTRO_GRAVIDADE` vazio de propósito: é obrigatório, e o registro deve ser **rejeitado**, não zerado.)

```python
# tests/unit/conectores/test_ccee_geracao_usina.py
"""Conector CCEE/geração horária por usina — gzip mensal, período dentro do mês, sem rede.

O que estes testes protegem, lido do arquivo real de julho/2026 em 14/09:

- o recurso é mensal (`_202607`) e gzip: a base descomprime em fluxo;
- `PERIODO_COMERCIALIZACAO` é o índice da hora **no mês** (1..744), como no
  PLD, e `DATA` vem explícita — os dois têm de concordar, e a Silver exige isso;
- `CODIGO_PARCELA_USINA` não é CEG: `codigo_usina` fica nulo até o de-para
  (#141);
- geração vazia é registro inválido, não zero.
"""

from __future__ import annotations

import gzip
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_geracao_usina import CceeGeracaoUsina, GeracaoHorariaUsina
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_geracao_usina_202607.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeGeracaoUsina()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "geracao_horaria_usina_202607", "url": "u", "format": "GZIP", "last_modified": "2026-09-01T10:00:00"}]},
    )
    # A fixture é texto; o conector recebe gzip, como na origem.
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(gzip.compress(FIXTURE.read_bytes())))
    return conector


def test_recurso_e_mensal():
    assert CceeGeracaoUsina.recurso_por == "mes"


def test_extrai_o_mes_do_recurso_gzip(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert len(registros) == 6
    assert registros[0]["_sufixo"] == "202607"


def test_transformar_deriva_hora_do_periodo_e_converte_submercado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = GeracaoHorariaUsina.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.hora == 0
    assert registro.periodo_comercializacao == 1
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.codigo_parcela_usina == "201"
    assert registro.sigla_usina == "UHE ALFA"
    assert registro.submercado == "SE"  # SUDESTE por extenso vira sigla
    assert registro.tipo_usina == "Hidráulicas MRE"
    assert registro.geracao_centro_gravidade == Decimal("22.702357")
    assert registro.garantia_fisica_rrh_modulada_ajustada_2 == Decimal("126.399655")
    assert registro.custo_declarado_parcela_usina is None


def test_periodo_25_e_a_hora_zero_do_dia_dois(conector):
    registros = [GeracaoHorariaUsina.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")) if b["PERIODO_COMERCIALIZACAO"] == "025"]

    assert registros[0].data_referencia == date(2026, 7, 2)
    assert registros[0].hora == 0


def test_data_que_nao_bate_com_o_periodo_e_rejeitada(conector):
    """A CCEE publica os dois; se discordarem, a origem mudou a regra — não escolhemos por ela."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    bruto = bruto | {"DATA": "15/07/2026"}  # período 1 é dia 1, não 15

    with pytest.raises(ValueError, match="DATA .* período"):
        GeracaoHorariaUsina.model_validate(conector.transformar(bruto))


def test_geracao_vazia_e_registro_invalido_nao_zero(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-07-31"))

    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 1  # a EOL BETA sem geração
    assert execucao.status == "SUCESSO"


def test_tipo_de_usina_desconhecido_e_rejeitado():
    with pytest.raises(ValueError):
        GeracaoHorariaUsina.model_validate(
            {
                "data_referencia": "2026-07-01",
                "hora": 0,
                "periodo_comercializacao": 1,
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_parcela_usina": "1",
                "sigla_usina": "X",
                "fonte_primaria": "X",
                "submercado": "SE",
                "tipo_usina": "Nuclear",
                "geracao_centro_gravidade": "1",
                "fator_perda_interna": "1",
                "fator_rateio_perda_geracao": "1",
            }
        )
```

Run: `uv run pytest tests/unit/conectores/test_ccee_geracao_usina.py -q` → `ModuleNotFoundError`.

- [ ] **Step 2: Conector**

```python
# src/conectores/ccee_geracao_usina.py
"""Conector CCEE — geração horária por parcela de usina (Onda 1, público). Ordem 3 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `geracao_horaria_usina`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/geracao_horaria_usina

A maior fonte do lake: ~3 milhões de linhas por mês (3.984 parcelas de usina ×
744 horas), publicadas **por mês e em gzip** — 61 MB comprimidos, ~800 MB de
texto. É a granularidade de usina que o A7 fixa para dado de portfólio.

Três coisas herdadas do PLD e uma diferença:

- `PERIODO_COMERCIALIZACAO` é o índice da hora **no mês** (1..744), e a hora do
  dia sai da mesma aritmética de `ccee_pld._data_e_hora`;
- o submercado vem por extenso e vira a sigla do ONS;
- o recurso é descoberto no CKAN;
- a diferença: aqui **há** coluna `DATA`. O conector deriva o dia do período,
  compara com a `DATA` publicada, e rejeita a linha se discordarem — é a
  origem mudando a regra, e não cabe a nós escolher qual das duas vale.

`CODIGO_PARCELA_USINA` é código interno da CCEE, não o CEG da ANEEL:
`codigo_usina` fica nulo até o de-para da Lacuna 1 (#141).
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee
from src.conectores.ccee_pld import SIGLA_SUBMERCADO, SUBMERCADOS, _data_e_hora
from src.core.registry import registrar

TIPOS_USINA = ("Hidráulicas MRE", "Hidráulicas não MRE", "Usinas com CVU", "Biomassa", "Eólicas", "Demais usinas")

# Coluna da origem → coluna do lake. As três primeiras são obrigatórias; as
# outras 25 são nulas na maior parte das linhas (só hidráulicas MRE e usinas
# com CVU as preenchem) e entram como NUMERIC nulo.
MEDIDAS_OBRIGATORIAS = {
    "GERACAO_CENTRO_GRAVIDADE": "geracao_centro_gravidade",
    "FATOR_PERDA_INTERNA": "fator_perda_interna",
    "FATOR_RATEIO_PERDA_GERACAO": "fator_rateio_perda_geracao",
}
MEDIDAS_OPCIONAIS = {
    "GERACAO_SEGURANCA_ENERGETICA": "geracao_seguranca_energetica",
    "GERACAO_RESTRICAO_OPERATIVA_CONST_ON": "geracao_restricao_operativa_constrained_on",
    "ENERGIA_AJUSTADA_ENCARGO_RESTRICAO_OPERATIVA": "energia_ajustada_encargo_restricao_operativa",
    "INDISPONIBILIDADE_UTE_ORDEM_MERITO_ECONOMICO": "indisponibilidade_ute_ordem_merito",
    "CUSTO_DECLARADO_PARCELA_USINA": "custo_declarado_parcela_usina",
    "FATOR_DESLOCAMENTO_HIDRAULICO": "fator_deslocamento_hidraulico",
    "GERACAO_VERIFICADA_ONS": "geracao_verificada_ons",
    "DISPONIBILIDADE_VERIFICADA_UG": "disponibilidade_verificada_ug",
    "GERACAO_INFLEXIVEL": "geracao_inflexivel",
    "GERACAO_SUBSTITUTA_COMPENSACAO_INDISPONIBILIDADE": "geracao_substituta_compensacao_indisponibilidade",
    "DESPACHO_RESTRICAO_ENERGETICA_EX_ANTE": "despacho_restricao_energetica_ex_ante",
    "DESPACHO_PAGAMENTO_ENCARGO_RESTRICAO_OPERACAO": "despacho_pagamento_encargo_restricao_operacao",
    "GERACAO_FORA_ORDEM_MERITO": "geracao_fora_ordem_merito",
    "DESPACHO_ORDEM_MERITO_DECK_ONS": "despacho_ordem_merito_deck_ons",
    "DESPACHO_ORDEM_MERITO_PRECO": "despacho_ordem_merito_preco",
    "DESPACHO_ORDEM_MERITO": "despacho_ordem_merito",
    "GERACAO_RESERVA_POTENCIA": "geracao_reserva_potencia",
    "PRECO_ENCARGO_RESERVA_POTENCIA": "preco_encargo_reserva_potencia",
    "GERACAO_UNIT_COMMITMENT": "geracao_unit_commitment",
    "GERACAO_FINAL_ORDEM_MERITO": "geracao_final_ordem_merito",
    "DESLOCAMENTO_HIDRAULICO_ENERGETICO_PRELIMINAR": "deslocamento_hidraulico_energetico_preliminar",
    "GARANTIA_FISICA_AJUSTADA_FATOR_DISPONIBILIDADE": "garantia_fisica_ajustada_fator_disponibilidade",
    "GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_2": "garantia_fisica_rrh_modulada_ajustada_2",
    "GARANTIA_FISICA_RRH_MODULADA_AJUSTADA_3": "garantia_fisica_rrh_modulada_ajustada_3",
    "FATOR_RISCO_HIDROLOGICO": "fator_risco_hidrologico",
}


class GeracaoHorariaUsina(BaseModel):
    """A geração de uma parcela de usina em uma hora do mês de apuração."""

    data_referencia: date
    data_publicada: date  # a DATA que a CCEE escreve; tem de bater com a derivada do período
    hora: int = Field(ge=0, le=23)
    periodo_comercializacao: int = Field(ge=1, le=744)
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_parcela_usina: str
    sigla_usina: str
    fonte_primaria: str
    submercado: str
    tipo_usina: Literal[TIPOS_USINA]  # type: ignore[valid-type]
    geracao_centro_gravidade: Decimal
    fator_perda_interna: Decimal
    fator_rateio_perda_geracao: Decimal
    geracao_seguranca_energetica: Decimal | None = None
    geracao_restricao_operativa_constrained_on: Decimal | None = None
    energia_ajustada_encargo_restricao_operativa: Decimal | None = None
    indisponibilidade_ute_ordem_merito: Decimal | None = None
    custo_declarado_parcela_usina: Decimal | None = None
    fator_deslocamento_hidraulico: Decimal | None = None
    geracao_verificada_ons: Decimal | None = None
    disponibilidade_verificada_ug: Decimal | None = None
    geracao_inflexivel: Decimal | None = None
    geracao_substituta_compensacao_indisponibilidade: Decimal | None = None
    despacho_restricao_energetica_ex_ante: Decimal | None = None
    despacho_pagamento_encargo_restricao_operacao: Decimal | None = None
    geracao_fora_ordem_merito: Decimal | None = None
    despacho_ordem_merito_deck_ons: Decimal | None = None
    despacho_ordem_merito_preco: Decimal | None = None
    despacho_ordem_merito: Decimal | None = None
    geracao_reserva_potencia: Decimal | None = None
    preco_encargo_reserva_potencia: Decimal | None = None
    geracao_unit_commitment: Decimal | None = None
    geracao_final_ordem_merito: Decimal | None = None
    deslocamento_hidraulico_energetico_preliminar: Decimal | None = None
    garantia_fisica_ajustada_fator_disponibilidade: Decimal | None = None
    garantia_fisica_rrh_modulada_ajustada_2: Decimal | None = None
    garantia_fisica_rrh_modulada_ajustada_3: Decimal | None = None
    fator_risco_hidrologico: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @model_validator(mode="after")
    def _data_bate_com_o_periodo(self) -> GeracaoHorariaUsina:
        """A CCEE publica DATA e período; se discordarem, a origem mudou a regra."""
        if self.data_publicada != self.data_referencia:
            raise ValueError(
                f"DATA {self.data_publicada} não bate com o período {self.periodo_comercializacao} ({self.data_referencia})"
            )
        return self


@registrar
class CceeGeracaoUsina(CceeCsvCkan):
    """Geração horária por parcela de usina. Gzip por mês; ~3 milhões de linhas cada."""

    dataset = "geracao_horaria_usina"
    entidade = "geracao_usina"
    schema = GeracaoHorariaUsina
    recurso_por = "mes"

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = limpar(bruto["MES_REFERENCIA"])
        periodo = int(limpar(bruto["PERIODO_COMERCIALIZACAO"]))
        dia, hora = _data_e_hora(mes, periodo)
        nome = limpar(bruto.get("SUBMERCADO")).upper()

        registro: dict[str, Any] = {
            "data_referencia": dia,
            # A DATA publicada viaja junto: o schema exige que bata com a derivada,
            # e a discordância vira ValidationError — contada, não fatal.
            "data_publicada": datetime.strptime(limpar(bruto["DATA"]), "%d/%m/%Y").date(),
            "hora": hora,
            "periodo_comercializacao": periodo,
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_parcela_usina": limpar(bruto.get("CODIGO_PARCELA_USINA")),
            "sigla_usina": limpar(bruto.get("SIGLA_USINA")),
            "fonte_primaria": limpar(bruto.get("FONTE_PRIMARIA")),
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "tipo_usina": limpar(bruto.get("TIPO_USINA")),
        }
        for origem, destino in MEDIDAS_OBRIGATORIAS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))  # None → o schema rejeita
        for origem, destino in MEDIDAS_OPCIONAIS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
```

Por que a conferência DATA × período vive no **schema** e não em `transformar()`: o runner (`Conector._validar_e_carregar`) só captura `ValidationError`. Um `ValueError` solto em `transformar()` derrubaria a execução inteira por uma linha; no `model_validator` a linha discordante vira `linhas_invalidas += 1`, com aviso no log, e o mês segue.

Run: `uv run pytest tests/unit/conectores/test_ccee_geracao_usina.py -q` → `7 passed`.

- [ ] **Step 3: Bronze**

```sql
-- definitions/bronze/ccee_geracao_usina.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: geração horária por parcela de usina (CCEE, dados abertos, gzip mensal).
-- ~3 milhões de linhas por mês. As 25 medidas opcionais são nulas na maior
-- parte das linhas (só hidráulicas MRE e usinas com CVU as têm) e custam quase
-- nada no armazenamento colunar; guardá-las evita reler 61 MB por mês depois.
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia                                   DATE      NOT NULL OPTIONS(description="Dia, derivado do período e conferido com a DATA publicada"),
  hora                                              INT64     NOT NULL OPTIONS(description="0 a 23, horário de Brasília"),
  periodo_comercializacao                           INT64     NOT NULL OPTIONS(description="Índice da hora no mês, 1..744, como a CCEE publica"),
  periodo_apuracao_ccee                             STRING    NOT NULL OPTIONS(description="AAAA-MM, como a CCEE declara"),
  versao_publicacao                                 DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN (ADR 016)"),
  data_publicada                                    DATE      NOT NULL OPTIONS(description="A coluna DATA da origem, preservada para rastreio"),
  codigo_parcela_usina                              STRING    NOT NULL OPTIONS(description="Código interno da CCEE — NÃO é o CEG; de-para pendente (#141)"),
  sigla_usina                                       STRING    NOT NULL,
  fonte_primaria                                    STRING    NOT NULL,
  submercado                                        STRING    NOT NULL OPTIONS(description="N, NE, S, SE"),
  tipo_usina                                        STRING    NOT NULL OPTIONS(description="Hidráulicas MRE, Hidráulicas não MRE, Usinas com CVU, Biomassa, Eólicas, Demais usinas"),
  geracao_centro_gravidade                          NUMERIC   NOT NULL OPTIONS(description="Unidade não documentada pela CCEE no catálogo; ver dicionário"),
  fator_perda_interna                               NUMERIC   NOT NULL,
  fator_rateio_perda_geracao                        NUMERIC   NOT NULL,
  geracao_seguranca_energetica                      NUMERIC,
  geracao_restricao_operativa_constrained_on        NUMERIC,
  energia_ajustada_encargo_restricao_operativa      NUMERIC,
  indisponibilidade_ute_ordem_merito                NUMERIC,
  custo_declarado_parcela_usina                     NUMERIC,
  fator_deslocamento_hidraulico                     NUMERIC,
  geracao_verificada_ons                            NUMERIC,
  disponibilidade_verificada_ug                     NUMERIC,
  geracao_inflexivel                                NUMERIC,
  geracao_substituta_compensacao_indisponibilidade  NUMERIC,
  despacho_restricao_energetica_ex_ante             NUMERIC,
  despacho_pagamento_encargo_restricao_operacao     NUMERIC,
  geracao_fora_ordem_merito                         NUMERIC,
  despacho_ordem_merito_deck_ons                    NUMERIC,
  despacho_ordem_merito_preco                       NUMERIC,
  despacho_ordem_merito                             NUMERIC,
  geracao_reserva_potencia                          NUMERIC,
  preco_encargo_reserva_potencia                    NUMERIC,
  geracao_unit_commitment                           NUMERIC,
  geracao_final_ordem_merito                        NUMERIC,
  deslocamento_hidraulico_energetico_preliminar     NUMERIC,
  garantia_fisica_ajustada_fator_disponibilidade    NUMERIC,
  garantia_fisica_rrh_modulada_ajustada_2           NUMERIC,
  garantia_fisica_rrh_modulada_ajustada_3           NUMERIC,
  fator_risco_hidrologico                           NUMERIC,

  _ingestao_id                                      STRING    NOT NULL,
  _ingestao_timestamp                               TIMESTAMP NOT NULL,
  _fonte                                            STRING    NOT NULL,
  _schema_versao                                    STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, codigo_parcela_usina
OPTIONS(description="Geração horária por parcela de usina — camada Bronze, append-only");
```

- [ ] **Step 4: Silver e Gold**

```sql
-- definitions/silver/ccee_geracao_usina.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["data_referencia", "hora", "codigo_parcela_usina"],
    nonNull: ["data_referencia", "hora", "codigo_parcela_usina", "submercado", "geracao_centro_gravidade"],
    rowConditions: [
      "submercado IN ('N','NE','S','SE')",
      "hora BETWEEN 0 AND 23",
      "periodo_apuracao = periodo_apuracao_ccee",
      "data_publicada = data_referencia",
      "geracao_centro_gravidade >= 0"
    ]
  }
}

-- Silver: geração horária por parcela de usina, vigente pela publicação mais
-- recente (ADR 016). `codigo_usina` é nulo: a origem usa código interno da
-- CCEE, não o CEG — Lacuna 1, #141. `codigo_parcela_usina` e `sigla_usina`
-- ficam prontos para o de-para.
-- Faixas (issue #110): geração negativa não existe; DATA e período têm de
-- concordar (a mesma regra do PLD: off-by-one apareceria aqui).
SELECT
  data_referencia,
  submercado,
  CAST(NULL AS STRING) AS codigo_usina,  -- CODIGO_PARCELA_USINA não é CEG; de-para pendente (#141)
  CAST(NULL AS STRING) AS agente_ccee,   -- a usina não é agente; a parcela pertence a um perfil
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  hora,
  periodo_comercializacao,
  data_publicada,
  codigo_parcela_usina,
  sigla_usina,
  fonte_primaria,
  tipo_usina,
  geracao_centro_gravidade,
  fator_perda_interna,
  fator_rateio_perda_geracao,
  geracao_verificada_ons,
  custo_declarado_parcela_usina,
  despacho_ordem_merito,
  garantia_fisica_rrh_modulada_ajustada_2,
  fator_risco_hidrologico,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_geracao_usina")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY data_referencia, hora, codigo_parcela_usina
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

(A Silver expõe as 3 medidas obrigatórias e 5 das opcionais — as que têm preenchimento acima de 2% no arquivo real. As outras 20 ficam na Bronze; se um domínio pedir, entra na Silver com uma linha.)

```sql
-- definitions/gold/geracao_mensal_usina.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: quanto cada parcela de usina gerou no mês, por submercado, fonte e
-- tipo — na granularidade de usina que o A7 fixa para dado de portfólio.
--
-- Soma das horas de `geracao_centro_gravidade`. A unidade não está
-- documentada pela CCEE no catálogo (ver dicionário); o nome da coluna não
-- afirma MWh até que o dono do domínio confirme. Sem KPI (ADR 012).
SELECT
  periodo_apuracao,
  codigo_parcela_usina,
  sigla_usina,
  fonte_primaria,
  tipo_usina,
  submercado,
  COUNT(*)                          AS horas,
  SUM(geracao_centro_gravidade)     AS geracao_centro_gravidade_total,
  AVG(geracao_centro_gravidade)     AS geracao_centro_gravidade_media_horaria,
  MAX(geracao_centro_gravidade)     AS geracao_centro_gravidade_maxima_horaria,
  MAX(versao_publicacao)            AS versao_publicacao
FROM ${ref("silver", "ccee_geracao_usina")}
GROUP BY periodo_apuracao, codigo_parcela_usina, sigla_usina, fonte_primaria, tipo_usina, submercado
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde.

- [ ] **Step 5: Agendamento, alerta, domínio, dicionário**

Scheduler:

```hcl
    ccee_geracao_usina = {
      # Um recurso gzip de 61 MB por mês, ~3 milhões de linhas. Roda de
      # madrugada, um dia depois das entidades mensais leves, com janela que
      # alcança o mês fechado e o anterior (recontabilização, ADR 016).
      cron         = "0 3 7 * *"
      ultimos_dias = 70
    }
```

Monitoramento: `ccee_geracao_usina = 780`. Portal: `"ccee_geracao_usina": "Geração e Operacional",` e em `BYTES_POR_LINHA`: `"ccee_geracao_usina": 420,  # 36 colunas, 25 quase sempre nulas`.

`docs/dicionario-dados/ccee_geracao_usina.md` — seções da Task 2, com:

- cabeçalho: dataset `geracao_horaria_usina`; **29 recursos mensais gzip** `_202403`…`_202607`; natureza série horária por parcela de usina; volume 2.964.096 linhas / 61 MB gz / ~800 MB texto (julho/2026); 3.984 parcelas; dono Taina Mota (usinas do SIN) e Letícia Ferreira (usinas da Alupar) — Geração e Operacional (B1);
- Particularidades: gzip mensal (detectado pelos bytes); `PERIODO_COMERCIALIZACAO` 1..744 no mês, mesma regra do PLD; `DATA` explícita conferida com o período; `CODIGO_PARCELA_USINA` **não é CEG** (Lacuna 1, #141); `TIPO_USINA` com 6 valores; **unidade de `GERACAO_CENTRO_GRAVIDADE` não documentada** no catálogo — a Gold não afirma MWh;
- Campos: as 36 colunas com o nome do lake conforme `MEDIDAS_OBRIGATORIAS` e `MEDIDAS_OPCIONAIS`, e a **frequência de preenchimento** lida em 14/09 (11 sempre; 4 em 21,6%; `INDISPONIBILIDADE…` em 70%; as demais ≤ 4,4%); quais 8 medidas a Silver expõe e por quê;
- Dimensões comuns: `submercado` sim; `codigo_usina` **não** (motivo); `agente_ccee` não;
- Deduplicação: (`data_referencia`, `hora`, `codigo_parcela_usina`), vence `versao_publicacao`;
- Gold: `geracao_mensal_usina`;
- Qualidade: volume e tempo de execução medidos no Step 6; o `timeout` do job; o que fazer se a CCEE republicar um mês (a janela de 70 dias pega);
- Linhagem: `geracao_horaria_usina_{AAAAMM}.gz → raw/ccee/geracao_usina → bronze → silver → gold.geracao_mensal_usina`.

README: `| CCEE — geração horária por usina | [`ccee_geracao_usina.md`](ccee_geracao_usina.md) | 1 | `submercado` | `geracao_mensal_usina` |`.

- [ ] **Step 6: Dry-run real — e a medida de tempo**

Run: `uv run python -m src.cli ingerir ccee_geracao_usina --de 2026-07-01 --ate 2026-07-31 --dry-run`
Expected: `SUCESSO`, 2.964.096 extraídos, 0 inválidos. **Anote a duração do log** (`… carregados em Xs`). Se X > 1200, edite em `infra/modules/scheduler/main.tf` o `timeout` do `google_cloud_run_v2_job` — hoje fixo em `"1800s"` para todos — para ler de `each.value` com default: acrescente `timeout_s = optional(number, 1800)` ao `object({...})` da variável, `timeout = "${each.value.timeout_s}s"` no recurso, e `timeout_s = 3600` nesta entidade. `uv run pytest tests/unit/test_infra.py -q` precisa continuar verde; se um teste fixar `"1800s"`, ajuste-o para aceitar a interpolação. Registre a medida no dicionário.

- [ ] **Step 7: Suíte, lint, commit**

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_geracao_usina.py definitions/bronze/ccee_geracao_usina.sqlx definitions/silver/ccee_geracao_usina.sqlx definitions/gold/geracao_mensal_usina.sqlx tests/unit/conectores/test_ccee_geracao_usina.py tests/fixtures/ccee_geracao_usina_202607.csv docs/dicionario-dados/ccee_geracao_usina.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): geracao horaria por usina -- a granularidade que o A7 pede

A maior fonte do lake: ~3 milhoes de linhas por mes, 3.984 parcelas de usina
vezes 744 horas, publicadas por mes e em gzip (61 MB comprimidos, ~800 MB de
texto). A base le em fluxo; nada disso cabe em memoria.

Herda do PLD a regra do periodo dentro do mes e a sigla de submercado. A
diferenca: aqui ha coluna DATA, e o schema exige que ela bata com o dia
derivado do periodo -- se discordarem, a origem mudou a regra, e nao cabe a
nos escolher qual vale.

codigo_usina fica nulo de proposito: CODIGO_PARCELA_USINA e codigo interno da
CCEE, nao o CEG. E a Lacuna 1 (#141) aparecendo no dado. A Silver guarda o
codigo e a sigla para o dia do de-para.

Bronze guarda as 36 colunas; 25 sao nulas na maior parte das linhas e custam
quase nada. A unidade de GERACAO_CENTRO_GRAVIDADE nao esta documentada no
catalogo: a Gold soma sem afirmar MWh.

Dry-run contra a API real: 2.964.096 registros de julho, 0 invalidos, <T>s.
```

---
### Task 6: `ccee_contrato_montante` — compra e venda contratadas por perfil (ordem 4)

**Files:**
- Create: `src/conectores/ccee_contrato_montante.py`
- Create: `definitions/bronze/ccee_contrato_montante.sqlx`
- Create: `definitions/silver/ccee_contrato_montante.sqlx`
- Create: `definitions/gold/posicao_contratual_mensal_perfil.sqlx`
- Test: `tests/unit/conectores/test_ccee_contrato_montante.py`
- Create: `tests/fixtures/ccee_contrato_montante_2026.csv`
- Create: `docs/dicionario-dados/ccee_contrato_montante.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan`, `limpar`, `numero_ou_nulo`, `primeiro_dia`, `periodo_ccee`; `gold.agentes_ccee` na Gold.
- Produces: `silver.ccee_contrato_montante`; `gold.posicao_contratual_mensal_perfil`.

**O dado, lido em 14/09.** Dataset `contrato_montante_compra_venda_perfil_agente`, recursos `_2024`…`_2026`. 183.893 linhas em 2026 (jan–jul), 18,5 MB. `(MES_REFERENCIA, CODIGO_PERFIL_AGENTE)` único. Colunas: `MES_REFERENCIA`, `CODIGO_AGENTE`, `NOME_EMPRESARIAL`, `CODIGO_PERFIL_AGENTE`, `SIGLA_PERFIL_AGENTE`, `CNPJ`, `CONTRATACAO_VENDA`, `CONTRATACAO_COMPRA`. **Atenção aos nomes**: aqui é `CODIGO_AGENTE` e `CODIGO_PERFIL_AGENTE` (a contabilização usa `COD_AGENTE` e `COD_PERF_AGENTE`). Vazios: `CONTRATACAO_VENDA` em 80% (a maioria dos perfis só compra), `CONTRATACAO_COMPRA` em 8,5%. Valores com até 14 casas decimais (`766.21345206586`) — a **unidade não está documentada no catálogo**; pela ordem de grandeza é energia (MWmed ou MWh), não R$. A Gold não afirma unidade.

É a **via pública de Comercial e Contratos** (ADR 021, §4): a visão que a Câmara tem da Alupar, não o book interno, que segue preso ao A7.

- [ ] **Step 1: Fixture e teste (falha)**

`tests/fixtures/ccee_contrato_montante_2026.csv`:

```csv
MES_REFERENCIA;CODIGO_AGENTE;NOME_EMPRESARIAL;CODIGO_PERFIL_AGENTE;SIGLA_PERFIL_AGENTE;CNPJ;CONTRATACAO_VENDA;CONTRATACAO_COMPRA
202607;100;ALFA DISTRIBUIÇÃO S.A.;83729;ALFA DIST;11111111000111;18.12572811828;766.21345206586
202607;100;ALFA DISTRIBUIÇÃO S.A.;100;ALFA SUL;11111111000111;15.603337365591;780.03478886828
202607;300;GAMA INDÚSTRIA LTDA;300;GAMA CL;33333333000133;;12.5
202606;100;ALFA DISTRIBUIÇÃO S.A.;100;ALFA SUL;11111111000111;10;700
```

```python
# tests/unit/conectores/test_ccee_contrato_montante.py
"""Conector CCEE/contrato montante — compra e venda por perfil, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_contrato_montante import CceeContratoMontante, ContratoMontante
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_contrato_montante_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeContratoMontante()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "contrato_montante_compra_venda_perfil_agente_2026", "url": "u", "last_modified": "2026-09-01T14:00:00"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_extrai_o_mes(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert [r["CODIGO_PERFIL_AGENTE"] for r in registros] == ["83729", "100", "300"]


def test_transformar_le_os_nomes_de_coluna_desta_fonte(conector):
    """Aqui é CODIGO_AGENTE / CODIGO_PERFIL_AGENTE, não COD_AGENTE / COD_PERF_AGENTE."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ContratoMontante.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.codigo_agente == "100"
    assert registro.codigo_perfil == "83729"
    assert registro.sigla_perfil == "ALFA DIST"
    assert registro.contratacao_venda == Decimal("18.12572811828")
    assert registro.contratacao_compra == Decimal("766.21345206586")


def test_venda_vazia_vira_nulo(conector):
    registros = {r["CODIGO_PERFIL_AGENTE"]: r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))}
    gama = ContratoMontante.model_validate(conector.transformar(registros["300"]))

    assert gama.contratacao_venda is None
    assert gama.contratacao_compra == Decimal("12.5")


def test_montante_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        ContratoMontante.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_agente": "1",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "cnpj": "11111111000111",
                "contratacao_compra": "-1",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
```

Run: `uv run pytest tests/unit/conectores/test_ccee_contrato_montante.py -q` → `ModuleNotFoundError`.

- [ ] **Step 2: Conector**

```python
# src/conectores/ccee_contrato_montante.py
"""Conector CCEE — montantes contratados de compra e venda por perfil (Onda 1, público). Ordem 4 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `contrato_montante_compra_venda_perfil_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/contrato_montante_compra_venda_perfil_agente

Uma linha por perfil e mês: quanto o perfil vendeu e quanto comprou em
contratos registrados na CCEE. É a via pública de Comercial e Contratos — a
visão que a Câmara tem de cada agente, não o book interno (esse segue preso ao
A7). 80% dos perfis só compram: `CONTRATACAO_VENDA` vazia é o normal, e vira
nulo.

Os nomes de coluna diferem da contabilização: `CODIGO_AGENTE` e
`CODIGO_PERFIL_AGENTE`, não `COD_*`. A unidade dos montantes não está
documentada no catálogo; a Gold não afirma MWmed nem MWh.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


class ContratoMontante(BaseModel):
    """Os montantes contratados de um perfil de agente em um mês."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_agente: str
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    cnpj: str
    contratacao_venda: Decimal | None = Field(default=None, ge=0)
    contratacao_compra: Decimal | None = Field(default=None, ge=0)

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos


@registrar
class CceeContratoMontante(CceeCsvCkan):
    """Montantes de compra e venda por perfil. CSV por ano, uma linha por perfil e mês."""

    dataset = "contrato_montante_compra_venda_perfil_agente"
    entidade = "contrato_montante"
    schema = ContratoMontante

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_agente": limpar(bruto.get("CODIGO_AGENTE")),
            "codigo_perfil": limpar(bruto.get("CODIGO_PERFIL_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "cnpj": limpar(bruto.get("CNPJ")),
            "contratacao_venda": numero_ou_nulo(bruto.get("CONTRATACAO_VENDA")),
            "contratacao_compra": numero_ou_nulo(bruto.get("CONTRATACAO_COMPRA")),
        }
```

Run: `uv run pytest tests/unit/conectores/test_ccee_contrato_montante.py -q` → `5 passed`.

- [ ] **Step 3: Bronze, Silver, Gold**

```sql
-- definitions/bronze/ccee_contrato_montante.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: montantes contratados de compra e venda por perfil (CCEE, dados abertos).
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia        DATE      NOT NULL OPTIONS(description="Primeiro dia do mês de referência"),
  periodo_apuracao_ccee  STRING    NOT NULL OPTIONS(description="AAAA-MM, como a CCEE declara"),
  versao_publicacao      DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN (ADR 016)"),
  codigo_agente          STRING    NOT NULL,
  codigo_perfil          STRING    NOT NULL,
  sigla_perfil           STRING    NOT NULL,
  nome_empresarial       STRING    NOT NULL,
  cnpj                   STRING    NOT NULL,
  contratacao_venda      NUMERIC            OPTIONS(description="Montante vendido; unidade não documentada pela CCEE — ver dicionário"),
  contratacao_compra     NUMERIC            OPTIONS(description="Montante comprado; idem"),

  _ingestao_id           STRING    NOT NULL,
  _ingestao_timestamp    TIMESTAMP NOT NULL,
  _fonte                 STRING    NOT NULL,
  _schema_versao         STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, codigo_perfil
OPTIONS(description="Montantes contratados por perfil — camada Bronze, append-only");
```

```sql
-- definitions/silver/ccee_contrato_montante.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee", "codigo_perfil"],
    nonNull: ["data_referencia", "periodo_apuracao_ccee", "versao_publicacao", "codigo_perfil", "cnpj"],
    rowConditions: [
      "periodo_apuracao = periodo_apuracao_ccee",
      "contratacao_venda IS NULL OR contratacao_venda >= 0",
      "contratacao_compra IS NULL OR contratacao_compra >= 0"
    ]
  }
}

-- Silver: uma linha por perfil e mês, pela publicação mais recente (ADR 016).
-- `agente_ccee` nulo pelo mesmo motivo da contabilização: a origem traz
-- código, e a sigla entra na Gold por `gold.agentes_ccee`.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,    -- o contrato é do perfil; o submercado está em ccee_perfil
  CAST(NULL AS STRING) AS codigo_usina,  -- não é dado de ativo
  CAST(NULL AS STRING) AS agente_ccee,   -- código na origem, sigla na Gold
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  codigo_agente,
  codigo_perfil,
  sigla_perfil,
  nome_empresarial,
  cnpj,
  contratacao_venda,
  contratacao_compra,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_contrato_montante")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee, codigo_perfil
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

```sql
-- definitions/gold/posicao_contratual_mensal_perfil.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: o que cada perfil comprou e vendeu em contrato, mês a mês, e o saldo —
-- a posição contratual como a CCEE a enxerga. É a via pública de Comercial e
-- Contratos (ADR 021 §4): não substitui o book interno, e o dicionário diz
-- onde os dois divergem por natureza.
--
-- `saldo` é compra menos venda, aritmética de leitura, sem unidade afirmada.
-- LEFT JOIN com a dimensão de agente pela mesma razão da contabilização.
SELECT
  c.periodo_apuracao,
  c.versao_publicacao,
  c.codigo_perfil,
  c.sigla_perfil,
  a.agente_ccee,
  a.submercado,
  c.cnpj,
  c.contratacao_compra,
  c.contratacao_venda,
  COALESCE(c.contratacao_compra, 0) - COALESCE(c.contratacao_venda, 0) AS saldo_compra_menos_venda
FROM ${ref("silver", "ccee_contrato_montante")} AS c
LEFT JOIN ${ref("gold", "agentes_ccee")} AS a
  ON a.codigo_perfil = c.codigo_perfil
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde.

- [ ] **Step 4: Agendamento, alerta, domínio, dicionário**

Scheduler: bloco `ccee_contrato_montante` com `cron = "0 10 6 * *"` e `ultimos_dias = 120` (mesmo comentário das entidades mensais: recontabilização, ADR 016). Monitoramento: `ccee_contrato_montante = 780`. Portal: `"ccee_contrato_montante": "Comercial e Contratos",`.

`docs/dicionario-dados/ccee_contrato_montante.md` — seções da Task 2, com: dataset e recursos `_2024`…`_2026`; natureza série mensal por perfil; volume 183.893 linhas / 18,5 MB em 2026; encoding com 1.052 linhas ISO-8859-1; dono Letícia Ferreira (book) e Tahigo Santos (varejo) — Comercial e Contratos (B1); os **nomes de coluna diferentes** da contabilização; Campos (8, com `CONTRATACAO_*` `NUMERIC` nulos e **unidade não documentada**); vazios (`VENDA` 80%, `COMPRA` 8,5%) e o que significam (perfil que só compra); Dimensões comuns (só data e períodos; `agente_ccee` via Gold); Deduplicação (`periodo_apuracao_ccee`, `codigo_perfil`); Gold `posicao_contratual_mensal_perfil`, com a seção **"O que este dado não é"**: não é o book interno — o book tem preço, contraparte e vigência; isto tem só montante mensal agregado por perfil; Linhagem.

README: `| CCEE — montantes contratados por perfil | [`ccee_contrato_montante.md`](ccee_contrato_montante.md) | 1 | — | `posicao_contratual_mensal_perfil` |`.

- [ ] **Step 5: Dry-run real, suíte, commit**

Run: `uv run python -m src.cli ingerir ccee_contrato_montante --de 2026-06-01 --ate 2026-07-31 --dry-run`
Expected: `SUCESSO`, ~52.500 extraídos, 0 inválidos.

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_contrato_montante.py definitions/bronze/ccee_contrato_montante.sqlx definitions/silver/ccee_contrato_montante.sqlx definitions/gold/posicao_contratual_mensal_perfil.sqlx tests/unit/conectores/test_ccee_contrato_montante.py tests/fixtures/ccee_contrato_montante_2026.csv docs/dicionario-dados/ccee_contrato_montante.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): montantes contratados por perfil -- a via publica de Comercial e Contratos

Uma linha por perfil e mes: quanto vendeu e quanto comprou em contrato
registrado na CCEE. E a visao que a Camara tem de cada agente, nao o book
interno -- esse segue preso ao A7. Nao substitui; muda a frase "o dominio de
maior valor esta 100% parado esperando credencial".

80% dos perfis so compram: CONTRATACAO_VENDA vazia e o normal, e vira nulo.
Os nomes de coluna diferem da contabilizacao (CODIGO_* em vez de COD_*), e o
teste do transformar existe por isso.

A unidade dos montantes nao esta documentada no catalogo. A Gold calcula o
saldo compra menos venda sem afirmar MWmed nem MWh; quem afirma e o dono do
dominio.

Dry-run contra a API real: <N> registros em junho e julho, 0 invalidos.
```

---

### Task 7: `ccee_varejista_consumidor` — o consumo das cargas de varejo (ordem 4, subtema do Tahigo)

**Files:**
- Create: `src/conectores/ccee_varejista_consumidor.py`
- Create: `definitions/bronze/ccee_varejista_consumidor.sqlx`
- Create: `definitions/silver/ccee_varejista_consumidor.sqlx`
- Create: `definitions/gold/consumo_varejista_mensal_uf.sqlx`
- Test: `tests/unit/conectores/test_ccee_varejista_consumidor.py`
- Create: `tests/fixtures/ccee_varejista_consumidor_2026.csv`
- Create: `docs/dicionario-dados/ccee_varejista_consumidor.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan`, `limpar`, `numero_ou_nulo`, `primeiro_dia`, `periodo_ccee`; `SIGLA_SUBMERCADO`, `SUBMERCADOS` de `ccee_pld`.
- Produces: `silver.ccee_varejista_consumidor`; `gold.consumo_varejista_mensal_uf`.

**O dado, lido em 14/09.** Dataset `varejista_consumidor`, recursos `_2024`…`_2026`. 23.478 linhas em 2026 (jan–jul), 2,6 MB. Colunas: `MES_REFERENCIA`, `COD_PERF_AGENTE`, `SIGLA_PERFIL_AGENTE`, `NOME_EMPRESARIAL`, `ESTADO_UF_CARGA`, `SUBMERCADO_CARGA`, `COD_PERF_AGENTE_CONECTADO`, `SIGLA_PERFIL_AGENTE_CONECTADO`, `QTD_PARCELA_CARGA`, `CONSUMO_TOTAL`. **A chave é de cinco colunas**: (`MES_REFERENCIA`, `COD_PERF_AGENTE`, `ESTADO_UF_CARGA`, `SUBMERCADO_CARGA`, `COD_PERF_AGENTE_CONECTADO`) — 0 duplicatas; `(mês, perfil)` sozinho duplica 2.465 vezes, porque um varejista atende cargas em várias UFs e distribuidoras. `SUBMERCADO_CARGA` por extenso. Uma linha com `COD_PERF_AGENTE_CONECTADO` vazio. Nota da própria CCEE no catálogo: *"no momento não são considerados os consumidores migrados no processo de migração simplificada"*.

**Confidencialidade (F1, F2, F4).** Consumo por cliente vindo da CCEE é classificado como **confidencial** pela Alup; o dataset é interno e o acesso é restrito por tipo de usuário. Este dado é por varejista e UF, não por consumidor final — mas o dicionário registra a classificação, e a Gold não desce abaixo de (mês, varejista, UF).

- [ ] **Step 1: Fixture e teste (falha)**

`tests/fixtures/ccee_varejista_consumidor_2026.csv`:

```csv
MES_REFERENCIA;COD_PERF_AGENTE;SIGLA_PERFIL_AGENTE;NOME_EMPRESARIAL;ESTADO_UF_CARGA;SUBMERCADO_CARGA;COD_PERF_AGENTE_CONECTADO;SIGLA_PERFIL_AGENTE_CONECTADO;QTD_PARCELA_CARGA;CONSUMO_TOTAL
202607;500;ALFA VAREJO CL;ALFA COMERCIALIZADORA LTDA;PR;SUL;81;DIST PR;150;4974.494964
202607;500;ALFA VAREJO CL;ALFA COMERCIALIZADORA LTDA;SC;SUL;82;DIST SC;20;300.5
202607;600;BETA VAR CQ5;BETA COMERCIALIZADORA S/A;MG;SUDESTE;1141;DIST MG;34;1327.388871
202607;600;BETA VAR CQ5;BETA COMERCIALIZADORA S/A;MG;SUDESTE;;;1;10
202606;500;ALFA VAREJO CL;ALFA COMERCIALIZADORA LTDA;PR;SUL;81;DIST PR;140;4500
```

```python
# tests/unit/conectores/test_ccee_varejista_consumidor.py
"""Conector CCEE/varejista consumidor — consumo das cargas de varejo, sem rede.

A chave tem cinco colunas: um varejista atende cargas em várias UFs e
distribuidoras no mesmo mês. (mês, perfil) sozinho duplica 2.465 vezes no
arquivo real — é o que o teste de chave protege.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_varejista_consumidor import CceeVarejistaConsumidor, ConsumoVarejista
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_varejista_consumidor_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeVarejistaConsumidor()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "varejista_consumidor_2026", "url": "u", "last_modified": "2026-09-01T14:00:00"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_o_mesmo_varejista_tem_uma_linha_por_uf_e_distribuidora(conector):
    registros = [ConsumoVarejista.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))]
    alfa = [r for r in registros if r.codigo_perfil == "500"]

    assert {(r.uf_carga, r.codigo_perfil_conectado) for r in alfa} == {("PR", "81"), ("SC", "82")}


def test_transformar_converte_submercado_e_tipa_consumo(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = ConsumoVarejista.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.submercado == "S"  # SUL vira sigla
    assert registro.uf_carga == "PR"
    assert registro.sigla_perfil_conectado == "DIST PR"
    assert registro.quantidade_parcelas_carga == 150
    assert registro.consumo_total == Decimal("4974.494964")


def test_conectado_vazio_vira_nulo(conector):
    registros = [ConsumoVarejista.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))]
    sem_conectado = [r for r in registros if r.codigo_perfil_conectado is None]

    assert len(sem_conectado) == 1
    assert sem_conectado[0].sigla_perfil_conectado is None


def test_consumo_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        ConsumoVarejista.model_validate(
            {
                "data_referencia": "2026-07-01",
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_perfil": "1",
                "sigla_perfil": "X",
                "nome_empresarial": "X",
                "uf_carga": "SP",
                "submercado": "SE",
                "quantidade_parcelas_carga": 1,
                "consumo_total": "-1",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0
```

Run → `ModuleNotFoundError`.

- [ ] **Step 2: Conector**

```python
# src/conectores/ccee_varejista_consumidor.py
"""Conector CCEE — consumo das parcelas de carga dos varejistas (Onda 1, público). Ordem 4 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `varejista_consumidor`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/varejista_consumidor

Uma linha por varejista, mês, UF da carga e distribuidora à qual a carga está
conectada — a chave tem cinco colunas, porque um varejista atende cargas em
várias UFs e distribuidoras. É o subtema "contratos de varejo" de Comercial e
Contratos (Tahigo Santos, B1), pela via pública.

A CCEE avisa no catálogo que os consumidores migrados pela migração
simplificada ainda não entram. A Alup classifica consumo vindo da CCEE como
confidencial (F1); o dataset é interno (F4) e a Gold não desce abaixo de
(mês, varejista, UF).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.conectores.ccee_pld import SIGLA_SUBMERCADO, SUBMERCADOS
from src.core.registry import registrar


class ConsumoVarejista(BaseModel):
    """O consumo das cargas de um varejista em uma UF e distribuidora, em um mês."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_perfil: str
    sigla_perfil: str
    nome_empresarial: str
    uf_carga: str
    submercado: str
    codigo_perfil_conectado: str | None = None
    sigla_perfil_conectado: str | None = None
    quantidade_parcelas_carga: int = Field(ge=0)
    consumo_total: Decimal = Field(ge=0)

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @field_validator("uf_carga")
    @classmethod
    def _uf_com_duas_letras(cls, valor: str) -> str:
        uf = valor.strip().upper()
        if len(uf) != 2 or not uf.isalpha():
            raise ValueError(f"UF inválida: {valor!r}")
        return uf


@registrar
class CceeVarejistaConsumidor(CceeCsvCkan):
    """Consumo de varejo por varejista, UF e distribuidora. CSV por ano."""

    dataset = "varejista_consumidor"
    entidade = "varejista_consumidor"
    schema = ConsumoVarejista

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        nome = limpar(bruto.get("SUBMERCADO_CARGA")).upper()
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_perfil": limpar(bruto.get("COD_PERF_AGENTE")),
            "sigla_perfil": limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "nome_empresarial": limpar(bruto.get("NOME_EMPRESARIAL")),
            "uf_carga": limpar(bruto.get("ESTADO_UF_CARGA")),
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "codigo_perfil_conectado": limpar(bruto.get("COD_PERF_AGENTE_CONECTADO")) or None,
            "sigla_perfil_conectado": limpar(bruto.get("SIGLA_PERFIL_AGENTE_CONECTADO")) or None,
            "quantidade_parcelas_carga": numero_ou_nulo(bruto.get("QTD_PARCELA_CARGA")),
            "consumo_total": numero_ou_nulo(bruto.get("CONSUMO_TOTAL")),
        }
```

Run → `5 passed`.

- [ ] **Step 3: Bronze, Silver, Gold**

```sql
-- definitions/bronze/ccee_varejista_consumidor.sqlx
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: consumo das cargas de varejo por varejista, UF e distribuidora (CCEE).
-- Dado classificado como confidencial pela Alup (F1); dataset interno (F4).
CREATE TABLE IF NOT EXISTS ${self()} (
  data_referencia            DATE      NOT NULL OPTIONS(description="Primeiro dia do mês de referência"),
  periodo_apuracao_ccee      STRING    NOT NULL,
  versao_publicacao          DATE      NOT NULL OPTIONS(description="last_modified do recurso no CKAN (ADR 016)"),
  codigo_perfil              STRING    NOT NULL OPTIONS(description="Perfil do varejista"),
  sigla_perfil               STRING    NOT NULL,
  nome_empresarial           STRING    NOT NULL,
  uf_carga                   STRING    NOT NULL,
  submercado                 STRING    NOT NULL OPTIONS(description="N, NE, S, SE — submercado da carga"),
  codigo_perfil_conectado    STRING             OPTIONS(description="Perfil da distribuidora à qual a carga está conectada; nulo em raras linhas"),
  sigla_perfil_conectado     STRING,
  quantidade_parcelas_carga  INT64     NOT NULL,
  consumo_total              NUMERIC   NOT NULL OPTIONS(description="Unidade não documentada pela CCEE — ver dicionário"),

  _ingestao_id               STRING    NOT NULL,
  _ingestao_timestamp        TIMESTAMP NOT NULL,
  _fonte                     STRING    NOT NULL,
  _schema_versao             STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia, codigo_perfil
OPTIONS(description="Consumo de varejo por varejista, UF e distribuidora — camada Bronze, append-only, confidencial (F1)");
```

```sql
-- definitions/silver/ccee_varejista_consumidor.sqlx
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["periodo_apuracao_ccee", "codigo_perfil", "uf_carga", "submercado", "codigo_perfil_conectado"],
    nonNull: ["data_referencia", "periodo_apuracao_ccee", "codigo_perfil", "uf_carga", "submercado", "consumo_total"],
    rowConditions: [
      "periodo_apuracao = periodo_apuracao_ccee",
      "submercado IN ('N','NE','S','SE')",
      "consumo_total >= 0",
      "quantidade_parcelas_carga >= 0"
    ]
  }
}

-- Silver: uma linha por varejista, mês, UF e distribuidora (chave de cinco
-- colunas — (mês, varejista) sozinho duplica 2.465 vezes no arquivo real).
-- `codigo_perfil_conectado` nulo entra na chave como um valor só: o BigQuery
-- agrupa nulos juntos no GROUP BY da asserção, e há uma linha assim por mês.
-- `agente_ccee` nulo: a origem traz o perfil do varejista, não a sigla do
-- agente; a Gold junta com `gold.agentes_ccee`.
SELECT
  data_referencia,
  submercado,
  CAST(NULL AS STRING) AS codigo_usina,  -- carga, não ativo de geração
  CAST(NULL AS STRING) AS agente_ccee,   -- perfil na origem, sigla na Gold
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  periodo_apuracao_ccee,
  versao_publicacao,
  codigo_perfil,
  sigla_perfil,
  nome_empresarial,
  uf_carga,
  codigo_perfil_conectado,
  sigla_perfil_conectado,
  quantidade_parcelas_carga,
  consumo_total,
  _ingestao_id,
  _ingestao_timestamp
FROM ${ref("bronze", "ccee_varejista_consumidor")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY periodo_apuracao_ccee, codigo_perfil, uf_carga, submercado, codigo_perfil_conectado
  ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC
) = 1
```

```sql
-- definitions/gold/consumo_varejista_mensal_uf.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: quanto cada varejista atendeu de carga em cada UF, mês a mês — parcelas
-- e consumo somados sobre as distribuidoras. Não desce abaixo de
-- (mês, varejista, UF): consumo vindo da CCEE é confidencial (F1), e a
-- distribuidora é detalhe operacional, não pergunta de domínio.
-- Unidade de `consumo_total` não documentada pela CCEE; a Gold não a afirma.
SELECT
  v.periodo_apuracao,
  v.codigo_perfil,
  v.sigla_perfil,
  a.agente_ccee,
  v.uf_carga,
  v.submercado,
  COUNT(DISTINCT v.codigo_perfil_conectado)  AS distribuidoras,
  SUM(v.quantidade_parcelas_carga)           AS parcelas_de_carga,
  SUM(v.consumo_total)                       AS consumo_total,
  MAX(v.versao_publicacao)                   AS versao_publicacao
FROM ${ref("silver", "ccee_varejista_consumidor")} AS v
LEFT JOIN ${ref("gold", "agentes_ccee")} AS a
  ON a.codigo_perfil = v.codigo_perfil
GROUP BY v.periodo_apuracao, v.codigo_perfil, v.sigla_perfil, a.agente_ccee, v.uf_carga, v.submercado
```

Run: `uv run pytest tests/unit/test_sql.py -q` → verde.

- [ ] **Step 4: Agendamento, alerta, domínio, dicionário**

Scheduler: bloco `ccee_varejista_consumidor`, `cron = "0 10 6 * *"`, `ultimos_dias = 120`. Monitoramento: `= 780`. Portal: `"ccee_varejista_consumidor": "Comercial e Contratos",`.

`docs/dicionario-dados/ccee_varejista_consumidor.md` — seções da Task 2, com: dataset; recursos `_2024`…`_2026`; natureza série mensal por varejista × UF × distribuidora; volume 23.478 linhas / 2,6 MB em 2026; dono Tahigo Santos — Comercial e Contratos, subtema varejo (B1); a **chave de cinco colunas** e o número que a justifica (2.465 duplicatas em (mês, perfil)); a nota da CCEE sobre migração simplificada; a seção **"Confidencialidade"** com F1, F2 (acesso por tipo de usuário) e F4 (interno) e o que a Gold não expõe; Campos (10; `SUBMERCADO_CARGA` → sigla; `COD_PERF_AGENTE_CONECTADO` nulo em 1 linha; **unidade de `CONSUMO_TOTAL` não documentada**); Dimensões (`submercado` sim — o da carga; `agente_ccee` via Gold); Deduplicação; Gold; Linhagem.

README: `| CCEE — consumo de varejo | [`ccee_varejista_consumidor.md`](ccee_varejista_consumidor.md) | 1 | `submercado` | `consumo_varejista_mensal_uf` |`.

- [ ] **Step 5: Dry-run real, suíte, commit**

Run: `uv run python -m src.cli ingerir ccee_varejista_consumidor --de 2026-06-01 --ate 2026-07-31 --dry-run`
Expected: `SUCESSO`, ~6.700 extraídos, 0 inválidos.

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_varejista_consumidor.py definitions/bronze/ccee_varejista_consumidor.sqlx definitions/silver/ccee_varejista_consumidor.sqlx definitions/gold/consumo_varejista_mensal_uf.sqlx tests/unit/conectores/test_ccee_varejista_consumidor.py tests/fixtures/ccee_varejista_consumidor_2026.csv docs/dicionario-dados/ccee_varejista_consumidor.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): consumo das cargas de varejo -- o subtema de varejo pela via publica

Uma linha por varejista, mes, UF da carga e distribuidora conectada. A chave
tem cinco colunas: (mes, varejista) sozinho duplica 2.465 vezes no arquivo
real, porque um varejista atende cargas em varias UFs e distribuidoras.

Consumo vindo da CCEE e confidencial para a Alup (F1). O dataset e interno
(F4) e a Gold nao desce abaixo de (mes, varejista, UF): distribuidora e
detalhe operacional, nao pergunta de dominio.

A CCEE avisa que os consumidores da migracao simplificada ainda nao entram.
Registrado no dicionario; quando entrarem, e o mesmo conector.

Dry-run contra a API real: <N> registros em junho e julho, 0 invalidos.
```

---
### Task 8: CVU, ESS e EER — o que o B1 nomeia em Mercado de Energia (ordem 5)

Três entidades numa tarefa porque duas delas (`encargo_ess_ancilar`,
`energia_reserva_liquidacao`) têm a forma de `exposicao_financeira_mensal` —
uma linha por mês, mercado inteiro — e a terceira (`custo_variavel_unitario_estrutural`)
é a única que precisa de perfilamento antes de fechar a chave.

**Files:**
- Create: `src/conectores/ccee_encargo_ess.py`, `src/conectores/ccee_energia_reserva.py`, `src/conectores/ccee_cvu_estrutural.py`
- Create: `definitions/bronze/ccee_encargo_ess.sqlx`, `definitions/bronze/ccee_energia_reserva.sqlx`, `definitions/bronze/ccee_cvu_estrutural.sqlx`
- Create: `definitions/silver/ccee_encargo_ess.sqlx`, `definitions/silver/ccee_energia_reserva.sqlx`, `definitions/silver/ccee_cvu_estrutural.sqlx`
- Create: `definitions/gold/encargos_setoriais_mensal.sqlx`, `definitions/gold/cvu_estrutural_vigente_usina.sqlx`
- Test: `tests/unit/conectores/test_ccee_encargo_ess.py`, `test_ccee_energia_reserva.py`, `test_ccee_cvu_estrutural.py`
- Create: `tests/fixtures/ccee_encargo_ess_2026.csv`, `ccee_energia_reserva_2026.csv`, `ccee_cvu_estrutural_2026.csv`
- Create: `docs/dicionario-dados/ccee_encargo_ess.md`, `ccee_energia_reserva.md`, `ccee_cvu_estrutural.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`

**Interfaces:**
- Consumes: `CceeCsvCkan` (com `delimitador = ","` no CVU), `limpar`, `numero_ou_nulo`, `primeiro_dia`, `periodo_ccee`.
- Produces: três Silver; `gold.encargos_setoriais_mensal` (ESS + EER lado a lado por mês); `gold.cvu_estrutural_vigente_usina`.

**O dado, lido em 14/09 (só os primeiros 64 KB de cada recurso).**

- `encargo_ess_ancilar`, recursos `_2023`…`_2026`, `;`. Uma linha por `MES_REFERENCIA`, 16 colunas: `ENCARGO_CONST_ON`, `ENCARGO_CONST_OFF`, `OUTROS_SERVICOS_ANCILARES`, `ENCARGO_CS`, `ENCARGO_SEG_ENER`, `RECEBIMENTO_ENCARGO_DH`, `ENCARGO_REST_OP_UNIT_COMT`, `ENCARGO_IMPORTACAO`, `RECEBIMENTO_ENCARGO_RESERVA_OP`, `RESSARCIMENTO_SERVICOS_ANCILARES`, `RESSARCIMENTO_CUSTO_OP_MNT_EQUIP`, `RESSARCIMENTO_CUSTO_OP_MNT_EQUIP_CAG`, `RESSARCIMENTO_CUSTO_IMPL_OP_MNT_SEP`, `RESSARCIMENTO_CUSTO_EMERGENCIAL`, `RESSARCIMENTO_DIST_IMPL_OP_MNT`. Valores em R$; muitos `0`. (A linha de exemplo tinha 14 valores para 16 cabeçalhos — **conferir no Step 1 se as duas últimas colunas vêm vazias ou se o cabeçalho tem coluna a mais**; o `csv.DictReader` põe `None` no que falta, e `numero_ou_nulo(None)` devolve `None`, então o conector não quebra em nenhum dos casos.)
- `energia_reserva_liquidacao`, recursos `_2024`…`_2026`, `;`. Uma linha por mês, 5 colunas: `EFEITO_CCEAR_DISP_CER`, `REPASSE_USUARIOS_RESERVA`, `AJUSTE`, `VALOR_TOTAL_LIQUID`. R$.
- `custo_variavel_unitario_estrutural`, recursos `_2025`, `_2026`, **vírgula**. Colunas: `MES_REFERENCIA`, `ANO_HORIZONTE`, `CODIGO_PARCELA_USINA`, `SIGLA_PARCELA`, `TIPO_COMBUSTIVEL`, `LEILAO`, `PRODUTO`, `CVU_ESTRUTURAL`, `CODIGO_MODELO_PRECO`, `TERMINO_SUPRIMENTO`, `INICIO_SUPRIMENTO`. Datas `dd/mm/aaaa`. Um CVU **por ano de horizonte**: a mesma usina aparece uma vez por `ANO_HORIZONTE` no mesmo mês. Chave candidata: (`MES_REFERENCIA`, `ANO_HORIZONTE`, `CODIGO_PARCELA_USINA`, `LEILAO`, `PRODUTO`). **Não verificada no arquivo inteiro.**

- [ ] **Step 1: Perfilar o CVU e conferir o ESS antes de escrever schema**

Rode, no diretório de rascunho (fora do repositório):

```python
import json, urllib.request, csv, io, collections
UA = {"User-Agent": "Alupar-DataCollector/1.0 (+https://alupar.com.br; contato: comercializacao@alupar.com.br)"}
def get(url): return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180)
for ds, delim, chave in [
    ("custo_variavel_unitario_estrutural", ",", ["MES_REFERENCIA", "ANO_HORIZONTE", "CODIGO_PARCELA_USINA", "LEILAO", "PRODUTO"]),
    ("encargo_ess_ancilar", ";", ["MES_REFERENCIA"]),
]:
    d = json.load(get(f"https://dadosabertos.ccee.org.br/api/3/action/package_show?id={ds}"))["result"]
    alvo = max(d["resources"], key=lambda r: r["name"])
    texto = get(alvo["url"]).read().decode("iso-8859-1")
    rows = list(csv.DictReader(io.StringIO(texto), delimiter=delim))
    dup = sum(v > 1 for v in collections.Counter(tuple(r[k] for k in chave) for r in rows).values())
    vazios = collections.Counter(k for r in rows for k, v in r.items() if v in ("", None))
    print(ds, "| linhas:", len(rows), "| dup na chave:", dup, "| colunas:", list(rows[0].keys()))
    print("  vazios:", dict(vazios))
    if ds.startswith("custo"):
        print("  horizontes:", sorted({r["ANO_HORIZONTE"] for r in rows}))
        print("  combustiveis:", sorted({r["TIPO_COMBUSTIVEL"] for r in rows}))
```

Registre os quatro números no dicionário do CVU (linhas, duplicatas, horizontes, combustíveis). **Se `dup na chave` for maior que zero**, acrescente `CODIGO_MODELO_PRECO` à chave (é a próxima coluna discriminante) e rode de novo; se ainda houver duplicatas, pare e registre em `docs/status.md` §2 como pendência técnica — a chave natural não é evidente e escolhê-la por tentativa é adivinhar schema.

- [ ] **Step 2: ESS — fixture, teste, conector**

`tests/fixtures/ccee_encargo_ess_2026.csv` (16 colunas, uma linha completa e uma com vazios):

```csv
MES_REFERENCIA;ENCARGO_CONST_ON;ENCARGO_CONST_OFF;OUTROS_SERVICOS_ANCILARES;ENCARGO_CS;ENCARGO_SEG_ENER;RECEBIMENTO_ENCARGO_DH;ENCARGO_REST_OP_UNIT_COMT;ENCARGO_IMPORTACAO;RECEBIMENTO_ENCARGO_RESERVA_OP;RESSARCIMENTO_SERVICOS_ANCILARES;RESSARCIMENTO_CUSTO_OP_MNT_EQUIP;RESSARCIMENTO_CUSTO_OP_MNT_EQUIP_CAG;RESSARCIMENTO_CUSTO_IMPL_OP_MNT_SEP;RESSARCIMENTO_CUSTO_EMERGENCIAL;RESSARCIMENTO_DIST_IMPL_OP_MNT
202607;2747079.77;19314484.15;0;24289284.37;0;2584264.9;14954509.45;0;0;0;0;0;0;0;0
202606;5118573.8;33332843.36;0;25561251.62;0;7153000.89;10807204.35;0;0;0;0;0;0;;
```

```python
# tests/unit/conectores/test_ccee_encargo_ess.py
"""Conector CCEE/ESS — encargos de serviço do sistema, uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_encargo_ess import CceeEncargoEss, EncargoEss
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_encargo_ess_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeEncargoEss()
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "encargo_ess_ancilar_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]})
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_os_encargos(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))
    registro = EncargoEss.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.encargo_constrained_on == Decimal("2747079.77")
    assert registro.encargo_constrained_off == Decimal("19314484.15")
    assert registro.encargo_seguranca_energetica == Decimal("0")


def test_coluna_ausente_no_fim_da_linha_vira_nulo(conector):
    bruto = next(r for r in conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30")))
    registro = EncargoEss.model_validate(conector.transformar(bruto))

    assert registro.ressarcimento_custo_emergencial is None
    assert registro.ressarcimento_distribuidora_implantacao is None


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
```

```python
# src/conectores/ccee_encargo_ess.py
"""Conector CCEE — encargos de serviço do sistema (ESS) e serviços ancilares, por mês (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `encargo_ess_ancilar`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/encargo_ess_ancilar

Uma linha por mês, valores do mercado inteiro em R$: o ESS que o B1 nomeia em
Mercado de Energia. Mesma forma da exposição financeira.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

CAMPOS = {
    "ENCARGO_CONST_ON": "encargo_constrained_on",
    "ENCARGO_CONST_OFF": "encargo_constrained_off",
    "OUTROS_SERVICOS_ANCILARES": "outros_servicos_ancilares",
    "ENCARGO_CS": "encargo_cs",
    "ENCARGO_SEG_ENER": "encargo_seguranca_energetica",
    "RECEBIMENTO_ENCARGO_DH": "recebimento_encargo_dh",
    "ENCARGO_REST_OP_UNIT_COMT": "encargo_restricao_operativa_unit_commitment",
    "ENCARGO_IMPORTACAO": "encargo_importacao",
    "RECEBIMENTO_ENCARGO_RESERVA_OP": "recebimento_encargo_reserva_operativa",
    "RESSARCIMENTO_SERVICOS_ANCILARES": "ressarcimento_servicos_ancilares",
    "RESSARCIMENTO_CUSTO_OP_MNT_EQUIP": "ressarcimento_custo_operacao_manutencao_equipamento",
    "RESSARCIMENTO_CUSTO_OP_MNT_EQUIP_CAG": "ressarcimento_custo_operacao_manutencao_equipamento_cag",
    "RESSARCIMENTO_CUSTO_IMPL_OP_MNT_SEP": "ressarcimento_custo_implantacao_operacao_manutencao_sep",
    "RESSARCIMENTO_CUSTO_EMERGENCIAL": "ressarcimento_custo_emergencial",
    "RESSARCIMENTO_DIST_IMPL_OP_MNT": "ressarcimento_distribuidora_implantacao",
}


class EncargoEss(BaseModel):
    """Os encargos de serviço do sistema de um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    encargo_constrained_on: Decimal | None = None
    encargo_constrained_off: Decimal | None = None
    outros_servicos_ancilares: Decimal | None = None
    encargo_cs: Decimal | None = None
    encargo_seguranca_energetica: Decimal | None = None
    recebimento_encargo_dh: Decimal | None = None
    encargo_restricao_operativa_unit_commitment: Decimal | None = None
    encargo_importacao: Decimal | None = None
    recebimento_encargo_reserva_operativa: Decimal | None = None
    ressarcimento_servicos_ancilares: Decimal | None = None
    ressarcimento_custo_operacao_manutencao_equipamento: Decimal | None = None
    ressarcimento_custo_operacao_manutencao_equipamento_cag: Decimal | None = None
    ressarcimento_custo_implantacao_operacao_manutencao_sep: Decimal | None = None
    ressarcimento_custo_emergencial: Decimal | None = None
    ressarcimento_distribuidora_implantacao: Decimal | None = None


@registrar
class CceeEncargoEss(CceeCsvCkan):
    """ESS mensal. CSV por ano, uma linha por mês."""

    dataset = "encargo_ess_ancilar"
    entidade = "encargo_ess"
    schema = EncargoEss

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
        }
        for origem, destino in CAMPOS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
```

Run: `uv run pytest tests/unit/conectores/test_ccee_encargo_ess.py -q` → `3 passed`.

- [ ] **Step 3: EER — fixture, teste, conector**

`tests/fixtures/ccee_energia_reserva_2026.csv`:

```csv
MES_REFERENCIA;EFEITO_CCEAR_DISP_CER;REPASSE_USUARIOS_RESERVA;AJUSTE;VALOR_TOTAL_LIQUID
202607;366353559.57;0;210898.64;366564458.21
202606;394306918.14;0;-3547179.17;390762770.66
```

```python
# tests/unit/conectores/test_ccee_energia_reserva.py
"""Conector CCEE/EER — liquidação da energia de reserva, uma linha por mês, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_energia_reserva import CceeEnergiaReserva, EnergiaReserva
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_energia_reserva_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeEnergiaReserva()
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "energia_reserva_liquidacao_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]})
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_transformar_tipa_e_aceita_ajuste_negativo(conector):
    junho = next(r for r in conector.extrair(Janela.de_texto("2026-06-01", "2026-06-30")))
    registro = EnergiaReserva.model_validate(conector.transformar(junho))

    assert registro.data_referencia == date(2026, 6, 1)
    assert registro.ajuste == Decimal("-3547179.17")  # ajuste pode ser negativo
    assert registro.valor_total_liquidado == Decimal("390762770.66")


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-06-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0
```

```python
# src/conectores/ccee_energia_reserva.py
"""Conector CCEE — liquidação da energia de reserva (EER), por mês (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `energia_reserva_liquidacao`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/energia_reserva_liquidacao

Uma linha por mês, R$, mercado inteiro: o EER que o B1 nomeia em Mercado de
Energia. `AJUSTE` pode ser negativo — é ajuste, não montante.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from src.conectores.ccee_ckan import CceeCsvCkan, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar

CAMPOS = {
    "EFEITO_CCEAR_DISP_CER": "efeito_ccear_disponibilidade_cer",
    "REPASSE_USUARIOS_RESERVA": "repasse_usuarios_reserva",
    "AJUSTE": "ajuste",
    "VALOR_TOTAL_LIQUID": "valor_total_liquidado",
}


class EnergiaReserva(BaseModel):
    """A liquidação da energia de reserva em um mês, em R$."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    efeito_ccear_disponibilidade_cer: Decimal | None = None
    repasse_usuarios_reserva: Decimal | None = None
    ajuste: Decimal | None = None
    valor_total_liquidado: Decimal | None = None


@registrar
class CceeEnergiaReserva(CceeCsvCkan):
    """EER mensal. CSV por ano, uma linha por mês."""

    dataset = "energia_reserva_liquidacao"
    entidade = "energia_reserva"
    schema = EnergiaReserva

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        registro: dict[str, Any] = {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
        }
        for origem, destino in CAMPOS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
```

Run: `uv run pytest tests/unit/conectores/test_ccee_energia_reserva.py -q` → `2 passed`.

- [ ] **Step 4: CVU — fixture, teste, conector (com a chave confirmada no Step 1)**

`tests/fixtures/ccee_cvu_estrutural_2026.csv` — **vírgula**:

```csv
MES_REFERENCIA,ANO_HORIZONTE,CODIGO_PARCELA_USINA,SIGLA_PARCELA,TIPO_COMBUSTIVEL,LEILAO,PRODUTO,CVU_ESTRUTURAL,CODIGO_MODELO_PRECO,TERMINO_SUPRIMENTO,INICIO_SUPRIMENTO
202601,2026,986386,UTE Alfa,Diesel,2º Leilão de Energia Nova,2009-15,2427.25,235,05/10/2035,06/10/2020
202601,2027,986386,UTE Alfa,Diesel,2º Leilão de Energia Nova,2009-15,2837.36,235,05/10/2035,06/10/2020
202601,2026,777001,UTE Beta,Gás natural,1º Leilão de Energia Nova,2010-15,310.1,236,31/12/2040,01/01/2026
202602,2026,986386,UTE Alfa,Diesel,2º Leilão de Energia Nova,2009-15,2450,235,05/10/2035,06/10/2020
```

```python
# tests/unit/conectores/test_ccee_cvu_estrutural.py
"""Conector CCEE/CVU estrutural — o único CSV com vírgula, e um CVU por ano de horizonte, sem rede."""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_cvu_estrutural import CceeCvuEstrutural, CvuEstrutural
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_cvu_estrutural_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeCvuEstrutural()
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "custo_variavel_unitario_estrutural_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]})
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(FIXTURE.read_bytes()))
    return conector


def test_delimitador_e_virgula():
    assert CceeCvuEstrutural.delimitador == ","


def test_a_mesma_usina_tem_um_cvu_por_ano_de_horizonte(conector):
    registros = [CvuEstrutural.model_validate(conector.transformar(b)) for b in conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))]
    alfa = sorted((r.ano_horizonte, r.cvu_estrutural) for r in registros if r.codigo_parcela_usina == "986386")

    assert alfa == [(2026, Decimal("2427.25")), (2027, Decimal("2837.36"))]


def test_transformar_converte_datas_brasileiras(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))
    registro = CvuEstrutural.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 1)
    assert registro.inicio_suprimento == date(2020, 10, 6)
    assert registro.termino_suprimento == date(2035, 10, 5)
    assert registro.tipo_combustivel == "Diesel"
    assert registro.leilao == "2º Leilão de Energia Nova"


def test_cvu_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        CvuEstrutural.model_validate(
            {
                "data_referencia": "2026-01-01",
                "periodo_apuracao_ccee": "2026-01",
                "versao_publicacao": "2026-09-01",
                "ano_horizonte": 2026,
                "codigo_parcela_usina": "1",
                "sigla_parcela": "X",
                "tipo_combustivel": "X",
                "leilao": "X",
                "produto": "X",
                "cvu_estrutural": "-1",
                "codigo_modelo_preco": "1",
            }
        )


def test_ingerir_em_dry_run(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-02-28"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 4
    assert execucao.linhas_invalidas == 0
```

```python
# src/conectores/ccee_cvu_estrutural.py
"""Conector CCEE — custo variável unitário estrutural por usina (Onda 1, público). Ordem 5 da ADR 021.

Fonte: dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_estrutural`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/custo_variavel_unitario_estrutural

O CVU que o B1 nomeia em Mercado de Energia. Uma linha por usina, leilão,
produto e **ano de horizonte** no mês de referência: a mesma usina aparece uma
vez por ano projetado. É o único CSV da CCEE com **vírgula** como delimitador,
e traz datas em `dd/mm/aaaa`.

`CODIGO_PARCELA_USINA` é código interno da CCEE, não CEG: `codigo_usina` fica
nulo até o de-para (#141), como na geração.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee, primeiro_dia
from src.core.registry import registrar


def _data_br(valor: str | None) -> date | None:
    texto = limpar(valor)
    return datetime.strptime(texto, "%d/%m/%Y").date() if texto else None


class CvuEstrutural(BaseModel):
    """O CVU estrutural de uma usina para um ano de horizonte, no mês de referência."""

    data_referencia: date
    periodo_apuracao_ccee: str
    versao_publicacao: date
    ano_horizonte: int = Field(ge=2000, le=2100)
    codigo_parcela_usina: str
    sigla_parcela: str
    tipo_combustivel: str
    leilao: str
    produto: str
    cvu_estrutural: Decimal = Field(ge=0, description="R$/MWh")
    codigo_modelo_preco: str
    inicio_suprimento: date | None = None
    termino_suprimento: date | None = None


@registrar
class CceeCvuEstrutural(CceeCsvCkan):
    """CVU estrutural por usina e horizonte. CSV por ano, delimitado por vírgula."""

    dataset = "custo_variavel_unitario_estrutural"
    entidade = "cvu_estrutural"
    schema = CvuEstrutural
    delimitador = ","

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = bruto["MES_REFERENCIA"]
        return {
            "data_referencia": primeiro_dia(mes),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "ano_horizonte": numero_ou_nulo(bruto.get("ANO_HORIZONTE")),
            "codigo_parcela_usina": limpar(bruto.get("CODIGO_PARCELA_USINA")),
            "sigla_parcela": limpar(bruto.get("SIGLA_PARCELA")),
            "tipo_combustivel": limpar(bruto.get("TIPO_COMBUSTIVEL")),
            "leilao": limpar(bruto.get("LEILAO")),
            "produto": limpar(bruto.get("PRODUTO")),
            "cvu_estrutural": numero_ou_nulo(bruto.get("CVU_ESTRUTURAL")),
            "codigo_modelo_preco": limpar(bruto.get("CODIGO_MODELO_PRECO")),
            "inicio_suprimento": _data_br(bruto.get("INICIO_SUPRIMENTO")),
            "termino_suprimento": _data_br(bruto.get("TERMINO_SUPRIMENTO")),
        }
```

Run: `uv run pytest tests/unit/conectores/test_ccee_cvu_estrutural.py -q` → `5 passed`.

- [ ] **Step 5: Bronze e Silver das três**

As três Silver seguem o molde da exposição financeira (Task 3, Step 3): seis dimensões comuns, `QUALIFY … ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC`, asserção `periodo_apuracao = periodo_apuracao_ccee`. O que muda:

| Entidade | Bronze: colunas de valor | Silver `uniqueKey` | Silver `rowConditions` extra | `CLUSTER BY` |
|---|---|---|---|---|
| `ccee_encargo_ess` | as 15 de `CAMPOS`, `NUMERIC` nulas | `["periodo_apuracao_ccee"]` | `"encargo_constrained_on IS NULL OR encargo_constrained_on >= 0"`, idem `encargo_constrained_off` | `data_referencia` |
| `ccee_energia_reserva` | as 4 de `CAMPOS`, `NUMERIC` nulas | `["periodo_apuracao_ccee"]` | `"valor_total_liquidado IS NULL OR valor_total_liquidado >= 0"` (o `ajuste` pode ser negativo) | `data_referencia` |
| `ccee_cvu_estrutural` | `ano_horizonte INT64 NOT NULL`, `codigo_parcela_usina STRING NOT NULL`, `sigla_parcela`, `tipo_combustivel`, `leilao`, `produto`, `cvu_estrutural NUMERIC NOT NULL`, `codigo_modelo_preco`, `inicio_suprimento DATE`, `termino_suprimento DATE` | a chave confirmada no Step 1 — por padrão `["periodo_apuracao_ccee", "ano_horizonte", "codigo_parcela_usina", "leilao", "produto"]` | `"cvu_estrutural >= 0"`, `"ano_horizonte >= EXTRACT(YEAR FROM data_referencia)"`, `"termino_suprimento IS NULL OR inicio_suprimento IS NULL OR termino_suprimento >= inicio_suprimento"` | `data_referencia, codigo_parcela_usina` |

Escreva os seis arquivos com esses valores; o Bronze do CVU leva `OPTIONS(description="Código interno da CCEE — NÃO é o CEG; de-para pendente (#141)")` em `codigo_parcela_usina` e a Silver deixa `codigo_usina` nulo com o mesmo comentário da geração.

- [ ] **Step 6: Gold**

```sql
-- definitions/gold/encargos_setoriais_mensal.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: ESS e EER lado a lado, mês a mês — os dois encargos que o B1 nomeia
-- em Mercado de Energia, em R$. FULL OUTER JOIN pelo mesmo motivo de
-- `mercado_mensal_submercado`: as duas séries fecham em datas diferentes, e o
-- mês em que só uma existe não pode sumir.
-- Sem KPI (ADR 012): os totais são somas das colunas publicadas.
SELECT
  COALESCE(ess.periodo_apuracao, eer.periodo_apuracao) AS periodo_apuracao,
  ess.encargo_constrained_on,
  ess.encargo_constrained_off,
  ess.encargo_cs,
  ess.encargo_importacao,
  COALESCE(ess.encargo_constrained_on, 0) + COALESCE(ess.encargo_constrained_off, 0)
    + COALESCE(ess.outros_servicos_ancilares, 0) + COALESCE(ess.encargo_cs, 0)
    + COALESCE(ess.encargo_seguranca_energetica, 0) + COALESCE(ess.encargo_restricao_operativa_unit_commitment, 0)
    + COALESCE(ess.encargo_importacao, 0)                     AS ess_total_reais,
  eer.efeito_ccear_disponibilidade_cer,
  eer.repasse_usuarios_reserva,
  eer.ajuste                                                  AS eer_ajuste_reais,
  eer.valor_total_liquidado                                   AS eer_total_liquidado_reais,
  ess.versao_publicacao                                       AS ess_versao_publicacao,
  eer.versao_publicacao                                       AS eer_versao_publicacao
FROM ${ref("silver", "ccee_encargo_ess")} AS ess
FULL OUTER JOIN ${ref("silver", "ccee_energia_reserva")} AS eer
  ON eer.periodo_apuracao = ess.periodo_apuracao
```

```sql
-- definitions/gold/cvu_estrutural_vigente_usina.sqlx
config {
  type: "table",
  schema: "gold",
  tags: ["gold"]
}

-- Gold: o CVU estrutural de cada usina térmica, por ano de horizonte, como
-- publicado no mês de referência mais recente. Uma linha por (usina, leilão,
-- produto, horizonte). É o custo que explica o despacho por ordem de mérito
-- e cruza com `geracao_mensal_usina` por `codigo_parcela_usina`.
-- Sem KPI (ADR 012).
SELECT
  codigo_parcela_usina,
  sigla_parcela,
  tipo_combustivel,
  leilao,
  produto,
  ano_horizonte,
  cvu_estrutural                AS cvu_estrutural_reais_mwh,
  inicio_suprimento,
  termino_suprimento,
  periodo_apuracao              AS publicado_no_mes,
  versao_publicacao
FROM ${ref("silver", "ccee_cvu_estrutural")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY codigo_parcela_usina, leilao, produto, ano_horizonte
  ORDER BY periodo_apuracao DESC
) = 1
```

(A Gold com `QUALIFY` é aceita pelo teste de SQL — ele só exige `type: "table"` e leitura da Silver.)

Run: `uv run pytest tests/unit/test_sql.py -q` → verde.

- [ ] **Step 7: Agendamento, alerta, domínio, dicionários**

Scheduler — três blocos, `cron = "0 10 6 * *"`, `ultimos_dias = 120`. Monitoramento — `ccee_encargo_ess = 780`, `ccee_energia_reserva = 780`, `ccee_cvu_estrutural = 780`. Portal — as três em `"Mercado de Energia"`.

Três dicionários com as seções da Task 2. Específicos:

- `ccee_encargo_ess.md`: uma linha por mês; os 15 valores com nome do lake; a **conferência do Step 1** sobre as duas últimas colunas (vazias ou cabeçalho a mais — registrar o que se viu); Gold `encargos_setoriais_mensal`.
- `ccee_energia_reserva.md`: uma linha por mês; 4 valores; `ajuste` pode ser negativo; Gold `encargos_setoriais_mensal`.
- `ccee_cvu_estrutural.md`: **vírgula**; um CVU por ano de horizonte; os números do Step 1 (linhas, duplicatas, horizontes, combustíveis); a chave escolhida e por quê; `codigo_parcela_usina` não é CEG (#141); datas `dd/mm/aaaa`; `CVU_ESTRUTURAL` em R$/MWh (é a única unidade que o nome da coluna deixa claro); Gold `cvu_estrutural_vigente_usina`.

README — três linhas: `| CCEE — ESS e serviços ancilares | … | 1 | — | `encargos_setoriais_mensal` |`, `| CCEE — energia de reserva (EER) | … | 1 | — | `encargos_setoriais_mensal` |`, `| CCEE — CVU estrutural | … | 1 | — | `cvu_estrutural_vigente_usina` |`.

- [ ] **Step 8: Dry-run real das três, suíte, commit**

```
uv run python -m src.cli ingerir ccee_encargo_ess       --de 2026-01-01 --ate 2026-07-31 --dry-run
uv run python -m src.cli ingerir ccee_energia_reserva   --de 2026-01-01 --ate 2026-07-31 --dry-run
uv run python -m src.cli ingerir ccee_cvu_estrutural    --de 2026-01-01 --ate 2026-02-28 --dry-run
```

Expected: `SUCESSO` nas três, 0 inválidos; 7 registros nas duas mensais.

Run: `uv run ruff check src tests && uv run pytest tests/unit -q && terraform fmt -check -recursive infra/`

```bash
git add src/conectores/ccee_encargo_ess.py src/conectores/ccee_energia_reserva.py src/conectores/ccee_cvu_estrutural.py definitions/bronze/ccee_encargo_ess.sqlx definitions/bronze/ccee_energia_reserva.sqlx definitions/bronze/ccee_cvu_estrutural.sqlx definitions/silver/ccee_encargo_ess.sqlx definitions/silver/ccee_energia_reserva.sqlx definitions/silver/ccee_cvu_estrutural.sqlx definitions/gold/encargos_setoriais_mensal.sqlx definitions/gold/cvu_estrutural_vigente_usina.sqlx tests/unit/conectores/test_ccee_encargo_ess.py tests/unit/conectores/test_ccee_energia_reserva.py tests/unit/conectores/test_ccee_cvu_estrutural.py tests/fixtures/ccee_encargo_ess_2026.csv tests/fixtures/ccee_energia_reserva_2026.csv tests/fixtures/ccee_cvu_estrutural_2026.csv docs/dicionario-dados/ccee_encargo_ess.md docs/dicionario-dados/ccee_energia_reserva.md docs/dicionario-dados/ccee_cvu_estrutural.md docs/dicionario-dados/README.md infra/modules/scheduler/main.tf infra/modules/monitoramento/main.tf src/portal/custo.py
```

Mensagem:

```
feat(ccee): CVU, ESS e EER -- o que o B1 nomeia em Mercado de Energia

Tres entidades num commit porque duas tem a mesma forma da exposicao
financeira (uma linha por mes, mercado inteiro, R$) e a terceira e a unica
que precisou de perfilamento antes de fechar a chave.

ESS e EER entram lado a lado na Gold encargos_setoriais_mensal, com FULL
OUTER JOIN: as duas series fecham em datas diferentes e o mes em que so uma
existe nao pode sumir.

O CVU estrutural e o unico CSV da CCEE com virgula. Um CVU por usina e por
ano de horizonte: a mesma usina aparece uma vez por ano projetado, e a chave
tem <N> colunas (<D> duplicatas no arquivo inteiro com a chave escolhida).
CODIGO_PARCELA_USINA nao e CEG, como na geracao -- e a Lacuna 1 de novo.

Com isto, o dominio Mercado de Energia tem todos os itens que o B1 nomeia
do lado da CCEE. EAR e ENA sao do ONS e ficam para outro plano.

Dry-run contra a API real: ESS 7, EER 7, CVU <N> registros, 0 invalidos.
```

---
### Task 9: Conciliação escrita — o que a construção mudou nos documentos

Nenhum código novo. É a tarefa que deixa `status.md`, a ADR 021, o painel de custo e o backlog do GitHub dizendo a verdade depois das Tasks 1–8. Sem ela, o próximo agente relê tudo e chega às mesmas conclusões erradas que a ADR 021 tinha.

**Files:**
- Modify: `docs/arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md` (três correções)
- Modify: `docs/status.md` (tabela de conectores; §1 "Entregue e verificado"; §3 A11/A12 se algo mudou)
- Modify: `docs/arquitetura/dominios-analiticos.md` (situação por domínio)
- Modify: `docs/arquitetura/visao-geral.md` (tabela de domínios)
- Modify: `docs/proximos-passos.md` (§4, a fila)
- Modify: `definitions/silver/bcb_juros.sqlx` — **só se o #143 já tiver entrado sem o #146**, ou o contrário
- GitHub: rótulos das issues #17 e #25; comentário na #141 com o que agora depende dela

**Interfaces:**
- Consumes: os números anotados nos dry-runs das Tasks 2–8 (registros, inválidos, duração).
- Produces: documentação em dia; nada que outra tarefa consuma.

- [ ] **Step 1: Corrigir a ADR 021 com o que os arquivos mostraram**

Em `docs/arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md`:

1. Na tabela de **Mercado de Energia**, a linha de `lista_agente_associado`: trocar `agente ↔ perfil: um agente tem vários perfis, e é o perfil que transaciona` por `lista mensal de agentes — classe, situação de comercializador e de varejista, UF, categoria — com histórico por mês. **Não traz perfil**: o elo agente ↔ perfil já está em `lista_perfil_v1``. Estado: `entregue`.
2. Acrescentar, depois da §2, uma seção **"2.1 O que a leitura dos arquivos corrigiu"** com as três correções da Parte 1 §1.3 deste plano (sem coluna de perfil; gzip mensal na geração; vírgula no CVU) e a frase: *"A ADR foi escrita do catálogo; estas três coisas só o arquivo mostra. O dicionário de cada entidade é a fonte a partir daqui."*
3. Na §3 "Ordem de entrada", marcar cada linha com `**entregue em <data>**` conforme as tasks fecharem, e o estado das demais entidades da ADR que **não** entraram neste plano (`geracao_horaria_submercado`, `geracao_fonte_primaria`, `garantia_fisica_*`, `mre_*`, `contrato_montante_mensal_tipo`, `contrato_montante_periodo`, `sazonalizacao_*`, `varejista_subclasse`, `montante_mensal_mcp_agente`, `sumario_mensal_liquidacao`, `fator_ajuste_gf`, `premio_risco_hidrologico`, `repasse_risco_hidrologico`, `proinfa_*`, `penalidade_preco_mensal`, `custo_variavel_unitario_conjuntural*`, `encargo_horario_submercado`, `energia_reserva_mensal_leilao`, `consumo_horario_submercado`) como `**a entrar — mesmo caminho: subclasse de `CceeCsvCkan`, arquivo lido antes do schema**`.

- [ ] **Step 2: `status.md`**

Na tabela "Conectores (7 componentes cada)", acrescentar uma linha por entidade das Tasks 2–8, no formato das existentes, com o **volume verificado no dry-run** e o agendamento. Exemplo da primeira:

```markdown
| **CCEE/agente** | CSV anual, UTF-8 e ISO-8859-1 misturados por linha, via CKAN | **<N> registros / 2 meses**, 0 inválidos, contra a API real | mensal, dia 6 às 10h, janela 120 dias |
```

Atualizar a frase `**Sete das dez falaram com a API real**` para o total novo (dez entidades da CCEE somadas às existentes: conte pelo `alupdata listar`). Em §1 "Framework e ferramental", acrescentar:

```markdown
| Base `CceeCsvCkan`: CKAN, fluxo, gzip, decodificação por linha, janela por mês | `src/conectores/ccee_ckan.py` | 18 testes; lida dos arquivos reais em 14/09 — encoding misto, gzip mensal, vírgula no CVU |
| ADR 016 **aceita**: `versao_publicacao` do CKAN, Silver vigente + `_historico` | `definitions/silver/ccee_contabilizacao_perfil*.sqlx` | replay de raw antigo deixa de rebaixar a vigente |
```

Em §3, a linha A11 (de-para de usina) ganha: `**Agora bloqueia dado real**: `ccee_geracao_usina` e `ccee_cvu_estrutural` guardam `codigo_parcela_usina` com `codigo_usina` nulo à espera dele`.

- [ ] **Step 3: Domínios e visão geral**

Em `docs/arquitetura/dominios-analiticos.md`, por domínio, na linha **Fontes hoje** / **Gold hoje** / **Situação**:

- Mercado de Energia: `+ ccee_agente · ccee_encargo_ess · ccee_energia_reserva · ccee_cvu_estrutural`; Gold `+ agentes_por_classe_mensal, encargos_setoriais_mensal, cvu_estrutural_vigente_usina`; situação `**pronto do lado da CCEE** — faltam EAR e ENA, que são do ONS`.
- Geração e Operacional: `+ ccee_geracao_usina`; Gold `+ geracao_mensal_usina`; situação `**parcial** — geração na granularidade de usina entregue; `codigo_usina` depende do de-para (#141)`.
- Comercial e Contratos: `+ ccee_contrato_montante · ccee_varejista_consumidor`; Gold `+ posicao_contratual_mensal_perfil, consumo_varejista_mensal_uf`; situação `**parcial pela via pública** — o book interno segue em A7`.
- Risco e Compliance: `Fontes hoje: ccee_exposicao_financeira · ccee_contabilizacao_perfil (com histórico de recontabilização)`; Gold `exposicao_mercado_mensal, resultado_contabilizacao_mensal_perfil`; situação `**iniciado** — saiu de zero sem credencial`.

Em `docs/arquitetura/visao-geral.md`, tabela "8 Domínios Analíticos", coluna Situação: as mesmas quatro frases, curtas.

- [ ] **Step 4: `proximos-passos.md` §4**

Acrescentar à tabela "O que entrou na fila em 14/09" as linhas dos PRs que este plano gerar, e mover para "O que segue parado" o que ficou: EAR/ENA do ONS (plano próprio), as entidades secundárias da ADR 021 (§Step 1.3), e o `timeout` do Cloud Run Job se a Task 5 o tiver tornado configurável.

- [ ] **Step 5: `bcb_juros` e a sexta dimensão — só se preciso**

Run: `uv run pytest tests/unit/test_sql.py -q -k dimensoes`

Se falhar em `silver/bcb_juros.sqlx`, é porque #143 e #146 entraram e a Silver do `bcb_juros` nasceu antes da sexta dimensão. Em `definitions/silver/bcb_juros.sqlx`, depois de `FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,`:

```sql
  CAST(NULL AS STRING) AS periodo_apuracao_ccee,  -- a origem não declara período próprio
```

Se passar, nada a fazer.

- [ ] **Step 6: Backlog do GitHub**

```bash
gh issue edit 17 --remove-label "status/bloqueado" --add-label "status/em-review"
gh issue comment 17 --body "Destravada em 14/09 pela ADR 018 (era filtro de cliente nao identificado, nao bloqueio). Entregues pela via publica: ccee_pld, ccee_perfil e as entidades da ADR 021. O rotulo bloqueado estava desatualizado."
gh issue edit 25 --remove-label "status/bloqueado"
gh issue comment 25 --body "O conector esta entregue e verificado contra a API real (ADR 019). O que falta nao e o conector: e o acervo posterior a 26/10/2022, que e a pendencia A10 / #129. Rotulo ajustado para nao contar duas vezes a mesma dependencia."
gh issue comment 141 --body "Passou a bloquear dado real: silver.ccee_geracao_usina e silver.ccee_cvu_estrutural guardam CODIGO_PARCELA_USINA (codigo interno da CCEE) com codigo_usina nulo. No dia em que o de-para chegar, e uma tabela pelo S2 Data Intake e uma juncao em cada Silver."
```

**Regra 6**: nenhum desses textos leva assinatura, rodapé ou menção a ferramenta. Confira o corpo antes de enviar — o hook de commit não vê comentário de issue.

- [ ] **Step 7: Commit e PR**

```bash
git checkout -b docs/conciliacao-pos-fila-ccee main   # ou a partir da branch da Task 8, se as tasks estiverem empilhadas
git add docs/ definitions/silver/bcb_juros.sqlx
```

Mensagem:

```
docs: conciliacao depois da fila da CCEE -- ADR 021 corrigida, status e dominios em dia

A ADR 021 foi escrita do catalogo; tres coisas so o arquivo mostrou:
lista_agente_associado nao tem coluna de perfil, geracao_horaria_usina vem
em gzip mensal, e o CVU estrutural usa virgula. Entram como secao propria da
ADR, e o dicionario de cada entidade passa a ser a fonte.

status.md ganha as <N> entidades novas com o volume verificado em dry-run, a
base CceeCsvCkan e a ADR 016 aceita. Dominios: Mercado de Energia pronto do
lado da CCEE; Risco e Compliance iniciado sem credencial; Comercial e
Contratos parcial pela via publica; Geracao e Operacional na granularidade
de usina, a espera do de-para (#141), que agora bloqueia dado real.

Rotulos das issues #17 e #25 ajustados: estavam bloqueadas por dependencias
que ja se resolveram ou que pertencem a outra issue.
```

---

## Parte 3 — Auto-revisão do plano

**Cobertura da spec (ADR 021).** Ordem 1: Task 2. Ordem 2: Tasks 3 e 4. Ordem 3: Task 5. Ordem 4: Tasks 6 e 7. Ordem 5: Task 8. As 15 entidades secundárias da ADR ficam nomeadas na Task 9, Step 1.3, como "a entrar pelo mesmo caminho" — não estão neste plano porque cada uma exige ler o arquivo antes do schema, e este plano só escreve schema do que leu. EAR e ENA (ONS) estão fora por serem outro subsistema.

**Cobertura da ADR 016.** Task 4 implementa a opção B (Silver vigente por `versao_publicacao`, view `_historico`, `uniqueKey` em chave+versão) e muda o status para aceito com o identificador registrado no dicionário. As outras entidades mensais carregam `versao_publicacao` e ordenam por ele, sem `_historico` — a ADR só pede a view de histórico onde há recontabilização, e a Task 4 é a única fonte com `AJUSTE_RECONTAB`.

**Cobertura dos 7 componentes.** Cada Task 2–8 tem: conector (01), Bronze (02), Silver com `uniqueKey`/`nonNull`/faixas (03), Gold `type: "table"` descritiva (04), testes unitários sem rede mais dry-run real (05), scheduler + alerta (06), dicionário com linhagem + README (07). O checklist da skill `conector-alupdata` é cumprido item a item; o "teste de idempotência" que ela pede é o `QUALIFY` da Silver, coberto por `test_silver_deduplica_e_expoe_as_dimensoes_comuns`.

**Placeholders.** Nenhum `TODO`/`TBD`. Os únicos valores em aberto são medidas que só a execução dá — `<N>` registros, `<T>` segundos, e a chave do CVU depois do Step 1 da Task 8 — e cada um diz como obter o número. Os dicionários das Tasks 3–8 são descritos por seção com o conteúdo específico em vez de repetir o esqueleto integral da Task 2; o esqueleto está lá uma vez, completo.

**Consistência de tipos e nomes.** `CceeCsvCkan` expõe `_abrir(sufixo) -> IO[bytes]`, `_pacote() -> dict`, `_recurso(sufixo) -> dict`, `publicado_em(sufixo) -> date`, `extrair(janela)`; `decodificar(bytes) -> str`, `limpar(str|None) -> str`, `numero_ou_nulo(str|None) -> str|None`, `primeiro_dia(str) -> date`, `periodo_ccee(str) -> str`. Todas as tasks monkeypatcham `_pacote` e `_abrir` e chamam os cinco helpers com esses nomes. O bruto sempre carrega `_versao_publicacao` (ISO) e `_sufixo`. `SIGLA_SUBMERCADO`, `SUBMERCADOS` e `_data_e_hora` vêm de `src.conectores.ccee_pld` com os nomes que o arquivo já tem. `gold.agentes_ccee` expõe `codigo_perfil`, `agente_ccee`, `sigla_perfil`, `submercado` — conferido no arquivo existente.

**Riscos que o plano nomeia e não resolve.** (1) Tempo de execução da Task 5 — medido no Step 6, com o caminho para subir o `timeout`. (2) `Literal[tupla]` no pydantic — alternativa dada na Task 2. (3) A chave do CVU — perfilamento obrigatório antes do schema. (4) Duas sessões no mesmo worktree — conferir a branch antes de cada commit.

---

## Execução

Plano salvo em `docs/superpowers/plans/2026-09-14-conciliacao-e-fila-ccee.md`. Duas formas de executar:

1. **Subagent-Driven** (recomendado) — um subagente novo por task, revisão entre tasks, iteração rápida. Skill: `superpowers:subagent-driven-development`.
2. **Inline** — as tasks nesta sessão, em lotes com pontos de revisão. Skill: `superpowers:executing-plans`.

Pré-condições antes da Task 1: mesclar **#146** (sexta dimensão) e **#145** (ADR 021). As Tasks 2–8 podem ir em PRs separados (um por entidade, como o histórico faz) ou empilhados; a Task 9 fecha depois do último.
