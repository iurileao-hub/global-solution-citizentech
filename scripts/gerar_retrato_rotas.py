"""Gera data/retrato_rotas.json: se a escola do campo fechar, quão longe fica a escola que receberia os alunos.

É o retrato agregado (Brasil, região, UF e recorte por localização diferenciada) do pré-cálculo de rotas
(scripts/precalcular_rotas.py). Lê só o índice nacional já fundido (data/escolas_campo.json.gz, campo "rota"),
então roda em segundos e com a biblioteca padrão. Alimenta a tabela do README, o vídeo e o painel da camada 1.

Qual receptora conta (o MESMO critério da frase de abertura da ficha, ficha._manchete):
  a mais próxima por estrada que recebe TODAS as etapas da escola; se nenhuma das listadas recebe todas,
  a mais próxima, e a escola entra em "nenhuma_recebe_todas" (a família pode precisar de mais de uma escola).
  O índice guarda até 4 receptoras por escola (MAX_RECEPTORAS), então "nenhuma recebe todas" quer dizer
  "nenhuma das 4 mais próximas com rota".

Com --rotas-v2 (pasta da segunda passada, scripts/precalcular_rotas_v2.py), a lista de cada escola vem de lá:
até 10 receptoras em vez de 4. Isso muda o número, e não é ruído: medido no ES em 05/11, "nenhuma recebe
todas" cai de 141 para 53 escolas e a mediana sobe de 12,1 para 13,5 km. Com 4, quando nenhuma recebia todas
as etapas, a conta caía na mais próxima PARCIAL, que é mais perto do que a escola que de fato receberia a
criança. Sem a segunda passada inteira, o retrato recusa misturar as duas (uma UF com 10, outra com 4).

Leitura dos números: km e minutos são de IDA E VOLTA por dia, de escola a escola, e são PISO. A casa de cada
criança, as paradas do ônibus e a estrada na chuva deixam o trajeto real maior. Em AM, PA e AP parte do
transporte é fluvial e a rota por estrada pode não ser o caminho real (campo "aviso_fluvial").
Mediana e 9º decil, não média: a distribuição tem cauda longa (poucas escolas a mais de 100 km puxariam a média).

Uso:  python scripts/gerar_retrato_rotas.py [--indice data/escolas_campo.json.gz] [--saida data/retrato_rotas.json]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from escola_em_pauta.osm_local import REGIAO_POR_UF  # noqa: E402
from precalcular_rotas import INDICE, ORDEM_REGIOES, UFS_FLUVIAIS  # noqa: E402

SAIDA = RAIZ / "data" / "retrato_rotas.json"
# Faixas de ida e volta por dia. Limites inclusivos à esquerda: 10 km cai em "10_a_30".
FAIXAS_KM = ((10, "ate_10"), (30, "10_a_30"), (50, "30_a_50"), (100, "50_a_100"), (None, "100_ou_mais"))
FAIXAS_MIN = ((30, "ate_30"), (60, "30_a_60"), (120, "60_a_120"), (None, "120_ou_mais"))
POVOS = ("indígena", "quilombola", "assentamento", "comunidade tradicional")


def principal(e: dict) -> tuple[dict | None, bool]:
    """(receptora que conta, recebe todas as etapas?). (None, False) se a escola não tem rota."""
    rs = [r for r in ((e.get("rota") or {}).get("receptoras") or []) if r.get("km") is not None]
    if not rs:
        return None, False
    todas = [r for r in rs if set(r.get("etapas") or ()) >= set(e.get("e") or {})]
    return min(todas or rs, key=lambda r: r["km"]), bool(todas)


def faixa(valor: float, faixas: tuple) -> str:
    for limite, nome in faixas:
        if limite is None or valor < limite:
            return nome
    raise AssertionError("a última faixa não tem limite")


def quantil(ordenados: list[float], q: float) -> float | None:
    """Quantil por posição mais próxima (sem interpolação): o valor devolvido é de uma escola real."""
    if not ordenados:
        return None
    i = min(len(ordenados) - 1, max(0, round(q * (len(ordenados) - 1))))
    return ordenados[i]


class Bloco:
    """Acumula as escolas de um recorte (Brasil, região, UF ou povo) e resume no fim."""

    def __init__(self) -> None:
        self.escolas = 0
        self.alunos = 0
        self.sem_rota: Counter = Counter()      # motivo -> escolas sem receptora com rota
        self.km: list[float] = []
        self.minutos: list[float] = []
        self.frac_chao: list[float] = []
        self.faixa_km: Counter = Counter()
        self.faixa_km_alunos: Counter = Counter()
        self.faixa_min: Counter = Counter()
        self.faixa_min_alunos: Counter = Counter()
        self.extra: Counter = Counter()

    def add(self, e: dict) -> None:
        self.escolas += 1
        self.alunos += e.get("t") or 0
        r, todas = principal(e)
        if r is None:
            rota = e.get("rota")
            if rota is None:  # sem coordenada no Ipea o pré-cálculo nem tenta (05/11: 12.601 escolas, 23%)
                motivo = "sem_coordenada" if not e.get("geo") else "nao_calculada"
            else:
                motivo = rota.get("motivo", "sem_rota")
            self.sem_rota[motivo] += 1
            return
        t = e.get("t") or 0
        self.km.append(r["km"])
        self.minutos.append(r["min"])
        self.frac_chao.append((r.get("chao") or 0) / r["km"] if r["km"] else 0.0)
        fk, fm = faixa(r["km"], FAIXAS_KM), faixa(r["min"], FAIXAS_MIN)
        self.faixa_km[fk] += 1
        self.faixa_km_alunos[fk] += t
        self.faixa_min[fm] += 1
        self.faixa_min_alunos[fm] += t
        self.extra["alunos_com_rota"] += t
        self.extra["receptora_urbana"] += not r["rural"]
        self.extra["alunos_receptora_urbana"] += t if not r["rural"] else 0
        self.extra["outro_municipio"] += bool(r.get("m") or r.get("uf"))
        self.extra["nenhuma_recebe_todas"] += not todas
        self.extra["metade_ou_mais_em_chao"] += r["km"] > 0 and (r.get("chao") or 0) / r["km"] >= 0.5

    def resumo(self) -> dict:
        km, mi, ch = sorted(self.km), sorted(self.minutos), sorted(self.frac_chao)
        com = len(km)
        return {
            "escolas": self.escolas, "alunos": self.alunos, "com_rota": com,
            "alunos_com_rota": self.extra["alunos_com_rota"],
            "sem_rota": dict(sorted(self.sem_rota.items())),
            "km_ida_volta": {"mediana": quantil(km, 0.5), "p90": quantil(km, 0.9)},
            "min_ida_volta": {"mediana": quantil(mi, 0.5), "p90": quantil(mi, 0.9)},
            "fracao_chao_mediana": None if not ch else round(quantil(ch, 0.5), 2),
            "faixas_km": {n: {"escolas": self.faixa_km[n], "alunos": self.faixa_km_alunos[n]} for _, n in FAIXAS_KM},
            "faixas_min": {n: {"escolas": self.faixa_min[n], "alunos": self.faixa_min_alunos[n]} for _, n in FAIXAS_MIN},
            **{k: self.extra[k] for k in ("receptora_urbana", "alunos_receptora_urbana", "outro_municipio",
                                          "nenhuma_recebe_todas", "metade_ou_mais_em_chao")},
        }


def aplicar_v2(doc: dict, linhas: dict[int, dict]) -> dict:
    """Troca a rota de cada escola pela da segunda passada. Sem lista e sem motivo na v2 (a malha não ligou a
    escola), vale o motivo da primeira (origem_longe ou sem_rota), que a v2 não recalcula. Recusa mistura:
    toda escola com rota tentada na primeira passada precisa ter linha na segunda."""
    faltam = [e["c"] for e in doc["escolas"] if e.get("rota") is not None and e["c"] not in linhas]
    if faltam:
        raise SystemExit(f"segunda passada incompleta: {len(faltam)} escolas com rota na 1ª passada e sem linha "
                         f"na 2ª (ex.: {faltam[:3]}); use --ufs para um retrato só das UFs prontas")
    escolas = []
    for e in doc["escolas"]:
        x = linhas.get(e["c"])
        if x is not None:
            if "erro" in x:
                raise SystemExit(f"escola {e['c']} com erro na segunda passada: {x['erro']}")
            rota = dict(x["rota"])
            if not rota.get("receptoras") and not rota.get("motivo") and (e.get("rota") or {}).get("motivo"):
                rota["motivo"] = e["rota"]["motivo"]
            e = {**e, "rota": rota}
        escolas.append(e)
    return {**doc, "escolas": escolas}


def retrato(doc: dict, k: int = 4) -> dict:
    brasil, regiao, uf, povo = Bloco(), defaultdict(Bloco), defaultdict(Bloco), defaultdict(Bloco)
    datas_osm = set()
    for e in doc["escolas"]:
        brasil.add(e)
        if e.get("uf"):  # 1 escola do índice vem sem UF no Censo: conta no Brasil, não em UF nem região
            regiao[REGIAO_POR_UF[e["uf"]]].add(e)
            uf[e["uf"]].add(e)
        if e.get("d") in POVOS:
            povo[e["d"]].add(e)
        if (e.get("rota") or {}).get("osm"):
            datas_osm.add(e["rota"]["osm"])
    por_uf = {}
    for u, b in sorted(uf.items()):
        por_uf[u] = {"regiao": REGIAO_POR_UF.get(u), **b.resumo()}
        if u in UFS_FLUVIAIS:
            por_uf[u]["aviso_fluvial"] = True
    return {
        "esquema": 1,
        "fonte": doc.get("fonte"),
        "rotas": "pré-cálculo pela malha do OpenStreetMap (scripts/precalcular_rotas.py"
                 + (", segunda passada: precalcular_rotas_v2.py)" if k > 4 else ")"),
        "receptoras_por_escola": k,
        "data_osm": sorted(datas_osm),
        "criterio": ("receptora = a mais próxima por estrada que recebe todas as etapas da escola (senão, a mais "
                     f"próxima, contada em nenhuma_recebe_todas), entre até {k} receptoras com rota; km e minutos de "
                     "ida e volta por dia, de escola a escola, como piso; mediana e p90 por posição; faixas "
                     "inclusivas à esquerda"),
        "brasil": brasil.resumo(),
        "regiao": {r: regiao[r].resumo() for r in ORDEM_REGIOES if r in regiao},
        "uf": por_uf,
        "povos": {p: povo[p].resumo() for p in POVOS if p in povo},
    }


def _pct(n: int, d: int) -> str:
    return f"{100 * n / d:.0f}%" if d else "–"


def tabela(doc: dict) -> str:
    """Tabela em Markdown para o README (Brasil e regiões)."""
    linhas = ["| Recorte | Escolas com rota | Mediana (km / min) | 1 em 10 passa de | 50 km ou mais | Receptora urbana |",
              "|---|---|---|---|---|---|"]
    blocos = [("Brasil", doc["brasil"])] + [(r.capitalize(), b) for r, b in doc["regiao"].items()]
    for nome, b in blocos:
        if not b["com_rota"]:
            continue
        longe = b["faixas_km"]["50_a_100"]["escolas"] + b["faixas_km"]["100_ou_mais"]["escolas"]
        linhas.append(f"| {nome} | {b['com_rota']:,} de {b['escolas']:,} | {b['km_ida_volta']['mediana']:.0f} km / "
                      f"{b['min_ida_volta']['mediana']:.0f} min | {b['km_ida_volta']['p90']:.0f} km / "
                      f"{b['min_ida_volta']['p90']:.0f} min | {longe:,} ({_pct(longe, b['com_rota'])}) | "
                      f"{_pct(b['receptora_urbana'], b['com_rota'])} |".replace(",", "."))
    return "\n".join(linhas)


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--indice", type=Path, default=INDICE)
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--rotas-v2", type=Path, help="pasta da segunda passada (até 10 receptoras por escola)")
    p.add_argument("--ufs", nargs="+", help="só estas UFs (para comparar antes de a segunda passada terminar)")
    a = p.parse_args(argv)
    doc = json.loads(gzip.decompress(a.indice.read_bytes()))
    if a.ufs:
        doc = {**doc, "escolas": [e for e in doc["escolas"] if e.get("uf") in set(a.ufs)]}
    k = 4
    if a.rotas_v2:
        from precalcular_rotas import ler_todas
        k = json.loads((a.rotas_v2 / "meta.json").read_text())["k"]
        doc = aplicar_v2(doc, ler_todas(a.rotas_v2))
    doc = retrato(doc, k)
    a.saida.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    b = doc["brasil"]
    print(f"{a.saida.name}: {b['com_rota']} de {b['escolas']} escolas com rota | sem rota: {b['sem_rota']}")
    print(tabela(doc))


if __name__ == "__main__":
    main()
