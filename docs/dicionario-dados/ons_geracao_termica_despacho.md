# ONS — geração térmica por motivo de despacho

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `geracao-termica-despacho-2` (arquivos em `geracao_termica_despacho_2_ho/`) |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/geracao_termica_despacho_2_ho/GERACAO_TERMICA_DESPACHO-2_{ano}_{mes:02d}.csv` |
| Escopo | **Aditivo 01** ([`contrato/aditivo-01-conjuntos-publicos.md`](../contrato/aditivo-01-conjuntos-publicos.md), [#294](https://github.com/nessenergy/Alupdatalake/issues/294)) — arquivo público, sem credencial |
| Frequência | Horária, um CSV por mês; o mês corrente aparece com atraso (2026-10 ainda não existia em 02/10/2026) |
| Histórico | **Mensal desde 2022-01.** Antes disso o ONS publica **um CSV por ano** (`GERACAO_TERMICA_DESPACHO_AAAA.csv`, sem o `-2`, ~265 MB). O conector **não lê o anual** e recusa, com erro claro, janela que comece antes de 2022-01. Os 24 meses que o projeto precisa (09/2024 em diante) cabem na série mensal |
| Credencial | nenhuma |
| Volume verificado | 09/2026: 102.960 linhas, 33,1 MB, 143 usinas, 720 instantes, 47 colunas — lido em 02/10/2026 |
| Encoding | UTF-8 (09/2024 e 09/2026), com acentos em nomes de usina e combustível; o conector decide por linha |

## Por que esta fonte existe no lake

Para cada usina térmica e hora, quanto foi **programado** (dia anterior) e quanto foi **verificado**, e **por qual motivo** a usina gerou: ordem de mérito (CVU abaixo do CMO), inflexibilidade, razão elétrica, segurança energética (decisão do CMSE), reserva de potência, substituição de usina sem combustível, unit commitment ou constrained-off. É o que explica por que a térmica foi chamada, e não só que foi. Pedida pela Alup em 28/09/2026.

## Particularidades

- **O cabeçalho cresceu três vezes na série** — conferido em 01/2022, 09/2024 e 09/2026 e, só pelo cabeçalho, em cada mês de 09/2024 a 09/2026:

  | Meses | Colunas | O que entrou |
  |---|---|---|
  | 2022-01 a 2024-08 (conferidos 2022-01, 2022-06, 2023-06) | 41 | — |
  | 2024-09 a 2026-01 | 42 | `val_fdexp` |
  | 2026-02 e 2026-03 | 43 | `val_progdisponibilidade` |
  | 2026-04 em diante | 47 | `val_geracaodespachada`, `nom_combustivel`, `dsc_tpmotivorestricao`, `din_publicacao` |

  A leitura é **por nome de coluna**, e o que o mês não traz fica **NULL — nunca zero**. As seis colunas posteriores a 2022 são, portanto, nulas para os meses anteriores à entrada delas: `verif_fator_exportacao` até 08/2024, `prog_disponibilidade_mwmed` até 01/2026 e `geracao_despachada_mwmed`, `combustivel`, `motivo_restricao` e `publicado_em` até 03/2026. **A virada exata em 2024 (entre 2023-06 e 2024-09) não foi localizada** por mês; o conector não depende dela.
- O dicionário JSON do ONS chama o combustível `nom_tipocombustivel`; **no arquivo a coluna é `nom_combustivel`**. O conector lê a do arquivo.
- **O patamar muda de caixa**: `LEVE`/`MÉDIA`/`PESADA` até 2026-03, `Leve`/`Média`/`Pesada` desde 2026-04. Normalizado para maiúsculas; a Silver afirma o domínio.
- **Números em duas grafias**: `201.0` e `0E-8` no arquivo de 2022-01, `201` e `0.000` depois. O conector aceita as duas (`201.0` vira o inteiro 201; fração é erro).
- **Muita coluna sempre zero**: em 09/2026, `prog_garantia_energetica`, `prog_gfom`, `prog_reposicao_perdas`, `prog_exportacao`, `prog_reserva_potencia`, `verif_gfom`, `verif_reposicao_perdas`, `verif_exportacao`, `verif_reserva_potencia`, `verif_fator_exportacao` e `atendimento_rpo` não têm um valor diferente de zero. Foram mantidas: o motivo existe no dicionário do ONS e pode aparecer em outro mês.
- **O CEG não é único por usina**: 99 CEG para 143 usinas em 09/2026; **16 CEG são compartilhados** por mais de uma usina (`Maranhão 4 P0`, `P1`, `P2` com o mesmo CEG). Por isso a chave é o nome da usina, e `ceg` vira `codigo_usina` (dimensão comum) sem ser chave. Dois CEG são `UTN.` (nucleares); os demais, `UTE.`. Não houve `-` nem vazio em `ceg` em 09/2024 e 09/2026.
- `cod_usinaplanejamento` vem vazio em 2.880 linhas (4 usinas) em 09/2026: vira NULL, a linha é válida.
- `dsc_tpmotivorestricao` vem vazio em 101.743 de 102.960 linhas: vazio é "sem restrição", não erro.
- `din_publicacao` é única no arquivo de 09/2026 (`2026-10-02 12:04:30`, o dia da leitura): o ONS **republica o mês corrente inteiro**. Por isso a Silver deduplica pela ingestão mais recente, e `publicado_em` mostra qual republicação gerou a linha.
- Nenhum valor negativo em 09/2024 e 09/2026. Sem duplicata na chave (`din_instante`, `nom_usina`) nos dois meses.
- O instante é o **início** da hora (00:00 a 23:00), ao contrário de `ons_dados_hidrologicos`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia`, `instante` | DATE, DATETIME | primeiros 10 caracteres; ISO |
| `nom_tipopatamar` | `patamar` | STRING | trim, maiúsculas |
| `id_subsistema` | `submercado` | STRING | trim; validado contra `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `nom_usina` | `nome_usina` | STRING | trim; obrigatório |
| `cod_usinaplanejamento` | `codigo_usina_planejamento` | INT64 | `201.0` → 201; vazio → NULL |
| `ceg` | `codigo_usina` | STRING | CEG canônico (`src/core/ceg.py`); vazio ou `-` → NULL |
| `val_prog*` (17 colunas) | `prog_*_mwmed` | NUMERIC | MWmed; ver a tabela de motivos abaixo |
| `val_verif*` (15 colunas) | `verif_*_mwmed` | NUMERIC | MWmed |
| `val_fdexp` | `verif_fator_exportacao` | NUMERIC | código 0, 0,5 ou 1 (não é MW); NULL antes de 09/2024 |
| `val_atendsatisfatoriorpo` | `atendimento_rpo` | INT64 | 0 não despachada por esse motivo, 1 satisfatório, 2 insatisfatório |
| `tip_restricaoeletrica` | `tipo_restricao_eletrica` | INT64 | 0 a 9; `9.0` → 9 |
| `val_progdisponibilidade` | `prog_disponibilidade_mwmed` | NUMERIC | NULL antes de 02/2026 |
| `val_geracaodespachada` | `geracao_despachada_mwmed` | NUMERIC | NULL antes de 04/2026 |
| `nom_combustivel` | `combustivel` | STRING | NULL antes de 04/2026 |
| `dsc_tpmotivorestricao` | `motivo_restricao` | STRING | vazio → NULL; NULL antes de 04/2026 |
| `din_publicacao` | `publicado_em` | DATETIME | NULL antes de 04/2026 |

Colunas técnicas do Bronze: `_ingestao_id`, `_ingestao_timestamp`, `_fonte`, `_schema_versao`.

### Os motivos de despacho (`prog_` programado, `verif_` verificado)

| Sufixo do destino | Coluna de origem (sem `val_prog`/`val_verif`) | Significado (dicionário do ONS) |
|---|---|---|
| `geracao` | `geracao` | geração total da usina |
| `ordem_merito` | `ordemmerito` | por ordem de mérito: CVU da usina menor que o CMO |
| `ordem_merito_ref` (só prog) | `ordemdemeritoref` | referência para o despacho por mérito |
| `ordem_merito_acima_inflex` | `ordemdemeritoacimadainflex` | por mérito, sem inflexibilidade embutida |
| `inflexibilidade` | `inflexibilidade` | por inflexibilidade declarada pelo agente (embutida no mérito, se também despachada por mérito) |
| `inflex_embutida_merito` | `inflexembutmerito` | inflexibilidade embutida no mérito |
| `inflex_pura` | `inflexpura` | inflexibilidade fora do mérito |
| `razao_eletrica` | `razaoeletrica` | razão elétrica ou necessidade do SIN |
| `garantia_energetica` | `garantiaenergetica` | segurança energética, decisão do CMSE |
| `gfom` | `gfom` | fora do mérito, para compensar falta futura de combustível |
| `reposicao_perdas` | `reposicaoperdas` | repor perdas na transmissão ou variação de térmicas alocadas à exportação |
| `exportacao` | `exportacao` | exportação a países vizinhos |
| `reserva_potencia` | `reservapotencia` | recompor a reserva de potência operativa (REN 822/2018) |
| `gsub` | `gsub` | substituir usina de CVU menor sem combustível |
| `unit_commitment` | `unitcommitment` | rampa e tempo mínimo ligada ou desligada; desde 01/2020 |
| `constrained_off` | `constrainedoff` | restrição de geração em usina despachada por mérito |
| `inflexibilidade_dessem` (só prog) | `inflexibilidadedessem` | inflexibilidade dos modelos, referência do deslocamento hidráulico |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia do instante |
| `submercado` | sim | `id_subsistema` |
| `codigo_usina` | **sim — o CEG** | não único por usina; nulo se a origem vier vazia ou com traço |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | `YYYY-MM` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`instante`, `nome_usina`). Vence a ingestão mais recente; o mês corrente é republicado inteiro.

## Gold

`gold.despacho_termico_mensal_usina` — por mês e usina: horas, horas gerando, geração programada e verificada somadas e, por motivo verificado, a soma de mérito, inflexibilidade, razão elétrica, segurança energética, reserva de potência, substituição, unit commitment e constrained-off. **Os motivos não somam a geração**: a inflexibilidade pode estar embutida no mérito, então nenhum é calculado como resto. As somas são das médias horárias (equivalentes a MWh), sem `_mwh` no nome, como em `geracao_mensal_usina_ons`. Sem KPI (ADR 012).

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → GERACAO_TERMICA_DESPACHO-2_{ano}_{mes}.csv   (stream, linha a linha)
  → gs://<bucket>-raw/ons/geracao_termica_despacho/dt=…/<ingestao_id>.json.gz
    → bronze.ons_geracao_termica_despacho     (append-only, particionado por _ingestao_timestamp)
      → silver.ons_geracao_termica_despacho   (vigente; QUALIFY por (instante, nome_usina), _ingestao_timestamp DESC)
        → gold.despacho_termico_mensal_usina
```

## Agendamento

Cloud Scheduler `0 5 8 * *` (dia 8, 05h), janela dos últimos 40 dias, Cloud Run Job com 1 GiB. Limite de silêncio do alerta: 780 h (mensal + folga).

## Verificação e o que não foi verificado

- **Verificado contra o arquivo real, em 02/10/2026:** cabeçalho, separador, UTF-8, vazios, negativos, CEG e unicidade da chave de 09/2024 e 09/2026; os cabeçalhos de 2022-01, 2022-06, 2023-06 e de cada mês de 09/2024 a 09/2026 (quatro formatos); duas linhas reais de 2022-01 e de 09/2024 nas fixtures; `ingerir --dry-run` da janela 01 a 30/09/2026: 102.960 extraídas, **0 inválidas**, 28 s, pico de 95 MiB em stream.
- **Não verificado:** o corpo dos meses de 2022-02 a 2024-08 e de 10/2024 a 08/2026 (só o cabeçalho foi lido nos meses conferidos); a execução no Cloud Run, o Dataform e a Gold no BigQuery, que só ocorrem no deploy; o histórico anterior a 2022-01 (CSV anual, fora do escopo do conector).
