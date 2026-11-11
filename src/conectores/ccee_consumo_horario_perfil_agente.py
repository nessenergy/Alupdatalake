"""Conector CCEE — consumo horário por perfil de agente (Aditivo 01, público). Item 26.

Fonte: dados abertos da CCEE (CKAN), dataset `consumo_horario_perfil_agente`.
Catálogo: https://dadosabertos.ccee.org.br/dataset/consumo_horario_perfil_agente

A maior fonte do lake: ~34,9 milhões de linhas por mês (46.890 cargas × 744
horas), uma linha por carga e por hora, ~11 GiB por mês na Bronze. Dimensionamento
e custo: `docs/superpowers/specs/2026-11-10-item26-consumo-horario-design.md`.

Mesmo molde do `ccee_geracao_usina` (recurso gzip por mês, `PERIODO_COMERCIALIZACAO`
1..744 como índice da hora no mês). `transformar()` só repassa texto; quem converte
e rejeita é o schema, porque só `ValidationError` é capturado por linha pelo runner.

**Guarda de recarga.** A Bronze é append-only e cada mês pesa ~11 GiB: reler o mês
a cada execução mensal triplicaria o armazenamento. Antes de baixar, o conector
pergunta à Bronze se o mês já foi carregado, por uma execução concluída, na mesma
`versao_publicacao`. Mês republicado (versão nova) é relido; a Silver deduplica, a
mais recente vence (ADR 016). Para reprocessar de propósito, `RELER_MESES_CARREGADOS=true`.

Nada aqui lê credencial: o dado é público.
"""

from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from src.conectores.ccee_ckan import CceeCsvCkan, limpar, numero_ou_nulo, periodo_ccee
from src.conectores.ccee_pld import SIGLA_SUBMERCADO, SUBMERCADOS, _data_e_hora
from src.core.bigquery import TABELA_EXECUCOES, cliente, rotulos
from src.core.config import get_settings
from src.core.registry import registrar

if TYPE_CHECKING:
    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

# Teto de bytes lidos pela consulta da guarda: ela toca 3 colunas de um mês
# (~2 GiB de 11); 20 GiB é folga larga que ainda impede uma varredura completa.
TETO_BYTES_GUARDA = 20 * 1024**3

MEDIDAS = {
    "CAPACIDADE_CARGA": "capacidade_carga",
    "CONSUMO_CARGA_ACL": "consumo_carga_acl",
    "CONSUMO_CARGA_AJUSTADO_ACL": "consumo_carga_ajustado_acl",
    "CONSUMO_CARGA_AJUSTADO": "consumo_carga_ajustado",
    "CONSUMO_CARGA_PONTO_CONEXAO": "consumo_carga_ponto_conexao",
}


def _texto_ou_nulo(valor: str | None) -> str | None:
    texto = limpar(valor)
    return texto or None


class ConsumoHorarioPerfilAgente(BaseModel):
    """O consumo de uma carga em uma hora do mês de apuração.

    `data_referencia` e `data_hora` não vêm prontos: são derivados de
    `mes_referencia` + `periodo_comercializacao` pelo `model_validator`, com a
    mesma aritmética de `ccee_pld._data_e_hora`. Medidas vazias são nulas.
    """

    mes_referencia: str = Field(exclude=True)  # AAAAMM cru: só deriva data/hora; não é coluna do lake
    data_referencia: date | None = None  # preenchido por `_deriva_data_e_hora`
    data_hora: datetime | None = None  # hora local de Brasília, sem fuso; idem
    periodo_comercializacao: int = Field(ge=1, le=744)
    periodo_apuracao_ccee: str
    versao_publicacao: date
    codigo_carga: int
    nome_carga: str | None = None
    data_migracao: date | None = None
    codigo_perfil_agente: int
    sigla_perfil_agente: str | None = None
    classe_perfil_agente: str
    nome_empresarial: str | None = None
    cnpj_carga: str | None = None
    cidade_carga: str | None = None
    estado_carga: str | None = None
    submercado: str
    codigo_perfil_agente_distribuidora: int | None = None
    sigla_perfil_agente_distribuidora: str | None = None
    capacidade_carga: Decimal | None = None  # MW
    consumo_carga_acl: Decimal | None = None  # MWh
    consumo_carga_ajustado_acl: Decimal | None = None
    consumo_carga_ajustado: Decimal | None = None
    consumo_carga_ponto_conexao: Decimal | None = None

    @field_validator("data_migracao", mode="before")
    @classmethod
    def _parseia_data_migracao(cls, valor: Any) -> Any:
        """`dd/mm/aaaa` ou ISO; vazio é nulo. Outro formato vira `ValidationError` (linha inválida)."""
        if not isinstance(valor, str):
            return valor
        texto = valor.strip()
        if not texto:
            return None
        if "/" in texto:
            return datetime.strptime(texto, "%d/%m/%Y").date()
        return texto

    @field_validator("submercado")
    @classmethod
    def _submercado_conhecido(cls, valor: str) -> str:
        if valor not in SUBMERCADOS:
            raise ValueError(f"submercado desconhecido: {valor}")
        return valor

    @model_validator(mode="after")
    def _deriva_data_e_hora(self) -> ConsumoHorarioPerfilAgente:
        """Período fora do mês vira `ValueError` e, dentro do validador, `ValidationError`: linha inválida, contada."""
        dia, hora = _data_e_hora(self.mes_referencia, self.periodo_comercializacao)
        self.data_referencia = dia
        self.data_hora = datetime(dia.year, dia.month, dia.day, hora)
        return self


