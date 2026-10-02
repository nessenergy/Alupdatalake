# ONS — fator de capacidade de eólicas e solares

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `fator-capacidade-2` (arquivos em `fator_capacidade_2_di/`) |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/fator_capacidade_2_di/FATOR_CAPACIDADE-2_{ano}_{mes:02d}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | **Horária** (o `_di` do nome do diretório não é "diário": 720 instantes em 09/2026), um CSV por mês; o mês corrente aparece com atraso (2026-10 ainda não existia em 02/10/2026) |
| Histórico | **Mensal desde 2022-01.** Antes disso o ONS publica **um CSV por ano** (`FATOR_CAPACIDADE_AAAA.csv`, sem o `-2`, ~320 MB). O conector **não lê o anual** e recusa, com erro claro, janela que comece antes de 2022-01. Os 24 meses que o projeto precisa (09/2024 em diante) cabem na série mensal |
| Credencial | nenhuma |
| Volume verificado | 09/2026: 169.536 linhas, 40,8 MB, 236 usinas e conjuntos, 720 instantes — lido em 02/10/2026. 09/2024: 160.728 linhas, 39,1 MB |
| Encoding | UTF-8 (09/2024 e 09/2026), com acentos em estado e usina; o conector decide por linha |

## Por que esta fonte existe no lake

Geração programada e verificada, capacidade instalada e fator de capacidade (verificada ÷ instalada) de cada usina eólica ou solar, ou conjunto delas, por hora, com o ponto de conexão e as coordenadas. É a medida de quanto da capacidade renovável foi aproveitada. Pedida pela Alup em 28/09/2026.

## Particularidades

- **A unidade é a usina _ou o conjunto_.** Em 09/2026, 158.232 das 169.536 linhas (93%) são `Conjunto de Usinas`, com `ceg` igual a `-`; só `Tipo I` e `Tipo II-B` trazem CEG (16 CEG em 09/2026 e 15 em 09/2024, fora o traço). `-` vira NULL em `codigo_usina`.
- **A chave é `id_ons`** (`CJU_...` nos conjuntos), não o nome: 233 nomes de usina ou conjunto para 238 `id_ons` em 09/2026. Sem duplicata em (`din_instante`, `id_ons`) em 09/2024 e 09/2026.
- **Valores negativos e acima de 1 existem na origem**: geração verificada de -1,4 a 1.270,5 MWmed (14 linhas negativas em 09/2026) e fator de -0,004 a 1,049 (09/2026); em 09/2024 o fator chegou a 1,816. O Bronze e a Silver guardam o que a origem publica.
- **Vazios que são ausência**: `val_geracaoprogramada` vazio em 3.984 linhas (2%), `nom_localizacao` em 28.080 (só o Nordeste traz), `val_latitudesecoletora`/`val_longitudesecoletora` em 3.600 e as do ponto de conexão em 2.160. Viram NULL. Zero informado continua zero (fator 0.0 é geração zero, não ausência).
- **Decimais longos**: o fator chega a 22 casas (`0.4433154442456768`) e as coordenadas a 15. O NUMERIC do BigQuery guarda 9; o runner ajusta e o raw guarda o original. Em 09/2024 o arquivo usava outra grafia (`0E-8`, `1.81606285714285714285`), aceita igual.
- `nom_pontoconexao` tem texto irregular na origem (`MIRANDA II500kVA`, `IGAPORA II - 230 kV (B)`); é guardado como publicado, aparado.
- O cabeçalho (21 colunas) é idêntico nos 26 meses conferidos (2022-01 e 09/2024 a 09/2026).

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia`, `instante` | DATE, DATETIME | primeiros 10 caracteres; ISO |
| `id_subsistema` | `submercado` | STRING | trim; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `id_estado`, `nom_estado` | `uf`, `nome_uf` | STRING | trim |
| `cod_pontoconexao`, `nom_pontoconexao` | `codigo_ponto_conexao`, `nome_ponto_conexao` | STRING | trim |
| `nom_localizacao` | `localizacao` | STRING | vazio → NULL; só o Nordeste |
| `val_latitudesecoletora`, `val_longitudesecoletora` | `latitude_coletora`, `longitude_coletora` | NUMERIC | graus; vazio → NULL |
| `val_latitudepontoconexao`, `val_longitudepontoconexao` | `latitude_ponto_conexao`, `longitude_ponto_conexao` | NUMERIC | graus |
| `nom_modalidadeoperacao` | `modalidade_operacao` | STRING | trim; `Conjunto de Usinas`, `Tipo I`, `Tipo II-B` |
| `nom_tipousina` | `tipo_usina` | STRING | trim; `Eólica` ou `Solar` |
| `nom_usina_conjunto` | `nome_usina_conjunto` | STRING | trim; obrigatório |
| `id_ons` | `id_ons` | STRING | trim; obrigatório |
| `ceg` | `codigo_usina` | STRING | CEG canônico (`src/core/ceg.py`); `-` ou vazio → NULL |
| `val_geracaoprogramada` | `geracao_programada_mwmed` | NUMERIC | MWmed; vazio → NULL |
| `val_geracaoverificada` | `geracao_verificada_mwmed` | NUMERIC | MWmed; negativo aceito |
| `val_capacidadeinstalada` | `capacidade_instalada_mw` | NUMERIC | MW |
| `val_fatorcapacidade` | `fator_capacidade` | NUMERIC | publicado pelo ONS; negativo e >1 aceitos |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | **sim — o CEG, quando há** | nulo em conjunto de usinas (93% das linhas) |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`instante`, `id_ons`). Vence a ingestão mais recente: o ONS revisa dado publicado.

## Gold

`gold.fator_capacidade_mensal_usina` — por mês e usina (ou conjunto): horas, horas com programação, fator de capacidade médio, mínimo e máximo, geração verificada e programada médias e capacidade instalada média. O fator é a **média do fator que o ONS publica a cada hora**: a Gold não recalcula a razão (ADR 012). Se o dono do domínio preferir o fator mensal ponderado (geração total ÷ capacidade total), é uma decisão de negócio e entra em `indicadores_mensais`, onde a divisão mora.

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → FATOR_CAPACIDADE-2_{ano}_{mes}.csv   (stream, linha a linha)
  → gs://<bucket>-raw/ons/fator_capacidade/dt=…/<ingestao_id>.json.gz
    → bronze.ons_fator_capacidade     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_fator_capacidade   (vigente; QUALIFY por (instante, id_ons), _ingestao_timestamp DESC)
        → gold.fator_capacidade_mensal_usina
```

## Agendamento

Cloud Scheduler `30 5 8 * *` (dia 8, 05h30), janela dos últimos 40 dias, Cloud Run Job com 1 GiB. Limite de silêncio do alerta: 780 h (mensal + folga).

## Verificação e o que não foi verificado

- **Verificado contra o arquivo real, em 02/10/2026:** cabeçalho, separador, UTF-8, vazios, negativos, CEG e unicidade da chave de 09/2024 e 09/2026; o cabeçalho de 26 meses; `ingerir --dry-run` da janela 01 a 30/09/2026: 169.536 extraídas, **0 inválidas**, 15 s, pico de 91 MiB em stream.
- **Não verificado:** o corpo dos meses fora de 09/2024 e 09/2026; a execução no Cloud Run, o Dataform e a Gold no BigQuery, que só ocorrem no deploy; o histórico anterior a 2022-01 (CSV anual, fora do escopo do conector).
