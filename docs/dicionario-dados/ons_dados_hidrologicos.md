# ONS — dados hidrológicos por reservatório, base horária

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `dados_hidrologicos_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/dados_hidrologicos_ho/DADOS_HIDROLOGICOS_HO_{ano}_{mes:02d}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, um CSV por mês; o mês corrente é atualizado ao longo do mês |
| Histórico | Mensal desde **2010-01** (conferido no catálogo em 02/10/2026; 2009-12 não existe). O conector recusa janela anterior a 2010-01 |
| Credencial | nenhuma |
| Volume verificado | 09/2026: 122.129 linhas, 21,6 MB, 170 reservatórios, 720 instantes — lido em 02/10/2026 |
| Encoding | UTF-8 nos arquivos de 09/2024 e 09/2026 (zero linhas fora de UTF-8); o conector ainda decide por linha, como o `ons_csv_anual` |

## Por que esta fonte existe no lake

Nível, volume útil e todas as vazões (afluente, defluente, turbinada, vertida, transferida) de cada reservatório do SIN, hora a hora. É o dado de operação por baixo do que `ons_ear_reservatorio` e `ons_ena_reservatorio` mostram por dia. Pedida pela Alup em 28/09/2026.

## Particularidades

- **O instante é a hora FIM.** O dicionário do ONS diz que `01:00` cobre de 00:00 a 00:59. O fim do dia vem como **`23:59:00`**, na mesma data (30 por mês, 720 instantes = 30 dias × 24). Por isso a chave é o instante inteiro, e a Silver deriva `hora_fim` (`23:59` vira 24). Em 09/2024 há ainda **9 linhas com `00:00:00`** (reservatório `RLPPAS`, de 01 a 09/09/2024), que não cabem nessa convenção: ficam no Bronze com o instante da origem, e a Silver as mostra com `hora_fim = 0`. **Não foi possível confirmar** o que `00:00:00` significa para esse reservatório.
- **Texto em largura fixa**, com espaço à direita: `id_subsistema` (`N `, `S `), `tip_reservatorio` (`Reservatório com Usina` seguido de 18 espaços), `nom_bacia` (15 colunas), `id_reservatorio` (6), `nom_reservatorio` (20). Tudo é aparado; sem isso `submercado` não passaria na validação e o mesmo reservatório teria dois ids.
- **Colunas vazias são ausência, não zero**: `val_vazaoturbinada` vem vazia em 5.760 linhas (reservatório sem usina), `val_vazaooutrasestruturas` em 48.780, `val_vazaotransferida` em 84.715, `val_niveljusante` em 5.782, `val_volumeutil` em 4.408 e `cod_usina` em 3.598 (reservatório fictício ou sem usina). Todas viram NULL. Zero informado continua zero.
- **Valores negativos e fora de faixa existem na origem**: `val_volumeutil` de -1.917,58% a 836,53% (3.634 linhas negativas em 09/2026, sobretudo fio d'água, onde o volume útil não tem significado), `val_vazaoafluente` de -93.681 a 327.763 m3/s (4.329 negativas) e `val_vazaotransferida` de -835 a 835 (negativa quando o reservatório recebe). O Bronze e a Silver guardam o que a origem publica; a Gold aplica a faixa de 0 a 100% ao volume útil e declara isso (ver abaixo).
- `cod_usina` é o código da usina **nos modelos de otimização**, não o CEG. Vai para `codigo_usina_modelo`, e a dimensão comum `codigo_usina` da Silver fica nula.
- Sem duplicata na chave (`id_reservatorio`, `din_instante`) em 09/2024, 09/2026 e 10/2026 (parcial).
- O cabeçalho (18 colunas) é idêntico em 28 meses conferidos: 09/2024 a 10/2026, 2010-01 e 2015-06.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` | DATE | primeiros 10 caracteres |
| `din_instante` | `instante` | DATETIME | `AAAA-MM-DD HH:MM:SS`, hora fim |
| `din_instante` | `hora_fim` (só Silver) | INT64 | 1 a 24 (`23:59` → 24) |
| `id_subsistema` | `submercado` | STRING | trim; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `tip_reservatorio` | `tipo_reservatorio` | STRING | trim |
| `nom_bacia` | `bacia` | STRING | trim |
| `id_reservatorio` | `id_reservatorio` | STRING | trim; obrigatório |
| `nom_reservatorio` | `nome_reservatorio` | STRING | trim; obrigatório |
| `cod_usina` | `codigo_usina_modelo` | INT64 | vazio → NULL; **não é CEG** |
| `val_nivelmontante` | `nivel_montante_m` | NUMERIC | m; vazio → NULL |
| `val_niveljusante` | `nivel_jusante_m` | NUMERIC | m; vazio → NULL |
| `val_volumeutil` | `volume_util_percentual` | NUMERIC | %; vazio → NULL; negativo e >100 aceitos |
| `val_vazaoafluente` | `vazao_afluente_m3s` | NUMERIC | m3/s; vazio → NULL; negativo aceito |
| `val_vazaodefluente` | `vazao_defluente_m3s` | NUMERIC | m3/s |
| `val_vazaoturbinada` | `vazao_turbinada_m3s` | NUMERIC | m3/s; vazio → NULL |
| `val_vazaovertida` | `vazao_vertida_m3s` | NUMERIC | m3/s |
| `val_vazaooutrasestruturas` | `vazao_outras_estruturas_m3s` | NUMERIC | m3/s; vazio → NULL |
| `val_vazaotransferida` | `vazao_transferida_m3s` | NUMERIC | m3/s; negativo aceito |
| `val_vazaovertidanaoturbinavel` | `vazao_vertida_nao_turbinavel_m3s` | NUMERIC | m3/s |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | não | a origem traz o código de modelo (`codigo_usina_modelo`), não o CEG |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`id_reservatorio`, `instante`). Vence a ingestão mais recente: o ONS revisa dado publicado, e o arquivo do mês corrente é republicado ao longo do mês.

