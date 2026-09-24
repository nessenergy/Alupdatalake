"""Conector BCB — cotação PTAX do dólar (Onda 1, API pública, sem credencial).

Fonte: Olinda / Banco Central do Brasil, serviço PTAX.
Documentação: https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/documentacao
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao, get_json
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoDolarPeriodo(dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)


class CotacaoDolar(BaseModel):
    """Um boletim de cotação do dólar em um instante do dia."""

    data_referencia: date
    data_hora_cotacao: datetime
    tipo_boletim: str
    cotacao_compra: Decimal = Field(ge=0)
    cotacao_venda: Decimal = Field(ge=0)

    @field_validator("tipo_boletim")
    @classmethod
    def _boletim_nao_vazio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("tipoBoletim vazio")
        return valor.strip()


@registrar
class BcbCambioPtax(Conector):
    """Cotação PTAX diária. O BCB só publica em dia útil — fim de semana volta vazio."""

    fonte = "bcb"
    entidade = "cambio_ptax"
    schema = CotacaoDolar
    schema_versao = "1"
    max_dias_por_requisicao = 90  # a API recusa intervalos longos

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        params = {
            "@dataInicial": f"'{janela.inicio.strftime('%m-%d-%Y')}'",
            "@dataFinalCotacao": f"'{janela.fim.strftime('%m-%d-%Y')}'",
            "$format": "json",
        }
        payload = get_json(self._sessao, URL, params=params)
        yield from payload.get("value", [])

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        data_hora = bruto["dataHoraCotacao"]
        return {
            "data_referencia": data_hora[:10],
            "data_hora_cotacao": data_hora,
            # Em 2026-09 o BCB parou de enviar `tipoBoletim` e passou a
            # devolver uma cotação por dia (verificado em 24/09 contra a API
            # real). Sem a classificação Abertura/Intermediário/Fechamento,
            # a única cotação do dia é tratada como o fechamento — é a
            # leitura que a Gold (`cambio_mensal`) já fazia e continua
            # fazendo. Boletim vazio explícito segue caindo aqui também.
            "tipo_boletim": bruto.get("tipoBoletim") or "Fechamento",
            "cotacao_compra": bruto["cotacaoCompra"],
            "cotacao_venda": bruto["cotacaoVenda"],
        }
