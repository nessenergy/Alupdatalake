"""Conector ONS — constrained-off de usinas fotovoltaicas (Onda 1, público).

Mesmas 24 colunas da eólica, conferido contra o arquivo de agosto/2026: schema
e extração vivem em `ons_restricao_coff`. Volume verificado: 121.536 linhas, 83
usinas, no mesmo mês.
"""

from __future__ import annotations

from src.conectores.ons_restricao_coff import OnsRestricaoCoff
from src.core.registry import registrar


@registrar
class OnsRestricaoCoffFotovoltaica(OnsRestricaoCoff):
    """Constrained-off fotovoltaico, de meia em meia hora, um CSV por mês."""

    entidade = "restricao_coff_fotovoltaica"
    url_mes = (
        "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_fotovoltaica_tm/"
        "RESTRICAO_COFF_FOTOVOLTAICA_{ano}_{mes:02d}.csv"
    )
