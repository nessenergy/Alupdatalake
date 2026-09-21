"""Conector TempoOK/ENA-PREVS — um tar.gz por dia, catálogo no Bronze, sem rede.

O caminho de exemplo veio da Alup em 18/09/2026 e foi conferido contra a origem
real em 21/09: 43 de 45 dias respondem (diário, inclusive fim de semana), ~94
KB por arquivo. Estes testes fixam o que essa conferência permite afirmar; o
conteúdo dos tar.gz não entra no repositório — os que aparecem aqui são sintéticos.

A guarda que importa é a mesma do boletim (ADR 019, item 4), com a assinatura
do gzip no lugar da do PDF: **resposta que não é o arquivo esperado vira
ausência, não registro**.
"""

import hashlib
import io
import tarfile
from datetime import date

import pytest
from src.conectores.tempook_ena_prevs import ArquivoEnaPrevs, TempookEnaPrevs, caminho_do_dia
from src.core.execucao import Janela

MODELO = "ECENSav-ETA40-GEFSav-ECENS45-av_upt"


def _tar_gz_sintetico() -> bytes:
    """Um tar.gz mínimo e falso, com a mesma forma do real (arquivos .txt)."""
    saida = io.BytesIO()
    with tarfile.open(fileobj=saida, mode="w:gz") as tar:
        conteudo = b"ENA - subsystem: (conteudo sintetico de teste)\n"
        info = tarfile.TarInfo("2026_9_rev2_teste.txt")
        info.size = len(conteudo)
        tar.addfile(info, io.BytesIO(conteudo))
    return saida.getvalue()


ARQUIVO = _tar_gz_sintetico()


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.tempook_arquivos.criar_sessao", lambda **_: None)
    monkeypatch.setattr("src.conectores.tempook_arquivos.ler_secret", lambda *_a, **_k: "token-de-teste")
    return TempookEnaPrevs()


# ------------------------------------------------------- o caminho vem da data


def test_caminho_do_dia_e_o_exemplo_fornecido_pela_alup():
    """É literalmente o exemplo de 18/09 — o único caminho que se sabe existir,
    e por isso o que ancora o template."""
    esperado = (
        "Comercializadora/Arquivos/ENA-PREVS/ECENSav-ETA40-GEFSav-ECENS45_upt/"
        "ECENSav-ETA40-GEFSav-ECENS45-av_upt/2026-09/"
        "ENA-PREVS_ECENSav-ETA40-GEFSav-ECENS45-av_upt_20260915.tar.gz"
    )

    assert caminho_do_dia(date(2026, 9, 15)) == esperado


def test_o_mes_da_pasta_e_o_do_dia_nao_o_da_janela():
    """A pasta é `AAAA-MM` do próprio arquivo: janela que cruza o mês muda de pasta."""
    assert "/2026-08/" in caminho_do_dia(date(2026, 8, 31))
    assert "/2026-09/" in caminho_do_dia(date(2026, 9, 1))


# --------------------------------------------------------- um arquivo por dia


def test_um_registro_por_dia_da_janela(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda _c: ARQUIVO)

    registros = list(conector.extrair(Janela.de_texto("2026-09-13", "2026-09-15")))

    assert [r["data_referencia"] for r in registros] == ["2026-09-13", "2026-09-14", "2026-09-15"]


def test_dia_sem_arquivo_nao_derruba_a_janela(conector, monkeypatch):
    """Na sondagem de 21/09, 15/08, 05/09 e 19/09 devolveram 404 no meio de uma série
    diária. Buraco existe, e a execução tem de seguir."""
    monkeypatch.setattr(conector, "_baixar", lambda c: None if "20260914" in c else ARQUIVO)

    registros = list(conector.extrair(Janela.de_texto("2026-09-13", "2026-09-15")))

    assert [r["data_referencia"] for r in registros] == ["2026-09-13", "2026-09-15"]


def test_fim_de_semana_nao_e_pulado(conector, monkeypatch):
    """Diferente do boletim, que só sai em dia útil: este produto é diário, e
    sábado e domingo chegaram 200 em 21/09. Pular fim de semana perderia dado."""
    monkeypatch.setattr(conector, "_baixar", lambda _c: ARQUIVO)

    registros = list(conector.extrair(Janela.de_texto("2026-09-12", "2026-09-13")))  # sábado e domingo

    assert len(registros) == 2


