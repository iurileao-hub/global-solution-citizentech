"""Coordenadas das escolas.

Fonte principal: Ipea/geobr, schools_2023.gpkg (212 mil escolas, mesmo código
INEP em code_school; empty_geo=1 quando não há coordenada).
https://www.ipea.gov.br/geobr/data_gpkg/schools/2023/schools_2023.gpkg
Sistema de referência: SIRGAS 2000 (EPSG:4674), que difere do WGS84 do GPS e
do OpenStreetMap em menos de um metro. Para este uso, são equivalentes.

GeoPackage é SQLite: lemos com sqlite3 da biblioteca padrão, sem geopandas.
A geometria é um blob "GeoPackage binary": cabeçalho de 8 bytes ("GP", versão,
flags, srs_id), um envelope opcional cujo tamanho vem dos flags, e depois o
ponto em WKB (Well-Known Binary). Ver decodificar_ponto().

Cobertura de escolas rurais públicas em funcionamento com coordenada:
DF 96%, SP 96%, GO 92%, AM 61%, BA 60%.
Plano B: geocodificar pelo endereço (coluna address), marcando a precisão
na ficha. Nunca inventar coordenada.

Saída em dados/processados/escolas_coord.parquet (codigo_inep, lat, lon,
endereco). Gerar com: python -m escola_em_pauta.geo
"""

from __future__ import annotations

import math
import sqlite3
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .censo import BRUTOS, PROCESSADOS

GPKG = BRUTOS / "schools_2023.gpkg"

# Tamanho do envelope (bytes) pelo indicador nos bits 1-3 dos flags.
# 0 = sem envelope; 1 = [minx,maxx,miny,maxy]; 2 e 3 = +z ou +m; 4 = +z e +m.
_TAMANHO_ENVELOPE = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}


def decodificar_ponto(blob: bytes) -> tuple[float, float] | None:
    """Converte o blob GeoPackage de um ponto em (lat, lon). None se a geometria estiver vazia."""
    if blob is None or blob[:2] != b"GP":
        return None
    flags = blob[3]
    if flags & 0b0001_0000:  # bit 4: geometria vazia
        return None
    inicio_wkb = 8 + _TAMANHO_ENVELOPE[(flags >> 1) & 0b111]
    wkb = blob[inicio_wkb:]
    ordem = "<" if wkb[0] == 1 else ">"  # 1 = little-endian
    (tipo,) = struct.unpack(ordem + "I", wkb[1:5])
    if tipo != 1:  # 1 = Point
        raise ValueError(f"Geometria não é ponto (tipo WKB {tipo}).")
    lon, lat = struct.unpack(ordem + "dd", wkb[5:21])  # WKB guarda x (lon) antes de y (lat)
    if math.isnan(lon) or math.isnan(lat):
        return None
    return lat, lon


def processar(gpkg: Path = GPKG, processados: Path = PROCESSADOS) -> None:
    """Extrai do GeoPackage (101 MB) um arquivo leve só com código, coordenada e endereço."""
    con = sqlite3.connect(f"file:{gpkg}?mode=ro", uri=True)
    linhas = []
    for codigo, blob, endereco in con.execute("SELECT code_school, geom, address FROM schools_2023"):
        ponto = decodificar_ponto(blob)
        lat, lon = ponto if ponto else (None, None)
        linhas.append((int(codigo), lat, lon, endereco))
    con.close()
    df = pd.DataFrame(linhas, columns=["codigo_inep", "lat", "lon", "endereco"])
    df = df.drop_duplicates("codigo_inep")
    processados.mkdir(parents=True, exist_ok=True)
    df.to_parquet(processados / "escolas_coord.parquet", index=False)
    print(f"  {len(df):,} escolas; {df['lat'].notna().sum():,} com coordenada")


@lru_cache(maxsize=1)
def tabela() -> pd.DataFrame:
    return pd.read_parquet(PROCESSADOS / "escolas_coord.parquet").set_index("codigo_inep", drop=False)


@dataclass(frozen=True)
class Coordenada:
    lat: float | None
    lon: float | None
    precisao: str  # "ipea_geobr" | "ausente" (o plano B acrescenta "geocodificada_endereco")
    endereco: str | None


def coordenada(codigo_inep: int) -> Coordenada:
    t = tabela()
    if codigo_inep not in t.index:
        return Coordenada(None, None, "ausente", None)
    linha = t.loc[codigo_inep]
    endereco = None if pd.isna(linha["endereco"]) else str(linha["endereco"])
    if pd.isna(linha["lat"]):
        return Coordenada(None, None, "ausente", endereco)
    return Coordenada(float(linha["lat"]), float(linha["lon"]), "ipea_geobr", endereco)


RAIO_TERRA_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância em linha reta sobre a esfera. É o limite inferior de qualquer estrada."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * RAIO_TERRA_KM * math.asin(math.sqrt(a))


if __name__ == "__main__":
    processar()
