# ONS — energia vertida turbinável

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `energia-vertida-turbinavel` (arquivos em `energia_vertida_turbinavel_ho/`) |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/energia_vertida_turbinavel_ho/ENERGIA_VERTIDA_TURBINAVEL_{ano}_{mes:02d}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, um CSV por mês; o mês corrente aparece com atraso (2026-10 ainda não existia em 02/10/2026) |
| Histórico | **Mensal desde 2024-01.** De 2015 a 2023 o ONS publica **um CSV por ano** (`ENERGIA_VERTIDA_TURBINAVEL_AAAA.csv`, ~190 MB cada), com outro nome de arquivo. O conector **não lê o anual** e recusa, com erro claro, janela que comece antes de 2024-01. Os 24 meses que o projeto precisa (09/2024 em diante) cabem na série mensal |
| Credencial | nenhuma |
| Volume verificado | 09/2026: 109.464 linhas, 16,5 MB, 153 usinas, 720 instantes — lido em 02/10/2026 |
| Encoding | UTF-8 (09/2024 e 09/2026), com acentos em `nom_rio` e `nom_agente`; o conector decide por linha |

## Por que esta fonte existe no lake

Energia vertida turbinável é a água que a usina hidrelétrica verteu **podendo** ter turbinado: geração que deixou de existir, em MWmed. Para a hidráulica, é o que o constrained-off (`ons_restricao_coff_*`) é para a eólica e a solar. Pedida pela Alup em 28/09/2026.

## Particularidades

- **Instante de início da hora**: `00:00` cobre 00:00 a 00:59:59 (dicionário do ONS), ao contrário de `ons_dados_hidrologicos`, que usa a hora fim.
- **Sem espaço sobrando e sem coluna vazia** em 09/2026: as 18 colunas vêm preenchidas nas 109.464 linhas. Mesmo assim as medidas aceitam NULL — o que a série não mostrou não vira regra.
- **Zero e negativo**: nenhum valor negativo em 09/2026. Zero é muito comum (usina sem vertimento) e é dado, não ausência.
- **Float com resíduo**: até 20 casas decimais (`val_produtividade`, `val_energiavertidaturbinavel`: 0.0007989898989898991). O NUMERIC do BigQuery guarda 9; o runner ajusta (`_cabe_no_numeric`) e o raw guarda o valor original.
- `cod_usina` é o código da usina **nos modelos de otimização**, não o CEG: vai para `codigo_usina_modelo` e é obrigatório (compõe a chave). A origem não traz o CEG, e `codigo_usina` da Silver fica nulo.
- Sem duplicata na chave (`cod_usina`, `din_instante`) em 09/2024 e 09/2026. Cabeçalho idêntico nos 26 meses conferidos (2024-01 e 09/2024 a 09/2026).
- **O que o dataset diz de si**: a Versão 2.0 do dicionário é de 06/06/2024.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` | DATE | primeiros 10 caracteres |
| `din_instante` | `instante` | DATETIME | `AAAA-MM-DD HH:MM:SS`, início da hora |
| `id_subsistema` | `submercado` | STRING | trim; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `nom_bacia` | `bacia` | STRING | trim |
| `nom_rio` | `rio` | STRING | trim |
| `nom_agente` | `agente` | STRING | trim |
| `nom_reservatorio` | `reservatorio` | STRING | trim |
| `cod_usina` | `codigo_usina_modelo` | INT64 | obrigatório; **não é CEG** |
| `val_geracao` | `geracao_mwmed` | NUMERIC | MWmed |
| `val_disponibilidade` | `disponibilidade_mwmed` | NUMERIC | MWmed |
| `val_vazaoturbinada` | `vazao_turbinada_m3s` | NUMERIC | m3/s |
| `val_vazaovertida` | `vazao_vertida_m3s` | NUMERIC | m3/s |
| `val_vazaovertidanaoturbinavel` | `vazao_vertida_nao_turbinavel_m3s` | NUMERIC | m3/s |
| `val_produtividade` | `produtividade_mw_por_m3s` | NUMERIC | MW/(m3/s) |
| `val_folgadegeracao` | `folga_geracao_mwmed` | NUMERIC | MWmed |
| `val_energiavertida` | `energia_vertida_mwmed` | NUMERIC | MWmed |
| `val_vazaovertidaturbinavel` | `vazao_vertida_turbinavel_m3s` | NUMERIC | m3/s |
| `val_energiavertidaturbinavel` | `energia_vertida_turbinavel_mwmed` | NUMERIC | MWmed — o que a usina deixou de gerar |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem não traz CEG; o código de modelo está em `codigo_usina_modelo` |
| `agente_ccee` | não | o ONS não usa perfil da CCEE; `agente` é o nome do agente no ONS |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`codigo_usina_modelo`, `instante`). Vence a ingestão mais recente: o ONS revisa dado publicado.

## Gold

`gold.vertimento_turbinavel_mensal_usina` — por mês e usina: horas, horas com vertimento turbinável, geração e disponibilidade médias, energia vertida turbinável média, máxima e somada, vazão vertida turbinável média. A soma (`_soma_mwmed`) é a soma das médias horárias, equivalente a MWh, e não leva `_mwh` no nome sem a confirmação do dono do domínio. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → ENERGIA_VERTIDA_TURBINAVEL_{ano}_{mes}.csv   (stream, linha a linha)
  → gs://<bucket>-raw/ons/energia_vertida_turbinavel/dt=…/<ingestao_id>.json.gz
    → bronze.ons_energia_vertida_turbinavel     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_energia_vertida_turbinavel   (vigente; QUALIFY por (codigo_usina_modelo, instante), _ingestao_timestamp DESC)
        → gold.vertimento_turbinavel_mensal_usina
```

## Agendamento

Cloud Scheduler `30 4 8 * *` (dia 8, 04h30), janela dos últimos 40 dias, Cloud Run Job com 1 GiB. Limite de silêncio do alerta: 780 h (mensal + folga).

## Verificação e o que não foi verificado

- **Verificado contra o arquivo real, em 02/10/2026:** cabeçalho, separador, UTF-8, vazios, negativos, unicidade da chave e instantes de 09/2024 e 09/2026; a existência de cada arquivo mensal de 2024-01 a 2026-09 no catálogo CKAN e o cabeçalho de 26 deles (2024-01 e 09/2024 a 09/2026); `ingerir --dry-run` da janela 01 a 30/09/2026: 109.464 extraídas, **0 inválidas**, 11 s.
- **Não verificado:** o corpo dos meses fora de 09/2024 e 09/2026 (e o cabeçalho de 02/2024 a 08/2024); a execução no Cloud Run, o Dataform e a Gold no BigQuery, que só ocorrem no deploy; o histórico anterior a 2024-01 (CSV anual, fora do escopo do conector).
