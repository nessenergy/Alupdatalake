# ANEEL — Tarifas homologadas das distribuidoras

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ANEEL, dataset `tarifas-distribuidoras-energia-eletrica` ("Tarifas de aplicação das distribuidoras de energia elétrica") |
| Recurso | CSV `tarifas-homologadas-distribuidoras-energia-eletrica.csv` (id `fcf2906c-7c32-4b9b-a637-054e7a5234f4`) |
| Endpoint | `dadosabertos.aneel.gov.br/dataset/5a583f3e-1646-4f67-bf0f-69db4203e89e/resource/fcf2906c-7c32-4b9b-a637-054e7a5234f4/download/tarifas-homologadas-distribuidoras-energia-eletrica.csv` |
| Escopo | **Onda 1**, linha "ANEEL tarifas regulatórias" da proposta (`raw.aneel_tarifas`); pedido de carga cobrado pela Alup em 02/10/2026. Não é Aditivo 01 |
| Frequência | Semanal, segundo o CKAN; o PDF do dicionário diz mensal (ver "Frequência") |
| Cobertura | Vigências de 2010-02-03 a 2026-09-22 (início) e até 2027-09-21 (fim); 115 CNPJ de distribuidora |
| Volume | 89.235.715 bytes, 328.293 linhas, 17 colunas (02/10/2026) |
| Licença | a do catálogo da ANEEL (não conferida aqui) |
| Credencial | nenhuma |

## Por que esta fonte existe no lake

A tarifa homologada é o preço regulado da energia na distribuição: a TUSD (uso
do sistema) e a TE (energia), por distribuidora, subgrupo, modalidade e posto
horário, com a vigência que a resolução fixou. É a referência para quem compara
mercado cativo e mercado livre. Pedida pela Alup (Eduardo Pires, 02/10/2026) como
"Tarifas Homologadas".

## Descoberta: o que o recurso é

- **Um arquivo único, reescrito inteiro** pela ANEEL. Não há um arquivo por
  ano nem parâmetro de período. O CKAN publica o mesmo conteúdo em CSV, em XML
  (323 MB) e no datastore (`datastore_active`, `datastore_search` com
  `resource_id`; `datastore_search_sql` **não existe** neste CKAN).
- **Formato lido: o CSV.** Separador `;`, tudo entre aspas, UTF-8 (sem BOM
  visto), CRLF. Decimal com vírgula e sem separador de milhar; o zero vem como
  `,00`. Datas ISO. O datastore pagina a 1.000 linhas (329 requisições para o
  arquivo todo), e o CSV em stream é uma só.
- **URL estável** pelo id do recurso; o nome do arquivo não carrega data.
  `Last-Modified` e `ETag` existem (`Last-Modified` de 02/10/2026 10:01 GMT).
- **A coluna `DatGeracaoConjuntoDados` vale o dia da geração** do arquivo
  (`2026-10-02` em todas as linhas), não uma data do negócio.
- **O que versiona é a vigência**, não o arquivo: cada linha carrega
  `DatInicioVigencia`, `DatFimVigencia` e a resolução (`DscREH`). Uma nova
  resolução adiciona linhas com nova vigência; o arquivo antigo não vira
  histórico.

## Como a janela de datas se aplica

A janela recorta pelo **início da vigência** (`DatInicioVigencia`), na extração.
O conector lê o arquivo inteiro em stream, descarta o que está fora da janela e
entrega o resto.

- **Recarga:** janela de 2010-02-03 em diante, de uma vez (328.293 linhas,
  validadas sem uma inválida; o runner carrega em lotes de 50 mil).
- **Execução semanal:** janela de 400 dias (`ultimos_dias = 400`), cerca de 50 mil
  linhas. Cobre um ciclo tarifário inteiro, para apanhar correção de uma
  vigência publicada meses antes.