@registrar
class CceeConsumoHorarioPerfilAgente(CceeCsvCkan):
    """Consumo horário por carga. Gzip por mês; ~34,9 milhões de linhas cada."""

    dataset = "consumo_horario_perfil_agente"
    entidade = "consumo_horario_perfil_agente"
    schema = ConsumoHorarioPerfilAgente
    recurso_por = "mes"

    # Mesmo lote do `ccee_geracao_usina` (4x menos load jobs que o default de
    # 8 MiB). Vazão a medir na carga de prova do item 26; o plano é de ~5,4 h por mês.
    bytes_por_lote = 32 * 1024 * 1024

    # ----------------------------------------------------------------- guarda

    def _sufixos(self, janela: Janela) -> list[str]:
        meses = super()._sufixos(janela)
        cfg = get_settings()
        if cfg.dry_run or cfg.reler_meses_carregados:
            return meses
        return [m for m in meses if not self._mes_ja_carregado(m)]

    def _mes_ja_carregado(self, sufixo: str) -> bool:
        """Mês ausente do CKAN não é decidido aqui: a base o loga e ignora."""
        try:
            recurso = self._recurso(sufixo)
        except FileNotFoundError:
            return False
        modificado = str(recurso.get("last_modified") or "")[:10]
        try:
            versao: date | None = date.fromisoformat(modificado)
        except ValueError:
            versao = None  # sem versão na origem, `publicado_em` valeria a data da carga e nunca bateria
        primeiro = date(int(sufixo[:4]), int(sufixo[4:6]), 1)
        ultimo = primeiro.replace(day=monthrange(primeiro.year, primeiro.month)[1])
        carregado = self._bronze_tem_carga_concluida(primeiro, ultimo, versao)
        if carregado:
            logger.info("CCEE %s: %s já está na Bronze (versão %s), não será relido", self.dataset, sufixo, versao)
        return carregado

    def _bronze_tem_carga_concluida(self, inicio: date, fim: date, versao: date | None) -> bool:
        """A Bronze tem linha do mês, na versão dada, de uma execução com status SUCESSO?

        Lê 3 colunas de um mês, sempre com filtro de partição (a tabela exige) e
        teto de bytes. Execução que morreu no meio não conta: o mês seria relido.
        """
        from google.cloud import bigquery

        cfg = get_settings()
        tabela = cfg.tabela_bronze(self.fonte, self.entidade)
        execucoes = f"{cfg.gcp_project_id}.{cfg.bq_dataset_bronze}.{TABELA_EXECUCOES}"
        filtro_versao = "AND b.versao_publicacao = @versao" if versao else ""
        # Tabelas vêm da configuração; os valores vão por parâmetro.
        sql = (
            f"SELECT 1 FROM `{tabela}` b JOIN `{execucoes}` e ON e.ingestao_id = b._ingestao_id "  # noqa: S608  # nosec B608
            f"WHERE b.data_referencia BETWEEN @inicio AND @fim AND e.status = 'SUCESSO' "
            f"{filtro_versao} LIMIT 1"
        )
        parametros = [
            bigquery.ScalarQueryParameter("inicio", "DATE", inicio),
            bigquery.ScalarQueryParameter("fim", "DATE", fim),
        ]
        if versao:
            parametros.append(bigquery.ScalarQueryParameter("versao", "DATE", versao))
        config = bigquery.QueryJobConfig(
            query_parameters=parametros,
            maximum_bytes_billed=TETO_BYTES_GUARDA,
            labels=rotulos(self._execucao, "bronze") if self._execucao else {},
        )
        return any(True for _ in cliente().query(sql, job_config=config).result())

    # ------------------------------------------------------------ transformação

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        mes = limpar(bruto["MES_REFERENCIA"])
        nome = limpar(bruto.get("SUBMERCADO")).upper()

        registro: dict[str, Any] = {
            "mes_referencia": mes,
            "periodo_comercializacao": limpar(bruto.get("PERIODO_COMERCIALIZACAO")),
            "periodo_apuracao_ccee": periodo_ccee(mes),
            "versao_publicacao": bruto["_versao_publicacao"],
            "codigo_carga": limpar(bruto.get("CODIGO_CARGA")),
            "nome_carga": _texto_ou_nulo(bruto.get("NOME_CARGA")),
            "data_migracao": limpar(bruto.get("DATA_MIGRACAO")),
            "codigo_perfil_agente": limpar(bruto.get("CODIGO_PERFIL_AGENTE")),
            "sigla_perfil_agente": _texto_ou_nulo(bruto.get("SIGLA_PERFIL_AGENTE")),
            "classe_perfil_agente": limpar(bruto.get("CLASSE_PERFIL_AGENTE")),
            "nome_empresarial": _texto_ou_nulo(bruto.get("NOME_EMPRESARIAL")),
            "cnpj_carga": _texto_ou_nulo(bruto.get("CNPJ_CARGA")),
            "cidade_carga": _texto_ou_nulo(bruto.get("CIDADE_CARGA")),
            "estado_carga": _texto_ou_nulo(bruto.get("ESTADO_CARGA")),
            "submercado": SIGLA_SUBMERCADO.get(nome, nome),
            "codigo_perfil_agente_distribuidora": _texto_ou_nulo(bruto.get("CODIGO_PERFIL_AGENTE_DISTRIBUIDORA")),
            "sigla_perfil_agente_distribuidora": _texto_ou_nulo(bruto.get("SIGLA_PERFIL_AGENTE_DISTRIBUIDORA")),
        }
        for origem, destino in MEDIDAS.items():
            registro[destino] = numero_ou_nulo(bruto.get(origem))
        return registro
