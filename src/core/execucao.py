"""Janela de ingestão e contexto de execução.

Toda extração é parametrizada por uma janela de datas. Nenhum conector
decide sozinho "hoje": reprocessar é passar outra janela.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta


@dataclass(frozen=True)
class Janela:
    """Intervalo fechado de datas [inicio, fim]."""

    inicio: date
    fim: date

    def __post_init__(self) -> None:
        if self.fim < self.inicio:
            raise ValueError(f"janela invertida: {self.inicio} > {self.fim}")

    @classmethod
    def de_texto(cls, inicio: str, fim: str) -> Janela:
        """Constrói a partir de duas datas ISO (YYYY-MM-DD)."""
        return cls(date.fromisoformat(inicio), date.fromisoformat(fim))

    @classmethod
    def ultimos_dias(cls, dias: int, ate: date | None = None) -> Janela:
        """Janela terminando em `ate` (padrão: ontem, em UTC)."""
        fim = ate or (datetime.now(UTC).date() - timedelta(days=1))
        return cls(fim - timedelta(days=dias - 1), fim)

    def dias(self) -> list[date]:
        """Todos os dias da janela, inclusive as pontas."""
        return [self.inicio + timedelta(days=i) for i in range((self.fim - self.inicio).days + 1)]

    def particionar(self, tamanho: int) -> list[Janela]:
        """Quebra a janela em pedaços de no máximo `tamanho` dias.

        Fontes com limite de intervalo por requisição (CCEE, BCB) consomem
        estes pedaços em vez de pedir cinco anos de uma vez.
        """
        if tamanho < 1:
            raise ValueError("tamanho deve ser >= 1")
        passo = timedelta(days=tamanho)
        inicios = (self.inicio + passo * i for i in range((self.fim - self.inicio).days // tamanho + 1))
        return [Janela(ini, min(ini + passo - timedelta(days=1), self.fim)) for ini in inicios]

    def __str__(self) -> str:
        return f"{self.inicio.isoformat()}..{self.fim.isoformat()}"


@dataclass
class Execucao:
    """Identidade e métricas de uma execução de ingestão."""

    fonte: str
    entidade: str
    janela: Janela
    modo: str = "FONTE"
    origem_ingestao_id: str | None = None
    ingestao_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    iniciada_em: datetime = field(default_factory=lambda: datetime.now(UTC))
    linhas_extraidas: int = 0
    linhas_invalidas: int = 0
    linhas_carregadas: int = 0
    encerrada_em: datetime | None = None
    erro: str | None = None

    @property
    def status(self) -> str:
        if self.encerrada_em is None:
            return "EM_EXECUCAO"
        return "ERRO" if self.erro else "SUCESSO"

    @property
    def duracao_segundos(self) -> float | None:
        if self.encerrada_em is None:
            return None
        return (self.encerrada_em - self.iniciada_em).total_seconds()

    def encerrar(self, erro: str | None = None) -> None:
        self.encerrada_em = datetime.now(UTC)
        self.erro = erro

    def to_row(self) -> dict:
        """Linha para `bronze._execucoes` — o log operacional da ingestão."""
        return {
            "ingestao_id": self.ingestao_id,
            "fonte": self.fonte,
            "entidade": self.entidade,
            "modo": self.modo,
            "origem_ingestao_id": self.origem_ingestao_id,
            "janela_inicio": self.janela.inicio.isoformat(),
            "janela_fim": self.janela.fim.isoformat(),
            "status": self.status,
            "linhas_extraidas": self.linhas_extraidas,
            "linhas_invalidas": self.linhas_invalidas,
            "linhas_carregadas": self.linhas_carregadas,
            "iniciada_em": self.iniciada_em.isoformat(),
            "encerrada_em": self.encerrada_em.isoformat() if self.encerrada_em else None,
            "duracao_segundos": self.duracao_segundos,
            "erro": self.erro,
        }
