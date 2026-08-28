"""Conector ANEEL — SIGA, empreendimentos de geração (Onda 1, público).

Fonte: Dados Abertos ANEEL (CKAN), recurso `siga-empreendimentos-geracao.csv`.
Documentação: https://dadosabertos.aneel.gov.br/dataset/siga-sistema-de-informacoes-de-geracao-da-aneel

Terceiro formato do projeto: é **cadastro**, não série temporal. A API devolve o
retrato completo (~25 mil empreendimentos), sem parâmetro de período — por isso
a janela é ignorada e `data_referencia` vem de `DatGeracaoConjuntoDados`, a data
que a própria ANEEL declara para o conjunto.

É esta fonte que alimenta `codigo_usina` (CodCEG) como dimensão comum: sem ela,
as fontes internas da Onda 3 não têm com o que cruzar.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao, get_json
from src.core.planilha import decimal_br
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
RECURSO = "11ec447d-698d-4ab8-977f-b424d5deee6a"  # siga-empreendimentos-geracao.csv
PAGINA = 1000  # limite por requisição do datastore

logger = logging.getLogger(__name__)


def _decimal_br(valor: str | None) -> Decimal | None:
    """Como `decimal_br`, mas número inválido vira None em vez de erro.

    A ANEEL publica campo sujo em cadastro de 25 mil linhas: descartar o
    registro inteiro por causa de uma potência ilegível perderia o resto dele.
    """
    try:
        return decimal_br(valor)
    except ValueError:
        return None


class Empreendimento(BaseModel):
    """Um empreendimento de geração no cadastro da ANEEL."""

    data_referencia: str  # DatGeracaoConjuntoDados, ISO
    codigo_usina: str  # CodCEG — dimensão comum do projeto
    nome: str
    uf: str | None = None
    tipo_geracao: str | None = None
    fase: str | None = None
    origem_combustivel: str | None = None
    fonte_combustivel: str | None = None
    data_entrada_operacao: str | None = None
    potencia_outorgada_kw: Decimal | None = None
    potencia_fiscalizada_kw: Decimal | None = None
    garantia_fisica_kw: Decimal | None = None

    @field_validator("codigo_usina", "nome")
    @classmethod
    def _obrigatorio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("campo obrigatório vazio")
        return valor.strip()


@registrar
class AneelSiga(Conector):
    """Cadastro de empreendimentos de geração. Snapshot completo a cada execução."""

    fonte = "aneel"
    entidade = "siga"
    schema = Empreendimento
    schema_versao = "1"
    max_dias_por_requisicao = None  # cadastro: a janela não se aplica

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        """Pagina o datastore até o fim. A janela é ignorada: a fonte é cadastral."""
        del janela  # explícito: o cadastro não tem recorte de período
        offset = 0
        while True:
            pagina = get_json(
                self._sessao,
                URL,
                params={"resource_id": RECURSO, "limit": PAGINA, "offset": offset},
            )["result"]
            registros = pagina["records"]
            if not registros:
                return
            yield from registros
            offset += len(registros)
            if offset >= pagina["total"]:
                return
            logger.info("ANEEL SIGA: %d de %d", offset, pagina["total"])

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["DatGeracaoConjuntoDados"],
            "codigo_usina": bruto.get("CodCEG", ""),
            "nome": bruto.get("NomEmpreendimento", ""),
            "uf": bruto.get("SigUFPrincipal") or None,
            "tipo_geracao": bruto.get("SigTipoGeracao") or None,
            "fase": bruto.get("DscFaseUsina") or None,
            "origem_combustivel": bruto.get("DscOrigemCombustivel") or None,
            "fonte_combustivel": bruto.get("NomFonteCombustivel") or None,
            "data_entrada_operacao": bruto.get("DatEntradaOperacao") or None,
            "potencia_outorgada_kw": _decimal_br(bruto.get("MdaPotenciaOutorgadaKw")),
            "potencia_fiscalizada_kw": _decimal_br(bruto.get("MdaPotenciaFiscalizadaKw")),
            "garantia_fisica_kw": _decimal_br(bruto.get("MdaGarantiaFisicaKw")),
        }
