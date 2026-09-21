"""Conector TempoOK — previsão de ENA (ENA-PREVS), um tar.gz por dia (Onda 2, exige token).

Fonte: `https://storage.tempook.com/tokstorage/download_post/`, pasta
`Comercializadora/Arquivos/ENA-PREVS/`. Mecânica e contrato em
`tempook_arquivos` (ADR 019).

**É o produto do TempoOK que está em dia.** O acervo de boletins alcançável pelo
token termina em 26/10/2022 (#129); o ENA-PREVS responde para 15/09/2026, e a
sondagem de 21/09 achou 43 de 45 dias consecutivos — diário, inclusive sábado
e domingo. Os buracos são pontuais e **todos em sábado** (15/08, 05/09 e 19/09,
devolvendo 404). O acervo começa em ~17/11/2024, e o arquivo do dia só aparece
depois das 11h: às 10h56 de 21/09, o de 20/09 estava lá e o de 21/09 não.

O que a Alup entregou (18/09) foi **um caminho de exemplo**, não a lista dos que
importam: "nós vamos pegar aqui o caminho dos arquivos que precisamos". Por isso
o modelo é coluna da tabela e `MODELOS` é a única lista a estender quando a Alup
indicar os demais — o Bronze é append-only, e cada caminho novo pediria mudança
de schema se o modelo não estivesse lá desde o começo.

O que há dentro do tar.gz, verificado em 21/09 (só nomes e tamanhos; o conteúdo
não é versionado): 7 arquivos `.txt` de ~93 KB, um por revisão do PMO
(`2026_9_rev2`, `2026_9_rev3`, `2026_10_rev0` … `2026_10_rev4`), cada um com uma
tabela de ENA por subsistema e semana. **Este conector não abre o tar.gz** — extrair
os números é escopo futuro, e depende de a Alup dizer quais importam.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from src.conectores.tempook_arquivos import ArquivoTempook, TempookArquivos
from src.core.registry import registrar

if TYPE_CHECKING:
    from datetime import date

__all__ = [
    "ASSINATURA_GZIP",
    "CONTENT_TYPE",
    "MODELOS",
    "PASTA",
    "ArquivoEnaPrevs",
    "TempookEnaPrevs",
    "caminho_do_dia",
]

PASTA = "Comercializadora/Arquivos/ENA-PREVS"

# (pasta do conjunto de modelos, nome do modelo no arquivo). Só a primeira
# combinação é conhecida — veio no exemplo da Alup. Outras entram aqui quando a
# Alup indicar os caminhos; o resto do conector não muda.
MODELOS: tuple[tuple[str, str], ...] = (("ECENSav-ETA40-GEFSav-ECENS45_upt", "ECENSav-ETA40-GEFSav-ECENS45-av_upt"),)

NOME = "ENA-PREVS_{modelo}_{dia:%Y%m%d}.tar.gz"

ASSINATURA_GZIP = b"\x1f\x8b"

# O servidor devolve `application/octet-stream`; o que o arquivo é, é gzip.
CONTENT_TYPE = "application/gzip"


def caminho_do_dia(dia: date, combinacao: tuple[str, str] = MODELOS[0]) -> str:
    """Caminho do arquivo de um modelo naquele dia. A pasta de mês é a do próprio arquivo.

    Sem `combinacao`, vale a única conhecida — a do exemplo da Alup.
    """
    conjunto, modelo = combinacao
    return f"{PASTA}/{conjunto}/{modelo}/{dia:%Y-%m}/{NOME.format(modelo=modelo, dia=dia)}"


class ArquivoEnaPrevs(ArquivoTempook):
    """Um tar.gz diário de previsão de ENA — catálogo, não conteúdo."""

    modelo: str = Field(description="Combinação de modelos, como aparece no nome do arquivo")


@registrar
class TempookEnaPrevs(TempookArquivos):
    """Um tar.gz por modelo e por dia da janela. Dia sem arquivo é aviso, não falha.

    Diferente do boletim, **não pula fim de semana**: o produto é diário.
    """

    entidade = "ena_prevs"
    schema = ArquivoEnaPrevs
    assinatura = ASSINATURA_GZIP
    content_type = CONTENT_TYPE

    def caminho_do_dia(self, dia: date) -> str:
        return caminho_do_dia(dia)

    def caminhos_do_dia(self, dia: date) -> list[str]:
        return [caminho_do_dia(dia, combinacao) for combinacao in MODELOS]

    def _registro(self, dia: date, caminho: str, nome: str, conteudo: bytes, uri: str | None) -> dict[str, Any]:
        registro = super()._registro(dia, caminho, nome, conteudo, uri)
        # O modelo é o penúltimo segmento antes da pasta do mês: .../<modelo>/<AAAA-MM>/<arquivo>
        registro["modelo"] = caminho.split("/")[-3]
        return registro
