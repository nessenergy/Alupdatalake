# TempoOK — previsão de ENA, ENA-PREVS (catálogo)

| Item | Valor |
|---|---|
| Fonte | `https://storage.tempook.com/tokstorage/download_post/` — o mesmo endpoint do [boletim](tempook_boletins.md) |
| Documentação | **não existe publicada** — o contrato vem do exemplo de consulta que a Alup entregou em 18/09/2026, conferido contra a origem real em 21/09 |
| Onda | 2 — exige credencial |
| Método | `POST` form-data: `t` (token), `p` (caminho do arquivo) |
| Resposta | o arquivo, não JSON |
| Formato | `tar.gz`, com 7 arquivos `.txt` dentro |
| Frequência | **Diária, inclusive sábado e domingo** |
| Volume verificado | ~80–95 KB por arquivo; ~670 arquivos desde o início do acervo ≈ **60 MB** |
| Credencial | token no secret `alupdata-tempook-api-token` — o mesmo do boletim |

## Por que esta fonte existe no lake

O domínio **Meteorologia** pergunta *que chuva, vento e clima explicam a oferta
que vem?* Até 21/09 ele só tinha o boletim do TempoOK, cujo acervo alcançável
pelo token **termina em 26/10/2022** ([#129](https://github.com/nessenergy/Alupdatalake/issues/129)) —
o domínio respondia "o boletim de tal dia chegou", e nada posterior a 2022.

**Este é o primeiro produto do TempoOK que responde para a data de hoje.** A
Alup entregou o caminho em 18/09, junto da função que ela mesma usa para
baixá-lo; o conector foi verificado em 21/09 contra a origem real.

A previsão de ENA (energia natural afluente) é a contraparte prospectiva do que
o lake já tem observado: o `ons_ena` diz quanto chegou, este arquivo diz quanto
os modelos esperam que chegue.

## O que a Alup entregou — e o que ainda não

A Alup entregou **um caminho de exemplo**, não a lista dos que interessam: *"nós
vamos pegar aqui o caminho dos arquivos que precisamos"*. Por isso:

- só **uma combinação de modelos** é conhecida (`ECENSav-ETA40-GEFSav-ECENS45`);
- `modelo` é **coluna da tabela desde o primeiro dia**. O Bronze é append-only, e
  sem a coluna cada combinação nova pediria mudança de schema;
- para acrescentar um caminho, basta estender `MODELOS` em
  `src/conectores/tempook_ena_prevs.py` — o resto do conector não muda.

Enquanto a lista não vem, o conector ingere exatamente o que foi verificado, e
nada além. Inventar outros caminhos por semelhança de nome seria dado sem
origem.

## Particularidades

- **Não é API de dados; é endpoint de download.** Pede-se um caminho e recebe-se
  um arquivo. O caminho é derivável da data — é isso que torna a fonte ingerível
  por janela (regra 3) sem endpoint de listagem:

  ```
  Comercializadora/Arquivos/ENA-PREVS/<conjunto>/<modelo>/AAAA-MM/ENA-PREVS_<modelo>_AAAAMMDD.tar.gz
  ```

  A pasta `AAAA-MM` é a do próprio arquivo: uma janela que cruza o mês muda de
  pasta.
- **O Bronze guarda o catálogo, não o conteúdo**
  ([ADR 019](../arquitetura/decisoes/019-boletim-do-tempook-como-arquivo.md)). O
  tar.gz vai inteiro para o bucket raw; o Bronze aponta para ele. **O conector não
  abre o tar.gz** — extrair os números é escopo futuro, e depende de a Alup dizer
  quais importam.
- **Resposta que não começa com a assinatura do gzip (`1f 8b`) é tratada como
  ausência**, mesmo com status 200. É a mesma guarda do PDF no boletim, com a
  assinatura trocada; um PDF no caminho do ENA-PREVS é rejeitado.
- **O servidor devolve `application/octet-stream`.** Por isso a guarda é pela
  assinatura, não pelo cabeçalho, e o catálogo grava `application/gzip`.
- **A verificação de TLS permanece ligada.** A função que a Alup usa tem
  `verify=False`; o conector não reproduz isso — o token viaja na conexão. Conferido
  em 21/09: **a verificação passa sem ajuste**, então o `verify=False` é
  desnecessário aqui também.
- **Não pula fim de semana**, ao contrário do boletim, que só saía em dia útil.
- **O arquivo do dia demora a aparecer.** Às 10h56 de 21/09 o arquivo de 20/09
  estava lá e o de 21/09 não. O agendamento (11h30, janela de 5 dias) cobre isso.
- **Dia sem arquivo vira aviso no log** e a janela segue; 5xx **não** é ausência
  e derruba a execução, para o dia não sumir do lake sem ninguém notar.

## O que há dentro do tar.gz

Verificado em 21/09 abrindo um arquivo só para listar nomes e tamanhos; o
conteúdo não é versionado aqui.

- **7 arquivos `.txt`** de ~93 KB cada, **um por revisão do PMO**:
  `2026_9_rev2`, `2026_9_rev3`, `2026_10_rev0` … `2026_10_rev4`, cada um com o
  sufixo do modelo e a data;
- cada `.txt` começa com **`ENA - subsystem:`** e uma tabela por subsistema, com
  colunas de semana (`S1` a `S6`) e `MES`.

Isso descreve a **forma**, não o significado: não se sabe ainda quais números
importam nem como cruzá-los com o `ons_ena`. É a pergunta que fica para a Alup.

## Campos

| Origem | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| nome do arquivo | `data_referencia` | DATE | o dia do arquivo, o da data no nome |
| segmento da pasta | `modelo` | STRING | combinação de modelos, como aparece no nome do arquivo |
| `p` da requisição | `caminho_origem` | STRING | preservado para rastrear até a origem |
| último segmento do caminho | `nome_arquivo` | STRING | direto |
| — (gravação no GCS) | `uri_arquivo` | STRING | `gs://…`; nulo em dry-run |
| corpo da resposta | `tamanho_bytes` | INT64 | tamanho do tar.gz |
| corpo da resposta | `sha256` | STRING | identifica republicação corrigida sem reabrir o arquivo |
| — | `content_type` | STRING | `application/gzip` |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do arquivo |
| `periodo_apuracao` | sim | `AAAA-MM` |
| `submercado` | não | o catálogo não abre o conteúdo, onde a tabela por subsistema está |
| `codigo_usina` | não | catálogo de documento, não de ativo |
| `agente_ccee` | não | idem |

## Deduplicação

Chave natural: (`data_referencia`, `modelo`). Vence a ingestão mais recente.
`sha256` diferente entre duas ingestões do mesmo dia e modelo significa que a
origem republicou o arquivo corrigido — o histórico continua no Bronze, que é
append-only.

## Gold

`gold.cobertura_ena_prevs_tempook` — por mês e modelo: dias com arquivo, primeiro
e último dia, bytes arquivados, arquivos distintos e **dias sem arquivo**.

Diferente da cobertura dos boletins, **aqui buraco é sinal**: o produto é diário
e inclui fim de semana, então `dias_sem_arquivo` maior que zero não é feriado.
O mês corrente só conta até o último dia que o modelo tem arquivo, para o futuro
não aparecer como falta.

É controle de cobertura, não indicador de negócio (ADR 012).

## Linhagem

```
storage.tempook.com (POST download_post)
  → ENA-PREVS_<modelo>_AAAAMMDD.tar.gz
    ├→ gs://<bucket>-raw/tempook/ena_prevs/dt=.../<ingestao_id>/<nome>.tar.gz   (o arquivo)
    └→ gs://<bucket>-raw/tempook/ena_prevs/dt=.../<ingestao_id>.json.gz         (o catálogo)
       → bronze.tempook_ena_prevs
         → silver.tempook_ena_prevs
           → gold.cobertura_ena_prevs_tempook
```

## Verificado contra a API real em 21/09/2026

Sondagem com o token do cofre local, TLS ligado, sem gravar nada em disco além de
metadados.

| Pergunta | Resposta |
|---|---|
| O exemplo da Alup responde? | **Sim** — 15/09/2026, 94.246 bytes, gzip |
| O produto está em dia? | **Sim**, diferente do boletim. Arquivo de 20/09 presente; o do dia corrente ainda não |
| Qual a cobertura? | **43 de 45 dias** consecutivos até 15/09 |
| Onde estão os buracos? | 15/08, 05/09 e 19/09 — **os três são sábado**; a causa é desconhecida |
| Sábado e domingo têm arquivo? | **Sim**, na maioria; 3 de 8 sábados amostrados faltaram |
| Onde começa o acervo? | **~17/11/2024** (busca binária: 16/11 ausente, 17/11 presente) |
| Qual o tamanho? | ~79 KB em dez/2024, ~94 KB em set/2026 — cresce devagar |
| Como a origem sinaliza dia sem arquivo? | **404**, com corpo de 20 bytes |
| O TLS passa sem `verify=False`? | **Sim** |
| O `Content-Type` identifica o gzip? | **Não** — `application/octet-stream` |
| A ingestão de ponta a ponta funciona? | **Sim** — dry-run de 01 a 15/09: 14 arquivos, 0 inválidos, 69 s |

### Carga histórica

O acervo tem ~670 dias, e cada requisição leva ~4,6 s — **~52 minutos no total, mais
que o timeout de 1800 s do Cloud Run Job**. A carga histórica não cabe em uma
execução; pela regra 3 ela é feita em janelas (`--de` / `--ate`) de até ~300 dias.
São ~60 MB no bucket raw, o que é irrelevante para custo.

## O que segue em aberto — e é da Alup

1. **Quais são os caminhos que importam?** A lista das demais combinações de
   modelos, e de outros produtos da pasta `Arquivos/`. É a pergunta que destrava
   o resto desta fonte.
2. **Por que faltam alguns sábados?** 15/08, 05/09 e 19/09. Se for característica
   do produto (o modelo não roda), o Gold vai mostrar buraco permanente e a
   leitura precisa saber disso; se for falha de publicação, é do TempoOK.
3. **O token é estático ou renovável?** A função que a Alup usa chama
   `get_tok_token()`, o que sugere obtenção dinâmica. O token que temos é o de
   14/09 e **continua funcionando em 21/09** — sete dias —, mas se ele expirar, o
   job agendado passa a falhar. É o gatilho da
   [ADR 020](../arquitetura/decisoes/020-token-tempook-rotacao-na-producao.md).
4. **O boletim está em `Arquivos/` também?** A ADR 019 tinha três hipóteses para o
   acervo de 2022; a segunda — *os boletins passaram para outra área do storage* —
   ganhou evidência, porque existe outra área com dado atual. **Não foi testada:**
   sem listagem, achar o caminho depende de a Alup indicá-lo.
