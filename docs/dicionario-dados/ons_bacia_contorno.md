# ONS — Contornos das bacias hidrográficas do SIN

| Item | Valor |
|---|---|
| Fonte | Conjunto aberto `bacia_contorno` ("Contornos das Bacias Hidrográficas"), Dados Abertos do ONS (`https://dados.ons.org.br/dataset/bacia_contorno`) |
| Autor e licença | **ONS**, Creative Commons Attribution (**CC-BY**): o crédito ao ONS acompanha o dado onde ele for reutilizado |
| Onda | 1 — apoio ao item "INMET — precipitação histórica **por bacia**" da cláusula 4ª; decisão no [ADR 026](../arquitetura/decisoes/026-precipitacao-por-bacia.md) |
| Recurso | `Bacias_Hidrograficas_SIN.zip` (1,6 MB), com `.shp`, `.shx`, `.dbf`, `.prj`, `.cpg` e `.qmd`; achado pelo `package_show` do CKAN (`https://dados.ons.org.br/api/3/action/package_show?id=bacia_contorno`) |
| Formato | shapefile de polígonos em WGS84 (`GCS_WGS_1984`), atributos `ID` e `Nome_Bacia`, `.dbf` em **UTF-8** (o `.cpg` o declara) |
| Frequência | Retrato lido **todo dia 1 às 7h**; o conjunto muda raramente (`metadata_modified` do CKAN: 27/05/2024) |
| Janela | **não se aplica**: é um retrato. A data que vale é a que o CKAN declara, não a da leitura |
| Dono do dado (Alup) | domínio **Meteorologia** (apoio à chuva); o ONS é a origem |
| Credencial | nenhuma |

## Por que esta fonte existe no lake

O INMET entrega a chuva por estação, com latitude e longitude. A cláusula 4ª pede "por bacia". Ligar a estação à
bacia exige um polígono de bacia, e este é o conjunto do próprio ONS, o mesmo órgão cujos nomes de bacia a
`silver.ons_ear_bacia` já usa. A Gold da chuva
([`inmet_precipitacao.md`](inmet_precipitacao.md)) acrescenta a coluna `bacia` por ponto em polígono.

## O que o conjunto é, medido no arquivo real (03/10/2026, TLS ligado)

- **31 polígonos**, todos `POLYGON` de uma só parte (nenhum `MULTIPOLYGON` nem furo), de 196 a 15.855 vértices.
  O WKT tem em média **155 KB** por polígono (máximo de 627 KB; 4,8 MB no conjunto).
- `metadata_modified` do CKAN: **27/05/2024**; o `Last-Modified` do zip no S3 é de 03/11/2023. O conector usa o
  `metadata_modified` (é o que o CKAN declara para o conjunto).
- **Nomes de bacia, como vêm no `.dbf` (UTF-8, com acento):** Parnaíba, Correntes, Itajaí-Açu, Tapajós, Xingu,
  Grande, Iguaçu, Madeira, Paraná, Paranaíba, Paranapanema, São Francisco, Tietê, Tocantins, Uruguai, Antas, Manso,
  Uatuamã, Capivari, Araguari, Curuá-Una, Doce, Jacuí, Itabapoana, Itiquira, Jauru, Mucuri, Paraguaçu,
  Jequitinhonha, Jari, Paraíba do Sul.
- **"Uatuamã"** é como o ONS escreve no arquivo (o ADR 026 escrevia "Uatumã" antes de ler o shapefile, e foi
  corrigido); o conector não altera o nome.
- **6 polígonos têm autointerseção** (Iguaçu, Madeira, Paraná, Paranaíba, São Francisco e Tocantins, segundo o ADR 026,
  medido com `shapely`). O conector grava a geometria como veio; o reparo é da Silver (`make_valid`).
- **Cobertura em relação ao EAR:** 20 dos 23 nomes da `ons_ear_bacia` têm polígono (ignorando acento e caixa; o
  Itajaí aparece como `Itajaí-Açu`). **Sem polígono:** AMAZONAS, PARAGUAI e SANTA MARIA VIT. 11 polígonos não são nome de
  EAR (Correntes, Tapajós, Xingu, Madeira, Antas, Manso, Uatuamã, Curuá-Una, Itiquira, Jauru, Jari). Os nomes do
  EAR são em maiúsculas e sem acento: a Silver traz `bacia_chave` (ver Campos) para cruzar. Calculado localmente com os 31 nomes reais e os 23
  `nomecurto` do ADR 026, **19 casam** pela chave; o ADR dizia 20 por contar o Itajaí, mas `ITAJAI-ACU` não é `ITAJAI`
  (de-para manual). Sem casar: AMAZONAS, PARAGUAI, SANTA MARIA VIT e ITAJAI.
