# Itens 1 a 4 da Onda 1 — Plano de Implementação

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Goal:** (1) descobrir se o CPTEC responde a partir do GCP; (2) entregar a chuva média por bacia; (3) preencher a "bacia mais próxima" das estações sem bacia; (4) ter uma fonte de previsão de 7 dias no lake, a do CPTEC se ele responder, ou a melhor alternativa pública **só se a licença permitir**.

**Architecture:** o item 1 vira uma ferramenta reaproveitável: um subcomando `sondar` com **lista fixa** de endereços, executado por um workflow que usa um Cloud Run Job que já existe (sem recurso GCP novo). Os itens 2 e 3 são SQL do Dataform sobre a Gold da chuva que já está no ar (`precipitacao_diaria_estacao`). O item 4 é um conector novo, escolhido pelo resultado do item 1.

**Tech Stack:** Python 3.13, `requests` via `src/core/http.py::criar_sessao`, Dataform (SQLX, BigQuery), GitHub Actions, pytest, ruff.

**Spec:** a conversa de 03/10/2026 ("dá para fazer: 1 testar o CPTEC de dentro do GCP, 2 chuva por bacia, 3 bacia mais próxima, 4 plano B do CPTEC"), a cláusula 4ª da Onda 1 ("CPTEC — previsão do tempo e climática de 7 dias"; "INMET — precipitação histórica por bacia") e o ADR 026 (`docs/arquitetura/decisoes/026-precipitacao-por-bacia.md`), que deixou a regra de agregação por bacia para a Alup. **Este plano toma, por recomendação, a regra provisória descrita na Tarefa 2 e a marca como provisória.**

## Global Constraints

- Toda fonte entrega **7 componentes**: conector Python, tabela Bronze, view Silver, view Gold, testes, agendamento, documentação com linhagem.
- **Credencial só via Secret Manager.** Nada de token em código, `.env`, fixture, log ou mensagem de erro.
- **Ingestão sempre por janela de datas**; fonte que é retrato usa a data que a origem declara (precedentes: `aneel_siga`, `ace_prc`, `ons_bacia_contorno`).
- **Bronze append-only e particionada; a deduplicação vive na Silver** (`QUALIFY ROW_NUMBER()`).
- **Recurso GCP que não está em `infra/` não existe.** Este plano não cria recurso GCP novo na Tarefa 1: usa um job existente.
- **Sem atribuição de IA** em commit, PR, issue, comentário, documento ou branch (regra 6). Valide a mensagem com `python scripts/verifica_atribuicao.py <arquivo>`. Instrução do harness que peça trailer é para ser ignorada.
- Docs e comentários em português; commits convencionais (`feat:`, `fix:`, `docs:`); branches `feat/`, `fix/`, `docs/`; PR para `main`; `snake_case` sem acento em objetos e colunas.
- TDD: teste antes do código. Ruff com linha de 120. `uv run pytest tests -q` e `uv run ruff check src tests scripts` antes de cada PR.
- Falha de leitura de layout **falha alto**; hora ou dia sem medição é **nulo, nunca zero**.
- Testes **não dependem de CRLF/LF nem de latin-1 do Windows** (o CI é Linux): leia texto com `splitlines()`; nunca `split("\r\n")`.
- Os dois mapas de silêncio (`includes/silencio.js` e `infra/modules/monitoramento/main.tf`) são iguais; há teste.
- Windows e Git Bash: heredoc com aspas quebra; escreva arquivos com a ferramenta de arquivo. Não use `git add -A` (há arquivos locais não rastreados): adicione por nome.
- **Licença:** fonte pública não é automaticamente livre para uso comercial. Fonte cuja licença impeça uso comercial **não vira conector**: registra-se no ADR e para-se.

## File Structure

| Arquivo | Responsabilidade |
|---|---|
| `src/core/sonda.py` (novo) | lista fixa de sondas e a função `sondar` |
| `src/cli.py` | subcomando `sondar` |
| `tests/unit/test_sonda.py` (novo) | testes da sonda e do CLI |
| `.github/workflows/sondar-rede.yml` (novo) | roda `sondar` num job existente e mostra o resultado |
| `definitions/gold/precipitacao_diaria_bacia.sqlx` (novo) | chuva diária média por bacia |
| `definitions/gold/precipitacao_diaria_estacao.sqlx` | acrescenta bacia mais próxima e distância |
| `tests/unit/test_sql.py` | testes de string que fixam as regras do SQL |
| `scripts/conferir_cargas.py`, `tests/unit/test_conferir_cargas.py` | conferem as duas Gold novas |
| `scripts/anotar_catalogo.py`, `docs/dicionario-dados/inmet_precipitacao.md`, `docs/arquitetura/dominios-analiticos.md`, `docs/arquitetura/decisoes/026-...md` | catálogo e documentação |
| `docs/arquitetura/decisoes/029-previsao-do-tempo-fonte.md` (novo, Tarefa 1) | resultado das sondas e a decisão do item 4 |
| Tarefa 4 (condicional) | `src/conectores/<fonte>.py`, camadas SQL, agendamento, silêncio, dicionário |

