# Política de retenção de dados da plataforma AlupData — proposta

**Versão** 0.2 · **Data** 2026-09-11 · **Situação**: critérios da Alup de 11/09
incorporados; aguarda aprovação formal da Alup (controladora) e da encarregada

Responde às perguntas F3 e G5 do [Questionário de Gaps](../questionario-gaps.md)
e trata os riscos R02 e R08 do [RIPD](ripd.md). Base: princípio da necessidade
(LGPD, art. 6º, III), término do tratamento (arts. 15 e 16) e cláusula 8.3 do
contrato CPS-01025/2026.

## Critérios da Alup (11/09/2026)

| Pergunta | Resposta |
|---|---|
| F3 | **No mínimo 5 anos para todos os dados.** Exceções: consumo dos clientes, 5 anos na Bronze e até 10 anos na Gold, já em bases mensais; dados públicos do ONS e da CCEE acumulados, sem perder o passado — os muito pesados (geração horária por usina do SIN e *curtailment* semi-horário por usina do SIN) podem ficar só na Gold, como médias mensais, a partir do 6º ano |
| G5 | A primeira carga traz todo o histórico existente, independentemente do tamanho; **a retenção passa a contar a partir de 2027** |
| E4 | Três projetos: `dev`, `hml` e `prod` |

## Princípios

1. **Mínimo de 5 anos, contados a partir de 01/01/2027.** Vale para todo dado,
   inclusive o histórico que a primeira carga trouxer: o que chegar em 2026
   conta como se tivesse chegado em 01/01/2027. Onde a Alup não pediu prazo
   maior, o dado sai ao fim do mínimo — dado sem finalidade não fica
   (art. 6º, III).
2. **O prazo vale para `prod`.** É onde fica o dado oficial. `dev` e `hml`
   guardam cópia para desenvolver e homologar, com prazo curto.
3. **Nada sai da Bronze sem estar agregado.** Onde a Bronze expira e a Gold
   fica — consumo por cliente e públicos pesados —, a Gold é incremental e
   protegida contra recálculo total; não depende de a Bronze continuar lá.
4. **Tudo declarado no repositório.** Bucket, datasets e logs em `infra/`
   (regra 5); expiração de tabela junto do DDL, em `definitions/` (ADR 012).
   Prazo que não está no repositório não está valendo.

## Prazos propostos para `prod`

