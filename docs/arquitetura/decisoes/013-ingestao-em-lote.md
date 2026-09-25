# ADR 013 — Ingestão em lote: sem CDC e sem Dataflow

**Status**: aceito · **Data**: 2026-09-10 · **Complementa** as ADRs
[003](003-framework-de-conectores.md) e [008](008-acesso-a-bancos-relacionais.md) ·
**Revisada** em 2026-09-11 (rede e janela de extração das fontes internas)

## Contexto

A revisão arquitetural com o Google (G1) perguntava onde o modelo escreve
código que um serviço gerenciado já resolve, citando Datastream e Dataflow. A
pergunta pesa sobre a Onda 3, cujas fontes — Oracle FMB, MySQL do Portal Alup,
MySQL RDS de Comercialização, SQL Server do Balanço Energético e RM/TOTVS —
são sistemas transacionais.

Na reunião de 10/09 com o Google, o template *JDBC to BigQuery* foi bem
recebido como forma de dispensar código nas fontes relacionais. A decisão
abaixo foi confirmada em 11/09, depois de pesada contra a cláusula 2.2.

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

O *replay* (`alupdata reprocessar-raw`) não emite — ele lê o raw já arquivado e
não toca a origem; a aresta origem → Bronze é a da ingestão que produziu
aquele raw (sujeita à retenção descrita no adendo da ADR 014).

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

---

## Revisão de 2026-09-11 — rede e janela das fontes internas

As respostas da Alup ao [Questionário de Gaps](../../questionario-gaps.md), em
11/09, mudam duas premissas desta ADR. A decisão — lote, por janela, pelo
executor único — não muda.

### O MySQL RDS de Comercialização dispensa VPN (C8)

O banco está na AWS, em Norte da Virgínia (`us-east-1`), e **não precisa de
peering nem de VPN**; o acesso será concedido pelo Leonardo. A frase "qualquer
uma delas precisa da VPN da Alup ligada a uma VPC", acima, deixa de valer para
essa fonte. O Balanço Energético, que saiu do SQL Server (C11, adendo de 11/09
da [ADR 008](008-acesso-a-bancos-relacionais.md)), também está no MySQL RDS.

Sem VPN, a conexão atravessa a internet até o endpoint do RDS. Duas
consequências:

1. **IP de saída fixo, se a liberação for por lista de IPs — a confirmar com o
   Leonardo.** O Cloud Run não tem IP de saída estável. Se o acesso ao RDS
   exigir lista de origens, o Cloud Run Job precisa sair pela VPC (*Direct VPC
   egress*, já previsto em `infra/modules/networking`) e por um **Cloud NAT com
   IP reservado**, declarado em `infra/` (regra 5). Se a liberação for por
   outro meio, nada disso entra.
2. **TLS na conexão.** Credencial e dado passam pela internet. Hoje `banco.py`
   não repassa opção de TLS ao `pymysql` — a parte de consulta da DSN é
   ignorada. Habilitar e exigir TLS no caminho `mysql://`, com teste, vem antes
   da primeira leitura do RDS.

### O caminho de rede do Oracle FMB segue a confirmar (C5)

> **25/09/2026:** decidido na [ADR 024](024-rede-das-fontes-internas.md): VPC
> compartilhada da Alupar, com o FMB alcançado pelo FortiGate dela e o MySQL
> RDS pelo IP fixo do Cloud NAT.

A Alup liberou acesso somente às views e informou host, porta e schema —
recebidos em 11/09 e guardados fora do repositório, na DSN do Secret Manager
(regra 2). Não informou se o banco é alcançável sem VPN. Até isso ser
confirmado, a VPN ligada à VPC continua sendo a premissa para o FMB.

O mesmo vale para o Portal Alup — cujas bases (Aurora, DynamoDB e S3, C6)
indicam que também está na AWS — e para o RM/TOTVS (C7, até 25/09).

### Janela de extração: das 22h às 6h (C9)

Os sistemas internos só podem ser lidos das 22h às 6h. É janela de **horário de
execução**, e não se confunde com a janela de datas da regra 3.

- O agendamento das fontes da Onda 3 cai dentro dela. O Cloud Scheduler agenda
  com fuso explícito; a resposta não informou o fuso, e supor o de Brasília
  precisa de confirmação.
- A execução do Dataform vem depois da ingestão (ADR 012), também dentro da
  janela ou logo após o seu fim.
- Consequência para o consumo: dado de sistema interno chega à Gold no máximo
  uma vez por dia, com a leitura da noite anterior. O "quase em tempo real"
  pedido em A1 e A2 vale, para essas fontes, como atualização diária —
  expectativa a alinhar com a Alup.

### Consequências da revisão

- `infra/modules/networking`: sem VPN para o MySQL RDS; Cloud NAT com IP
  reservado só se a liberação for por lista de IPs. VPN segue prevista para o
  FMB até confirmação.
- `src/core/banco.py`: TLS no caminho `mysql://`, com teste, antes da Onda 3.
  **Feito em 25/09**: toda conexão `mysql://` exige TLS com certificado e host
  verificados; a CA vem de `?ssl_ca=<caminho>` na DSN, e `?tls=0` só é aceito
  para banco local. Falta, para a primeira leitura do RDS, pôr na imagem o
  pacote público de CAs do RDS e apontar a DSN para ele.
- Para o MySQL RDS, a dependência A7 deixa de ser VPN e passa a ser credencial
  somente leitura e liberação de acesso pelo Leonardo.
