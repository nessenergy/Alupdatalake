"""Renderiza um documento Markdown com a identidade ness., em HTML e/ou PDF.

O Markdown é sempre a fonte única; este script só apresenta. Usado pelos
documentos que saem para a contratante: o Questionário de Gaps e os relatórios
de situação, que por convenção existem em `.md` e `.html`
(ver `docs/relatorios/README.md`).

O HTML é autocontido — abre direto no navegador, sem servidor e sem dependência
externa além das fontes da identidade: Montserrat nos títulos e na marca, Inter
no corpo e JetBrains Mono no dado técnico. Sem elas o documento continua legível
nos fallbacks declarados. O PDF sai do Chrome/Edge headless, a mesma
engine em que o documento é revisado, o que evita divergência entre o que se vê
em tela e o que o cliente recebe.

    uv run --with markdown python scripts/gerar_documento.py FONTE.md --html --pdf
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

NAVEGADORES = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
)

ESTILO = """
@page { size: A4; margin: 16mm 14mm 16mm 14mm; }

/* O documento existe para virar A4. Declarar o esquema claro impede o
   navegador de escurecer por conta própria e descolar tela de papel. */
:root { color-scheme: light; }

/* Só a versão de tela: no PDF a margem é da @page. Em tela o documento se
   apresenta como folha sobre fundo, que é como ele será lido e impresso. */
@media screen {
  html { background: var(--zebra); }
  body {
    max-width: 940px;
    margin: 0 auto;
    padding: 56px 56px 72px;
    font-size: 15px;
    background: #fff;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04),
                0 10px 15px -3px rgba(15, 23, 42, 0.06);
  }
  table { font-size: 14px; }
}

:root {
  --tinta: #0f172a;
  --suave: #475569;
  --tenue: #94a3b8;
  --linha: #e2e8f0;
  --linha-fina: #eef2f6;
  --zebra: #f8fafc;
  --ness: #00ade8;
  --alerta: #b3261e;
  --fundo-alerta: #fdf3f2;
  /* Corpo em Inter, títulos e marca em Montserrat, dado técnico em mono. */
  --texto: Inter, "Segoe UI", system-ui, sans-serif;
  --titulo: Montserrat, "Segoe UI", system-ui, sans-serif;
  --mono: "JetBrains Mono", "Cascadia Mono", Consolas, monospace;
}

* { box-sizing: border-box; }

body {
  font-family: var(--texto);
  font-size: 9.4pt;
  line-height: 1.55;
  color: var(--tinta);
  margin: 0;
  -webkit-font-smoothing: antialiased;
}

/* ---------------------------------------------------------------- cabeçalho */

.marca {
  font-family: var(--titulo);
  font-weight: 500;
  font-size: 15pt;
  letter-spacing: -0.01em;
  margin: 0 0 2mm;
}
/* O ponto da marca é sempre BlueDot, em qualquer fundo. */
.marca span { color: var(--ness); }

h1 {
  font-family: var(--titulo);
  font-size: 17pt;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.25;
  margin: 0 0 1mm;
  padding-bottom: 3mm;
  border-bottom: 2px solid var(--ness);
}

/* A primeira linha depois do h1 é a tarja de identificação do documento —
   emissão, contrato, marco. Ela se lê como etiqueta, não como parágrafo. */
h1 + p {
  font-size: 8.4pt;
  color: var(--suave);
  margin-bottom: 5mm;
}

h2 {
  font-family: var(--titulo);
  font-size: 11.5pt;
  font-weight: 500;
  letter-spacing: -0.01em;
  margin: 8mm 0 2.5mm;
  padding-top: 3mm;
  border-top: 1px solid var(--linha);
  /* Um bloco não deve abrir no rodapé e continuar na página seguinte. */
  break-after: avoid;
}

/* Marcador BlueDot antes do título de seção: assinatura discreta, custo zero
   de espaço, e dá ao olho um ponto de entrada por seção. */
h2::before {
  content: "";
  display: inline-block;
  width: 1.4mm;
  height: 1.4mm;
  border-radius: 50%;
  background: var(--ness);
  margin-right: 1.8mm;
  vertical-align: 0.4mm;
}

h3 {
  font-family: var(--titulo);
  font-size: 10pt;
  font-weight: 500;
  margin: 5mm 0 2mm;
  break-after: avoid;
}

p { margin: 0 0 2.5mm; }
strong { font-weight: 600; }
code {
  font-family: var(--mono);
  font-size: 8.3pt;
  background: var(--zebra);
  border: 0.2mm solid var(--linha-fina);
  padding: 0.3mm 1mm;
  border-radius: 2px;
}

/* -------------------------------------------------------------------- tabela */

