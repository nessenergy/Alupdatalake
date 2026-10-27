# Esquema do MySQL Alup (sete tabelas pedidas pela Alupar)

Levantado em **27/10/2026**, em dev, pelo workflow *Testar conexão* com `tabelas` (`alupdata esquema portal-alup`).
Só metadado de `information_schema.columns`: nenhuma linha de dado foi lida. Fonte do pedido: resposta do Leonardo (Alupar)
de 27/10/2026, ponto 5.

## Pontos que mudam o desenho dos conectores

- **Renomeação pendente.** A Alupar disse que `medicao_cinco_minutos_api` passará a `medicao_cinco_minutos_rest` e
  `medicao_cinco_minutos_xml` a `medicao_horaria_soap`. Em 27/10 as duas ainda tinham os nomes antigos. O conector deve ler
  o nome de configuração, e não de constante, e a data da troca precisa ser combinada com a Alupar.
- **Carga incremental.** As duas tabelas de medição devem ser as maiores (leitura de 5 minutos por ponto); o volume não foi medido. A janela de datas do runner mapeia para `datahora`
  (`_api`) e `hora_timestamp` (`_xml`); `updated_at` existe nas duas para capturar correção posterior.
- **Chave composta em `medicao_cinco_minutos_xml`:** `ponto_medicao`, `hora_timestamp`, `tipo_energia` e `subtipo`
  (coluna `id` é `MUL`, não é a chave). A deduplicação da Silver usa essa chave.
- **Colunas JSON** (`invoice.nfe`, `invoice.jsonInfo`, `faturas_processadas.parcelas`): entram como texto na Bronze e são
  tipadas na Silver.
- **Dado pessoal e sensível a tratar antes da Silver:** `cnpj` (`client`, `uc`, `faturas_processadas.cnpjEmpresaDestino`),
  `uc.address`, `uc.vendedor`, e as chaves de arquivo `invoice.s3_key*` e `invoice.barcode`. Decidir com a Alupar o que sobe.
- **Sem coluna de modificação em `client`, `bandeira` e `uc`:** cadastros pequenos, lidos por inteiro a cada execução
  (retrato), como a ANEEL.

Legenda de chave: `PRI` primária, `UNI` única, `MUL` índice não único.

## `bandeira`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `int` | não | PRI |
| `mes` | `varchar(255)` | sim | UNI |
| `bandeira` | `varchar(255)` | não |  |
| `valor` | `double` | não |  |

## `client`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `int` | não | PRI |
| `nickname` | `varchar(255)` | sim |  |
| `corporate_name` | `varchar(255)` | sim |  |
| `cnpj` | `varchar(18)` | não |  |

## `faturas_processadas`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `int` | não | PRI |
| `nome` | `varchar(50)` | não |  |
| `idUc` | `varchar(255)` | não | MUL |
| `idTransacaoFMB` | `varchar(50)` | não |  |
| `idPreFaturaFMB` | `varchar(100)` | não |  |
| `codigoContrato` | `varchar(50)` | sim |  |
| `idErpEmpresaOrigem` | `varchar(10)` | sim |  |
| `cnpjEmpresaDestino` | `varchar(20)` | sim |  |
| `mesSuprimento` | `varchar(7)` | sim |  |
| `quantidade` | `decimal(15,4)` | sim |  |
| `preco` | `decimal(15,4)` | sim |  |
| `valorTotal` | `decimal(15,2)` | sim |  |
| `condicaoPagamentoErp` | `varchar(20)` | sim |  |
| `naturezaContrato` | `varchar(50)` | sim |  |
| `consumidorFinal` | `tinyint(1)` | sim |  |
| `numeroParcelas` | `int` | sim |  |
| `tags` | `varchar(100)` | sim |  |
| `parcelas` | `json` | sim |  |
| `dataVencimento` | `date` | sim |  |
| `statusProcessamento` | `varchar(20)` | sim |  |
| `createdAt` | `timestamp` | sim |  |
| `updatedAt` | `timestamp` | sim |  |
| `erros` | `varchar(255)` | sim |  |
| `idContrato` | `varchar(10)` | não |  |
| `ordemCadastrada` | `varchar(10)` | sim |  |
| `estado` | `varchar(100)` | sim |  |
| `desconto` | `decimal(15,2)` | sim |  |
| `submercado` | `varchar(100)` | sim |  |

## `invoice`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `int` | não | PRI |
| `client_id` | `int` | não | MUL |
| `uc_id` | `varchar(255)` | não | MUL |
| `month` | `varchar(7)` | não |  |
| `consumption` | `decimal(10,3)` | não |  |
| `value` | `decimal(10,2)` | não |  |
| `tax` | `decimal(10,2)` | não |  |
| `status` | `int` | não |  |
| `due_date` | `date` | sim |  |
| `nfe` | `json` | sim |  |
| `jsonInfo` | `json` | sim |  |
| `s3_key` | `varchar(255)` | sim |  |
| `barcode` | `text` | sim |  |
| `s3_key_report` | `varchar(255)` | sim |  |
| `s3_key_xml` | `varchar(255)` | sim |  |
| `s3_key_danfe` | `varchar(255)` | sim |  |
| `updated_at` | `datetime` | sim |  |
| `created_at` | `datetime` | sim |  |

