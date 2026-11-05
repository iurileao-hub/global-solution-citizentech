"""Gera data/escolas_campo.json.gz, o índice nacional que o assistente (camada 0) consulta.

Roda do NOSSO lado (precisa de pandas e dos dados processados em dados/). O arquivo gerado é
lido pelo assistente só com a biblioteca padrão (gzip + json), na máquina de qualquer pessoa.

Quem entra: escolas públicas ATIVAS no Censo mais recente, fora de unidade prisional ou
socioeducativa, que são
  - rurais (TP_LOCALIZACAO = 2), ou
  - urbanas em que mais da metade dos alunos mora na zona rural. O Decreto 7.352/2010
    (art. 1º, §1º, II) chama de escola do campo a urbana que atende predominantemente
    população do campo; morar na zona rural é o INDÍCIO que o Censo permite medir.

Campos curtos de propósito: são ~50 mil escolas, e cada byte se repete 50 mil vezes.
A legenda dos campos vai no próprio arquivo ("campos").

Uso:  python scripts/gerar_indice_escolas.py
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
PROC = RAIZ / "dados" / "processados"
SAIDA = RAIZ / "data" / "escolas_campo.json.gz"

ESQUEMA = 1
DIFERENCIADA = {1: "assentamento", 2: "indígena", 3: "quilombola", 8: "comunidade tradicional"}
REDE = {1: "federal", 2: "estadual", 3: "municipal"}
ETAPAS = ["creche", "pre_escola", "anos_iniciais", "anos_finais", "medio"]

CAMPOS = {
    "c": "código INEP", "n": "nome", "m": "município", "uf": "UF", "r": "rede",
    "z": "localização (rural | urbana-campo: urbana com mais da metade dos alunos morando na zona rural)",
    "d": "localização diferenciada (indígena, quilombola, assentamento, comunidade tradicional) ou null",
    "t": "matrícula total", "e": "matrícula por etapa", "zr": "alunos que moram na zona rural",
    "tp": "alunos que usam transporte escolar público", "s": "série da matrícula total {ano: alunos}",
    "geo": "tem coordenada na base do Ipea (sem ela não há rota)",
    "rota": "resumo das receptoras com rota calculada (preenchido pelo pré-cálculo) ou null",
}


def _int(v) -> int | None:
    return None if pd.isna(v) else int(v)


def _str(v) -> str | None:
    return None if pd.isna(v) else str(v)


def main() -> None:
    r = pd.read_parquet(PROC / "censo_retrato.parquet")
    s = pd.read_parquet(PROC / "censo_serie.parquet")
    geo = set(pd.read_parquet(PROC / "escolas_coord.parquet", columns=["codigo_inep", "lat"])
              .dropna()["codigo_inep"].astype(int))

    ano = int(r["ano"].max())
    base = r[(r["ano"] == ano) & (r["situacao"] == 1) & (r["em_prisional_socio"].fillna(0) == 0)]
    rural = base["localizacao"] == 2
    tot = base["matricula_total"].fillna(0)
    urbana_campo = (base["localizacao"] == 1) & (tot > 0) & (base["moram_zona_rural"].fillna(0) > tot / 2)
    sel = base[rural | urbana_campo].copy()
    sel["z"] = rural[rural | urbana_campo].map({True: "rural", False: "urbana-campo"})

    serie = (s[s["codigo_inep"].isin(sel["codigo_inep"])].dropna(subset=["matricula_total"])
             .sort_values("ano").groupby("codigo_inep")
             .apply(lambda g: {str(int(a)): int(m) for a, m in zip(g["ano"], g["matricula_total"])},
                    include_groups=False).to_dict())

    escolas = []
    for x in sel.itertuples(index=False):
        c = int(x.codigo_inep)
        escolas.append({
            "c": c, "n": _str(x.nome), "m": _str(x.municipio), "uf": _str(x.uf), "r": REDE.get(_int(x.dependencia)),
            "z": x.z, "d": DIFERENCIADA.get(_int(x.localizacao_diferenciada)),
            "t": _int(x.matricula_total),
            "e": {k: v for k in ETAPAS if (v := _int(getattr(x, k)))},
            "zr": _int(x.moram_zona_rural), "tp": _int(x.usam_transporte_publico),
            "s": serie.get(c, {}), "geo": c in geo, "rota": None,
        })
    escolas.sort(key=lambda e: e["c"])

    doc = {
        "esquema": ESQUEMA,
        "fonte": f"Censo Escolar {ano}, INEP (microdados por escola); coordenadas: Ipea/geobr, base 2023",
        "data_verificacao": "2026-11-04",
        "criterio": "escolas públicas ativas, rurais ou urbanas com mais da metade dos alunos morando na zona rural; "
                    "excluídas as de unidade prisional ou socioeducativa",
        "campos": CAMPOS,
        "escolas": escolas,
    }
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    bruto = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    SAIDA.write_bytes(gzip.compress(bruto, mtime=0))  # mtime=0: mesmo dado -> mesmo arquivo (git não vê mudança falsa)
    n_urb = int((sel["z"] == "urbana-campo").sum())
    print(f"{len(escolas)} escolas ({len(escolas) - n_urb} rurais, {n_urb} urbanas-campo) | "
          f"com coordenada: {sum(e['geo'] for e in escolas) / len(escolas):.0%} | "
          f"{len(bruto) / 1e6:.1f} MB -> {SAIDA.stat().st_size / 1e6:.1f} MB gzip")


if __name__ == "__main__":
    main()
