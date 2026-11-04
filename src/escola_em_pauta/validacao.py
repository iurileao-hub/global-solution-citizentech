"""Análise de erro do piso: quanto o dado público subestima a estrada real.

Caso: EMEF Durval Máximo (Muniz Freire/ES, INEP 32049501). O TCE-ES mediu
52 km por dia de transporte em estradas precárias. A fonte não identifica a
escola receptora, então comparamos as candidatas urbanas com anos finais
(as mesmas do experimento do passo 6) por três métodos:

1. linha reta (haversine), ida e volta: o limite inferior absoluto;
2. OSRM, perfil de carro (servidor público de demonstração, só como referência);
3. nossa rota: Dijkstra no grafo do OSM com velocidade de ônibus por superfície.

Erro = estimativa - medição de campo. Erro relativo = erro / medição.
n = 1 caso medido: o resultado mostra a ordem de grandeza da subestimação, e
não autoriza um fator de correção geral.

Rodar: python -m escola_em_pauta.validacao
"""

from __future__ import annotations

import json
import urllib.request

import pandas as pd

from . import censo, geo, grafo, rota
from .censo import PROCESSADOS

DURVAL = 32049501
KM_DIA_TCE = 52.0
CANDIDATAS = (32049536, 32049552, 32050070, 32050089, 32050364, 32050836)  # urbanas com anos finais

OSRM = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}?overview=false"
CACHE_OSRM = PROCESSADOS / "osrm_referencia.json"


def _osrm_km_min(origem: tuple[float, float], destino: tuple[float, float], cache: dict) -> tuple[float, float]:
    chave = f"{origem[0]:.6f},{origem[1]:.6f}->{destino[0]:.6f},{destino[1]:.6f}"
    if chave not in cache:
        url = OSRM.format(origem[1], origem[0], destino[1], destino[0])  # OSRM usa lon,lat
        req = urllib.request.Request(url, headers={"User-Agent": "escola-em-pauta/0.1 (projeto academico)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            rotas = json.load(r)["routes"][0]
        cache[chave] = (rotas["distance"] / 1000, rotas["duration"] / 60)
    return tuple(cache[chave])


def validar_muniz_freire() -> pd.DataFrame:
    cache = json.loads(CACHE_OSRM.read_text()) if CACHE_OSRM.exists() else {}
    o = geo.coordenada(DURVAL)
    origem = (o.lat, o.lon)
    destinos = {c: geo.coordenada(c) for c in CANDIDATAS}
    g = grafo.grafo_ao_redor([origem] + [(d.lat, d.lon) for d in destinos.values()])
    r = censo.retrato()
    linhas = []
    for codigo, d in destinos.items():
        destino = (d.lat, d.lon)
        nossa = rota.piso(g, origem, destino)
        ida = _osrm_km_min(origem, destino, cache)
        volta = _osrm_km_min(destino, origem, cache)
        linhas.append({
            "receptora": r.loc[codigo, "nome"],
            "linha_reta_km": nossa.km_linha_reta_ida_volta,
            "osrm_km": ida[0] + volta[0],
            "osrm_min": ida[1] + volta[1],
            "nossa_km": nossa.km_ida_volta,
            "nossa_min": nossa.minutos_ida_volta,
            "nossa_km_chao": nossa.km_chao_ida_volta,
        })
    CACHE_OSRM.write_text(json.dumps(cache, indent=1))
    df = pd.DataFrame(linhas)
    for m in ("linha_reta", "osrm", "nossa"):
        df[f"{m}_erro_rel"] = (df[f"{m}_km"] - KM_DIA_TCE) / KM_DIA_TCE
    df.to_csv(PROCESSADOS / "validacao_muniz_freire.csv", index=False)
    return df


def resumo(df: pd.DataFrame) -> str:
    """Tabela em Markdown para o README e o relatório."""
    cab = "| Receptora candidata | Linha reta (km) | OSRM carro (km / min) | Nossa rota ônibus (km / min) | dos quais de chão (km) |\n|---|---|---|---|---|\n"
    corpo = "".join(
        f"| {x.receptora.title()} | {x.linha_reta_km:.1f} | {x.osrm_km:.1f} / {x.osrm_min:.0f} | {x.nossa_km:.1f} / {x.nossa_min:.0f} | {x.nossa_km_chao:.1f} |\n"
        for x in df.itertuples()
    )
    faixa = lambda c: f"{df[c].min():+.0%} a {df[c].max():+.0%}"  # noqa: E731
    rodape = (
        f"\nErro relativo contra os {KM_DIA_TCE:.0f} km/dia medidos pelo TCE-ES: "
        f"linha reta {faixa('linha_reta_erro_rel')}; OSRM {faixa('osrm_erro_rel')}; "
        f"nossa rota {faixa('nossa_erro_rel')}.\n"
    )
    return cab + corpo + rodape


if __name__ == "__main__":
    print(resumo(validar_muniz_freire()))
