"""Base dos conectores ONS de constrained-off (Onda 1, público).

Fonte: Dados Abertos ONS, datasets `restricao_coff_eolica_tm` e
`restricao_coff_fotovoltaica_tm`. Um CSV por mês, **de meia em meia hora**.
Documentação: https://dados.ons.org.br/dataset/restricao_coff_eolica_usi

Constrained-off é a energia que a usina **poderia** ter gerado e não gerou
porque o sistema a limitou — restrição elétrica, de confiabilidade ou excedente
de energia. Para um gerador renovável é receita que não entrou, e nenhuma outra
fonte pública do lake responde isso: `ons_disponibilidade_usina` cobre só o
parque despachado centralmente (UHE, UTE, UTN), e `ons_geracao_usina` diz o que
foi gerado, não o que deixou de ser.

As duas fontes têm **exatamente as mesmas 24 colunas**, conferido contra os
arquivos de agosto/2026. Por isso o schema e a extração vivem aqui e cada fonte
é uma subclasse que só troca a URL e o rótulo — o mesmo desenho do
`CceeCsvCkan`.

Uma diferença que muda o modelo em relação às outras fontes horárias do ONS:
aqui o passo é de **30 minutos** (1.488 instantes em agosto/2026 = 31 × 48).
Derivar só `hora`, como no `ons_geracao_usina`, colapsaria dois registros
distintos em um. Por isso o instante inteiro é coluna.
"""

from __future__ import annotations

import csv
import logging
from datetime import date, datetime
from decimal import Decimal
from io import StringIO
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.ons_carga import SUBMERCADOS
from src.conectores.ons_geracao_usina import _meses, _texto_ou_nulo
from src.core.ceg import ceg_canonico
from src.core.conector import Conector
from src.core.http import criar_sessao

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

# Metade das meias-horas do arquivo real não tem restrição; todos os campos de
# restrição vêm vazios nessas linhas. Vazio é "não houve restrição", não erro.
_NUMERICOS = (
    "geracao_mw",
    "geracao_limitada_mw",
    "disponibilidade_mw",
    "geracao_referencia_mw",
    "geracao_referencia_final_mw",
    "geracao_nao_realizada_mw",
    "minutos_rel",
    "minutos_cnf",
    "minutos_ene",
    "minutos_restricao",
)
_TEXTOS = (
    "id_ons",
    "razao_restricao",
    "origem_restricao",
    "descricao_restricao",
    "id_ponto_conexao",
    "nome_ponto_conexao",
    "agente_operador",
)


class RestricaoCoff(BaseModel):
    """Uma meia hora de uma usina (ou conjunto) sob restrição de operação.

    `data_referencia` e `instante` são derivados de `din_instante` no
    `model_validator`: timestamp malformado vira `linhas_invalidas`, não crash
    em `transformar()`.
    """

    din_instante: str = Field(exclude=True)  # cru; só deriva data_referencia/instante
    data_referencia: date | None = None
    instante: datetime | None = None
    submercado: str
    nome_subsistema: str
    uf: str
    nome_uf: str
    nome_usina: str
    # O identificador que sempre existe. O CEG não serve de chave aqui: só
    # 7,2% das linhas de agosto/2026 o trazem, porque a granularidade é o
    # **conjunto** de usinas (`Conj. …`), que não tem CEG próprio.
    id_ons: str | None = None
    codigo_usina: str | None = None  # CEG na forma canônica, quando a origem publica

    geracao_mw: Decimal | None = None  # pode ser negativa: usina parada consumindo da rede
    geracao_limitada_mw: Decimal | None = None
    disponibilidade_mw: Decimal | None = None
    geracao_referencia_mw: Decimal | None = None
    geracao_referencia_final_mw: Decimal | None = None

    razao_restricao: str | None = None  # REL (elétrica), CNF (confiabilidade), ENE (energia)
    origem_restricao: str | None = None  # SIS (sistêmica), LOC (local)
    descricao_restricao: str | None = None
    id_ponto_conexao: str | None = None
    nome_ponto_conexao: str | None = None
    agente_operador: str | None = None

    geracao_nao_realizada_mw: Decimal | None = None  # o constrained-off apurado
    minutos_rel: int | None = None
    minutos_cnf: int | None = None
    minutos_ene: int | None = None
    minutos_restricao: int | None = None

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = valor.strip().upper()
        if sigla not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return sigla

    @field_validator(*_TEXTOS, mode="before")
    @classmethod
    def _vazio_ou_traco_e_nulo(cls, valor: str | None) -> str | None:
        return _texto_ou_nulo(valor)

    @field_validator("codigo_usina", mode="before")
    @classmethod
    def _ceg_na_forma_canonica(cls, valor: str | None) -> str | None:
        return ceg_canonico(valor)

    @field_validator(*_NUMERICOS, mode="before")
    @classmethod
    def _numero_vazio_e_nulo(cls, valor: Any) -> Any:
        if isinstance(valor, str):
            texto = valor.strip()
            return texto or None
        return valor

    @model_validator(mode="after")
    def _deriva_data_e_instante(self) -> RestricaoCoff:
        try:
            instante = datetime.strptime(self.din_instante, "%Y-%m-%d %H:%M:%S")
        except ValueError as exc:
            raise ValueError(f"din_instante inválido: {self.din_instante!r}") from exc
        self.instante = instante
        self.data_referencia = instante.date()
        return self