table {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 4mm;
  font-size: 8.8pt;
  /* Número em coluna alinha por dígito, não por forma da letra. */
  font-variant-numeric: tabular-nums;
}
th {
  text-align: left;
  font-family: var(--titulo);
  font-weight: 600;
  font-size: 7.6pt;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--suave);
  border-bottom: 1.5px solid var(--tinta);
  padding: 1.6mm 2mm;
}
td {
  border-bottom: 1px solid var(--linha-fina);
  padding: 2.4mm 2mm;
  vertical-align: top;
}
/* Faixa alternada: em tabela densa, o olho perde a linha sem ela. Tom baixo
   o bastante para não competir com o texto nem pesar na impressão. */
tbody tr:nth-child(even) td { background: var(--zebra); }
/* A primeira coluna costuma ser a chave da linha — onda, item, código. */
tbody td:first-child { font-weight: 500; }
/* Uma pergunta não se parte entre páginas. */
tr { break-inside: avoid; }
thead { display: table-header-group; }

/* Larguras de coluna do formulário: código estreito, "Resposta" com espaço de
   escrita. Valem só no questionário — num relatório espremeriam a 1ª coluna e
   pintariam a última sem motivo. */
.questionario td:first-child { width: 7%; font-weight: 600; font-variant-numeric: tabular-nums; }
.questionario th:last-child, .questionario td:last-child { width: 30%; background: #fafbfc; }
.questionario td:nth-child(3) { width: 15%; color: var(--suave); font-size: 8.2pt; }

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


def montar_html(texto_md: str, *, classe: str = "relatorio") -> str:
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
        "<link rel='preconnect' href='https://fonts.gstatic.com' crossorigin>"
        "<link href='https://fonts.googleapis.com/css2?"
        "family=Montserrat:wght@500;600&"
        "family=Inter:wght@400;500;600&"
        "family=JetBrains+Mono:wght@400;500&display=swap' "
        "rel='stylesheet'>"
        f"<style>{ESTILO}</style></head>"
        f"<body class='{classe}'>{marca}{corpo}{rodape}</body></html>"
    )


def gerar_html(fonte: Path, saida: Path, classe: str) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(montar_html(fonte.read_text(encoding="utf-8"), classe=classe), encoding="utf-8")
    return saida


def gerar_pdf(fonte: Path, saida: Path, classe: str) -> Path:
    saida.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        origem = Path(tmp) / "documento.html"
        origem.write_text(montar_html(fonte.read_text(encoding="utf-8"), classe=classe), encoding="utf-8")
        # Escreve num temporário e só então substitui. Imprimir direto sobre o
        # destino falha em silêncio quando ele está aberto num visualizador: o
        # navegador não grava, o arquivo antigo continua lá, e um documento
        # desatualizado seguiria para a contratante.
        provisorio = Path(tmp) / "documento.pdf"
        subprocess.run(  # noqa: S603 — argumentos fixos, sem entrada do usuário
            [
                str(encontrar_navegador()),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--virtual-time-budget=10000",  # espera a fonte remota carregar
                f"--print-to-pdf={provisorio}",
                origem.as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=180,
        )
        if not provisorio.exists():
            raise SystemExit("o navegador terminou sem escrever o PDF")
        try:
            shutil.move(str(provisorio), str(saida))
        except OSError as exc:
            raise SystemExit(
                f"não foi possível escrever em {saida}: {exc}.\n"
                "O arquivo provavelmente está aberto num visualizador de PDF — feche-o e repita."
            ) from exc
    return saida


def main() -> int:
    parser = argparse.ArgumentParser(description="Renderiza Markdown com a identidade ness.")
    parser.add_argument("fonte", type=Path, help="arquivo .md a renderizar")
    parser.add_argument("--html", action="store_true", help="gera .html ao lado da fonte")
    parser.add_argument("--pdf", action="store_true", help="gera .pdf")
    parser.add_argument("--saida-pdf", type=Path, help="caminho do PDF (padrão: ao lado da fonte)")
    parser.add_argument(
        "--classe",
        default="relatorio",
        choices=("relatorio", "questionario"),
        help="questionario aplica as larguras de coluna do formulário",
    )
    args = parser.parse_args()

    if not args.fonte.exists():
        raise SystemExit(f"fonte não encontrada: {args.fonte}")
    if not (args.html or args.pdf):
        raise SystemExit("escolha ao menos um formato: --html, --pdf")

    if args.html:
        caminho = gerar_html(args.fonte, args.fonte.with_suffix(".html"), args.classe)
        print(f"{caminho} ({caminho.stat().st_size / 1024:.0f} KB)")
    if args.pdf:
        destino = args.saida_pdf or args.fonte.with_suffix(".pdf")
        caminho = gerar_pdf(args.fonte, destino, args.classe)
        print(f"{caminho} ({caminho.stat().st_size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
