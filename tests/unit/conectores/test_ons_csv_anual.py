"""Base `OnsCsvAnual` — o que a extração garante para todo conector do padrão A."""

import pytest
from src.conectores.ons_ear_bacia import OnsEarBacia
from src.core.execucao import Janela


class _Resposta:
    def __init__(self, status: int, conteudo: bytes = b"") -> None:
        self.status_code = status
        self.content = conteudo

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class _Sessao:
    def __init__(self, resposta: _Resposta) -> None:
        self.resposta = resposta
        self.urls: list[str] = []

    def get(self, url, timeout):
        self.urls.append(url)
        return self.resposta


@pytest.fixture
def conector_com(monkeypatch):
    def _fabrica(resposta):
        sessao = _Sessao(resposta)
        monkeypatch.setattr("src.conectores.ons_csv_anual.criar_sessao", lambda: sessao)
        return OnsEarBacia(), sessao

    return _fabrica


def test_monta_a_url_do_ano(conector_com):
    conector, sessao = conector_com(_Resposta(404))
    list(conector.extrair(Janela.de_texto("2025-12-31", "2026-01-01")))

    assert sessao.urls[0].endswith("ear_bacia_di/EAR_DIARIO_BACIAS_2025.csv")
    assert sessao.urls[1].endswith("ear_bacia_di/EAR_DIARIO_BACIAS_2026.csv")


def test_linha_em_iso_8859_1_nao_vira_caractere_trocado(conector_com):
    """Os arquivos conferidos em 28/09 são UTF-8; um ano em ISO-8859-1 não pode corromper texto."""
    conteudo = b"nomecurto;ear_data;ear_max_bacia;ear_verif_bacia_mwmes;ear_verif_bacia_percentual\n"
    conteudo += "PARAGUAÇU;2026-03-04;1;1;100\n".encode("iso-8859-1")
    conector, _ = conector_com(_Resposta(200, conteudo))

    [linha] = list(conector.extrair(Janela.de_texto("2026-03-04", "2026-03-04")))

    assert linha["nomecurto"] == "PARAGUAÇU"


def test_ano_ausente_vira_aviso_e_nao_erro(conector_com, caplog):
    conector, _ = conector_com(_Resposta(404))

    with caplog.at_level("WARNING"):
        assert list(conector.extrair(Janela.de_texto("1999-01-01", "1999-01-02"))) == []
    assert any("1999" in r.message for r in caplog.records)
