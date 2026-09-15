# ONS — constrained-off de eólica e fotovoltaica

Duas fontes, um documento: os dois conjuntos têm **exatamente as mesmas 24
colunas**, conferido contra os arquivos de agosto/2026. O schema e a extração
vivem em `src/conectores/ons_restricao_coff.py`; cada fonte é uma subclasse que
só troca a URL e o rótulo.

| Item | `ons_restricao_coff_eolica` | `ons_restricao_coff_fotovoltaica` |
|---|---|---|
| Dataset | `restricao_coff_eolica_tm` | `restricao_coff_fotovoltaica_tm` |
| Endpoint | `…/dataset/restricao_coff_eolica_tm/RESTRICAO_COFF_EOLICA_{ano}_{mes:02d}.csv` | `…/dataset/restricao_coff_fotovoltaica_tm/RESTRICAO_COFF_FOTOVOLTAICA_{ano}_{mes:02d}.csv` |
| Volume verificado | **227.664 linhas, 46 MB**, 153 usinas e conjuntos (agosto/2026) | **121.536 linhas**, 83 usinas (agosto/2026) |
| Pico de memória medido | 389 MiB em 60 s | 275 MiB em 33 s |
| Onda | 1 — arquivo público, sem credencial | 1 |
| Frequência | Um CSV por mês | Um CSV por mês |
| Encoding | UTF-8 | UTF-8 |
| Licença | CC-BY | CC-BY |
| Credencial | nenhuma | nenhuma |

## Por que estas fontes existem no lake

Constrained-off é a energia que a usina **poderia** ter gerado e não gerou
porque o sistema a limitou. Para um gerador renovável é receita que não entrou,
e nenhuma outra fonte pública do lake responde isso:

- `ons_disponibilidade_usina` cobre só o parque despachado centralmente — UHE,
  UTE e UTN, **nenhuma eólica ou solar**;
- `ons_geracao_usina` diz o que foi gerado, não o que deixou de ser.

## Particularidades

- **O passo é de 30 minutos, não de hora.** Agosto/2026 trouxe 1.488 instantes
  (31 × 48), com minuto `00` e `30`. É a primeira fonte do lake nesse passo, e
  por isso o **instante inteiro é coluna** (`instante`, DATETIME) em vez de só
  `hora`: deduplicar por hora colapsaria dois registros distintos em um. A
  coluna `hora` continua existindo na Silver, derivada, para quem só quer o
  perfil horário.
- **A chave é `(instante, nome_usina)`.** Conferido no arquivo real: 227.664
  pares distintos para 227.664 linhas, zero duplicata. O mesmo vale para
  `(instante, id_ons)`.
- **Quase metade das meias-horas não tem restrição.** Em agosto/2026,
  **108.060 de 227.664 linhas (47,5%)** vieram com `cod_razaorestricao` vazio —
  é a usina gerando livre, não linha incompleta. Todos os campos de restrição
  vêm nulos junto. Quem contar linha em vez de restrição transforma operação
  normal em evento.
- **O CEG quase não aparece: 7,2% das linhas**, 11 CEGs distintos. A
  granularidade é o **conjunto** de usinas (`Conj. Paulino Neves`), que não tem
  CEG próprio. Quem identifica a linha é o `id_ons` (`CJU_MAPLN`). Quando o CEG
  vem, entra na forma canônica de `src/core/ceg.py` e cruza com o
  `gold.de_para_usina`.
- **Concentração no Nordeste**: 205.344 das 227.664 linhas eólicas (90,2%) são
  do submercado NE. Sul 19.344, Norte e Sudeste 1.488 cada.
- **`val_geracao` pode ser negativo** — 4 linhas em agosto/2026. É usina parada
  consumindo da rede, não erro de sinal.

## Códigos que a origem usa

