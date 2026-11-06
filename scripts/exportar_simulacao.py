"""Gera data/regressao_simulacao.json: o que o simulador Python responde a uma lista fixa de planos.

É o CONTRATO do simulador da web (web/src/nucleo/simulacao.ts): para cada plano, o TypeScript tem de devolver
exatamente o mesmo resultado (alocações, faixas, cargas, escolas, avisos), campo por campo. Sem isso, a tela
poderia dizer outra coisa que o terminal.

Os planos cobrem os casos que já deram trabalho ou que o desenho exige:
  - Muniz Freire/ES (o caso de validação): a Durval sozinha, com indicação da prefeitura válida e inválida, e
    o município inteiro;
  - esgotamento das 10 receptoras (Monte Santo/BA e Bragança/PA fechando tudo);
  - área fluvial e escolas sem rota (Breves/PA, "< 30 alunos");
  - indicação de receptora que também fecha (procurada no dado);
  - planos sorteados (semente fixa) em municípios de todas as regiões, inteiros ou "< 30 alunos".

"insumos" guarda o hash de data/simulacao.json.gz: tests/test_simulacao.py falha se o contrato ficar velho.

Uso:  python scripts/exportar_simulacao.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from assistente import simulacao as sim  # noqa: E402

DADOS = RAIZ / "data"
ENTRADA = DADOS / "simulacao.json.gz"
SAIDA = DADOS / "regressao_simulacao.json"
DURVAL, ARQUIMIMO, ANA_BAZILIO = 32049501, 32050364, 32071175


def planos(doc: dict) -> list[dict]:
    lugar = lambda nome: sim.lugar_por_nome(doc, nome)  # noqa: E731
    muniz = lugar("Muniz Freire/ES")
    todas = lambda l: sorted(e["c"] for e in sim.municipio(doc, l)["escolas"])  # noqa: E731
    menos = lambda l, n: sim.menores_que(sim.municipio(doc, l), n)  # noqa: E731
    p = [
        {"id": "durval", "lugar": muniz, "fechar": [DURVAL], "indicacoes": {}},
        {"id": "durval-indicada", "lugar": muniz, "fechar": [DURVAL],
         "indicacoes": {f"{DURVAL}:pre_escola": ANA_BAZILIO, f"{DURVAL}:anos_iniciais": ARQUIMIMO}},
        {"id": "durval-indicada-invalida", "lugar": muniz, "fechar": [DURVAL],
         "indicacoes": {f"{DURVAL}:anos_finais": ANA_BAZILIO, f"{DURVAL}:pre_escola": 99999999}},
        {"id": "muniz-todas", "lugar": muniz, "fechar": todas(muniz), "indicacoes": {}},
        {"id": "muniz-vazio", "lugar": muniz, "fechar": [], "indicacoes": {}},
        {"id": "muniz-de-fora", "lugar": muniz, "fechar": [DURVAL, 53000001, 99999999], "indicacoes": {}},
        {"id": "monte-santo-todas", "lugar": lugar("Monte Santo/BA"), "fechar": todas(lugar("Monte Santo/BA")), "indicacoes": {}},
        {"id": "braganca-todas", "lugar": lugar("Bragança/PA"), "fechar": todas(lugar("Bragança/PA")), "indicacoes": {}},
        {"id": "breves-menos-30", "lugar": lugar("Breves/PA"), "fechar": menos(lugar("Breves/PA"), 30), "indicacoes": {}},
    ]
    # indicação que também fecha: a primeira escola (em ordem de código) com receptora do campo do próprio município
    for k in sorted(doc["municipios"], key=int):
        mun = sim.municipio(doc, int(k))
        cods = {e["c"] for e in mun["escolas"]}
        achou = next(((e, et, r[0]) for e in mun["escolas"] for et in e["e"] for r in e["r"]
                      if et in r[6] and r[0] in cods), None)
        if achou:
            e, et, rc = achou
            p.append({"id": "indicada-fecha", "lugar": int(k), "fechar": sorted({e["c"], rc}),
                      "indicacoes": {f"{e['c']}:{et}": rc}})
            break
    rnd = random.Random(2026)
    candidatos = sorted(int(k) for k, es in doc["municipios"].items() if len(es) >= 3)
    for i, l in enumerate(rnd.sample(candidatos, 40)):
        mun = sim.municipio(doc, l)
        cods = [e["c"] for e in mun["escolas"]]
        if i % 3 == 0:
            fechar = sorted(cods)
        elif i % 3 == 1:
            fechar = sim.menores_que(mun, 30) or sorted(cods[:1])
        else:
            fechar = sorted(rnd.sample(cods, rnd.randint(1, len(cods))))
        ind = {}
        if i % 4 == 0:  # indicações sorteadas: algumas válidas, algumas para escola que fecha
            for c in fechar[:3]:
                e = next(x for x in mun["escolas"] if x["c"] == c)
                for et in e["e"]:
                    ofer = [r[0] for r in e["r"] if et in r[6]]
                    if ofer:
                        ind[f"{c}:{et}"] = rnd.choice(ofer)
        p.append({"id": f"sorteio-{i:02d}-{mun['uf']}", "lugar": l, "fechar": fechar, "indicacoes": ind})
    return p


def gerar() -> dict:
    doc = sim.carregar(ENTRADA)
    casos = []
    for p in planos(doc):
        r = sim.simular(sim.municipio(doc, p["lugar"]), p["fechar"], p["indicacoes"])
        casos.append({**p, "resultado": r})
    return {"esquema": 1, "insumos": {ENTRADA.name: hashlib.sha256(ENTRADA.read_bytes()).hexdigest()},
            "casos": casos}


def main() -> int:
    c = gerar()
    SAIDA.write_text(json.dumps(c, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    n = sum(len(x["resultado"]["alocacoes"]) for x in c["casos"])
    print(f"{SAIDA.relative_to(RAIZ)}: {len(c['casos'])} planos, {n} alocações, {SAIDA.stat().st_size / 1e3:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
