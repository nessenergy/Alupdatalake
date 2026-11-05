"""Sessão SOAP da Plataforma de Integração da CCEE: mTLS com o .pfx, usuário e
senha no envelope. Nada aqui toca a rede nem lê segredo de verdade."""

import json
from types import SimpleNamespace
from xml.sax.saxutils import escape

import pytest
from defusedxml.common import DefusedXmlException
from src.conectores import ccee_pi_sessao as ccee
from src.conectores.ccee_pi_sessao import CceeError, Sessao

USUARIO = "usuario.teste"
SENHA = "s&nh<a>teste"
PFX = b"\x30\x82binario-de-teste"

OK = '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><r>ok</r></s:Body></s:Envelope>'
FALHA = (
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><s:Fault>'
    f"<faultcode>s:Client</faultcode><faultstring>Acesso negado para {USUARIO} com {escape(SENHA)}</faultstring>"
    "</s:Fault></s:Body></s:Envelope>"
)


@pytest.fixture
def sessao():
    return Sessao(pfx=PFX, senha_pfx="senha-do-pfx", usuario=USUARIO, senha=SENHA, perfil="6166")


@pytest.fixture
def chamadas(monkeypatch):
    """Captura o POST; a resposta é trocada por teste via `resposta`."""
    registro = SimpleNamespace(args=None, kwargs=None, resposta=SimpleNamespace(status_code=200, text=OK))

    def post_falso(url, **kwargs):
        registro.args, registro.kwargs = url, kwargs
        resposta = registro.resposta
        resposta.raise_for_status = lambda: None if resposta.status_code < 400 else _erro_http(resposta)
        return resposta

    monkeypatch.setattr(ccee, "post", post_falso)
    monkeypatch.setattr(ccee.time, "sleep", lambda _s: None)
    return registro


def _erro_http(resposta):
    raise RuntimeError(f"HTTP {resposta.status_code}")


def test_envelope_leva_usuario_perfil_e_corpo_com_escape(sessao):
    envelope = sessao.envelope("<corpo/>")

    assert USUARIO in envelope
    assert "6166" in envelope
    assert "<corpo/>" in envelope
    # a senha tem & e <: sem escape o XML quebra (ou, pior, injeta)
    assert "s&amp;nh&lt;a&gt;teste" in envelope
    assert SENHA not in envelope


def test_chamar_envia_o_pfx_em_memoria_e_o_soapaction(sessao, chamadas):
    raiz = sessao.chamar("/ws/medc/ListarMedidaBSv1", "listarMedida", "<corpo/>")

    assert chamadas.args == "https://servicos.ccee.org.br:443/ws/medc/ListarMedidaBSv1"
    assert chamadas.kwargs["pkcs12_data"] == PFX
    assert chamadas.kwargs["pkcs12_password"] == "senha-do-pfx"  # noqa: S105 — valor de teste, não credencial
    assert chamadas.kwargs["headers"]["SOAPAction"] == "listarMedida"
    assert chamadas.kwargs["timeout"] > 0
    assert raiz.tag.endswith("Envelope")


def test_fault_vira_erro_sem_vazar_usuario_nem_senha(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(status_code=500, text=FALHA)

    with pytest.raises(CceeError) as erro:
        sessao.chamar("/ws/x", "acao", "<corpo/>")

    texto = str(erro.value)
    assert "Client" in texto
    assert USUARIO not in texto
    assert SENHA not in texto


def test_erro_http_sem_fault_informa_so_o_status(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(status_code=503, text="<html>indisponível</html>")

    with pytest.raises(CceeError, match="503"):
        sessao.chamar("/ws/x", "acao", "<corpo/>")


def test_xml_com_entidade_externa_e_recusado(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(
        status_code=200,
        text='<?xml version="1.0"?><!DOCTYPE a [<!ENTITY x SYSTEM "file:///etc/passwd">]><a>&x;</a>',
    )

    with pytest.raises(DefusedXmlException):
        sessao.chamar("/ws/x", "acao", "<corpo/>")


def test_abrir_sessao_monta_a_partir_dos_dois_segredos(monkeypatch):
    credenciais = {"senha_certificado": "s-pfx", "usuario": USUARIO, "senha": SENHA, "codigo_perfil_agente": "6166"}
    monkeypatch.setattr(ccee, "ler_secret", lambda fonte, campo: json.dumps(credenciais))
    monkeypatch.setattr(ccee, "ler_secret_binario", lambda fonte, campo: PFX)

    s = ccee.abrir_sessao()

    assert (s.usuario, s.perfil, s.pfx) == (USUARIO, "6166", PFX)


def test_abrir_sessao_com_campo_faltando_nomeia_o_campo_e_nao_o_valor(monkeypatch):
    incompleta = {"senha_certificado": "s-pfx", "usuario": USUARIO}
    monkeypatch.setattr(ccee, "ler_secret", lambda fonte, campo: json.dumps(incompleta))
    monkeypatch.setattr(ccee, "ler_secret_binario", lambda fonte, campo: PFX)

    with pytest.raises(KeyError) as erro:
        ccee.abrir_sessao()

    assert "senha" in str(erro.value)
    assert "s-pfx" not in str(erro.value)
