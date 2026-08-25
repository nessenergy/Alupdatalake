"""Gera o esqueleto dos 7 componentes de um conector novo.

    uv run python -m scripts.novo_conector --fonte ons --entidade carga

Cria conector, DDL Bronze, views Silver/Gold, teste e dicionário de dados.
Nenhum arquivo existente é sobrescrito.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

CONECTOR = '''"""Conector {fonte_titulo} — {entidade}.

Fonte: TODO (endpoint, banco ou arquivo de origem)
Documentação: TODO
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import date
from typing import Any

from pydantic import BaseModel

from src.core.conector import Conector
from src.core.execucao import Janela
from src.core.http import criar_sessao, get_json
from src.core.registry import registrar

URL = "TODO"


class {classe}Registro(BaseModel):
    """Um registro de {entidade} já normalizado."""

    data_referencia: date
    # TODO: campos da fonte


@registrar
class {classe}(Conector):
    fonte = "{fonte}"
    entidade = "{entidade}"
    schema = {classe}Registro
    schema_versao = "1"
    max_dias_por_requisicao = None  # TODO: limite da fonte, se houver

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        raise NotImplementedError("TODO: extrair {fonte}/{entidade}")

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError("TODO: mapear o payload para {classe}Registro")
'''

BRONZE = """-- Bronze: {fonte}/{entidade}. Append-only; a Silver deduplica.
CREATE TABLE IF NOT EXISTS `${{projeto}}.${{bronze}}.{rotulo}` (
  data_referencia     DATE      NOT NULL,
  -- TODO: campos da fonte

  _ingestao_id        STRING    NOT NULL,
  _ingestao_timestamp TIMESTAMP NOT NULL,
  _fonte              STRING    NOT NULL,
  _schema_versao      STRING    NOT NULL
)
PARTITION BY DATE(_ingestao_timestamp)
CLUSTER BY data_referencia;
"""

SILVER = """-- Silver: {fonte}/{entidade} higienizada, deduplicada, com dimensões comuns.
CREATE OR REPLACE VIEW `${{projeto}}.${{silver}}.{rotulo}` AS
SELECT
  data_referencia,
  CAST(NULL AS STRING) AS submercado,      -- TODO: preencher ou justificar
  CAST(NULL AS STRING) AS codigo_usina,    -- TODO
  CAST(NULL AS STRING) AS agente_ccee,     -- TODO
  FORMAT_DATE('%Y-%m', data_referencia) AS periodo_apuracao,
  _ingestao_id,
  _ingestao_timestamp
FROM `${{projeto}}.${{bronze}}.{rotulo}`
QUALIFY ROW_NUMBER() OVER (
  PARTITION BY data_referencia  -- TODO: chave natural completa
  ORDER BY _ingestao_timestamp DESC
) = 1;
"""

GOLD = """-- Gold: TODO — nomeie pela pergunta de negócio que a view responde.
-- Se for um SELECT * da Silver, ela não deveria existir.
CREATE OR REPLACE VIEW `${{projeto}}.${{gold}}.{rotulo}` AS
SELECT *
FROM `${{projeto}}.${{silver}}.{rotulo}`;
"""

TESTE = '''"""Testes do conector {fonte}/{entidade} — sem rede."""

import pytest

from src.conectores.{modulo} import {classe}
from src.core.execucao import Janela


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.{modulo}.criar_sessao", lambda: None)
    return {classe}()


@pytest.mark.skip(reason="TODO: implementar com fixture de payload real")
def test_transformar_mapeia_campos(conector):
    raise NotImplementedError
'''

DICIONARIO = """# {fonte_titulo} — {entidade}

| Item | Valor |
|---|---|
| Fonte | TODO |
| Onda | TODO |
| Frequência | TODO |
| Dono do dado (Alup) | TODO |
| Credencial | TODO (Secret Manager: `alupdata-{fonte}-<campo>`) |

## Campos

| Origem | Bronze | Silver | Gold | Tipo | Transformação |
|---|---|---|---|---|---|
| TODO | TODO | TODO | — | TODO | TODO |

## Dimensões comuns

| Dimensão | Preenchida? | Observação |
|---|---|---|
| `data_referencia` | TODO | |
| `submercado` | TODO | |
| `codigo_usina` | TODO | |
| `agente_ccee` | TODO | |
| `periodo_apuracao` | TODO | |

## Qualidade e observações

- TODO
"""


def escrever(caminho: Path, conteudo: str) -> bool:
    """Grava só se o arquivo ainda não existir."""
    if caminho.exists():
        print(f"  existe, mantido: {caminho.relative_to(RAIZ)}")
        return False
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    print(f"  criado: {caminho.relative_to(RAIZ)}")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Esqueleto dos 7 componentes de um conector")
    parser.add_argument("--fonte", required=True, help="identificador curto da fonte (ons, ccee, aneel)")
    parser.add_argument("--entidade", required=True, help="o que é ingerido (carga, precos, cambio_ptax)")
    args = parser.parse_args(argv)

    fonte, entidade = args.fonte.lower(), args.entidade.lower()
    rotulo = f"{fonte}_{entidade}"
    modulo = rotulo
    classe = "".join(parte.capitalize() for parte in rotulo.split("_"))
    ctx = {
        "fonte": fonte,
        "entidade": entidade,
        "rotulo": rotulo,
        "modulo": modulo,
        "classe": classe,
        "fonte_titulo": fonte.upper(),
    }

    print(f"Conector {rotulo}:")
    escrever(RAIZ / "src" / "conectores" / f"{modulo}.py", CONECTOR.format(**ctx))
    escrever(RAIZ / "sql" / "bronze" / f"{rotulo}.sql", BRONZE.format(**ctx))
    escrever(RAIZ / "sql" / "silver" / f"{rotulo}.sql", SILVER.format(**ctx))
    escrever(RAIZ / "sql" / "gold" / f"{rotulo}.sql", GOLD.format(**ctx))
    escrever(RAIZ / "tests" / "unit" / "conectores" / f"test_{modulo}.py", TESTE.format(**ctx))
    escrever(RAIZ / "docs" / "dicionario-dados" / f"{rotulo}.md", DICIONARIO.format(**ctx))
    print("\nFaltam os componentes 06 (agendamento) e a implementação — ver skill `conector-alupdata`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
