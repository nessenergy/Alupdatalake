# Runbook — conferir cargas, sondar a rede e ler `origem_indisponivel`

Para quem opera o lake depois do handoff. Cobre três ferramentas de **leitura** que não mudam dado nem infraestrutura. O que muda dado (reprocessar, replay) está em [`incidentes.md`](incidentes.md) §4; o deploy, em [`deploy.md`](deploy.md).

## 1. Conferir cargas

**Para quê.** Dizer, sem `gcloud auth` pessoal, o que há no BigQuery de um ambiente: contagens e datas das Silver e Gold, a última execução de cada conector, a saúde da ingestão e o último erro.

**Como rodar.** Aba **Actions → Conferir cargas → Run workflow**, escolhendo o ambiente (`dev`, `hml` ou `prod`). Ou:

```bash
gh workflow run "Conferir cargas" -f environment=hml
```

O resultado sai no **Summary** da execução, uma seção por conjunto. A única entrada é o ambiente. O workflow roda com a conta de deploy e só executa `SELECT` ou `WITH`; o código recusa qualquer outro comando. Tabela que não existe no ambiente aparece como `ausente`, e o resto continua.

**Itens e como lê-los** (definidos em `scripts/conferir_cargas.py`):

| Item | O que mostra | Como interpretar |
|---|---|---|
| `ultima_execucao` | status, linhas extraídas, inválidas e carregadas da última execução de cada conector conferido, e a data | `SUCESSO` com 0 linhas pode ser janela sem dado na origem, não defeito; compare com a data |
| `ultimo_erro` | o erro mais recente nos últimos 3 dias, por conector | "sem linhas" quer dizer nenhum erro no período. O texto é truncado em 200 caracteres e passa por sanitização |
| `erros_3_dias` | quantas execuções com `ERRO` cada conector teve nos últimos 3 dias | um erro isolado e depois `SUCESSO` costuma ser origem fora do ar (§3) |
| `saude_ingestao` | quantas fontes há em cada situação | veja a tabela abaixo |
| `saude_fora_do_ok` | cada fonte que **não** está `OK`, com situação, último sucesso, última execução e último erro | é a lista a investigar; `aguardando_credencial = true` é espera da Alup, não defeito |
| `cruzamento_ear`, `poligonos`, `precipitacao_diaria_*`, `bcb_igpm_ultimos_3_meses` | conferências de entregas específicas da Onda 1 | usadas para homologar; não são alarme |

**Situações da `saude_ingestao`:**

| Situação | Significa |
|---|---|
| `OK` | sucesso dentro do limite de silêncio e sem erro posterior |
| `ATRASADA` | último sucesso mais antigo que o limite de silêncio da fonte |
| `FALHA_RECENTE` | houve erro depois do último sucesso |
| `SEM_SUCESSO` | a fonte nunca teve sucesso |

**O que NÃO fazer.** Não use este workflow para "consertar" nada: ele não escreve. Para recarregar, use `Executar ingestão` (`incidentes.md` §4). Se o item `saude_fora_do_ok` não existir no resumo, a `main` do ambiente é anterior ao PR #385.

## 2. Sondar rede

**Para quê.** Saber o que uma URL pública responde **de dentro do GCP**, para separar bloqueio do IP da máquina de desenvolvimento de bloqueio da origem. Foi assim que se verificou que o CPTEC devolve 403 também de dentro do GCP (ADR 029).

**Como rodar.** **Actions → Sondar rede**, com o ambiente e a sonda:

| Sonda | O que chama |
|---|---|
| `cptec` | duas URLs do webservice do CPTEC (lista de cidades e previsão de 7 dias) |
| `inmet_previsao` | a previsão do INMET para São Paulo |
| `open_meteo` | a previsão de 7 dias do Open-Meteo |

A lista é fixa em `src/core/sonda.py` (`SONDAS`). **Não aceita URL livre**, de propósito.

**Como funciona.** O workflow executa o Cloud Run Job `ingestao-bcb-cambio-ptax` com o argumento `sondar <nome>`. O job grava o resultado em `gs://<projeto>-raw/sondas/<nome>/<UTC>.json`, e o workflow lê esse arquivo e o mostra no Summary. A conta de deploy **não lê o Cloud Logging**, por isso o resultado vai ao bucket.

**Como interpretar.** Cada URL traz o status HTTP ou o erro de rede. 200 com corpo é fonte acessível. 403 é bloqueio da origem. Erro de DNS ou de conexão é rede.

**O que NÃO fazer.** Não adicione sonda de URL que carregue credencial. O job sai sempre com código 0: um resultado ruim não derruba o workflow, ele só aparece no resumo.

## 3. Ler `origem_indisponivel`

Em `bronze._execucoes.erro`, um erro que começa com `origem_indisponivel: ` significa que a **origem não respondeu**: erro de rede, DNS, *timeout* ou HTTP 5xx (`src/core/conector.py`, `descrever_erro`). **Não é defeito do conector** e normalmente se resolve sozinho.

| Situação | Ação |
|---|---|
| Um ou dois erros e depois `SUCESSO` | nenhuma: a janela móvel do agendamento cobre o dia perdido (`incidentes.md` §3.1) |
| Erro repetido por mais que a janela | reprocessar o intervalo (`incidentes.md` §4.1) e verificar se a origem mudou de endereço |
| Erro **sem** o prefixo (por exemplo `HTTPError: 401` ou `NotFound: ... secret`) | é nosso lado: credencial, formato ou segredo sem versão (`incidentes.md` §3.2 e §3.3) |

Um 401 ou 403 **não** ganha o prefixo: significa que a origem respondeu e recusou.