# ------------------------------------------- a guarda do gzip (ADR 019, item 4)


class _Resposta:
    def __init__(self, conteudo: bytes, status: int = 200, tipo: str = "application/octet-stream"):
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


def test_gzip_de_verdade_e_aceito(conector):
    conector._sessao = _sessao_que_devolve(_Resposta(ARQUIVO))

    assert conector._baixar("qualquer/caminho.tar.gz") == ARQUIVO


def test_html_de_erro_com_status_200_e_tratado_como_ausencia(conector):
    conector._sessao = _sessao_que_devolve(_Resposta(b"<html><body>Acesso negado</body></html>", tipo="text/html"))

    assert conector._baixar("qualquer/caminho.tar.gz") is None


def test_404_devolve_20_bytes_de_texto_e_e_ausencia(conector):
    """O 404 real da origem tem corpo de 20 bytes (visto em 21/09)."""
    conector._sessao = _sessao_que_devolve(_Resposta(b"nao encontrado......", status=404))

    assert conector._baixar("qualquer/caminho.tar.gz") is None


def test_5xx_nao_e_ausencia_e_derruba_a_execucao(conector):
    """503 é "a origem falhou", não "não há arquivo": tratá-lo como ausência
    abriria buraco silencioso na série."""
    conector._sessao = _sessao_que_devolve(_Resposta(b"indisponivel", status=503))

    with pytest.raises(AssertionError):
        conector._baixar("qualquer/caminho.tar.gz")


def test_pdf_nao_e_aceito_como_ena_prevs(conector):
    """A assinatura é por produto: um PDF no caminho do ENA-PREVS é anomalia."""
    conector._sessao = _sessao_que_devolve(_Resposta(b"%PDF-1.4\n%%EOF\n", tipo="application/pdf"))

    assert conector._baixar("qualquer/caminho.tar.gz") is None


# ------------------------------------------------------------------- catálogo


def test_registro_traz_o_catalogo_e_nao_o_conteudo(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda _c: ARQUIVO)

    registro = next(iter(conector.extrair(Janela.de_texto("2026-09-15", "2026-09-15"))))
    validado = ArquivoEnaPrevs.model_validate(registro)

    assert validado.data_referencia == date(2026, 9, 15)
    assert validado.nome_arquivo == f"ENA-PREVS_{MODELO}_20260915.tar.gz"
    assert validado.modelo == MODELO
    assert validado.tamanho_bytes == len(ARQUIVO)
    assert validado.sha256 == hashlib.sha256(ARQUIVO).hexdigest()
    assert validado.content_type == "application/gzip"
    assert not any(isinstance(v, bytes) for v in registro.values())


def test_modelo_e_coluna_porque_a_alup_vai_indicar_outros_caminhos(conector, monkeypatch):
    """Só uma combinação de modelos é conhecida hoje; a Alup vai apontar as
    demais. Sem `modelo` na tabela, cada uma nova pediria mudança de schema no
    Bronze, que é append-only."""
    monkeypatch.setattr(conector, "_baixar", lambda _c: ARQUIVO)

    registro = next(iter(conector.extrair(Janela.de_texto("2026-09-15", "2026-09-15"))))

    assert "modelo" in registro


def test_sha256_malformado_e_rejeitado():
    with pytest.raises(ValueError, match="sha256 malformado"):
        ArquivoEnaPrevs.model_validate(_registro_minimo(sha256="curto"))


def test_arquivo_vazio_e_rejeitado():
    with pytest.raises(ValueError):
        ArquivoEnaPrevs.model_validate(_registro_minimo(tamanho_bytes=0))


# -------------------------------------------------------------------- ingestão


def test_ingerir_conta_os_arquivos_da_janela(conector, monkeypatch):
    monkeypatch.setattr(conector, "_baixar", lambda c: None if "20260914" in c else ARQUIVO)

    execucao = conector.ingerir(Janela.de_texto("2026-09-13", "2026-09-15"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 0


def _registro_minimo(**troca):
    base = {
        "data_referencia": "2026-09-15",
        "caminho_origem": "x/y.tar.gz",
        "nome_arquivo": "y.tar.gz",
        "tamanho_bytes": 10,
        "sha256": "a" * 64,
        "content_type": "application/gzip",
        "modelo": MODELO,
    }
    return base | troca