---

### Tarefa 1: Sonda de rede e workflow (item 1)

**Por que:** o 403 do CPTEC pode ser só bloqueio do IP da máquina de desenvolvimento. Para saber, a chamada precisa sair de dentro do GCP. O `Executar ingestão` só roda `ingerir`; o job é o mesmo e aceita `--args`, então um subcomando novo roda por ele.

**Files:**
- Create: `src/core/sonda.py`, `tests/unit/test_sonda.py`, `.github/workflows/sondar-rede.yml`
- Modify: `src/cli.py` (subcomando `sondar`)

**Interfaces:**
- Produces: `SONDAS: dict[str, tuple[str, ...]]`; `ResultadoSonda` (dataclass: `url: str`, `status: int | None`, `bytes: int`, `tipo: str`, `amostra: str`, `erro: str | None`); `sondar(nome: str, sessao=None) -> list[ResultadoSonda]`. O CLI imprime **uma linha JSON por endereço** e **sempre devolve 0** (a sonda não é gate).

- [ ] **Passo 1: escrever os testes (falham)**

`tests/unit/test_sonda.py`:
```python
"""Sondas de rede: dizem se um endereço público responde do ambiente onde o job roda. Sem rede."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from src.cli import main
from src.core.sonda import PREVIEW, SONDAS, ResultadoSonda, sondar

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "sondar-rede.yml"


class RespostaFalsa:
    def __init__(self, status: int, corpo: bytes, tipo: str = "text/xml") -> None:
        self.status_code = status
        self.content = corpo
        self.headers = {"Content-Type": tipo}


class SessaoFalsa:
    def __init__(self, respostas: dict[str, object]) -> None:
        self.respostas = respostas
        self.chamadas: list[str] = []

    def get(self, url: str, timeout: float):  # noqa: ARG002
        self.chamadas.append(url)
        resposta = self.respostas[url]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _todas(status: int = 200) -> SessaoFalsa:
    return SessaoFalsa({url: RespostaFalsa(status, b"<ok/>") for urls in SONDAS.values() for url in urls})


def test_sonda_registra_status_tamanho_tipo_e_amostra() -> None:
    sessao = _todas(403)
    [primeiro, *_] = sondar("cptec", sessao)

    assert isinstance(primeiro, ResultadoSonda)
    assert (primeiro.status, primeiro.bytes, primeiro.tipo, primeiro.amostra) == (403, 5, "text/xml", "<ok/>")
    assert primeiro.erro is None


def test_endereco_que_levanta_vira_erro_e_nao_derruba_os_outros() -> None:
    urls = SONDAS["cptec"]
    sessao = SessaoFalsa({urls[0]: ConnectionError("dns"), urls[1]: RespostaFalsa(200, b"ok")})

    resultados = sondar("cptec", sessao)

    assert [r.status for r in resultados] == [None, 200]
    assert "ConnectionError" in (resultados[0].erro or "")
    assert sessao.chamadas == list(urls)


def test_amostra_e_truncada_e_sem_quebra_de_linha() -> None:
    url = SONDAS["open_meteo"][0]
    sessao = SessaoFalsa({url: RespostaFalsa(200, ("a\n" * 500).encode())})

    [resultado] = sondar("open_meteo", sessao)

    assert len(resultado.amostra) <= PREVIEW
    assert "\n" not in resultado.amostra


def test_so_conhece_as_sondas_da_lista() -> None:
    with pytest.raises(KeyError):
        sondar("qualquer_coisa", _todas())


def test_enderecos_sao_constantes_sem_marcador_de_substituicao() -> None:
    for urls in SONDAS.values():
        for url in urls:
            assert url.startswith(("http://", "https://"))
            assert "{" not in url
            assert " " not in url


def test_cli_imprime_uma_linha_json_por_endereco_e_devolve_zero(monkeypatch, capsys) -> None:
    monkeypatch.setattr("src.core.sonda.criar_sessao", lambda: _todas(403))

    codigo = main(["sondar", "cptec"])

    saida = [json.loads(linha) for linha in capsys.readouterr().out.splitlines() if linha.startswith("{")]
    assert codigo == 0
    assert [linha["status"] for linha in saida] == [403] * len(SONDAS["cptec"])
    assert {linha["sonda"] for linha in saida} == {"cptec"}


def test_cli_recusa_sonda_fora_da_lista() -> None:
    with pytest.raises(SystemExit):
        main(["sondar", "http://exemplo.com"])


def test_workflow_so_oferece_as_sondas_da_lista_e_nao_interpola_entrada_em_run() -> None:
    fluxo = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    entradas = fluxo[True]["workflow_dispatch"]["inputs"]  # PyYAML lê `on` como True

    assert set(entradas) == {"environment", "sonda"}
    assert set(entradas["sonda"]["options"]) == set(SONDAS)
    for passo in fluxo["jobs"]["sondar"]["steps"]:
        assert "${{ inputs." not in passo.get("run", "")
```

