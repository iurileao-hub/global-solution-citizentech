"""Traçado compacto de uma rota, para desenhar no mapa da versão web (segunda passada do pré-cálculo).

Do Dijkstra sai a lista de NÓS do caminho (rota.pisos(..., tracados=True)). Um caminho de 30 km tem
centenas de nós, quase todos em linha reta uns com os outros: guardar todos seria pesado demais para
~41 mil escolas x 10 receptoras. Três passos deixam o traçado pequeno sem perder o que importa:

1. SIMPLIFICAR (Douglas-Peucker): de uma sequência de pontos, mantém só os que se afastam mais de
   `tol_m` metros da reta entre os pontos mantidos vizinhos. O algoritmo é recursivo na ideia (liga as
   pontas; o ponto mais longe dessa reta, se passar da tolerância, vira ponta de dois pedaços menores) e
   aqui roda com uma pilha explícita, para caminhos longos não estourarem o limite de recursão do Python.
   Os pontos em que a estrada muda de asfalto para chão (e vice-versa) são SEMPRE mantidos: cada trecho
   de mesma superfície é simplificado à parte. Assim, o trecho de chão do traçado começa e termina onde
   começa e termina o chão de verdade.
2. CODIFICAR (polyline do Google, precisão 5 = 1e-5 grau, ~1 m): cada ponto vira a DIFERENÇA para o
   anterior, em inteiros pequenos escritos em 5 bits por caractere. É o formato que bibliotecas de mapa
   (Leaflet, MapLibre, OSRM, Google) já entendem, e o decodificador cabe em 15 linhas de JavaScript.
3. MARCAR O CHÃO: lista plana [i0, j0, i1, j1, ...] de índices do traçado simplificado: do ponto i ao
   ponto j, a estrada é de chão.

O traçado começa na coordenada da escola de origem e termina na da receptora (os trechos escola-estrada,
de até 1 km, entram como segmento reto, sem chão), então o mapa sabe onde pôr os dois marcadores.
Só biblioteca padrão: o navegador refaz a decodificação, e tests/test_tracado.py confere a ida e volta.
"""

from __future__ import annotations

import math

from .geo import RAIO_TERRA_KM, haversine_km

PRECISAO = 5
# Tolerância da simplificação, em metros. Medida em 05/11/2026 em 1.913 rotas (DF, Vale do Ribeira, PA, BA):
#   tol | pontos/rota (mediana) | erro do km do traçado: mediana, p5, p1 | gzip dos 10 traçados de uma escola
#    10 |  44 (de 187)          | -0,2%  -0,7%  -1,0%                     | ~0,8 KB
#    25 |  29                   | -0,7%  -1,9%  -3,0%                     | ~0,6 KB
#    50 |  20                   | -1,4%  -4,0%  -12%                      | ~0,5 KB
# (a simplificação corta curvas, então o traçado fica um pouco MAIS CURTO que a rota calculada.)
# 10 m: 99% das rotas a menos de 1% do km calculado, e no zoom de rua (~5 m por pixel) o desvio é de
# ~2 pixels, abaixo da largura do traço. Os 0,2 KB a mais por escola não pesam (cada escola abre um pedaço).
TOLERANCIA_M = 10.0


def pontos_e_chao(g, nos: tuple[int, ...] | list[int], origem: tuple[float, float],
                  destino: tuple[float, float]) -> tuple[list[tuple[float, float]], list[bool]]:
    """Pontos do traçado (escola, nós do caminho, receptora) e, para cada segmento, se é de chão.

    O Dijkstra guarda só o nó anterior; a aresta usada entre u e v é a de MENOR tempo entre as que ligam
    u a v (a mesma que o Dijkstra escolheu: ele só troca de caminho quando o tempo melhora de fato, e
    `min` devolve a primeira entre empates, como a relaxação).
    """
    pts = [tuple(origem)] + [tuple(g.coord[n]) for n in nos] + [tuple(destino)]
    chao = [False]  # acesso da escola de origem até a estrada
    for u, v in zip(nos, nos[1:]):
        aresta = min((e for e in g.adj[u] if e[0] == v), key=lambda e: e[1])
        chao.append(bool(aresta[3]))
    chao.append(False)  # da estrada até a receptora
    return pts, chao


