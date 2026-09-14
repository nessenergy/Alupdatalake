# ADR 019 — O boletim do TempoOK entra como arquivo, e o Bronze guarda o catálogo

**Status**: aceito · **Data**: 2026-09-14 · **Complementa** a
[ADR 003](003-framework-de-conectores.md) · **Depende de** A7 para a primeira
execução real

## Contexto

O TempoOK é uma das fontes da Onda 2. Diferente de todas as outras doze, **não
tem documentação publicada**: o que a Alup forneceu em 14/09 foi um exemplo de
consulta em Python e o token de acesso.

O exemplo revela o contrato inteiro da API:

```
POST https://storage.tempook.com/tokstorage/download_post/
form-data: t=<token>, p=Comercializadora/Boletins/Diario/2022-03/boletim_TOK_2022-03-31.pdf
→ o conteúdo do arquivo
```

Três fatos saem daí, e cada um força uma decisão:

1. **Não é uma API de dados; é um endpoint de download.** Não há listagem, não
   há filtro, não há JSON. Pede-se um caminho e recebe-se um arquivo.
2. **O caminho é derivável da data.** `.../Diario/AAAA-MM/boletim_TOK_AAAA-MM-DD.pdf`
   é template, não identificador opaco. Isso é o que torna a fonte ingerível
   por janela (regra 3) mesmo sem endpoint de listagem.
3. **O conteúdo é um PDF**, e o que ele contém não está documentado em lugar
   nenhum.

## Decisão

### 1. O Bronze guarda o catálogo do boletim, não o conteúdo do PDF

`bronze.tempook_boletins` recebe uma linha por boletim: data de referência,
caminho na origem, tamanho, `sha256`, tipo e o URI do arquivo no GCS. O PDF
inteiro é gravado no bucket raw, ao lado do JSONL da execução, e o Bronze
aponta para ele.

A alternativa era extrair os números do PDF já na ingestão. Foi recusada:

- **Não se sabe o que o boletim contém.** Nenhuma documentação descreve seus
  campos, e a Alup não os informou. Escrever um extrator agora seria decidir,
  por conta própria, quais números do boletim importam — exatamente o
  "schema por adivinhação" que o `status.md` §5 registra como pior que não
  escrever.
- **Extrair de PDF é frágil por natureza.** O layout muda sem aviso e sem
  versionamento, e o parser quebra em silêncio, produzindo número errado em vez
  de erro. Um extrator escrito antes de existir uma pergunta de negócio é um
  passivo de manutenção sem contrapartida.
- **Arquivar não impede extrair depois.** Com os PDFs no GCS desde a primeira
  execução, o dia em que a Alup disser quais indicadores quer, o histórico já
  está lá — e o `alupdata reprocessar-raw` existe justamente para reprocessar
  sem bater de novo na origem. O caminho inverso não existe: o que não foi
  baixado, não se recupera.

**A extração do conteúdo é escopo futuro, e depende de A4** (os domínios
analíticos) para saber o que extrair. Quando vier, é ADR própria e uma entidade
nova (`tempook_<indicador>`), não uma alteração desta.

### 2. O núcleo ganha gravação de arquivo, e só isso

`src/core/storage.py` ganha `gravar_arquivo()`, que põe bytes no bucket raw sob
`{fonte}/{entidade}/dt=.../{ingestao_id}/{nome}`. São doze linhas, e não tocam
o caminho do raw JSONL, nem o `identificar_raw`, nem o replay.

Considerou-se embutir o PDF em base64 dentro do próprio JSONL, o que evitaria
qualquer mudança no núcleo. Recusado: o conteúdo do raw vai inteiro para as
colunas do Bronze, e uma tabela do BigQuery com PDFs embutidos nas linhas é
cara de varrer e impossível de consultar — o oposto do que o particionamento e
o clustering da regra 4 existem para garantir.

### 3. A verificação de TLS permanece ligada

O exemplo fornecido usa `verify=False`. **O conector não reproduz isso.**
Desligar a verificação de certificado abre a conexão a interceptação, e o
token trafega nela — é o tipo de achado que a cláusula 8ª trata como bloqueante
(Bandit, B501). Se o certificado do `storage.tempook.com` estiver de fato
quebrado, o caminho é a Alup acionar o fornecedor, não a ness. desligar a
verificação.

### 4. Ausência de boletim não é falha

Não se sabe como a origem sinaliza um dia sem boletim — feriado, fim de semana,
publicação atrasada. O conector trata como ausência **qualquer resposta que não
comece com a assinatura `%PDF-`**, registra aviso e segue para o próximo dia.

É guarda deliberada, e não desconfiança gratuita: um endpoint de download que
devolve 200 com uma página de erro é comum, e sem essa verificação o lake
arquivaria HTML de erro como se fosse boletim.

### 5. O POST pode ser repetido

`criar_sessao(retry_post=True)`. O endpoint só lê: repetir depois de um 429 ou
503 não cria nem altera nada na origem.

## Consequências

- Nasce `tempook_boletins`, com os 7 componentes. A Gold é um catálogo de
  cobertura — quais dias têm boletim —, não um indicador; é o que se pode
  afirmar sem conhecer o conteúdo, e é coerente com a ADR 012 (Gold sem KPI
  nesta fase).
- **O conector não foi executado contra a API real.** Foi escrito a partir do
  exemplo, como o `hubspot_negocios` foi escrito a partir da documentação
  pública, e pelo mesmo motivo: a credencial não está no ambiente. O teste de
  integração fica `skipif` até o token existir no Secret Manager.
- O que só a primeira execução real revela está listado no fim de
  `docs/dicionario-dados/tempook_boletins.md`. O principal: **se o template do
  caminho vale para toda data**, ou se há exceção que o exemplo de um único dia
  não mostra.
- O token vai para `alupdata-tempook-api-token`, já declarado em
  `infra/modules/secrets`. O token entregue por e-mail em 14/09 **deve ser
  rotacionado antes do primeiro uso** — a recomendação está no
  [registro de 14/09](../../relatorios/2026-09-14-documentacao-de-apis-recebida.md) §5.
