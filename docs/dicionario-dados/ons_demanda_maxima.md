# ONS — demanda máxima diária por subsistema

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `demanda_maxima_di` ("Demanda Máxima Diária por Subsistema") |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/demanda_maxima_di/DEMANDA_MAXIMA_DI_{ano}.csv` |
| Escopo | **Onda 1**, item "ONS Operacional" da cláusula 4ª ([ADR 027](../arquitetura/decisoes/027-ons-operacional-ipdo-acomph.md)) — arquivo público, sem credencial |
| Frequência | Diária (o ONS publica o dia anterior); o arquivo do ano é reescrito |
| Histórico | **2024 em diante.** O recurso de 2023 devolve 404; o catálogo CKAN lista 2024, 2025 e 2026 |
| Licença | CC-BY |
| Credencial | nenhuma |
| Volume verificado | 2024: 1.464 linhas; 2025: 1.460; 2026: 556 (até 19/05/2026, 4 subsistemas por dia), 48 KB — lidos em 03/10/2026 |

## Por que esta fonte existe no lake

Esta fonte cobre a **seção de demanda máxima (seção 7) do IPDO**. O IPDO em si
não é carregado: é um PDF preliminar de uso interno, sem histórico (ADR 027). O
resto do conteúdo do informativo está nas fontes que o ADR 027 lista
(`ons_balanco_energia`, `ons_carga`, `ons_carga_verificada`, `ons_ear`, entre
outras); a seção de demandas máximas era a única sem tabela no lake. Quem
acompanhar a Onda 1 deve ler que o item "ONS Operacional" depende do aceite da
Alup sobre a substituição proposta no ADR, e não que o IPDO foi entregue.

## Particularidades

- **Espaços nos identificadores.** `id_subsistema` chega como `"SE "`, `"N  "`
  e `nom_subsistema` como `" SUDESTE    "`; o conector apara os dois. Sem isso a
  sigla reprovaria na Silver.
- **Duas medidas com instantes próprios.** A demanda **instantânea** é a máxima
  do dia, em **MW**, com o minuto em que ocorreu. A **integralizada** é o valor
  na hora dessa máxima, em **MWmed** (o dicionário do ONS escreve
  "MWhmedio"); o instante dela é a hora cheia (HH:00) mais próxima do
  da instantânea (21:11 e 21:00; 22:37 e 23:00), por isso os dois não coincidem.
- **Só os quatro subsistemas.** Não há linha do SIN: o total do sistema, que o
  IPDO mostra, não está neste conjunto, e o lake não o soma (somar máximas de
  instantes diferentes não dá a máxima do SIN).
- **Nenhum campo vazio** e nenhuma chave `(subsistema, data)` repetida em 2024,
  2025 e 2026. Se vier vazio, o valor vira nulo, nunca zero; valor negativo é
  recusado pelo conector (a linha conta em `linhas_invalidas`), antes da Silver.
- **A série tem lacuna recente.** O arquivo de 2026 terminava em 19/05/2026 na
  leitura de 03/10/2026: a origem ainda não publicara o resto. A ingestão
  diária segue; os dias aparecem quando o ONS os publicar. O limite de silêncio
  de 26 h mede a ingestão, não a data do último dado.
- **Janela anterior a 2024** não encontra arquivo: o conector falha alto
  (`RuntimeError`) quando nenhum ano da janela existe, em vez de devolver zero
  linhas. Uma janela que cruza o ano baixa os dois arquivos, e o ano ainda sem
  arquivo é ignorado com aviso.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `id_subsistema` | `submercado` | STRING | trim + maiúsculas; só N, NE, S e SE |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `dat_referencia` | `data_referencia` | DATE | primeiros 10 caracteres (já ISO) |
| `val_demandaintegralizada` | `demanda_integralizada_mwmed` | NUMERIC | MWmed; vazio é nulo |
| `din_demandaintegralizada` | `instante_integralizada` | DATETIME | hora cheia da medida integralizada |
| `val_demandainstantanea` | `demanda_instantanea_mw` | NUMERIC | MW; vazio é nulo |
| `din_demandainstantanea` | `instante_instantanea` | DATETIME | instante, com minuto, da máxima instantânea |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da demanda |
| `submercado` | **sim** | N, NE, S ou SE |
| `codigo_usina` | não | demanda é agregada por subsistema |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`data_referencia`, `submercado`). Vence a ingestão mais recente —
o ONS reescreve o arquivo do ano e revisa dado publicado, como no `ons_carga`.
A janela diária é de 30 dias.

## Gold

`gold.demanda_maxima_mensal_subsistema` — por mês e subsistema: a maior demanda
instantânea do mês, o dia e o instante em que ocorreu, e o número de dias com
dado. Sem KPI e sem comparação entre subsistemas (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → DEMANDA_MAXIMA_DI_{ano}.csv
  → gs://<bucket>-raw/ons/demanda_maxima/dt=…/<ingestao_id>.json.gz
    → bronze.ons_demanda_maxima     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_demanda_maxima   (vigente; QUALIFY por data+subsistema, _ingestao_timestamp DESC)
        → gold.demanda_maxima_mensal_subsistema
```