- **O contorno é "das bacias hidrográficas com aproveitamentos no SIN"**, segundo o próprio ONS: não cobre todo o
  território (ver "Granularidade").

## Campos

| Origem (shapefile) | Bronze | Silver | Tipo | Transformação |
|---|---|---|---|---|
| `metadata_modified` (CKAN) | `data_referencia` | `data_referencia` | DATE | só a data |
| `Nome_Bacia` | `nome_bacia` | `nome_bacia` | STRING | como veio, com acento |
| derivado de `Nome_Bacia` | — | `bacia_chave` | STRING | `UPPER(REGEXP_REPLACE(NORMALIZE(nome_bacia, NFD), r'[^[:ascii:]]', ''))`: maiúsculas, sem acento (`Paraná` vira `PARANA`); chave para `ons_ear_bacia.nomecurto` |
| `ID` | `id_bacia` | `id_bacia` | INT64 | 0 a 30 |
| geometria | `wkt` | `contorno` | STRING → GEOGRAPHY | WKT em longitude e latitude; a Silver faz `ST_GEOGFROMTEXT(wkt, make_valid => TRUE)` |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

**Anéis:** o anel externo do shapefile é horário e o furo é anti-horário; um polígono com vários anéis externos vira
`MULTIPOLYGON`, e o furo entra no último externo lido. O ONS hoje publica um anel por polígono, então a regra do furo
nunca foi exercida no dado real (só em teste).

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | a data que o CKAN declara, não a da leitura |
| `submercado` | não | a bacia não é submercado |
| `codigo_usina` | não | contorno não é dado de usina |
| `agente_ccee` | não | a origem é o ONS |
| `periodo_apuracao` | sim | `YYYY-MM` de `data_referencia` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural da Silver: (`nome_bacia`, `data_referencia`). Vence a ingestão mais recente. O mesmo shapefile lido todo
mês entra de novo no Bronze (append-only), e a Silver o reduz a 31 linhas; quando o ONS republicar com outra data de
modificação, as duas versões ficam na Silver e a Gold da chuva usa a mais recente de cada bacia.

## Gold que usa

`gold.precipitacao_diaria_estacao` (coluna `bacia`). Não há Gold própria: o contorno é insumo.

## Qualidade e observações

- **Falha alta.** Zip que não é zip, zip sem `.shp`, shapefile sem polígono, campo `Nome_Bacia` ausente e conjunto
  CKAN com número de recursos zip diferente de 1 levantam `LayoutInesperadoError`. Zero linhas como sucesso só
  apareceria dias depois, no alerta de silêncio (780 h).
- **Sem GDAL.** O shapefile é lido pelo `pyshp` (puro Python); o reparo da geometria fica no BigQuery.
- **Verificado em 03/10/2026:** o conector, com `requests` e a verificação de TLS ligada, leu o zip real: 31 polígonos,
  todos `POLYGON`, nomes legíveis em UTF-8, data de referência 27/05/2024, nenhuma exceção.

## O que não foi verificado

- **Nenhuma consulta espacial foi executada.** O `ST_GEOGFROMTEXT(..., make_valid => TRUE)` da Silver e o
  `ST_COVERS` da Gold só rodam no BigQuery (Dataform); os testes locais leem o SQL como texto e o `sqlglot` o
  analisa. Que o BigQuery aceite o WKT de 627 KB, o repare e devolva polígonos não vazios é hipótese até a primeira
  execução em hml.
- A execução do job no Cloud Run e o pico de memória (esperado pequeno: 1,6 MB de zip).
- Os mesmos limites do ADR 026: se a ANA publica polígonos melhores (o host tentado não resolveu).

## Linhagem

```
dados.ons.org.br (CKAN: bacia_contorno) → Bacias_Hidrograficas_SIN.zip (shapefile, ONS, CC-BY)
  → gs://<bucket>-raw/ons/bacia_contorno/dt=…/<ingestao_id>.json.gz
    → bronze.ons_bacia_contorno   (append-only, particionada por _ingestao_timestamp)
      → silver.ons_bacia_contorno (QUALIFY por bacia e data; contorno GEOGRAPHY com make_valid)
        → gold.precipitacao_diaria_estacao (colunas `bacia` e `bacia_chave`, por ponto em polígono)
```
