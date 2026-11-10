# BBCE — curva forward

| Item | Valor |
|---|---|
| Fonte | BBCE Connect, produto **BBCE Curva Forward** |
| Documentação | Coleção Postman recebida da Alup em 14/09/2026 (`documenter.getpostman.com/view/48979689/2sB3QJPWWr`) |
| Onda | 2 — exige credencial |
| Autenticação | `POST {base_url}/v2/login` → JWT com validade de **4h** |
| Endpoint | `GET {base_url}/v1/curve/bbce-fwd?referenceDate=AAAA-MM-DD` |
| Frequência | Por pregão (dia útil): `cron 0 20 * * 1-5`, janela de 7 dias (`infra/modules/scheduler`). Agendada em dev e hml desde 10/11/2026 (fora de `conectores_sem_agendamento`); em prod segue sem agendamento, por falta de credencial. Limite de silêncio de 80 h (sexta a segunda são 72 h), sem alerta de e-mail (o alerta de silêncio só cobre janelas de até 26 h; a `gold.saude_ingestao` marca `ATRASADA`) |
| Credencial | secret `alupdata-bbce-credenciais` (JSON: `base_url`, `api_key`, `company_external_code`, `email` e `password`); gravada em dev e hml (pendência A7, [#23](https://github.com/nessenergy/Alupdatalake/issues/23)) |
| Bronze | `bronze.bbce_curva_forward`, append-only, particionada por `DATE(_ingestao_timestamp)` e clusterizada por `data_referencia, curva, vertice_em` |

## Por que esta fonte entra

O `ccee_pld` traz o preço **à vista**. A curva forward traz o preço **negociado
hoje para entrega futura**: para cada data de referência, um conjunto de
vértices. É o que permite comparar a expectativa do mercado com o realizado.

## Particularidades

- **O host não está na documentação.** A coleção usa `{{baseUrl}}` sem valor —
  o endereço vem junto com o acesso. Por isso ele é **configuração, não
  constante**, e entra no mesmo secret das credenciais. Sem ele o conector falha
  dizendo exatamente o que falta, em vez de tentar um host inventado.
- **A autenticação é de sessão, não token fixo.** São quatro credenciais
  (`apiKey`, `companyExternalCode`, `email`, `password`), e o login devolve um
  JWT de 4h. Elas vão num **único secret estruturado em JSON**, como as DSN dos
  bancos da Onda 3: a Alup preenche uma coisa só e não há estado
  meio-configurado.
- **O token da consulta é o `idToken` do login**, em `Authorization: Bearer <idToken>`, e o `accessToken` vai também na query (`accessToken=`). Só com o `accessToken` em `Authorization` a API responde 500 `accessToken parameter is required` (27/10/2026); o `idToken` é o que o cliente de all-deals da mesa usa (corrigido em 28/10, PR #434).
- **A senha vai no corpo do POST, nunca em query string** — em query ela
  apareceria no log de acesso da BBCE e em qualquer proxy no caminho.
- **O JWT é reaproveitado** dentro da janela; um login por dia gastaria uma
  autenticação por requisição de dado. Diante de **401 o conector reautentica
  uma vez e repete**; 401 persistente é credencial revogada e **falha a
  execução** — devolver vazio seria lido como "dia sem curva" e o buraco
  passaria despercebido.
- **A BBCE data em UTC representando meia-noite de Brasília** (`03:00:00.000Z`).
  Cortar a string em 10 caracteres acerta por acidente; a conversão de fuso é
  explícita. O offset é fixo em −3h porque o Brasil não observa horário de verão
  desde 2019 — mesma premissa do agendador. **Se o horário de verão voltar, é
  esse ponto que quebra**, e o teste de `_data_brasilia` é o que avisa.
- **Dia sem pregão devolve lista vazia** e a janela segue.

## Campos

| Origem (JSON) | Bronze / Silver | Tipo | Transformação |
|---|---|---|---|
| `date` | `data_referencia` | DATE | instante UTC → data em Brasília |
| `name` | `curva` | STRING | nome do produto, ex.: `PLD` |
| `vertexDate` | `vertice_em` | DATE | instante UTC → data em Brasília |
| `vertexValue` | `preco_reais_mwh` | NUMERIC | R$/MWh; negativo é rejeitado |
| `dataSource` | `origem_dado` | STRING | direto |
| `identity` | `identidade` | STRING | ex.: `CURVE` |
| `id` | `id_origem` | STRING | identificador do vértice na BBCE |
| `updatedAt` | `atualizado_em` | TIMESTAMP | a curva é revisada |
| — (derivado) | `horizonte_dias` | INT64 | `vertice_em − data_referencia`, só na Silver |

**Regra de negócio validada**: vértice anterior à data de referência é
rejeitado. Curva forward precifica o futuro; vértice no passado é erro de
origem, não dado.

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | sim | pregão |
| `periodo_apuracao` | sim | `AAAA-MM` do pregão |
| `submercado` | não | a curva publicada é do produto, não do submercado |
| `codigo_usina` | não | — |
| `agente_ccee` | não | preço de mercado, não posição de agente |

## Deduplicação

Chave natural: (`data_referencia`, `curva`, `vertice_em`). Vence a ingestão mais
recente — a BBCE revisa curva publicada, e é por isso que `atualizado_em`
existe.

## Gold

`gold.curva_forward_vigente` — a curva do último pregão de cada curva, por vértice. Responde
"quanto o mercado está pedindo hoje para entrega em cada período futuro".

| Coluna | Tipo | Origem |
|---|---|---|
| `curva` | STRING | Silver |
| `data_referencia` | DATE | Silver (o último pregão da curva) |
| `vertice_em` | DATE | Silver |
| `vertice_periodo` | STRING | Silver (`AAAA-MM` do vértice) |
| `horizonte_dias` | INT64 | Silver |
| `preco_reais_mwh` | NUMERIC | Silver |
| `atualizado_em` | TIMESTAMP | Silver |

Asserções do Dataform (ADR 012): na Silver, `uniqueKey` (`data_referencia`, `curva`, `vertice_em`), `nonNull` e faixas (preço
maior ou igual a zero, vértice não anterior à referência, horizonte não negativo); na Gold, `uniqueKey` (`curva`, `vertice_em`)
e `nonNull`, para que duplicata ou nulo não cheguem a quem consome.

O histórico de curvas fica na Silver: estudar como a expectativa se moveu ao
longo do tempo é análise de outra natureza e merece tabela própria quando for
pedida. **Não há cálculo de prêmio sobre o PLD** — a regra de comparação depende
dos domínios analíticos (A4), e inventá-la seria escolher pelo cliente.

## Linhagem

```
BBCE Connect (POST /v2/login → JWT)
  → GET /v1/curve/bbce-fwd?referenceDate=…
    → gs://<bucket>-raw/bbce/curva_forward/dt=.../<ingestao_id>.json.gz
      → bronze.bbce_curva_forward
        → silver.bbce_curva_forward   (+ horizonte_dias)
          → gold.curva_forward_vigente
```

## O que foi verificado e o que falta

Verificado em 28/10/2026, com a credencial real, em dev e hml (PR #434):

1. **Host:** vem do `base_url` da credencial, como previsto.
2. **`Authorization`:** é `Bearer <idToken>`, e o `accessToken` também vai na query (ver Particularidades).
3. **Volume da execução de 28/10:** 255 linhas extraídas, 1 inválida e 254 carregadas, em dev e hml.

Sem verificação:

- **Motivo da linha inválida** de 28/10 (preço negativo, vértice anterior à referência ou outro): conferir no log da ingestão.
- **Dia sem pregão:** o conector trata lista vazia como ausência e não trata 404 à parte; a suposição é 200 com lista vazia.
- **Mais de um produto na curva:** o exemplo só mostra `name: "PLD"`; outros entrariam sem mudança, porque a chave já inclui `curva`.
- **Contagem em hml da Silver e da Gold depois do Dataform** (254 na Silver em 28/10; a Gold estava vazia até o Dataform rodar): só se confere no ambiente.
