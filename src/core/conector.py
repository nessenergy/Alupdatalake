"""Contrato que toda fonte de dados do AlupData implementa.

Um conector novo descreve apenas *como falar com a fonte*. Colunas técnicas,
gravação do raw, validação, carga no Bronze e log de execução são do runner.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ValidationError

from src.core.bigquery import carregar_bronze, registrar_execucao
from src.core.execucao import Execucao, Janela
from src.core.storage import gravar_raw

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class Conector(ABC):
    """Base de todos os conectores.

    Atributos de classe:
        fonte: identificador curto da fonte (`bcb`, `ccee`, `ons`).
        entidade: o que está sendo ingerido (`cambio_ptax`, `precos`).
        schema: modelo Pydantic que valida um registro já transformado.
        schema_versao: muda quando o contrato da fonte muda.
        max_dias_por_requisicao: limite de janela da fonte, quando houver.
    """

    fonte: str
    entidade: str
    schema: type[BaseModel]
    schema_versao: str = "1"
    max_dias_por_requisicao: int | None = None

    @abstractmethod
    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        """Devolve os registros brutos da fonte para a janela pedida."""

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        """Ajusta o registro bruto ao schema. Padrão: identidade."""
        return bruto

    # ------------------------------------------------------------------ runner

    def _colunas_tecnicas(self, execucao: Execucao) -> dict[str, Any]:
        return {
            "_ingestao_id": execucao.ingestao_id,
            "_ingestao_timestamp": datetime.now(UTC).isoformat(),
            "_fonte": self.fonte,
            "_schema_versao": self.schema_versao,
        }

    def _janelas(self, janela: Janela) -> list[Janela]:
        if self.max_dias_por_requisicao is None:
            return [janela]
        return janela.particionar(self.max_dias_por_requisicao)

    def ingerir(self, janela: Janela) -> Execucao:
        """Executa o ciclo completo: extrai, valida, grava raw, carrega, registra."""
        execucao = Execucao(fonte=self.fonte, entidade=self.entidade, janela=janela)
        logger.info("[%s] ingestão %s janela=%s", self.rotulo, execucao.ingestao_id, janela)

        try:
            brutos: list[dict[str, Any]] = []
            for pedaco in self._janelas(janela):
                brutos.extend(self.extrair(pedaco))
            execucao.linhas_extraidas = len(brutos)

            gravar_raw(execucao, brutos)

            tecnicas = self._colunas_tecnicas(execucao)
            linhas: list[dict[str, Any]] = []
            for bruto in brutos:
                try:
                    validado = self.schema.model_validate(self.transformar(bruto))
                except ValidationError as exc:
                    execucao.linhas_invalidas += 1
                    logger.warning("[%s] registro inválido descartado: %s", self.rotulo, exc.errors()[:1])
                    continue
                linhas.append(validado.model_dump(mode="json") | tecnicas)

            execucao.linhas_carregadas = carregar_bronze(execucao, linhas)
            execucao.encerrar()
        except Exception as exc:  # noqa: BLE001 — a execução precisa ser registrada como ERRO
            execucao.encerrar(erro=f"{type(exc).__name__}: {exc}")
            registrar_execucao(execucao)
            raise

        registrar_execucao(execucao)
        logger.info(
            "[%s] %s: %d extraídos, %d inválidos, %d carregados em %.1fs",
            self.rotulo,
            execucao.status,
            execucao.linhas_extraidas,
            execucao.linhas_invalidas,
            execucao.linhas_carregadas,
            execucao.duracao_segundos or 0.0,
        )
        return execucao

    @property
    def rotulo(self) -> str:
        """`fonte_entidade` — o nome pelo qual o conector é registrado e chamado."""
        return f"{self.fonte}_{self.entidade}"