- [ ] **Passo 2: rodar e ver falhar**

Run: `uv run pytest tests/unit/test_sonda.py -q`
Expected: erro de coleta (`ModuleNotFoundError: src.core.sonda`).

- [ ] **Passo 3: implementar `src/core/sonda.py`**

```python
"""Sondas de rede: dizem se um endereço público responde do ambiente onde o job roda.

Nasceu do CPTEC: o webservice responde 403 da máquina de desenvolvimento, e a pergunta "e de dentro do GCP?"
só se responde com a chamada saindo de lá. A lista de endereços é **constante** (nada vem de entrada do
usuário) e a sonda não grava nada: só devolve status, tamanho, tipo e os primeiros caracteres do corpo.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.core.http import criar_sessao

PREVIEW = 160
TIMEOUT_SEGUNDOS = 30

SONDAS: dict[str, tuple[str, ...]] = {
    "cptec": (
        "http://servicos.cptec.inpe.br/XML/listaCidades?city=sao%20paulo",
        "http://servicos.cptec.inpe.br/XML/cidade/7dias/244/previsao.xml",
    ),
    "inmet_previsao": ("https://apiprevmet3.inmet.gov.br/previsao/3550308",),
    "open_meteo": (
        "https://api.open-meteo.com/v1/forecast?latitude=-23.55&longitude=-46.63"
        "&daily=precipitation_sum&forecast_days=7&timezone=America%2FSao_Paulo",
    ),
}


@dataclass(frozen=True)
class ResultadoSonda:
    url: str
    status: int | None
    bytes: int
    tipo: str
    amostra: str
    erro: str | None


def sondar(nome: str, sessao=None) -> list[ResultadoSonda]:
    """Chama cada endereço da sonda `nome`. Erro de rede vira linha com `erro`, nunca exceção."""
    if nome not in SONDAS:
        raise KeyError(f"sonda desconhecida: {nome!r}; use uma de {sorted(SONDAS)}")
    sessao = sessao or criar_sessao()
    resultados = []
    for url in SONDAS[nome]:
        try:
            resposta = sessao.get(url, timeout=TIMEOUT_SEGUNDOS)
            corpo = resposta.content
            amostra = corpo[:PREVIEW].decode("utf-8", errors="replace").replace("\r", " ").replace("\n", " ")
            resultados.append(
                ResultadoSonda(url, resposta.status_code, len(corpo), resposta.headers.get("Content-Type", ""), amostra, None)
            )
        except Exception as exc:  # noqa: BLE001 - a sonda existe para registrar a falha, não para propagá-la
            resultados.append(ResultadoSonda(url, None, 0, "", "", f"{type(exc).__name__}: {str(exc)[:200]}"))
    return resultados
```

- [ ] **Passo 4: o subcomando no CLI**

Em `src/cli.py`, depois do bloco `teste = sub.add_parser("testar-conexao", ...)` e antes de `return parser`:
```python
    sonda = sub.add_parser("sondar", help="chama os endereços de uma sonda fixa e imprime status e amostra")
    sonda.add_argument("nome", choices=sorted(SONDAS), help="sonda da lista fixa em src/core/sonda.py")
```
No topo, `from src.core.sonda import SONDAS, sondar`. Em `main`, junto aos outros `if args.comando == ...`:
```python
    if args.comando == "sondar":
        for resultado in sondar(args.nome):
            print(json.dumps({"sonda": args.nome, **dataclasses.asdict(resultado)}, ensure_ascii=False))
        return 0
```
(com `import dataclasses` e `import json` no topo). Atualize o docstring do módulo com `alupdata sondar cptec`.

- [ ] **Passo 5: o workflow**

