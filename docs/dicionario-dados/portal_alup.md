# MySQL Alup — cadastro e faturamento do varejo (cinco tabelas)

| Item | Valor |
|---|---|
| Fonte | MySQL do Portal Alup, base da DSN do secret `alupdata-portal-alup-dsn` |
| Contrato de colunas | [`mysql_alup_esquema.md`](mysql_alup_esquema.md), levantado em 27/10/2026 (só metadado) |
| Desenho | [`2026-11-10-mysql-alup-onda3-design.md`](../superpowers/specs/2026-11-10-mysql-alup-onda3-design.md) |
| Onda | 3, banco relacional (ADR 008); rede pela ADR 024, saída pelo Cloud NAT da `vpc-dr-prd` |
| Conectores | `portal_alup_client`, `portal_alup_uc`, `portal_alup_bandeira`, `portal_alup_invoice`, `portal_alup_faturas_processadas` (`src/conectores/mysql_alup.py`) |
| Dono do dado | Alupar |
| Credencial | DSN no Secret Manager; nada em código, log ou erro |
| Estado | implementado contra o dicionário, **nenhuma linha lida**: tipos e anulabilidade vêm de `information_schema` e a primeira carga os confere |

Fora desta entrega: `medicao_cinco_minutos_api` (será `_rest`) e `medicao_cinco_minutos_xml` (será `medicao_horaria_soap`),
até a Alupar informar a data da renomeação. Proposta no spec: o nome da tabela passa a vir de configuração.

## Modo de extração e deduplicação

| Rótulo | Tabela de origem | Janela | Chave da Silver | Frequência |
|---|---|---|---|---|
| `portal_alup_client` | `client` | retrato completo; `data_referencia` = fim da janela | `id` | diária |
| `portal_alup_uc` | `uc` | retrato completo | `id` | diária |
| `portal_alup_bandeira` | `bandeira` | retrato completo | `id` | semanal |
| `portal_alup_invoice` | `invoice` | `COALESCE(updated_at, created_at)` em `[inicio, fim+1)` | `id` | diária, 7 dias |
| `portal_alup_faturas_processadas` | `faturas_processadas` | `COALESCE(updatedAt, createdAt)` em `[inicio, fim+1)` | `id` | diária, 7 dias |

Cadastro sem coluna de modificação é lido inteiro: carga repetida é idempotente, porque a Bronze acumula um retrato por
execução e a Silver fica com a versão mais recente de cada `id`. Nos dois fatos, a Silver ordena pela modificação na
origem antes da ingestão, para o reprocesso de janela antiga não reverter uma linha.

## Dado pessoal e sensível

| Campo | Tratamento |
|---|---|
| `uc.address`, `uc.vendedor` | não lidos |
| `invoice.barcode`, `s3_key`, `s3_key_report`, `s3_key_xml`, `s3_key_danfe` | não lidos |
| `invoice.nfe`, `invoice.jsonInfo`, `faturas_processadas.nome` | não lidos até a Alupar dizer o que há dentro |
| `cnpj` (`client`, `uc`), `cnpj_empresa_destino` | lidos; ficam na Bronze e na Silver; a Gold não os expõe |

## Linhagem e campos

Todas as Bronze acrescentam `_ingestao_id`, `_ingestao_timestamp`, `_fonte` e `_schema_versao`; são particionadas por
`DATE(_ingestao_timestamp)`. Onde o nome muda, a coluna da origem vem entre parênteses. Tipos: `int` → `INT64`,
`varchar` → `STRING`, `decimal` → `NUMERIC`, `date` → `DATE`, `datetime`/`timestamp` → `DATETIME` (sem fuso), `json` →
`STRING`, `tinyint(1)` → `BOOL`.

### `client` → `bronze.portal_alup_client` → `silver.portal_alup_client`

`id`, `nickname`, `corporate_name`, `cnpj` como na origem, mais `data_referencia` (fim da janela). Cluster: `id`.
Gold: `cadastro_uc_cliente` (nome do cliente) e `fatura_mensal_cliente`.

