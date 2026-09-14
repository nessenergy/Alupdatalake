"""Conector BBCE — curva forward (Onda 2, exige credencial).

Fonte: BBCE Connect, produto **BBCE Curva Forward**.
Documentação: coleção Postman entregue pela Alup em 14/09/2026
(`documenter.getpostman.com/view/48979689/2sB3QJPWWr`).

Escrito **sem credencial**, no mesmo regime do `hubspot_negocios`: os 7
componentes existem antes do acesso, para que a chegada do token seja "ligar e
conferir", não "começar". O acesso somente leitura está sendo providenciado
pela Alup (pendência A7, issue #23).

## O que a curva forward é, e por que ela entra

O `ccee_pld` traz o preço **à vista**. A curva forward traz o preço **negociado
hoje para entrega futura**: para cada data de referência, um conjunto de
vértices (`vertexDate`, `vertexValue`). É o que permite comparar a expectativa
de mercado com o realizado — e é a razão de a fonte estar no escopo.

## Três coisas que a documentação não resolve sozinha

1. **O host não está na coleção.** Ela usa `{{baseUrl}}` sem valor. O endereço
   vem junto com o acesso, então é **configuração e não constante** — sai das
   credenciais, e a ausência falha dizendo isso.
2. **A autenticação é de sessão, não de token fixo.** `POST /v2/login` devolve
   um JWT com validade de 4h (`expiresIn: 14400`). São quatro credenciais —
   `apiKey`, `companyExternalCode`, `email` e `password` —, e por isso elas vêm
   num único secret estruturado, como as DSN dos bancos da Onda 3.
3. **A BBCE data o vértice em UTC representando meia-noite de Brasília**
   (`2026-02-09T03:00:00.000Z`). Cortar a string em 10 caracteres acerta por
   acidente e erra no dia em que a origem mudar a representação; a conversão de
   fuso é explícita.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, model_validator

from src.core.conector import Conector
from src.core.config import get_settings
from src.core.http import criar_sessao
from src.core.registry import registrar
from src.core.secrets import ler_secret

if TYPE_CHECKING:
    from collections.abc import Iterator

    from src.core.execucao import Janela

logger = logging.getLogger(__name__)

# Offset fixo em vez de `ZoneInfo("America/Sao_Paulo")`: o Brasil não observa
# horário de verão desde 2019, e o `zoneinfo` exigiria a dependência `tzdata`
# em Windows, onde não há base de fusos do sistema. É a mesma premissa que o
# agendador já assume em `infra/modules/scheduler`.
#
# ponytail: se o horário de verão voltar, é aqui que quebra — e o teste de
# `_data_brasilia` é o que avisa.
BRASILIA = timezone(timedelta(hours=-3))

CAMPO_CREDENCIAIS = "credenciais"
ROTA_LOGIN = "/v2/login"
ROTA_CURVA = "/v1/curve/bbce-fwd"

OBRIGATORIAS = ("base_url", "api_key", "company_external_code", "email", "password")


def ler_credenciais() -> dict[str, Any]:
    """Credenciais do BBCE, como JSON num único secret.

    São quatro campos mais o host. Um secret estruturado, e não cinco secrets
    soltos, pela mesma razão das DSN da Onda 3: a Alup preenche uma coisa só, e
    não há estado meio-configurado.
    """
    return json.loads(ler_secret("bbce", CAMPO_CREDENCIAIS))


def _data_brasilia(iso: str) -> date:
    """Data em Brasília de um instante ISO da BBCE.

    A origem publica meia-noite local como `03:00:00.000Z`. Converter é o que
    mantém a série correta se ela passar a publicar em outro horário.
    """
    try:
        momento = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"data ISO inválida: {iso!r}") from exc
    return momento.astimezone(BRASILIA).date()


class VerticeCurva(BaseModel):
    """Um ponto da curva forward: o preço negociado hoje para uma data futura."""

    data_referencia: date
    curva: str
    vertice_em: date = Field(description="Data de entrega que o vértice precifica")
    preco_reais_mwh: Decimal = Field(ge=0)
    origem_dado: str
    identidade: str
    id_origem: str
    atualizado_em: datetime

    @model_validator(mode="after")
    def _vertice_nao_olha_para_tras(self) -> VerticeCurva:
        if self.vertice_em < self.data_referencia:
            raise ValueError(
                f"vértice {self.vertice_em} anterior à referência {self.data_referencia}: "
                "curva forward precifica o futuro"
            )
        return self


@registrar
class BbceCurvaForward(Conector):
    """Um pedido por dia da janela; dia sem pregão devolve lista vazia."""

    fonte = "bbce"
    entidade = "curva_forward"
    schema = VerticeCurva
    schema_versao = "1"
    max_dias_por_requisicao = None  # o endpoint aceita uma data por vez

    def __init__(self) -> None:
        # O login é POST e cria sessão; repetir depois de 5xx não duplica nada
        # na origem, e sem isso uma instabilidade derruba a janela inteira.
        self._sessao = criar_sessao(retry_post=True)
        self._cache_credenciais: dict[str, Any] | None = None
        self._cache_token: str | None = None

    # ----------------------------------------------------------- credenciais

    def _credenciais(self) -> dict[str, Any]:
        if self._cache_credenciais is None:
            credenciais = ler_credenciais()
            if faltando := [c for c in OBRIGATORIAS if not credenciais.get(c)]:
                raise KeyError(
                    f"credenciais do BBCE incompletas, faltam: {', '.join(faltando)}. "
                    "O secret alupdata-bbce-credenciais é um JSON com "
                    f"{', '.join(OBRIGATORIAS)} — o host vem junto com o acesso, não está na documentação pública"
                )
            self._cache_credenciais = credenciais
        return self._cache_credenciais

    def _token(self) -> str:
        """JWT da sessão, obtido uma vez e reaproveitado na janela."""
        if self._cache_token is None:
            credenciais = self._credenciais()
            resposta = self._sessao.post(
                f"{credenciais['base_url'].rstrip('/')}{ROTA_LOGIN}",
                # Senha no corpo, nunca em query string: ela apareceria no log
                # de acesso da BBCE e em qualquer proxy no caminho.
                json={
                    "companyExternalCode": credenciais["company_external_code"],
                    "email": credenciais["email"],
                    "password": credenciais["password"],
                },
                headers={"apiKey": credenciais["api_key"], "Accept": "application/json"},
                params=None,
                timeout=get_settings().http_timeout,
            )
            resposta.raise_for_status()
            self._cache_token = str(resposta.json()["accessToken"])
            logger.info("BBCE: sessão autenticada")
        return self._cache_token

    # -------------------------------------------------------------- extração

    def _curva_do_dia(self, dia: date) -> list[dict[str, Any]]:
        """Vértices da curva para uma data de referência.

        Reautentica **uma vez** diante de 401: o JWT vale 4h, e uma janela longa
        pode ultrapassá-las no meio. 401 que persiste é credencial revogada, e
        aí a execução falha em vez de devolver vazio — vazio seria lido como
        "dia sem curva" e o buraco passaria despercebido.
        """
        credenciais = self._credenciais()
        url = f"{credenciais['base_url'].rstrip('/')}{ROTA_CURVA}"

        for tentativa in (1, 2):
            resposta = self._sessao.get(
                url,
                headers={
                    "apiKey": credenciais["api_key"],
                    "Authorization": self._token(),
                    "Accept": "application/json",
                },
                params={"referenceDate": dia.isoformat()},
                timeout=get_settings().http_timeout,
            )
            if resposta.status_code == 401 and tentativa == 1:
                logger.info("BBCE: sessão expirada, reautenticando")
                self._cache_token = None
                continue
            resposta.raise_for_status()
            return list(resposta.json() or [])
        return []

    def extrair(self, janela: Janela) -> Iterator[dict[str, Any]]:
        dia = janela.inicio
        while dia <= janela.fim:
            vertices = self._curva_do_dia(dia)
            if not vertices:
                # Fim de semana e feriado não têm pregão.
                logger.info("BBCE: sem curva em %s", dia.isoformat())
            yield from vertices
            dia += timedelta(days=1)

    def transformar(self, bruto: dict[str, Any]) -> dict[str, Any]:
        return {
            "data_referencia": _data_brasilia(bruto["date"]),
            "curva": bruto.get("name", ""),
            "vertice_em": _data_brasilia(bruto["vertexDate"]),
            "preco_reais_mwh": bruto.get("vertexValue"),
            "origem_dado": bruto.get("dataSource", ""),
            "identidade": bruto.get("identity", ""),
            "id_origem": bruto.get("id", ""),
            "atualizado_em": bruto.get("updatedAt") or bruto.get("createdAt"),
        }
