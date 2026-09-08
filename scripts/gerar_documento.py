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

/* Imprimir do navegador (Ctrl+P → Salvar como PDF) vem com "gráficos de plano
   de fundo" DESLIGADO por padrão. Sem isto, a faixa alternada das tabelas, o
   fundo do `code` e o bloco de alerta somem no papel — e a etiqueta vermelha
   do questionário vira texto branco sobre branco, isto é, invisível.
   Forçar aqui garante que tela, --print-to-pdf e impressão manual coincidam. */
html {
  -webkit-print-color-adjust: exact;
  print-color-adjust: exact;
}

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

/* ------------------------------------------------- identificação do documento */

/* Ficha do documento: quem emite, para quem, sob qual contrato, em que data.
   Fica logo abaixo do título e não se parte entre páginas — um documento
   contratual precisa ser identificável pela primeira folha, isolada. */
.identificacao {
  display: grid;
  /* Largura suficiente para "RESPONSÁVEL TÉCNICO" caber em uma linha. */
  grid-template-columns: 37mm 1fr;
  gap: 1.2mm 4mm;
  margin: 4mm 0 6mm;
  padding: 3.5mm 4mm;
  background: var(--zebra);
  border-left: 2px solid var(--ness);
  font-size: 8.4pt;
  break-inside: avoid;
}
.id-rotulo {
  font-family: var(--titulo);
  font-size: 7.2pt;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--suave);
  padding-top: 0.4mm;
}
.id-valor { color: var(--tinta); }

/* ------------------------------------------------------------- fecho assinado */

.assinatura {
  margin-top: 12mm;
  break-inside: avoid;
}
.assinatura .local-data {
  font-size: 8.6pt;
  color: var(--suave);
  margin-bottom: 12mm;
}
.linha-assinatura {
  width: 68mm;
  border-top: 1px solid var(--tinta);
  margin-bottom: 1.6mm;
}
.assina-nome {
  font-family: var(--titulo);
  font-weight: 500;
  font-size: 9.4pt;
  margin: 0;
}
.assina-org {
  font-size: 8pt;
  color: var(--suave);
  margin: 0.4mm 0 0;
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

/* ---------------------------------------------------------------- impressão */

/* Token longo — URL, nome de secret, identificador — não pode estourar a
   largura da A4 e sumir na borda do papel. */
code, td, th { overflow-wrap: anywhere; }

@media print {
  /* Uma linha solta no pé ou no topo da página é o defeito mais visível de um
     documento impresso. Três linhas é o mínimo que se lê como parágrafo. */
  p, li { orphans: 3; widows: 3; }
  h1, h2, h3 { break-after: avoid; break-inside: avoid; }
  /* Título de seção seguido de tabela: os dois andam juntos ou nenhum anda. */
  h2 + table, h3 + table, h2 + p, h3 + p { break-before: avoid; }
  table, blockquote { break-inside: auto; }
  /* Link impresso vira texto: sublinhado só polui o papel. */
  a { text-decoration: none; color: var(--tinta); }
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


# Ordem em que os campos de identificação aparecem no documento. Chave do
# front-matter à esquerda, rótulo impresso à direita. Campo ausente na fonte
# simplesmente não é impresso — nenhum documento é obrigado a ter todos.
CAMPOS_IDENTIFICACAO = (
    ("documento", "Documento"),
    ("referencia", "Referência"),
    ("emitido_em", "Data de emissão"),
    ("emitente", "Emitente"),
    ("destinatario", "Destinatário"),
    ("contrato", "Contrato"),
    ("marco", "Marco em jogo"),
    ("responsavel", "Responsável técnico"),
    ("classificacao", "Classificação"),
)


def separar_frontmatter(texto: str) -> tuple[dict[str, str], str]:
    """Extrai o bloco `---` de metadados do topo, se houver.

    Sem front-matter o documento segue como antes: nada de identificação é
    inventado a partir do corpo, porque metadado adivinhado num documento
    contratual é pior que metadado ausente.
    """
    if not texto.startswith("---\n"):
        return {}, texto
    fim = texto.find("\n---\n", 4)
    if fim == -1:
        return {}, texto
    meta = {}
    for linha in texto[4:fim].splitlines():
        if ":" in linha:
            chave, _, valor = linha.partition(":")
            meta[chave.strip()] = valor.strip()
    return meta, texto[fim + 5 :].lstrip("\n")


def titulo_do_corpo(texto_md: str) -> str:
    """Título da aba e do PDF quando o front-matter não declara um.

    Vem do próprio `# ` do documento — antes esta função não existia e todo
    arquivo gerado saía com o título do questionário na aba do navegador e nos
    metadados do PDF, inclusive os relatórios.
    """
    for linha in texto_md.splitlines():
        if linha.startswith("# "):
            titulo = linha[2:].strip()
            # Título que já se nomeia não recebe o sufixo de novo.
            return titulo if "AlupData" in titulo else f"{titulo} — AlupData"
    return "Documento — AlupData"


def bloco_identificacao(meta: dict[str, str]) -> str:
    """Tabela de identificação do documento, logo abaixo do título."""
    linhas = [
        f"<div class='id-rotulo'>{rotulo}</div><div class='id-valor'>{meta[chave]}</div>"
        for chave, rotulo in CAMPOS_IDENTIFICACAO
        if meta.get(chave)
    ]
    return f"<section class='identificacao'>{''.join(linhas)}</section>" if linhas else ""


def bloco_assinatura(meta: dict[str, str]) -> str:
    """Fecho com responsável e local/data — um relatório emitido tem emissor."""
    if not meta.get("responsavel"):
        return ""
    local_data = meta.get("local_data", "")
    return (
        "<section class='assinatura'>"
        f"{f'<p class=local-data>{local_data}</p>' if local_data else ''}"
        "<div class='linha-assinatura'></div>"
        f"<p class='assina-nome'>{meta['responsavel']}</p>"
        f"<p class='assina-org'>{meta.get('emitente', '')}</p>"
        "</section>"
    )


def montar_html(texto_md: str, *, classe: str = "relatorio") -> str:
    meta, texto_md = separar_frontmatter(texto_md)
    corpo = markdown.markdown(texto_md, extensions=["tables", "attr_list"])
    # O marcador textual vira etiqueta visual — quem lê precisa achar as
    # perguntas que travam trabalho sem ler as 47.
    corpo = corpo.replace("[BLOQUEIA]", '<span class="bloqueia">BLOQUEIA</span>')
    # A identificação entra depois do <h1>, não antes: o leitor vê primeiro do
    # que se trata, depois a ficha do documento.
    identificacao = bloco_identificacao(meta)
    if identificacao and "</h1>" in corpo:
        corpo = corpo.replace("</h1>", "</h1>" + identificacao, 1)
    else:
        corpo = identificacao + corpo
    corpo += bloco_assinatura(meta)
    marca = '<p class="marca">ness<span>.</span></p>'
    titulo = meta.get("titulo") or meta.get("documento") or titulo_do_corpo(texto_md)
    rodape = (
        '<p class="rodape">ness. Processos e Tecnologia Ltda. · CNPJ 72.027.097/0001-37 · '
        "Contrato CPS-01025/2026 — AlupData Fase 1: DataLake</p>"
    )
    return (
        "<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'>"
        f"<title>{titulo}</title>"
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
