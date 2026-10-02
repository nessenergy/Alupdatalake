"""Conector ANEEL — tarifas homologadas das distribuidoras de energia elétrica (Onda 1, público).

Fonte: Dados Abertos ANEEL (CKAN), dataset `tarifas-distribuidoras-energia-eletrica`,
recurso `tarifas-homologadas-distribuidoras-energia-eletrica.csv`.
Documentação: https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica

O recurso é **um arquivo único, reescrito inteiro** a cada atualização (89 MB, 328 mil
linhas em 02/10/2026, desde 2010-02-03), sem parâmetro de período. Por isso a janela
**recorta na extração**: fica a linha cujo `DatInicioVigencia` cai dentro da janela e o
resto é descartado. Reprocessar é passar outra janela. Uma vigência que começou antes da
janela e ainda vale **não** entra: quem quer a carga completa passa a janela desde
2010-02-03 (recarga), e a execução recorrente usa uma janela de um ciclo tarifário
inteiro para apanhar correção de vigência recente (ver `infra/modules/scheduler`).

O que o arquivo real impõe (`docs/dicionario-dados/aneel_tarifas.md`):

1. **Separador `;`, tudo entre aspas, UTF-8, CRLF.** Valores com vírgula decimal e sem
   milhar; o zero é escrito `,00` (`decimal_br` lê como 0).
2. **`Não se aplica` é texto**, não vazio, em classe, subclasse, detalhe, posto e
   acessante. O Bronze guarda como veio; a Silver o troca por NULL.
3. **A mesma chave natural aparece mais de uma vez** (resoluções que se sobrepõem,
   tarifas nominais): o conector não escolhe, entrega tudo; a Silver guarda a versão
   mais recente de cada linha e a Gold resolve a vigência.
4. **Download em stream**, linha a linha, sem nunca ter o arquivo inteiro em memória.
"""

from __future__ import annotations

import csv
import logging
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.conectores.ccee_ckan import decodificar
from src.core.conector import Conector
from src.core.http import criar_sessao
from src.core.planilha import decimal_br
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    import requests

    from src.core.execucao import Janela

URL = (
    "https://dadosabertos.aneel.gov.br/dataset/5a583f3e-1646-4f67-bf0f-69db4203e89e/resource/"
    "fcf2906c-7c32-4b9b-a637-054e7a5234f4/download/tarifas-homologadas-distribuidoras-energia-eletrica.csv"
)
_BLOCO_DO_STREAM = 1 << 16
COLUNAS = (
    "DatGeracaoConjuntoDados",
    "DscREH",
    "SigAgente",
    "NumCNPJDistribuidora",
    "DatInicioVigencia",
    "DatFimVigencia",
    "DscBaseTarifaria",
    "DscSubGrupo",
    "DscModalidadeTarifaria",
    "DscClasse",
    "DscSubClasse",
    "DscDetalhe",
    "NomPostoTarifario",
    "DscUnidadeTerciaria",
    "SigAgenteAcessante",
    "VlrTUSD",
    "VlrTE",
)

logger = logging.getLogger(__name__)


def _nulo_se_vazio(valor: str | None) -> str | None:
    texto = (valor or "").strip()
    return texto or None


class Tarifa(BaseModel):
    """Uma tarifa (TUSD e TE) de uma distribuidora, para uma combinação tarifária e uma vigência."""

    data_referencia: date  # DatInicioVigencia: é por ela que a janela recorta
    data_geracao: date  # DatGeracaoConjuntoDados: o dia em que a ANEEL gerou o arquivo
    fim_vigencia: date
    reh: str | None = None  # resolução homologatória ou despacho; vazio em 274 linhas
    sigla_distribuidora: str
    cnpj_distribuidora: str
    base_tarifaria: str  # `Tarifa de Aplicação` ou `Base Econômica`
    subgrupo: str
    modalidade: str
    classe: str
    subclasse: str
    detalhe: str
    posto: str
    unidade: str  # `kW` ou `MWh`: a grandeza da TUSD; a TE é sempre R$/MWh
    acessante: str | None = None  # tarifa nominal; vazio em 22 linhas
    tusd: Decimal | None = None
    te: Decimal | None = None

    @field_validator("cnpj_distribuidora")
    @classmethod
    def _cnpj_de_catorze_digitos(cls, valor: str) -> str:
        texto = valor.strip()
        if not (len(texto) == 14 and texto.isdigit()):
            raise ValueError(f"CNPJ fora de 14 dígitos: {valor!r}")
        return texto

    @field_validator("sigla_distribuidora", "base_tarifaria", "subgrupo", "modalidade", "unidade")
    @classmethod
    def _obrigatorio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("campo obrigatório vazio")
        return valor.strip()


@registrar
class AneelTarifas(Conector):
    """Tarifas homologadas: o arquivo inteiro em stream, recortado pela janela de início de vigência."""

    fonte = "aneel"
    entidade = "tarifas"
    schema = Tarifa
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é feito no arquivo, não por requisição

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _abrir(self) -> Iterator[str]:
        """Linhas do CSV, decodificadas uma a uma."""
        from src.core.config import get_settings

        resposta = self._sessao.get(URL, timeout=get_settings().http_timeout, stream=True)
        try:
            resposta.raise_for_status()
        except Exception:
            resposta.close()
            raise
        return _linhas(resposta)

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        leitor = csv.DictReader(self._abrir(), delimiter=";")
        if not leitor.fieldnames:
            raise ValueError("aneel/tarifas: arquivo vazio, sem cabeçalho")
        faltam = [c for c in COLUNAS if c not in leitor.fieldnames]
        if faltam:
            raise ValueError(f"aneel/tarifas: o cabeçalho mudou, faltam colunas: {', '.join(faltam)}")
        lidas = 0
        for linha in leitor:
            lidas += 1
            if janela.inicio.isoformat() <= (linha["DatInicioVigencia"] or "") <= janela.fim.isoformat():
                yield linha
        logger.info("aneel/tarifas: %d linhas lidas no arquivo, janela %s a %s", lidas, janela.inicio, janela.fim)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": bruto["DatInicioVigencia"],
            "data_geracao": bruto["DatGeracaoConjuntoDados"],
            "fim_vigencia": bruto["DatFimVigencia"],
            "reh": _nulo_se_vazio(bruto["DscREH"]),
            "sigla_distribuidora": bruto["SigAgente"],
            "cnpj_distribuidora": bruto["NumCNPJDistribuidora"],
            "base_tarifaria": bruto["DscBaseTarifaria"],
            "subgrupo": bruto["DscSubGrupo"],
            "modalidade": bruto["DscModalidadeTarifaria"],
            "classe": bruto["DscClasse"],
            "subclasse": bruto["DscSubClasse"],
            "detalhe": bruto["DscDetalhe"],
            "posto": bruto["NomPostoTarifario"],
            "unidade": bruto["DscUnidadeTerciaria"],
            "acessante": _nulo_se_vazio(bruto["SigAgenteAcessante"]),
            "tusd": decimal_br(bruto["VlrTUSD"]),
            "te": decimal_br(bruto["VlrTE"]),
        }


def _linhas(resposta: requests.Response) -> Iterator[str]:
    """Linhas decodificadas, fechando a conexão ao fim (ou se o consumidor abandonar)."""
    with resposta:
        for numero, linha in enumerate(resposta.iter_lines(chunk_size=_BLOCO_DO_STREAM)):
            texto = decodificar(linha)
            yield texto.lstrip("﻿") if numero == 0 else texto
