# ADR 016 — Versionamento das recontabilizações da CCEE

**Status**: proposto · **Data**: 2026-09-11 · **Complementa** as ADRs
[003](003-framework-de-conectores.md) e [012](012-dataform.md)

## Contexto

A CCEE recontabiliza meses já fechados: publica de novo o resultado de uma
competência, com valores diferentes. Na pergunta D5 do
[Questionário de Gaps](../../questionario-gaps.md), a Alup respondeu em 11/09
que esse dado **deve ser versionado**, para rastrear as recontabilizações — e
não sobrescrito.

O que o modelo faz hoje:

- **Bronze append-only (regra 4).** Toda leitura fica guardada, com
  `_ingestao_id` e `_ingestao_timestamp`. Nenhuma versão se perde.
- **Silver deduplica pela ingestão mais recente.** `QUALIFY ROW_NUMBER() OVER
  (PARTITION BY <chave> ORDER BY _ingestao_timestamp DESC) = 1` é o padrão das
  cinco fontes atuais.

Isso guarda o histórico, mas não o versiona, por três motivos:

1. **A versão é implícita.** O que distingue duas linhas da mesma chave é a
   hora da leitura, não a publicação da CCEE. Ler duas vezes a mesma publicação
   cria duas "versões"; uma recontabilização publicada e substituída entre duas
   leituras nunca aparece.
2. **O *replay* inverte a ordem.** `alupdata reprocessar-raw` sobre um raw
   antigo grava linhas com `_ingestao_timestamp` novo, e a Silver passa a
   servir a versão velha como vigente. A [ADR 012](012-dataform.md) já apontava
   a medição da CCEE como fonte em que "o registro certo não é o mais recente".
3. **O histórico não é consultável em termos de negócio.** Responder "qual era
   o valor de março antes da recontabilização de junho" hoje exige ler a Bronze
   e interpretar colunas técnicas.

Ainda não existe conector da CCEE: o InfoMercado estava bloqueado por 403 (C4,
destravado em 11/09) e o Balanço Energético depende do acesso ao MySQL RDS
(C8). É o momento de decidir, antes do primeiro `.sqlx`.

## Opções

### A. Manter a Silver pela ingestão mais recente

Nada muda; o histórico fica só na Bronze. Não atende D5: a versão continua
implícita e o *replay* continua capaz de rebaixar o dado vigente.

### B. Versão da fonte na chave; Silver vigente mais view de histórico

- O conector extrai da fonte um **identificador de versão** — número da
  recontabilização, data de publicação ou data do processamento, o que a CCEE
  fornecer — em coluna de negócio (`versao_publicacao` ou `data_publicacao`),
  validada por Pydantic como qualquer outra.
- `silver.<fonte>` guarda a **versão vigente**: uma linha por chave de negócio,
  `ORDER BY <versao> DESC, _ingestao_timestamp DESC`. A versão da fonte decide;
  a hora da leitura só desempata leituras da mesma versão.
- `silver.<fonte>_historico` guarda **uma linha por chave e versão**, com as
  leituras repetidas da mesma versão colapsadas. *Assertion* `uniqueKey` em
  (chave, versão).
- A Gold lê só a vigente.

Tudo em view, sem estado novo: a Bronze continua sendo o único lugar que guarda
dado, e o *replay* deixa de rebaixar a vigente, porque a ordem vem da fonte.

### C. Dimensão de tipo 2 materializada (`valido_de`, `valido_ate`)

Tabela incremental com `MERGE` por chave, fechando a vigência anterior a cada
versão nova. Responde "como estava em tal data" diretamente, mas cria estado
fora da Bronze, exige Silver incremental — que a ADR 012 só admite quando o
painel de custo pedir — e o `MERGE` erra quando versões chegam fora de ordem,
como no *replay* e na carga de todo o histórico pedida em G5.

### D. Versões na Gold

Gold com coluna de versão, para o consumo comparar publicações. Leva a pergunta
do versionamento para cada tabela de consumo e para o BI, sem uso declarado
nesta fase: a Gold da Fase 1 não tem KPI (ADR 012, "Gold na Fase 1").

### Descartado de saída: *time travel* do BigQuery

Guarda no máximo sete dias. Serve para desfazer erro de operação, não para
versionar.

## Recomendação

**Opção B.** Atende D5 sem estado novo, preserva a regra 4 (Bronze
append-only, deduplicação na Silver), corrige o *replay* e mantém a Gold
simples. O custo é um identificador de versão por fonte da CCEE e uma view a
mais por fonte.

A opção C fica disponível depois, se a consulta por data de vigência se tornar
frequente; a D, como Gold comparativa específica lendo a view de histórico, se
um consumidor pedir.

Ordem de preferência para o identificador de versão:

1. versão ou número da recontabilização publicado pela CCEE;
2. data de publicação do arquivo ou do processamento, informada pela fonte;
3. **só em último caso**, a data da leitura — que é o que já existe hoje e não
   distingue publicação de leitura.

## O que falta para decidir

**O schema real das fontes da CCEE.** A opção B depende de a fonte trazer o
identificador de versão, e isso só se confirma com o dado na mão — escrever
schema por adivinhação continua proibido (`docs/status.md` §5):

- **InfoMercado** (dados abertos da CCEE): verificar se o arquivo ou o seu
  metadado trazem versão ou data de publicação.
- **Balanço Energético** (MySQL RDS da Alup): verificar se a tabela guarda cada
  recontabilização ou se a automação sob demanda sobrescreve o mês. Se
  sobrescreve, o lake só vê o que houver no momento da leitura, a versão cai no
  item 3, e a frequência de leitura passa a fazer parte da regra.

Esta ADR passa a "aceito" quando o dicionário de dados da primeira fonte da
CCEE registrar o identificador escolhido. Mudar de opção depois disso é ADR
nova.

## Consequências

- A regra 4 fica como está: a Bronze já guarda todas as versões; muda o que a
  Silver faz com elas.
- Cada fonte da CCEE ganha uma view a mais na Silver (`_historico`), com
  linhagem e dicionário como qualquer outra. O componente 03 continua sendo a
  view Silver vigente.
- A view de histórico relê a Bronze inteira a cada consulta, como a Silver
  vigente. Se o consumo dela pesar, materializá-la segue os gatilhos da
  ADR 012.
- O esqueleto de `scripts/novo_conector.py` não muda: o padrão só vale para
  fonte com recontabilização. A skill de conector o registra quando a primeira
  fonte o usar.
- O histórico de versões depende de a Bronze não expirar. Na
  [proposta de retenção](../../lgpd/politica-de-retencao.md), tabela sem dado
  pessoal fica sem prazo na Bronze.
- O ONS também revisa dado publicado (`silver.ons_carga`), mas D5 foi
  respondida para a CCEE. Estender o padrão a outra fonte depende de pedido da
  Alup.
