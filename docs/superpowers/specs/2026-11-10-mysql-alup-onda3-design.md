# MySQL Alup (Onda 3): cinco tabelas de cadastro e faturamento — desenho

**Data:** 10/11/2026 · **Frente:** B, Onda 3 · **Base:** [`mysql_alup_esquema.md`](../../dicionario-dados/mysql_alup_esquema.md) (levantado em 27/10, só metadado), [ADR 008](../../arquitetura/decisoes/008-acesso-a-bancos-relacionais.md) e [ADR 024](../../arquitetura/decisoes/024-rede-das-fontes-internas.md)

## Escopo

Entram `uc`, `client`, `invoice`, `faturas_processadas` e `bandeira`. **Ficam fora** `medicao_cinco_minutos_api` (será `medicao_cinco_minutos_rest`) e `medicao_cinco_minutos_xml` (será `medicao_horaria_soap`): a data da renomeação é desconhecida.

**Pendência registrada, com proposta.** Quando a Alupar informar a data, os dois conectores de medição entram com o **nome da tabela vindo de configuração**, não de constante: `Settings.mysql_alup_tabela_medicao_rest` e `..._soap`, com o nome antigo como padrão até a troca. O conector grava o nome lido no `_schema_versao`, para o Bronze mostrar de qual tabela veio cada lote. A janela mapeia para `datahora` (`_rest`) e `hora_timestamp` (`_soap`); `updated_at` captura correção. Chave da `_soap`: `ponto_medicao + hora_timestamp + tipo_energia + subtipo`. Nenhuma linha dessas tabelas é lida até lá. O volume é a maior incógnita do conjunto (5 minutos por ponto) e fica como pergunta 8.

## Origem e acesso

- Segredo `alupdata-portal-alup-dsn` (já existe em `infra/modules/secrets`), lido por `src/core/banco.py::abrir_conexao("portal-alup")`. O rótulo do conector usa `portal_alup` (sublinhado), porque o rótulo vira nome de tabela e de job.
- Os cinco conectores compartilham uma base (`src/conectores/mysql_alup.py`): monta o `SELECT` a partir de constantes da classe (nenhum texto externo vira SQL), passa a janela como parâmetro e usa `consultar()`, que já recusa tudo que não seja leitura. Cada tabela só declara colunas, coluna de data, modelo Pydantic e chave.
- O `SELECT` dá apelido em `snake_case` a cada coluna (`idUc AS id_uc`). `consultar()` devolve nomes em minúsculas, e sem apelido `idUc` viraria `iduc`.

## Modo de extração, por tabela

| Tabela | Coluna de data da janela | Modo | Chave natural (Silver) |
|---|---|---|---|
| `invoice` | `COALESCE(updated_at, created_at)` | incremental: `>= inicio 00:00` e `< fim+1 00:00` | `id` |
| `faturas_processadas` | `COALESCE(updatedAt, createdAt)` | incremental, como acima | `id` |
| `uc` | nenhuma | retrato completo, idempotente | `id` (`id_contrato` é UNI, serve de conferência) |
| `client` | nenhuma | retrato completo | `id` |
| `bandeira` | nenhuma | retrato completo | `id` (`mes` é UNI) |

**Por que retrato nos três cadastros.** Não há coluna de modificação (`ccee_last_date` em `uc` marca a última sincronização com a CCEE, não a edição da linha), são cadastros pequenos e uma carga completa repetida é idempotente: a Bronze acumula um retrato por execução e a Silver fica com a versão mais recente de cada `id`. Mesmo precedente do `aneel_siga`. A janela é aceita e ignorada, e `data_referencia` é `janela.fim`: o conector não consulta o relógio (regra 3), e reprocessar é passar outra janela.

**Incremental por `updated_at`.** A janela de 7 dias do agendamento reabre o que mudou. No reprocesso de janela antiga, a Silver ordena por `updated_at DESC` (nulo por último) antes de `_ingestao_timestamp`, para uma versão velha recarregada não vencer a nova. Datas são `datetime` sem fuso; o conector não converte (pergunta 3).

## Dimensões comuns na Silver

| Dimensão | `uc` | `client` | `invoice` | `faturas_processadas` | `bandeira` |
|---|---|---|---|---|---|
| `data_referencia` | `janela.fim` do retrato | idem | 1º dia de `month` (`SAFE.PARSE_DATE('%Y-%m')`; `NULL` se o formato for outro) | 1º dia de `mes_suprimento`, idem | 1º dia de `mes`, idem (pergunta 4) |
| `submercado` | `submarket` como veio | `NULL` | `NULL` | `submercado` como veio | `NULL` |
| `codigo_usina` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |
| `agente_ccee` | `NULL` (pergunta 5) | `NULL` | `NULL` | `NULL` | `NULL` |
| `periodo_apuracao` | de `data_referencia` | idem | de `data_referencia` | de `data_referencia` | de `data_referencia` |
| `periodo_apuracao_ccee` | `NULL` | `NULL` | `NULL` | `NULL` | `NULL` |

A fonte é comercial (consumidor e fatura), não tem usina. O valor de `submercado` fica como a origem escreve; a normalização para `N/NE/S/SE` espera a pergunta 6, para não inventar mapa.

## Dado pessoal e sensível

Princípio do `hubspot_negocios`: **sem finalidade, o campo não é lido.** A Bronze é append-only e o raw vai para o GCS; o que não entra no `SELECT` não tem como vazar nem como ser apagado depois.

