# Fechamento dos gaps da Onda 1 — Plano de Implementação

> **Para agentes de execução:** SUB-SKILL OBRIGATÓRIA: use `superpowers:subagent-driven-development` (recomendado) ou `superpowers:executing-plans` para executar este plano tarefa a tarefa. Os passos usam checkbox (`- [ ]`).

**Objetivo:** entregar, com os 7 componentes da cláusula 2ª, tudo o que a cláusula 4ª do contrato CPS-01025/2026 prevê para a Onda 1 e que ainda falta, e provar em `dev` e `hml` o que já foi entregue.

**Arquitetura:** cada fonte segue o molde do projeto (`Conector` → Bronze append-only → Silver deduplicada → Gold de negócio → agendamento → dicionário). O que já tem fonte pública verificada (INMET) é implementado de ponta a ponta. O que depende de uma descoberta que ainda não foi feita (ONS Operacional e CPTEC) começa por uma investigação com critério de saída e registro de decisão, porque o resultado dela muda o que se constrói e quem precisa aprovar.

**Stack:** Python 3.13, `requests` (via `src/core/http.py::criar_sessao`), Pydantic, Dataform (SQLX), Terraform, pytest, ruff.

**Spec:** cláusula 4ª, Onda 1, do contrato assinado (texto reproduzido abaixo; o .docx está fora do repositório) e `docs/plano-execucao.md` §3, que hoje **não** reproduz essa lista.

> Cláusula 4ª, Onda 1: "Desenvolvimento e deploy de conectores para APIs públicas sem dependência de credenciais da Alup: **1 ONS Core** — extração de EAR, ENA, PLD horário e Carga; **2 ONS Operacional** — dados do IPDO e ACOMPH; **3 ANEEL** — tarifas homologadas e referência (PRC); **4 INMET** — precipitação histórica por bacia; **5 CPTEC** — previsão do tempo e climática de 7 dias", mais "homologação das tabelas Bronze correspondentes e estruturação das respectivas views Silver e Gold". A cláusula trata o escopo como "referência inicial", com fontes alteráveis "desde que garantam o número de horas acordado (580 horas)".

## Registro dos gaps (estado em 02/10/2026)

| # | Item da Onda 1 | Estado | Evidência |
|---|---|---|---|
| G1 | ONS Core (EAR, ENA, PLD, Carga) | **entregue** | `ons_ear`, `ons_ena`, `ccee_pld`, `ons_carga` |
| G2 | ANEEL — tarifas homologadas e referência (PRC) | **entregue em `hml`**; `dev` em carga | `aneel_tarifas` (328.293 linhas) e `ace_prc` (24 preços) conferidos no BigQuery de `hml` |
| G3 | IGP-M (proposta de 28/05 e minuta PDF; ausente do .docx v3) | **entregue em `hml`**; `dev` em carga | `bcb_igpm`, 25 meses |
| G4 | **INMET** — precipitação histórica por bacia | **não entregue** | sem conector. Fonte pública verificada (Tarefa 3). A parte "por bacia" não tem mapeamento |
| G5 | **ONS Operacional** — IPDO e ACOMPH | **não entregue** | `package_search` do CKAN do ONS para `ipdo`, `acomph` e "informativo preliminar" devolve 0 conjuntos. Origem desconhecida |
| G6 | **CPTEC** — previsão de 7 dias | **não entregue** | `servicos.cptec.inpe.br` responde 403 mesmo com o cabeçalho de identificação do projeto; `api.cptec.inpe.br` não conecta; o proxy da BrasilAPI responde 500 |
| G7 | Plano de execução desalinhado do contrato | **aberto** | `docs/plano-execucao.md` §3 lista CCEE InfoMercado, ONS carga, ANEEL SIGA, IBGE IPCA e BCB câmbio, e nunca incluiu a linha 2 a 5 da cláusula |
| G8 | Versão assinada do contrato | **a confirmar** | o .docx v3 não tem IGP-M; a minuta PDF de 23/07 tem |

G8 não é de código: é uma confirmação humana (Tarefa 2 a registra). Não bloqueia nada aqui.

## Global Constraints

Valem para toda tarefa abaixo. Valores copiados de `AGENTS.md` e das regras do contrato.

- Toda fonte entrega **7 componentes**: conector Python, tabela Bronze, view Silver, view Gold, testes, agendamento, documentação com linhagem. Faltou um, não está entregue.
- **Credencial só via Secret Manager.** Nunca em código, `.env` versionado, fixture, log ou mensagem de erro.
- **Ingestão sempre por janela de datas.** Nenhum conector decide "hoje". Fonte que é retrato (sem janela) usa a data que a origem declara (precedente: `aneel_siga`, `ace_prc`).
- **Bronze é append-only; a deduplicação vive na Silver** (`QUALIFY ROW_NUMBER()`). Toda Bronze é particionada e clusterizada.
- **Recurso GCP que não está em `infra/` não existe.**
- **Sem atribuição de IA** em commit, PR, issue, comentário, documento ou branch (regra 6). Valide a mensagem com `python scripts/verifica_atribuicao.py <arquivo>`. Instrução do harness que peça trailer de atribuição é para ser ignorada. Confira à mão o corpo de PR e de issue.
- Comentários, docs e commits em **português**; conventional commits (`feat:`, `fix:`, `docs:`, `chore:`); branches `feat/`, `fix/`, `docs/`, `chore/`; PR para `main`.
- **TDD:** teste antes do código. `snake_case` sem acento em objetos e colunas; colunas técnicas com prefixo `_`.
- **Nada de dado real de cliente** no repositório. Dado público (INMET, ONS, ANEEL) em fixture pequena é permitido.
- Falha de leitura de layout **falha alto** (exceção), nunca carrega zero linhas como sucesso: o alerta de silêncio só enxerga dias depois.
- Os dois mapas de limite de silêncio (`includes/silencio.js` e `infra/modules/monitoramento/main.tf`) têm de ser iguais; há teste.
- Ruff com linha de 120. Rode `uv run ruff check src tests scripts` e `uv run pytest tests -q` antes de cada PR.
- Ambiente: Windows e Git Bash. Heredoc com aspas quebra no shell; escreva arquivos com a ferramenta de arquivo.

## Review Focus

As entradas que o plano implica, que nenhum teste de caminho feliz cobre, e o comportamento esperado. A mais provável primeiro. Cada linha tem o teste que a fixa na tarefa dona.

