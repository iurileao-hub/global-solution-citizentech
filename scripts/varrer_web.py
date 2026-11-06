"""Varre a versão web em busca de defeitos de tela que os testes de texto não pegam.

Os testes do contrato conferem o TEXTO da resposta; a tela pode errar com o texto certo (uma coluna de tabela
espremida até uma letra por linha, um "null" no lugar do município, uma página que rola para o lado no celular).
Esta varredura abre cada tela em quatro larguras e procura, mecanicamente:

  - rolagem lateral da página inteira;
  - texto quebrado letra a letra (muitas linhas para poucos caracteres por linha);
  - conteúdo cortado em elemento que não rola;
  - "null", "undefined", "NaN", "[object" ou "0,0 km" no texto visível;
  - erro no console, exceção na página, pedido com resposta 4xx/5xx;
  - ficha impressa com mais de 2 páginas A4.

As telas: início, retrato, sobre, os 4 assuntos, as 27 orientações, perguntas de exemplo e uma amostra de
escolas escolhida para cobrir os casos difíceis (cada UF com e sem rota, indígena, quilombola, urbana-campo,
5ª receptora, receptora no mesmo lugar, escola sem município, nome mais longo).

Ferramenta de desenvolvedor (precisa do Playwright). Rode com o site servido localmente:
    cd site && python3 -m http.server 8765 --bind 127.0.0.1
    ~/.venv/bin/python scripts/varrer_web.py [--url http://127.0.0.1:8765/] [--larguras 320,390,768,1280]
Sai com código 1 se achar defeito.
"""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parents[1]
PERGUNTAS = [
    "a prefeitura pode fechar a escola sem consultar a gente?", "quem paga o ônibus escolar?",
    "quantas escolas fecharam no Piauí?", "quantas escolas fecharam em Minas Gerais?", "Escola Municipal São José",
    "o que é escola rural", "como tiro a segunda via do RG?", "meu filho tem deficiência e precisa de monitor no ônibus",
    "", "9",
]

# roda dentro da página: devolve a lista de defeitos achados na tela atual
VERIFICAR = r"""
() => {
  const achados = [];
  const de = document.documentElement;
  if (de.scrollWidth > window.innerWidth + 1) achados.push(`rolagem lateral: página com ${de.scrollWidth}px numa tela de ${window.innerWidth}px`);
  const nome = (el) => el.tagName.toLowerCase() + (el.id ? "#" + el.id : "") + (el.className && typeof el.className === "string" ? "." + el.className.trim().split(/\s+/).join(".") : "");
  const vistos = new Set();
  const caminhar = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = caminhar.nextNode(); n; n = caminhar.nextNode()) {
    const t = n.textContent.replace(/\s+/g, " ").trim();
    if (t.length < 6) continue;
    const el = n.parentElement;
    if (!el || vistos.has(el) || !el.getClientRects().length) continue;
    const st = getComputedStyle(el);
    if (st.visibility === "hidden" || st.display === "none") continue;
    const r = document.createRange(); r.selectNodeContents(n);
    const linhas = new Set([...r.getClientRects()].filter((x) => x.width > 0).map((x) => Math.round(x.top))).size;
    if (linhas >= 4 && t.length / linhas < 5) { vistos.add(el); achados.push(`texto quebrado letra a letra (${linhas} linhas para ${t.length} caracteres) em ${nome(el)}: "${t.slice(0, 40)}"`); }
  }
  for (const el of document.querySelectorAll("main *")) {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(el.tagName)) continue; // campo de digitação rola o próprio texto
    const st = getComputedStyle(el);
    if (!["hidden", "clip"].includes(st.overflowX)) continue;
    if (el.scrollWidth > el.clientWidth + 2 && el.clientWidth > 0) achados.push(`conteúdo cortado na horizontal em ${nome(el)} (${el.scrollWidth}px em ${el.clientWidth}px)`);
  }
  const texto = (document.querySelector("main") || document.body).innerText;
  for (const ruim of ["null", "undefined", "NaN", "[object", "Infinity"]) {
    const re = new RegExp("(^|[^A-Za-zÀ-ú])" + ruim.replace("[", "\\[") + "($|[^A-Za-zÀ-ú])");
    const m = texto.match(re);
    if (m) { const i = texto.indexOf(m[0]); achados.push(`texto "${ruim}" visível: "…${texto.slice(Math.max(0, i - 40), i + 40).replace(/\s+/g, " ")}…"`); }
  }
  if (/\b0,0 km\b/.test(texto)) achados.push('texto "0,0 km" visível');
  return achados;
}
"""


