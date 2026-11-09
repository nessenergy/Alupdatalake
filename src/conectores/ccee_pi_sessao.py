"""Sessão SOAP da Plataforma de Integração da CCEE (ADR 018, via de acesso 2).

Como a Alupar acessa hoje (confirmado em 04/11/2026 com o código de
produção deles): o certificado .pfx vai na conexão HTTPS (mTLS) e o usuário e
a senha vão dentro do envelope SOAP. São duas credenciais distintas: a senha do
.pfx e a senha do usuário.

O .pfx vem do Secret Manager como bytes e fica em memória; nada é gravado em
disco. Usuário, senha e perfil vêm do JSON `alupdata-ccee-credenciais`.

O envelope segue o modelo de produção da Alupar (`geracao_xml.xml`, de
04/11/2026), igual ao exemplo da coleção Postman da CCEE. Cada endpoint tem o
seu corpo; aqui só existe o de `listarMedida` (`ListarMedidaBSv1`).
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
# Piloto: mesmas credenciais da produção, dados com um mês de defasagem.
URL_PILOTO = "https://piloto-servicos.ccee.org.br:443"

# A CCEE aceita 400 chamadas por minuto (erro 2003); 0,2 s de intervalo dá 300.
_INTERVALO_S = 0.2

_NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
_NS_BM = "http://xmlns.energia.org.br/BM/v1"

_ENVELOPE = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    f'<soapenv:Envelope xmlns:soapenv="{_NS_SOAP}"'
    ' xmlns:oas="http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd"'
    ' xmlns:v1="http://xmlns.energia.org.br/MH/v1"'
    f' xmlns:v11="{_NS_BM}"'
    ' xmlns:v12="http://xmlns.energia.org.br/BO/v1">'
    "<soapenv:Header>"
    "<v1:messageHeader><v1:codigoPerfilAgente>{perfil}</v1:codigoPerfilAgente></v1:messageHeader>"
    "<oas:Security><oas:UsernameToken>"
    "<oas:Username>{usuario}</oas:Username>"
    "<oas:Password>{senha}</oas:Password>"
    "</oas:UsernameToken></oas:Security>"
    "</soapenv:Header>"
    "<soapenv:Body>{corpo}</soapenv:Body>"
    "</soapenv:Envelope>"
)

CAMINHO_MEDIDA = "/ws/medc/ListarMedidaBSv1"


class CceeError(RuntimeError):
    """Falha da CCEE. A mensagem nunca carrega usuário, senha nem o envelope."""


@dataclass(frozen=True)
class Sessao:
    pfx: bytes
    senha_pfx: str = ""
    usuario: str = ""
    senha: str = ""
    perfil: str = ""
    base: str = URL_BASE

    def __repr__(self) -> str:  # o dataclass padrão imprimiria as senhas
        return f"Sessao(usuario={self.usuario!r}, perfil={self.perfil!r}, base={self.base!r})"

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
            self.base + caminho,
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
                # `detail` traz errorCode, message e transactionId (o que a CCEE pede
                # para rastrear). Só esses três campos; nunca o envelope enviado.
                detalhe = {
                    elemento.tag.rsplit("}", 1)[-1]: (elemento.text or "").strip()
                    for elemento in falha.iter()
                    if elemento.tag.rsplit("}", 1)[-1] in ("errorCode", "message", "transactionId")
                }
                extra = "".join(f" [{k}={self._sem_segredo(v)}]" for k, v in detalhe.items() if v)
                raise CceeError(f"Fault {codigo}: {self._sem_segredo(motivo)}{extra}")
        if resposta.status_code >= 400:
            raise CceeError(f"HTTP {resposta.status_code} em {caminho}")
        if raiz is None:
            raise CceeError(f"resposta sem XML válido em {caminho}")
        return raiz


def abrir_sessao(piloto: bool = False) -> Sessao:
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
        base=URL_PILOTO if piloto else URL_BASE,
    )


def corpo_listar_medida(ponto: str, inicio: str, fim: str, tipo: str = "FINAL") -> str:
    """Corpo de `listarMedida`. Datas em YYYY-MM-DD; o fim vai até 23:00 do dia."""
    return (
        "<v11:listarMedida>"
        f"<v11:pontoMedicao><v12:codigo>{escape(ponto)}</v12:codigo></v11:pontoMedicao>"
        f"<v11:tipoMedida>{escape(tipo)}</v11:tipoMedida>"
        f"<v11:periodo><v12:inicio>{escape(inicio)}T00:00:00</v12:inicio>"
        f"<v12:fim>{escape(fim)}T23:00:00</v12:fim></v11:periodo>"
        "</v11:listarMedida>"
    )


def listar_medidas(sessao: Sessao, ponto: str, inicio: str, fim: str, tipo: str = "FINAL") -> list:
    """Elementos `medida` devolvidos pela CCEE para o ponto e o período."""
    raiz = sessao.chamar(CAMINHO_MEDIDA, "listarMedida", corpo_listar_medida(ponto, inicio, fim, tipo))
    return raiz.findall(f".//{{{_NS_BM}}}medida")


def testar_ccee(ponto: str, dia: str, piloto: bool = False) -> tuple[bool, str]:
    """Uma única chamada de leitura, para provar credencial e certificado.

    Devolve só o resultado: a quantidade de medidas ou o motivo da CCEE. Erro
    inesperado mostra apenas o tipo, porque a mensagem de biblioteca de TLS
    pode trazer caminho e detalhe do certificado. Sem retry: errar a senha de
    um usuário pessoal repetidas vezes pode bloqueá-lo.
    """
    try:
        medidas = listar_medidas(abrir_sessao(piloto), ponto, dia, dia)
    except CceeError as erro:
        return False, f"ccee: {erro}"
    except Exception as erro:  # noqa: BLE001 — a mensagem pode carregar segredo
        return False, f"ccee: falha {type(erro).__name__}"
    return True, f"ccee: ok, {len(medidas)} medidas"
