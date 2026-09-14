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

## O que não foi possível verificar sem credencial

O conector **nunca falou com a API**. Foi escrito a partir de um exemplo de um
único dia, como o do Hubspot foi escrito a partir da documentação pública. O
teste de integração está `skipif` até o token existir no Secret Manager, e é
ele que responde:

1. **O template do caminho vale para toda data?** O único caminho que se sabe
   existir é o de 2022-03-31. Se houver exceção — nome diferente em algum
   período, pasta que mudou de nome em algum ano —, o exemplo de um dia não
   mostra. **É o risco principal desta fonte.**
2. **Como a origem sinaliza um dia sem boletim?** 404, corpo vazio, HTML de
   erro com 200? O conector trata os três como ausência, mas qual deles de
   fato ocorre é suposição.
3. **A verificação de TLS passa?** O exemplo fornecido a desliga, o que pode
   indicar certificado com problema. Se for o caso, o caminho é a Alup acionar
   o TempoOK — não desligar a verificação.
4. **O PDF de um dia é estável?** Se a origem gerar o arquivo a cada
   requisição com carimbo de tempo dentro, o `sha256` muda a cada ingestão e a
   detecção de republicação perde o sentido.
5. **Qual o tamanho típico de um boletim**, e portanto o custo de armazenar a
   série histórica no bucket raw.

## Uma pendência de segurança

O token foi entregue **em texto claro por e-mail**, com seis destinatários em
cópia, em 14/09/2026. A recomendação de **rotacioná-lo antes do primeiro uso**
está no [registro de 14/09](../relatorios/2026-09-14-documentacao-de-apis-recebida.md) §5.
Nenhuma versão dele consta deste repositório.
