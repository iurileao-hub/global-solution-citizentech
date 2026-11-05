"""Gera os prints do README a partir do assistente REAL (docs/img/*.png).

Cada print é uma sessão roteirizada: as respostas digitadas vêm de uma lista, e a função `input`
é trocada por uma que ECOA o que foi "digitado" (num pipe, o terminal não mostraria). A saída vira
uma janela de terminal em HTML, fotografada pelo Chromium do Playwright.

Ferramenta de desenvolvedor (precisa de Playwright); o assistente em si continua só stdlib.
Uso:  ~/.venv/bin/python scripts/gerar_prints.py [--escolas caminho/do/indice.json.gz]
"""

from __future__ import annotations

import argparse
import builtins
import contextlib
import html
import io
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
SAIDA = RAIZ / "docs" / "img"

# (arquivo, título da janela, argumentos, entradas digitadas, cortar_ate: só a parte que interessa)
SESSOES = [
    ("01-abertura", "Abertura e menu", [], ["0"], None),
    ("02-pergunta", "Pergunta em texto, com fonte e continuidade",
     [], ["2", "A prefeitura pode fechar a escola sem consultar a gente?", "", "0"], "Sua pergunta"),
    ("03-assunto", "Navegação por assunto (hierarquia tema > subtema > orientação)",
     [], ["1", "3", "", "0"], "Número do assunto"),
    ("04-escola", "Consulta de uma escola, com rotas como piso",
     [], ["3", "Durval Máximo", "", "0"], "Nome ou código"),
    ("05-ambigua", "Nome repetido: desempate por município e UF",
     [], ["3", "Escola Municipal São José", "Carlos Chagas", "MG", "", "0"], "Nome ou código"),
    ("06-limites", "Fora do tema, entrada vazia e opção inexistente",
     [], ["2", "Como tiro a segunda via do RG?", "", "2", "", "", "9", "0"], "Sua pergunta"),
]


def capturar(args: list[str], entradas: list[str]) -> str:
    import sistema  # noqa: PLC0415

    fila = list(entradas)
    buf = io.StringIO()

    def falso_input(rotulo: str = "") -> str:
        resp = fila.pop(0) if fila else "0"
        buf.write(f"{rotulo}\x00{resp}\x01\n")      # marca o texto digitado para destacar
        return resp

    original = builtins.input
    builtins.input = falso_input
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                sistema.main(args)
            except SystemExit:
                pass
    finally:
        builtins.input = original
    return buf.getvalue()


def para_html(titulo: str, texto: str) -> str:
    corpo = html.escape(texto).replace("\x00", '<b class="dig">').replace("\x01", "</b>")
    return f"""<!doctype html><meta charset="utf-8"><style>
body{{margin:0;background:#e8e6e1;font-family:system-ui,sans-serif}}
.jan{{margin:16px;border-radius:10px;overflow:hidden;box-shadow:0 6px 24px #0003;display:inline-block}}
.barra{{background:#2d2f33;color:#c9cdd3;font-size:13px;padding:8px 14px;display:flex;gap:8px;align-items:center}}
.p{{width:12px;height:12px;border-radius:50%;display:inline-block}}
pre{{margin:0;background:#16181c;color:#dfe3e8;font:14px/1.45 'DejaVu Sans Mono',monospace;padding:16px 20px;white-space:pre}}
.dig{{color:#7ee0a5;font-weight:600}}
</style><div class="jan"><div class="barra"><span class="p" style="background:#ff5f57"></span>
<span class="p" style="background:#febc2e"></span><span class="p" style="background:#28c840"></span>
<span style="margin-left:10px">python src/sistema.py · {html.escape(titulo)}</span></div><pre>{corpo}</pre></div>"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--escolas", help="índice alternativo (ex.: cópia já com rotas)")
    a = ap.parse_args()
    from playwright.sync_api import sync_playwright  # noqa: PLC0415

    SAIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        pag = nav.new_page(device_scale_factor=2)
        for nome, titulo, args, entradas, corte in SESSOES:
            extra = ["--escolas", a.escolas] if a.escolas else []
            texto = capturar(args + extra, entradas)
            if corte and corte in texto:            # começa no primeiro passo interessante
                texto = "Opção: " + texto[texto.index(corte):]
            fim = texto.rfind("\nO que você quer fazer?")
            if corte and fim > 0:                   # o menu final + "Até logo" se repetem em todo print
                texto = texto[:fim]
            texto = texto.rstrip() + "\n"
            pag.set_content(para_html(titulo, texto))
            pag.locator(".jan").screenshot(path=str(SAIDA / f"{nome}.png"))
            print("ok", nome)
        nav.close()


if __name__ == "__main__":
    main()