`.github/workflows/sondar-rede.yml`: leia `.github/workflows/executar-ingestao.yml` **inteiro** e copie dele a autenticação (WIF com `vars.GCP_WIF_PROVIDER` e `vars.GCP_DEPLOY_SA`), as ações **fixadas por SHA**, o `permissions: contents: read, id-token: write`, o `environment: ${{ inputs.environment }}`, e a forma de executar o job e de ler os logs da execução. Diferenças:
- Entradas: `environment` (choice `dev`, `hml`, `prod`) e `sonda` (choice com **exatamente** as chaves de `SONDAS`: `cptec`, `inmet_previsao`, `open_meteo`).
- O job executado é `ingestao-bcb-cambio-ptax` (existe em todos os ambientes), com `--args="sondar,$SONDA"` e `--wait`. A sonda não grava nada e devolve 0, então não dispara o alerta de ingestão falhou.
- Os logs da execução (linhas que começam com `{"sonda"`) vão para o log do passo **e** para `$GITHUB_STEP_SUMMARY`, em bloco de código.
- **Nenhuma entrada do usuário entra num `run:` por `${{ }}`**: vai por `env:` e é validada (`[[ "$SONDA" =~ ^[a-z_]+$ ]]`).
- Cabeçalho comentado: explica o porquê (ADR 015, só a SA de deploy executa job) e que a sonda é somente leitura de endereço público.

- [ ] **Passo 6: rodar os testes e o lint**

Run: `uv run pytest tests/unit/test_sonda.py -q` e depois `uv run pytest tests -q`, `uv run ruff check src tests scripts`, `uv run ruff format src tests`
Expected: PASS (8 testes novos), suíte verde.

- [ ] **Passo 7: commit**

```bash
git add src/core/sonda.py src/cli.py tests/unit/test_sonda.py .github/workflows/sondar-rede.yml
git commit -m "feat: sondar rede, workflow que chama endereços públicos de dentro do GCP"
```

- [ ] **Passo 8 (controlador, depois do merge): rodar as três sondas em `dev` e em `hml`** e gravar o resultado no ADR 029 (Tarefa 1b abaixo).

### Tarefa 1b: ADR 029 com o resultado das sondas

**Files:** Create: `docs/arquitetura/decisoes/029-previsao-do-tempo-fonte.md`

- [ ] **Passo 1:** rode `gh workflow run "Sondar rede" -f environment=dev -f sonda=<cada uma>` (e `hml`), leia a saída e escreva o ADR no formato do `028-cptec-acesso.md`: Contexto, uma tabela **ambiente × sonda × endereço × status × tipo × amostra**, e a **Decisão** pela regra abaixo.
- [ ] **Passo 2: regra de decisão (aplique nesta ordem)**
  1. **CPTEC responde 200 com XML** de dentro do GCP: decisão **A**, Tarefa 4A (conector do CPTEC). O 403 era do IP da máquina de desenvolvimento.
  2. CPTEC bloqueado também de dentro do GCP, e `inmet_previsao` responde 200 com JSON de pelo menos 7 dias de previsão: decisão **B**, Tarefa 4B (conector do INMET como **alternativa**, registrada como substituição que depende de aceite da Alup por escrito).
  3. Nenhuma das duas serve: decisão **C**, **não construir**. O Open-Meteo só entra se a licença permitir uso comercial **sem plano pago**; a página de termos dele diz que o uso gratuito é para fins não comerciais, então por padrão ele **não** vira conector. Registre isso e pare.
- [ ] **Passo 3:** commit `docs: ADR 029, de onde vem a previsão do tempo`.

---

### Tarefa 2: Chuva diária média por bacia (item 2)

**Regra provisória (decisão deste plano, por recomendação, a ser confirmada pela Alup):** média **simples** entre as estações da bacia, contando só **dia de estação completo** (24 horas com medição). Dia com buraco não entra na média, porque somar só as horas medidas subestimaria a chuva. A linha traz `estacoes_na_bacia` (estações da bacia com algum dado no dia) e `estacoes_validas` (as que entraram), para a pessoa ver em quantas a média se apoia. Sem ponderação por área.

**Files:**
- Create: `definitions/gold/precipitacao_diaria_bacia.sqlx`
- Modify: `tests/unit/test_sql.py`, `scripts/conferir_cargas.py`, `tests/unit/test_conferir_cargas.py`, `scripts/anotar_catalogo.py`, `docs/dicionario-dados/inmet_precipitacao.md`, `docs/arquitetura/dominios-analiticos.md`, `docs/arquitetura/decisoes/026-precipitacao-por-bacia.md`

**Interfaces:**
- Consumes: `gold.precipitacao_diaria_estacao` com as colunas `estacao`, `bacia`, `bacia_chave`, `data_referencia`, `precipitacao_mm_dia`, `horas_com_medicao`.
- Produces: `gold.precipitacao_diaria_bacia` com `bacia`, `bacia_chave`, `data_referencia`, `estacoes_na_bacia`, `estacoes_validas`, `precipitacao_mm_dia_media`, `precipitacao_mm_dia_maxima`.

- [ ] **Passo 1: testes de SQL (falham)** em `tests/unit/test_sql.py` (o arquivo já importa `Path`; confira e reutilize o padrão dos outros testes de Gold):