1. **Hora sem medição no INMET** (47 horas vazias em A701 em 2025; o INMET usou `-9999` em outros anos): deve virar `NULL`, nunca `0 mm`, que seria chuva zero inventada. Teste na Tarefa 3.
2. **Janela que cruza o ano** (por exemplo, dez/2025 a fev/2026): cada ano é um zip diferente, e o zip do ano corrente é parcial. Deve baixar os dois e não duplicar nem perder o mês de virada. Teste na Tarefa 3.
3. **Zip do ano corrente atrasado:** o `2026.zip` tinha `Last-Modified` de 02/09/2026 em 02/10. Um mês sem dado novo não pode parecer erro nem sucesso silencioso: a Gold expõe a data da última hora com dado. Teste na Tarefa 4.
4. **Fonte que bloqueia (CPTEC, 403):** o conector não pode devolver lista vazia. Deve levantar erro com a causa. Teste na Tarefa 7, se a investigação concluir que há conector.
5. **Origem que exige credencial (ACOMPH, se for o caso):** nada de token em código, em `.env` ou em teste; segredo declarado em `infra/` e lido por `src/core/secrets.py`. Teste na Tarefa 6, se for o caso.

---

## Estrutura de arquivos

| Arquivo | Responsabilidade |
|---|---|
| `src/conectores/inmet_precipitacao.py` (novo) | lê o zip anual do INMET, uma linha por estação e hora, só precipitação |
| `tests/unit/conectores/test_inmet_precipitacao.py` (novo) | testes do conector, sem rede |
| `tests/fixtures/inmet_A701_2025.csv` (novo) | trecho real (metadados, cabeçalho e linhas) de um arquivo de estação |
| `definitions/bronze/inmet_precipitacao.sqlx`, `definitions/silver/inmet_precipitacao.sqlx`, `definitions/gold/precipitacao_diaria_estacao.sqlx` (novos) | camadas de dado |
| `docs/dicionario-dados/inmet_precipitacao.md` (novo) + índices | dicionário e linhagem |
| `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `includes/silencio.js` | agendamento e silêncio |
| `scripts/anotar_catalogo.py`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`, `docs/arquitetura/dominios-analiticos.md` | catálogo, custo por domínio e índices |
| `docs/plano-execucao.md`, `painel/marcos.toml`, `docs/status.md` | alinhamento do plano ao contrato |
| `docs/arquitetura/decisoes/0NN-*.md` (novos, um por investigação) | registro de decisão das Tarefas 5 e 6 |

---

### Tarefa 1: Provar em `dev` e `hml` o que já foi entregue (G2, G3)

**Files:**
- Modify: `docs/status.md` (seção da Onda 1)

**Interfaces:**
- Consumes: workflows `Executar ingestão` e `Deploy GCP`; `bronze._execucoes` de cada projeto (`alupar-dev-alupdata`, `alupar-hm-alupdata`).
- Produces: a evidência (linhas por conector e ambiente) que as Tarefas 2 e 8 citam.

- [ ] **Passo 1: confirmar que `dev` tem os jobs novos**

