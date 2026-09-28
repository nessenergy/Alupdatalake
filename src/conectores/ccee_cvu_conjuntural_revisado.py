"""Conector CCEE — CVU conjuntural revisado por agente vendedor (Aditivo 01, público). Item 22.

Fonte: dados abertos da CCEE (CKAN), dataset `custo_variavel_unitario_conjuntural_revisado`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/custo_variavel_unitario_conjuntural_revisado

O CVU conjuntural depois da revisão de preço de combustível do mês (ADR 016):
mesmo layout do `custo_variavel_unitario_conjuntural`, publicado como dataset
próprio pela CCEE, não como nova versão do mesmo recurso — por isso é um
conjunto separado, não um replay do item 21. Schema e transformação vêm de
`ccee_cvu_conjuntural`.
"""

from __future__ import annotations

from src.conectores.ccee_ckan import CceeCsvCkan
from src.conectores.ccee_cvu_conjuntural import CvuConjuntural, transformar_cvu_conjuntural
from src.core.registry import registrar


@registrar
class CceeCvuConjunturalRevisado(CceeCsvCkan):
    """CVU conjuntural revisado por agente vendedor. CSV por ano, delimitado por vírgula."""

    dataset = "custo_variavel_unitario_conjuntural_revisado"
    entidade = "cvu_conjuntural_revisado"
    schema = CvuConjuntural
    delimitador = ","

    transformar = staticmethod(transformar_cvu_conjuntural)