```python
def _gold(nome: str) -> str:
    return (Path(__file__).resolve().parents[2] / "definitions" / "gold" / f"{nome}.sqlx").read_text(encoding="utf-8")


def test_chuva_por_bacia_so_media_dia_completo_de_estacao() -> None:
    """Dia com buraco subestimaria a chuva se entrasse na média: só horas_com_medicao = 24 conta."""
    sql = _gold("precipitacao_diaria_bacia")
    assert "horas_com_medicao = 24" in sql
    assert "AVG(IF(horas_com_medicao = 24, precipitacao_mm_dia, NULL))" in sql
    assert "WHERE bacia IS NOT NULL" in sql
    assert "COALESCE(precipitacao_mm_dia" not in sql  # dia sem dado é nulo, nunca zero


def test_chuva_por_bacia_diz_em_quantas_estacoes_se_apoia() -> None:
    sql = _gold("precipitacao_diaria_bacia")
    assert "estacoes_na_bacia" in sql
    assert "estacoes_validas" in sql
    assert "GROUP BY bacia, bacia_chave, data_referencia" in sql


def test_chuva_por_bacia_le_a_gold_da_estacao_e_nao_a_silver() -> None:
    sql = _gold("precipitacao_diaria_bacia")
    assert 'ref("gold", "precipitacao_diaria_estacao")' in sql
    assert 'ref("silver"' not in sql
```

- [ ] **Passo 2:** `uv run pytest tests/unit/test_sql.py -q -k chuva_por_bacia` → FAIL (arquivo inexistente).

- [ ] **Passo 3: a Gold**

`definitions/gold/precipitacao_diaria_bacia.sqlx`:
```sql
config {
  type: "table",
  schema: "gold",
  tags: ["gold"],
  dependOnDependencyAssertions: true
}

-- Gold: chuva diária por bacia, a partir da chuva por estação (cláusula 4ª: "precipitação histórica por bacia").
-- **Regra provisória, da ness., a confirmar com a Alup (ADR 026):** média SIMPLES entre as estações da bacia,
-- contando só o dia de estação COMPLETO (24 horas com medição). Dia com buraco não entra: somar só as horas
-- medidas subestimaria a chuva, e 38% das horas do INMET vêm vazias. Sem ponderação por área nem por distância.
-- `estacoes_na_bacia` conta as estações da bacia com algum dado no dia; `estacoes_validas`, as que entraram na média.
-- Quando nenhuma estação da bacia teve o dia completo, a média é NULL (e não zero). Estação sem bacia não entra.
SELECT
  bacia,
  bacia_chave,
  data_referencia,
  COUNT(*) AS estacoes_na_bacia,
  COUNTIF(horas_com_medicao = 24) AS estacoes_validas,
  AVG(IF(horas_com_medicao = 24, precipitacao_mm_dia, NULL)) AS precipitacao_mm_dia_media,
  MAX(IF(horas_com_medicao = 24, precipitacao_mm_dia, NULL)) AS precipitacao_mm_dia_maxima
FROM ${ref("gold", "precipitacao_diaria_estacao")}
WHERE bacia IS NOT NULL
GROUP BY bacia, bacia_chave, data_referencia
```

- [ ] **Passo 4:** `uv run pytest tests/unit/test_sql.py -q` → PASS.

- [ ] **Passo 5: catálogo e conferência**
  - `scripts/anotar_catalogo.py`: junto às entradas de meteorologia, `"precipitacao_diaria_bacia": {"dominio": "meteorologia", "responsavel": INTELIGENCIA},`.
  - `scripts/conferir_cargas.py`: leia como `precipitacao_diaria_estacao` entra hoje na lista de Gold e acrescente `precipitacao_diaria_bacia` com **linhas**, **bacias distintas** e **`COUNTIF(estacoes_validas = 0)`** (dias de bacia sem nenhuma estação completa). `tests/unit/test_conferir_cargas.py`: o teste que confere que todo nome de Gold citado existe em `definitions/` já cobre o nome novo; acrescente uma asserção de que a consulta nova começa por `SELECT` e cita `precipitacao_diaria_bacia`.

- [ ] **Passo 6: documentação**
  - `docs/dicionario-dados/inmet_precipitacao.md`: nova seção "Chuva por bacia (`precipitacao_diaria_bacia`)" com a tabela de campos, a **regra provisória** e por quê, e o limite (cobre só as estações que caem num contorno do ONS: 61% em 03/10/2026).
  - `docs/arquitetura/decisoes/026-precipitacao-por-bacia.md`: uma frase datada de 03/10/2026: "a ness. entregou, como regra provisória, a média simples dos dias completos de estação em `precipitacao_diaria_bacia`; a Alup pode trocá-la."
  - `docs/arquitetura/dominios-analiticos.md`: a Gold nova na lista do domínio Meteorologia.

