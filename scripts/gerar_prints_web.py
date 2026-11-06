"""Gera os prints da versão web para o README (docs/img/07 a 09), a partir do site REAL servido localmente.

  07-web-celular.png    três telas de celular lado a lado: a pergunta respondida, a ficha da escola e a prancha
                        do mapa (EMEF Durval Máximo, Muniz Freire/ES, a escola usada na validação)
  08-web-retrato.png    o retrato do Brasil por UF, no computador, com Mato Grosso escolhido
  09-web-impressao.png  as 2 páginas A4 da ficha impressa, lado a lado

Ferramenta de desenvolvedor (precisa do Playwright, do Pillow e do pdftoppm, do poppler-utils). Rode com o site
servido localmente:
    cd site && python3 -m http.server 8765 --bind 127.0.0.1
    ~/.venv/bin/python scripts/gerar_prints_web.py [--url http://127.0.0.1:8765/]
"""

from __future__ import annotations

import argparse
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import quote

from PIL import Image
from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
SAIDA = RAIZ / "docs" / "img"
ESCOLA = 32049501
PERGUNTA = "a prefeitura pode fechar a escola sem consultar a gente?"
PAPEL = (248, 249, 244)
FIO = (197, 205, 195)


def abrir(pg, url: str) -> None:
    pg.goto(url)
    pg.wait_for_load_state("networkidle")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(400)


def lado_a_lado(imagens: list[Image.Image], largura_final: int, vao: int = 48) -> Image.Image:
    h = max(i.height for i in imagens)
    tela = Image.new("RGB", (sum(i.width for i in imagens) + vao * (len(imagens) + 1), h + 2 * vao), PAPEL)
    x = vao
    for i in imagens:
        tela.paste(Image.new("RGB", (i.width + 4, i.height + 4), FIO), (x - 2, vao - 2))
        tela.paste(i, (x, vao))
        x += i.width + vao
    return tela.resize((largura_final, round(tela.height * largura_final / tela.width)), Image.LANCZOS)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://127.0.0.1:8765/")
    a = p.parse_args()
    SAIDA.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as pw, tempfile.TemporaryDirectory() as tmp:
        nav = pw.chromium.launch()
        cel = nav.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, service_workers="block", reduced_motion="reduce",
                              color_scheme="light")
        pg = cel.new_page()
        telas = []
        abrir(pg, a.url + "#/pergunta/" + quote(PERGUNTA))
        telas.append(Path(tmp) / "a.png")
        pg.screenshot(path=telas[-1])
        abrir(pg, a.url + f"#/escola/{ESCOLA}")
        telas.append(Path(tmp) / "b.png")
        pg.screenshot(path=telas[-1])
        pg.evaluate("document.querySelector('figure.prancha').scrollIntoView({block: 'start'})")
        pg.wait_for_timeout(300)
        telas.append(Path(tmp) / "c.png")
        pg.screenshot(path=telas[-1])
        lado_a_lado([Image.open(t).convert("RGB") for t in telas], 1800).save(SAIDA / "07-web-celular.png", optimize=True)

        pc = nav.new_context(viewport={"width": 1280, "height": 1900}, device_scale_factor=1.5, service_workers="block", reduced_motion="reduce",
                             color_scheme="light")
        pg = pc.new_page()
        abrir(pg, a.url + "#/retrato")
        pg.click('path[data-uf="MT"]')  # mostra o painel da UF escolhida
        pg.wait_for_timeout(300)
        pg.screenshot(path=SAIDA / "08-web-retrato.png")
        img = Image.open(SAIDA / "08-web-retrato.png").convert("RGB")
        img.resize((1600, round(img.height * 1600 / img.width)), Image.LANCZOS).save(SAIDA / "08-web-retrato.png", optimize=True)

        abrir(pg, a.url + f"#/escola/{ESCOLA}")
        pdf = Path(tmp) / "ficha.pdf"
        pg.pdf(path=str(pdf), format="A4", print_background=True)
        subprocess.run(["pdftoppm", "-png", "-r", "80", str(pdf), str(Path(tmp) / "pag")], check=True)
        paginas = sorted(Path(tmp).glob("pag*.png"))
        lado_a_lado([Image.open(x).convert("RGB") for x in paginas], 1400).save(SAIDA / "09-web-impressao.png", optimize=True)
        nav.close()
    for nome in ("07-web-celular.png", "08-web-retrato.png", "09-web-impressao.png"):
        print(nome, f"{(SAIDA / nome).stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
