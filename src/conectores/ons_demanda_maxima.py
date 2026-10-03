"""Conector ONS — demanda máxima diária por subsistema (Onda 1, público).

Fonte: Dados Abertos ONS, dataset `demanda_maxima_di`, um CSV por ano (2024 em
diante; 2023 e antes devolvem 404).
Documentação: https://dados.ons.org.br/dataset/demanda-maxima-di

É a seção de demanda máxima do IPDO (ADR 027): o resto do conteúdo do boletim
já está no lake por outras fontes. Extração na base `OnsCsvAnual`. O que o dado
impõe:

- `id_subsistema` e `nom_subsistema` vêm com **espaços** (`"SE "`, `" SUDESTE    "`);
  o trim vive no validador.
- São duas medidas, cada uma com o seu instante: a demanda **instantânea**
  máxima do dia (MW) e a **integralizada** (MWmed) na hora dessa máxima. Os dois
  instantes não coincidem (a integralizada é horária, a instantânea tem minuto).
- Vazio é nulo, nunca zero. Nos arquivos de 2024 a 2026 nenhum campo veio vazio.
- O ano sem arquivo é ignorado (a base registra aviso), mas a janela cujos anos
  inteiros não têm arquivo falha alto: zero linhas silenciosas esconderiam
  janela anterior a 2024.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import OnsCsvAnual, instante, submercado, vazio_e_nulo
from src.core.registry import registrar


class DemandaMaxima(BaseModel):
    """Demanda máxima de um subsistema em um dia."""

    data_referencia: date
    submercado: str
    nome_subsistema: str
    demanda_integralizada_mwmed: Decimal | None
    """Integralizada na hora da máxima instantânea, em MWmed."""
    instante_integralizada: datetime | None
    demanda_instantanea_mw: Decimal | None
    """Máxima instantânea do dia, em MW."""
    instante_instantanea: datetime | None

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("nome_subsistema")
    @classmethod
    def _trim(cls, valor: str) -> str:
        return valor.strip()

    @field_validator("demanda_integralizada_mwmed", "demanda_instantanea_mw")
    @classmethod
    def _nao_negativa(cls, valor: Decimal | None) -> Decimal | None:
        if valor is not None and valor < 0:
            raise ValueError(f"demanda negativa: {valor}")
        return valor


@registrar
class OnsDemandaMaxima(OnsCsvAnual):
    """Demanda máxima diária por subsistema."""

    entidade = "demanda_maxima"
    schema = DemandaMaxima
    caminho = "demanda_maxima_di/DEMANDA_MAXIMA_DI_{ano}.csv"
    coluna_data = "dat_referencia"
    exige_algum_ano = True  # a série começa em 2024; janela anterior falha alto

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        def ou_nulo(chave: str) -> Any:
            return vazio_e_nulo(bruto.get(chave))

        def instante_ou_nulo(chave: str) -> str | None:
            texto = ou_nulo(chave)
            return instante(texto) if texto else None

        return {
            "data_referencia": bruto["dat_referencia"][:10],
            "submercado": bruto["id_subsistema"],
            "nome_subsistema": bruto.get("nom_subsistema", ""),
            "demanda_integralizada_mwmed": ou_nulo("val_demandaintegralizada"),
            "instante_integralizada": instante_ou_nulo("din_demandaintegralizada"),
            "demanda_instantanea_mw": ou_nulo("val_demandainstantanea"),
            "instante_instantanea": instante_ou_nulo("din_demandainstantanea"),
        }
