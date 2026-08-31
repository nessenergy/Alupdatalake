"""Gera o PDF de envio do Questionário de Gaps a partir do Markdown.

O Markdown em `docs/questionario-gaps.md` é a fonte única: este script só
apresenta. Reemitir depois de qualquer alteração é `make questionario-pdf`.

Renderiza via Chrome/Edge headless — a mesma engine do navegador, o que evita
divergência entre o que se revisa em tela e o que o cliente recebe.

    uv run python scripts/gerar_pdf_questionario.py [--saida caminho.pdf]
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

RAIZ = Path(__file__).resolve().parent.parent
FONTE = RAIZ / "docs" / "questionario-gaps.md"
SAIDA_PADRAO = RAIZ / "docs" / "envio" / "Questionario-de-Gaps-AlupData.pdf"

NAVEGADORES = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
)

ESTILO = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }

:root {
  --tinta: #12161a;
  --suave: #5c6772;
  --linha: #dfe4e9;
  --ness: #00ade8;
  --alerta: #b3261e;
  --fundo-alerta: #fdf3f2;
}

* { box-sizing: border-box; }

body {
  font-family: Montserrat, "Segoe UI", system-ui, sans-serif;
  font-size: 9.4pt;
  line-height: 1.5;
  color: var(--tinta);
  margin: 0;
}

/* ---------------------------------------------------------------- cabeçalho */

.marca {
  font-weight: 600;
  font-size: 15pt;
  letter-spacing: -0.02em;
  margin: 0 0 2mm;
}
.marca span { color: var(--ness); }

h1 {
  font-size: 17pt;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 0 0 1mm;
  padding-bottom: 3mm;
  border-bottom: 2px solid var(--ness);
}

h2 {
  font-size: 11.5pt;
  font-weight: 600;
  margin: 8mm 0 2.5mm;
  padding-top: 3mm;
  border-top: 1px solid var(--linha);
  /* Um bloco não deve abrir no rodapé e continuar na página seguinte. */
  break-after: avoid;
}

h3 { font-size: 10pt; font-weight: 600; margin: 5mm 0 2mm; break-after: avoid; }

p { margin: 0 0 2.5mm; }
strong { font-weight: 600; }
code {
  font-family: "Cascadia Mono", Consolas, monospace;
  font-size: 8.6pt;
  background: #f2f4f6;
  padding: 0.3mm 1mm;
  border-radius: 2px;
}

/* -------------------------------------------------------------------- tabela */

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 4mm;
  font-size: 8.8pt;
}
th {
  text-align: left;
  font-weight: 600;
  font-size: 7.8pt;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--suave);
  border-bottom: 1.5px solid var(--tinta);
  padding: 1.6mm 2mm;
}
td {
  border-bottom: 1px solid var(--linha);
  padding: 2.4mm 2mm;
  vertical-align: top;
}
/* Uma pergunta não se parte entre páginas. */
tr { break-inside: avoid; }
thead { display: table-header-group; }

/* Coluna 1 (código) estreita; a última (Resposta) recebe o espaço de escrita. */
table td:first-child { width: 7%; font-weight: 600; font-variant-numeric: tabular-nums; }
table th:last-child, table td:last-child { width: 30%; background: #fafbfc; }
.bloco table td:nth-child(3) { width: 15%; color: var(--suave); font-size: 8.2pt; }

/* --------------------------------------------------------------- destaques */

.bloqueia {
  display: inline-block;
  background: var(--alerta);
  color: #fff;
  font-size: 6.8pt;
  font-weight: 600;
  letter-spacing: 0.06em;
  padding: 0.4mm 1.4mm;
  border-radius: 2px;
  margin-right: 1.2mm;
  vertical-align: 1px;
}

blockquote {
  margin: 0 0 3mm;
  padding: 2.5mm 3mm;
  background: var(--fundo-alerta);
  border-left: 3px solid var(--alerta);
}
blockquote p:last-child { margin-bottom: 0; }

/* O `---` do Markdown separa as seções na fonte, mas no PDF a borda de `h2` já
   faz esse trabalho: manter os dois empilha traços. */
hr { display: none; }
hr + h2 { margin-top: 7mm; }

ul { margin: 0 0 3mm; padding-left: 5mm; }
li { margin-bottom: 1.2mm; }

.rodape {
  margin-top: 8mm;
  padding-top: 3mm;
  border-top: 1px solid var(--linha);
  font-size: 7.6pt;
  color: var(--suave);
}
"""


def encontrar_navegador() -> Path:
    for caminho in NAVEGADORES:
        if caminho.exists():
            return caminho
    achado = shutil.which("chrome") or shutil.which("msedge") or shutil.which("chromium")
    if achado:
        return Path(achado)
    raise SystemExit("Chrome ou Edge não encontrado; nenhum deles está instalado num caminho conhecido.")


def montar_html(texto_md: str) -> str:
    corpo = markdown.markdown(texto_md, extensions=["tables", "attr_list"])
    # O marcador textual vira etiqueta visual — quem lê precisa achar as
    # perguntas que travam trabalho sem ler as 47.
    corpo = corpo.replace("[BLOQUEIA]", '<span class="bloqueia">BLOQUEIA</span>')
    marca = '<p class="marca">ness<span>.</span></p>'
    rodape = (
        '<p class="rodape">ness. Processos e Tecnologia Ltda. · CNPJ 72.027.097/0001-37 · '
        "Contrato CPS-01025/2026 — AlupData Fase 1: DataLake</p>"
    )
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        "<title>Questionário de Gaps — AlupData</title>"
        "<link rel='preconnect' href='https://fonts.googleapis.com'>"
        "<link href='https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap' "
        "rel='stylesheet'>"
        f"<style>{ESTILO}</style></head>"
        f"<body class='bloco'>{marca}{corpo}{rodape}</body></html>"
    )


def gerar(saida: Path) -> Path:
    if not FONTE.exists():
        raise SystemExit(f"fonte não encontrada: {FONTE}")
    html = montar_html(FONTE.read_text(encoding="utf-8"))
    saida.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        origem = Path(tmp) / "questionario.html"
        origem.write_text(html, encoding="utf-8")
        subprocess.run(  # noqa: S603 — argumentos fixos, sem entrada do usuário
            [
                str(encontrar_navegador()),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--virtual-time-budget=10000",  # espera a fonte remota carregar
                f"--print-to-pdf={saida}",
                origem.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
    if not saida.exists():
        raise SystemExit("o navegador terminou sem escrever o PDF")
    return saida


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=SAIDA_PADRAO)
    args = parser.parse_args()
    caminho = gerar(args.saida)
    print(f"{caminho} ({caminho.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
