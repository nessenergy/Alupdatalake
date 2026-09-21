"""Conector TempoOK — boletins diários em PDF (Onda 2, exige token).

Mecânica, contrato e a razão de não reproduzir o `verify=False` do exemplo da
Alup estão em `tempook_arquivos` (ADR 019). Aqui só o que é do boletim:

- o caminho, derivado do único exemplo conhecido (14/09/2026);
- a assinatura de PDF. Endpoint de download que devolve 200 com página de erro é
  comum; sem esta conferência o lake arquivaria HTML de erro como se fosse
  boletim (ADR 019, item 4).

Escrito **sem token**, como o `hubspot_negocios`: a credencial era pendência da
Alup (A7). O que não pôde ser verificado está no fim de
`docs/dicionario-dados/tempook_boletins.md`.

Atenção ao alcance: o token entregue em 14/09 só alcança boletins até
26/10/2022 (#129). O produto que está em dia é o ENA-PREVS
(`tempook_ena_prevs`), recebido em 18/09 e verificado em 21/09.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.conectores.tempook_arquivos import URL, ArquivoTempook, TempookArquivos
from src.core.registry import registrar

if TYPE_CHECKING:
    from datetime import date

__all__ = ["ASSINATURA_PDF", "CONTENT_TYPE", "NOME", "PASTA", "URL", "Boletim", "TempookBoletins", "caminho_do_dia"]

# Template do caminho na origem, derivado do único exemplo conhecido:
#   Comercializadora/Boletins/Diario/2022-03/boletim_TOK_2022-03-31.pdf
PASTA = "Comercializadora/Boletins/Diario"
NOME = "boletim_TOK_{dia}.pdf"

ASSINATURA_PDF = b"%PDF-"

CONTENT_TYPE = "application/pdf"


def caminho_do_dia(dia: date) -> str:
    """Caminho do boletim daquele dia na origem."""
    return f"{PASTA}/{dia:%Y-%m}/{NOME.format(dia=dia.isoformat())}"


class Boletim(ArquivoTempook):
    """Um boletim diário arquivado — catálogo, não conteúdo (ver `ArquivoTempook`)."""


@registrar
class TempookBoletins(TempookArquivos):
    """Um boletim por dia da janela. Dia sem boletim é aviso, não falha."""

    entidade = "boletins"
    schema = Boletim
    assinatura = ASSINATURA_PDF
    content_type = CONTENT_TYPE

    def caminho_do_dia(self, dia: date) -> str:
        return caminho_do_dia(dia)
