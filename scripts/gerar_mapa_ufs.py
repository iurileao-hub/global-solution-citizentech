"""Gera web/src/mapa/ufs.json: o contorno de cada UF como caminho SVG, para o mapa do retrato na versão web.

Fonte: malha do IBGE na qualidade "mínima" (API de malhas v3), baixada em dados/brutos/ibge/ufs_minima.json:
  https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json&qualidade=minima&intrarregiao=UF

Projeção: equiretangular com o eixo x multiplicado pelo cosseno de 15° S (a latitude média do país). Para um mapa
por UF do tamanho de uma tela de celular, a distorção é pequena e a conta cabe em uma linha; um mapa de atlas
usaria uma cônica, que aqui não muda a leitura. Coordenadas inteiras numa largura de 1000 (1 unidade = ~4,4 km, abaixo do que a tela mostra).

Uso:  python scripts/gerar_mapa_ufs.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "dados" / "brutos" / "ibge" / "ufs_minima.json"
SAIDA = RAIZ / "web" / "src" / "mapa" / "ufs.json"
URL = ("https://servicodados.ibge.gov.br/api/v3/malhas/paises/BR?formato=application/vnd.geo+json"
       "&qualidade=minima&intrarregiao=UF")
SIGLA = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI",
         "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
         "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
LARGURA = 1000
COS = math.cos(math.radians(-15))


def aneis(geom: dict) -> list[list[list[float]]]:
    if geom["type"] == "Polygon":
        return geom["coordinates"]
    return [anel for poligono in geom["coordinates"] for anel in poligono]


def main() -> None:
    doc = json.loads(ENTRADA.read_text(encoding="utf-8"))
    pontos = [p for f in doc["features"] for anel in aneis(f["geometry"]) for p in anel]
    x0 = min(p[0] for p in pontos) * COS
    x1 = max(p[0] for p in pontos) * COS
    y0, y1 = -max(p[1] for p in pontos), -min(p[1] for p in pontos)
    k = LARGURA / (x1 - x0)
    altura = round((y1 - y0) * k, 1)

    def xy(p: list[float]) -> tuple[float, float]:
        return round((p[0] * COS - x0) * k), round((-p[1] - y0) * k)

    ufs = {}
    for f in doc["features"]:
        sigla = SIGLA[f["properties"]["codarea"]]
        partes, area_total, cx, cy = [], 0.0, 0.0, 0.0
        for anel in aneis(f["geometry"]):
            pts = [xy(p) for p in anel]
            limpos = [pts[0]] + [q for a, q in zip(pts, pts[1:]) if q != a]
            partes.append("M" + "L".join(f"{x:g},{y:g}" for x, y in limpos) + "Z")
            # centroide pela fórmula da área com sinal (shoelace); serve para pôr o rótulo da UF
            a = sum(x0_ * y1_ - x1_ * y0_ for (x0_, y0_), (x1_, y1_) in zip(limpos, limpos[1:] + limpos[:1])) / 2
            if a:
                cx += sum((x0_ + x1_) * (x0_ * y1_ - x1_ * y0_)
                          for (x0_, y0_), (x1_, y1_) in zip(limpos, limpos[1:] + limpos[:1])) / 6
                cy += sum((y0_ + y1_) * (x0_ * y1_ - x1_ * y0_)
                          for (x0_, y0_), (x1_, y1_) in zip(limpos, limpos[1:] + limpos[:1])) / 6
                area_total += a
        ufs[sigla] = {"d": "".join(partes), "x": round(cx / area_total, 1), "y": round(cy / area_total, 1)}
    # graticula: onde cada meridiano e paralelo de 10 em 10 graus corta o quadro (a moldura do atlas)
    lon = [{"g": g, "x": round((g * COS - x0) * k, 1)} for g in range(-70, -30, 10) if x0 <= g * COS <= x1]
    lat = [{"g": g, "y": round((-g - y0) * k, 1)} for g in range(0, -40, -10) if y0 <= -g <= y1]
    saida = {"fonte": "IBGE, malha de UFs, qualidade mínima", "url": URL, "largura": LARGURA, "altura": altura,
             "km_por_unidade": round(111.32 / k, 4), "meridianos": lon, "paralelos": lat, "ufs": ufs}
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(saida, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{SAIDA.relative_to(RAIZ)}: {len(ufs)} UFs, {SAIDA.stat().st_size / 1e3:.0f} KB, {LARGURA}x{altura}")


if __name__ == "__main__":
    main()
