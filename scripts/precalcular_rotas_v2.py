"""Segunda passada do pré-cálculo de rotas: 10 receptoras por escola, com o TRAÇADO e a capacidade.

POR QUE UMA SEGUNDA PASSADA
A camada 2 (web, sem servidor) terá um simulador "e se estas escolas fecharem?" rodando no navegador e
um mapa com o traçado da rota. A primeira passada (precalcular_rotas.py) guarda até 4 receptoras por
escola e nenhum traçado: 35.677 das 35.917 escolas com rota batem no teto de 4, e uma cascata de
fechamentos no cliente esgota essa lista cedo. Esta passada grava, por escola:
  - até K_V2 receptoras com rota (o pré-filtro em linha reta sobe na mesma proporção da primeira
    passada: lá eram 12 candidatas para 6 receptoras, aqui PRE_FILTRO_V2 para K_V2);
  - o traçado da IDA de cada rota, simplificado e codificado (escola_em_pauta.tracado), com os trechos
    de chão marcados;
  - a capacidade da receptora pelo Censo: matrícula total e salas utilizadas.

O QUE NÃO MUDA
O índice data/escolas_campo.json.gz, o assistente e o contrato data/regressao_web.json não leem nada
daqui. A saída vai para uma pasta própria, dados/processados/rotas_v2/<UF>.jsonl (fora do git), com a
MESMA mecânica da primeira passada (precalcular_rotas.rodar_uf): planejamento por células de 0,25 grau,
uma passada no PBF por lote de células, cache das malhas em dados/processados/osm_celulas/, uma linha
por escola gravada com fsync, retomada de onde parou. Os km/min/chão de cada receptora saem do MESMO
Dijkstra (rota.pisos), então batem com os da primeira passada quando o grafo é o mesmo
(tests/test_tracado.py confere). O grafo pode ser um pouco MAIOR aqui (a área inclui as 20 candidatas,
não 12), e num grafo maior a rota só pode ficar igual ou mais curta.

Por que não chamar diagnosticar()? Ele monta a ficha inteira (série, tendência, checklist) e, para cada
candidata, relê a série do Censo (receptoras.escola). Aqui só interessam as rotas: nome, município e UF
da receptora saem da mesma linha do retrato do Censo que o pré-filtro já trouxe.

PARÂMETROS DE UMA PASTA
Ficam em <dir>/meta.json, gravado na primeira execução. Rodar de novo na mesma pasta com outros K,
pré-filtro ou tolerância é recusado: uma pasta com linhas de parâmetros diferentes não teria leitura honesta.

USO (de dentro do repo). O lote nacional vai num tmux, com teto de memória (o systemd mata o processo
acima de 6 GB, em vez de a VM entrar em swap; a retomada continua de onde parou):
  export XDG_RUNTIME_DIR=/run/user/$(id -u)
  systemd-run --user --scope -p MemoryMax=6G -p MemorySwapMax=0 \
      nice -n 19 .venv/bin/python scripts/precalcular_rotas_v2.py rodar 2>&1 | tee -a dados/processados/rotas_v2/rodar.log
  .venv/bin/python scripts/precalcular_rotas_v2.py rodar --codigos lista.txt --dir dados/processados/rotas_v2_amostra
  .venv/bin/python scripts/precalcular_rotas_v2.py status [--dir ...]
"""

from __future__ import annotations

import argparse
import json
import resource
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import precalcular_rotas as pr  # noqa: E402  (mesma pasta; também põe src/ no caminho)

RAIZ = pr.RAIZ
DIR_V2 = RAIZ / "dados" / "processados" / "rotas_v2"
ESQUEMA_V2 = 2
# Medido na amostra de 05/11/2026 (723 escolas: DF, Vale do Ribeira, 150 do PA, 150 da BA, Monte Santo/BA,
# Bragança/PA): 678 de 699 escolas com rota chegam a 10. Fechando TODAS as rurais de um município, sobra
# receptora aberta entre as 10 em 20/20 (Eldorado/SP), 78/79 (DF), 46/58 (Monte Santo) e 63/98 (Bragança):
# no caso extremo de município rural denso, 10 não bastam (ver o relatório da amostra).
K_V2 = 10            # receptoras com rota por escola
PRE_FILTRO_V2 = 20   # candidatas em linha reta: 2 por receptora, como na primeira passada (12 para 6)


def parametros() -> dict:
    from escola_em_pauta import tracado
    return {"esquema": ESQUEMA_V2, "k": K_V2, "pre_filtro": PRE_FILTRO_V2,
            "tolerancia_m": tracado.TOLERANCIA_M, "precisao": tracado.PRECISAO}