| Coluna | Valor | Significado | Linhas em agosto/2026 (eólica) |
|---|---|---|---|
| `cod_razaorestricao` | `ENE` | Excedente de energia | 71.534 |
| | `CNF` | Confiabilidade | 41.000 |
| | `REL` | Confiabilidade elétrica | 7.070 |
| | *(nulo)* | Sem restrição na meia hora | 108.060 |
| `cod_origemrestricao` | `SIS` | Sistêmica | 75.539 |
| | `LOC` | Local | 44.065 |
| | *(nulo)* | Sem restrição na meia hora | 108.060 |

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` + `instante` | DATE + DATETIME | derivados no `model_validator`; formato inválido vira linha inválida, não crash |
| `id_subsistema` | `submercado` | STRING | trim, maiúsculas; só `{N,NE,S,SE}` |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `id_estado` | `uf` | STRING | trim |
| `nom_estado` | `nome_uf` | STRING | trim |
| `nom_usina` | `nome_usina` | STRING | usina **ou conjunto** |
| `id_ons` | `id_ons` | STRING | vazio ou `"-"` → NULL; é o identificador que sempre existe |
| `ceg` | `codigo_usina` | STRING | forma canônica; `"-"` → NULL (92,8% das linhas) |
| `val_geracao` | `geracao_mw` | NUMERIC | vazio → NULL; **pode ser negativo** |
| `val_geracaolimitada` | `geracao_limitada_mw` | NUMERIC | vazio → NULL |
| `val_disponibilidade` | `disponibilidade_mw` | NUMERIC | vazio → NULL |
| `val_geracaoreferencia` | `geracao_referencia_mw` | NUMERIC | vazio → NULL |
| `val_geracaoreferenciafinal` | `geracao_referencia_final_mw` | NUMERIC | vazio → NULL (96,9% das linhas) |
| `cod_razaorestricao` | `razao_restricao` | STRING | `REL`, `CNF`, `ENE`; nulo = sem restrição |
| `cod_origemrestricao` | `origem_restricao` | STRING | `SIS`, `LOC`; nulo = sem restrição |
| `dsc_restricao` | `descricao_restricao` | STRING | vazio → NULL |
| `id_pontoconexao` | `id_ponto_conexao` | STRING | vazio → NULL |
| `nom_pontoconexao` | `nome_ponto_conexao` | STRING | vazio → NULL |
| `nom_agenteoperador` | `agente_operador` | STRING | vazio → NULL |
| `val_geracaonaorealizadaapurada` | `geracao_nao_realizada_mw` | NUMERIC | **o constrained-off apurado**; nulo sem restrição |
| `num_minutos_rel` | `minutos_rel` | INT64 | vazio → NULL |
| `num_minutos_cnf` | `minutos_cnf` | INT64 | vazio → NULL |
| `num_minutos_ene` | `minutos_ene` | INT64 | vazio → NULL |
| `num_minutos_restricao` | `minutos_restricao` | INT64 | vazio → NULL; 0 a 30 |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | derivada de `din_instante` |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | **parcialmente — 7,2%** | a granularidade é o conjunto, que não tem CEG; use `id_ons` |
| `agente_ccee` | não | o ONS não usa perfil da CCEE; há `agente_operador`, que é outra coisa |
| `periodo_apuracao` | sim | derivado de `data_referencia` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`instante`, `nome_usina`). Vence a ingestão mais recente — o
ONS revisa dado publicado.

## Gold

`gold.restricao_coff_mensal_usina` — **uma tabela para as duas fontes**, com a
coluna `tecnologia` dizendo de onde veio a linha. Por mês e usina: meias-horas
com restrição, quebradas por razão (`ENE`, `REL`, `CNF`) e por origem (`SIS`,
`LOC`), minutos de restrição e as somas do que a origem publica.

Sem KPI (ADR 012), e com um cuidado explícito: **não há conversão de MW em
energia nem em dinheiro**. A origem publica em passo de meia hora, e a regra de
conversão para MWh depende de convenção do ONS que não está no arquivo —
inventá-la aqui seria fabricar número. Por isso as colunas de soma carregam
`mw_meia_hora` no nome, dizendo exatamente o que somam.

## Qualidade e observações

- **Dry-run contra a origem real de agosto/2026 (15/09/2026)**: eólica 227.664
  extraídos, **0 inválidos**, 60,1 s; fotovoltaica 121.536 extraídos, **0
  inválidos**, 36,1 s.
- Os dois jobs declaram 1 GiB, contra 389 MiB e 275 MiB medidos — a folga cobre
  o payload que o `load_table_from_json` monta por fatia, que o dry-run não
  exercita.

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → RESTRICAO_COFF_{EOLICA|FOTOVOLTAICA}_{ano}_{mes}.csv
  → gs://<bucket>-raw/ons/restricao_coff_{eolica|fotovoltaica}/dt=…/<ingestao_id>.json.gz
    → bronze.ons_restricao_coff_{eolica|fotovoltaica}    (append-only, particionado por _ingestao_timestamp)
      → silver.ons_restricao_coff_{eolica|fotovoltaica}  (vigente; QUALIFY por instante+usina, _ingestao_timestamp DESC)
        → gold.restricao_coff_mensal_usina              (UNION ALL das duas)
```
