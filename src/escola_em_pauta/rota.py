"""Caminho mais curto (em tempo) entre duas escolas: Dijkstra com fila de prioridade.

A fila de prioridade (heapq, um heap binário mínimo) é a estrutura de dados que
o problema exige: a cada passo, o Dijkstra precisa do nó ainda não fechado com
o MENOR tempo acumulado. Numa lista comum, achar esse mínimo custa O(n) a cada
passo; no heap, custa O(log n). Com ~10^5 nós, é a diferença entre segundos e
horas. Complexidade total: O((V + E) log V).

Saída: km e minutos de ida e volta, como PISO. Se não houver caminho no grafo,
devolvemos None e o aviso "rota não encontrada", nunca uma estimativa inventada.

Validação (docs/pesquisa/tce-es-durval-maximo.md): em Muniz Freire o TCE-ES
estimou até 52 km/dia; de escola a escola, 25 km para a receptora indicada. Ver validacao.py.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass

from .geo import haversine_km
from .grafo import Grafo

# Velocidade do trecho entre a escola e a estrada mais próxima (pátio, acesso).
KMH_ACESSO = 10.0
# Acima disso, a escola está longe demais de qualquer via mapeada para confiar na rota.
KM_ACESSO_MAX = 1.0


@dataclass(frozen=True)
class Caminho:
    minutos: float
    km: float
    km_chao: float  # quanto do trajeto é estrada sem pavimento
    nos: list[int]


def dijkstra(g: Grafo, origem: int, destino: int) -> Caminho | None:
    """Menor tempo de origem a destino. None se não houver caminho."""
    tempo = {origem: 0.0}
    anterior: dict[int, tuple[int, float, bool]] = {}  # nó -> (de onde veio, km da aresta, chão?)
    fechados: set[int] = set()
    heap = [(0.0, origem)]
    while heap:
        t, u = heapq.heappop(heap)
        if u in fechados:
            # "Remoção preguiçosa": o heapq não sabe diminuir a prioridade de um item,
            # então empilhamos de novo com o tempo menor e ignoramos a cópia velha aqui.
            continue
        if u == destino:
            break
        fechados.add(u)
        for v, minutos, km, chao in g.adj[u]:
            novo = t + minutos
            if novo < tempo.get(v, math.inf):
                tempo[v] = novo
                anterior[v] = (u, km, chao)
                heapq.heappush(heap, (novo, v))
    if destino not in tempo:
        return None
    nos, km, km_chao, n = [destino], 0.0, 0.0, destino
    while n != origem:
        n, k, chao = anterior[n]
        km += k
        km_chao += k if chao else 0.0
        nos.append(n)
    return Caminho(minutos=tempo[destino], km=km, km_chao=km_chao, nos=nos[::-1])


def dijkstra_muitos(adj: dict[int, list], origem: int, alvos: set[int]) -> dict[int, tuple[float, float, float]]:
    """Um Dijkstra só, da origem até TODOS os alvos: {alvo: (minutos, km, km_chao)}.

    O Dijkstra já calcula o menor caminho para cada nó que fecha; basta não parar
    no primeiro destino. Km e km de chão vão "de carona" na relaxação das arestas
    (o caminho é escolhido pelo tempo), então não é preciso reconstruir o trajeto.
    """
    melhor: dict[int, tuple[float, float, float]] = {origem: (0.0, 0.0, 0.0)}
    fechados: set[int] = set()
    faltam = set(alvos)
    heap = [(0.0, origem)]
    while heap and faltam:
        t, u = heapq.heappop(heap)
        if u in fechados:
            continue
        fechados.add(u)
        faltam.discard(u)
        _, km_u, chao_u = melhor[u]
        for v, minutos, km, chao in adj.get(u, ()):
            novo = t + minutos
            if novo < melhor.get(v, (math.inf,))[0]:
                melhor[v] = (novo, km_u + km, chao_u + (km if chao else 0.0))
                heapq.heappush(heap, (novo, v))
    return {a: melhor[a] for a in alvos if a in fechados}


@dataclass(frozen=True)
class Rota:
    """Ida e volta entre duas escolas, como piso."""
    km_ida_volta: float | None
    minutos_ida_volta: float | None
    km_chao_ida_volta: float | None
    km_linha_reta_ida_volta: float
    km_acesso: float  # maior distância entre uma das escolas e a estrada mais próxima
    aviso: str | None = None


def piso(g: Grafo, origem: tuple[float, float], destino: tuple[float, float]) -> Rota:
    """Rota de ida (origem→destino) e de volta (destino→origem); as duas podem diferir por mão única."""
    reta = 2 * haversine_km(*origem, *destino)
    no_o, acesso_o = g.no_mais_proximo(*origem)
    no_d, acesso_d = g.no_mais_proximo(*destino)
    acesso = max(acesso_o, acesso_d)
    if acesso > KM_ACESSO_MAX:
        return Rota(None, None, None, reta, acesso, f"escola a {acesso:.1f} km da estrada mapeada mais próxima".replace(".", ",", 1))
    ida, volta = dijkstra(g, no_o, no_d), dijkstra(g, no_d, no_o)
    if ida is None or volta is None:
        return Rota(None, None, None, reta, acesso, "rota não encontrada na malha do OpenStreetMap")
    km_acesso_total = 2 * (acesso_o + acesso_d)  # o trecho escola↔estrada, nas duas pontas, ida e volta
    return Rota(
        km_ida_volta=ida.km + volta.km + km_acesso_total,
        minutos_ida_volta=ida.minutos + volta.minutos + km_acesso_total / KMH_ACESSO * 60,
        km_chao_ida_volta=ida.km_chao + volta.km_chao,
        km_linha_reta_ida_volta=reta,
        km_acesso=acesso,
    )


def pisos(g: Grafo, origem: tuple[float, float], destinos: list[tuple[float, float]]) -> list[Rota]:
    """Igual a piso(), para vários destinos com 2 Dijkstras no total (ida no grafo, volta no grafo reverso)."""
    no_o, acesso_o = g.no_mais_proximo(*origem)
    pontas = [g.no_mais_proximo(*d) for d in destinos]
    alvos = {n for n, a in pontas if a <= KM_ACESSO_MAX}
    ida = dijkstra_muitos(g.adj, no_o, alvos) if acesso_o <= KM_ACESSO_MAX else {}
    volta = dijkstra_muitos(g.reverso, no_o, alvos) if acesso_o <= KM_ACESSO_MAX else {}
    saida = []
    for d, (no_d, acesso_d) in zip(destinos, pontas):
        reta = 2 * haversine_km(*origem, *d)
        acesso = max(acesso_o, acesso_d)
        if acesso > KM_ACESSO_MAX:
            saida.append(Rota(None, None, None, reta, acesso, f"escola a {acesso:.1f} km da estrada mapeada mais próxima".replace(".", ",", 1)))
        elif no_d not in ida or no_d not in volta:
            saida.append(Rota(None, None, None, reta, acesso, "rota não encontrada na malha do OpenStreetMap"))
        else:
            (m1, k1, c1), (m2, k2, c2) = ida[no_d], volta[no_d]
            ac = 2 * (acesso_o + acesso_d)
            saida.append(Rota(k1 + k2 + ac, m1 + m2 + ac / KMH_ACESSO * 60, c1 + c2, reta, acesso))
    return saida
