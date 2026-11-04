"""Malha viária do OpenStreetMap como grafo.

Fonte: Overpass API (dados sob licença ODbL, atribuição obrigatória na ficha
e no site: "© colaboradores do OpenStreetMap"). Baixamos as vias de carro de
um retângulo (bbox) e guardamos em cache local; a mesma bbox nunca é baixada
duas vezes. Na v1 a bbox cobre a escola e as receptoras candidatas; na v2 é a
mesma chamada, feita sob demanda.

Estrutura de dados: LISTA DE ADJACÊNCIA, dict[nó, list[(vizinho, minutos, km, chão)]],
em que chão = True quando a via não é pavimentada.
É a representação natural de uma malha viária, que é um grafo esparso: cada
cruzamento liga a 3 ou 4 vizinhos, e não a milhares. Uma matriz de adjacência
de 50 mil nós teria 2,5 bilhões de células, quase todas vazias.

O custo de cada aresta é TEMPO, com velocidade de ÔNIBUS ESCOLAR por tipo de
via e superfície (estrada de chão é mais lenta que asfalto).

Por que calcular a rota nós mesmos, se o OSRM existe? Não é porque o OSRM
ignore a superfície: o perfil de carro dele já limita terra a 40 km/h
(conferido em profiles/car.lua, 04/11/2026; nossa hipótese inicial estava
errada). Os motivos são outros: (1) o perfil do OSRM é de carro, e o nosso é
de ônibus, com a tabela de velocidades à vista de quem lê a ficha; (2) o
servidor público do OSRM é de demonstração e não aceita uso em produção, o
que a v2 exigiria; (3) contamos quantos km do trajeto são de chão, o que o
OSRM não informa; (4) o grafo com Dijkstra é a estrutura de dados do projeto.

As velocidades da tabela abaixo são PARÂMETROS DECLARADOS para um ônibus
escolar, e não medidas. Quando a superfície não está marcada no OSM, usamos a
velocidade da via pavimentada: isso mantém o resultado como PISO (nunca
superestima o tempo) e fica declarado na ficha.
"""

from __future__ import annotations

import gzip
import json
import math
import sys
import time
import urllib.parse
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from pathlib import Path

from .censo import PROCESSADOS
from .geo import haversine_km

CACHE_OSM = PROCESSADOS / "osm"

OVERPASS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)

# km/h de um ônibus escolar em via pavimentada, por tipo de via (highway=*).
VELOCIDADE_PAVIMENTADA = {
    "motorway": 80, "motorway_link": 50,
    "trunk": 70, "trunk_link": 45,
    "primary": 60, "primary_link": 40,
    "secondary": 50, "secondary_link": 35,
    "tertiary": 40, "tertiary_link": 30,
    "unclassified": 35, "road": 30,
    "residential": 25, "living_street": 15, "service": 15,
    "track": 25,
}

# Teto de velocidade (km/h) quando a via NÃO é pavimentada, por surface=*.
TETO_SEM_PAVIMENTO = {
    "compacted": 35, "fine_gravel": 30, "gravel": 30, "pebblestone": 25,
    "unpaved": 25, "dirt": 25, "earth": 25, "ground": 25,
    "grass": 15, "sand": 15, "mud": 10,
}

# Estradas de chão marcadas só pela qualidade (tracktype), sem surface.
TETO_TRACKTYPE = {"grade1": 35, "grade2": 25, "grade3": 20, "grade4": 15, "grade5": 10}

VIAS = "|".join(VELOCIDADE_PAVIMENTADA)


def velocidade_kmh(tags: dict) -> tuple[float, str]:
    """Velocidade de ônibus numa via e a categoria de piso usada ('pavimentada', 'sem pavimento', 'não marcada')."""
    v = VELOCIDADE_PAVIMENTADA.get(tags.get("highway"), 25)
    superficie = tags.get("surface")
    if superficie in TETO_SEM_PAVIMENTO:
        return min(v, TETO_SEM_PAVIMENTO[superficie]), "sem pavimento"
    if tags.get("tracktype") in TETO_TRACKTYPE and superficie is None:
        return min(v, TETO_TRACKTYPE[tags["tracktype"]]), "sem pavimento"
    if superficie is None:
        return v, "não marcada"
    return v, "pavimentada"


def _consulta(sul: float, oeste: float, norte: float, leste: float) -> str:
    return (
        "[out:json][timeout:180];"
        f'way["highway"~"^({VIAS})$"]({sul},{oeste},{norte},{leste});'
        "out body;>;out skel qt;"
    )


