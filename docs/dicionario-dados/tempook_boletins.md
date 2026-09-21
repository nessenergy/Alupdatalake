# TempoOK — boletins diários (catálogo)

| Item | Valor |
|---|---|
| Fonte | `https://storage.tempook.com/tokstorage/download_post/` |
| Documentação | **não existe publicada** — o contrato foi derivado do exemplo fornecido pela Alup em 14/09/2026 |
| Onda | 2 — exige credencial |
| Método | `POST` form-data: `t` (token), `p` (caminho do arquivo) |
| Resposta | o arquivo, não JSON |
| Formato | PDF |
| Frequência | Diária |
| Credencial | token no secret `alupdata-tempook-api-token` (pendência A7) |

## Particularidades

- **Não é API de dados; é endpoint de download.** Não há listagem, não há
  filtro, não há JSON: pede-se um caminho e recebe-se um arquivo.
- **O caminho é derivável da data**, e é isso que torna a fonte ingerível por
  janela (regra 3) sem endpoint de listagem:

  ```
  Comercializadora/Boletins/Diario/AAAA-MM/boletim_TOK_AAAA-MM-DD.pdf
  ```

- **O Bronze guarda o catálogo, não o conteúdo**
  ([ADR 019](../arquitetura/decisoes/019-boletim-do-tempook-como-arquivo.md)).
  O PDF vai inteiro para o bucket raw; o Bronze aponta para ele. Extrair os
  números do boletim é escopo futuro e depende de A4 — sem saber quais
  indicadores importam, um extrator de PDF seria adivinhação com custo de
  manutenção.
- **Resposta que não começa com `%PDF-` é tratada como ausência**, mesmo com
  status 200. Endpoint de download que devolve página de erro com 200 é comum,
  e sem essa guarda o lake arquivaria HTML como se fosse boletim.
- **A verificação de TLS permanece ligada.** O exemplo fornecido usa
  `verify=False`; o conector não reproduz isso — o token viaja na conexão.
- Dia sem boletim (fim de semana, feriado, publicação atrasada) vira aviso no
  log e a janela segue.

## Campos

| Origem | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| — (derivado da janela) | `data_referencia` | DATE | o dia cujo boletim foi pedido |
| `p` da requisição | `caminho_origem` | STRING | preservado para rastrear até a origem |
| último segmento do caminho | `nome_arquivo` | STRING | direto |
| — (gravação no GCS) | `uri_arquivo` | STRING | `gs://…`; nulo em dry-run |
| corpo da resposta | `tamanho_bytes` | INT64 | tamanho do PDF |
| corpo da resposta | `sha256` | STRING | identifica republicação corrigida sem reabrir o PDF |
| — | `content_type` | STRING | `application/pdf` |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do boletim |
| `periodo_apuracao` | sim | `AAAA-MM` |
| `submercado` | não | o boletim é nacional |
| `codigo_usina` | não | catálogo de documento, não de ativo |
| `agente_ccee` | não | idem |

## Deduplicação

Chave natural: `data_referencia`. Vence a ingestão mais recente. `sha256`
diferente entre duas ingestões do mesmo dia significa que a origem republicou
o boletim corrigido — o histórico continua no Bronze, que é append-only.

## Gold

`gold.cobertura_boletins_tempook` — quantos dias de cada mês têm boletim
arquivado, primeiro e último dia, bytes arquivados e dias sem boletim.

É controle de cobertura, não indicador de negócio: é o que se pode afirmar sem
conhecer o conteúdo do PDF. Quando a Alup definir quais números importam (A4),
nasce uma entidade nova com o conteúdo extraído, e esta continua sendo o
controle de que o arquivamento não tem buraco.

## Linhagem

