"""Conector CCEE Plataforma de Integração — medição horária final por ponto.

Fonte: serviço SOAP `ListarMedidaBSv1`, operação `listarMedida` com `tipoMedida` FINAL, uma medida por hora e por
ponto (geração e consumo, ativos e reativos). Catálogo: `docs/dicionario-dados/ccee_plataforma_integracao.md`.

Os pontos e o perfil de cada um vêm do cadastro (`ccee_pi_ponto_medicao`), pela Gold `perfil_vigente_ponto_medicao`:
o guia da CCEE manda usar o perfil do agente principal do ponto, e o cadastro o devolve. Ponto sem perfil é pulado
e contado no log (o código do ponto é dado de cliente e não vai ao log). Sem nenhum ponto o conector falha alto: seria o
cadastro ainda não carregado, e não um dia sem medição.

A hora termina no horário informado (`fim_periodo`), em -03:00: a medida das 00:00 é a energia da última hora do dia
anterior. `data_referencia` é o dia da hora medida, não o do fim do período.
"""

from __future__ import annotations

import dataclasses
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from src.conectores.ccee_pi_sessao import NS_BO1, abrir_sessao, listar_medidas
from src.core.conector import Conector
from src.core.config import get_settings
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator
    from xml.etree.ElementTree import Element  # nosec B405 - só tipo; o XML é lido com defusedxml

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

TIPO_MEDIDA = "FINAL"


def _pontos_com_perfil() -> list[tuple[str, str | None]]:
    """Ponto e perfil para medição de cada ponto do retrato mais recente do cadastro (Gold)."""
    from src.core.bigquery import cliente

    cfg = get_settings()
    tabela = f"{cfg.gcp_project_id}.{cfg.bq_dataset_gold}.perfil_vigente_ponto_medicao"
    linhas = cliente().query(f"SELECT ponto_codigo, perfil_para_medicao FROM `{tabela}`").result()  # noqa: S608  # nosec B608
    return [(linha["ponto_codigo"], linha["perfil_para_medicao"]) for linha in linhas]


def _texto(medida: Element, caminho: str) -> str | None:
    achado = medida.find("/".join(f"{{{NS_BO1}}}{parte}" for parte in caminho.split("/")))
    texto = (achado.text or "").strip() if achado is not None else ""
    return texto or None


class CceePiMedidaRegistro(BaseModel):
    """Uma hora de medição de um ponto, com os quatro valores de energia."""

    data_referencia: date
    ponto_codigo: str
    tipo_medida: str
    fim_periodo: datetime
    sub_tipo: str | None = None
    status: str | None = None
    geracao_ativa: Decimal | None = None
    geracao_reativa: Decimal | None = None
    consumo_ativo: Decimal | None = None
    consumo_reativo: Decimal | None = None


@registrar
class CceePiMedida(Conector):
    fonte = "ccee_pi"
    entidade = "medida"
    schema = CceePiMedidaRegistro
    schema_versao = "1"
    # ponytail: o limite de período por chamada não está documentado; 31 dias é conservador e o runner fatia a janela.
    max_dias_por_requisicao = 31

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        pontos = _pontos_com_perfil()
        if not pontos:
            raise RuntimeError("nenhum ponto no cadastro da CCEE (ccee_pi_ponto_medicao ainda não carregou?)")
        sessao = abrir_sessao()
        sem_perfil = 0
        for ponto, perfil in pontos:
            if not perfil:
                sem_perfil += 1
                continue
            sessao_do_ponto = dataclasses.replace(sessao, perfil=str(perfil))
            for medida in listar_medidas(
                sessao_do_ponto, ponto, janela.inicio.isoformat(), janela.fim.isoformat(), TIPO_MEDIDA
            ):
                yield {
                    "ponto_codigo": _texto(medida, "pontoMedicao/codigo"),
                    "tipo_medida": TIPO_MEDIDA,
                    "fim_periodo": _texto(medida, "periodo/fim"),
                    "sub_tipo": _texto(medida, "subTipo"),
                    "status": _texto(medida, "status"),
                    "geracao_ativa": _texto(medida, "geracaoAtiva"),
                    "geracao_reativa": _texto(medida, "geracaoReativo"),
                    "consumo_ativo": _texto(medida, "consumoAtivo"),
                    "consumo_reativo": _texto(medida, "consumoReativo"),
                }
        if sem_perfil:
            logger.warning("%d pontos sem perfil para medição foram pulados", sem_perfil)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        # a hora termina em `fim_periodo`: o dia medido é o da hora, uma hora antes do fim
        fim = datetime.fromisoformat(bruto["fim_periodo"])
        return {**bruto, "data_referencia": (fim - timedelta(hours=1)).date()}
