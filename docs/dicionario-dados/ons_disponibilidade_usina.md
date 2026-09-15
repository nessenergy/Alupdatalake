# ONS — disponibilidade horária por usina

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `disponibilidade_usina_ho` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/disponibilidade_usina_ho/DISPONIBILIDADE_USINA_{ano}_{mes:02d}.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Um CSV por mês |
| Volume verificado | 117.480 linhas, 17 MB — recurso de agosto/2026, lido em 15/09/2026 |
| Encoding | UTF-8 |
| Licença | CC-BY |
| Credencial | nenhuma |

## Por que esta fonte existe no lake

O domínio Geração e Operacional pergunta **quais ativos existem, quanto cada um
gerou e quanto foi medido**. Com o cadastro (`aneel_siga`), a capacidade
(`ons_capacidade`) e a geração (`ons_geracao_usina`), faltava a peça que separa
duas leituras que se parecem no dado e não se parecem no negócio: **usina
parada** e **usina apta mas não despachada**. As duas geram pouco; só uma é
problema do ativo.

É esta fonte que responde isso, hora a hora.

## Particularidades

- **Recurso mensal, não anual.** A janela decide quais meses baixar e recorta
  as linhas na extração — mesmo desenho do `ons_geracao_usina`.
- **Cobre só o parque despachado centralmente.** Em agosto/2026 o arquivo
  trouxe **UHE (72.168), UTE (43.824) e UTN (1.488)** — nenhuma eólica ou
  solar. Quem procurar disponibilidade de eólica não a encontra aqui; o
  equivalente para essas fontes é o constrained-off (`restricao_coff_eolica_usi`),
  que ainda não está conectado.
- **158 usinas × 24 h × 31 dias = 117.480 linhas**, exatamente. Uma linha por
  usina por hora, sem furo — o que torna `(data_referencia, hora, nome_usina)`
  uma chave natural confiável.
- **Zero não é ausência.** Usina indisponível na hora vem com
  `val_dispoperacional = 0`, e é o caso que esta fonte existe para mostrar.
  Campo **vazio** vira NULL. Confundir os dois inverteria a leitura, e há um
  teste fixando cada um.
- **O CEG vem em 100% das linhas** de agosto/2026 — diferente do
  `ons_geracao_usina`, onde só 52% trazem CEG (MMGD agregada não tem). Das 155
  usinas com CEG, **152 (98,1%) casam com o cadastro da ANEEL** na forma
  canônica de `src/core/ceg.py`. Esta fonte entra praticamente inteira no
  `gold.de_para_usina`.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` + `hora` | DATE + INT64 | derivados no `model_validator`; formato inválido vira linha inválida, não crash |
| `id_subsistema` | `submercado` | STRING | trim, maiúsculas; só `{N,NE,S,SE}` — sigla desconhecida é rejeitada |
| `nom_subsistema` | `nome_subsistema` | STRING | trim |
| `id_estado` | `uf` | STRING | trim |
| `nom_estado` | `nome_uf` | STRING | trim |
| `id_tipousina` | `tipo_usina` | STRING | UHE, UTE, UTN |
| `nom_tipocombustivel` | `tipo_combustivel` | STRING | trim |
| `nom_usina` | `nome_usina` | STRING | trim |
| `id_ons` | `id_ons` | STRING | vazio ou `"-"` → NULL |
| `ceg` | `codigo_usina` | STRING | **forma canônica** (`src/core/ceg.py`); vazio ou `"-"` → NULL |
| `val_potenciainstalada` | `potencia_instalada` | NUMERIC | vazio → NULL; **zero é zero** |
| `val_dispoperacional` | `disponibilidade_operacional` | NUMERIC | vazio → NULL; **zero é zero** |
| `val_dispsincronizada` | `disponibilidade_sincronizada` | NUMERIC | vazio → NULL; **zero é zero** |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | derivada de `din_instante` |
| `submercado` | sim | N, NE, S, SE |
| `codigo_usina` | **sim — o CEG, em 100% das linhas** | na forma canônica; 98,1% casam com a ANEEL |
| `agente_ccee` | não | o ONS não usa perfil da CCEE |
| `periodo_apuracao` | sim | derivado de `data_referencia` |
| `periodo_apuracao_ccee` | não | a origem não declara período próprio |

## Deduplicação

Chave natural: (`data_referencia`, `hora`, `nome_usina`). Vence a ingestão mais
recente — o ONS revisa dado publicado, como no `ons_carga`.

## Gold

`gold.disponibilidade_mensal_usina` — horas no mês, horas com medida, **horas
indisponível** (disponibilidade igual a zero), potência instalada e a média, o
mínimo e o máximo da disponibilidade, por mês e usina. Sem KPI (ADR 012): a
razão entre disponibilidade e capacidade é decisão de negócio, não desta fase.

`gold.de_para_usina` — CEG ↔ nome ANEEL ↔ nome ONS, com `sigla_ccee` nula à
espera do insumo da Alup ([#141](https://github.com/nessenergy/Alupdatalake/issues/141)).

## Qualidade e observações

- **Dry-run contra a origem real de agosto/2026 (15/09/2026)**: 117.480
  extraídos, **0 inválidos**, `SUCESSO` em 29,8 s.
- **Pico de memória medido**: 226 MiB, somando processo e filhos, 132 amostras.
  O job declara 1 GiB — folga de 4x sobre o medido, que é o que cobre o payload
  que o `load_table_from_json` monta por fatia e que o dry-run não exercita.
- Nenhum campo veio vazio no mês verificado. O tratamento de vazio existe assim
  mesmo: um mês com falha de medição não pode derrubar a ingestão inteira.

## Linhagem

```
ons-aws-prod-opendata.s3.amazonaws.com → DISPONIBILIDADE_USINA_{ano}_{mes}.csv
  → gs://<bucket>-raw/ons/disponibilidade_usina/dt=…/<ingestao_id>.json.gz
    → bronze.ons_disponibilidade_usina    (append-only, particionado por _ingestao_timestamp)
      → silver.ons_disponibilidade_usina  (vigente; QUALIFY por data+hora+usina, _ingestao_timestamp DESC)
        → gold.disponibilidade_mensal_usina
```
