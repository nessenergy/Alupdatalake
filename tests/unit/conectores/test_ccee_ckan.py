"""Base dos conectores CSV da CCEE via CKAN — descoberta, streaming e decodificação, sem rede.

O que estes testes protegem, e que a leitura dos arquivos reais em 14/09 mostrou:

- os CSVs da CCEE misturam UTF-8 e ISO-8859-1 **no mesmo arquivo**: em
  `lista_agente_associado_2026`, 49.269 linhas decodificam como UTF-8 e 98.532
  só como ISO-8859-1. Decodificar o arquivo inteiro num encoding só mutila
  metade dele em silêncio;
- `geracao_horaria_usina` vem gzip e por mês (`_202607`); os outros, CSV por ano;
- a janela recorta pelo `MES_REFERENCIA`, não por dia;
- `versao_publicacao` vem do `last_modified` do CKAN (ADR 016, opção B).
"""

from __future__ import annotations

import gzip
import io
from datetime import date

import pytest
from src.conectores.ccee_ckan import (
    CceeCsvCkan,
    decodificar,
    numero_ou_nulo,
    periodo_ccee,
    primeiro_dia,
)
from src.core.execucao import Janela

CSV = "MES_REFERENCIA;SIGLA;VALOR\n202601;ALFA;1.5\n202602;BETA;\n202603;GAMA;3\n"


class Dummy(CceeCsvCkan):
    """Subclasse mínima: só o que a base exige."""

    dataset = "dummy_mensal"
    entidade = "dummy"
    schema = None  # não passa pelo runner nestes testes

    def transformar(self, bruto):  # pragma: no cover — não usado aqui
        return bruto


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Dummy()
    pacote = {
        "resources": [
            {
                "name": "dummy_mensal_2025",
                "url": "https://exemplo/2025",
                "format": "CSV",
                "last_modified": "2026-02-02T17:36:17",
            },
            {
                "name": "dummy_mensal_2026",
                "url": "https://exemplo/2026",
                "format": "CSV",
                "last_modified": "2026-09-01T14:50:45",
            },
        ]
    }
    monkeypatch.setattr(conector, "_pacote", lambda: pacote)
    monkeypatch.setattr(conector, "_abrir", lambda _sufixo: io.BytesIO(CSV.encode("iso-8859-1")))
    return conector


# ------------------------------------------------------------ decodificação


def test_linha_utf8_e_linha_latin1_no_mesmo_arquivo_decodificam_as_duas():
    assert decodificar("Comercialização".encode()) == "Comercialização"
    assert decodificar("Comercialização".encode("iso-8859-1")) == "Comercialização"


def test_linha_ascii_passa_intacta():
    assert decodificar(b"202601;ALFA;1.5") == "202601;ALFA;1.5"


# ------------------------------------------------------------- utilitários


def test_primeiro_dia_do_mes_de_referencia():
    assert primeiro_dia("202607") == date(2026, 7, 1)


def test_mes_de_referencia_vira_periodo_ccee():
    assert periodo_ccee("202607") == "2026-07"


def test_mes_de_referencia_invalido_e_recusado():
    with pytest.raises(ValueError):
        primeiro_dia("2026-07")


def test_vazio_vira_nulo_e_zero_continua_zero():
    assert numero_ou_nulo("") is None
    assert numero_ou_nulo(None) is None
    assert numero_ou_nulo("0") == "0"
    assert numero_ou_nulo(" 1.5 ") == "1.5"


# ------------------------------------------------------------ janela e recorte


