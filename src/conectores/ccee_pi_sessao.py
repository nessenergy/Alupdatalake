"""Sessão SOAP da Plataforma de Integração da CCEE (ADR 018, via de acesso 2).

Como a Alupar acessa hoje (confirmado em 04/11/2026 com o código de
produção deles): o certificado .pfx vai na conexão HTTPS (mTLS) e o usuário e
a senha vão dentro do envelope SOAP. São duas credenciais distintas: a senha do
.pfx e a senha do usuário.

O .pfx vem do Secret Manager como bytes e fica em memória; nada é gravado em
disco. Usuário, senha e perfil vêm do JSON `alupdata-ccee-credenciais`.

ponytail: o cabeçalho de segurança segue a documentação (WS-Security
UsernameToken); se o template de produção da Alupar (`geracao_xml.xml`) for
diferente, é só `Sessao.envelope` que muda.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from xml.sax.saxutils import escape

from defusedxml import ElementTree
from requests_pkcs12 import post

from src.core.config import get_settings
from src.core.secrets import ler_secret, ler_secret_binario

URL_BASE = "https://servicos.ccee.org.br:443"

# A CCEE aceita 400 chamadas por minuto (erro 2003); 0,2 s de intervalo dá 300.
_INTERVALO_S = 0.2

_NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
_NS_WSSE = "http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"

_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}" xmlns:wsse="{_NS_WSSE}">'
    "<soapenv:Header>"
    "<wsse:Security><wsse:UsernameToken>"
    "<wsse:Username>{usuario}</wsse:Username>"
    "<wsse:Password>{senha}</wsse:Password>"
    "</wsse:UsernameToken></wsse:Security>"
    "<codigoPerfilAgente>{perfil}</codigoPerfilAgente>"
    "</soapenv:Header>"
    "<soapenv:Body>{corpo}</soapenv:Body>"
    "</soapenv:Envelope>"
)


class CceeError(RuntimeError):
    """Falha da CCEE. A mensagem nunca carrega usuário, senha nem o envelope."""


@dataclass(frozen=True)
class Sessao:
    pfx: bytes
    senha_pfx: str = ""
    usuario: str = ""
    senha: str = ""
    perfil: str = ""

    def __repr__(self) -> str:  # o dataclass padrão imprimiria as senhas
        return f"Sessao(usuario={self.usuario!r}, perfil={self.perfil!r})"

    def envelope(self, corpo: str) -> str:
        return _ENVELOPE.format(
            usuario=escape(self.usuario), senha=escape(self.senha), perfil=escape(self.perfil), corpo=corpo
        )

    def _sem_segredo(self, texto: str) -> str:
        for segredo in (self.senha, self.senha_pfx, self.usuario):
            if segredo:
                texto = texto.replace(segredo, "***")
        return texto

    def chamar(self, caminho: str, acao: str, corpo: str):
        """Uma chamada SOAP; devolve a raiz do XML de resposta."""
        time.sleep(_INTERVALO_S)
        resposta = post(
            URL_BASE + caminho,
            headers={"Content-Type": "text/xml; charset=utf-8", "SOAPAction": acao},
            data=self.envelope(corpo).encode("utf-8"),
            pkcs12_data=self.pfx,
            pkcs12_password=self.senha_pfx,
            timeout=get_settings().http_timeout,
        )
        # Fault vem com HTTP 500; lê o XML antes de olhar o status para dar o motivo.
        try:
            raiz = ElementTree.fromstring(resposta.text)
        except ElementTree.ParseError:
            raiz = None
        if raiz is not None:
            falha = raiz.find(f".//{{{_NS_SOAP}}}Fault")
            if falha is not None:
                codigo = (falha.findtext("faultcode") or "?").strip()
                motivo = (falha.findtext("faultstring") or "").strip()
                raise CceeError(f"Fault {codigo}: {self._sem_segredo(motivo)}")
        if resposta.status_code >= 400:
            raise CceeError(f"HTTP {resposta.status_code} em {caminho}")
        if raiz is None:
            raise CceeError(f"resposta sem XML válido em {caminho}")
        return raiz


def abrir_sessao() -> Sessao:
    """Monta a sessão a partir dos dois segredos. Falta de campo nomeia o campo, não o valor."""
    credenciais = json.loads(ler_secret("ccee", "credenciais"))
    faltam = [c for c in ("senha_certificado", "usuario", "senha", "codigo_perfil_agente") if not credenciais.get(c)]
    if faltam:
        raise KeyError(f"alupdata-ccee-credenciais sem os campos: {', '.join(faltam)}")
    return Sessao(
        pfx=ler_secret_binario("ccee", "certificado"),
        senha_pfx=credenciais["senha_certificado"],
        usuario=credenciais["usuario"],
        senha=credenciais["senha"],
        perfil=str(credenciais["codigo_perfil_agente"]),
    )
