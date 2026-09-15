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
- **`id_subsistema` traz uma quinta sigla além de N/NE/S/SE: `PY`.** É a
  interligação com o Paraguai — a metade paraguaia de Itaipu, 10 unidades
  geradoras e 7.000 MW de potência efetiva, o maior ativo de geração do
  cadastro. Diferente do `ons_carga` (onde submercado é a chave do fato, e
  sigla fora da lista é dado que não deveria existir), aqui submercado é
  atributo de localização de um ativo: um ativo fora dos quatro submercados
  continua sendo um ativo. Por isso `PY` vira `submercado = NULL`, não linha
  inválida — omiti-lo subestimaria a capacidade instalada do SIN em 7 GW.
  Qualquer outra sigla que não seja N/NE/S/SE/PY continua rejeitada.

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

### Correção de 15/09/2026: o de-para só fecha com o CEG normalizado

A afirmação acima estava certa na origem e errada na prática. O último
segmento do CEG vem com **um dígito na ANEEL** (`...-4.1`) e **dois no ONS**
(`...-4.01`); como texto, são chaves distintas, e o JOIN por `codigo_usina`
devolvia **zero** linha em 2.047 usinas. Com o sufixo igualado na ingestão
(`src/core/ceg.py`), **1.946 (95,1%)** casam — as 101 restantes são usinas que
o ONS opera e o cadastro da ANEEL não traz sob aquele código.

O de-para que sobra está materializado em `gold.de_para_usina`.


## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `Last-Modified` (cabeçalho HTTP) | `data_referencia` | DATE | ver particularidades acima |
| `id_subsistema` | `submercado` | STRING | trim, maiúsculas; `{N,NE,S,SE}` direto, `PY` (Itaipu/Paraguai) → NULL, qualquer outra sigla rejeitada |
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
| `submercado` | sim, exceto Itaipu/PY | N, NE, S, SE; NULL para a interligação com o Paraguai |
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

`gold.de_para_usina` — CEG ↔ nome ANEEL ↔ nome ONS, com `sigla_ccee` nula à
espera do insumo da Alup ([#141](https://github.com/nessenergy/Alupdatalake/issues/141)).

## Qualidade e observações

- **Dry-run contra a API real (15/09/2026)**: 5.688 extraídos, **0
  inválidos**, `SUCESSO`. Antes de tratar `PY` como o achado descrito acima, as
  10 linhas de Itaipu/Paraguai contavam como inválidas (5.678 extraídos válidos
  de fato, 10 descartadas) — a correção fez o cadastro ganhar 7.000 MW que
  estavam sendo silenciosamente perdidos: potência efetiva total salta de
  **200.233 MW (5.668 unidades) para 207.233 MW (5.678 unidades)**, +3,5%.
  As 10 linhas de Itaipu (`cod_equipamento` únicos, 700 MW cada) já vêm com
  `ceg` preenchido (`UHE.PH.PR.001161-4.01`) — diferente do que se poderia
  supor, não é um caso de CEG ausente.
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
