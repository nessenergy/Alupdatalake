"""O CEG é a dimensão comum `codigo_usina`; só serve se as origens casarem.

Medido em 15/09/2026 contra as origens reais: das 2.047 usinas com CEG no
cadastro de capacidade do ONS, **nenhuma** casava com o CodCEG da ANEEL, e
1.946 (95,1%) passaram a casar depois de igualar o último segmento. A ANEEL
publica um dígito (`...-6.1`), o ONS publica dois (`...-6.01`).
"""

from src.core.ceg import ceg_canonico


def test_o_sufixo_de_um_digito_da_aneel_vira_dois():
    assert ceg_canonico("PCH.PH.MG.000008-6.1") == "PCH.PH.MG.000008-6.01"


def test_o_sufixo_de_dois_digitos_do_ons_fica_como_esta():
    assert ceg_canonico("EOL.CV.BA.030283-0.01") == "EOL.CV.BA.030283-0.01"


def test_as_duas_origens_convergem_para_a_mesma_chave():
    """É esta a propriedade que faz o de-para existir."""
    assert ceg_canonico("UHE.PH.PA.030354-2.1") == ceg_canonico("UHE.PH.PA.030354-2.01")


def test_o_zero_do_ons_nao_vira_um():
    """O ONS publica sufixo `00` em 9 usinas; não é o mesmo que `01`."""
    assert ceg_canonico("UFV.RS.CE.038364-3.00") == "UFV.RS.CE.038364-3.00"
    assert ceg_canonico("UFV.RS.CE.038364-3.00") != ceg_canonico("UFV.RS.CE.038364-3.1")


def test_sufixo_de_dois_digitos_maior_que_nove_e_preservado():
    assert ceg_canonico("UTE.PE.RN.028655-9.12") == "UTE.PE.RN.028655-9.12"


def test_espaco_em_volta_e_caixa_sao_normalizados():
    assert ceg_canonico("  uhe.ph.rs.000012-4.1  ") == "UHE.PH.RS.000012-4.01"


def test_vazio_e_marcador_viram_nulo():
    for valor in (None, "", "   ", "-"):
        assert ceg_canonico(valor) is None


def test_formato_inesperado_e_devolvido_inteiro_em_vez_de_descartado():
    """Não é papel desta função decidir que um código novo é lixo."""
    assert ceg_canonico("CODIGO.NOVO") == "CODIGO.NOVO"
    assert ceg_canonico("UHE.PH.RS.000012-4.AB") == "UHE.PH.RS.000012-4.AB"
