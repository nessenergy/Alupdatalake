# Dossiê da Onda 2 — preparado antes das credenciais

Preparado em **25/09/2026** para que o dossiê da Onda 2 saia em dias, e não
em uma semana, depois que as credenciais chegarem (pedido 3 da
[pauta de 25/09](../relatorios/2026-09-25-alinhamento.md), prazo 12/10).

A parte A é o roteiro de fechamento; a parte B é o rascunho do dossiê, com o
que já é verificável preenchido e marcado **〔a preencher〕** o que só a carga
real responde. Na emissão, a parte B vira
`docs/relatorios/<data>-dossie-onda-2.md`, no formato do
[dossiê das Ondas 0 e 1](../relatorios/2026-09-25-dossie-ondas-0-e-1.md).

## Estado em 25/09

| Entidade | 7 componentes | dev | hml | O que falta |
|---|---|---|---|---|
| `tempook_ena_prevs` | completos | carregando: 5 linhas em 25/09, agendada 11h30 | fora da agenda — sem credencial | gravar o token em `hml` |
| `tempook_boletins` | completos | 0 linhas: o acervo do fornecedor parou em 2022 (A10) | fora da agenda | resposta do TempoOK sobre o acervo |
| `hubspot_negocios` | completos | erro: secret sem versão | fora da agenda | token do Hubspot (A9, pedido 3) |
| `bbce_curva_forward` | completos | nunca rodou | fora da agenda | acesso e host do BBCE (A7, pedido 3) |
| CCEE agente credenciado | — | — | — | posição da Alup sobre as 32h do item 2.1 (pedido 4) |

Os 7 componentes foram conferidos arquivo a arquivo em 25/09: conector,
Bronze, Silver, Gold (`cobertura_ena_prevs_tempook`,
`cobertura_boletins_tempook`, `funil_comercial`, `curva_forward_vigente`),
testes unitários e de integração, agendamento no Terraform e dicionário.

## Parte A — roteiro de fechamento

Cada passo vale para `dev` e depois para `hml`. Passo humano é pelo console.

1. **Credencial gravada** (Alup, pelo grupo dela, ou `operacao-datalake@`
   quando a credencial é da ness.): *Segurança → Secret Manager →* o secret
   *→ Nova versão*. Nomes: `alupdata-hubspot-api-token`,
   `alupdata-bbce-credenciais`, `alupdata-tempook-api-token`. O token do
   TempoOK em `hml` é gravado por quem o recebeu, pelo console — nunca copiado
   de `dev` por terminal.
2. **Teste de integração contra a origem real**, na máquina de quem opera,
   antes de agendar:
   `ALUPDATA_INTEGRACAO_HUBSPOT=1 uv run pytest tests/integration/test_hubspot_negocios.py -v`
   (idem `ALUPDATA_INTEGRACAO_BBCE` para o BBCE). Falhou aqui, corrige aqui —
   é mais barato que no Cloud Run.
3. **Agendamento**: tirar a entidade de `conectores_sem_agendamento` no
   `.tfvars` do ambiente, por PR.
   Deploy `all` no ambiente.
4. **Primeira carga** pelo workflow *Executar ingestão*, conector e ambiente.
   Conferir em `bronze._execucoes` (`status = 'SUCESSO'`, linhas > 0).
5. **Reprocessamento** de uma entidade da onda, a partir do arquivo bruto,
   como no dossiê das Ondas 0 e 1 (§4.4). Sugestão: `tempook_ena_prevs`, que
   já carrega em `dev`.
6. **Gold com linha** nas quatro tabelas da onda.
7. **`terraform plan` sem mudança** nos dois ambientes (deploy `infra` com a
   imagem publicada).
8. **Preencher a parte B**, emitir em `docs/relatorios/`, gerar o HTML e
   indexar.

O que não chegar até a data da emissão sai **declarado** no dossiê, com
motivo e dependência — nunca some do escopo.

## Parte B — rascunho do dossiê

### 1. Resumo dos critérios

| Critério | Situação | Evidência |
|---|---|---|
| Sete componentes por fonte | atendido — 4 de 4 entidades | §3 |
| Carga real com sucesso | 〔a preencher〕 de 4, nos dois ambientes | §3 |
| Portões de segurança do CI | 〔a preencher: CI da `main` na data〕 | §4.1 |
| Infraestrutura sem pendência | 〔a preencher: runs do plan em dev e hml〕 | §4.2 |
| Dicionário de dados e linhagem | atendido | §4.3 |
| Reprocessamento sem chamar a origem | 〔a preencher〕 | §4.4 |
| Agendamento em funcionamento | 〔a preencher: agendas ativas e primeira execução agendada〕 | §4.5 |

### 2. Escopo da Onda 2

| Fonte contratual | Entidades | Situação |
|---|---|---|
| TempoOK | `tempook_ena_prevs`, `tempook_boletins` | 〔a preencher〕 — boletins dependem do acervo (A10) |
| Hubspot | `hubspot_negocios` | 〔a preencher〕 |
| BBCE | `bbce_curva_forward` | 〔a preencher〕 |
| CCEE agente credenciado | nenhuma | 〔a preencher conforme a posição da Alup sobre o item 2.1: credencial solicitada, ou horas realocadas〕 |

### 3. Entidades

| Entidade | Linhas — dev | Linhas — hml | Gold, em hml (linhas) |
|---|---:|---:|---|
| TempoOK — previsão de ENA<br>`tempook_ena_prevs` | 〔 〕 | 〔 〕 | `cobertura_ena_prevs_tempook` (〔 〕) |
| TempoOK — boletins<br>`tempook_boletins` | 〔 〕 | 〔 〕 | `cobertura_boletins_tempook` (〔 〕) |
| Hubspot — negócios<br>`hubspot_negocios` | 〔 〕 | 〔 〕 | `funil_comercial` (〔 〕) |
| BBCE — curva forward<br>`bbce_curva_forward` | 〔 〕 | 〔 〕 | `curva_forward_vigente` (〔 〕) |

Consulta que preenche a tabela, em cada ambiente:

```sql
SELECT CONCAT(fonte, '_', entidade) AS entidade, linhas_carregadas, iniciada_em
FROM bronze._execucoes
WHERE modo = 'FONTE' AND status = 'SUCESSO' AND fonte IN ('tempook', 'hubspot', 'bbce')
QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY iniciada_em DESC) = 1
```

### 4. Evidências

As subseções seguem o dossiê das Ondas 0 e 1: portões do CI (4.1), plan
sem mudança (4.2), dicionário (4.3), reprocessamento (4.4), agendamento
(4.5). Cada uma recebe a data e o número da execução no dia da emissão.

### 5. O que fica para depois da emissão

〔a preencher: o que não chegou, com motivo, dependência e data prevista〕