- [ ] **Passo 7:** `uv run pytest tests -q` (o teste de catálogo exige toda Gold documentada e anotada) e `uv run ruff check src tests scripts`.

- [ ] **Passo 8: commit**
```bash
git add definitions/gold/precipitacao_diaria_bacia.sqlx tests/unit/test_sql.py scripts/conferir_cargas.py tests/unit/test_conferir_cargas.py scripts/anotar_catalogo.py docs/dicionario-dados/inmet_precipitacao.md docs/arquitetura/dominios-analiticos.md docs/arquitetura/decisoes/026-precipitacao-por-bacia.md
git commit -m "feat(inmet): chuva diária média por bacia, com a regra provisória declarada"
```

---

### Tarefa 3: Bacia mais próxima das estações sem bacia (item 3)

**Regra (decisão deste plano):** só para a estação **sem** bacia exata, calcula-se a bacia **mais próxima** (menor `ST_DISTANCE` entre o ponto e o contorno) e a **distância em km**. É aproximação, **sem limite de distância**: quem usa filtra pela distância. Estação com bacia exata fica com as três colunas nulas. A coluna `bacia` (exata) **não muda**, e a Tarefa 2 **não usa** a bacia mais próxima.

**Files:**
- Modify: `definitions/gold/precipitacao_diaria_estacao.sqlx`, `tests/unit/test_sql.py`, `scripts/conferir_cargas.py`, `tests/unit/test_conferir_cargas.py`, `docs/dicionario-dados/inmet_precipitacao.md`

**Interfaces:**
- Produces: três colunas novas em `gold.precipitacao_diaria_estacao`: `bacia_proxima STRING`, `bacia_proxima_chave STRING`, `distancia_bacia_km FLOAT64`. As colunas existentes e o `LEFT JOIN` ficam como estão.

- [ ] **Passo 1: testes de SQL (falham)**
```python
def test_bacia_proxima_so_para_estacao_sem_bacia_exata() -> None:
    sql = _gold("precipitacao_diaria_estacao")
    assert "ST_DISTANCE(" in sql
    assert "IF(b.bacia IS NULL, p2.bacia_proxima, NULL) AS bacia_proxima" in sql
    assert "IF(b.bacia IS NULL, p2.distancia_km, NULL) AS distancia_bacia_km" in sql


def test_bacia_proxima_nao_substitui_a_bacia_exata() -> None:
    sql = _gold("precipitacao_diaria_estacao")
    assert "ST_COVERS(" in sql  # a bacia exata continua pelo ponto em polígono
    assert "b.bacia," in sql


def test_bacia_proxima_roda_por_estacao_e_nao_por_dia() -> None:
    sql = _gold("precipitacao_diaria_estacao")
    assert "estacao_proxima AS (" in sql
    assert "FROM estacao_ponto" in sql
```
(O arquivo de teste reaproveita `_gold` da Tarefa 2.)

- [ ] **Passo 2:** `uv run pytest tests/unit/test_sql.py -q -k bacia_proxima` → FAIL.

- [ ] **Passo 3: o SQL.** Em `precipitacao_diaria_estacao.sqlx`, depois do CTE `estacao_bacia` e antes do `SELECT` final, acrescente (a vírgula entre CTEs fica a cargo de quem edita; confira a sintaxe):
```sql
,

-- Bacia mais próxima, só para a estação sem bacia exata (~255 de 653 em 03/10/2026): roda por estação, não por dia.
-- É aproximação, sem limite de distância; quem usa filtra por `distancia_bacia_km`.
estacao_proxima AS (
  SELECT
    e.estacao,
    ARRAY_AGG(
      STRUCT(c.nome_bacia AS bacia_proxima, c.bacia_chave AS bacia_proxima_chave,
             ST_DISTANCE(c.contorno, e.ponto) / 1000 AS distancia_km)
      ORDER BY ST_DISTANCE(c.contorno, e.ponto) ASC, c.nome_bacia ASC
      LIMIT 1
    )[SAFE_OFFSET(0)] AS p
  FROM estacao_ponto AS e
  CROSS JOIN contorno_vigente AS c
  WHERE e.estacao NOT IN (SELECT estacao FROM estacao_bacia WHERE bacia IS NOT NULL)
  GROUP BY e.estacao
),

estacao_proxima_plana AS (
  SELECT estacao, p.bacia_proxima, p.bacia_proxima_chave, ROUND(p.distancia_km, 1) AS distancia_km
  FROM estacao_proxima
)
```
No `SELECT` final, depois de `b.bacia_chave,`:
```sql
  IF(b.bacia IS NULL, p2.bacia_proxima, NULL) AS bacia_proxima,
  IF(b.bacia IS NULL, p2.bacia_proxima_chave, NULL) AS bacia_proxima_chave,
  IF(b.bacia IS NULL, p2.distancia_km, NULL) AS distancia_bacia_km,
```
e, depois do `LEFT JOIN estacao_bacia AS b ...`:
```sql
LEFT JOIN estacao_proxima_plana AS p2 ON p2.estacao = p.estacao
```
e o `GROUP BY` ganha `p2.bacia_proxima, p2.bacia_proxima_chave, p2.distancia_km`. Se o teste do Passo 1 usar `p2.` com outro alias, ajuste o **teste e o SQL juntos**. Atualize o comentário do cabeçalho da Gold com um parágrafo sobre as três colunas.

