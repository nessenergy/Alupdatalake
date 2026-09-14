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
from src.core.linhagem import emitir as emitir_linhagem
from src.core.observabilidade import contexto_execucao
from src.core.seguranca import sanitizar
from src.core.storage import gravar_raw, identificar_raw, ler_raw

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

    # Execução em curso, para o conector que precisa gravar um artefato da
    # origem além dos registros — o boletim em PDF do TempoOK (ADR 019) grava
    # o arquivo e devolve um ponteiro. Fonte que só devolve registros ignora.
    _execucao: Execucao | None = None

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
        with contexto_execucao(execucao):
            return self._ingerir(execucao, janela)

    def _ingerir(self, execucao: Execucao, janela: Janela) -> Execucao:
        logger.info("[%s] ingestão %s janela=%s", self.rotulo, execucao.ingestao_id, janela)
        self._execucao = execucao

        try:
            brutos: list[dict[str, Any]] = []
            for pedaco in self._janelas(janela):
                brutos.extend(self.extrair(pedaco))
            execucao.linhas_extraidas = len(brutos)

            gravar_raw(execucao, brutos)
            self._validar_e_carregar(execucao, brutos)
            execucao.encerrar()
        except Exception as exc:  # noqa: BLE001 — a execução precisa ser registrada como ERRO
            execucao.encerrar(erro=sanitizar(f"{type(exc).__name__}: {exc}"))
            logger.exception("[%s] ingestão falhou", self.rotulo)  # exc_info alimenta o Error Reporting
            try:
                registrar_execucao(execucao)
            except Exception:  # noqa: BLE001 — preserva a exceção original da ingestão
                logger.critical("[%s] falha adicional ao registrar a execução com erro", self.rotulo, exc_info=True)
            raise

        registrar_execucao(execucao)
        # Replay não passa por aqui: a aresta origem → Bronze já foi registrada
        # pela ingestão original (ADR 013).
        emitir_linhagem(execucao, self.origem_linhagem)
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

    def _validar_e_carregar(self, execucao: Execucao, brutos: list[dict[str, Any]]) -> None:
        tecnicas = self._colunas_tecnicas(execucao)
        linhas: list[dict[str, Any]] = []
        for bruto in brutos:
            try:
                validado = self.schema.model_validate(self.transformar(bruto))
            except ValidationError as exc:
                execucao.linhas_invalidas += 1
                logger.warning(
                    "[%s] registro inválido descartado: %s",
                    self.rotulo,
                    exc.errors(include_input=False)[:1],
                )
                continue
            linhas.append(validado.model_dump(mode="json") | tecnicas)
        execucao.linhas_carregadas = carregar_bronze(execucao, linhas)

    def reprocessar_raw(self, uri: str, janela: Janela) -> Execucao:
        """Revalida e recarrega um raw existente sem acessar a fonte."""
        info = identificar_raw(uri)
        if (info.fonte, info.entidade) != (self.fonte, self.entidade):
            raise ValueError(f"raw pertence a {info.fonte}_{info.entidade}, não a {self.rotulo}")

        execucao = Execucao(
            fonte=self.fonte,
            entidade=self.entidade,
            janela=janela,
            modo="REPLAY",
            origem_ingestao_id=info.ingestao_id,
        )
        with contexto_execucao(execucao):
            logger.info("[%s] replay %s a partir de %s", self.rotulo, execucao.ingestao_id, uri)
            try:
                brutos = ler_raw(uri)
                execucao.linhas_extraidas = len(brutos)
                self._validar_e_carregar(execucao, brutos)
                execucao.encerrar()
            except Exception as exc:  # noqa: BLE001 — registra toda falha do replay
                execucao.encerrar(erro=sanitizar(f"{type(exc).__name__}: {exc}"))
                logger.exception("[%s] replay falhou", self.rotulo)
                try:
                    registrar_execucao(execucao)
                except Exception:  # noqa: BLE001 — preserva a exceção original
                    logger.critical("[%s] falha adicional ao registrar o replay com erro", self.rotulo, exc_info=True)
                raise
            registrar_execucao(execucao)
            return execucao

    @property
    def rotulo(self) -> str:
        """`fonte_entidade` — o nome pelo qual o conector é registrado e chamado."""
        return f"{self.fonte}_{self.entidade}"

    @property
    def origem_linhagem(self) -> str:
        """Nome da origem no Knowledge Catalog (`custom:<este valor>`). Sobrescreva se houver nome melhor."""
        return f"{self.fonte}.{self.entidade}"