| Campo | Tratamento |
|---|---|
| `uc.address`, `uc.vendedor` | **não lidos.** Endereço pode ser de pessoa física; o vendedor é pessoa natural. Nenhuma Gold os usa. |
| `invoice.barcode`, `invoice.s3_key`, `s3_key_report`, `s3_key_xml`, `s3_key_danfe` | **não lidos.** Código de barras paga fatura de terceiro; a chave de objeto S3 dá endereço de arquivo (a DANFE e o XML levam dado do destinatário). Sem finalidade analítica. |
| `invoice.nfe`, `invoice.jsonInfo` (JSON) | **não lidos até a Alupar dizer o que há dentro** (pergunta 2). Nota fiscal e JSON livre costumam trazer nome, endereço e documento do destinatário; tipar na Silver uma estrutura desconhecida seria adivinhar. |
| `faturas_processadas.nome` | **não lido** até a Alupar dizer o que é (nome do cliente, do arquivo?) — pergunta 2. |
| `cnpj` (`client`, `uc`) e `faturas_processadas.cnpj_empresa_destino` | **lidos e mantidos** na Bronze e na Silver: é a chave de cruzamento com o cadastro da CCEE, e CNPJ é dado de pessoa jurídica. **Não sobem para a Gold**, que agrega por `client_id`. Se houver empresário individual na base, passa a ser dado pessoal (pergunta 1). |
| `faturas_processadas.parcelas` (JSON) | lido como texto na Bronze, valor financeiro sem identificação; a Silver o expõe como `STRING`. |
| `faturas_processadas.erros`, `tags` | lidos; texto livre do ERP, sem evidência de dado pessoal. Se aparecer, entra na pergunta 1. |
| `nickname`, `corporate_name` | lidos: nome empresarial do cliente, necessário para a leitura da diretoria. Mesma ressalva do CNPJ. |

A Gold nunca expõe CNPJ. O RIPD e o RoPA da Onda 4 devem listar `cnpj` como identificador de pessoa jurídica, com a ressalva do MEI.

## Silver e Gold

Silver: `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ...) = 1`, `uniqueKey` e `nonNull` em `id`, mais `rowConditions` conservadoras (o teste de infra exige uma por Silver): `id > 0`, demanda contratada não negativa e `state` com 2 letras em `uc`, `valor >= 0` em `bandeira`, parcelas não negativas em `faturas_processadas`. Faixa de consumo e valor em `invoice` fica de fora: crédito e estorno podem ser negativos e uma asserção falsa barra a Gold.

Gold, todas tabelas (ADR 012):

- `cadastro_uc_cliente` (`uc` + `client`): uma linha por unidade consumidora, com cliente, subgrupo, modalidade, demanda contratada, vigência e preço-base. Sem CNPJ.
- `fatura_mensal_cliente` (`invoice` + `client` + `bandeira`): por cliente e mês, consumo, valor, imposto e faturas. A `bandeira` entra por `periodo_apuracao` das duas Silver, que é o mês lido com `SAFE.PARSE_DATE('%Y-%m')`; se o formato de `mes` não for esse, a coluna fica `NULL`, sem erro e sem casar errado (pergunta 4).
- `faturamento_mensal_contrato` (`faturas_processadas`): por mês de suprimento, natureza e submercado, quantidade e valor total.

## Agendamento e rede

Um job por tabela em `infra/modules/scheduler`, e os cinco em `conectores_rede_interna` de `dev.tfvars`: o MySQL Alup sai pelo IP fixo do Cloud NAT da `vpc-dr-prd` (ADR 024). `invoice` e `faturas_processadas`: diário, `ultimos_dias = 7`; `uc` e `client`: diário, retrato; `bandeira`: semanal. Limites de silêncio: 26 h os diários, 180 h o semanal.

## Riscos

1. **Linha apagada na origem continua na Silver.** O retrato com `QUALIFY` não sabe de exclusão. Se a Alupar apagar `uc`, a linha segue vigente. Mitigação fora desta entrega: coluna `no_ultimo_retrato` na Silver, a combinar depois do primeiro dado real (pergunta 7).
2. **`updated_at` nulo.** Linha com `updated_at` e `created_at` nulos nunca entra na janela. Sem dado real não se mede; a conferência de contagem contra o banco vem na primeira carga.
3. **Fuso.** `datetime` e `timestamp` sem fuso podem estar em UTC ou em horário de Brasília; a diferença desloca até um dia a borda da janela, coberta pela folga dos 7 dias.
4. **Volume desconhecido.** Nenhuma contagem foi feita (só metadado). `memoria` e `timeout` ficam no padrão e são revistos na primeira execução, como se fez com a CCEE.
5. **Sem dado real, o contrato é o dicionário.** Tipos e anulabilidade vêm de `information_schema`; o teste de integração (pulado sem credencial) é o que confere na primeira carga.

## Perguntas para a Alupar

1. Há empresário individual (MEI) ou pessoa física entre `client`, `uc` e `faturas_processadas`? O CNPJ pode subir como está?
2. O que `invoice.nfe`, `invoice.jsonInfo` e `faturas_processadas.nome` guardam (estrutura e campos)? Algum identifica o destinatário?
3. `updated_at` e `createdAt` são mantidos pelo banco (`ON UPDATE`) ou pela aplicação? Em que fuso? Pode haver linha com os dois nulos?
4. Qual o formato de `bandeira.mes` (`2026-10`, `10/2026`, nome do mês)? Os valores de `bandeira` e a unidade de `valor` (R$/100 kWh)?
5. Qual coluna de `uc` é o agente CCEE: `cod_agente`, `cod_agente_concessionaria` ou `codigo_ativo`?
6. Valores de `uc.submarket` e `faturas_processadas.submercado`: siglas (`SE`) ou nomes?
7. A Alupar apaga linha de `uc`, `client` ou `bandeira`, ou só altera?
8. Volume aproximado (linhas) de cada uma das sete tabelas, e a data da renomeação das duas de medição.
