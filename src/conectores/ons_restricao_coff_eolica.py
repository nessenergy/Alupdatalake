"""Conector ONS — constrained-off de usinas eólicas (Onda 1, público).

Só a URL e o rótulo mudam; schema e extração vivem em `ons_restricao_coff`.
Volume verificado: 227.664 linhas e 46 MB no mês de agosto/2026, 153 usinas e
conjuntos, nos quatro submercados — o Nordeste concentra 90% das linhas.
"""

from __future__ import annotations

from src.conectores.ons_restricao_coff import OnsRestricaoCoff
from src.core.registry import registrar


@registrar
class OnsRestricaoCoffEolica(OnsRestricaoCoff):
    """Constrained-off eólico, de meia em meia hora, um CSV por mês."""

    entidade = "restricao_coff_eolica"
    url_mes = (
        "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_eolica_tm/"
        "RESTRICAO_COFF_EOLICA_{ano}_{mes:02d}.csv"
    )
