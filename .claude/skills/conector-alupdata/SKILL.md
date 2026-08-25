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

O runner em `src/core/conector.py` já faz raw no GCS, validação, colunas
técnicas, carga no Bronze e log de execução. **Um conector novo implementa
apenas `extrair()` e `transformar()`** — não escreva BigQuery, GCS nem
`_ingestao_id` à mão. Comece pelo scaffolding:

```bash
make novo-conector fonte=ons entidade=carga   # gera os 7 componentes esqueletados
```

```python
@registrar
class OnsCarga(Conector):
    fonte = "ons"
    entidade = "carga"
    schema = CargaRegistro          # modelo Pydantic, valida registro a registro
    schema_versao = "1"
    max_dias_por_requisicao = 30    # o runner particiona a janela sozinho

    def extrair(self, janela: Janela) -> Iterator[dict]: ...
    def transformar(self, bruto: dict) -> dict: ...
```

Use `src/conectores/bcb_cambio.py` como referência viva — é o conector completo
da Onda 1.

Regras que valem para todo conector:

- Use `src/core/config.py::get_settings` para projeto, datasets e bucket, e
  `src/core/logging.py::get_logger` — nunca `print`, nunca o nome do dataset
  escrito literalmente.
- Credencial **só** via `src/core/secrets.py` (Secret Manager). Nada de token em
  código, em `.env` versionado ou em default de função.
- HTTP por `src/core/http.py::criar_sessao` — timeout e retry já configurados.
  Fonte que não é HTTP (banco da Onda 3, planilha da Onda 4) implementa o mesmo
  contrato com outro `extrair()`.
- Extração **sempre por janela**; nunca "hoje". Reprocessar é passar outra
  janela, não escrever outro script.
- Valide com Pydantic. Registro inválido é descartado com log e contado em
  `linhas_invalidas` — nunca sumir em silêncio.
- Idempotência: o Bronze é append-only; quem garante que reprocessar não
  duplica é o `QUALIFY ROW_NUMBER()` da Silver.

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
