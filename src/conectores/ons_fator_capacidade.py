"""Conector ONS — fator de capacidade de eólicas e solares (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `fator-capacidade-2` (arquivos em
`fator_capacidade_2_di/`), um CSV por mês desde **2022-01**
(`FATOR_CAPACIDADE-2_AAAA_MM.csv`, ~41 MB e ~170 mil linhas em 09/2026, 236
usinas e conjuntos). Antes disso o ONS publica **um CSV por ano**
(`FATOR_CAPACIDADE_AAAA.csv`, ~320 MB), que o conector não lê: janela anterior a
2022-01 é recusada com erro claro (ver `OnsCsvMensal`).
Documentação: https://dados.ons.org.br/dataset/fator-capacidade-2

Geração programada e verificada, capacidade instalada e o fator de capacidade
(verificada / instalada) de cada usina ou conjunto de usinas eólicas e solares,
por hora, com o ponto de conexão e as coordenadas. O arquivo se chama `_di` no
catálogo, mas o passo é **horário** (720 instantes em 09/2026).

O que o arquivo real impõe:

1. **A unidade é a usina _ou o conjunto_.** Em 158 mil das 170 mil linhas a
   modalidade é `Conjunto de Usinas` e o `ceg` vem `-`: vira NULL em
   `codigo_usina`. Só `Tipo I` e `Tipo II-B` trazem o CEG. A chave é `id_ons`
   (`CJU_...` nos conjuntos); o nome do conjunto não é único (233 nomes para 238
   ids em 09/2026).
2. **Há valores negativos e acima de 1**: geração verificada até -1,4 MWmed e
   fator até -0,004 e 1,05 em 09/2026 (1,82 em 09/2024). O Bronze guarda o que a
   origem publica.
3. **Vazios que são ausência**: programada vazia em 3.984 linhas, localização
   vazia fora do Nordeste, coordenadas vazias em alguns conjuntos. Viram NULL.
4. **Decimais longos**: o fator chega a 22 casas; o runner ajusta às 9 do NUMERIC.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import instante, submercado, vazio_e_nulo
from src.conectores.ons_csv_mensal import OnsCsvMensal
from src.core.ceg import ceg_canonico
from src.core.registry import registrar

_MEDIDAS = {
    "latitude_coletora": "val_latitudesecoletora",
    "longitude_coletora": "val_longitudesecoletora",
    "latitude_ponto_conexao": "val_latitudepontoconexao",
    "longitude_ponto_conexao": "val_longitudepontoconexao",
    "geracao_programada_mwmed": "val_geracaoprogramada",
    "geracao_verificada_mwmed": "val_geracaoverificada",
    "capacidade_instalada_mw": "val_capacidadeinstalada",
    "fator_capacidade": "val_fatorcapacidade",
}


class FatorCapacidade(BaseModel):
    """Uma usina eólica ou solar (ou um conjunto delas) em uma hora."""

    data_referencia: date
    instante: datetime
    submercado: str
    nome_subsistema: str
    uf: str
    nome_uf: str
    codigo_ponto_conexao: str
    nome_ponto_conexao: str
    localizacao: str | None = None
    modalidade_operacao: str
    tipo_usina: str
    nome_usina_conjunto: str
    id_ons: str
    codigo_usina: str | None = None  # CEG — dimensão comum do projeto; nulo em conjunto
    latitude_coletora: Decimal | None = None
    longitude_coletora: Decimal | None = None
    latitude_ponto_conexao: Decimal | None = None
    longitude_ponto_conexao: Decimal | None = None
    geracao_programada_mwmed: Decimal | None = None
    geracao_verificada_mwmed: Decimal | None = None
    capacidade_instalada_mw: Decimal | None = None
    fator_capacidade: Decimal | None = None

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("id_ons", "nome_usina_conjunto")
    @classmethod
    def _identificacao_preenchida(cls, valor: str) -> str:
        if not valor:
            raise ValueError("identificação da usina vazia")
        return valor

    @field_validator("codigo_usina", mode="before")
    @classmethod
    def _ceg_na_forma_canonica(cls, valor: str | None) -> str | None:
        return ceg_canonico(valor)

    @field_validator("localizacao", *_MEDIDAS, mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)


@registrar
class OnsFatorCapacidade(OnsCsvMensal):
    """Fator de capacidade de eólicas e solares, por usina (ou conjunto) e hora. Um CSV por mês, em stream."""

    entidade = "fator_capacidade"
    schema = FatorCapacidade
    caminho = "fator_capacidade_2_di/FATOR_CAPACIDADE-2_{ano}_{mes:02d}.csv"
    primeiro_mes = (2022, 1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        texto = {
            "nome_subsistema": "nom_subsistema",
            "uf": "id_estado",
            "nome_uf": "nom_estado",
            "codigo_ponto_conexao": "cod_pontoconexao",
            "nome_ponto_conexao": "nom_pontoconexao",
            "modalidade_operacao": "nom_modalidadeoperacao",
            "tipo_usina": "nom_tipousina",
            "nome_usina_conjunto": "nom_usina_conjunto",
            "id_ons": "id_ons",
        }
        return (
            {
                "data_referencia": bruto["din_instante"][:10],
                "instante": instante(bruto["din_instante"]),
                "submercado": bruto.get("id_subsistema", ""),
                "localizacao": bruto.get("nom_localizacao"),
                "codigo_usina": bruto.get("ceg"),
            }
            | {destino: (bruto.get(origem) or "").strip() for destino, origem in texto.items()}
            | {destino: bruto.get(origem) for destino, origem in _MEDIDAS.items()}
        )