```
storage.tempook.com (POST download_post)
  → boletim_TOK_AAAA-MM-DD.pdf
    ├→ gs://<bucket>-raw/tempook/boletins/dt=.../<ingestao_id>/<nome>.pdf   (o arquivo)
    └→ gs://<bucket>-raw/tempook/boletins/dt=.../<ingestao_id>.json.gz      (o catálogo)
       → bronze.tempook_boletins
         → silver.tempook_boletins
           → gold.cobertura_boletins_tempook
```

## Verificado contra a API real em 14/09/2026

O contrato acima **deixou de ser suposição**. A API foi sondada com o token
recebido, em ~40 datas, com verificação de TLS ligada.

| Pergunta | Resposta |
|---|---|
| O template do caminho vale para toda data? | **Sim.** Confirmado ao longo de 7 meses de 2022 |
| Como a origem sinaliza dia sem boletim? | **404** |
| O TLS passa sem `verify=False`? | **Sim.** O `verify=False` do exemplo é desnecessário |
| Qual o tamanho de um boletim? | **~9 MB** (31/03/2022). Um ano de dias úteis ≈ **2 GB** no bucket raw |
| O `Content-Type` identifica o PDF? | **Não** — a origem devolve `application/octet-stream`. Por isso a guarda é pela assinatura `%PDF-`, não pelo cabeçalho |
| O PDF de um dia é byte-a-byte estável? | **Sim.** Duas leituras do mesmo boletim deram `sha256` idêntico — a coluna detecta republicação de verdade, e não ruído |

### O boletim é de dia útil

A varredura diária de outubro de 2022 mostra o calendário: 404 em sábados e
domingos, e **404 em 12/10, feriado de Nossa Senhora Aparecida**. A janela de 5
dias do agendamento cobre um fim de semana prolongado.

### 5xx não é ausência

Um caminho que respondera 200 devolveu **503** minutos depois. O retry da sessão
absorve o transitório; persistindo, a execução falha — que é o certo. Tratar
503 como "sem boletim" faria o dia sumir do lake sem ninguém notar.

## O que segue em aberto — e é da Alup

> **Atualização de 21/09/2026.** O mesmo token alcança **outro produto em dia**: a
> previsão de ENA, documentada em [`tempook_ena_prevs.md`](tempook_ena_prevs.md). Isso
> não resolve o acervo de boletins, mas dá à hipótese 2 abaixo — os boletins mudaram
> de área do storage — uma evidência que ela não tinha: existe outra área, e ela tem
> dado atual.

**A série alcançável por este token termina em 2022-10-26.** Nenhum boletim de
novembro ou dezembro de 2022 responde, nem nada de 2023, 2024, 2025 ou 2026.
Sete variações plausíveis do caminho para uma data recente também devolveram
404.

Não é defeito do conector: o token funciona e o caminho está certo. As
hipóteses, em ordem de probabilidade:

1. o token é antigo e sua permissão cobre só o período contratado à época;
2. os boletins passaram a ser publicados em outra área do storage;
3. o produto foi descontinuado ou renomeado.

**Enquanto isso não for respondido, o conector ingere zero boletins** — o
comportamento correto para um acervo vazio, mas não o que a Onda 2 precisa
entregar. A pergunta está no
[registro de 14/09](../relatorios/2026-09-14-documentacao-de-apis-recebida.md).

Fora isso, **o contrato de dados desta fonte está integralmente verificado.** O
que falta para a primeira ingestão real é ambiente (A3) e acervo — não
conhecimento da origem.

## Uma pendência de segurança

O token foi entregue **em texto claro por e-mail**, com seis destinatários em
cópia, em 14/09/2026. Ele **é mantido até a virada de produção** e rotacionado
lá — rotacionar antes de existir Secret Manager entregaria o valor novo pelo
mesmo e-mail, renovando a exposição em vez de encerrá-la. A decisão, com dono,
alcance medido e gatilhos que antecipam a rotação, está na
[ADR 020](../arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md).

Até lá ele vive no cofre local ([runbook](../runbook/credenciais.md)), fora do
repositório. Nenhuma versão dele consta deste repositório.
