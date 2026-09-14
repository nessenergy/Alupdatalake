# CCEE — contabilização por perfil

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `contabilizacao_montante_perfil_agente` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=contabilizacao_montante_perfil_agente` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2024` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal por perfil, com recontabilização**: uma linha por (`MES_REFERENCIA`, `COD_PERF_AGENTE`), ~47.000 perfis por mês |
| Volume verificado | 329.080 linhas em 2026 (jan–jul), 43 MB, em 14/09/2026 |
| Encoding | **UTF-8 e ISO-8859-1 misturados linha a linha** (760 linhas UTF-8, 1.001 ISO-8859-1) — decodificação por linha na base `CceeCsvCkan` |
| Dono do dado (Alup) | Letícia Ferreira — Risco e Compliance (B1) |
| Credencial | nenhuma |

Ordem 2 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
É o resultado financeiro de cada perfil de agente no mercado de curto prazo
(MCP), mês a mês: os 16 componentes que compõem `RESULTADO_FINAL`, inclusive
`AJUSTE_RECONTAB` — a recontabilização declarada no próprio dado.

## Versão — a ADR 016 na prática

Esta é a fonte que a [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md)
esperava para decidir. `versao_publicacao` é o `last_modified` do recurso no
CKAN — item 2 da ordem de preferência da ADR, porque o arquivo em si não traz
número de versão nem data de publicação.

- **Silver vigente** (`ccee_contabilizacao_perfil`): uma linha por
  (`periodo_apuracao_ccee`, `codigo_perfil`), da publicação mais recente
  (`ORDER BY versao_publicacao DESC, _ingestao_timestamp DESC`). O replay de um
  raw antigo não rebaixa a vigente, porque a ordem vem da fonte, não da hora
  da leitura.
- **Silver de histórico** (`ccee_contabilizacao_perfil_historico`): uma linha
  por (`periodo_apuracao_ccee`, `codigo_perfil`, `versao_publicacao`) — é o que
  responde "qual era o resultado de março antes da recontabilização de junho".
- **Evidência de que a republicação é do ano inteiro**: o recurso `_2025` tem
  `last_modified` de 02/02/2026 — o ano inteiro foi reescrito, não só o mês
  recontabilizado.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `COD_AGENTE` | `codigo_agente` | STRING | trim; a origem não traz a sigla |
| `COD_PERF_AGENTE` | `codigo_perfil` | STRING | trim — o perfil é quem transaciona |
| `SIGLA_PERFIL_AGENTE` | `sigla_perfil` | STRING | trim |
| `NOME_EMPRESARIAL` | `nome_empresarial` | STRING | trim |
| `CNPJ` | `cnpj` | STRING | só dígitos; 14 obrigatórios |
| `VALOR_TM_MCP` | `valor_tm_mcp` | NUMERIC | R$; vazio → NULL |
| `COMPENSACAO_MRE` | `compensacao_mre` | NUMERIC | R$; vazio → NULL |
| `VALOR_ENCARGO` | `valor_encargo` | NUMERIC | R$; vazio → NULL |
| `VALOR_AJUSTE_EXPOSICAO` | `valor_ajuste_exposicao` | NUMERIC | R$; vazio → NULL |
| `VALOR_AJUSTE_ALIVIO_RET` | `valor_ajuste_alivio_retroativo` | NUMERIC | R$; vazio → NULL |
| `EFEITO_CONTRAT_DISP` | `efeito_contratos_disponibilidade` | NUMERIC | R$; vazio → NULL |
| `EFEITO_CONTRAT_COTA_GF` | `efeito_contratos_cota_gf` | NUMERIC | R$; vazio → NULL |
| `EFEITO_CONTRAT_NUCLEAR` | `efeito_contratos_nuclear` | NUMERIC | R$; vazio → NULL |
| `AJUSTE_RECONTAB` | `ajuste_recontab` | NUMERIC | R$; vazio → NULL — a recontabilização, quando houve |
| `AJUSTE_MCSD_EX` | `ajuste_mcsd_ex` | NUMERIC | R$; vazio → NULL |
| `RESULTADO_FINANCEIRO_ER` | `resultado_financeiro_energia_reserva` | NUMERIC | R$; vazio → NULL |
| `EFEITO_CCEARQ` | `efeito_ccearq` | NUMERIC | R$; vazio → NULL |
| `EFEITO_CONTRAT_ITAIPU` | `efeito_contratos_itaipu` | NUMERIC | R$; vazio → NULL |
| `EFEITO_REPASSE_RISCO_HIDRO` | `efeito_repasse_risco_hidrologico` | NUMERIC | R$; vazio → NULL |
| `EFEITO_DESLOC_PLD_CMO` | `efeito_deslocamento_pld_cmo` | NUMERIC | R$; vazio → NULL |
| `RESULTADO_FINAL` | `resultado_final` | NUMERIC | R$; vazio → NULL — o número que o perfil liquida |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