### `uc` → `bronze.portal_alup_uc` → `silver.portal_alup_uc`

Todas as colunas da origem com o nome original (já em `snake_case`), **exceto** `address` e `vendedor`, mais
`data_referencia`. Cluster: `client_id`, `id`. Na Silver, `submarket` também aparece como `submercado`, sem mapa para
`N/NE/S/SE` (pergunta 6 do spec). Gold: `cadastro_uc_cliente`, uma linha por UC com o cliente, a demanda contratada, o
preço-base e a vigência.

### `bandeira` → `bronze.portal_alup_bandeira` → `silver.portal_alup_bandeira`

`id`, `mes`, `bandeira`, `valor` (`double` → `NUMERIC`). Na Silver, `data_referencia` é o 1º dia de `mes` lido como
`YYYY-MM` (`SAFE.PARSE_DATE`: formato diferente vira `NULL`, sem erro) e a data do retrato fica em `data_retrato`.
Gold: `fatura_mensal_cliente` (bandeira do mês, por `periodo_apuracao`).

### `invoice` → `bronze.portal_alup_invoice` → `silver.portal_alup_invoice`

`id`, `client_id`, `uc_id`, `month`, `consumption`, `value`, `tax`, `status`, `due_date`, `updated_at`, `created_at`.
Cluster: `client_id`, `month`. Silver: `data_referencia` e `periodo_apuracao` a partir de `month`.
Gold: `fatura_mensal_cliente`, por cliente e mês: faturas, consumo, valor, imposto e bandeira.

### `faturas_processadas` → `bronze.portal_alup_faturas_processadas` → `silver.portal_alup_faturas_processadas`

| Origem | Bronze / Silver |
|---|---|
| `idUc`, `idTransacaoFMB`, `idPreFaturaFMB` | `id_uc`, `id_transacao_fmb`, `id_pre_fatura_fmb` |
| `codigoContrato`, `idErpEmpresaOrigem`, `cnpjEmpresaDestino` | `codigo_contrato`, `id_erp_empresa_origem`, `cnpj_empresa_destino` |
| `mesSuprimento` | `mes_suprimento` (Silver: `data_referencia` e `periodo_apuracao`) |
| `quantidade`, `preco`, `valorTotal`, `desconto` | `quantidade`, `preco`, `valor_total`, `desconto` |
| `condicaoPagamentoErp`, `naturezaContrato`, `consumidorFinal`, `numeroParcelas` | `condicao_pagamento_erp`, `natureza_contrato`, `consumidor_final` (`BOOL`), `numero_parcelas` |
| `parcelas` (`json`) | `parcelas`, texto JSON, estrutura não tipada |
| `dataVencimento`, `statusProcessamento`, `createdAt`, `updatedAt` | `data_vencimento`, `status_processamento`, `created_at`, `updated_at` |
| `erros`, `idContrato`, `ordemCadastrada`, `estado`, `submercado`, `tags` | mesmos nomes em `snake_case` |

Cluster: `mes_suprimento`, `id_uc`. Gold: `faturamento_mensal_contrato`, por mês, natureza, submercado e status.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | retrato: fim da janela; fatos e bandeira: 1º dia do mês da linha |
| `submercado` | `uc` e `faturas_processadas`, como a origem escreve | sem mapa para siglas; pergunta 6 |
| `codigo_usina` | não | fonte comercial, sem usina |
| `agente_ccee` | não | `cod_agente`, `cod_agente_concessionaria` e `codigo_ativo` sem significado confirmado; pergunta 5 |
| `periodo_apuracao` | sim | de `data_referencia` |
| `periodo_apuracao_ccee` | não | a origem não declara |

## Perguntas em aberto para a Alupar

As oito do spec (seção "Perguntas para a Alupar"): MEI no CNPJ; conteúdo de `nfe`, `jsonInfo` e `nome`; quem mantém
`updated_at` e em que fuso; formato de `bandeira.mes`; coluna do agente CCEE; valores de submercado; se há exclusão na
origem; volume e data da renomeação das tabelas de medição.
