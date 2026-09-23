"""O que o Dockerfile copia precisa estar no contexto de build.

O build só roda no CI (Docker Desktop não sobe nesta estação), então o erro
aparecia tarde: em 23/09 o primeiro deploy parou porque `.dockerignore`
excluía `*.md` e o Dockerfile copia `README.md`, exigido pelo
`readme = "README.md"` do `pyproject.toml` na hora de instalar o projeto.
"""

from fnmatch import fnmatch
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def fontes_copiadas() -> list[str]:
    """Caminhos que o Dockerfile copia do contexto, sem os `COPY --from=`."""
    saida = []
    for linha in (RAIZ / "Dockerfile").read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha.startswith("COPY ") or "--from=" in linha:
            continue
        # O último argumento é o destino na imagem.
        saida.extend(linha.split()[1:-1])
    return saida


def ignorado(caminho: str) -> bool:
    """Aplica as regras do `.dockerignore` na ordem: a última que casa vence."""
    veredito = False
    for regra in (RAIZ / ".dockerignore").read_text(encoding="utf-8").splitlines():
        regra = regra.strip()
        if not regra or regra.startswith("#"):
            continue
        negada = regra.startswith("!")
        padrao = regra.removeprefix("!")
        if fnmatch(caminho, padrao) or caminho.startswith(padrao.rstrip("/") + "/"):
            veredito = not negada
    return veredito


def test_tudo_que_o_dockerfile_copia_chega_ao_contexto():
    fontes = fontes_copiadas()
    assert fontes, "nenhum COPY encontrado no Dockerfile"
    for fonte in fontes:
        assert (RAIZ / fonte.rstrip("/")).exists(), f"{fonte} não existe no repositório"
        assert not ignorado(fonte), f"{fonte} é excluído pelo .dockerignore"


def test_o_readme_continua_escapando_da_regra_de_markdown():
    assert ignorado("CLAUDE.md"), "a regra *.md deixou de valer"
    assert not ignorado("README.md"), "sem README.md o uv sync não instala o projeto"
