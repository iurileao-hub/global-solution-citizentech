"""Malha viária a partir de um recorte regional do OpenStreetMap (Geofabrik), sem depender do Overpass.

FONTE PADRÃO do projeto (decisão de Iúri, 04/11/2026): os servidores públicos do
Overpass caíram os três ao mesmo tempo durante a geração do site, e a apresentação
não pode depender deles. Baixamos uma vez o recorte da região (formato PBF, binário
compacto do OSM, com md5 publicado: reprodutível) e extraímos localmente as vias de
várias áreas numa passada só. O Overpass só é usado se pedido explicitamente
(grafo.arquivo_da_malha(..., fonte="overpass")).

Recortes (https://download.geofabrik.de/south-america/brazil/):
centro-oeste-latest.osm.pbf (~208 MB) e sudeste-latest.osm.pbf (~863 MB),
em dados/brutos/osm/. Conferir o .md5 publicado ao lado de cada arquivo.

A saída tem o MESMO formato do cache do Overpass (grafo.baixar_malha): o resto
do código não sabe de onde a malha veio.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from .censo import BRUTOS
from .grafo import CACHE_OSM, VELOCIDADE_PAVIMENTADA

PBF_DIR = BRUTOS / "osm"
REGIAO_POR_UF = {
    **dict.fromkeys(("DF", "GO", "MT", "MS"), "centro-oeste"),
    **dict.fromkeys(("SP", "RJ", "MG", "ES"), "sudeste"),
    **dict.fromkeys(("PR", "SC", "RS"), "sul"),
}
TAGS = ("highway", "surface", "tracktype", "oneway", "name")


def pbf_que_cobre(bbox: tuple[float, float, float, float]) -> Path | None:
    """O menor recorte em dados/brutos/osm/ cuja área (gravada no cabeçalho do PBF) contém a bbox."""
    import osmium

    s, o, n, l = bbox
    melhor = None
    for pbf in sorted(PBF_DIR.glob("*.osm.pbf")):
        r = osmium.io.Reader(str(pbf), osmium.osm.osm_entity_bits.NOTHING)
        caixa = r.header().box()
        r.close()
        if not caixa.valid():
            continue
        bl, tr = caixa.bottom_left, caixa.top_right
        if bl.lat <= s and bl.lon <= o and tr.lat >= n and tr.lon >= l:
            area = (tr.lat - bl.lat) * (tr.lon - bl.lon)
            if melhor is None or area < melhor[0]:
                melhor = (area, pbf)
    return melhor[1] if melhor else None


def pbf_da_uf(uf: str) -> Path | None:
    regiao = REGIAO_POR_UF.get(uf)
    p = PBF_DIR / f"{regiao}-latest.osm.pbf" if regiao else None
    return p if p and p.exists() else None


def extrair(pbf: Path, bboxes: list[tuple[float, float, float, float]], cache: Path = CACHE_OSM) -> list[Path]:
    """Uma passada pelo PBF; cada via de carro que toca uma bbox entra inteira na malha daquela bbox."""
    import osmium

    malhas = [{"bbox": list(b), "nos": {}, "vias": []} for b in bboxes]
    fp = (osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
          .with_locations()  # guarda a coordenada de todo nó lido e a entrega junto com as vias
          .with_filter(osmium.filter.EntityFilter(osmium.osm.WAY))
          .with_filter(osmium.filter.TagFilter(*[("highway", v) for v in VELOCIDADE_PAVIMENTADA])))
    data_osm = fp.header.get("osmosis_replication_timestamp") or None
    for via in fp:
        pts = [(n.ref, n.location.lat, n.location.lon) for n in via.nodes if n.location.valid()]
        if len(pts) < 2:
            continue
        lats = [p[1] for p in pts]
        lons = [p[2] for p in pts]
        sul_v, norte_v, oeste_v, leste_v = min(lats), max(lats), min(lons), max(lons)
        tags = None
        for m, (s, o, n, l) in zip(malhas, bboxes):
            if norte_v < s or sul_v > n or leste_v < o or oeste_v > l:
                continue  # retângulo da via não encosta na bbox
            if not any(s <= la <= n and o <= lo <= l for _, la, lo in pts):
                continue  # Overpass inclui a via se algum nó dela estiver dentro
            if tags is None:
                tags = {k: via.tags[k] for k in TAGS if k in via.tags}
            m["vias"].append({"nodes": [p[0] for p in pts], "tags": tags})
            for ref, la, lo in pts:
                m["nos"][ref] = (la, lo)
    saidas = []
    cache.mkdir(parents=True, exist_ok=True)
    for m, (s, o, n, l) in zip(malhas, bboxes):
        m["data_osm"] = data_osm
        m["fonte"] = f"Geofabrik {pbf.name}"
        arq = cache / f"{s:.3f}_{o:.3f}_{n:.3f}_{l:.3f}.json.gz"
        with gzip.open(arq, "wt") as f:
            json.dump(m, f)
        saidas.append(arq)
    return saidas
