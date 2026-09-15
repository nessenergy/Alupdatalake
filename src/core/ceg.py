"""Forma canônica do CEG, a chave da dimensão comum `codigo_usina`.

O CEG é o código da ANEEL para um empreendimento de geração, com cinco
segmentos: tipo, fonte, UF, número de registro e ordem — `UHE.PH.RS.000012-4.1`.
O último segmento é o problema: a **ANEEL publica um dígito** e o **ONS publica
dois**, com zero à esquerda. Como texto, `...-4.1` e `...-4.01` são chaves
diferentes, e qualquer JOIN entre as duas origens devolve zero linha.

Medido em 15/09/2026 contra as origens reais: das 2.047 usinas com CEG no
cadastro de capacidade do ONS, nenhuma casava com o CodCEG da ANEEL; com o
sufixo igualado, 1.946 (95,1%) passam a casar, e os nomes confirmam o par. As
101 restantes são usinas que o ONS opera e o cadastro da ANEEL não traz sob
esse código — diferença de conteúdo, não de formato.

A forma canônica é a do ONS, com dois dígitos: ela é a que preserva o sufixo
`00` (9 usinas), que na forma de um dígito colidiria com nada e só perderia
informação. Normalizar aqui, e não em cada JOIN, é o que faz `codigo_usina`
ser de fato uma dimensão comum.
"""

from __future__ import annotations

SEGMENTOS = 5
_NULOS = {"", "-"}


def ceg_canonico(valor: str | None) -> str | None:
    """Devolve o CEG na forma canônica, ou None se não houver código.

    Formato inesperado volta inteiro, só aparado e em caixa alta: não é papel
    desta função decidir que um código que ela não reconhece é lixo.
    """
    if valor is None:
        return None
    texto = valor.strip().upper()
    if texto in _NULOS:
        return None
    partes = texto.split(".")
    if len(partes) == SEGMENTOS and partes[-1].isdigit():
        partes[-1] = partes[-1].zfill(2)
    return ".".join(partes)
