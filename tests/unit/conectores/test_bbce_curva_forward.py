"""Conector BBCE/curva forward — sem rede e sem credencial.

Escrito contra a coleção Postman recebida em 14/09, no mesmo regime do Hubspot:
os 7 componentes existem antes do acesso, e o teste de integração fica `skipif`.

O que estes testes fixam, e que a documentação não deixa óbvio:

- a BBCE datava o vértice em **UTC representando meia-noite de Brasília**
  (`03:00:00.000Z`). Cortar a string em 10 caracteres funciona por acidente e
  quebra no dia em que a origem mudar de fuso — a conversão é explícita;
- a sessão é **JWT com validade de 4h**, obtido por login; o conector reautentica
  uma vez diante de 401 em vez de derrubar uma janela longa;
- **o host não veio na documentação**: é configuração, não constante, e a
  ausência tem de falhar com mensagem que diga isso.
"""

from datetime import date

import pytest
from src.conectores.bbce_curva_forward import (
    BbceCurvaForward,
    VerticeCurva,
    _data_brasilia,
)
from src.core.execucao import Janela

SENHA_DE_TESTE = "valor-de-teste-nao-e-credencial"

CREDENCIAIS = {
    "base_url": "https://exemplo-bbce/api",
    "api_key": "chave-de-teste",
    "company_external_code": 123,
    "email": "conta@exemplo",
    "password": SENHA_DE_TESTE,
}

RESPOSTA = [
    {
        "dataSource": "BBCE",
        "name": "PLD",
        "identity": "CURVE",
        "vertexDate": "2026-02-09T03:00:00.000Z",
        "vertexValue": 65.55,
        "date": "2026-01-02T03:00:00.000Z",
        "createdAt": "2026-01-03T03:18:02.026Z",
        "updatedAt": "2026-01-03T03:18:02.026Z",
        "id": "677756ead85a96505a2b9a41",
    },
    {
        "dataSource": "BBCE",
        "name": "PLD",
        "identity": "CURVE",
        "vertexDate": "2026-03-10T03:00:00.000Z",
        "vertexValue": 71.52,
        "date": "2026-01-02T03:00:00.000Z",
        "createdAt": "2026-01-03T03:18:02.038Z",
        "updatedAt": "2026-01-03T03:18:02.038Z",
        "id": "677756ead85a96505a2b9a42",
    },
]


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.bbce_curva_forward.criar_sessao", lambda **_: None)
    monkeypatch.setattr("src.conectores.bbce_curva_forward.ler_credenciais", lambda: CREDENCIAIS)
    return BbceCurvaForward()


# ---------------------------------------------------- o fuso do vértice


@pytest.mark.parametrize(
    ("iso", "esperado"),
    [
        # A BBCE representa meia-noite de Brasília como 03:00Z.
        ("2026-02-09T03:00:00.000Z", date(2026, 2, 9)),
        ("2026-01-02T03:00:00.000Z", date(2026, 1, 2)),
        # Antes das 03:00Z ainda é o dia anterior em Brasília — o caso que o
        # corte de string erraria.
        ("2026-01-02T01:00:00.000Z", date(2026, 1, 1)),
        ("2026-01-01T23:00:00.000Z", date(2026, 1, 1)),
    ],
)
def test_data_em_brasilia_e_nao_corte_de_string(iso, esperado):
    assert _data_brasilia(iso) == esperado


def test_data_invalida_e_recusada():
    with pytest.raises(ValueError, match="data ISO"):
        _data_brasilia("ontem")


# ------------------------------------------------------------- extração


def test_um_pedido_por_dia_da_janela(conector, monkeypatch):
    pedidos = []
    monkeypatch.setattr(conector, "_curva_do_dia", lambda d: pedidos.append(d) or [])

    list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-03")))

    assert pedidos == [date(2026, 1, 1), date(2026, 1, 2), date(2026, 1, 3)]


def test_dia_sem_curva_nao_derruba_a_janela(conector, monkeypatch):
    """Fim de semana e feriado não têm pregão: lista vazia é normal."""
    monkeypatch.setattr(conector, "_curva_do_dia", lambda d: RESPOSTA if d.day == 2 else [])

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-03")))

    assert len(registros) == 2


def test_transformar_produz_o_vertice(conector, monkeypatch):
    monkeypatch.setattr(conector, "_curva_do_dia", lambda _d: RESPOSTA)

    bruto = next(iter(conector.extrair(Janela.de_texto("2026-01-02", "2026-01-02"))))
    registro = VerticeCurva.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 1, 2)
    assert registro.vertice_em == date(2026, 2, 9)
    assert float(registro.preco_reais_mwh) == 65.55
    assert registro.curva == "PLD"
    assert registro.id_origem == "677756ead85a96505a2b9a41"


def test_preco_negativo_e_rejeitado():
    with pytest.raises(ValueError):
        VerticeCurva.model_validate(_minimo(preco_reais_mwh="-1"))


