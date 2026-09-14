"""Conector CCEE/perfil — cadastro de perfis de agente, sem rede.

Esta é a fonte da dimensão comum `agente_ccee`, que estava sem origem desde o
início do projeto. O que os testes protegem, e que o código não deixa óbvio:

- é **cadastro**, não série: não há coluna de data, e `data_referencia` vem do
  `last_modified` que o CKAN declara para o recurso;
- o dataset `lista_perfil` foi **descontinuado** pela CCEE (CO 562/25); o vivo é
  `lista_perfil_v1`, e apontar para o errado traria dado que congela em 2025;
- `SUBMERCADO` vem sujo: perfil sem submercado traz **espaço não separável**
  (`\xa0`), não string vazia.
"""

from datetime import date
from pathlib import Path

import pytest
from src.conectores.ccee_perfil import DATASET, CceePerfil, PerfilAgente
from src.core.execucao import Janela

FIXTURE = Path(__file__).parents[2] / "fixtures" / "ccee_perfil_2026.csv"


@pytest.fixture
def conector(monkeypatch):
    monkeypatch.setattr("src.conectores.ccee_perfil.criar_sessao", lambda: None)
    conector = CceePerfil()
    monkeypatch.setattr(
        conector,
        "_recurso_mais_recente",
        lambda: ("https://exemplo/2026", date(2026, 9, 1)),
    )
    monkeypatch.setattr(conector, "_baixar", lambda _url: FIXTURE.read_text(encoding="iso-8859-1"))
    return conector


def test_aponta_para_o_dataset_vivo_e_nao_para_o_descontinuado():
    """A CCEE descontinuou `lista_perfil` em favor de `lista_perfil_v1` (CO 562/25).

    Apontar para o antigo traria cadastro congelado em dezembro de 2025, e o
    erro não apareceria como falha — apareceria como dado velho.
    """
    assert DATASET == "lista_perfil_v1"


def test_le_o_cadastro_inteiro(conector):
    registros = list(conector.extrair(Janela.de_texto("2026-09-14", "2026-09-14")))

    assert len(registros) == 5


def test_a_janela_nao_recorta_cadastro(conector):
    """Cadastro é retrato completo; janela estreita não pode devolver menos (ADR 013)."""
    um_dia = list(conector.extrair(Janela.de_texto("2026-09-14", "2026-09-14")))
    um_mes = list(conector.extrair(Janela.de_texto("2026-08-15", "2026-09-14")))

    assert len(um_dia) == len(um_mes) == 5


def test_data_referencia_vem_do_ckan_e_nao_da_janela(conector):
    """O retrato é datado pela origem, não por quando resolvemos baixá-lo."""
    bruto = next(iter(conector.extrair(Janela.de_texto("2026-09-14", "2026-09-14"))))
    registro = PerfilAgente.model_validate(conector.transformar(bruto))

    assert registro.data_referencia == date(2026, 9, 1)  # last_modified do recurso


# ------------------------------------------------------------ a dimensão comum


def test_preenche_agente_ccee(conector):
    registros = [PerfilAgente.model_validate(conector.transformar(b)) for b in conector.extrair(_janela())]

    assert {r.agente_ccee for r in registros} == {"AES TIETE", "ALUPAR", "COMERC", "SEM SUB", "NORDESTE SA"}


def test_perfil_e_distinto_do_agente(conector):
    """Um agente pode ter vários perfis; é o perfil que transaciona na CCEE."""
    registros = [PerfilAgente.model_validate(conector.transformar(b)) for b in conector.extrair(_janela())]
    comerc = next(r for r in registros if r.agente_ccee == "COMERC")

    assert comerc.codigo_agente == "11"
    assert comerc.codigo_perfil == "110"
    assert comerc.sigla_perfil == "COMERC VAREJO"


# ------------------------------------------------------------------- submercado


def test_submercado_vira_a_sigla_do_lake(conector):
    registros = [PerfilAgente.model_validate(conector.transformar(b)) for b in conector.extrair(_janela())]
    por_agente = {r.agente_ccee: r.submercado for r in registros}

    assert por_agente["ALUPAR"] == "SE"
    assert por_agente["COMERC"] == "S"
    assert por_agente["NORDESTE SA"] == "NE"


def test_espaco_nao_separavel_no_submercado_vira_nulo(conector):
    """O arquivo real traz \\xa0, não string vazia, para perfil sem submercado.

    Sem normalizar, o schema rejeitaria a linha e o cadastro perderia registros
    silenciosamente — contados como inválidos, sem ninguém entender por quê.
    """
    registros = [PerfilAgente.model_validate(conector.transformar(b)) for b in conector.extrair(_janela())]
    sem_sub = next(r for r in registros if r.agente_ccee == "SEM SUB")

    assert sem_sub.submercado is None


def test_submercado_desconhecido_e_rejeitado():
    with pytest.raises(ValueError, match="submercado desconhecido"):
        PerfilAgente.model_validate(_registro_minimo(submercado="CENTRO-OESTE"))


# ------------------------------------------------------------------- validação


def test_varejista_sim_nao_vira_booleano(conector):
    registros = [PerfilAgente.model_validate(conector.transformar(b)) for b in conector.extrair(_janela())]
    por_agente = {r.agente_ccee: r.varejista for r in registros}

    assert por_agente["COMERC"] is True
    assert por_agente["ALUPAR"] is False


def test_status_desconhecido_e_rejeitado():
    """ATIVO, ENCERRADO e PERFIL ESPECIFICO são os três que a CCEE publica."""
    with pytest.raises(ValueError, match="status de perfil desconhecido"):
        PerfilAgente.model_validate(_registro_minimo(status_perfil="SUSPENSO"))


def test_os_tres_status_conhecidos_passam():
    for status in ("ATIVO", "ENCERRADO", "PERFIL ESPECIFICO"):
        assert PerfilAgente.model_validate(_registro_minimo(status_perfil=status)).status_perfil == status


def test_cnpj_fora_de_14_digitos_e_rejeitado():
    with pytest.raises(ValueError, match="CNPJ"):
        PerfilAgente.model_validate(_registro_minimo(cnpj="123"))


def test_cnpj_com_mascara_e_normalizado():
    """A CCEE publica sem máscara, mas normalizar torna a chave estável se mudar."""
    registro = PerfilAgente.model_validate(_registro_minimo(cnpj="08.364.948/0001-38"))

    assert registro.cnpj == "08364948000138"


# -------------------------------------------------------------------- ingestão


def test_ingerir_carrega_o_cadastro(conector):
    execucao = conector.ingerir(_janela())

    assert execucao.status == "SUCESSO"
    assert execucao.linhas_extraidas == 5
    assert execucao.linhas_invalidas == 0


# ------------------------------------------------------------------- auxiliares


def _janela() -> Janela:
    return Janela.de_texto("2026-09-14", "2026-09-14")


def _registro_minimo(**troca):
    base = {
        "data_referencia": "2026-09-01",
        "codigo_agente": "10",
        "agente_ccee": "ALUPAR",
        "nome_empresarial": "ALUPAR INVESTIMENTO S.A.",
        "cnpj": "08364948000138",
        "codigo_perfil": "10",
        "sigla_perfil": "ALUPAR",
        "classe_perfil": "Transmissor",
        "status_perfil": "ATIVO",
        "categoria_agente": "Transmissão",
        "submercado": "SE",
        "varejista": False,
        "tipo_energia": "Convencional Não Especial N/A",
    }
    return base | troca