def amostra_escolas() -> dict[int, str]:
    doc = json.loads(gzip.decompress((RAIZ / "data" / "escolas_campo.json.gz").read_bytes()))
    es = sorted(doc["escolas"], key=lambda e: e["c"])
    escolha: dict[int, str] = {}

    def pega(motivo: str, filtro, n: int = 1) -> None:
        achadas = [e for e in es if filtro(e) and e["c"] not in escolha][:n]
        for e in achadas:
            escolha[e["c"]] = motivo

    def rs(e):
        return (e.get("rota") or {}).get("receptoras") or []

    for uf in sorted({e["uf"] for e in es if e["uf"]}):
        pega(f"{uf} com rota", lambda e, uf=uf: e["uf"] == uf and rs(e))
        pega(f"{uf} sem rota", lambda e, uf=uf: e["uf"] == uf and not rs(e))
    pega("Durval Máximo (demonstração)", lambda e: e["c"] == 32049501)
    pega("indígena", lambda e: e["d"] == "indígena" and rs(e), 3)
    pega("quilombola", lambda e: e["d"] == "quilombola" and rs(e), 3)
    pega("assentamento", lambda e: e["d"] == "assentamento" and rs(e), 2)
    pega("urbana-campo", lambda e: e["z"] == "urbana-campo" and rs(e), 3)
    pega("5ª receptora", lambda e: len(rs(e)) >= 5, 3)
    pega("receptora no mesmo lugar", lambda e: any(r["km"] < 1 for r in rs(e)), 3)
    pega("sem município", lambda e: not e["m"] or not e["uf"], 2)
    pega("sem coordenada", lambda e: not e["geo"], 2)
    pega("nome mais longo", lambda e: len(e["n"]) == max(len(x["n"]) for x in es))
    pega("matrícula zero", lambda e: not e["t"], 2)
    return escolha


def telas(base: dict) -> list[tuple[str, str]]:
    t = [("#/", "início"), ("#/retrato", "retrato"), ("#/sobre", "sobre")]
    t += [(f"#/assunto/{k}", f"assunto {k}") for k in base["temas"]]
    t += [(f"#/orientacao/{r['id']}", f"orientação {r['id']}") for r in base["registros"]]
    t += [(f"#/pergunta/{quote(q)}", f'pergunta "{q}"') for q in PERGUNTAS if q]
    t += [(f"#/escola/{c}", f"escola {c} ({m})") for c, m in amostra_escolas().items()]
    return t


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", default="http://127.0.0.1:8765/")
    p.add_argument("--larguras", default="320,390,768,1280")
    p.add_argument("--impressas", type=int, default=12, help="quantas fichas conferir na impressão")
    a = p.parse_args()
    base = json.loads((RAIZ / "data" / "base_orientacoes.json").read_text(encoding="utf-8"))
    lista = telas(base)
    defeitos: dict[str, list[str]] = defaultdict(list)
    with sync_playwright() as pw:
        nav = pw.chromium.launch()
        for w in (int(x) for x in a.larguras.split(",")):
            ctx = nav.new_context(viewport={"width": w, "height": 900}, service_workers="block")
            pg = ctx.new_page()
            atual = {"tela": ""}
            pg.on("console", lambda m: defeitos[atual["tela"]].append(f"{w}px console: {m.text}") if m.type == "error" else None)
            pg.on("pageerror", lambda e: defeitos[atual["tela"]].append(f"{w}px exceção: {e}"))
            pg.on("response", lambda r: defeitos[atual["tela"]].append(f"{w}px HTTP {r.status}: {r.url}")
                  if r.status >= 400 and "desligar-sw.txt" not in r.url else None)
            pg.goto(a.url)
            pg.wait_for_load_state("networkidle")
            for hash_, rotulo in lista:
                atual["tela"] = rotulo
                pg.evaluate("h => { location.hash = h; }", hash_)
                pg.wait_for_load_state("networkidle")
                pg.wait_for_timeout(250)
                for d in pg.evaluate(VERIFICAR):
                    defeitos[rotulo].append(f"{w}px {d}")
            ctx.close()
            print(f"{w}px: {len(lista)} telas", file=sys.stderr)
        # impressão: a ficha tem de caber em 2 páginas A4
        ctx = nav.new_context(service_workers="block")
        pg = ctx.new_page()
        for hash_, rotulo in [x for x in lista if x[0].startswith("#/escola/")][: a.impressas]:
            pg.goto(a.url + hash_)
            pg.wait_for_load_state("networkidle")
            pg.wait_for_timeout(300)
            paginas = len(re.findall(rb"/Type\s*/Page(?!s)", pg.pdf(format="A4")))
            if paginas > 2:
                defeitos[rotulo].append(f"impressão em {paginas} páginas (o limite é 2)")
        nav.close()
    total = sum(len(v) for v in defeitos.values())
    for rotulo, ds in sorted(defeitos.items()):
        if not ds:
            continue
        print(f"\n== {rotulo}")
        for d in dict.fromkeys(ds):
            print("  -", d)
    print(f"\n{len(lista)} telas x {len(a.larguras.split(','))} larguras: {total} defeito(s) em "
          f"{sum(1 for v in defeitos.values() if v)} tela(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