- [ ] **Passo 4:** `uv run pytest tests/unit/test_sql.py -q` → PASS.

- [ ] **Passo 5: conferência.** Em `scripts/conferir_cargas.py`, na consulta da Gold `precipitacao_diaria_estacao`, acrescente: estações com `bacia_proxima` (`COUNT(DISTINCT IF(bacia_proxima IS NOT NULL, estacao, NULL))`), a distância máxima (`MAX(distancia_bacia_km)`) e a mediana (`APPROX_QUANTILES(distancia_bacia_km, 2)[OFFSET(1)]`). Teste: a consulta continua começando por `SELECT`/`WITH`, não contém `;` e cita `bacia_proxima`.

- [ ] **Passo 6: documentação** em `inmet_precipitacao.md`: as três colunas, a regra, "aproximação sem limite de distância", e o aviso de que a chuva por bacia (`precipitacao_diaria_bacia`) **não** usa a bacia mais próxima.

- [ ] **Passo 7:** suíte, ruff, commit:
```bash
git add definitions/gold/precipitacao_diaria_estacao.sqlx tests/unit/test_sql.py scripts/conferir_cargas.py tests/unit/test_conferir_cargas.py docs/dicionario-dados/inmet_precipitacao.md
git commit -m "feat(inmet): bacia mais próxima e distância para as estações sem bacia exata"
```

---

### Tarefa 4: Fonte de previsão de 7 dias (item 4; **condicional ao ADR 029**)

**Esta tarefa só começa depois da Tarefa 1b.** Ela tem **um** ramo por execução, escolhido pela decisão do ADR 029. O formato da resposta (XML do CPTEC ou JSON do INMET) **ainda não foi visto** por quem escreveu este plano; por isso o primeiro passo de cada ramo é capturar a resposta real, e o código e os testes se escrevem **a partir da amostra capturada**, nunca de memória.

**Interface comum (qualquer ramo):**
- Conector registrado, fonte `<fonte>` e entidade `previsao`, que devolve **uma linha por cidade e por dia de previsão**, com: `cidade_codigo: str`, `cidade_nome: str`, `uf: str`, `data_previsao: date` (o dia previsto), `data_emissao: date` (o dia em que a previsão foi emitida, que vale como `data_referencia`), `temperatura_maxima_c: Decimal | None`, `temperatura_minima_c: Decimal | None`, `precipitacao_mm: Decimal | None` (ou `probabilidade_chuva_pct: int | None` se a fonte só tem isso), `condicao: str | None`, e um campo `bruto` descartável.
- **Cidades:** as 27 capitais (nome e UF em constante no código). Código da cidade resolvido na própria fonte, falhando alto se for ambíguo.
- **Retrato por emissão:** a previsão é lida todo dia; a Silver deduplica por `(cidade_codigo, data_previsao, data_emissao)`. A Gold `previsao_vigente` traz, por cidade e dia previsto, **a emissão mais recente**.
- Agendamento diário, silêncio de 26 h nos dois mapas, domínio Meteorologia, dicionário com linhagem, os 7 componentes.

#### Ramo 4A — o CPTEC responde de dentro do GCP

- [ ] **A1:** capture a resposta real: `uv run python` com `criar_sessao()` e as duas URLs da sonda `cptec` (**só funcionará de dentro do GCP**: a resposta capturada vem do log do workflow `Sondar rede`, que o ADR 029 cita). Salve um trecho curto em `tests/fixtures/cptec_listacidades.xml` e `cptec_previsao_7dias.xml`.
- [ ] **A2:** escreva os testes (RED) contra essas fixtures: parsing de cidade e de cada dia, `maxima`/`minima` como número, ausência vira `None`, resposta sem `<previsao>` ou HTML de erro **falha alto** (`LayoutInesperadoError`), cidade ambígua falha alto, dia fora dos 7 esperados é aviso.
- [ ] **A3:** implemente `src/conectores/cptec_previsao.py` (use `ace_prc.py` e `inmet_precipitacao.py` como molde: sessão por `criar_sessao`, parser da biblioteca padrão `xml.etree.ElementTree` com `defusedxml` **só se já for dependência**; caso contrário, o parser padrão com a entrada limitada a 1 MB). Camadas, agendamento, silêncio, dicionário, catálogo, custo.
- [ ] **A4:** o dicionário registra: a sonda de dentro do GCP, o que o endpoint devolve, e que o webservice é o legado do CPTEC.

