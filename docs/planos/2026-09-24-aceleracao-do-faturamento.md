# Aceleração do faturamento: aceite conjunto das Ondas 0 e 1

> **Para quem executa:** tarefas em ordem; as marcadas *paralela* andam juntas.
> Passos com checkbox (`- [ ]`). Defeito que a carga real revelar vira correção
> com teste antes do passo seguinte, no mesmo padrão do #223.

**Objetivo:** entregar os dossiês das Ondas 0 e 1 juntos, em 29–30/09, e
levar os dois marcos (R$ 53.760, 36,2% do contrato) a um único aceite em
~01/10 — duas semanas antes do prazo da Onda 1 (16/10).

**Abordagem:** o código das duas ondas está pronto; o que falta é evidência e
aceite. A carga das fontes públicas deixa de esperar o agendamento mensal e
roda pelo workflow `Executar ingestão`; a janela de `hml` abre em 25/09, não
em 30/09; e o tempo de aceite da Alup, que é onde o dinheiro espera, encurta
com o assinante definido e a reunião marcada antes da entrega.

**Ferramentas:** workflow `Executar ingestão` (#221) e `Deploy GCP`, API REST
do BigQuery com as credenciais de aplicação, `gh`, a skill `homologacao-onda`
e `scripts/gerar_documento.py`.

**Base:** desenho aprovado pelo Ricardo em 24/09 (conversa de brainstorming),
[plano de fechamento das ondas](2026-09-24-fechamento-das-ondas.md) e
[avaliação global](2026-09-24-avaliacao-global.md). Este plano substitui as
datas daquele para as Ondas 0 e 1; o resto dele continua valendo.

## Restrições globais

- As seis regras do [`AGENTS.md`](../../AGENTS.md), em especial nenhuma
  atribuição de IA em commit, PR, issue, comentário ou documento.
- **Homologação é aceite da Alup.** Os dossiês pedem aceite; nenhum documento
  declara onda homologada.
- Mensagens à Alup (quem assina, convite da reunião, pedido de credenciais) são
  **redigidas e entregues ao Ricardo**; quem envia é a coordenação.
- Reordenar ou fatiar ondas no contrato não entra: é negociação comercial.
- Janela e carga seguem a regra 3: toda execução tem janela explícita ou a do
  agendamento; carga retroativa além disso só por pedido de domínio (D1).
- `hml` volta a `agendamentos_ativos = false` depois do aceite (teto da E2).

## Calendário

| Dia | Marco |
|---|---|
| 24/09 (qui) | replay da Onda 0; disparo das 18 fontes públicas restantes |
| 25/09 (sex) | janela de `hml` aberta; correções da primeira carga |
| 26/09 (sáb) | 3º dia seguido de `SUCESSO` no BCB — critério da Onda 0 cumprido |
| 28/09 (seg) | carga repetida em `hml` (feita em 25/09) |
| 29–30/09 | dossiês das Ondas 0 e 1 entregues juntos |
| ~01/10 | reunião de homologação e aceite conjunto |

---

## Tarefa 1: Replay da Onda 0 contra o GCS real (24/09)

**Critério:** reprocessamento demonstrado em uma fonte, sem chamar a origem.

- [ ] **Passo 1: Achar o objeto raw e a janela da execução de 24/09 do câmbio**

```bash
TOKEN=$(gcloud auth application-default print-access-token)
curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  "https://bigquery.googleapis.com/bigquery/v2/projects/alupar-dev-alupdata/queries" \
  -d '{"query":"SELECT ingestao_id, janela_inicio, janela_fim FROM bronze._execucoes WHERE fonte=\"bcb\" AND entidade=\"cambio_ptax\" AND status=\"SUCESSO\" AND modo=\"FONTE\" ORDER BY iniciada_em DESC LIMIT 1","useLegacySql":false}'
```

O objeto é `gs://alupar-dev-alupdata-raw/bcb/cambio_ptax/dt=<janela_inicio>/<ingestao_id>.json.gz`.

- [ ] **Passo 2: Disparar o replay**

```bash
gh workflow run "Executar ingestão" -f environment=dev -f conector=bcb_cambio_ptax \
  -f uri=gs://alupar-dev-alupdata-raw/bcb/cambio_ptax/dt=<janela_inicio>/<ingestao_id>.json.gz \
  -f de=<janela_inicio> -f ate=<janela_fim>
```

- [ ] **Passo 3: Conferir** a linha nova em `bronze._execucoes`: `modo = REPLAY`,
  `origem_ingestao_id = <ingestao_id>`, `status = SUCESSO`, 3 linhas. Guardar a
  saída para o dossiê.

## Tarefa 2: Carga das 18 fontes públicas restantes (24/09) *(paralela à 1)*

Já carregadas em 24/09: `bcb_cambio_ptax`, `bcb_juros`, `ons_carga`, `ons_ear`,
`ons_ena`. Restam 18.

- [ ] **Passo 1: Disparar**

```bash
for c in ibge_ipca aneel_siga ons_capacidade ons_geracao_usina \
         ons_disponibilidade_usina ons_restricao_coff_eolica ons_restricao_coff_fotovoltaica \
         ccee_pld ccee_perfil ccee_agente ccee_exposicao_financeira ccee_contabilizacao_perfil \
         ccee_geracao_usina ccee_contrato_montante ccee_varejista_consumidor \
         ccee_encargo_ess ccee_energia_reserva ccee_cvu_estrutural; do
  gh workflow run "Executar ingestão" -f environment=dev -f conector="$c"
done
```

- [ ] **Passo 2: Ler o resultado** (última execução de cada entidade):

```sql
SELECT fonte, entidade, status, linhas_extraidas, linhas_invalidas,
       linhas_carregadas, ROUND(duracao_segundos) AS s, SUBSTR(erro, 1, 200) AS erro
FROM bronze._execucoes
QUALIFY ROW_NUMBER() OVER (PARTITION BY fonte, entidade ORDER BY iniciada_em DESC) = 1
ORDER BY status, fonte, entidade
```

Esperado: 23 entidades públicas com `SUCESSO`.

- [ ] **Passo 3: Para cada `ERRO`**, uma correção por PR, com teste que
  reproduz a mensagem do BigQuery antes do código (padrão do #223), merge, deploy
  `all` em `dev` e novo disparo só daquela fonte. Registrar cada defeito no
  `status.md` com a data.

## Tarefa 3: Silver e Gold com linha (25/09)

- [ ] **Passo 1:** rodar o Dataform pelo deploy (o `apply` não muda nada e o
  Dataform roda em seguida):

```bash
gh workflow run "Deploy GCP" -f environment=dev -f module=all
```

- [ ] **Passo 2:** contar as linhas das 22 tabelas Gold de mercado (lista na
  Tarefa 3.2 do plano de fechamento). Gold vazia com Silver cheia é defeito de
  SQL: teste em `tests/unit/test_sql.py` e correção. Gold vazia porque a fonte
  ainda não tem período publicado (mensal) é registrada no dossiê com o motivo.

## Tarefa 4: Janela de homologação em `hml` a partir de 25/09 *(paralela à 3)*

- [ ] **Passo 1 (humano, grupo de operação):** gravar o token do Dataform no
  secret `alupdata-dataform-git-token` de `alupar-hm-alupdata`
  ([`acoes-humanas.md`](../acoes-humanas.md) §1) e definir
  `DATAFORM_GIT_TOKEN_VERSAO=1` no ambiente `hml` do GitHub.
- [ ] **Passo 2:** em `infra/environments/hml.tfvars`, ligar a janela e os
  alertas também para o endereço da Alup (E3), como na decisão 1 da avaliação:

```hcl
agendamentos_ativos        = true # janela de homologação das Ondas 0 e 1, 25/09
emails_alerta              = ["operacao-datalake@ness.com.br", "alup.alertas@alupar.com.br"]
conectores_sem_agendamento = ["hubspot_negocios", "bbce_curva_forward", "tempook_boletins"]
```

  O teste `test_hml_nasce_sem_agendamento` exige `false` e quebra. Antes de
  mudar o `.tfvars`, ajustar o teste para aceitar `true` só com a janela
  declarada na mesma linha — assim a regra de custo da E2 continua cobrada:

```python
    hml = _ler("infra/environments/hml.tfvars")
    assert _tem(r"agendamentos_ativos\s*=\s*false", hml) or _tem(
        r"agendamentos_ativos\s*=\s*true\s*#\s*janela de homologação.*\d{2}/\d{2}", hml
    ), "hml só agenda na janela de homologação, declarada com a data"
```

  Rodar o teste com o `.tfvars` ainda em `false` (passa), trocar a linha
  (passa), e com `true` sem o comentário (falha — conferir e desfazer). Depois
  `uv run pytest tests/unit/test_infra.py -q` e `terraform -chdir=infra fmt
  -check -recursive`; PR, merge e `gh workflow run "Deploy GCP" -f
  environment=hml -f module=all`.
- [ ] **Passo 3 (humano, Owner de `hml`):** ligar o `TABLE_STORAGE`
  ([`acoes-humanas.md`](../acoes-humanas.md) §1b) com o projeto
  `alupar-hm-alupdata`.
- [ ] **Passo 4:** repetir o laço da Tarefa 2 com `-f environment=hml`, mais
  `bcb_cambio_ptax`, `bcb_juros`, `ons_carga`, `ons_ear` e `ons_ena`; e um replay
  em `hml` (`ons_carga`), como na Tarefa 1.

## Tarefa 5: Portal com uma Gold real — demonstração com login da Alup

**Mudou em 25/09.** O IAP do Portal usa o cliente OAuth gerenciado pelo
Google, e nesse modo [só entram contas da organização dona do projeto](https://docs.cloud.google.com/iap/docs/managed-oauth-client)
— a da Alup. Contas `@ness.com.br` são recusadas mesmo com a concessão ao grupo
(conferida no log de auditoria em 24/09). Liberar externos exigiria cliente
OAuth próprio, configurado no console do projeto da Alup.

- [ ] A evidência passa a ser a **demonstração ao vivo na reunião de aceite,
  com o login de alguém da Alup**. Depende de a Alup informar os grupos de
  acesso (pedido 6 da pauta de 25/09), que entram em `portal_acesso` em `hml`.

## Tarefa 6: Dossiês das Ondas 0 e 1 (29–30/09)

- [ ] **Passo 1:** carregar a skill `homologacao-onda` e preencher o checklist
  para cada onda, uma evidência por linha: 7 componentes, CI verde na `main`,
  `terraform plan` sem mudança, dicionário e linhagem, replay (Tarefas 1 e 4),
  3 dias de `SUCESSO` (Onda 0), carga e Gold por entidade (Onda 1), Portal
  (Tarefa 5), `make all` e a captura do Scheduler.
- [ ] **Passo 2:** incluir o **de-para 13 fontes contratuais × 27 entidades**
  (item 9 da avaliação), na tabela abaixo, com o estado de cada linha em 29/09:

| Fonte contratual | Onda | Entidades |
|---|---|---|
| BCB | 0/1 | `bcb_cambio_ptax`, `bcb_juros` |
| IBGE | 1 | `ibge_ipca` |
| ANEEL | 1 | `aneel_siga` |
| ONS | 1 | `ons_carga`, `ons_ear`, `ons_ena`, `ons_geracao_usina`, `ons_capacidade`, `ons_disponibilidade_usina`, `ons_restricao_coff_eolica`, `ons_restricao_coff_fotovoltaica` |
| CCEE InfoMercado | 1 | `ccee_pld`, `ccee_perfil`, `ccee_agente`, `ccee_exposicao_financeira`, `ccee_contabilizacao_perfil`, `ccee_geracao_usina`, `ccee_contrato_montante`, `ccee_varejista_consumidor`, `ccee_encargo_ess`, `ccee_energia_reserva`, `ccee_cvu_estrutural` |
| CCEE agente credenciado | 2 | nenhuma (item 2.1) |
| BBCE | 2 | `bbce_curva_forward` |
| Hubspot | 2 | `hubspot_negocios` |
| TempoOK | 2 | `tempook_boletins`, `tempook_ena_prevs` |
| Oracle FMB, Portal Alup, MySQL RDS, RM/TOTVS | 3 | nenhuma (A7) |

  A mesma tabela entra em `docs/dicionario-dados/README.md` (feito em 25/09;
  em 29/09 falta só o estado de cada linha).
- [ ] **Passo 3:** escrever `docs/relatorios/2026-09-29-dossie-ondas-0-e-1.md`
  no formato dos relatórios, gerar o HTML e indexar:

```bash
uv run --with markdown python scripts/gerar_documento.py docs/relatorios/2026-09-29-dossie-ondas-0-e-1.md --html
```

- [ ] **Passo 4:** PR, merge e entrega ao Ricardo para envio.

## Tarefa 7: Mensagens de coordenação — substituída pela pauta de 25/09

**Mudou em 25/09.** Os três pedidos (quem assina o aceite, reunião de ~01/10 e
Onda 2 com as 32h do item 2.1) estão na seção 4 da
[pauta de alinhamento](../relatorios/2026-09-25-alinhamento.md), pedidos 1 a 4,
junto com os grupos do Portal (pedido 6). A pauta é o canal: não há mensagens
avulsas, e o que não estiver nela não vira e-mail.

## Tarefa 8: Documentos vivos (24/09 e a cada marco)

- [ ] `status.md` §4: corrigir "as outras 20" para **18**, e registrar o novo
  alvo (dossiês em 29–30/09, aceite conjunto ~01/10).
- [ ] Plano de fechamento: apontar as Fases 1 a 3 para este plano; a Onda 1
  deixa de ter dossiê em 07/10.
- [ ] A cada fonte carregada ou defeito corrigido, uma linha datada no
  `status.md`.
