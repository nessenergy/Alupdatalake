"""Sessão SOAP da Plataforma de Integração da CCEE: mTLS com o .pfx, usuário e
senha no envelope. Nada aqui toca a rede nem lê segredo de verdade."""

import json
from pathlib import Path
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
    assert "<v1:codigoPerfilAgente>6166</v1:codigoPerfilAgente>" in envelope
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


FALHA_COM_DETALHE = (
    '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><s:Fault>'
    "<faultcode>Server.2001</faultcode><faultstring>Acesso Negado</faultstring>"
    '<detail><ns2:securityFault xmlns:ns2="http://xmlns.energia.org.br/FH/v1">'
    "<ns2:errorCode>2001</ns2:errorCode>"
    f"<ns2:message>Usuario ou senha invalidos para {USUARIO}</ns2:message>"
    "<ns2:uri>/ws/medc/ListarMedidaBSv1</ns2:uri>"
    "<ns2:transactionId>tx-abc-123</ns2:transactionId>"
    "</ns2:securityFault></detail></s:Fault></s:Body></s:Envelope>"
)


def test_fault_traz_errorcode_message_e_transactionid_do_detail(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(status_code=500, text=FALHA_COM_DETALHE)

    with pytest.raises(CceeError) as erro:
        sessao.chamar("/ws/x", "acao", "<corpo/>")

    texto = str(erro.value)
    assert "Server.2001" in texto
    assert "errorCode=2001" in texto
    assert "Usuario ou senha invalidos" in texto
    assert "transactionId=tx-abc-123" in texto
    assert USUARIO not in texto  # o message da CCEE pode ecoar o usuário


def test_fault_sem_detail_continua_so_com_codigo_e_motivo(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(status_code=500, text=FALHA)

    with pytest.raises(CceeError) as erro:
        sessao.chamar("/ws/x", "acao", "<corpo/>")

    assert "transactionId" not in str(erro.value)


def test_sessao_do_piloto_chama_o_endereco_do_piloto(chamadas):
    piloto = Sessao(pfx=PFX, senha_pfx="x", usuario=USUARIO, senha=SENHA, perfil="6166", base=ccee.URL_PILOTO)

    piloto.chamar("/ws/medc/ListarMedidaBSv1", "listarMedida", "<corpo/>")

    assert chamadas.args == "https://piloto-servicos.ccee.org.br:443/ws/medc/ListarMedidaBSv1"


def test_abrir_sessao_piloto_aponta_para_o_piloto(monkeypatch):
    credenciais = {"senha_certificado": "s-pfx", "usuario": USUARIO, "senha": SENHA, "codigo_perfil_agente": "6166"}
    monkeypatch.setattr(ccee, "ler_secret", lambda fonte, campo: json.dumps(credenciais))
    monkeypatch.setattr(ccee, "ler_secret_binario", lambda fonte, campo: PFX)

    assert ccee.abrir_sessao(piloto=True).base == ccee.URL_PILOTO
    assert ccee.abrir_sessao().base == ccee.URL_BASE


def test_testar_ccee_com_piloto_abre_a_sessao_do_piloto(monkeypatch):
    pedido = {}
    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: pedido.setdefault("piloto", piloto))
    monkeypatch.setattr(ccee, "listar_medidas", lambda *a, **k: [])

    ccee.testar_ccee("P1", "2026-11-01", piloto=True)

    assert pedido["piloto"] is True


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


def test_corpo_de_listar_medida_segue_o_modelo_da_alupar():
    corpo = ccee.corpo_listar_medida("PONTO&1", "2026-11-01", "2026-11-01")

    assert "<v12:codigo>PONTO&amp;1</v12:codigo>" in corpo
    assert "<v11:tipoMedida>FINAL</v11:tipoMedida>" in corpo
    assert "<v12:inicio>2026-11-01T00:00:00</v12:inicio>" in corpo
    assert "<v12:fim>2026-11-01T23:00:00</v12:fim>" in corpo


def test_listar_medidas_devolve_as_medidas_da_resposta(sessao, chamadas):
    chamadas.resposta = SimpleNamespace(
        status_code=200,
        text=(
            '<s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"'
            ' xmlns:b="http://xmlns.energia.org.br/BM/v1"><s:Body><b:listarMedidaResponse>'
            "<b:medida/><b:medida/><b:medida/></b:listarMedidaResponse></s:Body></s:Envelope>"
        ),
    )

    assert len(ccee.listar_medidas(sessao, "P1", "2026-11-01", "2026-11-01")) == 3
    assert chamadas.kwargs["headers"]["SOAPAction"] == "listarMedida"


def test_testar_ccee_ok_informa_so_a_quantidade(monkeypatch):
    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: object())
    monkeypatch.setattr(ccee, "listar_medidas", lambda *a, **k: [1, 2])

    assert ccee.testar_ccee("P1", "2026-11-01") == (True, "ccee: ok, 2 medidas")


def test_testar_ccee_devolve_o_erro_da_ccee_sem_segredo(monkeypatch):
    def falha(*a, **k):
        raise CceeError("Fault s:Client: Acesso negado")

    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: object())
    monkeypatch.setattr(ccee, "listar_medidas", falha)

    assert ccee.testar_ccee("P1", "2026-11-01") == (False, "ccee: Fault s:Client: Acesso negado")


