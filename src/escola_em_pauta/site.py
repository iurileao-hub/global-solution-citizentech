"""Gerador do site estático (v1): uma ficha por escola dos territórios + página de busca.

Territórios de demonstração (decisão de 04/11):
- DF: todas as escolas públicas rurais ativas.
- Vale do Ribeira/SP: escolas públicas rurais ativas de 21 municípios (lista abaixo,
  definição usual do Vale do Ribeira paulista; a contagem do fase2b, "~22 municípios,
  177 ativas", usou uma lista que não ficou registrada; esta dá 172 em 2024).
- Muniz Freire/ES: caso de validação (medição de campo do TCE-ES).

Malha viária: um download do Overpass por grupo (município, ou o DF inteiro),
cobrindo todas as escolas do grupo e suas candidatas; depois, cada escola usa a
malha em cache que a contém. Publicação: GitHub Pages (pasta site/, fora do git
principal, publicada na branch gh-pages).

Rodar: python -m escola_em_pauta.site [territorio ...]
"""

from __future__ import annotations

import json
import math
import sys
import time
import traceback
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import censo, ficha, geo, grafo, receptoras
from .censo import ETAPAS, RAIZ
from .diagnostico import diagnosticar

SITE = RAIZ / "site"
CELULA = 0.25  # graus

VALE_DO_RIBEIRA = (
    "Apiaí", "Barra do Chapéu", "Barra do Turvo", "Cajati", "Cananéia", "Eldorado", "Iguape",
    "Ilha Comprida", "Iporanga", "Itaoca", "Itapirapuã Paulista", "Itariri", "Jacupiranga", "Juquiá",
    "Miracatu", "Pariquera-Açu", "Pedro de Toledo", "Registro", "Ribeira", "Sete Barras", "Tapiraí",
)

TERRITORIOS = {
    "muniz-freire": {"nome": "Muniz Freire (ES)", "uf": "ES", "municipios": ("Muniz Freire",),
                     "papel": "Caso de validação: o Tribunal de Contas do ES mediu a estrada de uma escola daqui."},
    "df": {"nome": "Distrito Federal", "uf": "DF", "municipios": None,
           "papel": "Escolas do campo da capital do país, a minutos e a horas do Plano Piloto."},
    "vale-do-ribeira": {"nome": "Vale do Ribeira (SP)", "uf": "SP", "municipios": VALE_DO_RIBEIRA,
                        "papel": "A região mais pobre do estado mais rico, com quilombos e aldeias."},
}


def escolas_do_territorio(chave: str) -> list[int]:
    """Escolas públicas ativas do campo: rurais, ou em terra indígena ou comunidade quilombola."""
    t = TERRITORIOS[chave]
    r = censo.retrato()
    sel = r[(r["uf"] == t["uf"]) & (r["situacao"] == 1)]
    if t["municipios"]:
        sel = sel[sel["municipio"].isin(t["municipios"])]
    campo = (sel["localizacao"] == 2) | sel["localizacao_diferenciada"].isin([2, 3])
    return sorted(int(c) for c in sel[campo].index)


def preparar_malhas(codigos: list[int]) -> None:
    """Baixa, por célula de grade (0,25°, ~28 km), uma malha que cobre as escolas da célula e suas candidatas.

    Uma área por município falharia no DF (um "município" só, do tamanho de uma metrópole); uma por
    escola faria centenas de chamadas. A célula é o meio-termo, e cada escola cabe na malha da sua célula.
    """
    r = censo.retrato()
    grupos: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for c in codigos:
        e = receptoras.escola(c)
        if e.lat is None:
            continue
        etapas = [v for v in ETAPAS.values() if r.loc[c, v] > 0] or list(ETAPAS.values())
        perto = receptoras.pre_filtrar(e, etapas, 12)
        celula = (math.floor(e.lat / CELULA), math.floor(e.lon / CELULA))
        grupos.setdefault(celula, []).extend([(e.lat, e.lon)] + list(zip(perto["lat"], perto["lon"])))
    for celula, pontos in sorted(grupos.items()):
        bbox = grafo.bbox_ao_redor(pontos)
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        print(f"  malha {celula}: bbox {bbox} ({area:.2f} grau²)", file=sys.stderr)
        grafo.arquivo_da_malha(*bbox)
        time.sleep(2)  # gentileza com o servidor público


def _ambiente() -> Environment:
    return Environment(loader=FileSystemLoader(ficha.TEMPLATES), autoescape=select_autoescape(["html", "j2"]))


def gerar(chaves: list[str] | None = None, destino: Path = SITE) -> dict:
    chaves = chaves or list(TERRITORIOS)
    (destino / "escola").mkdir(parents=True, exist_ok=True)
    hoje = date.today()
    indice, falhas = [], []
    for chave in chaves:
        codigos = escolas_do_territorio(chave)
        print(f"{TERRITORIOS[chave]['nome']}: {len(codigos)} escolas", file=sys.stderr)
        preparar_malhas(codigos)
        for i, c in enumerate(codigos, 1):
            try:
                d = diagnosticar(c)
                (destino / "escola" / f"{c}.html").write_text(ficha.renderizar(d, hoje))
                m = ficha._manchete(d)
                indice.append({
                    "c": c, "n": ficha.nome_legivel(d.escola.nome), "m": d.escola.municipio, "uf": d.escola.uf,
                    "t": chave, "a": d.matricula_total,
                    "km": round(m.km_ida_volta_piso) if m else None,
                    "r": bool(m and m.rural),
                })
            except Exception as e:  # uma escola com problema não derruba o site; fica registrada
                falhas.append({"codigo": c, "erro": f"{type(e).__name__}: {e}"})
                traceback.print_exc(file=sys.stderr)
            if i % 20 == 0:
                print(f"  {i}/{len(codigos)}", file=sys.stderr)
    (destino / "escolas.json").write_text(json.dumps(indice, ensure_ascii=False, separators=(",", ":")))
    contagem = {k: sum(1 for x in indice if x["t"] == k) for k in chaves}
    html = _ambiente().get_template("index.html.j2").render(
        css=(ficha.TEMPLATES / "ficha.css").read_text(), territorios=TERRITORIOS, contagem=contagem,
        total=len(indice), hoje=ficha.data_pt(hoje), validacao=_validacao_html(),
    )
    (destino / "index.html").write_text(html)
    (destino / ".nojekyll").write_text("")  # GitHub Pages: servir os arquivos como estão
    (destino / "falhas.json").write_text(json.dumps(falhas, ensure_ascii=False, indent=1))
    print(f"site: {len(indice)} fichas, {len(falhas)} falhas -> {destino}", file=sys.stderr)
    return {"fichas": len(indice), "falhas": falhas}


def _validacao_html() -> list[dict]:
    """Linhas da tabela de validação (Muniz Freire), se ela já tiver rodado."""
    arq = censo.PROCESSADOS / "validacao_muniz_freire.csv"
    if not arq.exists():
        return []
    import pandas as pd
    df = pd.read_csv(arq)
    return [{"nome": ficha.nome_legivel(x.receptora), "reta": f"{x.linha_reta_km:.0f}", "osrm": f"{x.osrm_km:.0f}",
             "nossa": f"{x.nossa_km:.0f}", "erro": f"{x.nossa_erro_rel:+.0%}".replace("-", "−")}
            for x in df.itertuples()]


if __name__ == "__main__":
    gerar(sys.argv[1:] or None)
