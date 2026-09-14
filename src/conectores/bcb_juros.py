"""Conector BCB — Selic e CDI diários (Onda 1, API pública, sem credencial).

Fonte: SGS / Banco Central do Brasil, séries 11 (Selic) e 12 (CDI).
Documentação: https://dadosabertos.bcb.gov.br/dataset/11-taxa-de-juros---selic

As duas séries fecham o domínio **Econômico** do B1 (IPCA, Selic, câmbio, CDI)
e entram por aqui, e não como fontes novas: é o mesmo BCB do PTAX, com o mesmo
regime de acesso. Uma entidade só, com a série como coluna, porque Selic e CDI
têm a mesma forma e quase sempre são lidas lado a lado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, Field

from src.core.conector import Conector
from src.core.http import criar_sessao, get_json
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"

# Código da série no SGS. Ambas são taxa **ao dia**, em percentual.
SERIES = {"selic": 11, "cdi": 12}

# 1% ao dia é da ordem de 1.100% ao ano: não é juro, é erro de origem.
TAXA_DIARIA_MAXIMA = Decimal("1")


class TaxaJuros(BaseModel):
    """A taxa de um dia útil, em uma das séries."""

    data_referencia: date
    serie: Literal["selic", "cdi"]
    taxa_percentual_dia: Decimal = Field(ge=0, le=TAXA_DIARIA_MAXIMA)


@registrar
class BcbJuros(Conector):
    """Selic e CDI diários. O SGS só publica em dia útil — feriado volta vazio."""

    fonte = "bcb"
    entidade = "juros"
    schema = TaxaJuros
    schema_versao = "1"
    max_dias_por_requisicao = 3650  # o SGS recusa mais de 10 anos de série diária

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        params = {
            "formato": "json",
            "dataInicial": janela.inicio.strftime("%d/%m/%Y"),
            "dataFinal": janela.fim.strftime("%d/%m/%Y"),
        }
        for serie, codigo in SERIES.items():
            # O payload do SGS não diz qual série ele é — só `data` e `valor`.
            # O rótulo vem do pedido, e entra no bruto para chegar ao raw: sem
            # ele, o arquivo no GCS seria irreprocessável.
            for registro in get_json(self._sessao, URL.format(codigo=codigo), params=params):
                yield registro | {"serie": serie}

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        dia, mes, ano = bruto["data"].split("/")
        return {
            "data_referencia": f"{ano}-{mes}-{dia}",
            "serie": bruto["serie"],
            "taxa_percentual_dia": bruto["valor"],
        }
