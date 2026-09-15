# ONS — geração horária por usina

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `geracao_usina_2_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_usina_2_ho/GERACAO_USINA-2_{ano}_{mes:02d}.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Um CSV por mês |
| Volume verificado | 533.833 linhas, 66 MB — recurso de julho/2026, lido em 14/09/2026 |
| Encoding | UTF-8 (confirmado: zero linhas exclusivamente ISO-8859-1) |
| Licença | CC-BY |
| Credencial | nenhuma |

## Particularidades

- **CSV remoto particionado por mês** (não por ano, como o `ons_carga`),
  separador `;`. A janela decide quais meses baixar; as linhas fora do
  intervalo pedido são descartadas na extração.
- `din_instante` é `AAAA-MM-DD HH:MM:SS`. `data_referencia` e `hora` são
  derivados dele por um `model_validator` do schema — não em `transformar()` —
  para que um timestamp malformado vire `linhas_invalidas`, não derrube o mês.
- `id_subsistema` **pode vir com espaço** em volta (`" N "`); o validador do
  submercado aplica `.strip()` antes de conferir contra a lista conhecida
  (`N`, `NE`, `S`, `SE`, a mesma do `ons_carga`).
- `ceg` pode vir como `"-"` quando a usina não tem CEG (típico de MMGD
  agregada) — vira `NULL`, não o literal `"-"`.
- `id_ons` pode vir vazio — mesma regra, vira `NULL`.
- `val_geracao` **pode ser zero e pode ser negativo** (usina reversível
  consumindo, ou ajuste de medição). Nenhuma das duas é rejeitada.
- **Achado do dry-run real (15/09/2026), não previsto na leitura original do
  formato**: `val_geracao` também vem **vazio** — 63.576 de 533.832 linhas do
  arquivo de julho/2026 (~12%), usina sem medição registrada naquela hora.
  Vazio é ausência, não erro: vira `NULL`, a linha continua válida e não é
  descartada.

## O achado desta entrega: `codigo_usina` sem depender da Lacuna 1

O `codigo_usina` (dimensão comum do projeto) hoje só é preenchido pelo
`aneel_siga`, com o CodCEG. A [issue #141](https://github.com/nessenergy/Alupdatalake/issues/141)
pede à Alup um de-para de quatro colunas — sigla interna ↔ CEG ↔ nome CCEE ↔
nome ONS — porque nenhuma fonte interna trazia as duas pontas ao mesmo tempo.

Esta fonte (e a `ons_capacidade`) trazem a coluna `ceg` **junto do nome da
usina como o ONS o publica** (`nom_usina`). Isso entrega o lado CEG ↔ nome ONS
do de-para **sem depender de ninguém**: a Silver já preenche `codigo_usina`
com o CEG (nulo quando a origem publica traço ou vazio), e a junção ONS ↔
ANEEL passa a ser possível por `codigo_usina` diretamente. O que ainda falta
na #141 se reduz a uma coisa só: sigla interna ↔ CEG.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` | DATE | primeiros 10 caracteres, via schema |
| `din_instante` | `hora` | INT64 | 0–23, via schema |
| `id_subsistema` | `submercado` | STRING | trim, maiúsculas; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `id_estado` | `uf` | STRING | trim |
| `nom_estado` | `nome_uf` | STRING | trim |
| `cod_modalidadeoperacao` | `modalidade_operacao` | STRING | trim |
| `nom_tipousina` | `tipo_usina` | STRING | trim |
| `nom_tipocombustivel` | `tipo_combustivel` | STRING | trim |
| `nom_usina` | `nome_usina` | STRING | trim |
| `id_ons` | `id_ons` | STRING | vazio → NULL |
| `ceg` | `codigo_usina` | STRING | `"-"` ou vazio → NULL — **é o CEG** |
| `val_geracao` | `geracao_mw` | NUMERIC | direto; zero e negativo são válidos; vazio → NULL (~12% das linhas) |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da geração |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | **sim — o CEG** | nulo quando a origem publica traço ou vazio (ver achado acima) |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`data_referencia`, `hora`, `nome_usina`) — o nome da usina, não
o CEG nem o `id_ons`, porque os dois podem vir vazios em MMGD agregada. Vence a
ingestão mais recente, como no `ons_carga`: o ONS revisa dado publicado.

## Gold

`gold.geracao_mensal_usina_ons` — soma, média, máximo e mínimo horário de
`geracao_mw` por mês, usina, submercado e tipo. Sem KPI (ADR 012). O nome leva
o sufixo `_ons` para não colidir com `gold.geracao_mensal_usina` (CCEE, por
parcela de usina e centro de gravidade contábil) — são perguntas parecidas,
respondidas por origens diferentes, com granularidade diferente.

## Qualidade e observações

- **Dry-run contra a API real de julho/2026 (15/09/2026)**: 533.832 extraídos,
  **0 inválidos**, `SUCESSO` em 53,6s — depois de corrigir o tratamento do
  `val_geracao` vazio (achado acima). Antes da correção, as 63.576 linhas sem
  medição contavam como inválidas.
- **278.928 das 533.832 linhas (52,2%) vieram com CEG preenchido** — é o
  tamanho real do que esta fonte entrega para a #141 (achado acima).
- `din_instante` em formato diferente de `AAAA-MM-DD HH:MM:SS` conta como
  `linhas_invalidas` — nunca derruba o mês inteiro (a conversão vive no
  `model_validator` do schema, não em `transformar()`).
- O runner (`src/core/conector.py`) materializa a janela inteira em memória
  antes de gravar o raw e validar. Para 533 mil linhas/mês isso é bem menor que
  o `ccee_geracao_usina` (~3 milhões/mês), mas o agendamento espelha a mesma
  cautela: janela de 40 dias e memória acima do padrão (ver Terraform).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → GERACAO_USINA-2_{ano}_{mes}.csv
  → gs://<bucket>-raw/ons/geracao_usina/dt=…/<ingestao_id>.json.gz
    → bronze.ons_geracao_usina    (append-only, particionado por _ingestao_timestamp)
      → silver.ons_geracao_usina  (vigente; QUALIFY por data+hora+usina, _ingestao_timestamp DESC)
        → gold.geracao_mensal_usina_ons
```
