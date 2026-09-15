# ONS — capacidade instalada por unidade geradora

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `capacidade-geracao` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/capacidade-geracao/CAPACIDADE_GERACAO.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Recurso único (sem ano/mês) — cadastro, não série |
| Volume verificado | 5.679 linhas, 1,2 MB — lido em 14/09/2026 |
| Encoding | UTF-8 (confirmado: zero linhas exclusivamente ISO-8859-1) |
| Licença | CC-BY |
| Credencial | nenhuma |

## Particularidades

- **É cadastro, não série temporal** — como o `aneel_siga` e o `ccee_perfil`:
  a janela é ignorada (ADR 013), e o retrato completo é lido a cada execução.
- **Sem campo de data próprio, e sem CKAN.** O `aneel_siga` tem
  `DatGeracaoConjuntoDados` no próprio registro; o `ccee_perfil` não tem campo
  de data, mas tem o `last_modified` que o CKAN declara para o recurso. O ONS
  publica direto no S3 — sem catálogo —, então `data_referencia` vem do
  cabeçalho HTTP `Last-Modified` que o próprio S3 devolve para o arquivo. Sem
  o cabeçalho, assume a data corrente e registra aviso — mesmo comportamento
  do `ccee_perfil` sem `last_modified`.
- `nom_subsistema` **vem com espaços à direita** (`"NORDESTE       "`); o
  conector aplica `.strip()`.
- `ceg` pode vir como `"-"` quando a unidade não tem CEG — vira `NULL`.
- `dat_entradateste`, `dat_entradaoperacao` e `dat_desativacao` são ISO e
  **podem vir vazias** (`dat_desativacao` quase sempre) — vazio vira `NULL`.

## O achado desta entrega: `codigo_usina` sem depender da Lacuna 1

O `codigo_usina` (dimensão comum do projeto) hoje só é preenchido pelo
`aneel_siga`, com o CodCEG. A [issue #141](https://github.com/nessenergy/Alupdatalake/issues/141)
pede à Alup um de-para de quatro colunas — sigla interna ↔ CEG ↔ nome CCEE ↔
nome ONS — porque nenhuma fonte interna trazia as duas pontas ao mesmo tempo.

Esta fonte (e a `ons_geracao_usina`) trazem a coluna `ceg` **junto do nome da
usina como o ONS o publica** (`nom_usina`). Isso entrega o lado CEG ↔ nome ONS
do de-para **sem depender de ninguém**: a Silver já preenche `codigo_usina`
com o CEG (nulo quando a origem publica traço ou vazio), e a junção ONS ↔
ANEEL passa a ser possível por `codigo_usina` diretamente. O que ainda falta
na #141 se reduz a uma coisa só: sigla interna ↔ CEG.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `Last-Modified` (cabeçalho HTTP) | `data_referencia` | DATE | ver particularidades acima |
| `id_subsistema` | `submercado` | STRING | trim, maiúsculas; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim (espaços à direita) |
| `id_estado` | `uf` | STRING | trim |
| `nom_estado` | `nome_uf` | STRING | trim |
| `nom_modalidadeoperacao` | `modalidade_operacao` | STRING | trim |
| `nom_agenteproprietario` | `agente_proprietario` | STRING | trim |
| `nom_agenteoperador` | `agente_operador` | STRING | trim |
| `nom_tipousina` | `tipo_usina` | STRING | trim |
| `nom_usina` | `nome_usina` | STRING | trim |
| `ceg` | `codigo_usina` | STRING | `"-"` ou vazio → NULL — **é o CEG** |
| `nom_unidadegeradora` | `nome_unidade_geradora` | STRING | trim |
| `cod_equipamento` | `codigo_equipamento` | STRING | trim; chave da unidade geradora |
| `num_unidadegeradora` | `numero_unidade_geradora` | STRING | trim |
| `nom_combustivel` | `combustivel` | STRING | trim |
| `dat_entradateste` | `data_entrada_teste` | DATE | vazio → NULL |
| `dat_entradaoperacao` | `data_entrada_operacao` | DATE | vazio → NULL |
| `dat_desativacao` | `data_desativacao` | DATE | vazio → NULL (quase sempre) |
| `val_potenciaefetiva` | `potencia_efetiva` | NUMERIC | direto; unidade não confirmada pela fonte no catálogo público |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | data do retrato (`Last-Modified` do S3) |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | **sim — o CEG** | nulo quando a origem publica traço ou vazio (ver achado acima) |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` do retrato |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: `codigo_equipamento` — a unidade geradora, não a usina (uma
usina tem várias unidades). Vence a ingestão mais recente, como no
`aneel_siga`: é cadastro, não série, então a dedup não é por data.

## Gold

`gold.capacidade_instalada_vigente_usina` — soma da potência efetiva por
usina, separando o que está ativo (sem `data_desativacao`) do total. Sem KPI
(ADR 012).

## Qualidade e observações

- **Dry-run contra a API real (15/09/2026)**: 5.678 extraídos, **10
  inválidos**, `SUCESSO` em 2,9s. Os 10 inválidos trazem `id_subsistema = "PY"`
  — unidades do lado paraguaio de interligação (não uma das quatro siglas do
  lake). Rejeitado por desenho, não por falha: o projeto trata sigla nova de
  submercado como dado que precisa de revisão de contrato antes de entrar
  silenciosamente (mesma regra do `ons_carga` e do `ccee_perfil`). Se a Alup
  precisar desse recorte, é uma revisão de escopo, não um bug.
- A data do retrato depende do cabeçalho `Last-Modified` do S3, não de um
  campo do próprio CSV — se o S3 não devolver o cabeçalho, a data assumida é a
  do dia da execução, e um aviso fica no log (mesma regra do `ccee_perfil`).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → CAPACIDADE_GERACAO.csv
  → gs://<bucket>-raw/ons/capacidade/dt=…/<ingestao_id>.json.gz
    → bronze.ons_capacidade    (append-only, particionado por _ingestao_timestamp)
      → silver.ons_capacidade  (vigente; QUALIFY por codigo_equipamento, _ingestao_timestamp DESC)
        → gold.capacidade_instalada_vigente_usina
```