def baixar_malha(sul: float, oeste: float, norte: float, leste: float, cache: Path = CACHE_OSM) -> dict:
    """Vias e nós de uma bbox, do cache local ou do Overpass (que tem limite de uso: 1 chamada por vez)."""
    chave = f"{sul:.3f}_{oeste:.3f}_{norte:.3f}_{leste:.3f}"
    arquivo = cache / f"{chave}.json.gz"
    # Reaproveita qualquer malha já baixada que CONTENHA a área pedida (a menor delas).
    contem = [
        (area, p) for p, (s, o, n, l) in _bboxes_em_cache(cache)
        if s <= sul and o <= oeste and n >= norte and l >= leste
        for area in [(n - s) * (l - o)]
    ]
    if contem:
        with gzip.open(min(contem)[1], "rt") as f:
            return json.load(f)
    print(f"  baixando malha OSM {chave} do Overpass...", file=sys.stderr)
    corpo = urllib.parse.urlencode({"data": _consulta(sul, oeste, norte, leste)}).encode()
    ultimo_erro = None
    for tentativa, url in enumerate(OVERPASS * 2):
        try:
            req = urllib.request.Request(url, data=corpo, headers={"User-Agent": "escola-em-pauta/0.1 (projeto academico)"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                bruto = json.load(resp)
            break
        except Exception as e:  # rede, 429 (limite) ou 504 (servidor ocupado): tenta o espelho, depois espera
            ultimo_erro = e
            time.sleep(5 * (tentativa + 1))
    else:
        raise RuntimeError(f"Overpass indisponível: {ultimo_erro}")
    # Guardamos só o que o grafo usa: coordenada dos nós e, das vias, a sequência de nós e 5 tags.
    nos = {e["id"]: (e["lat"], e["lon"]) for e in bruto["elements"] if e["type"] == "node"}
    vias = [
        {"nodes": e["nodes"], "tags": {k: e["tags"][k] for k in ("highway", "surface", "tracktype", "oneway", "name") if k in e.get("tags", {})}}
        for e in bruto["elements"] if e["type"] == "way"
    ]
    malha = {"bbox": [sul, oeste, norte, leste], "data_osm": bruto.get("osm3s", {}).get("timestamp_osm_base"), "nos": nos, "vias": vias}
    cache.mkdir(parents=True, exist_ok=True)
    with gzip.open(arquivo, "wt") as f:
        json.dump(malha, f)
    return json.loads(json.dumps(malha))  # mesmas chaves (str) que a leitura do cache devolve


def _bboxes_em_cache(cache: Path) -> list[tuple[Path, tuple[float, float, float, float]]]:
    """Lê as bboxes do nome dos arquivos de cache (sul_oeste_norte_leste.json.gz)."""
    saida = []
    for p in cache.glob("*.json.gz"):
        try:
            saida.append((p, tuple(float(x) for x in p.name.removesuffix(".json.gz").split("_"))))
        except ValueError:
            continue
    return saida


def bbox_ao_redor(pontos: list[tuple[float, float]], margem_km: float = 5.0) -> tuple[float, float, float, float]:
    """Retângulo que contém todos os pontos (lat, lon) mais uma margem, arredondado para reaproveitar o cache."""
    lats, lons = [p[0] for p in pontos], [p[1] for p in pontos]
    dlat = margem_km / 111.2
    dlon = margem_km / (111.2 * math.cos(math.radians(sum(lats) / len(lats))))
    arred = lambda x, f: f(x * 100) / 100  # noqa: E731  (passo de 0,01 grau, ~1 km)
    return (arred(min(lats) - dlat, math.floor), arred(min(lons) - dlon, math.floor),
            arred(max(lats) + dlat, math.ceil), arred(max(lons) + dlon, math.ceil))


@dataclass
class Grafo:
    adj: dict[int, list[tuple[int, float, float, bool]]] = field(default_factory=dict)  # nó -> [(vizinho, minutos, km, chão)]
    coord: dict[int, tuple[float, float]] = field(default_factory=dict)
    km_por_piso: dict[str, float] = field(default_factory=dict)
    data_osm: str | None = None

    @cached_property
    def reverso(self) -> dict[int, list[tuple[int, float, float, bool]]]:
        """Mesmas arestas, sentido invertido: caminhos de qualquer nó ATÉ a origem viram caminhos DA origem."""
        rev: dict[int, list[tuple[int, float, float, bool]]] = {n: [] for n in self.adj}
        for a, viz in self.adj.items():
            for b, minutos, km, chao in viz:
                rev[b].append((a, minutos, km, chao))
        return rev

    @property
    def n_nos(self) -> int:
        return len(self.adj)

    @property
    def n_arestas(self) -> int:
        return sum(len(v) for v in self.adj.values())

    @cached_property
    def _nos_np(self):
        import numpy as np
        ids = np.fromiter(self.adj.keys(), dtype=np.int64, count=len(self.adj))
        coords = np.array([self.coord[n] for n in ids], dtype=float)
        return ids, coords[:, 0], coords[:, 1]

    def no_mais_proximo(self, lat: float, lon: float) -> tuple[int, float]:
        """Nó do grafo mais perto de um ponto e a distância até ele em km.

        Busca linear O(n), mas vetorizada com numpy (milhões de nós em milissegundos).
        Aproximação equirretangular para ordenar; haversine exato só no vencedor.
        """
        import numpy as np
        ids, lats, lons = self._nos_np
        c = math.cos(math.radians(lat))
        i = int(np.argmin((lats - lat) ** 2 + ((lons - lon) * c) ** 2))
        melhor = int(ids[i])
        return melhor, haversine_km(lat, lon, *self.coord[melhor])


def construir(malha: dict) -> Grafo:
    """Transforma vias do OSM em lista de adjacência e mantém só a maior componente conexa."""
    coord = {int(k): tuple(v) for k, v in malha["nos"].items()}
    adj: dict[int, list[tuple[int, float, float, bool]]] = {}
    km_por_piso: dict[str, float] = {}
    for via in malha["vias"]:
        tags = via["tags"]
        kmh, piso = velocidade_kmh(tags)
        mao = tags.get("oneway")  # "yes": só no sentido do desenho; "-1": só no contrário
        ida = mao != "-1"
        volta = mao not in ("yes", "true", "1")
        nos = [n for n in via["nodes"] if n in coord]
        for a, b in zip(nos, nos[1:]):
            km = haversine_km(*coord[a], *coord[b])
            minutos = km / kmh * 60
            chao = piso == "sem pavimento"
            km_por_piso[piso] = km_por_piso.get(piso, 0.0) + km
            adj.setdefault(a, [])
            adj.setdefault(b, [])
            if ida:
                adj[a].append((b, minutos, km, chao))
            if volta:
                adj[b].append((a, minutos, km, chao))
    # Pedaços soltos (uma rua sem ligação mapeada) fariam a escola "grudar" num nó sem saída.
    maior = _maior_componente(adj)
    adj = {n: [e for e in viz if e[0] in maior] for n, viz in adj.items() if n in maior}
    return Grafo(adj=adj, coord={n: coord[n] for n in adj}, km_por_piso=km_por_piso, data_osm=malha.get("data_osm"))


def _maior_componente(adj: dict[int, list]) -> set[int]:
    """Busca em largura (BFS) ignorando a mão das vias; devolve o maior conjunto de nós ligados."""
    vizinhos: dict[int, set[int]] = {n: set() for n in adj}
    for a, viz in adj.items():
        for b, *_ in viz:
            vizinhos[a].add(b)
            vizinhos[b].add(a)
    vistos: set[int] = set()
    maior: set[int] = set()
    for inicio in vizinhos:
        if inicio in vistos:
            continue
        comp, fila = {inicio}, deque([inicio])
        while fila:
            for v in vizinhos[fila.popleft()]:
                if v not in comp:
                    comp.add(v)
                    fila.append(v)
        vistos |= comp
        if len(comp) > len(maior):
            maior = comp
    return maior


def arquivo_da_malha(sul: float, oeste: float, norte: float, leste: float, cache: Path = CACHE_OSM) -> Path:
    """Arquivo em cache que contém a bbox (a menor delas); baixa do Overpass se nenhum contiver."""
    contem = [((n - s) * (l - o), p) for p, (s, o, n, l) in _bboxes_em_cache(cache)
              if s <= sul and o <= oeste and n >= norte and l >= leste]
    if not contem:
        baixar_malha(sul, oeste, norte, leste, cache)
        return arquivo_da_malha(sul, oeste, norte, leste, cache)
    return min(contem)[1]


@lru_cache(maxsize=2)
def _grafo_do_arquivo(arquivo: Path) -> Grafo:
    with gzip.open(arquivo, "rt") as f:
        return construir(json.load(f))


def grafo_ao_redor(pontos: list[tuple[float, float]], margem_km: float = 5.0) -> Grafo:
    """Grafo que cobre os pontos. Construído uma vez por arquivo de malha e reaproveitado (muitas escolas, uma malha)."""
    return _grafo_do_arquivo(arquivo_da_malha(*bbox_ao_redor(pontos, margem_km)))
