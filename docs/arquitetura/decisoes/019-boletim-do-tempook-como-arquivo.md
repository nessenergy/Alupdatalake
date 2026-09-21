# ADR 019 — O boletim do TempoOK entra como arquivo, e o Bronze guarda o catálogo

**Status**: aceito · **Data**: 2026-09-14 · **Complementa** a
[ADR 003](003-framework-de-conectores.md) · **Verificada contra a API real** em
2026-09-14 — ver o adendo no fim

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

A origem sinaliza ausência com **404** — verificado no adendo; quando esta ADR
foi escrita, era suposição. O conector trata como ausência tanto o 404 quanto
**qualquer resposta que não comece com a assinatura `%PDF-`**, registra aviso e
segue para o próximo dia.

A segunda guarda é deliberada, e não desconfiança gratuita: um endpoint de
download que devolve 200 com página de erro é comum, e sem ela o lake
arquivaria HTML de erro como se fosse boletim. O adendo mostra que ela é
necessária por outro motivo também — a origem declara `application/octet-stream`
para um PDF, então o `Content-Type` não serve para decidir.

**5xx não é ausência.** Um 503 significa "a origem falhou", não "não há
boletim": tratá-lo como ausência abriria buraco silencioso na série. O retry da
sessão tenta de novo e, persistindo, a execução falha — que é o certo.

### 5. O POST pode ser repetido

`criar_sessao(retry_post=True)`. O endpoint só lê: repetir depois de um 429 ou
503 não cria nem altera nada na origem.

## Consequências

- Nasce `tempook_boletins`, com os 7 componentes. A Gold é um catálogo de
  cobertura — quais dias têm boletim —, não um indicador; é o que se pode
  afirmar sem conhecer o conteúdo, e é coerente com a ADR 012 (Gold sem KPI
  nesta fase).
- O conector foi **sondado contra a API real** em 14/09, com o token recebido —
  ver o adendo. As quatro suposições desta ADR se confirmaram; apareceu um
  problema de outra natureza, que é da Alup resolver.
- O teste de integração segue `skipif`: ele lê o token do Secret Manager, que
  não existe até A3.
- O token vai para `alupdata-tempook-api-token`, já declarado em
  `infra/modules/secrets`. O token entregue por e-mail em 14/09 **é mantido até
  a virada de produção**, quando é rotacionado — rotacionar antes de existir
  Secret Manager reproduziria a mesma exposição. Decisão, alcance medido e
  gatilhos de antecipação na
  [ADR 020](020-token-tempook-rotacao-na-producao.md).

---

## Adendo de 2026-09-14 — sondagem contra a API real

O `.eml` com o token voltou a ficar acessível na mesma tarde, e a API foi
sondada antes de a ADR ser dada por encerrada. **As quatro decisões acima se
confirmaram, e uma quinta questão apareceu.**

### O que se confirmou

| Suposição | Resultado |
|---|---|
| O template do caminho vale para toda data, não só para o exemplo | **Confirmado.** Verificado em ~40 datas distintas ao longo de 7 meses de 2022, todas respondendo com PDF |
| A verificação de TLS passa sem `verify=False` | **Confirmado.** Todas as requisições foram feitas com validação de certificado ligada. O `verify=False` do exemplo é desnecessário |
| A origem sinaliza ausência de forma detectável | **Confirmado: 404.** E a ausência tem sentido — ver abaixo |
| Tratar 5xx como falha, e não como ausência, importa | **Confirmado na prática.** Um caminho que respondera 200 devolveu **503** minutos depois. O retry da sessão absorve; tratar 503 como "sem boletim" teria criado buraco silencioso na série |

### O boletim é de dia útil, e o 404 prova isso

A varredura diária de outubro de 2022 desenha o calendário sozinha:

| Data | Dia | Resposta |
|---|---|---|
| 08/10, 09/10 | sábado, domingo | 404 |
| 10/10, 11/10 | segunda, terça | PDF |
| **12/10** | quarta — **Nossa Senhora Aparecida** | **404** |
| 13/10, 14/10 | quinta, sexta | PDF |
| 15/10, 16/10 | sábado, domingo | 404 |
| 17/10 a 20/10 | segunda a quinta | PDF |

