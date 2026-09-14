"""Conector CCEE/geração horária por usina — gzip mensal, período dentro do mês, sem rede.

O que estes testes protegem, lido do arquivo real de julho/2026 em 14/09:

- o recurso é mensal (`_202607`) e gzip: a base descomprime em fluxo;
- `PERIODO_COMERCIALIZACAO` é o índice da hora **no mês** (1..744), como no
  PLD, e `DATA` vem explícita — os dois têm de concordar, e a Silver exige isso;
- `CODIGO_PARCELA_USINA` não é CEG: `codigo_usina` fica nulo até o de-para
  (#141);
- geração vazia é registro inválido, não zero;
- `PERIODO_COMERCIALIZACAO` não numérico, fora de 1..744, ou `DATA` em formato
  que não seja `dd/mm/aaaa` conta como `linhas_invalidas` — nunca derruba a
  execução inteira (fix round 1: um `ValueError` desses escapava de
  `transformar()` e abortava o mês inteiro antes de qualquer linha boa
  carregar).
"""

from __future__ import annotations

import gzip
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from src.conectores.ccee_geracao_usina import CceeGeracaoUsina, GeracaoHorariaUsina
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_geracao_usina_202607.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_ckan.criar_sessao", lambda: None)
    conector = CceeGeracaoUsina()
    monkeypatch.setattr(
        conector,
        "_pacote",
        lambda: {
            "resources": [
                {
                    "name": "geracao_horaria_usina_202607",
                    "url": "u",
                    "format": "GZIP",
                    "last_modified": "2026-09-01T10:00:00",
                }
            ]
        },
    )
    # A fixture é texto; o conector recebe gzip, como na origem.
    monkeypatch.setattr(conector, "_abrir", lambda _s: io.BytesIO(gzip.compress(FIXTURE.read_bytes())))
    return conector


def test_recurso_e_mensal():
    assert CceeGeracaoUsina.recurso_por == "mes"


def test_extrai_o_mes_do_recurso_gzip(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31")))

    assert len(registros) == 6
    assert registros[0]["_sufixo"] == "202607"


def test_transformar_deriva_hora_do_periodo_e_converte_submercado(conector):
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    registro = GeracaoHorariaUsina.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 7, 1)
    assert registro.hora == 0
    assert registro.periodo_comercializacao == 1
    assert registro.periodo_apuracao_ccee == "2026-07"
    assert registro.codigo_parcela_usina == "201"
    assert registro.sigla_usina == "UHE ALFA"
    assert registro.submercado == "SE"  # SUDESTE por extenso vira sigla
    assert registro.tipo_usina == "Hidráulicas MRE"
    assert registro.geracao_centro_gravidade == Decimal("22.702357")
    assert registro.garantia_fisica_rrh_modulada_ajustada_2 == Decimal("126.399655")
    assert registro.custo_declarado_parcela_usina is None


def test_periodo_25_e_a_hora_zero_do_dia_dois(conector):
    registros = [
        GeracaoHorariaUsina.model_validate(conector.transformar(b))
        for b in conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))
        if b["PERIODO_COMERCIALIZACAO"] == "025"
    ]

    assert registros[0].data_referencia == date(2026, 7, 2)
    assert registros[0].hora == 0


def test_data_que_nao_bate_com_o_periodo_e_rejeitada(conector):
    """A CCEE publica os dois; se discordarem, a origem mudou a regra — não escolhemos por ela."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-07-01", "2026-07-31"))))
    bruto = bruto | {"DATA": "15/07/2026"}  # período 1 é dia 1, não 15

    with pytest.raises(ValueError, match="DATA .* período"):
        GeracaoHorariaUsina.model_validate(conector.transformar(bruto))


def test_geracao_vazia_e_registro_invalido_nao_zero(conector):
    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-07-31"))

    assert execucao.linhas_extraidas == 6
    assert execucao.linhas_invalidas == 1  # a EOL BETA sem geração
    assert execucao.status == "SUCESSO"


def _linha_fixture(indice_da_linha: int = 1) -> list[str]:
    """Uma linha de dado da fixture real, como lista de campos (36 colunas)."""
    linhas = FIXTURE.read_text(encoding="utf-8").splitlines()
    return linhas[indice_da_linha].split(";")


def _payload(*linhas_de_dado: str) -> io.BytesIO:
    """Um recurso gzip mínimo: o cabeçalho real da fixture + as linhas dadas."""
    cabecalho = FIXTURE.read_text(encoding="utf-8").splitlines()[0]
    texto = "\n".join([cabecalho, *linhas_de_dado]) + "\n"
    return io.BytesIO(gzip.compress(texto.encode("utf-8")))


@pytest.mark.parametrize(
    ("indice", "valor"),
    [
        (2, "abc"),  # PERIODO_COMERCIALIZACAO não numérico
        (2, "745"),  # período fora do mês (julho tem 31 dias: 744 é o máximo)
        (1, "2026-07-01"),  # DATA em ISO, não dd/mm/aaaa
    ],
    ids=["periodo_nao_numerico", "periodo_fora_do_mes", "data_em_formato_errado"],
)
def test_periodo_ou_data_malformados_contam_como_invalidos_nao_derrubam_o_mes(conector, monkeypatch, indice, valor):
    """Regressão (fix round 1): um valor malformado não pode abortar o mês inteiro.

    Antes da correção, `int(...)` e `datetime.strptime(...)` rodavam dentro de
    `transformar()`, fora do `try/except ValidationError` do runner — um
    `ValueError` ali escapava, e a linha discordante derrubava as ~3 milhões de
    linhas do mês em vez de contar como `linhas_invalidas`.
    """
    boa = ";".join(_linha_fixture())
    campos_ruins = _linha_fixture()
    campos_ruins[indice] = valor
    ruim = ";".join(campos_ruins)
    monkeypatch.setattr(conector, "_abrir", lambda _s: _payload(boa, ruim))

    execucao = conector.ingerir(Janela.de_texto("2026-07-01", "2026-07-31"))

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 2
    assert execucao.linhas_invalidas == 1


def test_tipo_de_usina_desconhecido_e_rejeitado():
    with pytest.raises(ValueError):
        GeracaoHorariaUsina.model_validate(
            {
                "data_referencia": "2026-07-01",
                "hora": 0,
                "periodo_comercializacao": 1,
                "periodo_apuracao_ccee": "2026-07",
                "versao_publicacao": "2026-09-01",
                "codigo_parcela_usina": "1",
                "sigla_usina": "X",
                "fonte_primaria": "X",
                "submercado": "SE",
                "tipo_usina": "Nuclear",
                "geracao_centro_gravidade": "1",
                "fator_perda_interna": "1",
                "fator_rateio_perda_geracao": "1",
            }
        )