### Frequência de vazio (lida em 14/09/2026)

| Coluna | % de linhas vazias |
|---|---|
| `COMPENSACAO_MRE` | 98% |
| `AJUSTE_MCSD_EX` | ~100% |
| `EFEITO_CCEARQ` | ~100% |
| `VALOR_TM_MCP` | 43% |
| `EFEITO_CONTRAT_DISP` | 14% |
| `AJUSTE_RECONTAB` | 2% |
| `VALOR_AJUSTE_ALIVIO_RET` | 0,2% |

Vazio vira NULL, nunca zero: são grandezas contábeis diferentes, e a origem
distingue as duas.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de apuração |
| `submercado` | não | o resultado é do perfil, não do submercado |
| `codigo_usina` | não | resultado de perfil, não de ativo |
| `agente_ccee` | **não, na Silver** | a origem traz `COD_AGENTE`, não a sigla; a Gold traz a sigla juntando com `gold.agentes_ccee` por `codigo_perfil` |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`, `codigo_perfil`). Vence a
**publicação mais recente** (`versao_publicacao`), e a hora da leitura só
desempata leituras da mesma publicação — opção B da ADR 016. A Silver de
histórico acrescenta `versao_publicacao` à chave: uma linha por perfil, mês
**e** publicação.

## Gold

`gold.resultado_contabilizacao_mensal_perfil` — resultado final, MCP,
encargos, recontabilização, risco hidrológico e energia de reserva em R$, mês
a mês por perfil, com a sigla do agente. `LEFT JOIN` com `gold.agentes_ccee`
por `codigo_perfil`, não `INNER`: perfil encerrado sai da dimensão (só
`ATIVO`) mas ainda tem resultado no mês registrado aqui; sumir com ele seria
lacuna silenciosa. Sem KPI (ADR 012).

## Qualidade e observações

- Encoding misto no arquivo real: 760 linhas UTF-8 e 1.001 ISO-8859-1 no
  recurso de 2026. Decodificação por linha, como em toda fonte da CCEE.
- O significado exato de cada componente do resultado (por exemplo
  `EFEITO_CCEARQ`, `AJUSTE_MCSD_EX`) **não está documentado pela CCEE no
  catálogo**. Os nomes do lake ficam próximos da origem por isso, em vez de
  arriscar uma tradução errada; a dúvida vai ao dono do domínio (B3: 3 dias
  úteis).
- `(periodo_apuracao_ccee, codigo_perfil)` é único na origem: dois perfis do
  mesmo agente no mesmo mês são linhas distintas, não duplicidade.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → contabilizacao_montante_perfil_agente_{ano}.csv
  → gs://<bucket>-raw/ccee/contabilizacao_perfil/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_contabilizacao_perfil            (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_contabilizacao_perfil          (vigente; QUALIFY por perfil+mês, versao_publicacao DESC)
      → silver.ccee_contabilizacao_perfil_historico (uma linha por chave e versão)
        → gold.resultado_contabilizacao_mensal_perfil
```