Fim de semana e feriado nacional não têm boletim. **A janela de 5 dias do
agendamento é adequada** — cobre um fim de semana prolongado sem multiplicar
requisições.

### O `Content-Type` não serve para decidir, e a guarda por bytes estava certa

A origem devolve **`application/octet-stream`**, não `application/pdf`, mesmo
quando o corpo é um PDF íntegro. A decisão de conferir a assinatura `%PDF-` em
vez de confiar no cabeçalho (item 4) deixou de ser precaução e passou a ser
necessária.

### A questão nova: a série acessível termina em outubro de 2022

O token funciona, o caminho está certo, e **nenhum boletim posterior a
2022-10-26 responde**. Amostragem em dias úteis de novembro e dezembro de 2022,
e em 2023, 2024, 2025 e 2026: **404 em todos**. Sete variações plausíveis do
caminho para uma data recente também devolveram 404.

Não é defeito do conector nem do template — é o acervo alcançável por esta
credencial. As hipóteses, em ordem de probabilidade:

1. o token é antigo e sua permissão cobre apenas o período contratado à época;
2. os boletins passaram a ser publicados em outra área do storage;
3. o produto "Boletim Diário da Comercializadora" foi descontinuado ou
   renomeado.

**É pergunta para a Alup, não decisão de arquitetura**, e está registrada no
[registro de 14/09](../../relatorios/2026-09-14-documentacao-de-apis-recebida.md).
Enquanto não for respondida, o conector está correto e ingere zero boletins —
que é o comportamento certo para um acervo vazio, mas não é o que a Onda 2
precisa entregar.

### Consequência para o histórico

Se a resposta for a hipótese 1 e a Alup obtiver um token com acervo completo, o
conector ingere o histórico de uma vez passando a janela desejada — é
exatamente o que a regra 3 existe para permitir. O PDF de 31/03/2022 tem
**9 MB**; a série de um ano de dias úteis fica na ordem de **2 GB no bucket
raw**, o que é barato e cabe no teto de custo, mas merece ser dito antes de
alguém pedir "todo o histórico".

---

## Adendo de 21/09/2026 — um segundo produto, e a hipótese 2 com evidência

Em 18/09 a Alup entregou a função que ela mesma usa para baixar do TempoOK e um
caminho de exemplo de **outro produto**: a previsão de ENA
(`Comercializadora/Arquivos/ENA-PREVS/…`, um `tar.gz` por dia). Conferido em 21/09
contra a origem real, com o token que já tínhamos:

- **está em dia** (arquivo de 20/09), diário inclusive fim de semana, ~94 KB;
- o acervo começa em ~17/11/2024;
- o TLS passa sem `verify=False` — que a função da Alup também traz;
- a resposta é `application/octet-stream`, como a do boletim.

**A mecânica é a mesma da decisão acima**, então ela foi generalizada em vez de
copiada: `tempook_arquivos` (base) carrega o POST, a guarda de assinatura e o
catálogo; `tempook_boletins` e `tempook_ena_prevs` declaram só o caminho e a
assinatura (PDF e gzip). Os quatro itens da decisão valem para os dois. O item 4
ganha uma consequência prática: **a assinatura é por produto**, e um PDF no
caminho do ENA-PREVS é rejeitado.

### O que muda na questão do acervo

A hipótese 2 — *os boletins passaram a ser publicados em outra área do storage* —
**ganhou evidência**: existe outra área (`Arquivos/`) e ela tem dado atual. Não foi
testada, porque sem listagem achar o caminho depende de a Alup indicá-lo. A
pergunta a fazer deixa de ser "por que o acervo para em 2022" e passa a ser **"onde
estão os boletins recentes"**.

### O que muda na segurança

O alcance do token, medido no item 3.1 desta ADR e tomado como premissa da
[ADR 020](020-token-tempook-rotacao-na-producao.md), **deixou de descrever a
realidade**. Ver o adendo daquela ADR.