def test_vertice_anterior_a_referencia_e_rejeitado():
    """Curva forward precifica o futuro; vértice no passado é erro de origem."""
    with pytest.raises(ValueError, match="vértice"):
        VerticeCurva.model_validate(_minimo(vertice_em="2025-12-01"))


def test_vertice_igual_a_referencia_e_aceito():
    """O vértice mais curto pode coincidir com o dia de referência."""
    assert VerticeCurva.model_validate(_minimo(vertice_em="2026-01-02")).vertice_em == date(2026, 1, 2)


# ---------------------------------------------------------- autenticação


class _Resposta:
    def __init__(self, payload=None, status=200):
        self._payload = payload if payload is not None else {}
        self.status_code = status

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"status {self.status_code}")


def test_login_manda_a_api_key_no_cabecalho_e_a_senha_so_no_corpo(conector):
    """A chave vai no header, a senha no corpo — como a documentação descreve.

    A senha nunca pode acabar em query string: ela apareceria no log de acesso
    do servidor da BBCE e em qualquer proxy no caminho.
    """
    visto = {}

    class SessaoFalsa:
        def post(self, url, json=None, headers=None, timeout=None, params=None):
            visto.update(url=url, json=json, headers=headers, timeout=timeout, params=params)
            return _Resposta({"accessToken": "jwt-de-teste", "expiresIn": 14400})

    conector._sessao = SessaoFalsa()
    assert conector._token() == "jwt-de-teste"

    assert visto["url"].endswith("/v2/login")
    assert visto["headers"]["apiKey"] == "chave-de-teste"
    assert visto["json"]["password"] == SENHA_DE_TESTE
    assert visto["params"] is None  # nada de credencial em query string
    assert visto["timeout"] is not None


def test_o_token_e_reaproveitado_entre_dias_da_janela(conector):
    """Login por dia gastaria uma autenticação por requisição de dado."""
    logins = {"n": 0}

    class SessaoFalsa:
        def post(self, *a, **k):
            logins["n"] += 1
            return _Resposta({"accessToken": "jwt", "expiresIn": 14400})

    conector._sessao = SessaoFalsa()
    conector._token()
    conector._token()

    assert logins["n"] == 1


def test_401_reautentica_uma_vez_e_repete(conector):
    """Janela longa pode ultrapassar as 4h de validade do JWT."""
    estado = {"logins": 0, "gets": 0}

    class SessaoFalsa:
        def post(self, *a, **k):
            estado["logins"] += 1
            return _Resposta({"accessToken": f"jwt{estado['logins']}", "expiresIn": 14400})

        def get(self, url, headers=None, params=None, timeout=None):
            estado["gets"] += 1
            if estado["gets"] == 1:
                return _Resposta(status=401)
            return _Resposta(RESPOSTA)

    conector._sessao = SessaoFalsa()

    assert len(conector._curva_do_dia(date(2026, 1, 2))) == 2
    assert estado["logins"] == 2  # reautenticou
    assert estado["gets"] == 2  # e repetiu o pedido


def test_401_persistente_falha_em_vez_de_devolver_vazio(conector):
    """Credencial revogada não pode virar 'dia sem curva'."""

    class SessaoFalsa:
        def post(self, *a, **k):
            return _Resposta({"accessToken": "jwt", "expiresIn": 14400})

        def get(self, *a, **k):
            return _Resposta(status=401)

    conector._sessao = SessaoFalsa()

    with pytest.raises(AssertionError):
        conector._curva_do_dia(date(2026, 1, 2))


# ------------------------------------------------------- host não documentado


def test_credenciais_sem_base_url_falham_dizendo_o_que_falta(monkeypatch):
    """A coleção Postman traz `{{baseUrl}}` sem valor: o host vem com o acesso."""
    monkeypatch.setattr("src.conectores.bbce_curva_forward.criar_sessao", lambda **_: None)
    monkeypatch.setattr(
        "src.conectores.bbce_curva_forward.ler_credenciais",
        lambda: {k: v for k, v in CREDENCIAIS.items() if k != "base_url"},
    )

    with pytest.raises(KeyError, match="base_url"):
        BbceCurvaForward()._credenciais()


# ------------------------------------------------------------------ ingestão


def test_ingerir_conta_os_vertices(conector, monkeypatch):
    monkeypatch.setattr(conector, "_curva_do_dia", lambda d: RESPOSTA if d.day == 2 else [])

    execucao = conector.ingerir(Janela.de_texto("2026-01-01", "2026-01-03"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0


def _minimo(**troca):
    base = {
        "data_referencia": "2026-01-02",
        "curva": "PLD",
        "vertice_em": "2026-02-09",
        "preco_reais_mwh": "65.55",
        "origem_dado": "BBCE",
        "identidade": "CURVE",
        "id_origem": "abc",
        "atualizado_em": "2026-01-03T03:18:02.026Z",
    }
    return base | troca
