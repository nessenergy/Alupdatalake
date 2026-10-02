"""Conector BCB — IGP-M mensal (Onda 1, API pública, sem credencial).

Fonte: SGS / Banco Central do Brasil, série 189 (IGP-M, variação mensal em %).
Documentação: https://dadosabertos.bcb.gov.br/dataset/189-indice-geral-de-precos-do-mercado---igp-m

O IGP-M (FGV) é o índice de reajuste de boa parte dos contratos de energia: entra no
domínio **Econômico** ao lado do IPCA. O SGS data o mês no **dia 1** (`01/09/2026` é
setembro) e o valor sai perto do fim do próprio mês. A FGV não revisa o número publicado.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from src.core.conector import Conector
from src.core.http import criar_sessao, get_json
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
SERIE_SGS = 189

# O índice já teve meses de dois dígitos na década de 1990; fora desta faixa não é inflação, é erro de origem.
VARIACAO_MINIMA = Decimal("-20")
VARIACAO_MAXIMA = Decimal("100")


class VariacaoIgpm(BaseModel):
    """A variação do IGP-M em um mês, em percentual."""

    data_referencia: date  # primeiro dia do mês, como o SGS publica
    variacao_percentual_mes: Decimal = Field(ge=VARIACAO_MINIMA, le=VARIACAO_MAXIMA)


@registrar
class BcbIgpm(Conector):
    """IGP-M mensal. Série curta (um ponto por mês): uma chamada cobre qualquer janela."""

    fonte = "bcb"
    entidade = "igpm"
    schema = VariacaoIgpm
    schema_versao = "1"
    max_dias_por_requisicao = None

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        # O SGS datou o mês no dia 1: uma janela que começa no meio do mês perderia o próprio mês.
        params = {
            "formato": "json",
            "dataInicial": janela.inicio.replace(day=1).strftime("%d/%m/%Y"),
            "dataFinal": janela.fim.strftime("%d/%m/%Y"),
        }
        yield from get_json(self._sessao, URL.format(codigo=SERIE_SGS), params=params)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        dia, mes, ano = bruto["data"].split("/")
        return {
            "data_referencia": f"{ano}-{mes}-{dia}",
            "variacao_percentual_mes": bruto["valor"],
        }