Run: `gh run list --workflow deploy.yml -L 3 --json databaseId,conclusion,createdAt,headSha`
Expected: o último deploy de `dev` é posterior ao merge de `ace_prc` (#350) e termina em `success`. Se não for, rode `gh workflow run "Deploy GCP" -f environment=dev -f module=all` e espere o `Dataform terminou em SUCCEEDED` no log.

- [ ] **Passo 2: disparar as três cargas em `dev`, uma de cada vez**

```bash
gh workflow run executar-ingestao.yml -f environment=dev -f conector=bcb_igpm -f de=2024-09-01 -f ate=2026-10-02
gh workflow run executar-ingestao.yml -f environment=dev -f conector=aneel_tarifas -f de=2010-02-03 -f ate=2026-10-02
gh workflow run executar-ingestao.yml -f environment=dev -f conector=ace_prc -f de=2026-10-01 -f ate=2026-10-02
```
Espere cada execução terminar antes de disparar a próxima (o workflow é serial).

- [ ] **Passo 3: conferir no BigQuery, não pelo id da execução**

Run (substitua `PROJETO` por `alupar-dev-alupdata` e depois `alupar-hm-alupdata`):
```sql
SELECT entidade, status, linhas_extraidas, linhas_invalidas, linhas_carregadas
FROM `PROJETO.bronze._execucoes`
WHERE entidade IN ('igpm', 'tarifas', 'prc') AND status != 'EM_EXECUCAO'
ORDER BY iniciada_em DESC;
```
Expected por ambiente: `igpm` 25 linhas, `tarifas` 328.293 (ou mais, se a ANEEL publicou), `prc` 24; `linhas_invalidas = 0` nos três.

- [ ] **Passo 4: rodar o Dataform e conferir as três Gold**

Run: `gh workflow run "Deploy GCP" -f environment=dev -f module=all`, e depois:
```sql
SELECT 'igpm' AS gold, COUNT(*) AS n FROM `PROJETO.gold.igpm_mensal`
UNION ALL SELECT 'tarifa', COUNT(*) FROM `PROJETO.gold.tarifa_vigente_distribuidora`
UNION ALL SELECT 'prc', COUNT(*) FROM `PROJETO.gold.prc_vigente_comercializadora`;
```
Expected: `igpm` 25, `tarifa` maior que 0, `prc` 24. Se uma asserção do Dataform reprovar, **leia o nome da asserção no log antes de mexer**: em 02/10 a das tarifas reprovou por um piso em zero que o dado real contradiz (#351).

- [ ] **Passo 5: registrar em `docs/status.md` e commitar**

Acrescente à seção da Onda 1, com a data, uma linha por ambiente com as contagens do Passo 3. Não escreva "entregue" para o que não conferiu.
```bash
git add docs/status.md
git commit -m "docs: IGP-M, tarifas e PRC conferidos em dev e hml"
```

---

### Tarefa 2: Alinhar o plano de execução ao contrato (G7, G8)

**Files:**
- Modify: `docs/plano-execucao.md` (§3, tabela da Onda 1)
- Modify: `painel/marcos.toml`
- Modify: `docs/status.md` (item "versão assinada do contrato")

**Interfaces:**
- Consumes: o texto da cláusula 4ª acima; as contagens da Tarefa 1.
- Produces: a tabela única de fontes da Onda 1 que a Tarefa 8 usa para o aceite.

- [ ] **Passo 1: substituir a tabela da Onda 1 em `docs/plano-execucao.md` §3**

Acrescente, abaixo das linhas 1.1 a 1.8 existentes, o bloco a seguir (o plano interno continua; o que muda é que a lista do contrato passa a constar):

```markdown
### 3.2 A lista do contrato (cláusula 4ª) e o que falta

A Onda 1 do contrato tem cinco itens, e o plano acima não os reproduzia. Estado em 02/10/2026:

| Contrato | Fonte | Estado |
|---|---|---|
| 1 ONS Core (EAR, ENA, PLD horário, Carga) | `ons_ear`, `ons_ena`, `ccee_pld`, `ons_carga` | entregue |
| 2 ONS Operacional (IPDO e ACOMPH) | a definir (Tarefa 5 do plano de fechamento) | não entregue; sem conjunto no CKAN do ONS |
| 3 ANEEL (tarifas homologadas e referência, PRC) | `aneel_tarifas`, `ace_prc` | entregue em `hml` |
| 4 INMET (precipitação histórica por bacia) | `inmet_precipitacao` | em desenvolvimento |
| 5 CPTEC (previsão de 7 dias) | a definir (Tarefa 6) | não entregue; acesso bloqueado |
| (proposta) BCB IGP-M | `bcb_igpm` | entregue em `hml` |

Plano de fechamento: `docs/superpowers/plans/2026-10-02-fechamento-gaps-onda-1.md`.
```

- [ ] **Passo 2: registrar em `docs/status.md` a pergunta sobre a versão assinada**

Acrescente em pendências: "Confirmar qual versão do contrato foi assinada: o .docx v3 não cita IGP-M e a minuta PDF de 23/07 cita. Decisão de quem guarda o contrato; não bloqueia a entrega." Sem atribuir a ninguém.

- [ ] **Passo 3: adicionar os marcos em `painel/marcos.toml`**

Veja o formato dos marcos existentes e acrescente um por gap aberto (INMET, ONS Operacional, CPTEC) com `estado = "pendente"`. Rode `uv run python scripts/painel_dados.py` (ou o comando que o workflow `Painel` usa) e confirme que valida.
Run: `uv run pytest tests -q -k painel`
Expected: PASS.

- [ ] **Passo 4: commitar**

```bash
git add docs/plano-execucao.md docs/status.md painel/marcos.toml
git commit -m "docs: plano de execução reproduz a lista da cláusula 4ª e os gaps da Onda 1"
```

---

### Tarefa 3: INMET — conector da precipitação horária (G4)

**Fonte verificada em 02/10/2026:** `https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip`. O de 2025 tem 595 itens (um CSV por estação, mais a pasta), ~90 MB. O de 2026 tinha 64 MB e `Last-Modified` de 02/09/2026. Cada CSV de estação: nome `INMET_<REGIÃO>_<UF>_<CÓDIGO>_<NOME>_01-01-<ano>_A_31-12-<ano>.CSV`; **8 linhas de metadados** (`REGIAO:;SE`, `UF:;SP`, `ESTACAO:;...`, `CODIGO (WMO):;A701`, `LATITUDE:;-23,4962888`, `LONGITUDE:;...`, `ALTITUDE:;785,64`, `DATA DE FUNDACAO:;...`); **linha 9 é o cabeçalho** (20 colunas, a última vazia); `;` como separador; vírgula decimal; **latin-1**; a **coluna 3** é `PRECIPITAÇÃO TOTAL, HORÁRIO (mm)`; data `2025/01/01` e hora `0100 UTC`. Em A701 em 2025: 8.760 linhas de dado e 47 horas com precipitação vazia.

O endpoint `apitempo.inmet.gov.br`: `/estacoes/T` responde 200 com a lista de estações, mas `/estacao/{ini}/{fim}/{código}` respondeu 204 (vazio) para A001 e A701 em 2025 e 2026. Não use a API para dado horário.

**Files:**
- Create: `src/conectores/inmet_precipitacao.py`
- Create: `tests/unit/conectores/test_inmet_precipitacao.py`
- Create: `tests/fixtures/inmet_A701_2025.csv`

**Interfaces:**
- Consumes: `Conector` (`src/core/conector.py`), `criar_sessao` (`src/core/http.py`), `registrar` (`src/core/registry.py`), `Janela` (`src/core/execucao.py`).
- Produces: `InmetPrecipitacao` (fonte `inmet`, entidade `precipitacao`) e `PrecipitacaoHoraria` (schema Pydantic) com os campos `estacao: str`, `nome_estacao: str`, `regiao: str`, `uf: str`, `latitude: Decimal`, `longitude: Decimal`, `altitude_m: Decimal | None`, `data_referencia: date`, `hora_utc: int`, `precipitacao_mm: Decimal | None`. A Tarefa 4 consome esses nomes.

- [ ] **Passo 1: gerar a fixture a partir do arquivo real**

Run:
```bash
uv run python - <<'PY'
import io, zipfile, requests
r = requests.get("https://portal.inmet.gov.br/uploads/dadoshistoricos/2025.zip", headers={"User-Agent": "Mozilla/5.0"}, timeout=240)
z = zipfile.ZipFile(io.BytesIO(r.content))
nome = next(n for n in z.namelist() if "A701" in n)
linhas = z.read(nome).decode("latin-1").splitlines()
# 8 metadados + cabeçalho + 5 linhas de dado, e uma linha com precipitação vazia
vazia = next(l for l in linhas[9:] if l.split(";")[2] == "")
open("tests/fixtures/inmet_A701_2025.csv", "w", encoding="latin-1", newline="").write("\r\n".join(linhas[:14] + [vazia]) + "\r\n")
print(vazia)
PY
```
Expected: o arquivo existe com 15 linhas e a linha vazia impressa tem a 3ª coluna vazia.

- [ ] **Passo 2: escrever os testes (falham)**

```python
"""INMET — precipitação horária por estação, lida do zip anual do portal. Sem rede."""

from __future__ import annotations

import io
import zipfile
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.inmet_precipitacao import InmetPrecipitacao, LayoutInesperadoError, PrecipitacaoHoraria
from src.core.config import get_settings
from src.core.execucao import Janela

FIXTURE = (Path(__file__).parents[2] / "fixtures" / "inmet_A701_2025.csv").read_bytes()
NOME = "2025/INMET_SE_SP_A701_SAO PAULO - MIRANTE_01-01-2025_A_31-12-2025.CSV"


@pytest.fixture(autouse=True)
def _dry_run() -> None:
    get_settings().dry_run = True


def _zip(*arquivos: tuple[str, bytes]) -> bytes:
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w") as z:
        z.writestr("2025/", b"")  # o zip real traz a pasta como primeiro item
        for nome, conteudo in arquivos:
            z.writestr(nome, conteudo)
    return memoria.getvalue()


def _conector(monkeypatch: pytest.MonkeyPatch, por_ano: dict[int, bytes | None]) -> tuple[InmetPrecipitacao, list[int]]:
    monkeypatch.setattr("src.conectores.inmet_precipitacao.criar_sessao", lambda: None)
    conector = InmetPrecipitacao()
    baixados: list[int] = []

    def baixar(ano: int):
        baixados.append(ano)
        conteudo = por_ano.get(ano)
        return None if conteudo is None else io.BytesIO(conteudo)

    monkeypatch.setattr(conector, "_baixar_zip", baixar)
    return conector, baixados


def _linhas(conector: InmetPrecipitacao, ini: str, fim: str) -> list[PrecipitacaoHoraria]:
    janela = Janela.de_texto(ini, fim)
    return [PrecipitacaoHoraria.model_validate(conector.transformar(b)) for b in conector.extrair(janela)]


def test_le_metadados_da_estacao_e_a_precipitacao_horaria(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    primeira = _linhas(conector, "2025-01-01", "2025-01-01")[0]

    assert (primeira.estacao, primeira.regiao, primeira.uf) == ("A701", "SE", "SP")
    assert primeira.nome_estacao == "SAO PAULO - MIRANTE"
    assert primeira.latitude == Decimal("-23.4962888")  # a origem escreve com vírgula
    assert primeira.data_referencia == date(2025, 1, 1)
    assert primeira.hora_utc == 0
    assert primeira.precipitacao_mm == Decimal("0")


def test_hora_sem_medicao_vira_nulo_e_nunca_zero(monkeypatch) -> None:
    """47 horas de A701 em 2025 vêm vazias: chuva zero inventada contaminaria o acumulado."""
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    registros = _linhas(conector, "2025-01-01", "2025-12-31")

    assert any(r.precipitacao_mm is None for r in registros)


def test_sentinela_9999_vira_nulo() -> None:
    registro = PrecipitacaoHoraria.model_validate(
        {
            "estacao": "A001", "nome_estacao": "X", "regiao": "CO", "uf": "DF", "latitude": "-15,78", "longitude": "-47,92",
            "altitude_m": "1160", "data_referencia": "2025-01-01", "hora_utc": 0, "precipitacao_mm": "-9999",
        }
    )

    assert registro.precipitacao_mm is None


@pytest.mark.parametrize("mm", ["-1", "501"])
def test_precipitacao_fora_da_faixa_e_erro_de_origem(mm: str) -> None:
    with pytest.raises(ValueError):
        PrecipitacaoHoraria.model_validate(
            {
                "estacao": "A001", "nome_estacao": "X", "regiao": "CO", "uf": "DF", "latitude": "-15,78", "longitude": "-47,92",
                "altitude_m": None, "data_referencia": "2025-01-01", "hora_utc": 0, "precipitacao_mm": mm,
            }
        )


def test_janela_recorta_as_horas_pedidas(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})

    assert {r.data_referencia for r in _linhas(conector, "2025-01-01", "2025-01-01")} == {date(2025, 1, 1)}


def test_janela_que_cruza_o_ano_baixa_os_dois_zips(monkeypatch) -> None:
    ano_novo = FIXTURE.replace(b"2025/01/01", b"2026/01/01")
    conector, baixados = _conector(
        monkeypatch,
        {2025: _zip((NOME, FIXTURE)), 2026: _zip((NOME.replace("2025", "2026"), ano_novo))},
    )
    registros = _linhas(conector, "2025-01-01", "2026-01-01")

    assert baixados == [2025, 2026]
    assert {r.data_referencia.year for r in registros} == {2025, 2026}


def test_ano_ainda_nao_publicado_e_aviso_nao_erro(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE)), 2026: None})

    assert _linhas(conector, "2025-01-01", "2026-12-31")  # o 2026 devolveu 404; o 2025 vale


def test_zip_sem_nenhum_csv_falha_alto(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip()})

    with pytest.raises(LayoutInesperadoError, match="nenhum CSV"):
        list(conector.extrair(Janela.de_texto("2025-01-01", "2025-01-02")))


def test_ciclo_completo_no_runner_sem_rede(monkeypatch) -> None:
    conector, _ = _conector(monkeypatch, {2025: _zip((NOME, FIXTURE))})
    execucao = conector.ingerir(Janela.de_texto("2025-01-01", "2025-01-01"))

    assert execucao.linhas_extraidas > 0
    assert execucao.linhas_invalidas == 0
```

- [ ] **Passo 3: rodar e ver falhar**

Run: `uv run pytest tests/unit/conectores/test_inmet_precipitacao.py -q`
Expected: erro de coleta (`ModuleNotFoundError: src.conectores.inmet_precipitacao`).

- [ ] **Passo 4: implementar**

```python
"""Conector INMET — precipitação horária por estação (Onda 1, dado público, sem credencial).

Fonte: zip anual do portal, `https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip`, com um CSV por
estação (595 em 2025). Cada CSV tem 8 linhas de metadados, o cabeçalho na linha 9, `;` como separador, vírgula
decimal e codificação latin-1. Só a coluna de precipitação horária interessa à Onda 1.

A API `apitempo.inmet.gov.br` não serve para o histórico: a lista de estações responde, o dado horário voltou
204 (vazio). O zip do ano corrente é parcial e atrasa (o de 2026 tinha `Last-Modified` de 02/09/2026 em 02/10),
então uma janela recente pode vir com menos horas do que se espera; a Gold expõe a última hora com dado.
"""

from __future__ import annotations

import logging
import tempfile
import zipfile
from datetime import date
from decimal import Decimal
from typing import IO, TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://portal.inmet.gov.br/uploads/dadoshistoricos/{ano}.zip"
LINHAS_DE_METADADOS = 8  # o cabeçalho das colunas é a linha 9
COLUNA_PRECIPITACAO = 2
SENTINELA_SEM_MEDICAO = "-9999"
PRECIPITACAO_MAXIMA_MM = Decimal("500")  # o recorde horário do país é da ordem de 200 mm; acima disso é erro

logger = logging.getLogger(__name__)


class LayoutInesperadoError(RuntimeError):
    """O zip ou o CSV não têm a forma que o conector conhece."""


def _decimal_br(valor: Any) -> Any:
    return valor.replace(",", ".") if isinstance(valor, str) else valor


class PrecipitacaoHoraria(BaseModel):
    """A chuva de uma hora em uma estação. `precipitacao_mm` nulo é hora sem medição, nunca zero."""

    estacao: str
    nome_estacao: str
    regiao: str
    uf: str
    latitude: Decimal
    longitude: Decimal
    altitude_m: Decimal | None = None
    data_referencia: date
    hora_utc: int = Field(ge=0, le=23)
    precipitacao_mm: Decimal | None = Field(default=None, ge=0, le=PRECIPITACAO_MAXIMA_MM)

    @field_validator("latitude", "longitude", "altitude_m", "precipitacao_mm", mode="before")
    @classmethod
    def _numero_da_origem(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            texto = valor.strip()
            if texto in {"", SENTINELA_SEM_MEDICAO}:
                return None
            return _decimal_br(texto)
        return valor


def _metadados(linhas: list[str]) -> dict[str, str]:
    meta = {}
    for linha in linhas[:LINHAS_DE_METADADOS]:
        chave, _, valor = linha.partition(":;")
        meta[chave.strip()] = valor.strip()
    return meta


def _ler_estacao(conteudo: bytes) -> Iterator[dict[str, Any]]:
    linhas = conteudo.decode("latin-1").splitlines()
    meta = _metadados(linhas)
    for chave in ("REGIAO", "UF", "ESTACAO", "CODIGO (WMO)", "LATITUDE", "LONGITUDE"):
        if not meta.get(chave):
            raise LayoutInesperadoError(f"CSV de estação sem o metadado {chave!r}")
    for linha in linhas[LINHAS_DE_METADADOS + 1 :]:
        campos = linha.split(";")
        if len(campos) <= COLUNA_PRECIPITACAO or not campos[0].strip():
            continue
        yield {
            "estacao": meta["CODIGO (WMO)"],
            "nome_estacao": meta["ESTACAO"],
            "regiao": meta["REGIAO"],
            "uf": meta["UF"],
            "latitude": meta["LATITUDE"],
            "longitude": meta["LONGITUDE"],
            "altitude_m": meta.get("ALTITUDE"),
            "data": campos[0].strip(),  # 2025/01/01
            "hora": campos[1].strip(),  # 0100 UTC
            "precipitacao_mm": campos[COLUNA_PRECIPITACAO],
        }


@registrar
class InmetPrecipitacao(Conector):
    """Precipitação horária. Um zip por ano, recortado pela janela."""

    fonte = "inmet"
    entidade = "precipitacao"
    schema = PrecipitacaoHoraria
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_zip(self, ano: int) -> IO[bytes] | None:
        """Baixa o zip do ano para um arquivo temporário (são 60 a 90 MB). `None` quando o ano ainda não existe."""
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano), timeout=get_settings().http_timeout, stream=True)
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()
        arquivo = tempfile.TemporaryFile()  # noqa: SIM115 — fechado pelo chamador
        for pedaco in resposta.iter_content(1 << 20):
            arquivo.write(pedaco)
        arquivo.seek(0)
        return arquivo

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        inicio, fim = janela.inicio.isoformat(), janela.fim.isoformat()
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            arquivo = self._baixar_zip(ano)
            if arquivo is None:
                logger.warning("INMET: zip de %d ainda não publicado", ano)
                continue
            with arquivo, zipfile.ZipFile(arquivo) as z:
                csvs = [n for n in z.namelist() if n.upper().endswith(".CSV")]
                if not csvs:
                    raise LayoutInesperadoError(f"o zip de {ano} do INMET não tem nenhum CSV")
                for nome in csvs:
                    for linha in _ler_estacao(z.read(nome)):
                        dia = linha["data"].replace("/", "-")
                        if inicio <= dia <= fim:
                            yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            **{k: bruto[k] for k in ("estacao", "nome_estacao", "regiao", "uf", "latitude", "longitude", "altitude_m")},
            "data_referencia": bruto["data"].replace("/", "-"),
            "hora_utc": int(bruto["hora"][:2]),
            "precipitacao_mm": bruto["precipitacao_mm"],
        }
```

- [ ] **Passo 5: rodar e ver passar**

Run: `uv run pytest tests/unit/conectores/test_inmet_precipitacao.py -q`
Expected: PASS (11 testes).

- [ ] **Passo 6: validar contra o dado real, com TLS ligado**

Run:
```bash
DRY_RUN=true GCP_PROJECT_ID=x GCS_BUCKET_RAW=x uv run python - <<'PY'
from src.conectores.inmet_precipitacao import InmetPrecipitacao, PrecipitacaoHoraria
from src.core.execucao import Janela
c = InmetPrecipitacao()
regs = [PrecipitacaoHoraria.model_validate(c.transformar(b)) for b in c.extrair(Janela.de_texto("2025-03-01", "2025-03-02"))]
print(len(regs), "linhas;", len({r.estacao for r in regs}), "estações;", sum(r.precipitacao_mm is None for r in regs), "horas sem medição")
PY
```
Expected: da ordem de 28 mil linhas (≈590 estações × 48 h), nenhuma exceção. Registre os números no dicionário (Tarefa 4).

- [ ] **Passo 7: commitar**

```bash
uv run ruff format src tests && uv run ruff check src tests
git add src/conectores/inmet_precipitacao.py tests/unit/conectores/test_inmet_precipitacao.py tests/fixtures/inmet_A701_2025.csv
git commit -m "feat(inmet): conector da precipitação horária por estação, lido do zip anual"
```

---

### Tarefa 4: INMET — Bronze, Silver, Gold, agendamento e dicionário (G4)

**Files:**
- Create: `definitions/bronze/inmet_precipitacao.sqlx`, `definitions/silver/inmet_precipitacao.sqlx`, `definitions/gold/precipitacao_diaria_estacao.sqlx`
- Create: `docs/dicionario-dados/inmet_precipitacao.md`
- Modify: `infra/modules/scheduler/main.tf`, `infra/modules/monitoramento/main.tf`, `includes/silencio.js`, `scripts/anotar_catalogo.py`, `src/portal/custo.py`, `docs/dicionario-dados/README.md`, `docs/arquitetura/dominios-analiticos.md`
- Test: `tests/unit/test_sql.py`

**Interfaces:**
- Consumes: os campos de `PrecipitacaoHoraria` da Tarefa 3.
- Produces: `bronze.inmet_precipitacao`, `silver.inmet_precipitacao`, `gold.precipitacao_diaria_estacao` (colunas `estacao`, `data_referencia`, `precipitacao_mm_dia`, `horas_com_medicao`, `horas_sem_medicao`, `ultima_hora_com_dado`).

- [ ] **Passo 1: Bronze**

```sql
config {
  type: "operations",
  schema: "bronze",
  hasOutput: true,
  tags: ["bronze"]
}

-- Bronze: precipitação horária por estação do INMET (zip anual do portal). Append-only.
CREATE TABLE IF NOT EXISTS ${self()} (
  estacao          STRING  NOT NULL OPTIONS(description="Código da estação (WMO), ex.: A701"),
  nome_estacao     STRING  NOT NULL,
  regiao           STRING  NOT NULL OPTIONS(description="N, NE, CO, SE ou S"),
  uf               STRING  NOT NULL,
  latitude         NUMERIC NOT NULL,
  longitude        NUMERIC NOT NULL,
  altitude_m       NUMERIC,
  data_referencia  DATE    NOT NULL OPTIONS(description="Dia da medição (UTC)"),
  hora_utc         INT64   NOT NULL OPTIONS(description="Hora UTC, 0 a 23"),
  precipitacao_mm  NUMERIC OPTIONS(description="Chuva da hora em mm; nulo é hora sem medição, nunca zero"),

  _ingestao_id        STRING    NOT NULL OPTIONS(description="Identificador da execução de ingestão"),
  _ingestao_timestamp TIMESTAMP NOT NULL OPTIONS(description="Quando o registro entrou no lake"),
  _fonte              STRING    NOT NULL OPTIONS(description="Identificador da fonte"),
  _schema_versao      STRING    NOT NULL OPTIONS(description="Versão do contrato lido na origem")
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY estacao, data_referencia
OPTIONS(description="Precipitação horária do INMET — camada Bronze, append-only");
```

- [ ] **Passo 2: Silver** (chave natural: estação, dia e hora; vence a ingestão mais recente)

```sql
config {
  type: "view",
  schema: "silver",
  tags: ["silver"],
  assertions: {
    uniqueKey: ["estacao", "data_referencia", "hora_utc"],
    nonNull: ["estacao", "data_referencia", "hora_utc"],
    rowConditions: [
      "hora_utc BETWEEN 0 AND 23",
      "precipitacao_mm IS NULL OR (precipitacao_mm >= 0 AND precipitacao_mm <= 500)"
    ]
  }
}

-- Silver: precipitação horária do INMET deduplicada. Para cada estação, dia e hora vence a ingestão mais recente.
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,    -- a estação é do INMET, não do submercado (o mapeamento por bacia é da Tarefa 5)
  CAST(NULL AS STRING) AS codigo_usina,
  CAST(NULL AS STRING) AS agente_ccee,
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  CAST(NULL AS STRING) AS periodo_apuracao_ccee,
  estacao, nome_estacao, regiao, uf, latitude, longitude, altitude_m,
  hora_utc, precipitacao_mm,
  _ingestao_id, _ingestao_timestamp
FROM ${ref("bronze", "inmet_precipitacao")}
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY estacao, data_referencia, hora_utc
  ORDER BY _ingestao_timestamp DESC
) = 1
```

- [ ] **Passo 3: Gold** (diária por estação; expõe a última hora com dado, para o zip atrasado não parecer sucesso). Atenção: `MAX(MAX(...)) OVER (...)` sobre um agregado é SQL válido no BigQuery, mas só o Dataform o compila de verdade; se ele rejeitar, mova a `ultima_hora_com_dado` para uma CTE separada e faça o `JOIN` por `estacao`.

```sql
config {
  type: "table",
  schema: "gold",
  tags: ["gold"],
  dependOnDependencyAssertions: true
}

-- Gold: chuva diária por estação do INMET. `horas_sem_medicao` mostra o buraco da origem em vez de escondê-lo
-- dentro de um zero. `ultima_hora_com_dado` é por estação: o zip do ano corrente atrasa semanas, e um dia
-- sem linhas não quer dizer um dia sem chuva. Sem KPI nem comparação entre estações (ADR 012).
SELECT
  estacao,
  ANY_VALUE(nome_estacao) AS nome_estacao,
  ANY_VALUE(uf) AS uf,
  data_referencia,
  SUM(precipitacao_mm) AS precipitacao_mm_dia,
  COUNTIF(precipitacao_mm IS NOT NULL) AS horas_com_medicao,
  COUNTIF(precipitacao_mm IS NULL) AS horas_sem_medicao,
  MAX(MAX(IF(precipitacao_mm IS NOT NULL, TIMESTAMP_ADD(TIMESTAMP(data_referencia), INTERVAL hora_utc HOUR), NULL)))
    OVER (PARTITION BY estacao) AS ultima_hora_com_dado
FROM ${ref("silver", "inmet_precipitacao")}
GROUP BY estacao, data_referencia
```

- [ ] **Passo 4: teste que fixa a regra "nulo não é zero"**

Acrescente a `tests/unit/test_sql.py`:
```python
def test_gold_da_chuva_nao_trata_hora_sem_medicao_como_zero() -> None:
    """Hora sem medição conta em `horas_sem_medicao`; somar COALESCE(..., 0) esconderia o buraco da origem."""
    caminho = Path(__file__).resolve().parents[2] / "definitions" / "gold" / "precipitacao_diaria_estacao.sqlx"
    sql = caminho.read_text(encoding="utf-8")
    assert "horas_sem_medicao" in sql
    assert "COALESCE(precipitacao_mm" not in sql
```
Run: `uv run pytest tests/unit/test_sql.py -q`
Expected: PASS.

- [ ] **Passo 5: agendamento, silêncio, catálogo e custo**

O zip é lido inteiro a cada execução (60 a 90 MB) e muda poucas vezes por mês: agende **uma vez por semana** (segunda, 06h), janela de 62 dias, 1 CPU e memória como a das fontes mensais do ONS. Acrescente em `infra/modules/scheduler/main.tf`, depois de `aneel_tarifas`:
```hcl
    inmet_precipitacao = {
      # O zip anual do portal é reescrito poucas vezes por mês e atrasa (o de 2026 tinha Last-Modified de 02/09
      # em 02/10). Semanal, segunda às 6h; a janela de 62 dias cobre a virada do zip e a republicação.
      cron         = "0 6 * * 1"
      ultimos_dias = 62
    }
```
Silêncio: `inmet_precipitacao: 180` em `includes/silencio.js` e `inmet_precipitacao = 180 # semanal + folga` em `infra/modules/monitoramento/main.tf`. Catálogo (`scripts/anotar_catalogo.py`): `"precipitacao_diaria_estacao": {"dominio": "meteorologico", "responsavel": INTELIGENCIA}` (confira o nome exato do domínio meteorológico em `docs/arquitetura/dominios-analiticos.md` e use o mesmo). Custo (`src/portal/custo.py`): domínio `"Meteorológico"` (mesma grafia do mapa existente) e `BYTES_POR_LINHA` 180.
Run: `uv run pytest tests -q -k "silencio or infra or catalogo or custo"`
Expected: PASS.

- [ ] **Passo 6: dicionário**

Escreva `docs/dicionario-dados/inmet_precipitacao.md` no formato de `docs/dicionario-dados/aneel_tarifas.md` (tabela de item, campos origem para Bronze para Silver, dimensões comuns, deduplicação, Gold, qualidade, linhagem). Inclua, **com os números que o Passo 6 da Tarefa 3 imprimiu**: o formato do CSV, as 47 horas vazias de A701 em 2025, o `-9999`, a defasagem do zip de 2026 e a observação de que "por bacia" depende da Tarefa 5. Atualize `docs/dicionario-dados/README.md` (linha da fonte e a contagem "N fontes em M dicionários") e `docs/arquitetura/dominios-analiticos.md` (fontes e Gold do domínio).
Run: `uv run pytest tests -q`
Expected: PASS (o teste de catálogo exige que toda Gold esteja documentada e anotada).

- [ ] **Passo 7: PR, merge, deploy e carga**

```bash
git add definitions docs infra includes scripts src tests
git commit -m "feat(inmet): Bronze, Silver, Gold, agendamento e dicionário da precipitação horária"
git push -u origin feat/inmet-precipitacao
```
Depois do merge: `gh workflow run "Deploy GCP" -f environment=hml -f module=all`; carga do histórico **em janelas de até 3 meses**, uma de cada vez, de 2024-09-01 a 2026-10-02 (`gh workflow run executar-ingestao.yml -f environment=hml -f conector=inmet_precipitacao -f de=... -f ate=...`). Confira no BigQuery: `SELECT COUNT(*), COUNT(DISTINCT estacao), MIN(data_referencia), MAX(data_referencia) FROM silver.inmet_precipitacao`. Registre a cobertura no dicionário.

---

### Tarefa 5: Decidir o "por bacia" do INMET (G4)

**Por que é uma tarefa à parte:** a cláusula diz "precipitação histórica **por bacia**". O INMET entrega **por estação**, com latitude e longitude. Ligar estação a bacia exige uma fonte de bacias que o projeto não tem. O conjunto `precipitacao-estacao` do ONS (CKAN) é chuva diária por estação, mas vai só até 2021 nos dois anos listados e não resolve o histórico recente.

**Files:**
- Create: `docs/arquitetura/decisoes/0NN-precipitacao-por-bacia.md` (use o próximo número livre; veja `ls docs/arquitetura/decisoes/`)

**Critério de saída:** um registro de decisão com uma das três saídas, com evidência.

- [ ] **Passo 1: levantar as fontes de bacia**

Run: `uv run python -c "import requests; print(requests.get('https://dadosabertos.aneel.gov.br/api/3/action/package_search', params={'q':'bacia','rows':20}, headers={'User-Agent':'Mozilla/5.0'}, timeout=40).json()['result']['count'])"` e o mesmo contra `https://dados.ons.org.br/api/3/action/package_search?q=bacia`. Liste, para cada conjunto achado: nome, formato (se tem geometria ou só nome de bacia) e URL. As bacias que o projeto já usa estão em `silver.ons_ear_bacia` (`nomecurto`): confira quantas e quais são.

- [ ] **Passo 2: avaliar as três saídas**

(A) **Ponto em polígono:** se houver polígonos de bacia hidrográfica públicos (por exemplo, da ANA), carregue-os numa tabela e faça `ST_CONTAINS` na Gold. Custo: nova fonte (7 componentes) e a granularidade das bacias do ONS (`nomecurto`) pode não coincidir com a da ANA. (B) **Estação mais próxima de uma usina/reservatório do ONS**, só se houver coordenadas deles. (C) **Entregar por estação e UF**, registrar que "por bacia" depende do mapeamento e pedir à Alup, por escrito, que aceite o recorte por estação, como a cláusula permite ao tratar o escopo como "referência inicial".

- [ ] **Passo 3: escrever o registro de decisão e commitar**

Estrutura: Contexto, Alternativas (A, B, C com evidência), Decisão, Consequências (o que muda na Gold e quantas horas). Se a decisão for (A) ou (B), acrescente ao plano uma tarefa nova com código; se for (C), a pergunta à Alup entra no fechamento (Tarefa 8).
```bash
git add docs/arquitetura/decisoes
git commit -m "docs: decisão sobre o recorte por bacia da precipitação do INMET"
```

---

### Tarefa 6: Investigar o ONS Operacional — IPDO e ACOMPH (G5)

**Fatos verificados:** o CKAN do ONS não tem conjunto chamado `ipdo` nem `acomph` (0 resultados em `package_search`). Existem conjuntos operacionais próximos: `carga-energia`, `demanda_maxima_di`, `programacao_diaria`, `dados-hidrologicos-res`. **Não verificado:** onde o IPDO (Informativo Preliminar Diário da Operação) e o ACOMPH (acompanhamento das condições hidroenergéticas) são distribuídos, e se exigem login.

**Files:**
- Create: `docs/arquitetura/decisoes/0NN-ons-operacional-ipdo-acomph.md`

**Critério de saída:** registro de decisão com uma de três saídas.

- [ ] **Passo 1: procurar a origem pública**

Rode, para cada termo (`IPDO`, `Informativo Preliminar Diário da Operação`, `ACOMPH`, `acompanhamento hidroenergético`), `package_search` no CKAN do ONS (`q=<termo>` e `q=<termo>` em `resource_search` com `query=name:<termo>`) e abra, no navegador, a página "Resultados da Operação" do site do ONS. Anote: o IPDO é arquivo (PDF, XLS) ou página? Tem URL previsível por data? Pede cadastro? O ACOMPH é distribuído por qual canal? Faça um `GET` leve em cada URL candidata com `criar_sessao()` e anote o status (200, 401, 403).

- [ ] **Passo 2: classificar**

(A) **Arquivo ou API pública com URL estável:** implemente como conector (siga a Tarefa 3 como molde e escreva uma tarefa nova com a fixture real). (B) **Exige credencial ou cadastro:** não é Onda 1 ("sem dependência de credenciais da Alup"): o segredo, a declaração em `infra/` e o pedido à Alup são de Onda 2; registre e proponha o deslocamento, por escrito. (C) **O conteúdo já está nos conjuntos entregues** (carga, EAR, ENA, geração): proponha à Alup a substituição, com a tabela "o que o IPDO traz" contra "onde está no lake", usando a flexibilidade da cláusula (fontes alteráveis dentro das 580 h).

- [ ] **Passo 3: escrever o registro de decisão e commitar**

Inclua a evidência (URLs e status) e, em (B) ou (C), o texto exato do pedido de aceite, **sem enviar**: a decisão de enviar é de quem fala com o cliente.
```bash
git add docs/arquitetura/decisoes
git commit -m "docs: decisão sobre IPDO e ACOMPH no ONS Operacional"
```

---

### Tarefa 7: Investigar o acesso ao CPTEC (G6)

**Fatos verificados:** `http://servicos.cptec.inpe.br/XML/...` responde 403 com `User-Agent` de navegador e com o cabeçalho de identificação do projeto; `https://api.cptec.inpe.br/` não conecta daqui; o proxy `brasilapi.com.br/api/cptec` respondeu 404 e 500. O site `https://www.cptec.inpe.br/` responde 200. **Não verificado:** se o bloqueio é por IP de origem, por geografia, por exigência de cadastro ou por endpoint descontinuado.

**Files:**
- Create: `docs/arquitetura/decisoes/0NN-cptec-acesso.md`

**Critério de saída:** registro de decisão com uma de três saídas.

- [ ] **Passo 1: achar a documentação vigente**

Abra `https://www.cptec.inpe.br/` e procure "Web Service", "API" e "dados abertos"; anote o endereço e o formato (XML, JSON) **atuais** da previsão de 7 dias e da previsão climática. Faça um `GET` leve de cada endereço com `criar_sessao()` e anote o status.

- [ ] **Passo 2: testar de dentro do GCP**

O 403 pode ser do IP da sua máquina. Rode a mesma chamada de dentro do Cloud Run de `dev` (um job de teste descartável declarado em `infra/`, porque recurso fora de `infra/` não existe) e compare o status. Se for 200 de lá, o bloqueio é do seu IP; se for 403, é da origem.

- [ ] **Passo 3: classificar**

(A) **Endpoint público acessível (daqui ou do GCP):** implemente o conector; a fixture é a resposta real; o conector levanta `LayoutInesperadoError` em 403 ou corpo vazio, **nunca** devolve lista vazia (Review Focus 4). (B) **Acesso por cadastro, token ou IP liberado:** é dependência da Alup ou do INPE, fora da Onda 1; registre, e o pedido sai pelo canal da Alup. (C) **Endpoint descontinuado sem substituto público:** proponha à Alup a troca da fonte (outro provedor público de previsão), com a evidência.

- [ ] **Passo 4: registro de decisão e commit**

```bash
git add docs/arquitetura/decisoes
git commit -m "docs: decisão sobre o acesso ao CPTEC"
```

---

### Tarefa 8: Fechamento — 7 componentes, painel e aceite da Onda 1

**Files:**
- Modify: `painel/marcos.toml`, `docs/status.md`, `docs/plano-execucao.md` §3.2
- Create: `docs/relatorios/2026-10-NN-fechamento-onda-1.md`

**Interfaces:**
- Consumes: as contagens da Tarefa 1, a carga da Tarefa 4, as decisões das Tarefas 5, 6 e 7.
- Produces: o relatório que a ness. usa para pedir o aceite da Onda 1, **sem prometer o que não foi conferido**.

- [ ] **Passo 1: montar a matriz dos 7 componentes por fonte**

Para cada fonte da Onda 1 (`ons_ear`, `ons_ena`, `ccee_pld`, `ons_carga`, `aneel_tarifas`, `ace_prc`, `bcb_igpm`, `inmet_precipitacao`, e as que as Tarefas 6 e 7 produzirem), marque os sete componentes e o ambiente em que foi conferido, com o comando que prova cada um. Fonte com componente faltando entra como **pendente**, nunca "entregue".

- [ ] **Passo 2: rodar a suíte completa e o deploy dos dois ambientes**

Run: `uv run pytest tests -q` e `uv run ruff check src tests scripts`
Expected: PASS e sem achados. Depois `gh workflow run "Deploy GCP" -f environment=hml -f module=all` e o mesmo em `dev`; ambos terminam em `success` com `Dataform terminou em SUCCEEDED`.

- [ ] **Passo 3: escrever o relatório**

Seções: o que a cláusula 4ª prevê (a tabela do início deste plano), o que foi entregue com a evidência por ambiente, o que **não** foi entregue e por quê (bloqueio, credencial, decisão pendente) e as decisões que dependem da Alup, com o texto pronto. Sem atribuição de IA. Conferir à mão antes de publicar.

- [ ] **Passo 4: atualizar painel e status**

Marque `estado = "entregue"` só para o que a matriz do Passo 1 prova. Rode o workflow `Painel` e confira `painel.alupdata.ness.com.br`.
```bash
git add painel docs
git commit -m "docs: fechamento da Onda 1 com a matriz de componentes e as decisões abertas"
```

---

## Autoavaliação

**Cobertura do spec.** Os cinco itens da cláusula 4ª e o IGP-M estão no registro de gaps. G2 e G3 (entregues em `hml`) são provados em `dev` na Tarefa 1; G4 tem as Tarefas 3, 4 e 5; G5 e G6 têm as Tarefas 6 e 7; G7 e G8 estão na Tarefa 2; o aceite e o painel, na Tarefa 8. Homologação das tabelas Bronze, Silver e Gold está nos passos de camada da Tarefa 4 e na matriz da Tarefa 8.

**Lacunas assumidas.** As Tarefas 6 e 7 **não** trazem código de conector: a origem de IPDO, ACOMPH e CPTEC não foi descoberta, e escrever código agora seria inventar o contrato de dados. Quando a investigação decidir "implementar", escreva a tarefa de implementação com o molde da Tarefa 3 e a fixture real (rode `writing-plans` de novo para a fonte). Não é um "TBD": é o ponto de reentrada, com critério de saída e dono.

**Consistência de tipos.** `PrecipitacaoHoraria` (Tarefa 3) define `estacao`, `data_referencia`, `hora_utc`, `precipitacao_mm`; a Bronze, a Silver e a Gold da Tarefa 4 usam exatamente esses nomes. A chave da Silver é `(estacao, data_referencia, hora_utc)` nas três.

**Review Focus.** As linhas 1 e 2 têm teste na Tarefa 3 (`test_hora_sem_medicao_vira_nulo_e_nunca_zero`, `test_sentinela_9999_vira_nulo`, `test_janela_que_cruza_o_ano_baixa_os_dois_zips`); a linha 3, na Tarefa 4 (`ultima_hora_com_dado` e o teste de SQL); as linhas 4 e 5 só se aplicam se as Tarefas 6 e 7 decidirem "implementar", e o teste que as fixa está descrito nelas.

## Estimativa de esforço (não é medição)

| Tarefa | Horas |
|---|---:|
| 1 Provar `dev` e `hml` | 2 |
| 2 Alinhar plano e painel | 2 |
| 3 INMET conector | 6 |
| 4 INMET camadas, agendamento, dicionário, carga | 8 |
| 5 Decisão "por bacia" | 3 |
| 6 Investigação ONS Operacional | 4 |
| 7 Investigação CPTEC | 4 |
| 8 Fechamento | 4 |
| **Total até a decisão dos três gaps** | **33** |

A implementação de IPDO, ACOMPH e CPTEC, se as investigações concluírem "implementar", soma de 10 a 20 horas por fonte e **não** está na tabela.
