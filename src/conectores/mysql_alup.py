"""Conectores do MySQL Alup (Onda 3): cadastro e faturamento do varejo, cinco tabelas.

Fonte: banco MySQL do Portal Alup, lido pela DSN do secret `alupdata-portal-alup-dsn`
(`src/core/banco.py`, ADR 008; rede pela ADR 024). Contrato de colunas:
`docs/dicionario-dados/mysql_alup_esquema.md`. Desenho: `docs/superpowers/specs/2026-11-10-mysql-alup-onda3-design.md`.

Escrito contra o dicionário de colunas, **sem ter lido uma linha de dado**: a credencial e a rede de dev chegaram em
19/10, mas esta entrega não depende delas. Os tipos vêm de `information_schema`; a primeira carga confere.

Dois modos, por tabela:

- **fato** (`invoice`, `faturas_processadas`): a janela filtra pela data de modificação, `[inicio, fim+1 dia)`;
- **retrato** (`uc`, `client`, `bandeira`): sem coluna de modificação, lê a tabela inteira e carimba
  `data_referencia` com o fim da janela (o conector não consulta o relógio). Mesmo caso do `aneel_siga`.

Fora do `SELECT`, de propósito (sem finalidade analítica; dado pessoal ou conteúdo desconhecido): `uc.address`,
`uc.vendedor`, `invoice.barcode`, `invoice.s3_key*`, `invoice.nfe`, `invoice.jsonInfo`, `faturas_processadas.nome`.
As tabelas de medição (`medicao_cinco_minutos_*`) esperam a data da renomeação e não estão aqui.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, field_validator

from src.core.banco import abrir_conexao, consultar
from src.core.conector import Conector
from src.core.registry import registrar

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

SEGREDO = "portal-alup"  # `alupdata-portal-alup-dsn`; o rótulo usa sublinhado, o secret usa hífen


class MysqlAlupConector(Conector):
    """Base das cinco tabelas: monta o SELECT de constantes da classe e lê pelo `consultar()` do framework."""

    fonte = "portal_alup"
    max_dias_por_requisicao = None  # a consulta aceita a janela inteira

    tabela: ClassVar[str]
    # coluna na origem -> campo do schema; o apelido evita que `idUc` chegue como `iduc` (consultar() usa minúsculas)
    colunas: ClassVar[dict[str, str]]
    # colunas de modificação, da mais confiável para a de reserva; vazio = retrato completo
    colunas_de_data: ClassVar[tuple[str, ...]] = ()

    @classmethod
    def sql(cls) -> str:
        """SELECT feito só de constantes da classe: nenhum texto externo vira SQL (daí o `noqa` e o `nosec`)."""
        lista = ", ".join(f"`{origem}` AS {destino}" for origem, destino in cls.colunas.items())
        consulta = f"SELECT {lista} FROM `{cls.tabela}`"  # noqa: S608 # nosec B608
        if cls.colunas_de_data:
            data = "COALESCE(" + ", ".join(f"`{c}`" for c in cls.colunas_de_data) + ")"
            consulta += f" WHERE {data} >= %(inicio)s AND {data} < %(fim)s"
        return consulta

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        if self.colunas_de_data:
            parametros: dict[str, Any] = {
                "inicio": datetime.combine(janela.inicio, time.min),
                "fim": datetime.combine(janela.fim + timedelta(days=1), time.min),  # fim exclusivo
            }
        else:
            parametros = {}
        with abrir_conexao(SEGREDO) as conexao:
            for linha in consultar(conexao, self.sql(), parametros):
                if not self.colunas_de_data:
                    linha["data_referencia"] = janela.fim.isoformat()
                yield linha


# ---- client


class Cliente(BaseModel):
    data_referencia: date
    id: int
    nickname: str | None = None
    corporate_name: str | None = None
    cnpj: str | None = None  # identificador de pessoa jurídica; não sobe para a Gold (spec, "Dado pessoal")


@registrar
class PortalAlupClient(MysqlAlupConector):
    """Clientes do Portal Alup. Retrato completo a cada execução."""

    entidade = "client"
    schema = Cliente
    tabela = "client"
    colunas = {"id": "id", "nickname": "nickname", "corporate_name": "corporate_name", "cnpj": "cnpj"}


# ---- uc


class UnidadeConsumidora(BaseModel):
    data_referencia: date
    id: str
    client_id: int | None = None
    contrato: str | None = None
    cnpj: str | None = None
    state: str | None = None
    contract_start_date: date | None = None
    submarket: str | None = None
    supplier: str | None = None
    subgroup: str | None = None
    modality: str | None = None
    contracted_demand_peak: Decimal | None = None
    contracted_demand_off_peak: Decimal | None = None
    scde_code: str | None = None
    contractual_modality: str | None = None
    supply_start_date: date | None = None
    supply_end_date: date | None = None
    guaranteed_discount_percentage: Decimal | None = None
    base_price: Decimal | None = None
    base_date: date | None = None
    adjustment_date: date | None = None
    adjustment_index: str | None = None
    losses: Decimal | None = None
    proinfa: Decimal | None = None
    included_charges: str | None = None
    icms: Decimal | None = None
    migration: str | None = None
    cod_agente: int | None = None
    due_day: int | None = None
    supply_duration: Decimal | None = None
    total_energy_volume: Decimal | None = None
    codigo_ativo: str | None = None
    adjusted_price: Decimal | None = None
    ccee_last_date: datetime | None = None
    api_ccee: int | None = None
    condicao_pagamento: str | None = None
    id_contrato: int | None = None
    reforma_tributaria: str | None = None
    id_migracao_ccee: str | None = None
    cod_agente_concessionaria: str | None = None
    status_do_contrato: str | None = None
    id_new: str | None = None
    status_faturamento: str | None = None
    interesse_em_renovar: str | None = None
    meses_renovacao: int | None = None
    renovacao_distrato: str | None = None

    @field_validator("id")
    @classmethod
    def _id_nao_vazio(cls, valor: str) -> str:
        if not valor.strip():
            raise ValueError("campo obrigatório vazio")
        return valor.strip()


@registrar
class PortalAlupUc(MysqlAlupConector):
    """Unidades consumidoras e o contrato de cada uma. Retrato completo; sem `address` nem `vendedor`."""

    entidade = "uc"
    schema = UnidadeConsumidora
    tabela = "uc"
    # Sem `address` e `vendedor`: dado pessoal sem finalidade analítica (spec, "Dado pessoal e sensível").
    colunas = {campo: campo for campo in UnidadeConsumidora.model_fields if campo != "data_referencia"}


# ---- bandeira


class Bandeira(BaseModel):
    data_referencia: date
    id: int
    mes: str | None = None  # formato não confirmado (pergunta 4 da spec): a Silver só o lê como YYYY-MM
    bandeira: str
    valor: Decimal


@registrar
class PortalAlupBandeira(MysqlAlupConector):
    """Bandeira tarifária por mês. Tabela pequena, retrato completo."""

    entidade = "bandeira"
    schema = Bandeira
    tabela = "bandeira"
    colunas = {"id": "id", "mes": "mes", "bandeira": "bandeira", "valor": "valor"}


# ---- invoice


class Fatura(BaseModel):
    id: int
    client_id: int | None = None
    uc_id: str | None = None
    month: str | None = None
    consumption: Decimal | None = None
    value: Decimal | None = None
    tax: Decimal | None = None
    status: int | None = None
    due_date: date | None = None
    updated_at: datetime | None = None
    created_at: datetime | None = None


@registrar
class PortalAlupInvoice(MysqlAlupConector):
    """Faturas por UC e mês, lidas pela data de modificação.

    Sem `nfe`, `jsonInfo`, `barcode` e `s3_key*`: conteúdo desconhecido, código de pagamento e endereço de arquivo.
    """

    entidade = "invoice"
    schema = Fatura
    tabela = "invoice"
    colunas = {campo: campo for campo in Fatura.model_fields}
    colunas_de_data = ("updated_at", "created_at")


# ---- faturas_processadas


class FaturaProcessada(BaseModel):
    id: int
    id_uc: str | None = None
    id_transacao_fmb: str | None = None
    id_pre_fatura_fmb: str | None = None
    codigo_contrato: str | None = None
    id_erp_empresa_origem: str | None = None
    cnpj_empresa_destino: str | None = None
    mes_suprimento: str | None = None
    quantidade: Decimal | None = None
    preco: Decimal | None = None
    valor_total: Decimal | None = None
    condicao_pagamento_erp: str | None = None
    natureza_contrato: str | None = None
    consumidor_final: bool | None = None
    numero_parcelas: int | None = None
    tags: str | None = None
    parcelas: str | None = None  # JSON como texto; a Silver o expõe sem tipar a estrutura
    data_vencimento: date | None = None
    status_processamento: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    erros: str | None = None
    id_contrato: str | None = None
    ordem_cadastrada: str | None = None
    estado: str | None = None
    desconto: Decimal | None = None
    submercado: str | None = None


@registrar
class PortalAlupFaturasProcessadas(MysqlAlupConector):
    """Faturas que o ERP processou, lidas pela data de modificação. Sem `nome` (conteúdo não confirmado)."""

    entidade = "faturas_processadas"
    schema = FaturaProcessada
    tabela = "faturas_processadas"
    colunas = {
        "id": "id",
        "idUc": "id_uc",
        "idTransacaoFMB": "id_transacao_fmb",
        "idPreFaturaFMB": "id_pre_fatura_fmb",
        "codigoContrato": "codigo_contrato",
        "idErpEmpresaOrigem": "id_erp_empresa_origem",
        "cnpjEmpresaDestino": "cnpj_empresa_destino",
        "mesSuprimento": "mes_suprimento",
        "quantidade": "quantidade",
        "preco": "preco",
        "valorTotal": "valor_total",
        "condicaoPagamentoErp": "condicao_pagamento_erp",
        "naturezaContrato": "natureza_contrato",
        "consumidorFinal": "consumidor_final",
        "numeroParcelas": "numero_parcelas",
        "tags": "tags",
        "parcelas": "parcelas",
        "dataVencimento": "data_vencimento",
        "statusProcessamento": "status_processamento",
        "createdAt": "created_at",
        "updatedAt": "updated_at",
        "erros": "erros",
        "idContrato": "id_contrato",
        "ordemCadastrada": "ordem_cadastrada",
        "estado": "estado",
        "desconto": "desconto",
        "submercado": "submercado",
    }
    colunas_de_data = ("updatedAt", "createdAt")
