# ADR 013 — Ingestão em lote: sem CDC e sem Dataflow

**Status**: aceito · **Data**: 2026-09-10 · **Complementa** as ADRs
[003](003-framework-de-conectores.md) e [008](008-acesso-a-bancos-relacionais.md)

## Contexto

A revisão arquitetural com o Google (G1) perguntava onde o modelo escreve
código que um serviço gerenciado já resolve, citando Datastream e Dataflow. A
pergunta pesa sobre a Onda 3, cujas fontes — Oracle FMB, MySQL do Portal Alup,
MySQL RDS de Comercialização, SQL Server do Balanço Energético e RM/TOTVS —
são sistemas transacionais.

Havia três caminhos para trazê-las ao Bronze:

1. **Datastream (CDC)** — replicação contínua a partir do log de alterações do
   banco;
2. **Dataflow com o template *JDBC to BigQuery*** — pipeline Java pronto que
   executa uma consulta e grava o resultado, em lote;
3. **conectores Python da ADR 008**, em Cloud Run Job, pelo executor da
   ADR 003.

## Decisão

**Caminho 3.** Toda fonte, inclusive as da Onda 3, entra em lote, por janela,
pelo executor único.

1. **O dado consumido não é transacional.** As fontes da Onda 3 são sistemas
   transacionais, mas o que o DataLake lê delas são recortes consolidados —
   fechamentos, cadastros, posições —, lidos periodicamente. Não há fluxo de
   eventos a capturar. CDC e Dataflow ficam descartados **por falta de caso de
   uso, não por limitação técnica**.
2. **O contrato pede conector Python.** A cláusula 2.2, item 1, exige "Conector
   Python estruturado" para cada fonte. O template JDBC não tem código nosso: a
   fonte que o usasse chegaria à homologação com 6 de 7 componentes.
3. **O template dispensa as garantias da ADR 003**: raw no GCS antes do parsing
   (que viabiliza o reprocessamento), validação Pydantic, colunas técnicas,
   registro em `bronze._execucoes` e ingestão por janela. Ele executa uma
   consulta e grava, por acréscimo ou truncando a tabela.
4. **CDC cobraria da origem e da Alup.** Exigiria que o DBA da Alup ligasse o
   log de alterações (binlog, LogMiner, CDC do SQL Server), com privilégio além
   do somente leitura pedido em A7, e manteria um fluxo ligado 24×7 com custo
   para a contratante.

A rede não distingue as opções: qualquer uma delas precisa da VPN da Alup
ligada a uma VPC. No caminho escolhido, o Cloud Run Job alcança essa VPC por
saída direta (*Direct VPC egress*), em `infra/modules/networking`.

### A janela nas fontes internas

A regra 3 continua valendo, com uma precisão: a janela filtra pela **data de
referência do negócio** (competência, data do fechamento), não por coluna de
última alteração. Tabela pequena de cadastro é lida inteira a cada execução,
tendo a janela como data de referência do retrato; o Bronze acumula as cópias
e a Silver deduplica (regra 4).

### Linhagem da origem até o Bronze

O Knowledge Catalog registra sozinho a linhagem de BigQuery e Dataform, mas não
enxerga o que acontece antes do Bronze. Para cobrir esse trecho, o executor
emite **um evento OpenLineage por execução** (`ProcessOpenLineageRunEvent`),
com a origem em *namespace* próprio e o destino na tabela Bronze. É um ponto só,
em `src/core/`, que vale para as 13 fontes — HTTP, banco e planilha.

Falha ao emitir linhagem não falha a ingestão: vira aviso no log. Linhagem é
metadado; o dado já está no Bronze.

### Válvula de escape

A ADR 008 registra que o executor mantém em memória as linhas da janela. Se o
volume real do FMB não couber num Cloud Run Job nem com janela curta, essa
fonte pode rodar como pipeline Apache Beam **em Python** no Dataflow — o que
continua cumprindo o item 1 da cláusula 2.2. A decisão depende de medição e,
se vier, é ADR próprio.

## Consequências

- A ADR 008 segue integralmente válida; nenhum serviço novo entra na ingestão.
- As APIs do Datastream e do Dataflow não são habilitadas.
- `infra/modules/networking` precisa da VPN e da saída direta para a VPC antes
  da Onda 3 — depende de A7.
- O executor ganha a emissão de linhagem, testada como qualquer outra parte do
  framework.
