"""Conector Hubspot — negócios do CRM (Onda 2, exige token).

Fonte: Hubspot CRM API v3, objeto `deals`.
Documentação: https://developers.hubspot.com/docs/api/crm/deals

Escrito contra a documentação pública, **sem token**: a credencial é uma
pendência da Alup (pendência A9, `docs/status.md`). O contrato de dados abaixo
vale até a primeira execução real — quando o token chegar, a tarefa é ligar e
conferir, não começar.

A janela filtra por `hs_lastmodifieddate`, não por data de criação: negócio que
muda de estágio precisa ser reingerido, e a Silver deduplica pela versão mais
recente.
"""

from __future__ import annotations

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar
from src.core.secrets import ler_secret

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

URL_BUSCA = "https://api.hubapi.com/crm/v3/objects/deals/search"
LIMITE_PAGINA = 100  # máximo aceito pelo endpoint de busca

PROPRIEDADES = [
    "dealname",
    "dealstage",
    "pipeline",
    "amount",
    "closedate",
    "createdate",
    "hs_lastmodifieddate",
    "hubspot_owner_id",
]


class Negocio(BaseModel):
    """Um negócio (deal) do CRM, na versão mais recente lida da API."""

    negocio_id: str
    nome: str
    estagio: str
    pipeline: str
    valor: Decimal | None = Field(default=None, ge=0)
    data_fechamento: date | None = None
    criado_em: datetime
    modificado_em: datetime
    proprietario_id: str | None = None

    @field_validator("negocio_id", "estagio", "pipeline")
    @classmethod
    def _nao_vazio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("campo obrigatório vazio")
        return valor.strip()


@registrar
class HubspotNegocios(Conector):
    """Negócios modificados na janela. Paginação por cursor `after`."""

    fonte = "hubspot"
    entidade = "negocios"
    schema = Negocio
    schema_versao = "1"
    max_dias_por_requisicao = None  # o filtro da busca aceita o intervalo inteiro

    def __init__(self) -> None:
        # O endpoint é POST, mas apenas consulta: repetir 429/5xx não cria ou
        # altera negócio na origem.
        self._sessao = criar_sessao(retry_post=True)

    def _cabecalhos(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {ler_secret(self.fonte, 'api-token')}"}

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        cfg = get_settings()
        corpo: dict[str, Any] = {
            "filterGroups": [
                {
                    "filters": [
                        {
                            "propertyName": "hs_lastmodifieddate",
                            "operator": "BETWEEN",
                            "value": _epoch_ms(janela.inicio),
                            "highValue": _epoch_ms(janela.fim, fim_do_dia=True),
                        }
                    ]
                }
            ],
            "properties": PROPRIEDADES,
            "sorts": [{"propertyName": "hs_lastmodifieddate", "direction": "ASCENDING"}],
            "limit": LIMITE_PAGINA,
        }

        pagina = 0
        while True:
            resposta = self._sessao.post(URL_BUSCA, json=corpo, headers=self._cabecalhos(), timeout=cfg.http_timeout)
            resposta.raise_for_status()
            payload = resposta.json()

            yield from payload.get("results", [])

            depois = payload.get("paging", {}).get("next", {}).get("after")
            if not depois:
                return
            pagina += 1
            logger.info("hubspot: página %d, cursor %s", pagina, depois)
            corpo["after"] = depois

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        props = bruto.get("properties", {})
        return {
            "negocio_id": bruto.get("id", ""),
            "nome": props.get("dealname") or "(sem nome)",
            "estagio": props.get("dealstage", ""),
            "pipeline": props.get("pipeline", ""),
            "valor": props.get("amount") or None,
            "data_fechamento": (props.get("closedate") or None) and props["closedate"][:10],
            "criado_em": props.get("createdate"),
            "modificado_em": props.get("hs_lastmodifieddate"),
            "proprietario_id": props.get("hubspot_owner_id") or None,
        }


def _epoch_ms(dia: date, *, fim_do_dia: bool = False) -> str:
    """Data em milissegundos desde a época, UTC — formato que o filtro exige."""
    from datetime import UTC, time

    momento = datetime.combine(dia, time.max if fim_do_dia else time.min, tzinfo=UTC)
    return str(int(momento.timestamp() * 1000))