CAMPOS_V2 = {
    "v": "versão do formato (2 = segunda passada, com traçado)",
    "receptoras": f"até {K_V2} escolas com rota na malha, da mais perto à mais longe por estrada",
    "receptoras[].c/n/rural/km/min/chao/etapas/m/uf": "os mesmos campos (e valores) da primeira passada",
    "receptoras[].mat": "matrícula total da receptora no Censo (capacidade: quantos alunos já tem)",
    "receptoras[].salas": "salas utilizadas da receptora no Censo, ou null se não informado/zero",
    "receptoras[].p": "traçado da IDA (escola -> receptora), simplificado, em polyline do Google, precisão 5",
    "receptoras[].pc": "trechos de chão no traçado: pares de índices [i, j, ...] de pontos do traçado",
    "todas": "true quando a lista considerou TODAS as candidatas a até 60 km em linha reta (o pré-filtro "
             "não cortou ninguém): se a cascata esgotar, é falta de escola, não de cálculo",
    "sem_rota": "quantas das candidatas consideradas ficaram sem rota na malha",
    "motivo": "sem lista porque a escola não tem coordenada, matrícula ou candidata (o detalhe está no índice)",
    "osm": "data da malha do OpenStreetMap (Geofabrik)",
}


def receptoras_v2(codigo: int, g, k: int = K_V2, pre_filtro: int = PRE_FILTRO_V2, tol_m: float | None = None) -> dict:
    """O resumo de rota da segunda passada para uma escola, com o grafo `g` (da célula) já pronto."""
    import pandas as pd

    from escola_em_pauta import censo, receptoras, rota, tracado

    tol_m = tracado.TOLERANCIA_M if tol_m is None else tol_m
    info, _ = censo.escola_e_serie(codigo)
    origem = receptoras.escola(codigo)
    etapas = list(info["matriculas_por_etapa"])
    saida: dict = {"v": ESQUEMA_V2, "receptoras": []}
    if origem.lat is None:
        return {**saida, "motivo": "sem_coordenada"}
    if not etapas:
        return {**saida, "motivo": "sem_matricula"}
    perto = receptoras.pre_filtrar(origem, etapas, pre_filtro)
    if perto.empty:
        return {**saida, "motivo": "sem_candidata", "todas": True}
    if g is None:
        raise RuntimeError("escola com candidatas mas sem malha planejada")  # nunca extrair fora do lote
    o = (origem.lat, origem.lon)
    destinos = list(zip(perto["lat"], perto["lon"]))
    rotas = rota.pisos(g, o, destinos, tracados=True)
    itens = []
    for (cod, x), rt, d in zip(perto.iterrows(), rotas, destinos):
        if rt.km_ida_volta is None:
            continue
        salas = x["salas_utilizadas"]
        r = {"c": int(cod), "n": str(x["nome"]), "rural": int(x["localizacao"]) == 2,
             "km": round(float(rt.km_ida_volta), 1), "min": round(float(rt.minutos_ida_volta)),
             "chao": round(float(rt.km_chao_ida_volta or 0.0), 1),
             "etapas": [str(e) for e in etapas if x[e] > 0]}
        if (str(x["municipio"]), str(x["uf"])) != (origem.municipio, origem.uf):
            r["m"] = str(x["municipio"])
        if str(x["uf"]) != origem.uf:
            r["uf"] = str(x["uf"])
        r["mat"] = 0 if pd.isna(x["matricula_total"]) else int(x["matricula_total"])
        r["salas"] = None if pd.isna(salas) or salas == 0 else int(salas)
        r.update(tracado.tracar(g, rt.nos_ida, o, (float(d[0]), float(d[1])), tol_m))
        # mesma ordem de receptoras.candidatas: por km de estrada (as sem rota já ficaram de fora)
        itens.append((float(rt.km_ida_volta), r))
    itens.sort(key=lambda t: t[0])  # sort estável: empates mantêm a ordem do pré-filtro, como lá
    saida["receptoras"] = [r for _, r in itens[:k]]
    sem = len(perto) - len(itens)
    if sem:
        saida["sem_rota"] = sem
    if len(perto) < pre_filtro:
        saida["todas"] = True
    if g.data_osm:
        saida["osm"] = str(g.data_osm)[:10]
    return saida


def processar_escola_v2(codigo: int, uf: str, g=None) -> dict:
    """Linha do arquivo de progresso. NUNCA levanta exceção comum (uma escola não derruba o lote)."""
    t0 = time.perf_counter()
    try:
        return {"c": codigo, "uf": uf, "rota": receptoras_v2(codigo, g), "s": round(time.perf_counter() - t0, 3)}
    except Exception as e:  # noqa: BLE001
        return {"c": codigo, "uf": uf, "erro": f"{type(e).__name__}: {e}"[:300], "s": round(time.perf_counter() - t0, 3)}


