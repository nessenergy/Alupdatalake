# ADR 026 — Precipitação do INMET por bacia: ponto em polígono com os contornos do ONS

**Status**: implementado (fonte `ons_bacia_contorno` e coluna `bacia` na Gold da chuva), **ainda não aceito**: só vira "aceito" depois da conversa de fechamento com a Alup sobre a cobertura (39% das estações sem bacia, 3 bacias do EAR sem polígono) · **Data**: 2026-10-03 · **Relaciona-se** com a cláusula 4ª (Onda 1,
"INMET — precipitação histórica por bacia") e com o dicionário de
[`ons_ear_bacia`](../../dicionario-dados/ons_ear_bacia.md)

## 1. Contexto

O INMET entrega a chuva **por estação**, com latitude e longitude. A cláusula pede "por
bacia". Ligar estação a bacia exige uma fonte de bacias. O lake já usa bacias: a
`silver.ons_ear_bacia` agrupa pelo `nomecurto` do ONS (23 nomes em 2026, lidos do CSV de 2026
em 03/10/2026: AMAZONAS, ARAGUARI, CAPIVARI, DOCE, GRANDE, IGUACU, ITABAPOANA, ITAJAI, JACUI,
JEQUITINHONHA, MUCURI, PARAGUACU, PARAGUAI, PARAIBA DO SUL, PARANA, PARANAIBA, PARANAPANEMA,
PARNAIBA, SANTA MARIA VIT, SAO FRANCISCO, TIETE, TOCANTINS, URUGUAI). Qualquer recorte novo
deve coincidir com esses nomes, para que chuva e armazenamento se cruzem.

## 2. Evidência levantada (03/10/2026, TLS ligado)

Fatos verificados:

- **CKAN da ANEEL** (`dadosabertos.aneel.gov.br/api/3/action/package_search`): 200, 72 conjuntos
  no total; as buscas `bacia`, `precipitacao`, `hidrografica`, `hidr`, `pluviom` e `estacoes`
  voltam com **0 conjuntos**; `chuva` acha só `evento-situacao-de-emergencia`. A ANEEL não
  publica polígono de bacia nem chuva por bacia.
- **CKAN do ONS** (`dados.ons.org.br/api/3/action/package_search`), busca `bacia`: 200, 3
  conjuntos. `ear-diario-por-bacia` e `ena-diario-por-bacia` (só nome de bacia, sem geometria)
  e **`bacia_contorno`** ("Contornos das Bacias Hidrográficas", licença Creative Commons
  Attribution, `metadata_modified` 27/05/2024).
- **`bacia_contorno`** tem um recurso, `Bacias_Hidrograficas_SIN.zip`
  (`ons-aws-prod-opendata.s3.amazonaws.com/dataset/bacia_contorno/Bacias_Hidrograficas_SIN.zip`,
  200, 1,6 MB, sem credencial): shapefile em WGS84 (`GCS_WGS_1984`), 31 polígonos, atributos
  `ID` e `Nome_Bacia`. Descrito pelo próprio ONS como os contornos "das bacias hidrográficas com
  aproveitamentos no SIN".
- **Cruzamento de nomes** com o EAR: 20 dos 23 nomes do EAR têm polígono (por nome, ignorando
  acento e caixa; Itajaí aparece como `Itajaí-Açu`). **Correção (03/10/2026, na implementação):** pela chave
  normalizada (maiúsculas e sem acento) são **19 de 23**, porque `ITAJAI-ACU` não é `ITAJAI`; o texto original
  fica como foi escrito, e o Itajaí exige um de-para manual. **Sem polígono**: AMAZONAS, PARAGUAI e
  SANTA MARIA VIT. O shapefile traz 11 polígonos que não são nome de EAR (Correntes, Tapajós,
  Xingu, Madeira, Antas, Manso, Uatuamã, Curuá-Una, Itiquira, Jauru, Jari).
- **Qualidade da geometria**: 6 dos 31 polígonos têm **autointerseção** (Iguaçu, Madeira, Paraná,
  Paranaíba, São Francisco, Tocantins) e `ST_CONTAINS` ingênuo os ignora ou o BigQuery os
  recusa; reparados com `make_valid` (shapely), as sobreposições entre bacias ficam em 3 pares
  de área desprezível (Tapajós/Madeira 0,3 grau², Madeira/Jauru 0,01, Paraná/Paranapanema 0,08).
- **Teste real de ponto em polígono**: `apitempo.inmet.gov.br/estacoes/T` (200) lista 672
  estações com coordenadas. Com os polígonos reparados, **408 caem em alguma bacia (61%), 264
  ficam fora (39%)**, e 1 cai em duas. Os percentuais são sobre as **672 estações da lista do INMET**, não
  sobre as que têm histórico de chuva. Contagem por bacia: Tocantins 53, Paraná 51, São
  Francisco 48, Uruguai 45, Grande 25, Paranaíba 23, Tapajós 23, Parnaíba 22, Paraíba do Sul 18,
  Xingu 14, Madeira 13, Paranapanema 13, Tietê 13, Iguaçu 12, Doce 10, Jequitinhonha 6, Jacuí 5,
  Antas 4, Paraguaçu 4, Itajaí-Açu 2, e 1 cada em Manso, Curuá-Una, Araguari, Itabapoana e Mucuri.
