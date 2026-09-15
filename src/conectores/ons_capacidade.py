"""Conector ONS — capacidade instalada por unidade geradora (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `capacidade-geracao`, recurso único (sem ano
nem mês — não é série).
Documentação: https://dados.ons.org.br/dataset/capacidade-geracao

Terceiro cadastro do projeto (depois de `aneel_siga` e `ccee_perfil`): a API
devolve o retrato corrente, sem parâmetro de período — a janela é ignorada
(ADR 013) e `data_referencia` vem de fora do corpo do CSV, como nos outros
dois. A diferença é a origem: o ONS publica direto no S3, sem catálogo CKAN
nem campo de data no próprio registro (ao contrário do `DatGeracaoConjuntoDados`
do `aneel_siga`), então o retrato é datado pelo cabeçalho `Last-Modified` que o
próprio S3 devolve — o mesmo papel que o `last_modified` do CKAN cumpre para o
`ccee_perfil`.

Junto do `ons_geracao_usina`, é a segunda fonte a trazer a coluna `ceg`: a
issue #141 pede um de-para de quatro colunas (sigla interna ↔ CEG ↔ nome CCEE
↔ nome ONS) que hoje só o `aneel_siga` alimenta pelo lado CEG. Estas duas
fontes entregam o lado CEG ↔ nome ONS sem depender de ninguém — ver o
dicionário de dados.

`id_subsistema` traz uma quinta sigla além de N/NE/S/SE: `PY`, a metade
paraguaia de Itaipu (10 unidades geradoras, 7.000 MW). Diferente do
`ons_carga`, onde submercado é a chave do fato (consumo *de* um submercado) e
sigla fora da lista é dado que não deveria existir, aqui submercado é atributo
de localização de um ativo — e um ativo fora dos quatro submercados continua
sendo um ativo do cadastro. Por isso `PY` não vira `linhas_invalidas`: vira
`submercado = NULL`, e o ativo entra no lake. Ver o dicionário de dados.
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from decimal import Decimal
from email.utils import parsedate_to_datetime
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_carga import SUBMERCADOS
from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

URL = "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/capacidade-geracao/CAPACIDADE_GERACAO.csv"

# A interligação com o Paraguai (a metade paraguaia de Itaipu) não é submercado
# do SIN; o ONS a identifica com esta sigla no mesmo campo. Não é sigla
# desconhecida por erro — é o ativo binacional, e vira `submercado = NULL`,
# não linha inválida.
SIGLA_ITAIPU_PARAGUAI = "PY"

logger = logging.getLogger(__name__)


def _texto_ou_nulo(valor: str | None) -> str | None:
    """Vazio ou "-" na origem é ausência de CEG, não um valor literal."""
    texto = (valor or "").strip()
    return texto if texto and texto != "-" else None


def _data_ou_nula(valor: str | None) -> str | None:
    """As três datas do cadastro (teste, operação, desativação) quase sempre vêm vazias."""
    texto = (valor or "").strip()
    return texto or None


class Capacidade(BaseModel):
    """Capacidade instalada de uma unidade geradora, no retrato corrente do ONS."""

    data_referencia: date
    submercado: str | None  # NULL para PY — a metade paraguaia de Itaipu não é submercado do SIN
    nome_subsistema: str
    uf: str
    nome_uf: str
    modalidade_operacao: str
    agente_proprietario: str
    agente_operador: str
    tipo_usina: str
    nome_usina: str
    codigo_usina: str | None = None  # CEG — dimensão comum do projeto (achado #141)
    nome_unidade_geradora: str
    codigo_equipamento: str
    numero_unidade_geradora: str
    combustivel: str
    data_entrada_teste: date | None = None
    data_entrada_operacao: date | None = None
    data_desativacao: date | None = None
    potencia_efetiva: Decimal  # unidade não confirmada pela fonte no catálogo público

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido_ou_itaipu_paraguai(cls, valor: str) -> str | None:
        """N/NE/S/SE viram a sigla; `PY` (Itaipu, lado paraguaio) vira NULL —
        é ativo do cadastro, não consumo de um submercado que não existe.
        Qualquer outra sigla segue rejeitada: aí é a origem mudando o contrato."""
        sigla = valor.strip().upper()
        if sigla == SIGLA_ITAIPU_PARAGUAI:
            return None
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator("codigo_usina", mode="before")
    @classmethod
    def _ceg_ou_nulo(cls, valor: str | None) -> str | None:
        return _texto_ou_nulo(valor)

    @field_validator("data_entrada_teste", "data_entrada_operacao", "data_desativacao", mode="before")
    @classmethod
    def _data_vazia_e_nula(cls, valor: str | None) -> str | None:
        return _data_ou_nula(valor)


@registrar
class OnsCapacidade(Conector):
    """Cadastro de capacidade instalada por unidade geradora. Retrato datado pelo Last-Modified do S3."""

    fonte = "ons"
    entidade = "capacidade"
    schema = Capacidade
    schema_versao = "1"
    max_dias_por_requisicao = None  # cadastro: a janela não se aplica

    def __init__(self) -> None:
        self._sessao = criar_sessao()
        self._data_retrato: date | None = None

    @staticmethod
    def _data_do_cabecalho(valor: str | None) -> date:
        """`Last-Modified` do S3 → data do retrato. Sem o cabeçalho, assume hoje
        e avisa — o mesmo comportamento do `ccee_perfil` sem `last_modified`."""
        if valor:
            try:
                return parsedate_to_datetime(valor).date()
            except (TypeError, ValueError):
                pass
        hoje = datetime.now().date()
        logger.warning("ONS capacidade: recurso sem Last-Modified; data_referencia assumida como %s", hoje)
        return hoje

    def _baixar(self) -> tuple[str, date]:
        """Texto do CSV e a data do retrato. É o seam dos testes."""
        resposta = self._sessao.get(URL, timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return resposta.text, self._data_do_cabecalho(resposta.headers.get("Last-Modified"))

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        del janela  # cadastro: o retrato é completo, a janela não recorta
        texto, data_retrato = self._baixar()
        self._data_retrato = data_retrato
        logger.info("ONS capacidade: retrato de %s", data_retrato.isoformat())
        yield from csv.DictReader(StringIO(texto), delimiter=";")

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": self._data_retrato,
            "submercado": bruto.get("id_subsistema", ""),
            "nome_subsistema": bruto.get("nom_subsistema", "").strip(),
            "uf": bruto.get("id_estado", "").strip(),
            "nome_uf": bruto.get("nom_estado", "").strip(),
            "modalidade_operacao": bruto.get("nom_modalidadeoperacao", "").strip(),
            "agente_proprietario": bruto.get("nom_agenteproprietario", "").strip(),
            "agente_operador": bruto.get("nom_agenteoperador", "").strip(),
            "tipo_usina": bruto.get("nom_tipousina", "").strip(),
            "nome_usina": bruto.get("nom_usina", "").strip(),
            "codigo_usina": bruto.get("ceg"),
            "nome_unidade_geradora": bruto.get("nom_unidadegeradora", "").strip(),
            "codigo_equipamento": bruto.get("cod_equipamento", "").strip(),
            "numero_unidade_geradora": bruto.get("num_unidadegeradora", "").strip(),
            "combustivel": bruto.get("nom_combustivel", "").strip(),
            "data_entrada_teste": bruto.get("dat_entradateste"),
            "data_entrada_operacao": bruto.get("dat_entradaoperacao"),
            "data_desativacao": bruto.get("dat_desativacao"),
            "potencia_efetiva": bruto.get("val_potenciaefetiva"),
        }
