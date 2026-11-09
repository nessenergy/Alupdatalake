"""Conector CCEE Plataforma de Integração — cadastro de pontos de medição (retrato).

Fonte: serviço SOAP `PontoMedicaoBSv2`, operação `listarPontoMedicao` ("Listar pontos de medição por agente
relacionado"), catalogada em `docs/dicionario-dados/ccee_plataforma_integracao.md`.

É um **retrato**, sem janela: o cadastro devolve os pontos em que o agente da credencial tem relação (conectado,
conectante, medição ou uso do fio), com o perfil de cada agente, que o `listarMedida` exige no cabeçalho. A janela só
dá a data do retrato (`data_referencia` = fim da janela); quem decide "hoje" é quem chama.

Uma linha por ponto e agente relacionado. Ponto sem agente relacionado vira uma linha com os campos do agente nulos,
para o ponto não sumir do cadastro. Cadastro vazio falha alto: seria credencial sem relação, não um dia sem pontos.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from src.conectores.ccee_pi_sessao import NS_BO2, abrir_sessao, pontos_medicao
from src.core.conector import Conector
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator
    from xml.etree.ElementTree import Element  # nosec B405 - só tipo; o XML é lido com defusedxml

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)


def _t(elemento: Element, caminho: str) -> str | None:
    """Texto do primeiro descendente `bo:<caminho>`, com `/` entre níveis; None se não existir."""
    achado = elemento.find("/".join(f"{{{NS_BO2}}}{parte}" for parte in caminho.split("/")))
    texto = (achado.text or "").strip() if achado is not None else ""
    return texto or None


class CceePiPontoMedicaoRegistro(BaseModel):
    """Um ponto de medição e um agente relacionado a ele, com o perfil do agente."""

    data_referencia: date
    ponto_codigo: str
    ponto_nome: str | None = None
    tipo_coleta: str | None = None
    tipo_relacao: str | None = None
    perfil_codigo: str | None = None
    agente_nome: str | None = None


@registrar
class CceePiPontoMedicao(Conector):
    fonte = "ccee_pi"
    entidade = "ponto_medicao"
    schema = CceePiPontoMedicaoRegistro
    schema_versao = "1"
    max_dias_por_requisicao = None  # retrato: a janela não se aplica

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        total = 0
        for ponto in pontos_medicao(abrir_sessao()):
            total += 1
            base = {
                "data_referencia": janela.fim.isoformat(),
                "ponto_codigo": _t(ponto, "codigo"),
                "ponto_nome": _t(ponto, "nome"),
                "tipo_coleta": _t(ponto, "tipoColeta/codigo"),
            }
            agentes = ponto.findall(f"{{{NS_BO2}}}agentesRelacionados/{{{NS_BO2}}}participanteMercadoRelacionado")
            if not agentes:
                yield {**base, "tipo_relacao": None, "perfil_codigo": None, "agente_nome": None}
            for agente in agentes:
                yield {
                    **base,
                    "tipo_relacao": _t(agente, "tipoRelacao/nome"),
                    "perfil_codigo": _t(agente, "perfis/perfil/codigo"),
                    "agente_nome": _t(agente, "parte/pessoaJuridica/nomeEmpresarial"),
                }
        if total == 0:
            raise RuntimeError("o cadastro da CCEE não devolveu nenhum ponto de medição")
        logger.info("cadastro de pontos da CCEE: %d pontos", total)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return bruto  # o parsing já normaliza; o Pydantic valida e converte a data