def test_testar_ccee_erro_inesperado_mostra_so_o_tipo(monkeypatch):
    def falha(*a, **k):
        raise ConnectionError("detalhe interno com C:/caminho/do/pfx e senha")

    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: object())
    monkeypatch.setattr(ccee, "listar_medidas", falha)

    assert ccee.testar_ccee("P1", "2026-11-01") == (False, "ccee: falha ConnectionError")


# ── cadastro de pontos de medição (PontoMedicaoBSv2, envelope v2 paginado) ─────

PAGINA_1 = (Path(__file__).parent.parent / "fixtures" / "ccee_pi" / "ponto_medicao_pagina1.xml").read_text(
    encoding="utf-8"
)
# A página 2 é a 1 renumerada, com outros códigos de ponto.
PAGINA_2 = (
    PAGINA_1.replace("<mh:numero>1</mh:numero>", "<mh:numero>2</mh:numero>")
    .replace("ABCDEFGH01-01", "ABCDEFGH03-03")
    .replace("ABCDEFGH02-02", "ABCDEFGH04-04")
)


def test_envelope_v2_leva_paginacao_perfil_e_namespaces_v2(sessao):
    envelope = sessao.envelope_v2("<corpo/>", pagina=2, itens=50)

    assert "http://xmlns.energia.org.br/MH/v2" in envelope
    assert "<mh:numero>2</mh:numero><mh:quantidadeItens>50</mh:quantidadeItens>" in envelope
    assert "<mh:codigoPerfilAgente>6166</mh:codigoPerfilAgente>" in envelope
    assert "s&amp;nh&lt;a&gt;teste" in envelope
    assert "<corpo/>" in envelope


def test_pontos_medicao_percorre_todas_as_paginas(sessao, chamadas, monkeypatch):
    paginas = iter([PAGINA_1, PAGINA_2])
    visto = []

    def post_paginado(url, **kwargs):
        visto.append((url, kwargs["headers"]["SOAPAction"], kwargs["data"].decode("utf-8")))
        return SimpleNamespace(status_code=200, text=next(paginas))

    monkeypatch.setattr(ccee, "post", post_paginado)

    codigos = [ponto.findtext(f"{{{ccee.NS_BO2}}}codigo") for ponto in ccee.pontos_medicao(sessao)]

    assert codigos == ["ABCDEFGH01-01", "ABCDEFGH02-02", "ABCDEFGH03-03", "ABCDEFGH04-04"]
    assert [v[0] for v in visto] == ["https://servicos.ccee.org.br:443/ws/v2/PontoMedicaoBSv2"] * 2
    assert {v[1] for v in visto} == {"listarPontoMedicao"}
    assert "<mh:numero>1</mh:numero>" in visto[0][2]
    assert "<mh:numero>2</mh:numero>" in visto[1][2]
    assert "<bo:nome>AGENTE_USO_FIO</bo:nome>" in visto[0][2]


def test_testar_cadastro_lista_tipo_e_perfil_sem_nomes(monkeypatch):
    xml = (
        '<e xmlns:bo="http://xmlns.energia.org.br/BO/v2"><bo:pontoMedicao><bo:agentesRelacionados>'
        "<bo:participanteMercadoRelacionado><bo:parte><bo:pessoaJuridica><bo:nomeEmpresarial>SIGILO</bo:nomeEmpresarial>"
        "</bo:pessoaJuridica></bo:parte><bo:perfis><bo:perfil><bo:codigo>999</bo:codigo></bo:perfil></bo:perfis>"
        "<bo:tipoRelacao><bo:nome>AGENTE_CONECTANTE</bo:nome></bo:tipoRelacao></bo:participanteMercadoRelacionado>"
        "</bo:agentesRelacionados></bo:pontoMedicao></e>"
    )
    from defusedxml import ElementTree

    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: object())
    monkeypatch.setattr(
        ccee, "obter_ponto", lambda s, c: ElementTree.fromstring(xml).find(f"{{{ccee.NS_BO2}}}pontoMedicao")
    )

    ok, texto = ccee.testar_cadastro("P1")

    assert ok
    assert "AGENTE_CONECTANTE perfil=999" in texto
    assert "SIGILO" not in texto


def test_testar_cadastro_sem_ponto_na_resposta(monkeypatch):
    monkeypatch.setattr(ccee, "abrir_sessao", lambda piloto=False: object())
    monkeypatch.setattr(ccee, "obter_ponto", lambda s, c: None)

    assert ccee.testar_cadastro("P1") == (False, "ccee: a resposta não trouxe o ponto")


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [(None, ()), ("", ()), (" P1, P2 ,,P3 ", ("P1", "P2", "P3"))],
)
def test_abrir_sessao_le_a_lista_opcional_de_pontos(monkeypatch, valor, esperado):
    credenciais = {"senha_certificado": "s-pfx", "usuario": USUARIO, "senha": SENHA, "codigo_perfil_agente": "6166"}
    if valor is not None:
        credenciais["pontos"] = valor
    monkeypatch.setattr(ccee, "ler_secret", lambda fonte, campo: json.dumps(credenciais))
    monkeypatch.setattr(ccee, "ler_secret_binario", lambda fonte, campo: PFX)

    assert ccee.abrir_sessao().pontos == esperado