class OnsRestricaoCoff(Conector):
    """Molde comum: um CSV por mês, recortado pela janela na extração.

    A subclasse declara `entidade` e `url_mes`; o resto é idêntico entre as
    duas fontes.
    """

    fonte = "ons"
    schema = RestricaoCoff
    schema_versao = "1"
    max_dias_por_requisicao = None  # o recorte é por mês de arquivo, não por dias
    url_mes: str  # a subclasse preenche

    def __init__(self) -> None:
        self._sessao = criar_sessao()

    def _baixar_mes(self, ano: int, mes: int) -> str:
        from src.core.config import get_settings

        resposta = self._sessao.get(self.url_mes.format(ano=ano, mes=mes), timeout=get_settings().http_timeout)
        resposta.raise_for_status()
        return resposta.text

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        for ano, mes in _meses(janela):
            logger.info("%s: baixando %d-%02d", self.rotulo, ano, mes)
            leitor = csv.DictReader(StringIO(self._baixar_mes(ano, mes)), delimiter=";")
            for linha in leitor:
                instante = linha.get("din_instante", "")[:10]
                if not instante:
                    continue
                if not (janela.inicio.isoformat() <= instante <= janela.fim.isoformat()):
                    continue  # o arquivo é mensal; a janela é o recorte pedido
                yield linha

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "din_instante": bruto.get("din_instante", ""),
            "submercado": bruto.get("id_subsistema", ""),
            "nome_subsistema": bruto.get("nom_subsistema", "").strip(),
            "uf": bruto.get("id_estado", "").strip(),
            "nome_uf": bruto.get("nom_estado", "").strip(),
            "nome_usina": bruto.get("nom_usina", "").strip(),
            "id_ons": bruto.get("id_ons"),
            "codigo_usina": bruto.get("ceg"),
            "geracao_mw": bruto.get("val_geracao"),
            "geracao_limitada_mw": bruto.get("val_geracaolimitada"),
            "disponibilidade_mw": bruto.get("val_disponibilidade"),
            "geracao_referencia_mw": bruto.get("val_geracaoreferencia"),
            "geracao_referencia_final_mw": bruto.get("val_geracaoreferenciafinal"),
            "razao_restricao": bruto.get("cod_razaorestricao"),
            "origem_restricao": bruto.get("cod_origemrestricao"),
            "descricao_restricao": bruto.get("dsc_restricao"),
            "id_ponto_conexao": bruto.get("id_pontoconexao"),
            "nome_ponto_conexao": bruto.get("nom_pontoconexao"),
            "agente_operador": bruto.get("nom_agenteoperador"),
            "geracao_nao_realizada_mw": bruto.get("val_geracaonaorealizadaapurada"),
            "minutos_rel": bruto.get("num_minutos_rel"),
            "minutos_cnf": bruto.get("num_minutos_cnf"),
            "minutos_ene": bruto.get("num_minutos_ene"),
            "minutos_restricao": bruto.get("num_minutos_restricao"),
        }
