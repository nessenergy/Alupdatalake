"""Conector ONS — geração térmica por motivo de despacho (Aditivo 01, público).

Fonte: Dados Abertos ONS, dataset `geracao-termica-despacho-2` (arquivos em
`geracao_termica_despacho_2_ho/`), um CSV por mês desde **2022-01**
(`GERACAO_TERMICA_DESPACHO-2_AAAA_MM.csv`, ~33 MB e ~103 mil linhas em 09/2026,
143 usinas). Antes disso o ONS publica **um CSV por ano**
(`GERACAO_TERMICA_DESPACHO_AAAA.csv`, ~265 MB), que o conector não lê: janela
anterior a 2022-01 é recusada com erro claro (ver `OnsCsvMensal`).
Documentação: https://dados.ons.org.br/dataset/geracao-termica-despacho-2

Para cada usina térmica e hora, quanto foi programado e quanto foi verificado, e
**por qual motivo** a usina gerou: ordem de mérito, inflexibilidade, razão
elétrica, segurança energética, reserva de potência, substituição, unit
commitment ou constrained-off. É o que explica por que a térmica ligou, e não só
que ligou.

O que a série real impõe (conferido em 01/2022, 09/2024 e 09/2026):

1. **O cabeçalho cresceu três vezes**: 41 colunas (2022-01), 42 com `val_fdexp`
   (2024-09), 43 com `val_progdisponibilidade` (2026-02) e 47 com
   `val_geracaodespachada`, `nom_combustivel`, `dsc_tpmotivorestricao` e
   `din_publicacao` (2026-04). A leitura é por nome de coluna, e o que o mês
   não traz fica NULL — nunca zero. O nome do combustível, aliás, é
   `nom_combustivel` no arquivo e `nom_tipocombustivel` no dicionário JSON.
2. **O patamar muda de caixa**: `LEVE`/`MÉDIA`/`PESADA` até 2026-03, `Leve`/
   `Média`/`Pesada` depois. Normalizado para maiúsculas.
3. **Números em duas grafias**: `201.0` e `0E-8` em 2022, `201` e `0.000` depois.
4. **O CEG não é único por usina** (usinas distintas compartilham CEG). A chave é
   o instante mais o nome da usina; `ceg` vira `codigo_usina`, a dimensão comum.
5. Ao contrário do hidrológico, o instante é o **início** da hora.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, field_validator

from src.conectores.ons_csv_anual import instante, submercado, vazio_e_nulo
from src.conectores.ons_csv_mensal import OnsCsvMensal, inteiro_ou_nulo
from src.core.ceg import ceg_canonico
from src.core.registry import registrar

# destino -> coluna do CSV. `prog_` é o programado (dia anterior); `verif_`, o verificado.
_MEDIDAS = {
    "prog_geracao_mwmed": "val_proggeracao",
    "prog_ordem_merito_mwmed": "val_progordemmerito",
    "prog_ordem_merito_ref_mwmed": "val_progordemdemeritoref",
    "prog_ordem_merito_acima_inflex_mwmed": "val_progordemdemeritoacimadainflex",
    "prog_inflexibilidade_mwmed": "val_proginflexibilidade",
    "prog_inflex_embutida_merito_mwmed": "val_proginflexembutmerito",
    "prog_inflex_pura_mwmed": "val_proginflexpura",
    "prog_razao_eletrica_mwmed": "val_prograzaoeletrica",
    "prog_garantia_energetica_mwmed": "val_proggarantiaenergetica",
    "prog_gfom_mwmed": "val_proggfom",
    "prog_reposicao_perdas_mwmed": "val_progreposicaoperdas",
    "prog_exportacao_mwmed": "val_progexportacao",
    "prog_reserva_potencia_mwmed": "val_progreservapotencia",
    "prog_gsub_mwmed": "val_proggsub",
    "prog_unit_commitment_mwmed": "val_progunitcommitment",
    "prog_constrained_off_mwmed": "val_progconstrainedoff",
    "prog_inflexibilidade_dessem_mwmed": "val_proginflexibilidadedessem",
    "verif_geracao_mwmed": "val_verifgeracao",
    "verif_ordem_merito_mwmed": "val_verifordemmerito",
    "verif_ordem_merito_acima_inflex_mwmed": "val_verifordemdemeritoacimadainflex",
    "verif_inflexibilidade_mwmed": "val_verifinflexibilidade",
    "verif_inflex_embutida_merito_mwmed": "val_verifinflexembutmerito",
    "verif_inflex_pura_mwmed": "val_verifinflexpura",
    "verif_razao_eletrica_mwmed": "val_verifrazaoeletrica",
    "verif_garantia_energetica_mwmed": "val_verifgarantiaenergetica",
    "verif_gfom_mwmed": "val_verifgfom",
    "verif_reposicao_perdas_mwmed": "val_verifreposicaoperdas",
    "verif_exportacao_mwmed": "val_verifexportacao",
    "verif_reserva_potencia_mwmed": "val_verifreservapotencia",
    "verif_gsub_mwmed": "val_verifgsub",
    "verif_unit_commitment_mwmed": "val_verifunitcommitment",
    "verif_constrained_off_mwmed": "val_verifconstrainedoff",
    # Ausentes dos arquivos mais antigos (ver o docstring do módulo).
    "verif_fator_exportacao": "val_fdexp",
    "prog_disponibilidade_mwmed": "val_progdisponibilidade",
    "geracao_despachada_mwmed": "val_geracaodespachada",
}


class GeracaoTermicaDespacho(BaseModel):
    """Uma usina térmica em uma hora: programado, verificado e o motivo do despacho."""

    data_referencia: date
    instante: datetime
    patamar: str
    submercado: str
    nome_subsistema: str
    nome_usina: str
    codigo_usina_planejamento: int | None = None
    codigo_usina: str | None = None  # CEG — dimensão comum do projeto; não é único por usina
    prog_geracao_mwmed: Decimal | None = None
    prog_ordem_merito_mwmed: Decimal | None = None
    prog_ordem_merito_ref_mwmed: Decimal | None = None
    prog_ordem_merito_acima_inflex_mwmed: Decimal | None = None
    prog_inflexibilidade_mwmed: Decimal | None = None
    prog_inflex_embutida_merito_mwmed: Decimal | None = None
    prog_inflex_pura_mwmed: Decimal | None = None
    prog_razao_eletrica_mwmed: Decimal | None = None
    prog_garantia_energetica_mwmed: Decimal | None = None
    prog_gfom_mwmed: Decimal | None = None
    prog_reposicao_perdas_mwmed: Decimal | None = None
    prog_exportacao_mwmed: Decimal | None = None
    prog_reserva_potencia_mwmed: Decimal | None = None
    prog_gsub_mwmed: Decimal | None = None
    prog_unit_commitment_mwmed: Decimal | None = None
    prog_constrained_off_mwmed: Decimal | None = None
    prog_inflexibilidade_dessem_mwmed: Decimal | None = None
    verif_geracao_mwmed: Decimal | None = None
    verif_ordem_merito_mwmed: Decimal | None = None
    verif_ordem_merito_acima_inflex_mwmed: Decimal | None = None
    verif_inflexibilidade_mwmed: Decimal | None = None
    verif_inflex_embutida_merito_mwmed: Decimal | None = None
    verif_inflex_pura_mwmed: Decimal | None = None
    verif_razao_eletrica_mwmed: Decimal | None = None
    verif_garantia_energetica_mwmed: Decimal | None = None
    verif_gfom_mwmed: Decimal | None = None
    verif_reposicao_perdas_mwmed: Decimal | None = None
    verif_exportacao_mwmed: Decimal | None = None
    verif_reserva_potencia_mwmed: Decimal | None = None
    verif_gsub_mwmed: Decimal | None = None
    verif_unit_commitment_mwmed: Decimal | None = None
    verif_constrained_off_mwmed: Decimal | None = None
    verif_fator_exportacao: Decimal | None = None
    """0 sem exportação, 0,5 em um patamar semi-horário, 1 em dois."""
    atendimento_rpo: int | None = None
    """Reserva de potência operativa: 0 não despachada por esse motivo, 1 satisfatório, 2 insatisfatório."""
    tipo_restricao_eletrica: int | None = None
    """0 a 9, conforme o dicionário do ONS."""
    prog_disponibilidade_mwmed: Decimal | None = None
    geracao_despachada_mwmed: Decimal | None = None
    combustivel: str | None = None
    motivo_restricao: str | None = None
    publicado_em: datetime | None = None
    """Quando o ONS publicou a linha; muda quando o arquivo é republicado."""

    @field_validator("submercado")
    @classmethod
    def _sigla(cls, valor: str) -> str:
        sigla = submercado(valor)
        if sigla is None:
            raise ValueError("submercado vazio")
        return sigla

    @field_validator("nome_usina")
    @classmethod
    def _usina_preenchida(cls, valor: str) -> str:
        if not valor:
            raise ValueError("nome da usina vazio")
        return valor

    @field_validator("codigo_usina", mode="before")
    @classmethod
    def _ceg_na_forma_canonica(cls, valor: str | None) -> str | None:
        return ceg_canonico(valor)

    @field_validator("codigo_usina_planejamento", "atendimento_rpo", "tipo_restricao_eletrica", mode="before")
    @classmethod
    def _inteiro(cls, valor: Any) -> int | None:
        return inteiro_ou_nulo(valor)

    @field_validator("combustivel", "motivo_restricao", "publicado_em", *_MEDIDAS, mode="before")
    @classmethod
    def _vazio_e_nulo(cls, valor: Any) -> Any:
        return vazio_e_nulo(valor)


@registrar
class OnsGeracaoTermicaDespacho(OnsCsvMensal):
    """Geração térmica por motivo de despacho, por usina e hora. Um CSV por mês, em stream."""

    entidade = "geracao_termica_despacho"
    schema = GeracaoTermicaDespacho
    caminho = "geracao_termica_despacho_2_ho/GERACAO_TERMICA_DESPACHO-2_{ano}_{mes:02d}.csv"
    primeiro_mes = (2022, 1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        publicado = vazio_e_nulo(bruto.get("din_publicacao"))
        return {
            "data_referencia": bruto["din_instante"][:10],
            "instante": instante(bruto["din_instante"]),
            "patamar": (bruto.get("nom_tipopatamar") or "").strip().upper(),
            "submercado": bruto.get("id_subsistema", ""),
            "nome_subsistema": (bruto.get("nom_subsistema") or "").strip(),
            "nome_usina": (bruto.get("nom_usina") or "").strip(),
            "codigo_usina_planejamento": bruto.get("cod_usinaplanejamento"),
            "codigo_usina": bruto.get("ceg"),
            "atendimento_rpo": bruto.get("val_atendsatisfatoriorpo"),
            "tipo_restricao_eletrica": bruto.get("tip_restricaoeletrica"),
            "combustivel": bruto.get("nom_combustivel"),
            "motivo_restricao": bruto.get("dsc_tpmotivorestricao"),
            "publicado_em": instante(publicado) if publicado else None,
        } | {destino: bruto.get(origem) for destino, origem in _MEDIDAS.items()}
