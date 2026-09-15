# CCEE — ESS e serviços ancilares

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset `encargo_ess_ancilar` |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=encargo_ess_ancilar` |
| Endpoint do arquivo | **descoberto pelo CKAN**, um recurso por ano (`_2023` … `_2026`) |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Série mensal, mercado inteiro**: uma linha por `MES_REFERENCIA`, sem agente |
| Volume verificado | 7 linhas em 2026, em 14/09/2026 |
| Encoding | mesma decodificação por linha da base `CceeCsvCkan` |
| Dono do dado (Alup) | Taina Mota — Mercado de Energia (B1) |
| Credencial | nenhuma |

Ordem 5 da [ADR 021](../arquitetura/decisoes/021-conjuntos-da-ccee-por-dominio.md).
O ESS (encargo de serviço do sistema) e os serviços ancilares que o B1 nomeia
em Mercado de Energia. Mesma forma da exposição financeira: uma linha por mês,
valores do mercado inteiro em R$, sem agente e sem submercado.

## Conferência do Step 1 (perfilamento)

O Questionário registrava uma linha de exemplo com 14 valores para 16
cabeçalhos, sem dizer se as duas últimas colunas (`RESSARCIMENTO_CUSTO_EMERGENCIAL`,
`RESSARCIMENTO_DIST_IMPL_OP_MNT`) vinham vazias na origem ou se o cabeçalho
tinha coluna a mais. Perfilando o recurso `encargo_ess_ancilar_2026` real em
14/09/2026: **as 7 linhas do arquivo têm as 16 colunas preenchidas**, nenhuma
vazia — o exemplo do Questionário não reflete o arquivo atual. A fixture de
teste continua com uma linha com as duas últimas colunas vazias de propósito,
porque a origem já mostrou esse padrão em anos anteriores e o `csv.DictReader`
lida com os dois casos sem quebrar (`numero_ou_nulo(None)` devolve `None`).

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `MES_REFERENCIA` | `data_referencia` | DATE | primeiro dia do mês (`AAAAMM` → `AAAA-MM-01`) |
| `MES_REFERENCIA` | `periodo_apuracao_ccee` | STRING | `AAAAMM` → `AAAA-MM`, **como a CCEE declara** |
| — | `periodo_apuracao` | STRING | derivado de `data_referencia` na Silver |
| `last_modified` do recurso (CKAN) | `versao_publicacao` | DATE | identificador de versão da [ADR 016](../arquitetura/decisoes/016-versionamento-de-recontabilizacao.md) |
| `ENCARGO_CONST_ON` | `encargo_constrained_on` | NUMERIC | R$; vazio → NULL |
| `ENCARGO_CONST_OFF` | `encargo_constrained_off` | NUMERIC | R$; vazio → NULL |
| `OUTROS_SERVICOS_ANCILARES` | `outros_servicos_ancilares` | NUMERIC | R$; vazio → NULL |
| `ENCARGO_CS` | `encargo_cs` | NUMERIC | R$; vazio → NULL |
| `ENCARGO_SEG_ENER` | `encargo_seguranca_energetica` | NUMERIC | R$; vazio → NULL |
| `RECEBIMENTO_ENCARGO_DH` | `recebimento_encargo_dh` | NUMERIC | R$; vazio → NULL |
| `ENCARGO_REST_OP_UNIT_COMT` | `encargo_restricao_operativa_unit_commitment` | NUMERIC | R$; vazio → NULL |
| `ENCARGO_IMPORTACAO` | `encargo_importacao` | NUMERIC | R$; vazio → NULL |
| `RECEBIMENTO_ENCARGO_RESERVA_OP` | `recebimento_encargo_reserva_operativa` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_SERVICOS_ANCILARES` | `ressarcimento_servicos_ancilares` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_CUSTO_OP_MNT_EQUIP` | `ressarcimento_custo_operacao_manutencao_equipamento` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_CUSTO_OP_MNT_EQUIP_CAG` | `ressarcimento_custo_operacao_manutencao_equipamento_cag` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_CUSTO_IMPL_OP_MNT_SEP` | `ressarcimento_custo_implantacao_operacao_manutencao_sep` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_CUSTO_EMERGENCIAL` | `ressarcimento_custo_emergencial` | NUMERIC | R$; vazio → NULL |
| `RESSARCIMENTO_DIST_IMPL_OP_MNT` | `ressarcimento_distribuidora_implantacao` | NUMERIC | R$; vazio → NULL |

Todos os valores são em R$, com ponto decimal na origem. Colunas técnicas do
Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | primeiro dia do mês de referência |
| `submercado` | não | total do mercado, sem submercado |
| `codigo_usina` | não | total do mercado, sem ativo |
| `agente_ccee` | não | total do mercado, sem agente |
| `periodo_apuracao` | sim | derivado |
| `periodo_apuracao_ccee` | **sim** | o que a CCEE declara; a Silver exige que coincida com o derivado |

## Deduplicação e versão

Chave natural: (`periodo_apuracao_ccee`). Vence a **publicação mais recente**
(`versao_publicacao`), e a hora da leitura só desempata leituras da mesma
publicação — opção B da ADR 016.

## Gold

`gold.encargos_setoriais_mensal` — ESS e EER lado a lado, mês a mês, com
`FULL OUTER JOIN` (as duas séries fecham em datas diferentes). Sem KPI
(ADR 012).

## Qualidade e observações

- Valores em R$ com ponto decimal; sem separador de milhar; muitos `0`
  (linha real de julho/2026 tem 6 dos 15 valores zerados).
- `encargo_constrained_on` e `encargo_constrained_off` não podem ser
  negativos (faixa da Silver, issue #110); os demais campos não têm faixa
  documentada pela CCEE.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN) → encargo_ess_ancilar_{ano}.csv
  → gs://<bucket>-raw/ccee/encargo_ess/dt=…/<ingestao_id>.json.gz
    → bronze.ccee_encargo_ess   (append-only, particionado por _ingestao_timestamp)
      → silver.ccee_encargo_ess (QUALIFY por mês, versao_publicacao DESC)
        → gold.encargos_setoriais_mensal
```
