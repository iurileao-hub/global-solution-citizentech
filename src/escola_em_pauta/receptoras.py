"""Escolas receptoras possíveis para os alunos de uma escola.

Critério: escolas públicas ATIVAS, com coordenada, que oferecem ao menos uma
das etapas da escola de origem (a nucleação pode dividir as etapas entre
escolas diferentes; por isso cada receptora diz quais etapas cobre).

Busca em dois tempos, para não rodar o Dijkstra contra o país inteiro:
1. pré-filtro em linha reta: as `pre_filtro` mais próximas (cálculo vetorial
   sobre ~140 mil escolas, alguns milissegundos);
2. rota real só para essas, e ficam as k de menor distância por estrada.

Marcamos se a receptora é rural ou urbana: o TCE-ES tratou receptora urbana
como irregularidade, e a Res. CNE/CEB 2/2008, art. 3º, pede pré-escola e anos
iniciais na própria comunidade. A ocupação é um PROXY (matrícula / salas
utilizadas), rotulado como estimativa: a vaga real não é publicada.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import censo, geo, grafo, rota
from .modelos import Escola, Receptora

RAIO_MAX_KM = 60.0  # em linha reta; além disso a escola não é receptora plausível


def escola(codigo_inep: int) -> Escola:
    info, _ = censo.escola_e_serie(codigo_inep)
    c = geo.coordenada(codigo_inep)
    return Escola(
        codigo_inep=codigo_inep, nome=info["nome"], municipio=info["municipio"], uf=info["uf"],
        rural=info["rural"], localizacao_diferenciada=info["localizacao_diferenciada"],
        lat=c.lat, lon=c.lon, precisao_coordenada=c.precisao,
    )


def _distancias_km(lat: float, lon: float, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Haversine vetorizado (a mesma fórmula de geo.haversine_km, para um array inteiro de uma vez)."""
    p1, p2 = np.radians(lat), np.radians(lats)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(lons - lon) / 2) ** 2
    return 2 * geo.RAIO_TERRA_KM * np.arcsin(np.sqrt(a))


def pre_filtrar(origem: Escola, etapas: list[str], n: int) -> pd.DataFrame:
    """As n escolas ativas mais próximas em linha reta que oferecem alguma das etapas."""
    r = censo.retrato()
    t = geo.tabela()
    pool = r[(r["situacao"] == 1) & (r.index != origem.codigo_inep)]
    pool = pool[(pool[etapas] > 0).any(axis=1)]
    pool = pool.join(t[["lat", "lon"]], how="inner").dropna(subset=["lat", "lon"])
    pool = pool.assign(reta_km=_distancias_km(origem.lat, origem.lon, pool["lat"].to_numpy(), pool["lon"].to_numpy()))
    return pool[pool["reta_km"] <= RAIO_MAX_KM].nsmallest(n, "reta_km")


def candidatas(origem: Escola, etapas: list[str], k: int = 6, pre_filtro: int = 12,
               g: grafo.Grafo | None = None) -> tuple[list[Receptora], grafo.Grafo | None]:
    """As k receptoras de menor distância por estrada, e o grafo usado (para a ficha citar a malha)."""
    if origem.lat is None:
        return [], None
    perto = pre_filtrar(origem, etapas, pre_filtro)
    if perto.empty:
        return [], None
    if g is None:
        g = grafo.grafo_ao_redor([(origem.lat, origem.lon)] + list(zip(perto["lat"], perto["lon"])))
    lista = []
    rotas = rota.pisos(g, (origem.lat, origem.lon), list(zip(perto["lat"], perto["lon"])))
    for (codigo, x), rt in zip(perto.iterrows(), rotas):
        salas = x["salas_utilizadas"]
        lista.append(Receptora(
            escola=escola(int(codigo)),
            rural=int(x["localizacao"]) == 2,
            etapas_cobertas=tuple(e for e in etapas if x[e] > 0),
            km_linha_reta_ida_volta=rt.km_linha_reta_ida_volta,
            km_ida_volta_piso=rt.km_ida_volta,
            minutos_ida_volta_piso=rt.minutos_ida_volta,
            km_chao_ida_volta=rt.km_chao_ida_volta,
            alunos_por_sala=None if pd.isna(salas) or salas == 0 else float(x["matricula_total"]) / float(salas),
            aviso=rt.aviso,
        ))
    # Ordem por estrada; sem rota vai para o fim, ordenado pela linha reta (que continua sendo informação).
    lista.sort(key=lambda r: (r.km_ida_volta_piso is None, r.km_ida_volta_piso or r.km_linha_reta_ida_volta))
    return lista[:k], g
