"""Base de conector para planilha — S2 Data Intake (Onda 4, tarefa 4.1).

Uma fonte de planilha declara o template e o schema; o resto (raw no GCS,
validação, colunas técnicas, carga, log) é do runner de `src/core/conector.py`,
igual a qualquer outra fonte.

    @registrar
    class MedicaoManual(ConectorPlanilha):
        fonte = "s2"
        entidade = "medicao_manual"
        schema = MedicaoRegistro
        template = TemplatePlanilha(
            colunas={"Data": "data_referencia", "MWh": "energia_mwh"},
            colunas_decimais=frozenset({"energia_mwh"}),
        )

Os templates concretos dependem do Questionário de Gaps (pendência A4) e das
planilhas reais da Alup. O motor não depende de nenhum dos dois.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from src.core.conector import Conector
from src.core.planilha import TemplatePlanilha, ler_tabela

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)


class ConectorPlanilha(Conector):
    """Conector cuja origem é um arquivo, não uma API.

    A janela não filtra a leitura: planilha é entregue fechada, e quem decide o
    recorte é quem a produziu. A janela continua identificando a execução e
    particionando o raw no GCS.
    """

    template: TemplatePlanilha
    caminho: Path | str

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        logger.info("[%s] lendo %s (janela %s)", self.rotulo, self.caminho, janela)
        yield from ler_tabela(self.caminho, self.template)