- **`precipitacao-estacao` do ONS** (`dados.ons.org.br`, `package_show`): só os anos 2020 e 2021
  (CSV), última modificação 28/04/2026. Não resolve o histórico recente.

Não verificado (hipótese): a ANA publica polígonos de bacia (o host
`dadosabertas.ana.gov.br`, que tentei, não resolve; não foi procurada outra URL). Se um dia o
recorte do ONS não bastar, é a fonte alternativa a investigar. Também não foi conferido se as
672 estações da lista incluem as já desativadas, que existem no histórico do INMET.

## 3. Alternativas

**A. Ponto em polígono com `bacia_contorno` do ONS.** Os polígonos são do próprio ONS, e 20 dos
23 nomes do EAR casam. Custo: fonte nova (os 7 componentes), leitura de shapefile em ZIP e
reparo de 6 geometrias. Cobre 61% das estações atuais; as demais ficam sem bacia.

**B. Estação mais próxima de uma usina ou reservatório do ONS.** Exigiria coordenadas das
usinas, que não foram achadas em nenhum conjunto listado. Além disso "mais próxima" não é "dentro
da bacia". **Descartada**: sem fonte de coordenadas.

**C. Entregar por estação e UF e pedir à Alup que aceite o recorte.** Sem custo de fonte nova,
mas deixa de entregar o "por bacia" da cláusula, quando existe fonte pública e gratuita que o
entrega em boa parte do território.

## 4. Decisão

A decisão é **híbrida**: **A** para o que cai nos contornos do ONS e **C** para o resto (estação com `bacia`
nula, entregue por estação e UF).

**Alternativa A**, com a regra de que **a chuva continua entregue por estação** e a bacia é uma
coluna a mais, não um agregado que esconda estação:

1. Fonte nova `ons_bacia_contorno` (conjunto estático: ZIP lido, polígonos reparados e gravados
   como WKT; precedente de fonte-retrato com data declarada pela origem: `aneel_siga`).
2. A Gold da chuva liga cada estação ao polígono por `ST_CONTAINS` e normaliza o nome
   (`trim`, maiúsculas, sem acento) para casar com `bacia` da `silver.ons_ear_bacia`.
3. Estação fora de qualquer polígono sai com `bacia` nula e a UF preenchida, nunca com bacia
   inventada (é a parte C da decisão). A Gold expõe também quantas estações entraram em cada bacia e quantas ficaram sem.
4. Bacias do EAR sem polígono (AMAZONAS, PARAGUAI, SANTA MARIA VIT) ficam sem chuva, e isso é
   declarado na documentação. Não se soma Tapajós, Xingu etc. para fabricar AMAZONAS: o ONS não
   diz que é essa a composição.

## 5. Consequências

- **Gold e fonte**: uma fonte nova (`ons_bacia_contorno`, sete componentes) e uma junção
  espacial na Gold de chuva. Estimativa: 12 a 16 horas, incluindo a leitura do shapefile,
  o reparo das geometrias e os testes. A leitura do shapefile precisa de dependência de leitura
  de shapefile ou de conversão prévia; a escolha fica para a tarefa de implementação.
- **Granularidade**: o polígono "Paraná" não contém Grande, Paranaíba nem Paranapanema (os
  contornos são faixas, não aninhados). A chuva "do Paraná" é a da faixa do polígono, e a
  documentação deve dizer isso.
- **Agregação por bacia** (média das estações, ponderada ou não) é decisão metodológica que
  este ADR não toma. A primeira entrega fica na estação com a bacia ao lado; a média por
  bacia, se a Alup quiser, entra com a regra escrita por ela.
- **Para a Alup**: informar por escrito que 39% das estações atuais ficam fora dos contornos
  do ONS (litoral, Nordeste e Norte sem aproveitamentos do SIN) e que 3 bacias do EAR não têm
  polígono. Pedir confirmação de que o recorte "por bacia" cobre as bacias do ONS e não todo o
  território; se não, vale a saída C para o restante (por estação e UF).
- **Licença e crédito**: o conjunto `bacia_contorno` é CC-BY, que exige crédito ao ONS na documentação e na
  linhagem; o crédito já consta em [`ons_bacia_contorno`](../../dicionario-dados/ons_bacia_contorno.md).
- **Plano**: acrescentar tarefa de implementação (fonte `ons_bacia_contorno` e junção na
  Gold). Este ADR não escreve código.