## `medicao_cinco_minutos_api`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `int` | não | PRI |
| `uc` | `varchar(30)` | não |  |
| `ponto_medicao` | `varchar(30)` | não | MUL |
| `datahora` | `datetime` | não | MUL |
| `consumo_ativo` | `decimal(16,6)` | sim |  |
| `consumo_reativo` | `decimal(16,6)` | sim |  |
| `tipo_horario` | `enum('PONTA','FORA_PONTA')` | não |  |
| `status` | `enum('CONSISTIDA','ESTIMADA')` | não |  |
| `data_atualizacao` | `datetime` | sim |  |
| `created_at` | `datetime` | não |  |
| `updated_at` | `datetime` | não |  |

## `medicao_cinco_minutos_xml`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `bigint` | não | MUL |
| `ponto_medicao` | `varchar(50)` | não | PRI |
| `hora_timestamp` | `datetime` | não | PRI |
| `tipo_energia` | `char(1)` | não | PRI |
| `data` | `date` | não |  |
| `hora` | `time` | não |  |
| `subtipo` | `enum('HCC','HCI','HEC','HEI','HIF','HE','HR','HEH','HEIH','HEFFC','HEFFRC','HEFFI','HEFFRI')` | não | PRI |
| `ativa_geracao` | `decimal(15,4)` | sim |  |
| `reativa_geracao` | `decimal(15,4)` | sim |  |
| `ativa_consumo` | `decimal(15,4)` | sim |  |
| `reativa_consumo` | `decimal(15,4)` | sim |  |
| `agente` | `varchar(50)` | não |  |
| `created_at` | `datetime` | não |  |
| `updated_at` | `datetime` | não |  |

## `uc`

| Coluna | Tipo | Nulo | Chave |
|---|---|---|---|
| `id` | `varchar(255)` | não | PRI |
| `client_id` | `int` | não | MUL |
| `contrato` | `varchar(100)` | não |  |
| `cnpj` | `varchar(18)` | não |  |
| `state` | `char(2)` | não |  |
| `contract_start_date` | `date` | não |  |
| `submarket` | `varchar(25)` | não |  |
| `supplier` | `varchar(50)` | não |  |
| `subgroup` | `varchar(5)` | não |  |
| `modality` | `varchar(15)` | não |  |
| `contracted_demand_peak` | `decimal(15,2)` | não |  |
| `contracted_demand_off_peak` | `decimal(15,2)` | não |  |
| `scde_code` | `varchar(100)` | sim |  |
| `contractual_modality` | `varchar(25)` | não |  |
| `supply_start_date` | `date` | não |  |
| `supply_end_date` | `date` | não |  |
| `guaranteed_discount_percentage` | `decimal(5,2)` | não |  |
| `base_price` | `decimal(15,2)` | não |  |
| `base_date` | `date` | não |  |
| `adjustment_date` | `date` | não |  |
| `adjustment_index` | `varchar(10)` | não |  |
| `losses` | `decimal(15,2)` | sim |  |
| `proinfa` | `decimal(5,2)` | sim |  |
| `included_charges` | `varchar(25)` | não |  |
| `icms` | `decimal(5,2)` | sim |  |
| `migration` | `varchar(25)` | não |  |
| `cod_agente` | `int` | sim |  |
| `due_day` | `int` | sim |  |
| `vendedor` | `varchar(50)` | sim |  |
| `supply_duration` | `decimal(10,2)` | sim |  |
| `total_energy_volume` | `decimal(15,2)` | sim |  |
| `codigo_ativo` | `varchar(25)` | sim |  |
| `address` | `varchar(255)` | sim |  |
| `adjusted_price` | `decimal(15,2)` | sim |  |
| `ccee_last_date` | `datetime` | sim |  |
| `api_ccee` | `smallint` | sim |  |
| `condicao_pagamento` | `varchar(10)` | sim |  |
| `id_contrato` | `int` | não | UNI |
| `reforma_tributaria` | `varchar(100)` | sim |  |
| `id_migracao_ccee` | `varchar(60)` | sim |  |
| `cod_agente_concessionaria` | `varchar(20)` | sim |  |
| `status_do_contrato` | `varchar(30)` | sim |  |
| `id_new` | `varchar(100)` | sim |  |
| `status_faturamento` | `varchar(100)` | sim |  |
| `interesse_em_renovar` | `varchar(30)` | sim |  |
| `meses_renovacao` | `int` | sim |  |
| `renovacao_distrato` | `varchar(100)` | sim |  |