def _xy(pontos: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """Projeção local equirretangular em metros (erro desprezível na escala de uma rota escolar)."""
    lat0 = math.radians(sum(p[0] for p in pontos) / len(pontos))
    r = RAIO_TERRA_KM * 1000
    c = math.cos(lat0)
    return [(r * math.radians(lon) * c, r * math.radians(lat)) for lat, lon in pontos]


def _dist_segmento(p, a, b) -> float:
    """Distância (m) do ponto p ao SEGMENTO a-b (não à reta infinita)."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    n2 = dx * dx + dy * dy
    if n2 == 0.0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / n2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _douglas_peucker(xy: list[tuple[float, float]], i: int, j: int, tol_m: float, manter: set[int]) -> None:
    """Marca em `manter` os índices entre i e j (exclusive) que a simplificação conserva."""
    pilha = [(i, j)]
    while pilha:
        a, b = pilha.pop()
        dmax, k = -1.0, -1
        for m in range(a + 1, b):
            d = _dist_segmento(xy[m], xy[a], xy[b])
            if d > dmax:
                dmax, k = d, m
        if k >= 0 and dmax > tol_m:
            manter.add(k)
            pilha.append((a, k))
            pilha.append((k, b))


def simplificar(pontos: list[tuple[float, float]], chao: list[bool],
                tol_m: float = TOLERANCIA_M) -> tuple[list[tuple[float, float]], list[int]]:
    """Douglas-Peucker por trecho de mesma superfície. Devolve (pontos mantidos, chão em pares [i, j, ...])."""
    if len(pontos) != len(chao) + 1:
        raise ValueError("chao deve ter um valor por segmento (len(pontos) - 1)")
    if len(pontos) <= 2:
        return list(pontos), ([0, 1] if chao and chao[0] else [])
    xy = _xy(pontos)
    # Fronteiras de superfície: o ponto i separa o segmento i-1 do segmento i.
    cortes = [0] + [i for i in range(1, len(chao)) if chao[i] != chao[i - 1]] + [len(pontos) - 1]
    manter = set(cortes)
    for a, b in zip(cortes, cortes[1:]):
        _douglas_peucker(xy, a, b, tol_m, manter)
    idx = sorted(manter)
    saida = [pontos[i] for i in idx]
    pares: list[int] = []
    for n, (a, b) in enumerate(zip(idx, idx[1:])):
        if chao[a]:  # o trecho a..b inteiro tem a mesma superfície (os cortes estão em `manter`)
            if pares and pares[-1] == n:
                pares[-1] = n + 1  # emenda com o trecho de chão anterior
            else:
                pares += [n, n + 1]
    return saida, pares


def _arredonda(x: float, f: int) -> int:
    return math.floor(x * f + 0.5)  # igual ao Math.round do JavaScript (meio arredonda para cima)


def codificar(pontos: list[tuple[float, float]], precisao: int = PRECISAO) -> str:
    """Polyline do Google: diferenças entre pontos consecutivos, em blocos de 5 bits (caracteres 63 a 126)."""
    f = 10 ** precisao
    saida: list[str] = []
    ant_lat = ant_lon = 0
    for lat, lon in pontos:
        ilat, ilon = _arredonda(lat, f), _arredonda(lon, f)
        for d in (ilat - ant_lat, ilon - ant_lon):
            v = ~(d << 1) if d < 0 else d << 1  # sinal no bit mais baixo
            while v >= 0x20:
                saida.append(chr((0x20 | (v & 0x1F)) + 63))
                v >>= 5
            saida.append(chr(v + 63))
        ant_lat, ant_lon = ilat, ilon
    return "".join(saida)


def decodificar(texto: str, precisao: int = PRECISAO) -> list[tuple[float, float]]:
    """Inverso de codificar (o navegador faz exatamente estas contas)."""
    f = 10 ** precisao
    pontos: list[tuple[float, float]] = []
    i = lat = lon = 0
    while i < len(texto):
        deltas = []
        for _ in range(2):
            resultado = deslocamento = 0
            while True:
                b = ord(texto[i]) - 63
                i += 1
                resultado |= (b & 0x1F) << deslocamento
                deslocamento += 5
                if b < 0x20:
                    break
            deltas.append(~(resultado >> 1) if resultado & 1 else resultado >> 1)
        lat += deltas[0]
        lon += deltas[1]
        pontos.append((lat / f, lon / f))
    return pontos


def comprimento_km(pontos: list[tuple[float, float]]) -> float:
    return sum(haversine_km(*a, *b) for a, b in zip(pontos, pontos[1:]))


def km_chao(pontos: list[tuple[float, float]], pares: list[int]) -> float:
    """Km de chão no traçado, a partir dos pares [i, j, ...]."""
    return sum(comprimento_km(pontos[i:j + 1]) for i, j in zip(pares[::2], pares[1::2]))


def tracar(g, nos, origem: tuple[float, float], destino: tuple[float, float],
           tol_m: float = TOLERANCIA_M) -> dict:
    """{"p": polyline do traçado simplificado, "pc": [i, j, ...] trechos de chão} (pc só quando há chão)."""
    pts, chao = pontos_e_chao(g, nos, origem, destino)
    simp, pares = simplificar(pts, chao, tol_m)
    saida = {"p": codificar(simp)}
    if pares:
        saida["pc"] = pares
    return saida
