# ONS — carga de energia diária por subsistema

| Item | Valor |
|---|---|
| Fonte | Dados Abertos ONS, dataset `carga_energia_di` |
| Endpoint | `ons-aws-prod-opendata.s3.amazonaws.com/dataset/carga_energia_di/CARGA_ENERGIA_{ano}.csv` |
| Onda | 1 — arquivo público, sem credencial |
| Frequência | Diária |
| Histórico | Desde 2000, um arquivo por ano |
| Licença | CC-BY |
| Credencial | nenhuma |

## Particularidades

- **CSV remoto particionado por ano**, separador `;`. A janela decide quais anos
  baixar; as linhas fora do intervalo são descartadas na extração, para uma
  janela de uma semana não carregar o ano inteiro.
- **Primeira fonte que preenche `submercado`** — a dimensão que permite cruzar
  carga com preço e com o parque gerador.
- Submercado fora de `{N, NE, S, SE}` é **rejeitado**: sigla nova sem revisão do
  contrato de dados seria dado silenciosamente errado.
- O ONS revisa dado já publicado; por isso o agendamento reprocessa uma janela
  de 30 dias e a Silver fica com a ingestão mais recente.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `din_instante` | `data_referencia` | DATE | primeiros 10 caracteres |
| `id_subsistema` | `submercado` | STRING | maiúsculas; validado contra a lista |
| `nom_subsistema` | `nome_subsistema` | STRING | direto |
| `val_cargaenergiamwmed` | `carga_mwmed` | NUMERIC | MW médios |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | dia da carga |
| `submercado` | **sim — esta é a fonte da dimensão** | N, NE, S, SE |
| `codigo_usina` | não | carga é agregada por subsistema |
| `agente_ccee` | não | idem |
| `periodo_apuracao` | sim | `YYYY-MM` |

## Deduplicação

Chave natural: (`data_referencia`, `submercado`). Vence a ingestão mais recente.

## Gold

`gold.carga_mensal_submercado` — média, máxima e mínima por mês e submercado.