#### Ramo 4B — CPTEC bloqueado, INMET previsão responde (substituição, depende de aceite)

- [ ] **B1:** capture a resposta real da sonda `inmet_previsao` (log do workflow) em `tests/fixtures/inmet_previsao_3550308.json`; confirme que traz **pelo menos 7 dias** e quais campos (temperatura, precipitação ou probabilidade, condição). Se trouxer menos de 7 dias, **pare e registre no ADR 029** (decisão C).
- [ ] **B2:** testes (RED) contra a fixture, como em A2, e `LayoutInesperadoError` se a chave do código IBGE sumir.
- [ ] **B3:** implemente `src/conectores/inmet_previsao.py` (fonte `inmet`, entidade `previsao`) com os códigos IBGE das 27 capitais em constante (cada código com teste que confere nome e UF contra a resposta real), camadas, agendamento, silêncio, dicionário, catálogo, custo.
- [ ] **B4:** o dicionário e o ADR 029 dizem, em destaque: **"alternativa ao CPTEC, aguardando aceite da Alup por escrito (cláusula 4ª)"**. O painel **não** marca o CPTEC como feito.

#### Ramo 4C — nenhuma fonte serve

- [ ] **C1:** nada a construir. O ADR 029 já registra a decisão; atualize a tabela de gaps do relatório de fechamento com o resultado.

---

### Tarefa 5: Fechamento dos itens 1 a 4

**Files:** Modify: `docs/relatorios/2026-10-03-fechamento-onda-1.md`, `docs/plano-execucao.md` §3.2, `docs/status.md`, `painel/marcos.toml` (títulos)

- [ ] **Passo 1:** depois do deploy de `hml` e `dev` e das cargas, rode `gh workflow run "Conferir cargas" -f environment=hml` e `-f environment=dev`, e registre no relatório, **com o run e a data**, as contagens de `precipitacao_diaria_bacia` (linhas, bacias, dias sem estação completa) e de `precipitacao_diaria_estacao` (estações com bacia próxima, distância máxima e mediana). Só vira `conferido` o que a saída traz.
- [ ] **Passo 2:** o relatório, o plano e o status refletem o resultado do ADR 029 (ramo A, B ou C) e o painel **não** muda o estado da Onda 1 nem marca nada como `feito` sem conferência.
- [ ] **Passo 3:** `uv run pytest tests -q` (inclui painel), ruff, commit `docs: fechamento dos itens 1 a 4 da Onda 1`.

---

## Autoavaliação

**Cobertura:** item 1 = Tarefas 1 e 1b; item 2 = Tarefa 2; item 3 = Tarefa 3; item 4 = Tarefa 4 (ramos A, B, C) e a decisão que a escolhe é a Tarefa 1b; o fechamento = Tarefa 5.

**Placeholders:** as Tarefas 1, 2 e 3 trazem código e testes completos. A Tarefa 4 **não** traz código de parser: ninguém viu a resposta real do CPTEC nem a do INMET previsão, e escrever o parser de memória seria inventar o contrato de dados. Isso não é "TBD": o primeiro passo de cada ramo é capturar a amostra, e os critérios de teste estão escritos. A execução do ramo é decidida por regra objetiva (Tarefa 1b, Passo 2).

**Consistência de tipos:** `ResultadoSonda` (Tarefa 1) tem os mesmos campos que o CLI imprime; a Gold da Tarefa 2 consome `horas_com_medicao` e `bacia_chave` que a Gold existente já expõe; a Tarefa 3 mantém `bacia`, `bacia_chave` e as colunas existentes, e a Tarefa 2 lê só estas.

**Riscos que o plano assume e declara:** a regra de média por bacia é **provisória** (a Alup pode trocá-la); o SQL espacial só se valida no Dataform (o BigQuery já aceitou `ST_COVERS` e `make_valid` em 03/10/2026, mas `ST_DISTANCE` e o `CROSS JOIN` ainda não rodaram); a sonda depende de o job `ingestao-bcb-cambio-ptax` existir no ambiente; a substituição do CPTEC depende de aceite que nenhum código dá.

## Estimativa de esforço (não é medição)

| Tarefa | Horas |
|---|---:|
| 1 Sonda e workflow | 2 |
| 1b ADR 029 | 1 |
| 2 Chuva por bacia | 2 |
| 3 Bacia mais próxima | 2 |
| 4 Previsão (um ramo) | 4 a 8 |
| 5 Fechamento | 1 |
| **Total** | **12 a 16** |
