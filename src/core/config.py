"""Configuração centralizada do projeto AlupData.

Todos os módulos leem daqui — nunca de `os.getenv` espalhado pelo código,
e nunca com o nome do dataset escrito literalmente.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuração lida de variáveis de ambiente (ver `.env.example`)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gcp_project_id: str = "alupdata-dev"
    gcp_region: str = Field(
        default="southamerica-east1",
        description="Região dos recursos (ADR 009). O INFORMATION_SCHEMA do BigQuery é por região: "
        "apontar para a região errada devolve zero linhas em silêncio",
    )

    bq_dataset_bronze: str = "bronze"
    bq_dataset_silver: str = "silver"
    bq_dataset_gold: str = "gold"

    gcs_bucket_raw: str = ""

    http_timeout: float = Field(default=30.0, description="Timeout por requisição, em segundos")
    http_max_tentativas: int = Field(default=3, description="Tentativas totais antes de desistir")

    banco_timeout: float = Field(default=30.0, description="Timeout de conexão a banco relacional, em segundos")
    banco_lote: int = Field(
        default=1000, description="Linhas por fetchmany; também é o arraysize pago em round-trip sob VPN"
    )

    dry_run: bool = Field(default=False, description="Extrai e valida sem gravar em GCS/BigQuery")

    portal_provedor: str = Field(default="simulado", description="'simulado' ou 'bigquery' (ver ADR 005)")
    portal_view: str = Field(default="cambio_mensal", description="View Gold exibida pelo Portal MVP")
    portal_limite_linhas: int = Field(default=200, description="Teto de linhas lidas por request")
    portal_orcamento_mensal_usd: float = Field(
        default=120.0, description="Orçamento mensal de nuvem, em USD, contra o qual a rota /custo compara"
    )

    @property
    def bucket_raw(self) -> str:
        """Bucket de dado bruto; deriva do projeto quando não informado."""
        return self.gcs_bucket_raw or f"{self.gcp_project_id}-raw"

    def tabela_bronze(self, fonte: str, entidade: str) -> str:
        """Nome totalmente qualificado da tabela Bronze de uma entidade."""
        return f"{self.gcp_project_id}.{self.bq_dataset_bronze}.{fonte}_{entidade}"


@lru_cache
def get_settings() -> Settings:
    """Settings memoizadas — o processo lê o ambiente uma vez só."""
    return Settings()