| Onde | Conteúdo | Prazo | Como se aplica |
|---|---|---|---|
| Bucket raw — versão atual | Todas as fontes | **5 anos**, contados de 2027. Classe STANDARD até 90 dias, COLDLINE dos 90 aos 365 dias, ARCHIVE depois | Ciclo de vida por idade: duas mudanças de classe e uma exclusão aos 1.826 dias, ativada em 01/01/2032 |
| Bucket raw — versões antigas | Todas | 30 dias depois de deixar de ser a atual | Ciclo de vida para versões não atuais |
| Bronze — regra geral | Hubspot, sistemas internos, planilhas, BBCE, TempoOK e `bronze._execucoes` | **5 anos**, contados de 2027 | Expiração de partição de 1.826 dias em cada tabela, ativada em 01/01/2032 |
| Bronze — consumo por cliente | Consumo realizado por cliente, extraído da CCEE | **5 anos**, contados de 2027 | Igual à regra geral |
| Gold — consumo por cliente | Consumo mensal por cliente | **10 anos**, contados de 2027 | Tabela incremental protegida, particionada por mês de referência; expiração de partição de 3.653 dias, ativada em 01/01/2037 |
| Bronze — públicos pesados | Geração horária por usina do SIN; *curtailment* semi-horário por usina do SIN | **5 anos**, contados de 2027; depois, só a Gold mensal | Ver [Públicos pesados](#públicos-pesados) |
| Gold — públicos pesados | Médias mensais das duas tabelas acima | **Sem expiração** | Tabela incremental protegida |
| Bronze — demais públicos | ONS, CCEE pública, ANEEL, BCB, IBGE | **Sem expiração** | — |
| Silver | Views | Não guarda dado | — |
| Gold recalculada | Demais tabelas Gold (ADR 012) | Segue a Bronze de origem: é recalculada a cada execução | — |
| Dataset `qualidade` | Resultado das *assertions* do Dataform | 90 dias | Expiração padrão do dataset. É evidência de qualidade, recalculável, não dado de negócio |
| Dataset `faturamento` | *Billing export* | Sem expiração | Histórico de fatura não se recupera (ADR 007) |
| Knowledge Catalog | Metadados, linhagem, perfil | Enquanto o ativo catalogado existir | — |
| Cloud Logging, bucket padrão | Logs de execução | 30 dias, padrão do serviço | — |
| Log de auditoria de acesso a dados (RIPD, R07) | Quem leu e quem gravou | **1 ano** | Bucket de log dedicado, com retenção de 365 dias, e roteamento dos logs de acesso a dados para ele |

**Dois enquadramentos a confirmar pela Alup.** O critério da pergunta F3 cita
como públicos o ONS e a CCEE. Por isso:

- **BBCE e TempoOK** ficam na regra geral: são dado de mercado sem dado
  pessoal, mas licenciado, e o contrato de licença pode limitar o que se guarda.
  Se a licença permitir, a Alup pode passá-los para "demais públicos";
- **dados internos sem dado pessoal** — balanço energético, premissas de GSF e
  de preço — também ficam na regra geral e saem aos 5 anos. Se a Alup quiser a
  série longa, entram na mesma exceção dos públicos.

### Como "contados a partir de 2027" se implementa

A expiração do BigQuery e o ciclo de vida do Cloud Storage contam a idade a
partir da data da partição ou da criação do objeto. Um prazo de 5 anos
declarado hoje apagaria em 2031 a primeira carga, feita em 2026 — antes do
prazo pedido.

A solução é **ativar cada regra na primeira data de vencimento**: 01/01/2032
para os prazos de 5 anos e 01/01/2037 para o de 10 anos. Nessa data, o que é
anterior a 2027 vence de uma vez, como pede o G5; o que veio depois vence na
própria data mais o prazo. Antes dela nada precisa expirar, e nenhuma regra é
necessária.

Para que a ativação não dependa de memória, a proposta inclui um teste em
`tests/unit/` que **passa a falhar em 01/01/2032** se as expirações não
estiverem declaradas — o CI avisa. As exceções que já valem hoje (`dev`, `hml`,
`qualidade`, versões antigas do raw e log de auditoria) entram desde o
primeiro `apply`.

A Bronze é particionada pela data da ingestão (`_ingestao_timestamp`), não pela
data do dado. Duas consequências:

- a primeira carga, com todo o histórico, fica numa mesma partição e sai
  inteira em 01/01/2032. Nessa data todo o seu conteúdo já tem mais de 5 anos;
- reprocessar uma janela antiga (regra 3) grava partição nova, e o prazo
  dessas linhas recomeça. A Silver deduplica.

### Públicos pesados

As duas tabelas ainda não existem; a regra entra no conector quando ele for
escrito. Ela tem três partes:

1. **Gold mensal antes da expiração.** Cada tabela pesada tem uma Gold de
   médias mensais, incremental e `protected: true` no Dataform — assim, uma
   execução com *full refresh* não a reconstrói a partir de uma Bronze que já
   perdeu o passado. Ela é atualizada a cada ingestão, anos antes de a
   partição vencer.
2. **Mês só é reagregado inteiro.** A Gold mensal só recalcula um mês que está
   completo na Bronze. Reprocessamento de mês antigo é feito pelo mês inteiro,
   para não gravar média de mês parcial por cima da média completa.
3. **Expiração com trava.** A expiração de partição da Bronze (1.826 dias,
   ativada em 01/01/2032) só é declarada depois de uma *assertion* do Dataform
   confirmar que todo mês presente na Bronze tem linha na Gold mensal.

**Custo.** Pelo G5, a Bronze guarda até 2032 todo o histórico horário e
semi-horário por usina. Partição que fica 90 dias sem alteração passa a ser
cobrada como armazenamento de longo prazo do BigQuery, pela metade do preço —
é o caso de toda partição antiga da Bronze, que só recebe acréscimos.

### Bucket raw

O raw existe para reprocessar, mas também é a **única cópia do que a fonte
entregou**: linhas que falham na validação são descartadas e não chegam à
Bronze. Por isso a recomendação é manter o raw **pelo mesmo prazo da Bronze —
5 anos, contados de 2027 — em classe fria**:

- **STANDARD até 90 dias.** É a janela em que reprocessar é provável, e ler
  STANDARD não tem taxa de recuperação.
- **COLDLINE dos 90 aos 365 dias.** Cobre um ciclo anual de reprocessamento —
  o ONS publica CSV anual.
- **ARCHIVE depois de 1 ano.** Reprocessar um dado com mais de um ano é
  exceção. No Google Cloud a classe ARCHIVE é lida em milissegundos, sem
  restauração: o *replay* do raw funciona igual, só paga a leitura.

**Custo relativo**, pelos preços de lista de referência para região dos
Estados Unidos, a conferir no fechamento:

| Classe | Armazenamento (US$ por GB por mês) | Relativo ao STANDARD | Leitura (US$ por GB) | Permanência mínima |
|---|---|---|---|---|
| STANDARD | 0,020 | 1 | — | — |
| NEARLINE | 0,010 | 1/2 | 0,01 | 30 dias |
| COLDLINE | 0,004 | 1/5 | 0,02 | 90 dias |
| ARCHIVE | 0,0012 | 1/17 | 0,05 | 365 dias |

Na ordem de grandeza da plataforma — algumas centenas de GB de raw em 5 anos —,
guardar 1 TB em ARCHIVE custa cerca de US$ 1,20 por mês. A diferença entre
guardar o raw 5 anos e guardá-lo 400 dias é desprezível no custo; o que pesa é
o critério de necessidade, discutido abaixo.

**Alternativa com prazo menor.** A versão 0.1 propunha excluir aos 90 dias o
raw com dado pessoal (Hubspot e, quando vier, consumo por cliente), porque a
Bronze já guarda o dado. É mais aderente ao princípio da necessidade, com a
contrapartida de que essas fontes só se reprocessam do raw dentro de 90 dias e
as linhas descartadas na validação se perdem. **A Alup e a encarregada
escolhem** entre as duas; esta versão recomenda os 5 anos, por coerência com o
critério F3 e porque o acesso ao raw fica restrito à conta de ingestão e ao
grupo de operação.

## `dev` e `hml`

| Ambiente | Prazo | Por quê | Como se aplica |
|---|---|---|---|
| `dev` | **30 dias** para qualquer dado, no raw e nas tabelas | Desenvolver um conector pede janelas curtas de dado; o público se recarrega por janela (regra 3) | Exclusão por idade no bucket; expiração padrão de partição e de tabela nos datasets; valores no `dev.tfvars` |
| `hml` | **90 dias** para qualquer dado, no raw e nas tabelas | Cobre uma onda e o ciclo de homologação com carga real | Idem, no `hml.tfvars` |

O mínimo de 5 anos não se aplica a esses ambientes: são cópia, e o dado oficial
fica em `prod`. É neles, e no período de desenvolvimento e homologação, que a
ness. acessa dado real (ADR 011). O log de auditoria de acesso a dados fica 1
ano também em `dev` e `hml`, porque é ali que se registra o acesso da ness. a
dado real.

## Direito de eliminação do titular (art. 18, VI)

A Bronze só recebe acréscimos (regra 4). O pedido de eliminação de um titular é
a exceção, sempre registrada:

1. A encarregada recebe o pedido e confirma que não há hipótese de conservação
   (art. 16). O mínimo de 5 anos, quando apoiado em obrigação legal ou
   regulatória, é hipótese de conservação (art. 16, I); o jurídico da Alup
   indica quais prazos têm essa base.
2. As linhas do titular são apagadas da Bronze com `DELETE`, e os objetos
   correspondentes, do raw — inclusive em ARCHIVE, que cobra a permanência
   mínima restante e nada mais.
3. As views da Silver refletem a exclusão na hora; a Gold recalculada, na
   execução seguinte. **A Gold incremental** (consumo mensal por cliente) não
   se recalcula a partir da Bronze e recebe o mesmo `DELETE`.
4. O atendimento é registrado com data, tabelas afetadas e quem executou.

A exclusão no Google leva até 180 dias depois do `DELETE` ([registro do
DPA](dpa.md)); o prazo informado ao titular considera isso.

## Fim do contrato (cláusula 8.3)

- Na homologação final e no handoff, a ness. **perde o acesso** aos três
  projetos e **elimina qualquer cópia** de dado que tenha sob sua posse.
- O dado da plataforma é da Alup e continua sob esta política depois do
  handoff.
- O procedimento, com lista de verificação, vai para o runbook.

## O que muda no repositório depois da aprovação

Desde o primeiro `apply`:

- **`infra/modules/storage`**: mudança para COLDLINE aos 90 dias e para
  ARCHIVE aos 365, no lugar da mudança para NEARLINE de hoje; exclusão de
  versões antigas 30 dias depois de deixarem de ser atuais; em `dev` e `hml`,
  exclusão por idade (30 e 90 dias).
- **`infra/modules/bigquery`**: expiração padrão no dataset `qualidade`; em
  `dev` e `hml`, expiração padrão de partição e de tabela; rótulo de
  classificação `interno` nos datasets e no bucket (pergunta F4).
- **`infra/`**: bucket de log dedicado, com 365 dias, e roteamento dos logs de
  auditoria de acesso a dados; ambiente `hml` (E4), com `hml.tfvars` e
  validação da variável de ambiente — depende da revisão da ADR 015, que previa
  dois ambientes.
- **`definitions/gold/`**: Gold mensal de consumo por cliente e dos públicos
  pesados como tabelas incrementais protegidas, quando os conectores existirem;
  *assertion* de completude entre Bronze e Gold mensal.
- **`tests/unit/`**: o teste que falha a partir de 01/01/2032 sem as
  expirações declaradas.

Em 01/01/2032 e em 01/01/2037:

- **`definitions/bronze/`** e **`infra/modules/storage`**: expiração de 1.826
  dias nas tabelas Bronze e exclusão aos 1.826 dias no raw, exceto nos demais
  públicos.
- **`definitions/gold/`**: expiração de 3.653 dias na Gold de consumo por
  cliente.

## Aprovação

| Papel | Nome | Data |
|---|---|---|
| Proposta | ness. | 11/09/2026 |
| Encarregada | Rosimeire Miler dos Santos | |
| Controladora | ACE Comercializadora Ltda. (Alup) | |

## Histórico

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 11/09/2026 | Proposta inicial, pela ness. |
| 0.2 | 11/09/2026 | Critérios da Alup de 11/09 (perguntas F3, G5 e E4): mínimo de 5 anos contado a partir de 2027; consumo por cliente com 10 anos na Gold mensal; públicos pesados só na Gold mensal a partir do 6º ano; demais públicos sem expiração; raw pelo prazo da Bronze em classe fria; `dev` e `hml` com prazo curto; log de auditoria com 1 ano |
