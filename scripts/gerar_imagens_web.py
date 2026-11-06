"""Gera as imagens fixas da versão web: web/public/previa.png (o cartão que aparece quando o link é colado no
WhatsApp, 1200x630) e os ícones icone-192.png e icone-512.png (instalação no celular).

O cartão usa as fontes e o mapa do próprio site (web/src/fontes, web/src/mapa/ufs.json) e o retrato nacional
(data/retrato_rotas.json): o Brasil por UF em degraus de "escolas a 50 km ou mais", como na prancha do início.
Ferramenta de desenvolvedor (precisa do Playwright, como scripts/gerar_prints.py).

Uso:  ~/.venv/bin/python scripts/gerar_imagens_web.py
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
WEB = RAIZ / "web"
SAIDA = WEB / "public"
CORES = ["#e6eed9", "#b9d09c", "#e2c477", "#c2853a", "#7f3f1d"]
LIMITES = [0.02, 0.05, 0.1, 0.2]


def mapa_svg() -> str:
    mapa = json.loads((WEB / "src" / "mapa" / "ufs.json").read_text(encoding="utf-8"))
    ret = json.loads((RAIZ / "data" / "retrato_rotas.json").read_text(encoding="utf-8"))
    partes = []
    for uf, g in mapa["ufs"].items():
        r = ret["uf"].get(uf)
        if r and r.get("aviso_fluvial"):
            cor = "url(#rio)"
        elif r and r["com_rota"]:
            fk = r["faixas_km"]
            v = (fk["50_a_100"]["escolas"] + fk["100_ou_mais"]["escolas"]) / r["com_rota"]
            cor = CORES[sum(v >= x for x in LIMITES)]
        else:
            cor = CORES[0]
        partes.append(f'<path d="{g["d"]}" fill="{cor}" stroke="#f8f9f4" stroke-width="2"/>')
    return (f'<svg viewBox="0 0 {mapa["largura"]} {mapa["altura"]}" xmlns="http://www.w3.org/2000/svg">'
            '<defs><pattern id="rio" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            '<rect width="10" height="10" fill="#d6e6f1"/><line x1="0" y1="0" x2="0" y2="10" stroke="#255f8a" '
            'stroke-width="2.5"/></pattern></defs>' + "".join(partes) + "</svg>")


def cartao() -> str:
    f = (WEB / "src" / "fontes").as_uri()
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: A; src: url({f}/alegreya.woff2); font-weight: 400 900; }}
@font-face {{ font-family: K; src: url({f}/atkinson-next.woff2); font-weight: 200 800; }}
body {{ margin: 0; width: 1200px; height: 630px; background: #f8f9f4; color: #1e2b2f; font-family: K; }}
.moldura {{ position: absolute; inset: 22px; border: 2px solid #1e2b2f; }}
.moldura::before {{ content: ""; position: absolute; inset: 6px; border: 1px solid #1e2b2f; }}
.texto {{ position: absolute; left: 76px; top: 82px; width: 560px; }}
.marca {{ font: 700 34px A; color: #2f5235; display: flex; align-items: center; gap: 14px; }}
h1 {{ font: 700 60px/1.08 A; margin: 46px 0 22px; letter-spacing: -0.5px; }}
p {{ font-size: 26px; line-height: 1.4; color: #4f5d62; margin: 0; }}
.mapa {{ position: absolute; right: 70px; top: 62px; width: 470px; }}
.pe {{ position: absolute; left: 76px; bottom: 60px; font: italic 22px A; color: #4f5d62; }}
</style></head><body><div class="moldura"></div>
<div class="texto"><div class="marca">{(SAIDA / "icone.svg").read_text().replace('viewBox="0 0 64 64"', 'viewBox="0 0 64 64" width="52" height="52"')}
Escola em Pauta</div>
<h1>Antes de uma escola do campo fechar, a lei manda medir o impacto.</h1>
<p>A ficha de cada uma das 53.759 escolas do campo, com dados públicos.</p></div>
<div class="mapa">{mapa_svg()}</div>
<div class="pe">Projeto acadêmico, não oficial. Dados do INEP, do Ipea e do OpenStreetMap.</div>
</body></html>"""


def main() -> None:
    icone = (SAIDA / "icone.svg").read_text()
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        # por arquivo, não por set_content: uma página em about:blank não pode carregar as fontes de file://
        with tempfile.TemporaryDirectory() as tmp:
            arq = Path(tmp) / "cartao.html"
            arq.write_text(cartao(), encoding="utf-8")
            pg.goto(arq.as_uri())
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(300)
            pg.screenshot(path=str(SAIDA / "previa.png"))
        for n in (192, 512):
            pg.set_viewport_size({"width": n, "height": n})
            pg.set_content(f'<body style="margin:0">{icone.replace("<svg ", f"<svg width={n} height={n} ", 1)}</body>')
            pg.screenshot(path=str(SAIDA / f"icone-{n}.png"), omit_background=True)
        b.close()
    for nome in ("previa.png", "icone-192.png", "icone-512.png"):
        print(nome, f"{(SAIDA / nome).stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
