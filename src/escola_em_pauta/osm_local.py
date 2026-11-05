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
import math
import os
from pathlib import Path

from .censo import BRUTOS, PROCESSADOS
from .grafo import CACHE_OSM, VELOCIDADE_PAVIMENTADA

PBF_DIR = BRUTOS / "osm"
REGIAO_POR_UF = {
    **dict.fromkeys(("DF", "GO", "MT", "MS"), "centro-oeste"),
    **dict.fromkeys(("SP", "RJ", "MG", "ES"), "sudeste"),
    **dict.fromkeys(("PR", "SC", "RS"), "sul"),
    **dict.fromkeys(("MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"), "nordeste"),
    **dict.fromkeys(("AC", "AM", "AP", "PA", "RO", "RR", "TO"), "norte"),
}
TAGS = ("highway", "surface", "tracktype", "oneway", "name")
GRADE_INDICE = 0.25  # graus, passo da grade que indexa as bboxes em extrair()


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
    """Uma passada pelo PBF; cada via de carro que toca uma bbox entra inteira na malha daquela bbox.

    Para muitas bboxes numa passada (o pré-cálculo nacional extrai dezenas por vez), as bboxes ficam
    numa GRADE de células de GRADE_INDICE graus: cada via só é comparada com as bboxes das células
    que o retângulo dela toca, em vez de com todas. Sem isso, o custo crescia com (vias × bboxes):
    16 bboxes já somavam ~45 s à passada no Sudeste. O resultado é o mesmo (a grade só descarta
    bboxes que o teste de retângulo descartaria). Listas e coordenadas de uma via que entra em
    várias malhas são o MESMO objeto na memória (só são lidas, ao gravar o JSON).
    """
    import osmium

    malhas = [{"bbox": list(b), "nos": {}, "vias": []} for b in bboxes]
    grade: dict[tuple[int, int], list[int]] = {}
    for k, (s, o, n, l) in enumerate(bboxes):
        for i in range(math.floor(s / GRADE_INDICE), math.floor(n / GRADE_INDICE) + 1):
            for j in range(math.floor(o / GRADE_INDICE), math.floor(l / GRADE_INDICE) + 1):
                grade.setdefault((i, j), []).append(k)
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
        candidatas: set[int] = set()
        for i in range(math.floor(sul_v / GRADE_INDICE), math.floor(norte_v / GRADE_INDICE) + 1):
            for j in range(math.floor(oeste_v / GRADE_INDICE), math.floor(leste_v / GRADE_INDICE) + 1):
                candidatas.update(grade.get((i, j), ()))
        if not candidatas:
            continue
        tags = refs = coords = None
        for k in sorted(candidatas):
            m, (s, o, n, l) = malhas[k], bboxes[k]
            if norte_v < s or sul_v > n or leste_v < o or oeste_v > l:
                continue  # retângulo da via não encosta na bbox
            if not any(s <= la <= n and o <= lo <= l for _, la, lo in pts):
                continue  # Overpass inclui a via se algum nó dela estiver dentro
            if tags is None:
                tags = {k2: via.tags[k2] for k2 in TAGS if k2 in via.tags}
                refs = [p[0] for p in pts]
                coords = [(p[1], p[2]) for p in pts]
            m["vias"].append({"nodes": refs, "tags": tags})
            nos = m["nos"]
            for ref, c in zip(refs, coords):
                nos[ref] = c
    saidas = []
    cache.mkdir(parents=True, exist_ok=True)
    for m, (s, o, n, l) in zip(malhas, bboxes):
        m["data_osm"] = data_osm
        m["fonte"] = f"Geofabrik {pbf.name}"
        arq = cache / f"{s:.3f}_{o:.3f}_{n:.3f}_{l:.3f}.json.gz"
        # Escreve ao lado e troca (os.replace é atômico): um processo morto no meio da escrita não
        # deixa uma malha cortada passando por pronta no cache.
        # O pid no nome: dois lotes em paralelo (regiões diferentes) podem gravar a mesma célula ao mesmo
        # tempo, e um temporário comum aos dois sairia com as duas escritas misturadas.
        tmp = arq.with_name(f"{arq.name}.{os.getpid()}.parcial")
        # compresslevel=1: no nível 9 (o padrão do gzip), gravar 16 malhas levava 41 s de uma passada
        # de 122 s; no nível 1, 11 s, com arquivos um pouco maiores. O conteúdo é o mesmo.
        with gzip.open(tmp, "wt", compresslevel=1) as f:
            f.write(json.dumps(m))
        os.replace(tmp, arq)
        saidas.append(arq)
    return saidas


VIAS_DIR = PROCESSADOS / "osm_vias"


def pbf_so_vias(pbf: Path, destino: Path = VIAS_DIR) -> Path:
    """Cópia do recorte regional com SÓ as vias de carro e os nós delas (gerada uma vez, depois reaproveitada).

    Por quê: para entregar a coordenada de cada nó junto com as vias, `extrair` guarda na memória a
    posição de TODOS os nós do arquivo, inclusive os de prédios, rios e limites, que não usamos. No
    recorte do Sudeste isso dava 4,3 GB de RAM por passada; no arquivo só com vias, 0,8 GB, a passada
    ficou ~30% mais rápida e as malhas extraídas saíram idênticas, nó por nó e via por via (conferido
    em 05/11/2026). Gerar custa uma passada lenta (~10 min e ~2 GB no Sudeste), paga uma vez.

    O cabeçalho do original é copiado (data da réplica do OSM e área coberta), porque `extrair` lê a
    data da malha e `pbf_que_cobre` lê a área dali.
    """
    import osmium

    destino.mkdir(parents=True, exist_ok=True)
    saida = destino / pbf.name.replace(".osm.pbf", ".vias.osm.pbf")
    if saida.exists() and saida.stat().st_mtime >= pbf.stat().st_mtime:
        return saida
    # O osmium descobre o formato pela extensão: os temporários precisam terminar em .osm.pbf.
    sem_cabecalho = saida.with_name(saida.name.replace(".vias.osm.pbf", ".parcial1.osm.pbf"))
    final = saida.with_name(saida.name.replace(".vias.osm.pbf", ".parcial2.osm.pbf"))
    # 1) As vias filtradas + todos os nós que elas citam (o BackReferenceWriter busca os nós no original).
    with osmium.BackReferenceWriter(str(sem_cabecalho), ref_src=str(pbf), overwrite=True) as w:
        for via in (osmium.FileProcessor(str(pbf), osmium.osm.WAY)
                    .with_filter(osmium.filter.TagFilter(*[("highway", v) for v in VELOCIDADE_PAVIMENTADA]))):
            w.add_way(via)
    # 2) Regrava com o cabeçalho do original (o passo 1 o perde).
    r = osmium.io.Reader(str(pbf), osmium.osm.osm_entity_bits.NOTHING)
    cabecalho = r.header()
    r.close()
    with osmium.SimpleWriter(str(final), header=cabecalho, overwrite=True) as w:
        for obj in osmium.FileProcessor(str(sem_cabecalho)):
            w.add(obj)
    sem_cabecalho.unlink()
    os.replace(final, saida)
    return saida