- **Limite do recorte:** uma vigência que começou antes da janela e continua
  valendo **não entra**. Se a ANEEL corrigir o valor de uma vigência com início
  anterior a 400 dias, a execução semanal não vê; só uma recarga com janela
  maior vê. Se a ANEEL faz correção retroativa assim, **não se sabe** (não há
  histórico do arquivo para comparar).

## Particularidades vistas no arquivo real de 02/10/2026

- **`Não se aplica` é texto**, não vazio, em classe (205.987 linhas), subclasse,
  detalhe, posto e acessante. O Bronze guarda como veio; a Silver o troca por
  NULL.
- **Dois "preços" por linha de tarifa**: `DscBaseTarifaria` é `Tarifa de
  Aplicação` (164.634 linhas, a que a distribuidora usa para faturar, segundo o
  dicionário da ANEEL) ou `Base Econômica` (163.659, "valores utilizados
  estritamente para cálculo tarifário"). São quase espelhos; a Gold usa só a de
  aplicação.
- **Unidade:** `DscUnidadeTerciaria` é `kW` (99.408) ou `MWh` (228.885) e é a
  grandeza da TUSD. A TE é R$/MWh e **é zero em toda linha em kW**.
- **`,00` é zero de verdade** (TE zero em 144.645 linhas, TUSD zero em 5.388).
  Nenhum valor vazio, nenhum negativo, no máximo 7 caracteres.
- **Resolução vazia em 274 linhas** (CEA, 2026-04-13); **`DESPACHO` e `DSP
  RETIFICAÇÃO`** no lugar de resolução em 524 linhas; `N°` e `Nº` convivem. O
  número da resolução **não ordena no tempo** (a nº 3.556 é de 12/2025 e a
  nº 3.318, de 08/2026): o conector não deriva ordem dele.
- **Acessante vazio em 22 linhas** (o exemplo visto é Neoenergia Brasília, 2010); nas outras, `Não
  se aplica` (regra geral) ou a sigla de um acessante nominal (896 valores).
- **A sigla muda para o mesmo CNPJ** (`CPFL JAGUARI` e `CPFL Santa Cruz`; `RGE` e
  `RGE SUL`): a identidade é o CNPJ, 115 deles, 116 siglas.
- **Chave natural repetida.** Com a chave (CNPJ, início, fim, base, subgrupo,
  modalidade, classe, subclasse, detalhe, posto, unidade, acessante) há 870 chaves
  em mais de uma linha, de 2010 a 2021: 295 com **resoluções diferentes e valor
  diferente** (a REH nº 959 e a nº 1.030 de 2010 fixam a mesma vigência) e **516 com a
  mesma resolução** (2010 a 2018; a origem não diz qual vale). Sem o `fim` na chave
  havia 1.290, entre elas as 174 da Ceraçá de 2025, cujo `fim` difere (2025-12-31
  e 2026-09-29).
- **Vigências sobrepostas hoje:** em 02/10/2026, das 10.366 chaves (sem início e
  fim) com tarifa de aplicação em vigor, 517 têm mais de uma vigência cobrindo o
  dia (a nova começou antes de a velha acabar). A Gold fica com a que começou por
  último.
- **81 das 115 distribuidoras** têm vigência em 02/10/2026. As 34 restantes não
  têm linha cobrindo o dia; **não foi verificado por quê** (extinção,
  incorporação, ou reajuste ainda não publicado).
- **Picos de vigência:** 2026-01 concentra 25.136 linhas (reajuste em lote); a
  vigência mais nova do arquivo é 2026-09-22.

## Frequência

Três respostas que não batem: o CKAN declara **Semanal**; o PDF do dicionário
(15/03/2022) diz **Mensal**; e o recurso foi regerado em 02/10/2026 (`Last-Modified`
10:01 GMT, mesma data de `DatGeracaoConjuntoDados`), uma sexta-feira, fora do
sábado em que o `componentes-tarifarias` se atualizou (26 e 27/09). O
agendamento é **semanal** (segunda, 9h), o que cobre as duas hipóteses; o limite
de silêncio é 180 h, como os outros semanais. **Não foi verificado** quantas
vezes por semana o arquivo muda: só se viu um carimbo.

## Os conjuntos vizinhos: por que não são a mesma coisa

Não foram implementados.

| Conjunto | O que é | Por que não é este |
|---|---|---|
| `componentes-tarifarias` | A **decomposição** da TE e da TUSD: uma linha por componente (`TUSD_CDE_COVID`, `TE_TRANSPORTE_ITAIPU`, ...), colunas `DscComponenteTarifario` e `VlrComponenteTarifario`. CSV por ano de 2012 a 2026, de 200 MB a 829 MB cada, e Parquet de 4 a 16 MB | Responde "do que a tarifa é feita", não "quanto vale". As colunas de vigência e de combinação tarifária coincidem, mas o valor é de componente (notação científica, `8,9999999999999995E-9`) e o volume é de duas ordens de grandeza acima. A tarifa fechada é a deste conjunto |
| `bandeiras-tarifarias` | A cor da bandeira por mês de competência (`Verde`, `Amarela`, `Vermelha P1`...) e o adicional em R$ por 100 kWh, mais a conta bandeira. Mensal, de 01/2015 em diante, SIN inteiro | Não é por distribuidora nem por subgrupo, é um adicional **sobre** a tarifa, e vem de outra regra (Proret 6.8). Não é a tarifa homologada |

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `DatInicioVigencia` | `data_referencia` | DATE | ISO; é a data pela qual a janela recorta |
| `DatGeracaoConjuntoDados` | `data_geracao` | DATE | ISO |
| `DatFimVigencia` | `fim_vigencia` | DATE | ISO; nunca menor que o início (0 casos) |
| `DscREH` | `reh` | STRING | vazio vira NULL; texto da resolução ou do despacho |
| `SigAgente` | `sigla_distribuidora` | STRING | trim |
| `NumCNPJDistribuidora` | `cnpj_distribuidora` | STRING | 14 dígitos, zero à esquerda preservado; outro tamanho é recusado |
| `DscBaseTarifaria` | `base_tarifaria` | STRING | `Tarifa de Aplicação` ou `Base Econômica` |
| `DscSubGrupo` | `subgrupo` | STRING | 13 valores: A1, A2, A3, A3a, A4, A4a, A4b, AS, B, B1, B2, B3, B4 |
| `DscModalidadeTarifaria` | `modalidade` | STRING | 14 valores (Azul, Verde, Branca, Convencional, Geração, Distribuição, variantes ABRACE, ...) |
| `DscClasse` | `classe` | STRING | Bronze: como veio; Silver: `Não se aplica` vira NULL |
| `DscSubClasse` | `subclasse` | STRING | idem |
| `DscDetalhe` | `detalhe` | STRING | idem; APE, SCEE, TIPO 01, TIPO 02, `<500GWh`... |
| `NomPostoTarifario` | `posto` | STRING | idem; Ponta, Fora ponta, Intermediário, Ponta/Fora ponta seca ou úmida |
| `DscUnidadeTerciaria` | `unidade` | STRING | `kW` ou `MWh`: a grandeza da TUSD |
| `SigAgenteAcessante` | `acessante` | STRING | vazio vira NULL no Bronze; `Não se aplica` vira NULL na Silver |
| `VlrTUSD` | `tusd` | NUMERIC | R$/kW ou R$/MWh conforme `unidade`; `,00` é 0 |
| `VlrTE` | `te` | NUMERIC | R$/MWh; `,00` é 0 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | início da vigência |
| `submercado` | **não** | a tarifa é da distribuidora; a área de concessão não é submercado |
| `codigo_usina` | **não** | distribuidora não é usina |
| `agente_ccee` | **não** | o arquivo traz o CNPJ da distribuidora, não o perfil CCEE; o cruzamento por CNPJ com `ccee_perfil` não foi feito |
| `periodo_apuracao` | sim | `YYYY-MM` do início da vigência |
| `periodo_apuracao_ccee` | não | a origem é a ANEEL |

## Deduplicação

Chave natural da Silver: (`cnpj_distribuidora`, `data_referencia`,
`fim_vigencia`, `base_tarifaria`, `subgrupo`, `modalidade`, `classe`,
`subclasse`, `detalhe`, `posto`, `unidade`, `acessante`, `reh`). Vence a
ingestão mais recente (a leitura em que a ANEEL corrigiu o valor), com
desempate pelo maior valor.

- **A resolução entra na chave** porque o dado tem duas resoluções para a mesma
  vigência e o número não diz qual é a mais nova; a Silver guarda as duas e a
  Gold escolhe pela vigência.
- **O desempate pelo maior valor não tem sentido regulatório.** Serve só para o
  resultado ser o mesmo a cada execução. Afeta as 516 chaves repetidas com a
  mesma resolução, que são de 2010 a 2018 e fora de qualquer consulta de
  vigente. A origem deve esclarecer.

## Gold

`gold.tarifa_vigente_distribuidora` — responde "quanto cada distribuidora cobra
hoje de TUSD e de TE, por subgrupo, modalidade, classe, subclasse, detalhe, posto,
acessante e unidade". Só a Tarifa de Aplicação, a vigente no dia da execução
(`vigente_em`), a de início mais recente quando duas cobrem o dia. TUSD e TE
ficam separadas: nem sempre estão na mesma unidade, e somá-las seria inventar um
número. Sem KPI e sem comparar distribuidoras (ADR 012). Em 02/10/2026 seriam
10.366 linhas, de 81 distribuidoras.

## Agendamento

Cloud Scheduler semanal, segunda 9h, janela de 400 dias (`infra/modules/scheduler`).
Limite de silêncio de 180 h (`includes/silencio.js` e `infra/modules/monitoramento`).
Memória padrão: o dry-run local com a janela de 400 dias leu 50.202 linhas com 46 MiB
de pico e 62 s (com `tracemalloc` ligado, que encarece).

## O que foi verificado e como

- O arquivo real foi baixado em 02/10/2026 e lido pelo conector, sem fixture: 328.293
  linhas, **nenhuma recusada** pelo schema, na janela cheia; 50.202 na janela de
  09/2025 a 02/10/2026.
- Cabeçalho, separador, encoding, tipos, vazios, `,00`, negativos e chaves repetidas
  foram medidos no arquivo inteiro.
- A fixture (`tests/fixtures/aneel_tarifas.csv`) tem 11 linhas **reais** do arquivo.
- A Gold e a Silver foram lidas pelo `sqlglot` (`tests/unit/test_sql.py`).

## O que não foi verificado

- A execução no Cloud Run e no Dataform: só ocorre no deploy; as `ASSERTIONS` da
  Silver nunca rodaram contra o BigQuery.
- Se a ANEEL reescreve vigências antigas (correção retroativa) e com que
  frequência o arquivo muda; só se viu um carimbo.
- Por que 34 das 115 distribuidoras não têm vigência em 02/10/2026.
- Qual das duas resoluções da mesma vigência a ANEEL considera a válida: os 295
  casos são antigos (até 2021) e a Gold usa a vigência mais nova, não a resolução.
- O texto da licença e se o recurso XML ou o datastore são mais baratos: só o CSV foi lido.
- O cruzamento por CNPJ com os cadastros da CCEE.
- A linha "ANEEL tarifas regulatórias" da proposta: citada pelo briefing da tarefa;
  o texto da proposta não está neste repositório.

## Linhagem

```
dadosabertos.aneel.gov.br → tarifas-homologadas-distribuidoras-energia-eletrica.csv (um arquivo, em stream)
  → gs://<bucket>-raw/aneel/tarifas/dt=…/<ingestao_id>.json.gz
    → bronze.aneel_tarifas   (append-only, particionado por _ingestao_timestamp)
      → silver.aneel_tarifas (vigência por linha; QUALIFY pela chave natural + reh, _ingestao_timestamp DESC)
        → gold.tarifa_vigente_distribuidora
```
