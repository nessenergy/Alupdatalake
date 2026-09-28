"""Conector ONS — energia armazenada (EAR) diária por bacia (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `ear_bacia_di`, um CSV por ano.
Documentação: https://dados.ons.org.br/dataset/ear-diario-por-bacia

Mesmo formato do `ons_ear` (CSV anual remoto, `;`, data ISO), com duas
diferenças que o dado impõe:

1. **Não há subsistema.** A unidade é a bacia (`nomecurto`); uma bacia pode
   atravessar subsistemas, então `submercado` fica nulo em vez de inventado.
2. **O percentual passa de 100.** Em 2026 a bacia do Paraguaçu ficou acima da
   própria capacidade máxima em 176 dias (até 154%), e o percentual bate com
   verificada/máxima. A regra 0-100 do `ons_ear` não vale aqui: só negativo é
   recusado.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/ear_bacia_di/EAR_DIARIO_BACIAS_{ano}.csv"

logger = logging.getLogger(__name__)


class EarBacia(BaseModel):
    """Energia armazenada verificada de uma bacia em um dia, em MWmês."""

    data_referencia: date
    bacia: str
    ear_max_mwmes: Decimal
    ear_verificada_mwmes: Decimal
    ear_verificada_percentual: Decimal
    """Pode passar de 100 (ver docstring do módulo)."""

    @field_validator("bacia")
    @classmethod
    def _bacia_preenchida(cls, valor: str) -> str:
        nome = valor.strip().upper()
        if not nome:
            raise ValueError("bacia vazia")
        return nome

    @field_validator("ear_max_mwmes", "ear_verificada_mwmes", "ear_verificada_percentual")
    @classmethod
    def _nao_negativo(cls, valor: Decimal) -> Decimal:
        if valor < 0:
            raise ValueError(f"valor negativo: {valor}")
        return valor


@registrar
class OnsEarBacia(Conector):
    """EAR diária por bacia. Um CSV por ano, filtrado pela janela."""

    fonte = "ons"
    entidade = "ear_bacia"
    schema = EarBacia
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por ano de arquivo, não por dias

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_ano(self, ano: int) -> str | None:
        """CSV do ano, ou `None` quando o catálogo ainda não publicou aquele ano."""
        from src.core.config import get_settings

        resposta = self._sessao.get(URL.format(ano=ano), timeout=get_settings().http_timeout)
        if resposta.status_code == 404:
            return None
        resposta.raise_for_status()
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano in range(janela.inicio.year, janela.fim.year + 1):
            logger.info("ONS EAR por bacia: baixando %d", ano)
            conteudo = self._baixar_ano(ano)
            if conteudo is None:
                logger.warning("ONS EAR por bacia: %d sem recurso publicado no catálogo, ignorado", ano)
                continue
            for linha in csv.DictReader(StringIO(conteudo), delimiter=";"):
                referencia = (linha.get("ear_data") or "")[:10]
                if not referencia:
                    continue
                if not (janela.inicio.isoformat() <= referencia <= janela.fim.isoformat()):
                    continue  # o arquivo é anual; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["ear_data"][:10],
            "bacia": bruto.get("nomecurto", ""),
            "ear_max_mwmes": bruto["ear_max_bacia"],
            "ear_verificada_mwmes": bruto["ear_verif_bacia_mwmes"],
            "ear_verificada_percentual": bruto["ear_verif_bacia_percentual"],
        }