def area_v2(codigo: int):
    return pr.area_da_escola(codigo, PRE_FILTRO_V2)


def conferir_meta(dir_v2: Path) -> None:
    """Grava os parâmetros na primeira execução; recusa misturar parâmetros na mesma pasta."""
    arq = dir_v2 / "meta.json"
    atual = parametros()
    if arq.exists():
        antigo = json.loads(arq.read_text())
        antigo.pop("campos", None)
        if antigo != atual:
            raise SystemExit(f"{arq}: parâmetros {antigo} diferentes dos atuais {atual}; use outra --dir")
    else:
        dir_v2.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({**atual, "campos": CAMPOS_V2}, ensure_ascii=False, indent=1))


def _pico_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux: ru_maxrss em KB


def cmd_rodar(a) -> None:
    doc = pr.carregar_indice()
    dir_v2 = Path(a.dir)
    conferir_meta(dir_v2)
    escolhidas = None
    if a.codigos:
        escolhidas = {int(x) for x in Path(a.codigos).read_text().split() if x.strip()}
    total: Counter = Counter()
    t0 = time.perf_counter()
    for uf in pr.ufs_em_ordem(doc, a.ufs):
        codigos = sorted(e["c"] for e in doc["escolas"] if e["uf"] == uf and e["geo"]
                         and (escolhidas is None or e["c"] in escolhidas))
        if not codigos:
            continue
        t_uf = time.perf_counter()
        cont = pr.rodar_uf(uf, codigos, dir_v2 / f"{uf}.jsonl", a.celulas_por_lote, processar=processar_escola_v2,
                           refazer_erros=a.refazer_erros, area=area_v2)
        total += cont
        feitas = cont["ok"] + cont["erro"]
        pr._log(f"{uf}: {feitas} escolas em {time.perf_counter() - t_uf:.0f} s de relógio "
                f"({(time.perf_counter() - t_uf) / max(feitas, 1):.2f} s/escola com extração) | pico de RAM "
                f"do processo até aqui: {_pico_mb():.0f} MB")
    pr._log(f"fim: {dict(total)} em {time.perf_counter() - t0:.0f} s | pico de RAM {_pico_mb():.0f} MB")


def cmd_status(a) -> None:
    import gzip
    linhas = pr.ler_todas(Path(a.dir))
    por_uf: dict[str, Counter] = {}
    dist: Counter = Counter()
    for x in linhas.values():
        c = por_uf.setdefault(x["uf"], Counter())
        c["escolas"] += 1
        c["s"] += x.get("s", 0)
        if "erro" in x:
            c["erro"] += 1
            continue
        n = len(x["rota"]["receptoras"])
        dist[n] += 1
        c["com_rota" if n else "sem_rota"] += 1
        c[f"k{K_V2}"] += n >= K_V2
        cru = json.dumps(x["rota"], ensure_ascii=False, separators=(",", ":")).encode()
        c["bytes"] += len(cru)
    for uf, c in sorted(por_uf.items()):
        n, s, b = c.pop("escolas"), c.pop("s"), c.pop("bytes")
        print(f"{uf}: {n} escolas, {s / n:.2f} s/escola, {b / n:,.0f} B/escola cru | "
              + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))
    print("receptoras com rota por escola:", dict(sorted(dist.items())))
    tudo = b"\n".join(json.dumps(x.get("rota"), ensure_ascii=False, separators=(",", ":")).encode()
                      for x in linhas.values())
    if linhas:
        print(f"total: {len(tudo) / len(linhas):,.0f} B/escola cru, {len(gzip.compress(tudo)) / len(linhas):,.0f} B/escola gzip")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rodar", help="calcula (retomável)")
    r.add_argument("--ufs", nargs="+", help="só estas UFs (padrão: todas, SE -> S -> CO -> NE -> N)")
    r.add_argument("--codigos", help="arquivo com códigos INEP (um por linha): só estas escolas")
    r.add_argument("--celulas-por-lote", type=int, default=pr.CELULAS_POR_LOTE)
    r.add_argument("--refazer-erros", action="store_true")
    for s in (r, sub.add_parser("status", help="resumo do progresso")):
        s.add_argument("--dir", default=str(DIR_V2), help="diretório dos .jsonl de progresso")
    a = p.parse_args(argv)
    {"rodar": cmd_rodar, "status": cmd_status}[a.cmd](a)


if __name__ == "__main__":
    main()
