# Reunião de 01/10/2026 — dados entregues e acesso ao lake

**Quando:** quinta, 01/10/2026, 15h, 30 minutos.
**Com:** Tainá, Leonardo, Maurício e Eduardo (Alup); Ricardo e equipe (ness.).
**Objetivo:** mostrar no Portal e no BigQuery o que está pronto, o que é novo
e a lista conferida das 13 fontes do contrato.

## 1. Onde olhar

| O quê | Endereço |
|---|---|
| Portal (homologação) | <https://alupdata-portal-u6o7nifu6q-uc.a.run.app> — login com a conta `@alupar.com.br` do grupo `alup.alertas@alupar.com.br` |
| Saúde das cargas | <https://alupdata-portal-u6o7nifu6q-uc.a.run.app/lake> |
| Indicadores | <https://alupdata-portal-u6o7nifu6q-uc.a.run.app/indicadores> |
| BigQuery | <https://console.cloud.google.com/bigquery?project=alupar-hm-alupdata> — dataset `gold` |
| Painel de acompanhamento | <https://painel.alupdata.ness.com.br> |
| Itens do pedido de 28/09 | <https://painel.alupdata.ness.com.br/aditivo.html> |
| As 13 fontes e as entidades de cada uma | [`dicionario-dados/README.md`](../dicionario-dados/README.md#das-13-fontes-do-contrato-às-27-entidades) |
| Dicionário de cada tabela | [`dicionario-dados/`](../dicionario-dados/) — um arquivo por fonte, com campos e linhagem |
| Dossiê das Ondas 0 e 1 | [`2026-09-25-dossie-ondas-0-e-1.md`](2026-09-25-dossie-ondas-0-e-1.md) |
| Cruzamento do pedido de 28/09 | [`planos/2026-09-28-fontes-pedidas-pela-alup.md`](../planos/2026-09-28-fontes-pedidas-pela-alup.md) |

## 2. Roteiro (30 min)

| Min | Bloco | O que mostrar |
|---|---|---|
| 0–5 | Acesso | Login no Portal com a conta de alguém da Alup, ao vivo |
| 5–12 | O que carrega | `/lake`: cada fonte, última carga, linhas, linhas recusadas |
| 12–20 | O dado | BigQuery, com as consultas da §3 |
| 20–27 | O pedido de 28/09 | Painel, tela do pedido: item a item, entregue e pendente |
| 27–30 | Próximos passos | Pendências com a Alup (§5) |

## 3. Consultas prontas (BigQuery, `alupar-hm-alupdata`)

PLD médio, máximo e mínimo por mês e submercado:

```sql
SELECT periodo_apuracao, submercado, pld_medio_reais_mwh, pld_maximo_reais_mwh, pld_minimo_reais_mwh
FROM `alupar-hm-alupdata.gold.pld_mensal_submercado`
ORDER BY periodo_apuracao DESC, submercado;
```

Carga média por mês e submercado (ONS):

```sql
SELECT periodo_apuracao, submercado, carga_media_mwmed, carga_maxima_mwmed
FROM `alupar-hm-alupdata.gold.carga_mensal_submercado`
ORDER BY periodo_apuracao DESC, submercado;
```

Geração por usina no mês (CCEE) — troque a sigla por uma usina do portfólio:

```sql
SELECT periodo_apuracao, sigla_usina, fonte_primaria, submercado, geracao_centro_gravidade_total
FROM `alupar-hm-alupdata.gold.geracao_mensal_usina`
WHERE sigla_usina LIKE '%<SIGLA>%'
ORDER BY periodo_apuracao DESC;
```

Indicadores com numerador e denominador na linha:

```sql
SELECT periodo_apuracao, indicador, submercado, fonte, numerador, denominador, valor, unidade_valor
FROM `alupar-hm-alupdata.gold.indicadores_mensais`
ORDER BY periodo_apuracao DESC, indicador;
```

## 4. Números de referência (29/09)

- **43 conectores** no lake; **26,9 milhões de linhas** carregadas nos últimos
  30 dias em `dev`.
- **13 fontes do contrato**, entregues por **27 entidades** (dicionário, §1).
- **Pedido de 28/09:** 17 de 25 itens entregues, com os 7 componentes e 24 meses
  de histórico em `dev`; 8 pendentes (ONS mensal pesado, arquivo diário e API);
  1 com estimativa em revisão (consumo horário por perfil de agente, ~185 GB).

## 5. Pendências com a Alup

| # | Pedido |
|---|---|
| [#258](https://github.com/nessenergy/Alupdatalake/issues/258) | Quem assina o aceite das Ondas 0 e 1 |
| [#259](https://github.com/nessenergy/Alupdatalake/issues/259) | Reunião de aceite das Ondas 0 e 1 |
| [#260](https://github.com/nessenergy/Alupdatalake/issues/260) | Posição sobre as 32h do item 2.1 (CCEE agente credenciado) |
| [#262](https://github.com/nessenergy/Alupdatalake/issues/262) | Credenciais da Onda 2: token do Hubspot e acesso do BBCE |
| [#12](https://github.com/nessenergy/Alupdatalake/issues/12) | VPN e credenciais do Oracle FMB (Onda 3) |
