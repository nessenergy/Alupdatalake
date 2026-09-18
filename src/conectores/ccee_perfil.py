"""Conector CCEE — cadastro de perfis de agente (Onda 1, público).

Fonte: dados abertos da CCEE (CKAN), dataset `lista_perfil_v1`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/lista_perfil_v1

**É esta fonte que alimenta `agente_ccee`**, a última das cinco dimensões
comuns que ainda não tinha origem. Sem ela, dado de mercado da CCEE e posição
comercial interna não têm por onde se cruzar.

Não exige credencial: vale a mesma via pública da ADR 018.

## Duas armadilhas desta fonte

1. **`lista_perfil` está descontinuada.** A CCEE criou `lista_perfil_v1` em
   06/08/2025 (CO 562/25) e avisa que o dataset antigo só é atualizado até
   dezembro de 2025. Apontar para o antigo não daria erro — daria cadastro
   congelado, que é pior.
2. **Não há coluna de data.** É cadastro, não série: a CCEE publica o retrato
   corrente, sem período. `data_referencia` vem do `last_modified` que o CKAN
   declara para o recurso — a data que a própria origem atribui ao retrato,
   no mesmo espírito do `DatGeracaoConjuntoDados` do `aneel_siga`.

Por ser cadastro, **a janela não recorta** (ADR 013): a tabela é lida inteira a
cada execução, o Bronze acumula os retratos e a Silver fica com o mais recente.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

CKAN_PACOTE = "https://dadosabertos.ccee.org.br/api/3/action/package_show"

# `lista_perfil` (sem sufixo) foi descontinuada pela CO 562/25 — ver docstring.
DATASET = "lista_perfil_v1"

ENCODING = "iso-8859-1"

SIGLA_SUBMERCADO = {
    "NORTE": "N",
    "NORDESTE": "NE",
    "SUL": "S",
    "SUDESTE": "SE",
}
SUBMERCADOS = frozenset(SIGLA_SUBMERCADO.values())

# Os três que a CCEE publica. Status novo sem revisão do contrato de dados
# entraria como dado silenciosamente errado.
STATUS_CONHECIDOS = frozenset({"ATIVO", "ENCERRADO", "PERFIL ESPECIFICO"})


def _limpar(valor: str | None) -> str:
    """Texto da CCEE sem espaço em volta, inclusive o não separável.

    Perfil sem submercado traz `\\xa0`, não string vazia. Sem esta limpeza a
    linha seria rejeitada pelo schema e o cadastro perderia registros sem que
    ninguém entendesse o motivo.
    """
    return (valor or "").replace("\xa0", " ").strip()


class PerfilAgente(BaseModel):
    """Um perfil de agente no cadastro da CCEE.

    Agente e perfil não são a mesma coisa: um agente pode ter vários perfis, e
    é o **perfil** que transaciona na contabilização.
    """

    data_referencia: date
    codigo_agente: str
    agente_ccee: str  # sigla do agente — dimensão comum do projeto
    nome_empresarial: str
    cnpj: str
    codigo_perfil: str
    sigla_perfil: str
    classe_perfil: str
    status_perfil: str
    categoria_agente: str
    submercado: str | None = None
    varejista: bool = False
    tipo_energia: str | None = None

    @field_validator("cnpj")
    @classmethod
    def _cnpj_normalizado(cls, valor: str) -> str:
        digitos = "".join(c for c in valor if c.isdigit())
        if len(digitos) != 14:
            raise ValueError(f"CNPJ deve ter 14 dígitos, veio com {len(digitos)}")
        return digitos

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str | None) -> str | None:
        if valor is None:
            return None
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @field_validator("status_perfil")
    @classmethod
    def _status_conhecido(cls, valor: str) -> str:
        if valor not in STATUS_CONHECIDOS:
            raise ValueError(f"status de perfil desconhecido: {valor}")
        return valor


@registrar
class CceePerfil(Conector):
    """Cadastro completo de perfis. Retrato datado pelo CKAN, não pela janela."""

    fonte = "ccee"
    entidade = "perfil"
    schema = PerfilAgente
    schema_versao = "1"
    max_dias_por_requisicao = None  # cadastro: a janela não se aplica

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    # ------------------------------------------------------------- descoberta

    def _recurso_mais_recente(self) -> tuple[str, date]:
        """URL do recurso mais recente e a data que o CKAN declara para ele."""
        cfg = get_settings()
        resposta = self._sessao.get(CKAN_PACOTE, params={"id": DATASET}, timeout=cfg.http_timeout)
        resposta.raise_for_status()
        recursos = resposta.json()["result"].get("resources", [])
        if not recursos:
            raise FileNotFoundError(f"a CCEE não publica recurso algum em {DATASET}")

        # Nome termina no ano (`lista_perfil_v1_2026`); o maior é o corrente.
        recurso = max(recursos, key=lambda r: str(r.get("name", "")))
        publicado = str(recurso.get("last_modified") or "")[:10]
        try:
            retrato = date.fromisoformat(publicado)
        except ValueError:
            raise ValueError("CCEE perfil: last_modified ausente ou inválido; data do retrato desconhecida") from None
        return str(recurso["url"]), retrato

    def _baixar(self, url: str) -> str:
        resposta = self._sessao.get(url, timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        resposta.encoding = ENCODING
        return resposta.text

    # ---------------------------------------------------------------- extração

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        del janela  # cadastro: o retrato é completo, a janela não recorta
        url, snapshot_date = self._recurso_mais_recente()
        logger.info("CCEE perfil: retrato de %s", snapshot_date.isoformat())

        for linha in csv.DictReader(StringIO(self._baixar(url)), delimiter=";"):
            if _limpar(linha.get("COD_PERF_AGENTE")):
                yield linha | {"_data_retrato": snapshot_date.isoformat()}

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        try:
            snapshot_date = date.fromisoformat(bruto.get("_data_retrato"))
        except (TypeError, ValueError):
            raise ValueError(
                "raw sem data do retrato válida; recuperar metadado original ou realizar nova extração"
            ) from None
        submercado = SIGLA_SUBMERCADO.get(_limpar(bruto.get("SUBMERCADO")).upper())

        return {
            "data_referencia": snapshot_date,
            "codigo_agente": _limpar(bruto.get("COD_AGENTE")),
            "agente_ccee": _limpar(bruto.get("SIGLA_AGENTE")),
            "nome_empresarial": _limpar(bruto.get("NOME_EMPRESARIAL")),
            "cnpj": _limpar(bruto.get("CNPJ")),
            "codigo_perfil": _limpar(bruto.get("COD_PERF_AGENTE")),
            "sigla_perfil": _limpar(bruto.get("SIGLA_PERFIL_AGENTE")),
            "classe_perfil": _limpar(bruto.get("CLASSE_PERFIL_AGENTE")),
            "status_perfil": _limpar(bruto.get("STATUS_PERFIL")).upper(),
            "categoria_agente": _limpar(bruto.get("CATEGORIA_AGENTE")),
            "submercado": submercado,
            "varejista": _limpar(bruto.get("VAREJISTA")).lower().startswith("s"),
            "tipo_energia": _limpar(bruto.get("TIPO_ENERG_PERF")) or None,
        }
