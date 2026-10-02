# ONS — carga verificada (API)

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `carga-energia-verificada` (API; o catálogo não publica CSV) |
| Endpoint | `GET https://apicarga.ons.org.br/prd/cargaverificada?dat_inicio=AAAA-MM-DD&dat_fim=AAAA-MM-DD&cod_areacarga=<área>` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — item 19 |
| Frequência | Semi-horária, publicada diariamente e revisada nos dias seguintes; agendamento diário |
| Histórico | Conferido de 09/2024 a 09/2026; o que existe antes disso não foi verificado |
| Credencial | **nenhuma.** A API é pública: sem token, sem cadastro, sem IP liberado (conferido em 02/10/2026) |
| Conector | `src/conectores/ons_carga_verificada.py`, que reaproveita a mecânica de [`ons_carga_programada`](ons_carga_programada.md) (`src/conectores/ons_carga_api.py`): mesma API, mesmo catálogo de 33 áreas, mesma janela |
| Volume verificado | 47.520 linhas em set/2026 (33 áreas × 1.440 meias horas), sem chave repetida — lido em 02/10/2026 |

## Por que esta fonte existe no lake

A carga realizada por área, com as parcelas que a compõem: supervisionada pelo ONS, não supervisionada (medição da CCEE) e a micro e minigeração distribuída (MMGD). Pedida pela Alup em 28/09/2026.

## Diferença para `ons_carga`

[`ons_carga`](ons_carga.md) (CSV `carga_energia_di`) é a carga **média do dia** por subsistema (4 linhas por dia). Esta é **semi-horária** por **33 áreas**, com a decomposição em parcelas. Não se duplicam e uma não substitui a outra; a conciliação entre as duas séries não foi feita.

## Contrato da API (o que se viu)

Igual ao da [carga programada](ons_carga_programada.md), com uma diferença que decide o desenho:

- **A resposta é truncada em silêncio quando passa de ~2,4 MB**, sem erro nem aviso. Com a janela de 100 dias a SECO voltou completa; com 104 voltou 4.944 de 4.992 linhas e com 200 dias, as mesmas 4.944. Por isso a janela do conector é de **31 dias** (≈0,75 MB), e `max_dias_por_requisicao` não deve subir. A programada, de linhas menores, não truncou em 200 dias.
- Limite documentado de 3 meses por chamada; `cod_areacarga` obrigatório; datas inclusivas; sem paginação; sem limite de taxa observado.

## Particularidades

- **Valores negativos existem na origem e são aceitos**: `carga_global_sem_mmgd_mwmed` e `carga_supervisionada_mwmed` ficam negativas onde a MMGD passa da carga (ex.: MT em 07/09/2026, com -238,7 e -703,7 MWmed), as áreas de perdas (`PES`, `PEN`) têm carga negativa e a consistência chega a -1.192 MWmed (SC, 03/2025). Em 33 áreas e 3 meses, nenhum campo veio nulo. Sem validação por sinal.
- **Notação científica**: a origem manda `-6.1035156e-05` em `val_consistencia`; o NUMERIC do BigQuery só guarda 9 casas e o runner arredonda para caber.
- O dicionário oficial do ONS grafa `val_cargaglobalsmmg`; o campo real da API é **`val_cargaglobalsmmgd`**.
- `instante_utc` é o **fim** da meia hora, em UTC; `data_referencia` é o dia em Brasília (ver a programada).
- `atualizado_em` (`din_atualizacao`) mostra a revisão: em 02/10/2026 havia valores de 20/09 atualizados em 30/09. A Silver fica com a ingestão mais recente, e a janela diária de 30 dias existe para pegar essa revisão.
- As áreas se sobrepõem; `tipo_area` na Silver, como na programada.
- **Fora do catálogo**: `SIN` (só zeros) e `SE` (~650 MWmed até 04/2025, sem documentação) não são ingeridos.
- Definição de "global" vs "consistida": em set/2026, `val_cargaglobalcons` ficou idêntica a `val_cargaglobal` em NE, S, SECO, RS e PEN e difere pouco no N (viés de -12 contra -14 MWmed frente à programada). Não há texto do ONS sobre o que a consistência corrige; só se conferiram essas seis áreas.

## Campos

| Origem (JSON) | Bronze / Silver | Tipo |
|---|---|---|
| `dat_referencia` | `data_referencia` | DATE |
| `din_referenciautc` | `instante_utc` | TIMESTAMP |
| `cod_areacarga` | `area_carga` | STRING, 33 códigos |
| `din_atualizacao` | `atualizado_em` | TIMESTAMP |
| `val_cargaglobal` | `carga_global_mwmed` | NUMERIC, MWmed |
| `val_cargaglobalcons` | `carga_global_consistida_mwmed` | NUMERIC, MWmed |
| `val_cargaglobalsmmgd` | `carga_global_sem_mmgd_mwmed` | NUMERIC, MWmed |
| `val_cargammgd` | `carga_mmgd_mwmed` | NUMERIC, MWmed |
| `val_cargasupervisionada` | `carga_supervisionada_mwmed` | NUMERIC, MWmed |
| `val_carganaosupervisionada` | `carga_nao_supervisionada_mwmed` | NUMERIC, MWmed |
| `val_consistencia` | `consistencia_mwmed` | NUMERIC, MWmed |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia em Brasília |
| `submercado` | só para as 4 áreas de subsistema | `SECO` vira `SE`; estado, área geoelétrica e perdas ficam nulos |
| `codigo_usina` | não | carga agregada por área |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem é o ONS |

## Deduplicação

Chave natural: (`instante_utc`, `area_carga`), com *assertion* de unicidade. Vence a ingestão mais recente (o ONS revisa o publicado).

## Gold

`gold.desvio_carga_programada_verificada_mensal` — por mês e área, o desvio entre `carga_global_mwmed` e a programada (média, média absoluta e máximo absoluto, em MWmed). Sem KPI (ADR 012). A escolha de `carga_global_mwmed` (e não a líquida de MMGD) é inferência: em set/2026 a diferença média absoluta contra a programada foi de 176 MWmed no Norte com a global e 1.098 com a líquida; no SECO, 1.254 contra 4.902. O ONS não documenta a correspondência.

## O que não foi verificado

- A execução no Cloud Run e no Dataform (ocorre no deploy).
- Séries anteriores a 09/2024.
- O significado oficial de "global" e "consistida" (ver acima).
- A conciliação com `ons_carga` (dataset diferente, mesma grandeza em outra granularidade).

## Linhagem

```
apicarga.ons.org.br/prd/cargaverificada (33 áreas × janelas de 31 dias)
  → gs://<bucket>-raw/ons/carga_verificada/dt=…/<ingestao_id>.json.gz
    → bronze.ons_carga_verificada     (append-only, particionado por _ingestao_timestamp, cluster data_referencia, area_carga)
      → silver.ons_carga_verificada   (vigente; QUALIFY por instante_utc e area_carga, _ingestao_timestamp DESC)
        → gold.desvio_carga_programada_verificada_mensal
```
