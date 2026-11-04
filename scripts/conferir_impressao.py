"""Imprime cada ficha do site em PDF A4, como o navegador faria, e conta as páginas: o certo é 2 (frente e verso).

Rodar depois de mexer no template ou no CSS da ficha, antes de publicar:
    python scripts/conferir_impressao.py            # todas as fichas em site/escola/
    python scripts/conferir_impressao.py 35215934   # uma só

Requer playwright (com o Chromium instalado) e pypdf. Sai com código 1 se alguma ficha não tiver 2 páginas.
"""

import collections
import io
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

PASTA = Path(__file__).resolve().parent.parent / "site" / "escola"
arqs = [PASTA / f"{c}.html" for c in sys.argv[1:]] or sorted(PASTA.glob("*.html"))
contagem, erradas = collections.Counter(), []
with sync_playwright() as p:
    navegador = p.chromium.launch()
    pagina = navegador.new_page()
    for arq in arqs:
        pagina.goto(arq.as_uri())
        pdf = pagina.pdf(format="A4", print_background=True, prefer_css_page_size=True)
        n = len(PdfReader(io.BytesIO(pdf)).pages)
        contagem[n] += 1
        if n != 2:
            erradas.append((arq.stem, n))
    navegador.close()
print(f"{len(arqs)} fichas; páginas por ficha: {dict(sorted(contagem.items()))}")
for cod, n in erradas:
    print(f"  {cod}: {n} páginas")
sys.exit(1 if erradas else 0)