## Gold

`gold.operacao_hidraulica_mensal_reservatorio` — por mês e reservatório: horas, volume útil médio, mínimo e máximo, nível médio a montante, vazões médias (afluente, defluente, turbinada, vertida), vazão vertida máxima e horas vertendo. Sem KPI (ADR 012).

**Decisão que o dono do domínio deve confirmar:** o volume útil só entra nas estatísticas **dentro de 0 a 100%**; as horas fora da faixa são contadas em `horas_com_volume_fora_da_faixa`, e as dentro, em `horas_com_volume_valido`. A faixa é minha leitura do que a origem publica (valores de -1.917% a 836%), não regra do ONS: se o dono quiser outra, é uma linha na Gold.

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → DADOS_HIDROLOGICOS_HO_{ano}_{mes}.csv   (stream, linha a linha)
  → gs://<bucket>-raw/ons/dados_hidrologicos/dt=…/<ingestao_id>.json.gz
    → bronze.ons_dados_hidrologicos     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_dados_hidrologicos   (vigente; QUALIFY por (id_reservatorio, instante), _ingestao_timestamp DESC)
        → gold.operacao_hidraulica_mensal_reservatorio
```

## Agendamento

Cloud Scheduler `0 4 8 * *` (dia 8, 04h), janela dos últimos 40 dias (o mês fechado e o anterior), Cloud Run Job com 1 GiB. Limite de silêncio do alerta: 780 h (mensal + folga).

## Verificação e o que não foi verificado

- **Verificado contra o arquivo real, em 02/10/2026:** cabeçalho, separador, UTF-8, vazios, negativos, unicidade da chave e instantes de 09/2026, 09/2024 e 10/2026 (parcial); `ingerir --dry-run` da janela 01 a 30/09/2026: 122.129 extraídas, **0 inválidas**, 11–18 s, pico de 98 MiB de memória em stream.
- **Não verificado:** o corpo de qualquer mês fora de 09/2024, 09/2026 e 10/2026 (dos demais só o cabeçalho foi conferido: 2010-01, 2015-06 e 10/2024 a 08/2026); a execução no Cloud Run, o Dataform e a Gold no BigQuery, que só ocorrem no deploy; o significado das 9 linhas `00:00:00` de 09/2024.
