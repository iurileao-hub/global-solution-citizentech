"""Tendência da matrícula de uma escola (série 2019-2025).

Responde à pergunta da comunidade: a "baixa demanda" alegada se sustenta?

Modelo: regressão linear simples (ano -> matrícula) por mínimos quadrados,
escrita à mão (são duas fórmulas) para ficar à vista o que o modelo faz.

Avaliação (backtest): ajustar só com 2019-2022 e prever 2023-2025, que o
modelo não viu; medir MAE (erro absoluto médio, em alunos) e RMSE (que pune
mais os erros grandes). Comparar com a LINHA DE BASE ingênua "o futuro repete
o último ano conhecido": se a reta não ganhar dela, a ficha mostra a série
sem prever nada.

Cuidado: escola pequena tem série ruidosa (uma família que se muda muda 10%).
Não extrapolar além de 2 anos.
"""

from __future__ import annotations

import math

ANO_CORTE = 2022  # último ano do treino no backtest
# Inclinação menor que 2% da média por ano = estável (~12% em 6 anos). Com 3%, uma queda de
# 71 para 57 alunos (−20%) saía como "estável" (Cananéia, 04/11): limiar baixado.
LIMIAR_ESTAVEL = 0.02


def ajustar_reta(anos: list[int], valores: list[float]) -> tuple[float, float]:
    """Mínimos quadrados: inclinação = cov(x, y) / var(x); intercepto = ȳ - inclinação·x̄."""
    n = len(anos)
    if n < 2:
        raise ValueError("São precisos ao menos 2 anos para ajustar uma reta.")
    mx, my = sum(anos) / n, sum(valores) / n
    var_x = sum((x - mx) ** 2 for x in anos)
    cov_xy = sum((x - mx) * (y - my) for x, y in zip(anos, valores))
    inclinacao = cov_xy / var_x
    return inclinacao, my - inclinacao * mx


def erros(reais: list[float], previstos: list[float]) -> tuple[float, float]:
    """MAE e RMSE."""
    d = [p - r for r, p in zip(reais, previstos)]
    return sum(abs(x) for x in d) / len(d), math.sqrt(sum(x * x for x in d) / len(d))


def backtest(serie: dict[int, int], corte: int = ANO_CORTE) -> dict | None:
    """Treina até `corte`, prevê os anos seguintes; devolve erros da reta e da linha de base."""
    treino = {a: v for a, v in serie.items() if a <= corte}
    teste = {a: v for a, v in serie.items() if a > corte}
    if len(treino) < 3 or not teste:
        return None
    b, a0 = ajustar_reta(list(treino), list(treino.values()))
    anos_t, reais = list(teste), list(teste.values())
    reta = [max(0.0, a0 + b * a) for a in anos_t]  # matrícula negativa não existe
    base = [float(treino[max(treino)])] * len(anos_t)
    mae_r, rmse_r = erros(reais, reta)
    mae_b, rmse_b = erros(reais, base)
    return {"mae_reta": mae_r, "rmse_reta": rmse_r, "mae_base": mae_b, "rmse_base": rmse_b,
            "previsto_reta": dict(zip(anos_t, reta)), "previsto_base": dict(zip(anos_t, base))}


def ajustar(serie: dict[int, int]) -> dict | None:
    """Tendência da série completa, com o backtest como medida de confiança."""
    serie = {a: v for a, v in sorted(serie.items()) if v is not None}
    if len(serie) < 3:
        return None
    anos, valores = list(serie), list(serie.values())
    b, a0 = ajustar_reta(anos, valores)
    media = sum(valores) / len(valores)
    rel = b / media if media else 0.0
    sentido = "estável" if abs(rel) < LIMIAR_ESTAVEL else ("queda" if b < 0 else "alta")
    bt = backtest(serie)
    return {
        "inclinacao_alunos_ano": b,
        "variacao_relativa_ano": rel,
        "sentido": sentido,
        "primeiro": (anos[0], valores[0]),
        "ultimo": (anos[-1], valores[-1]),
        "backtest": bt,
        # A reta só "vale" para a ficha se errar menos que repetir o último ano.
        "reta_supera_base": bool(bt and bt["mae_reta"] < bt["mae_base"]),
    }


def backtest_em_lote(series: dict[int, dict[int, int]]) -> dict:
    """MAE/RMSE agregados num território (a avaliação de desempenho do modelo para o relatório)."""
    mae_r, mae_b, rmse_r, rmse_b, n, vence = [], [], [], [], 0, 0
    for s in series.values():
        bt = backtest(s)
        if bt is None:
            continue
        n += 1
        mae_r.append(bt["mae_reta"]); mae_b.append(bt["mae_base"])
        rmse_r.append(bt["rmse_reta"]); rmse_b.append(bt["rmse_base"])
        vence += bt["mae_reta"] < bt["mae_base"]
    media = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
    return {"escolas": n, "mae_reta": media(mae_r), "mae_base": media(mae_b),
            "rmse_reta": media(rmse_r), "rmse_base": media(rmse_b),
            "reta_vence_em": vence / n if n else float("nan")}