def test_extrai_so_os_meses_dentro_da_janela(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-02-01", "2026-02-28")))

    assert [r["SIGLA"] for r in registros] == ["BETA"]


def test_janela_no_meio_do_mes_ainda_alcanca_o_mes_inteiro(conector):
    """A CCEE publica por mês; uma janela de 15/01 a 20/02 pede janeiro e fevereiro inteiros."""
    registros = list(conector.extrair(Janela.de_texto("2026-01-15", "2026-02-20")))

    assert [r["SIGLA"] for r in registros] == ["ALFA", "BETA"]


def test_cada_bruto_carrega_a_versao_de_publicacao_e_o_sufixo(conector):
    registro = next(iter(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31"))))

    assert registro["_versao_publicacao"] == "2026-09-01"
    assert registro["_sufixo"] == "2026"


def test_janela_que_cruza_o_ano_abre_cada_ano(conector, monkeypatch):
    abertos = []
    monkeypatch.setattr(conector, "_abrir", lambda s: abertos.append(s) or io.BytesIO(b"MES_REFERENCIA;SIGLA;VALOR\n"))

    list(conector.extrair(Janela.de_texto("2025-12-01", "2026-01-31")))

    assert abertos == ["2025", "2026"]


def test_recurso_mensal_usa_sufixo_aaaamm(monkeypatch):
    class Mensal(Dummy):
        recurso_por = "mes"

    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Mensal()
    abertos = []
    monkeypatch.setattr(conector, "_abrir", lambda s: abertos.append(s) or io.BytesIO(b"MES_REFERENCIA;SIGLA;VALOR\n"))

    list(conector.extrair(Janela.de_texto("2026-06-10", "2026-08-01")))

    assert abertos == ["202606", "202607", "202608"]


def test_recurso_ausente_vira_aviso_e_nao_derruba(conector, monkeypatch, caplog):
    def abrir(sufixo):
        if sufixo == "2025":
            raise FileNotFoundError("dummy_mensal_2025 não publicado")
        return io.BytesIO(CSV.encode("iso-8859-1"))

    monkeypatch.setattr(conector, "_abrir", abrir)

    registros = list(conector.extrair(Janela.de_texto("2025-12-01", "2026-01-31")))

    assert [r["SIGLA"] for r in registros] == ["ALFA"]
    assert "2025" in caplog.text


# ------------------------------------------------------------------- gzip


def test_recurso_gzip_e_descomprimido_em_fluxo(conector, monkeypatch):
    comprimido = gzip.compress(CSV.encode("iso-8859-1"))
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(comprimido))

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-03-31")))

    assert len(registros) == 3


class _FechaAoEsgotar(io.BytesIO):
    """Simula o socket HTTP que a CCEE fecha assim que o corpo termina de chegar.

    Visto contra a API real em 14/09/2026 (`lista_agente_associado_2026`, que a
    CDN entrega com `Content-Encoding: gzip`): a leitura que o `gzip` faz a mais
    para conferir o rodapé do arquivo batia num arquivo já fechado.
    """

    def read(self, *args, **kwargs):
        if self.tell() >= len(self.getvalue()):
            self.close()  # o `.closed` real é o que o envelope confere, não a mensagem
            raise ValueError("read of closed file")
        return super().read(*args, **kwargs)


def test_conexao_fechada_pelo_servidor_apos_o_corpo_nao_derruba_a_leitura(conector, monkeypatch):
    comprimido = gzip.compress(CSV.encode("iso-8859-1"))
    monkeypatch.setattr(conector, "_abrir", lambda _s: _FechaAoEsgotar(comprimido))

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-03-31")))

    assert len(registros) == 3


class _ErroAlheio(io.BytesIO):
    """Levanta `ValueError` por outro motivo, sem nunca fechar de verdade.

    O envelope só deve tratar como EOF a leitura pós-fechamento (`.closed`
    real); qualquer outro `ValueError` — disco cheio, conexão resetada, o que
    for — precisa subir como erro, não virar sucesso silencioso. `_SemErroAoFechar`
    chama `.read()` no fluxo bruto (não `.readinto()`), então é `.read()` que
    precisa levantar aqui. A primeira chamada (o `peek()` de detecção de gzip)
    passa normalmente; a partir da segunda, sempre levanta.
    """

    def read(self, *args, **kwargs):
        if self.tell() > 0:
            raise ValueError("defeito qualquer, nao fechamento")
        return super().read(*args, **kwargs)


def test_valueerror_sem_relacao_com_fechamento_nao_vira_eof_silencioso(conector, monkeypatch):
    comprimido = gzip.compress(CSV.encode("iso-8859-1"))
    monkeypatch.setattr(conector, "_abrir", lambda _s: _ErroAlheio(comprimido))

    with pytest.raises(ValueError, match="defeito qualquer"):
        list(conector.extrair(Janela.de_texto("2026-01-01", "2026-03-31")))


# --------------------------------------------------------------- descoberta


def test_url_do_recurso_vem_do_ckan_pelo_sufixo(conector):
    assert conector._recurso("2026")["url"] == "https://exemplo/2026"


def test_sufixo_sem_recurso_levanta_erro_nomeado(conector):
    with pytest.raises(FileNotFoundError, match="2027"):
        conector._recurso("2027")


def test_publicado_em_le_o_last_modified(conector):
    assert conector.publicado_em("2026") == date(2026, 9, 1)


def test_publicado_em_sem_last_modified_assume_hoje_e_avisa(conector, monkeypatch, caplog):
    monkeypatch.setattr(conector, "_pacote", lambda: {"resources": [{"name": "dummy_mensal_2026", "url": "u"}]})

    assert conector.publicado_em("2026") == date.today()
    assert "last_modified" in caplog.text


def test_delimitador_virgula_e_respeitado(monkeypatch):
    class Virgula(Dummy):
        delimitador = ","

    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = Virgula()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {"resources": [{"name": "dummy_mensal_2026", "url": "u", "last_modified": "2026-09-01T00:00:00"}]},
    )
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(b"MES_REFERENCIA,SIGLA,VALOR\n202601,ALFA,1.5\n"))

    registros = list(conector.extrair(Janela.de_texto("2026-01-01", "2026-01-31")))

    assert registros[0]["SIGLA"] == "ALFA"
