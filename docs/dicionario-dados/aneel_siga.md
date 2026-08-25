# ANEEL — SIGA (empreendimentos de geração)

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ANEEL (CKAN), recurso `siga-empreendimentos-geracao.csv` |
| Endpoint | `dadosabertos.aneel.gov.br/api/3/action/datastore_search?resource_id=11ec447d-…` |
| Onda | 1 — API pública, sem credencial |
| Frequência | Semanal (o cadastro muda devagar) |
| Volume | ~25 mil empreendimentos por snapshot |
| Licença | ODbL |
| Credencial | nenhuma |

## Particularidades

- **É cadastro, não série temporal.** A API devolve o retrato completo, sem
  parâmetro de período: a janela é ignorada e `data_referencia` vem de
  `DatGeracaoConjuntoDados`, a data que a ANEEL declara para o conjunto.
- **Paginação obrigatória**: 1.000 registros por requisição (~26 chamadas).
- **Número em formato brasileiro**: vírgula decimal, e a ANEEL às vezes omite o
  inteiro (`,00` = zero). Campo vazio vira `NULL` — ausência de outorga não é
  potência zero.
- **É esta fonte que alimenta `codigo_usina`** (CodCEG) como dimensão comum.
  Sem ela, as fontes internas da Onda 3 não têm com o que cruzar.

## Campos

| Origem (SIGA) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `DatGeracaoConjuntoDados` | `data_referencia` | DATE | direto |
| `CodCEG` | `codigo_usina` | STRING | obrigatório; vazio é rejeitado |
| `NomEmpreendimento` | `nome` | STRING | obrigatório |
| `SigUFPrincipal` | `uf` | STRING | vazio → NULL |
| `SigTipoGeracao` | `tipo_geracao` | STRING | UHE, PCH, EOL, UFV, UTE, CGH |
| `DscFaseUsina` | `fase` | STRING | Operação, Construção, … |
| `DscOrigemCombustivel` | `origem_combustivel` | STRING | |
| `NomFonteCombustivel` | `fonte_combustivel` | STRING | |
| `DatEntradaOperacao` | `data_entrada_operacao` | DATE | |
| `MdaPotenciaOutorgadaKw` | `potencia_outorgada_kw` | NUMERIC | decimal brasileiro |
| `MdaPotenciaFiscalizadaKw` | `potencia_fiscalizada_kw` | NUMERIC | decimal brasileiro |
| `MdaGarantiaFisicaKw` | `garantia_fisica_kw` | NUMERIC | decimal brasileiro |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | data do conjunto |
| `submercado` | não | a ANEEL publica UF, não submercado — mapa UF→submercado é decisão da Onda 0 |
| `codigo_usina` | **sim — esta é a fonte da dimensão** | CodCEG |
| `agente_ccee` | não | o cadastro não traz o agente |
| `periodo_apuracao` | sim | derivado de `data_referencia` |

## Deduplicação

Chave natural: `codigo_usina`. Vence a ingestão mais recente. A Silver é o
**cadastro vigente**; o histórico de mudanças fica no Bronze append-only.

## Gold

`gold.parque_gerador` — usinas, potência fiscalizada, potência em operação,
potência em expansão e garantia física por UF, tipo e origem.
