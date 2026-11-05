"""Avaliação objetiva: perguntas de teste -> acerto, tempo e comparação dos dois modelos.

Classificação de cada pergunta (data/perguntas_teste.json):
  - "esperado": [ids]  -> ACERTO se o assistente respondeu (única ou por código) com um desses ids;
                          PARCIAL se mostrou opções empatadas e uma delas é esperada;
                          ERRO nos demais casos. (Mais de um id aceito = pergunta com mais de uma
                          resposta legítima, como "quem paga o ônibus?".)
  - "esperado_tipo"    -> ACERTO se o tipo da resposta é esse (ex.: "nenhuma" para pergunta fora do
                          tema; "escola_ambigua" para um nome repetido), e, se houver
                          "esperado_escola", se a escola certa apareceu.
Taxa de acerto = acertos / total (o parcial conta como erro na taxa principal e aparece à parte).

Tempo de consulta: cada pergunta é respondida REPETICOES vezes e guarda-se a mediana (uma medida
só é ruidosa: o sistema operacional pode interromper o programa no meio).
"""

from __future__ import annotations

import csv
import json
import re
import statistics
import time
from pathlib import Path

from . import escolas as escolas_mod
from .nucleo import Contexto, responder
from .respostas import RODAPE

REPETICOES = 30


def _tempo_ms(func, *args) -> float:
    medidas = []
    for _ in range(REPETICOES):
        t0 = time.perf_counter()
        func(*args)
        medidas.append((time.perf_counter() - t0) * 1000)
    return statistics.median(medidas)


def classificar(p: dict, r) -> str:
    if "esperado" in p:
        if r.tipo in ("unica", "codigo") and r.ids and r.ids[0] in p["esperado"]:
            return "acerto"
        if r.tipo == "ambigua" and set(r.ids) & set(p["esperado"]):
            return "parcial"
        return "erro"
    ok = r.tipo == p["esperado_tipo"]
    if ok and "esperado_escola" in p:
        ok = p["esperado_escola"] in r.escolas
    return "acerto" if ok else "erro"


def obtido(r) -> str:
    if r.ids:
        return f"{r.tipo}:{'/'.join(r.ids)}"
    if r.escolas:
        return f"{r.tipo}:{len(r.escolas)} escola(s)" if len(r.escolas) > 1 else f"{r.tipo}:{r.escolas[0]}"
    return r.tipo


def checar_formato(ctx: Contexto, r) -> dict:
    """O que cada modelo de resposta CUMPRE da sua especificação (verificável por programa)."""
    t = r.texto
    frases = [f for f in re.split(r"[.!?]\s", t) if f.strip()]
    reg = ctx.base.registros.get(r.ids[0]) if r.tipo in ("unica", "codigo") else None
    return {
        "cita_fonte": "Fonte:" in t,
        "data_verificacao": bool(re.search(r"\d{2}/\d{2}/\d{4}", t)),
        "aviso_nao_oficial": RODAPE in t,
        "pede_confirmacao": ("Confirme:" in t) if reg and reg.get("confirmar") else None,
        "oferece_continuidade": "Para continuar" in t or "Talvez também" in t,
        "linhas": t.count("\n") + 1,
        "palavras_por_frase": round(len(t.split()) / max(len(frases), 1), 1),
    }


def rodar(ctx: Contexto, perguntas: list[dict], modelo: str) -> list[dict]:
    linhas = []
    for p in perguntas:
        r = responder(ctx, p["pergunta"], modelo)
        esperado = "/".join(p["esperado"]) if "esperado" in p else p["esperado_tipo"] + (
            f":{p['esperado_escola']}" if "esperado_escola" in p else "")
        linhas.append({"id": p["id"], "tipo": p["tipo"], "pergunta": p["pergunta"], "esperado": esperado,
                       "obtido": obtido(r), "classificacao": classificar(p, r),
                       "tempo_ms": round(_tempo_ms(responder, ctx, p["pergunta"], modelo), 3),
                       **{f"fmt_{k}": v for k, v in checar_formato(ctx, r).items()}})
    return linhas


def indicadores(linhas: list[dict]) -> dict:
    n = len(linhas)
    c = {k: sum(1 for x in linhas if x["classificacao"] == k) for k in ("acerto", "parcial", "erro")}
    tempos = [x["tempo_ms"] for x in linhas]
    return {"perguntas": n, **c, "taxa_acerto": round(100 * c["acerto"] / n, 1),
            "tempo_medio_ms": round(statistics.mean(tempos), 3), "tempo_max_ms": round(max(tempos), 3)}


def comparar_buscas_escola(ctx: Contexto, consultas: list[str]) -> list[dict]:
    """Busca linear x índice invertido, nas mesmas consultas, conferindo que acham o MESMO conjunto."""
    todas = ctx.escolas.doc["escolas"]
    saida = []
    for q in consultas:
        lin = {e["c"] for e in escolas_mod.busca_linear(todas, q)}
        idx = {e["c"] for e in ctx.escolas.buscar(q)["escolas"]}
        saida.append({"consulta": q, "encontradas": len(idx), "mesmo_resultado": lin == idx,
                      "linear_ms": round(_tempo_ms(escolas_mod.busca_linear, todas, q), 3),
                      "indice_ms": round(_tempo_ms(ctx.escolas.buscar, q), 3)})
    return saida


def _csv(caminho: Path, linhas: list[dict]) -> None:
    with caminho.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def main(ctx: Contexto, raiz: Path) -> int:
    dados = raiz / "data"
    perguntas = json.loads((dados / "perguntas_teste.json").read_text(encoding="utf-8"))["perguntas"]
    resultado = {}
    for modelo in ("A", "B"):
        linhas = rodar(ctx, perguntas, modelo)
        _csv(dados / f"resultados_testes_modelo_{modelo}.csv", linhas)
        resultado[modelo] = {"indicadores": indicadores(linhas), "formato": {
            k[4:]: (sum(1 for x in linhas if x[k]) if k not in ("fmt_linhas", "fmt_palavras_por_frase")
                    else round(statistics.mean(x[k] for x in linhas), 1))
            for k in linhas[0] if k.startswith("fmt_")}}
        print(f"\nModelo {modelo}: {resultado[modelo]['indicadores']}")
        erradas = [x for x in linhas if x["classificacao"] != "acerto"]
        for x in erradas:
            print(f"  {x['classificacao'].upper():8} {x['id']}: esperado {x['esperado']}, obtido {x['obtido']}  ({x['pergunta']})")
        print(f"  formato: {resultado[modelo]['formato']}")
    if ctx.escolas:
        consultas = ["Durval Maximo", "Escola Municipal Sao Jose", "Santo Antonio", "Rui Barbosa", "Quilombo"]
        busca = comparar_buscas_escola(ctx, consultas)
        _csv(dados / "busca_escolas_linear_x_indice.csv", busca)
        resultado["busca_escolas"] = busca
        print("\nBusca de escolas (mediana de", REPETICOES, "repetições):")
        for b in busca:
            print(f"  {b['consulta']:28} {b['encontradas']:4} escolas | linear {b['linear_ms']:8.2f} ms | "
                  f"índice {b['indice_ms']:6.3f} ms | mesmo resultado: {b['mesmo_resultado']}")
    (dados / "indicadores.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados gravados em {dados}/")
    return 0
