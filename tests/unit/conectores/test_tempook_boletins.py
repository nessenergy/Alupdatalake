"""Conector TempoOK/boletins — download por dia, catálogo no Bronze, sem rede.

Escrito sem token (A7), como o do Hubspot. O que estes testes fixam é o que o
exemplo fornecido pela Alup permite afirmar; o que depende da API real está
listado no dicionário de dados e no teste de integração, que fica `skipif`.

A guarda mais importante aqui é a do item 4 da ADR 019: **resposta que não é
PDF vira ausência, não registro**. Sem ela o lake arquivaria página de erro
como se fosse boletim, e o erro só apareceria meses depois, na leitura.
"""

from datetime import date

import pytest
from src.conectores.tempook_boletins import Boletim, TempookBoletins, caminho_do_dia
from src.core.execucao import Janela

PDF = b"%PDF-1.4\n%fake boletim para teste\n%%EOF\n"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.tempook_boletins.criar_sessao", lambda **_: None)
    monkeypatch.setattr("src.conectores.tempook_boletins.ler_secret", lambda *_a, **_k: "token-de-teste")
    return TempookBoletins()


# ------------------------------------------------------- o caminho vem da data


@pytest.mark.parametrize(
    ("dia", "esperado"),
    [
        (date(2022, 3, 31), "Comercializadora/Boletins/Diario/2022-03/boletim_TOK_2022-03-31.pdf"),
        (date(2026, 1, 1), "Comercializadora/Boletins/Diario/2026-01/boletim_TOK_2026-01-01.pdf"),
        (date(2026, 12, 9), "Comercializadora/Boletins/Diario/2026-12/boletim_TOK_2026-12-09.pdf"),
    ],
)
def test_caminho_do_dia_segue_o_exemplo_fornecido(dia, esperado):
    """O primeiro caso é literalmente o exemplo do e-mail de 14/09 — é o único
    caminho que se sabe existir, e por isso é o que ancora o template."""
    assert caminho_do_dia(dia) == esperado


# --------------------------------------------------------- um boletim por dia


def test_um_registro_por_dia_da_janela(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda _c: PDF)

    registros = list(conector.extrair(Janela.de_texto("2026-03-01", "2026-03-03")))

    assert [r["data_referencia"] for r in registros] == ["2026-03-01", "2026-03-02", "2026-03-03"]


def test_dia_sem_boletim_nao_derruba_a_janela(conector, monkeypatch):
    """Feriado, fim de semana ou publicação atrasada: pula e segue."""
    monkeypatch.setattr(conector, "_baixar", lambda c: None if "2026-03-02" in c else PDF)

    registros = list(conector.extrair(Janela.de_texto("2026-03-01", "2026-03-03")))

    assert [r["data_referencia"] for r in registros] == ["2026-03-01", "2026-03-03"]


def test_janela_inteira_sem_boletim_devolve_vazio_sem_erro(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda _c: None)

    assert list(conector.extrair(Janela.de_texto("2026-03-01", "2026-03-05"))) == []


# ------------------------------------------- a guarda do %PDF- (ADR 019, item 4)


class _Resposta:
    def __init__(self, conteudo: bytes, status: int = 200, tipo: str = "application/pdf"):
        self.content = conteudo
        self.status_code = status
        self.headers = {"Content-Type": tipo}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"status {self.status_code}")


def _sessao_que_devolve(resposta):
    class SessaoFalsa:
        def post(self, url, data=None, timeout=None, allow_redirects=None):
            assert data["t"] == "token-de-teste"  # o token vem do Secret Manager
            assert timeout is not None  # nunca requisição sem timeout
            return resposta

    return SessaoFalsa()


def test_pdf_de_verdade_e_aceito(conector):
    conector._sessao = _sessao_que_devolve(_Resposta(PDF))

    assert conector._baixar("qualquer/caminho.pdf") == PDF


def test_html_de_erro_com_status_200_e_tratado_como_ausencia(conector):
    """O caso que justifica a guarda: 200 com página de erro no corpo."""
    conector._sessao = _sessao_que_devolve(_Resposta(b"<html><body>Acesso negado</body></html>", tipo="text/html"))

    assert conector._baixar("qualquer/caminho.pdf") is None


def test_corpo_vazio_com_status_200_e_tratado_como_ausencia(conector):
    conector._sessao = _sessao_que_devolve(_Resposta(b""))

    assert conector._baixar("qualquer/caminho.pdf") is None


def test_404_e_ausencia_e_nao_excecao(conector):
    conector._sessao = _sessao_que_devolve(_Resposta(b"nao encontrado", status=404))

    assert conector._baixar("qualquer/caminho.pdf") is None


# ------------------------------------------------------------------- catálogo


def test_registro_traz_o_catalogo_e_nao_o_conteudo(conector, monkeypatch):
    import hashlib

    monkeypatch.setattr(conector, "_baixar", lambda _c: PDF)

    registro = next(iter(conector.extrair(Janela.de_texto("2026-03-31", "2026-03-31"))))
    validado = Boletim.model_validate(registro)

    assert validado.data_referencia == date(2026, 3, 31)
    assert validado.nome_arquivo == "boletim_TOK_2026-03-31.pdf"
    assert validado.tamanho_bytes == len(PDF)
    assert validado.sha256 == hashlib.sha256(PDF).hexdigest()
    # O conteúdo do PDF não entra no Bronze: o que entra é o ponteiro.
    assert not any(isinstance(v, bytes) for v in registro.values())


def test_sha256_malformado_e_rejeitado():
    with pytest.raises(ValueError, match="sha256 malformado"):
        Boletim.model_validate(
            {
                "data_referencia": "2026-03-31",
                "caminho_origem": "x/y.pdf",
                "nome_arquivo": "y.pdf",
                "tamanho_bytes": 10,
                "sha256": "curto",
                "content_type": "application/pdf",
            }
        )


def test_boletim_vazio_e_rejeitado():
    """Arquivo de zero byte não é boletim; é falha de origem que passou pela guarda."""
    with pytest.raises(ValueError):
        Boletim.model_validate(
            {
                "data_referencia": "2026-03-31",
                "caminho_origem": "x/y.pdf",
                "nome_arquivo": "y.pdf",
                "tamanho_bytes": 0,
                "sha256": "a" * 64,
                "content_type": "application/pdf",
            }
        )


# -------------------------------------------------------------------- ingestão


def test_ingerir_conta_os_boletins_da_janela(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda c: None if "2026-03-02" in c else PDF)

    execucao = conector.ingerir(Janela.de_texto("2026-03-01", "2026-03-03"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0


def test_5xx_nao_e_ausencia_e_derruba_a_execucao(conector):
    """Sondagem de 14/09: um caminho que respondera 200 devolveu 503 minutos depois.

    503 significa "a origem falhou", não "não há boletim". Tratá-lo como
    ausência abriria buraco silencioso na série — o dia sumiria do lake sem
    ninguém notar. O retry da sessão já tentou; aqui a execução tem de falhar.
    """
    conector._sessao = _sessao_que_devolve(_Resposta(b"indisponivel", status=503))

    with pytest.raises(AssertionError):  # o que raise_for_status levanta no dublê
        conector._baixar("qualquer/caminho.pdf")
