# CCEE — cadastro de perfis de agente

| Item | Valor |
|---|---|
| Fonte | Dados abertos da CCEE (CKAN), dataset **`lista_perfil_v1`** |
| Catálogo | `dadosabertos.ccee.org.br/api/3/action/package_show?id=lista_perfil_v1` |
| Onda | 1 — arquivo público, sem credencial |
| Natureza | **Cadastro** (retrato completo), não série temporal |
| Volume | ~60.500 perfis |
| Encoding | **ISO-8859-1** |
| Credencial | **nenhuma** |

> **É esta fonte que alimenta `agente_ccee`**, a última das cinco dimensões
> comuns que ainda não tinha origem.

## Particularidades

- **O dataset `lista_perfil` (sem sufixo) está descontinuado.** A CCEE criou
  `lista_perfil_v1` em 06/08/2025, conforme CO 562/25, e avisa no próprio
  catálogo que o antigo só é atualizado até dezembro de 2025. Apontar para o
  antigo **não daria erro** — daria cadastro congelado, que é pior, porque
  passa por dado bom.
- **Não há coluna de data.** A CCEE publica o retrato corrente, sem período.
  `data_referencia` vem do `last_modified` que o CKAN declara para o recurso —
  a data que a origem atribui ao retrato, no mesmo espírito do
  `DatGeracaoConjuntoDados` usado no `aneel_siga`. Se a origem não declarar
  data válida, a extração falha explicitamente; não é utilizada a data atual
  nem a janela como substituta.
- **A janela não recorta** (ADR 013): cadastro é lido inteiro a cada execução.
  O Bronze acumula um retrato por semana e a Silver fica com o mais recente.
- **Agente e perfil não são a mesma coisa.** Um agente pode ter vários perfis,
  e é o **perfil** que transaciona na contabilização. As duas chaves são
  preservadas.
- **`SUBMERCADO` vem sujo**: perfil sem submercado traz **espaço não separável**
  (`\xa0`), não string vazia. Sem normalizar, o schema rejeitaria a linha e o
  cadastro perderia registros contados como inválidos, sem ninguém entender o
  motivo. Nem todo perfil tem submercado — comercializador, por exemplo.
- O nome do submercado é convertido para a sigla do lake (`SUDESTE` → `SE`),
  igual ao `ccee_pld`, para cruzar com o ONS sem tradução na Silver.

## Campos

| Origem (CSV) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| — (`last_modified` do CKAN) | `data_referencia` | DATE | data do retrato |
| `COD_AGENTE` | `codigo_agente` | STRING | direto |
| `SIGLA_AGENTE` | **`agente_ccee`** | STRING | **dimensão comum** |
| `NOME_EMPRESARIAL` | `nome_empresarial` | STRING | direto |
| `CNPJ` | `cnpj` | STRING | só dígitos; 14 obrigatórios |
| `COD_PERF_AGENTE` | `codigo_perfil` | STRING | chave natural da Silver |
| `SIGLA_PERFIL_AGENTE` | `sigla_perfil` | STRING | direto |
| `CLASSE_PERFIL_AGENTE` | `classe_perfil` | STRING | Gerador, Comercializador, Consumidor Livre, Transmissor… |
| `STATUS_PERFIL` | `status_perfil` | STRING | validado contra ATIVO / ENCERRADO / PERFIL ESPECIFICO |
| `CATEGORIA_AGENTE` | `categoria_agente` | STRING | direto |
| `SUBMERCADO` | `submercado` | STRING | nome → sigla; `\xa0` vira nulo |
| `VAREJISTA` | `varejista` | BOOL | "Sim" → true |
| `TIPO_ENERG_PERF` | `tipo_energia` | STRING | vazio vira nulo |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `agente_ccee` | **sim — esta é a fonte da dimensão** | sigla do agente |
| `submercado` | parcialmente | nem todo perfil tem; nulo é legítimo |
| `data_referencia` | sim | data do retrato |
| `periodo_apuracao` | sim | `AAAA-MM` do retrato |
| `codigo_usina` | não | perfil é da empresa, não da usina |

## Deduplicação

Chave natural: `codigo_perfil` — **e não** (data, perfil) como nas fontes de
série. Aqui não se quer o histórico do cadastro, se quer o cadastro de hoje. O
histórico continua no Bronze, que é append-only, para quem precisar reconstituir
como o cadastro estava numa data passada.

## Gold

`gold.agentes_ccee` — a **tabela de dimensão**, com os perfis `ATIVO`.

Diferente das outras Gold, ela não responde uma pergunta de negócio: é o lado
"um" das junções, e é a ela que as Gold de posição comercial e de cruzamento com
dado interno vão se juntar. Perfil encerrado permanece na Silver e no Bronze,
mas sai da Gold — tabela de dimensão que devolve linha para agente extinto
produz junção que ninguém pediu.

## LGPD

O cadastro traz **CNPJ e razão social de pessoa jurídica**, que não são dado
pessoal. A exceção teórica é o perfil de pessoa física ou de MEI; não foi
observado nenhum no retrato de 01/09/2026, e o campo `NOME_EMPRESARIAL` traz
denominação empresarial em todos os registros. Se aparecer, é reavaliação de
RIPD, não ajuste de conector.

## Linhagem

```
dadosabertos.ccee.org.br (CKAN, lista_perfil_v1)
  → lista_perfil_v1_{ano}.csv (ISO-8859-1)
    → gs://<bucket>-raw/ccee/perfil/dt=.../<ingestao_id>.json.gz
      → bronze.ccee_perfil     (append-only, um retrato por execução)
        → silver.ccee_perfil   (QUALIFY ROW_NUMBER por codigo_perfil)
          → gold.agentes_ccee  (só ATIVO — tabela de dimensão)
```

## Verificação

Dry-run contra a API real em 14/09/2026: **60.509 registros, 0 inválidos**,
retrato de 01/09/2026. Não exercitado contra BigQuery real — o projeto GCP não
existe (A3). O que só a primeira carga revela: o custo de acumular ~60 mil
linhas por semana no Bronze (≈ 3 milhões de linhas por ano, particionadas por
`_ingestao_timestamp`).

## Replay do retrato

O raw JSONL inclui `_data_retrato` (data ISO do `last_modified` da origem)
em cada registro, antes da validação. `transformar()` lê esse metadado, sem
depender de extração anterior ou consulta à CCEE. A janela e o `dt=` da URI
não substituem a data do cadastro. O schema Bronze permanece igual.

Raw antigo sem esse metadado, ou com data inválida, interrompe o replay com
`ERRO`, em vez de descartar todas as linhas e informar sucesso. Preservar o
objeto original; recuperar a data apenas com evidência da publicação original.
Uma nova extração captura o retrato corrente e não recupera o histórico perdido.
