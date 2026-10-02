# ONS — Previsão versus programado de eólicas e solares

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `programacao_x_previsao` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/programacao_x_previsao/PROGRAMACAO_X_PREVISAO_{AAAA_MM_DD}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), item 16) — arquivo público, sem credencial |
| Frequência | Diária: **um arquivo por dia** (padrão C, base `OnsArquivoDiario`) |
| Histórico | 01/10/2024 a 02/10/2026: 730 arquivos de 732 dias possíveis. **Não há arquivo anterior a 01/10/2024** |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado | 23.904 a 30.144 linhas e 1,6 a 2,0 MB por arquivo; 1,27 GB nos 730 — lidos em 02/10/2026 |

## Por que esta fonte existe no lake

O ONS programa a geração das eólicas e solares com base numa previsão. As duas
coisas diferem, e a diferença é onde a programação do dia seguinte erra. Pedida
pela Alup em 28/09/2026.

## Como a janela vira arquivos

Um GET por dia da janela, na URL previsível — **não** se lista o catálogo CKAN
(`package_show`). Em 02/10/2026 o catálogo listava 721 CSV; o S3 tinha 730: o
catálogo omitia 9 arquivos que existem. A resposta 404 é o "dia sem arquivo":
fica como aviso no log e a execução segue. Se a janela tem 3 dias ou mais e
**nenhum** arquivo existe, é erro (URL quebrada), porque uma execução em
SUCESSO com zero linha escaparia do alerta de silêncio.

- **Quando o arquivo aparece:** o arquivo do dia D é gravado no fim da tarde ou
  à noite de D-1 (o de 02/10 tem `Last-Modified` 01/10 21:08 GMT) e, nas
  amostras vistas, não é regravado depois. A janela diária de 3 dias existe
  para cobrir execução perdida.
- **Buracos reais no S3:** 14/02/2025 e 26/03/2025 (sem arquivo, 404). O ONS
  avisa que o dado "pode ser atualizado após a publicação"; a Silver deduplica
  por `_ingestao_timestamp` mais recente se uma janela reabrir o dia.

## Tempo e recarga

Medido contra o dado real em 02/10/2026, só extração e validação: ~2 s por
arquivo (mediana 2,4 s numa varredura com 8 conexões, máximo 8,5 s). Sequencial,
730 arquivos passam de 1.800 s, o limite do Cloud Run: a recarga de 24 meses
**não cabe numa execução** e segue o runbook (janelas de até 3 meses; 92
arquivos ≈ 3 a 4 minutos de extração, 2,8 milhões de linhas por janela).
Como a carga no BigQuery e a gravação do raw não foram medidas aqui, a primeira
janela de uma recarga é a medida: se passar de ~900 s, reduzir para 2 meses.
A execução diária (3 dias, ~81 mil linhas) leva segundos.

## Particularidades

- **A data vem como `AAAAMMDD`** (`20261002`), sem hífen — diferente do
  `balanco_dessem_geral`, que vem ISO.
- **A unidade é a usina do PDP** (`cod_usinapdp`, ex.: `MMRAL`, `D2EOLI`), um
  código próprio do ONS. **Não é o CEG**: `codigo_usina` fica nulo na Silver e
  o cruzamento com `gold.de_para_usina` não existe ainda. Muitas "usinas" são
  conjuntos (`CJFVRIOALTO`, `CJ TANQUE NOVO`).
- **Código e nome vêm preenchidos com espaços à direita** (largura fixa 12 e
  30); a conversão faz trim. Há 628 códigos e 627 nomes num mesmo dia: um nome
  se repete para dois códigos.
- **48 patamares por dia** (1 a 48), em todos os 730 arquivos. O dicionário do
  ONS não diz a que hora cada patamar corresponde, e o conector **não deriva
  hora**. Presume-se meia hora (48 por dia), mas isso não foi confirmado.
- **Sem negativo e sem vazio**, nos 730 arquivos, em qualquer coluna; o
  dicionário do ONS proíbe negativo e nulo. Negativo é recusado.
- **Nenhuma chave `(dia, patamar, código)` repetida** em nenhum arquivo.
- **Encoding:** UTF-8 em todos os 730 (acentos corretos). A leitura decodifica
  linha a linha e cai em ISO-8859-1 se uma linha não for UTF-8, como os demais
  conectores do ONS.
- O arquivo do dia tem sempre uma única data (a do nome); a coluna de data
  nunca divergiu do nome.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `dat_programacao` | `data_referencia` | DATE | `AAAAMMDD` → data |
| `num_patamar` | `patamar` | INT64 | 1 a 48 |
| `cod_usinapdp` | `codigo_usina_pdp` | STRING | trim; vazio é recusado |
| `nom_usinapdp` | `nome_usina` | STRING | trim; vazio é recusado |
| `val_previsao` | `previsao_mw` | NUMERIC | MW; negativo é recusado |
| `val_programado` | `programado_mw` | NUMERIC | MW; negativo é recusado |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da programação |
| `submercado` | **não** | a origem não traz subsistema |
| `codigo_usina` | **não** | o código do PDP não é o CEG; fica em `codigo_usina_pdp` |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `patamar`, `codigo_usina_pdp`). Vence a
ingestão mais recente.

## Gold

`gold.previsao_x_programado_mensal_usina` — responde "o quanto a previsão do
ONS divergiu do programado, por usina e mês": médias de previsão e programado,
diferença média com sinal e diferença absoluta média e máxima, em MW por
patamar. Sem KPI (ADR 012): nenhuma razão entre as séries.

## O que não foi verificado

- A hora que cada patamar cobre (o dicionário não diz).
- O tempo de carga no BigQuery e de gravação do raw para uma janela de 3 meses
  (só roda no Cloud Run).
- Se um arquivo antigo é regravado pelo ONS: nas 5 amostras de `Last-Modified`
  o arquivo do `programacao_x_previsao` não foi regravado.
- O significado de cada código PDP (não há cadastro público do PDP aqui).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → PROGRAMACAO_X_PREVISAO_{AAAA_MM_DD}.csv (um por dia)
  → gs://<bucket>-raw/ons/programacao_previsao/dt=…/<ingestao_id>.json.gz
    → bronze.ons_programacao_previsao   (append-only, particionado por _ingestao_timestamp)
      → silver.ons_programacao_previsao (vigente; QUALIFY por dia+patamar+usina, _ingestao_timestamp DESC)
        → gold.previsao_x_programado_mensal_usina
```
