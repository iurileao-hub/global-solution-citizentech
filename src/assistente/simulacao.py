"""Simulador "e se estas escolas fecharem?": para onde iriam as crianças quando um PLANO fecha várias escolas.

Por que existe: a ficha mede uma escola fechando com todas as outras abertas. Fechamento real vem em plano
(93% das extinções de 2019 a 2025 caíram em município e ano com duas ou mais), e num plano a escola indicada
na ficha pode fechar também. O impacto do plano não é a soma das fichas.

Regra de destino (decisão de Iúri, 06/11/2026, depois do parecer do Fable):
  - por ETAPA, a mais próxima por estrada, entre as 10 receptoras pré-calculadas da escola, que oferece a etapa
    e não fecha no plano. Não há preferência pelo próprio município: ela mandaria 15,6% das crianças para mais
    longe do que o necessário e o número deixaria de ser piso. Receptora de outro município vem marcada;
  - a INDICAÇÃO da prefeitura (escola + etapa -> receptora) substitui a regra. É fato declarado por quem decide,
    não regra inventada. Se a indicada também fecha, ou não oferece a etapa, volta à regra, com aviso;
  - a origem é sempre a escola de origem da criança, nunca a receptora intermediária. Sem limite de vagas, a
    ordem dos fechamentos não muda nada: o cenário é um conjunto e cabe num link.

O que NÃO faz: realocar por capacidade (não há turnos nem vagas publicados; a carga só é sinalizada), fechar
escola de outro município ou escola urbana (os alunos delas não estão no índice) nem dizer quanto cada criança
anda a mais. A distância é da estrada entre a escola fechada e a receptora: é piso do caminho do ônibus que sai
da comunidade, não o acréscimo de cada criança (quem mora entre as duas escolas anda menos).

Os dados vêm de data/simulacao.json.gz (os mesmos de site/dados/simulacao/, gerados por
scripts/dividir_para_web.py). A versão web (web/src/nucleo/simulacao.ts) tem de devolver o mesmo resultado:
data/regressao_simulacao.json é o contrato. Só usa a biblioteca padrão.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Iterable

# Mesmas faixas do retrato nacional (scripts/gerar_retrato_rotas.py; um teste confere que não divergem).
# Valores de ida e volta: km por dia e minutos por dia.
FAIXAS_KM = ((10, "ate_10"), (30, "10_a_30"), (50, "30_a_50"), (100, "50_a_100"), (None, "100_ou_mais"))
FAIXAS_MIN = ((30, "ate_30"), (60, "30_a_60"), (120, "60_a_120"), (None, "120_ou_mais"))
# UFs em que a falta de rota por estrada é, na maior parte, transporte por rio (scripts/precalcular_rotas.py).
UFS_FLUVIAIS = frozenset({"AM", "PA", "AP"})
# Res. CNE/CEB 2/2008, art. 3º: pré-escola e anos iniciais na própria comunidade (o mesmo de checklist.py).
ETAPAS_NA_COMUNIDADE = ("pre_escola", "anos_iniciais")
ORDEM_ETAPAS = ("creche", "pre_escola", "anos_iniciais", "anos_finais", "medio")

# Por que uma etapa ficou sem destino. Os do pré-cálculo (escola inteira sem rota) vêm do arquivo; estes dois
# nascem aqui, quando o plano fecha as receptoras.
ESGOTADA = "lista_esgotada"          # todas as receptoras que oferecem a etapa fecham no plano
NENHUMA_OFERECE = "nenhuma_oferece"  # nenhuma das 10 oferece a etapa (com ou sem plano)

COLUNAS = ("c", "n", "rural", "km", "min", "chao", "etapas", "mat", "salas", "m", "uf")


def faixa(valor: float, faixas: tuple) -> str:
    for limite, nome in faixas:
        if limite is None or valor < limite:
            return nome
    raise AssertionError("a última faixa não tem limite")


def carregar(caminho: Path) -> dict:
    """data/simulacao.json.gz -> {"lugares": [[uf, município], ...], "municipios": {"lugar": [escolas]}, ...}."""
    doc = json.loads(gzip.decompress(caminho.read_bytes()))
    if tuple(doc["colunas_receptora"]) != COLUNAS:
        raise ValueError(f"colunas inesperadas em {caminho.name}: {doc['colunas_receptora']}")
    return doc


def municipio(doc: dict, lugar: int) -> dict:
    """O mesmo formato de site/dados/simulacao/LLLL.json."""
    uf, m = doc["lugares"][lugar]
    return {"lugar": lugar, "uf": uf, "municipio": m, "escolas": doc["municipios"].get(str(lugar), [])}


def _receptora(linha: list) -> dict:
    return dict(zip(COLUNAS, linha))


def _etapas(e: dict) -> list[str]:
    return [k for k in ORDEM_ETAPAS if e["e"].get(k)]


def principal_ficha(e: dict) -> int | None:
    """A receptora da manchete da ficha (regra b): a mais próxima que recebe TODAS as etapas; senão, a mais próxima.
    Igual a web/src/telas/ficha.ts:principal (a lista vem ordenada por km)."""
    rs = [_receptora(r) for r in e["r"]]
    precisa = set(e["e"])
    todas = [r for r in rs if precisa <= set(r["etapas"])]
    lista = todas or rs
    return lista[0]["c"] if lista else None


def _destino(e: dict, etapa: str, fechadas: frozenset[int], indicada: int | None) -> tuple[dict | None, str | None, str | None]:
    """(receptora, motivo se não há destino, aviso sobre a indicação)."""
    rs = [_receptora(r) for r in e["r"]]
    if not rs:
        return None, e.get("motivo") or "nao_calculada", None
    aviso = None
    if indicada is not None:
        r = next((r for r in rs if r["c"] == indicada), None)
        if r is None or etapa not in r["etapas"]:
            aviso = "indicada_invalida"
        elif r["c"] in fechadas:
            aviso = "indicada_fecha"
        else:
            return r, None, None
    oferecem = [r for r in rs if etapa in r["etapas"]]
    if not oferecem:
        return None, NENHUMA_OFERECE, aviso
    abertas = [r for r in oferecem if r["c"] not in fechadas]
    if not abertas:
        return None, ESGOTADA, aviso
    return abertas[0], None, aviso


def _alocar(escolas: dict[int, dict], fechadas: frozenset[int], indicacoes: dict[str, int]) -> list[dict]:
    aloc = []
    for c in sorted(fechadas):
        e = escolas[c]
        for etapa in _etapas(e):
            ind = indicacoes.get(f"{c}:{etapa}")
            r, motivo, aviso = _destino(e, etapa, fechadas, ind)
            aloc.append({
                "origem": c, "etapa": etapa, "n": e["e"][etapa],
                "destino": r["c"] if r else None,
                "km": r["km"] if r else None, "min": r["min"] if r else None, "chao": r["chao"] if r else None,
                "outro_municipio": bool(r and (r["m"] is not None or r["uf"] is not None)),
                "indicada": bool(r and ind is not None and aviso is None),
                "aviso": aviso, "motivo": motivo,
            })
    return aloc


def _acolheria(escolas: dict[int, dict], fechadas: frozenset[int], ind: dict[str, int]) -> dict[int, int]:
    """Quantas crianças de OUTRAS escolas do plano teriam cada escola fechada como destino se só ela ficasse aberta.

    Definição: rodar o plano sem a escola s e contar quem vai para s. Em vez de refazer o plano para cada s (custo
    que cresce com o quadrado do tamanho do plano: 160 ms em Santarém, 317 escolas), uma passada só: para cada
    criança, toda escola FECHADA que aparece na lista antes da primeira aberta que oferece a etapa seria o destino
    se reabrisse sozinha; a indicada pela prefeitura, se é válida e fecha, também. Indicada válida e aberta: a
    criança vai para ela em qualquer cenário, ninguém ganha. O teste confere contra a definição."""
    ganha: dict[int, int] = {}
    for o in fechadas:
        e = escolas[o]
        rs = [_receptora(r) for r in e["r"]]
        for etapa in _etapas(e):
            candidatas: set[int] = set()
            x = ind.get(f"{o}:{etapa}")
            r = next((r for r in rs if r["c"] == x), None) if x is not None else None
            if r is not None and etapa in r["etapas"]:
                if r["c"] not in fechadas:
                    continue
                candidatas.add(r["c"])
            for r in rs:
                if etapa not in r["etapas"]:
                    continue
                if r["c"] not in fechadas:
                    break
                candidatas.add(r["c"])
            for c in candidatas - {o}:
                ganha[c] = ganha.get(c, 0) + e["e"][etapa]
    return ganha


def simular(mun: dict, fechar: Iterable[int], indicacoes: dict[str, int] | None = None) -> dict:
    """O diagnóstico do plano. `fechar`: códigos INEP (os que não são escola do campo do município são devolvidos
    em "ignoradas"); `indicacoes`: {"código:etapa": código da receptora indicada pela prefeitura}."""
    escolas = {e["c"]: e for e in mun["escolas"]}
    pedidas = set(fechar)
    fechadas = frozenset(c for c in pedidas if c in escolas)
    ind = {k: v for k, v in (indicacoes or {}).items() if int(k.split(":")[0]) in fechadas}
    aloc = _alocar(escolas, fechadas, ind)

    sem: dict[str, int] = {}
    fk = {nome: 0 for _, nome in FAIXAS_KM}
    fm = {nome: 0 for _, nome in FAIXAS_MIN}
    metade_chao = outro = 0
    carga: dict[int, dict] = {}
    for a in aloc:
        if a["destino"] is None:
            sem[a["motivo"]] = sem.get(a["motivo"], 0) + a["n"]
            continue
        fk[faixa(a["km"], FAIXAS_KM)] += a["n"]
        fm[faixa(a["min"], FAIXAS_MIN)] += a["n"]
        metade_chao += a["n"] if a["km"] > 0 and (a["chao"] or 0) / a["km"] >= 0.5 else 0
        outro += a["n"] if a["outro_municipio"] else 0
        if a["destino"] not in carga:
            r = next(_receptora(x) for x in escolas[a["origem"]]["r"] if x[0] == a["destino"])
            carga[a["destino"]] = {"c": r["c"], "n": r["n"], "rural": r["rural"], "mat": r["mat"], "salas": r["salas"],
                                   "m": r["m"], "uf": r["uf"], "recebe": 0, "etapas": []}
        carga[a["destino"]]["recebe"] += a["n"]
        if a["etapa"] not in carga[a["destino"]]["etapas"]:
            carga[a["destino"]]["etapas"].append(a["etapa"])
    for r in carga.values():
        r["etapas"] = [k for k in ORDEM_ETAPAS if k in r["etapas"]]

    acolheria = _acolheria(escolas, fechadas, ind)
    resumo_escolas = []
    for c in sorted(fechadas):
        e = escolas[c]
        mesmas = [a for a in aloc if a["origem"] == c]
        p = principal_ficha(e)
        resumo_escolas.append({
            "c": c, "n": e["n"], "criancas": sum(e["e"].values()),
            "pre_iniciais": sum(e["e"].get(k, 0) for k in ETAPAS_NA_COMUNIDADE),
            "destinos": len({a["destino"] for a in mesmas if a["destino"] is not None}),
            "ficha": p, "ficha_fecha": p is not None and p in fechadas,
            "acolheria": acolheria.get(c, 0),
        })

    criancas = sum(a["n"] for a in aloc)
    return {
        "lugar": mun["lugar"], "uf": mun["uf"], "municipio": mun["municipio"],
        "fechadas": sorted(fechadas), "ignoradas": sorted(pedidas - fechadas),
        "criancas": criancas,
        "com_destino": criancas - sum(sem.values()),
        "sem_destino": dict(sorted(sem.items())),
        "fora_das_etapas": sum(max(0, escolas[c]["t"] - sum(escolas[c]["e"].values())) for c in fechadas),
        "faixas_km": fk, "faixas_min": fm, "metade_chao": metade_chao, "outro_municipio": outro,
        "ficha_fecha": sum(x["criancas"] for x in resumo_escolas if x["ficha_fecha"]),
        "aviso_fluvial": mun["uf"] in UFS_FLUVIAIS,
        "alocacoes": aloc,
        "receptoras": sorted(carga.values(), key=lambda r: (-r["recebe"], r["c"])),
        "escolas": resumo_escolas,
    }


def menores_que(mun: dict, alunos: int) -> list[int]:
    """O atalho "todas as escolas do município com menos de N alunos" (o total do Censo, todas as etapas)."""
    return sorted(e["c"] for e in mun["escolas"] if e["t"] < alunos)


# ---------- busca do município e texto do terminal ----------

def lugar_da_escola(doc: dict, codigo: int) -> int | None:
    for k, es in doc["municipios"].items():
        if any(e["c"] == codigo for e in es):
            return int(k)
    return None


def lugar_por_nome(doc: dict, texto: str) -> int | None:
    """ "Muniz Freire/ES" -> linha de lugares. Sem acento e sem caixa; a UF é obrigatória (há nomes repetidos)."""
    from .texto import normalizar
    if "/" not in texto:
        return None
    nome, uf = (x.strip() for x in texto.rsplit("/", 1))
    for i, (u, m) in enumerate(doc["lugares"]):
        if u.upper() == uf.upper() and normalizar(m) == normalizar(nome):
            return i
    return None


ROTULO_FAIXA_KM = {"ate_10": "até 10 km", "10_a_30": "de 10 a 30 km", "30_a_50": "de 30 a 50 km",
                   "50_a_100": "de 50 a 100 km", "100_ou_mais": "100 km ou mais"}
ROTULO_FAIXA_MIN = {"ate_30": "até 30 min", "30_a_60": "de 30 min a 1 h", "60_a_120": "de 1 h a 2 h",
                    "120_ou_mais": "2 h ou mais"}
MOTIVO = {
    "sem_coordenada": "a escola não tem coordenada pública (Catálogo de Escolas do INEP)",
    "origem_longe": "a escola fica longe da estrada mapeada no OpenStreetMap",
    "sem_rota": "não há rota por estrada na malha pública",
    "sem_candidata": "não há escola receptora num raio calculável",
    "sem_matricula": "sem alunos nas etapas que a busca usa",
    "nao_calculada": "rota não calculada",
    ESGOTADA: "todas as receptoras calculadas que oferecem a etapa também fecham neste plano",
    NENHUMA_OFERECE: "nenhuma das 10 receptoras calculadas oferece a etapa",
}


def _pct(x: float) -> str:
    """Como web/src/formato.ts:pct: inteiro a partir de 10% (meio para cima), uma casa abaixo disso ("3,1%")."""
    from decimal import ROUND_HALF_UP, Decimal
    import math
    v = x * 100
    if v >= 10 or v == 0:
        return f"{math.floor(v + 0.5)}%"   # Math.round
    # toFixed(1): arredonda o valor binário EXATO, meio para cima
    t = str(Decimal(v).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    return t.removesuffix(".0").replace(".", ",") + "%"


def texto(r: dict) -> str:
    """O diagnóstico do plano em texto corrido, para o terminal (a web monta o seu a partir do mesmo resultado)."""
    from .respostas import ETAPA, LARGURA, NAO_OFICIAL, _par, km_piso

    def mil(n: int) -> str:
        return f"{n:,}".replace(",", ".")

    def pl(n: int, um: str, varios: str) -> str:
        return f"{mil(n)} {um if n == 1 else varios}"

    nomes = {x["c"]: x["n"] for x in r["receptoras"]} | {x["c"]: x["n"] for x in r["escolas"]}
    linhas = [f"SIMULAÇÃO: e se estas escolas fecharem? {r['municipio']}/{r['uf']}", "=" * LARGURA]
    if not r["fechadas"]:
        return "\n".join(linhas + ["Nenhuma escola do campo deste município no plano."])
    linhas.append(_par(f"Plano: {pl(len(r['fechadas']), 'escola', 'escolas')}, "
                       f"{pl(r['criancas'], 'criança', 'crianças')} da creche ao ensino médio."))
    sem = sum(r["sem_destino"].values())
    if sem:
        linhas.append(_par(f"SEM DESTINO CALCULADO: {pl(sem, 'criança', 'crianças')}. Elas não entram nas contas abaixo:"))
        for m, n in sorted(r["sem_destino"].items(), key=lambda x: -x[1]):
            linhas.append(_par(f"{mil(n)}: {MOTIVO.get(m, m)}.", "  - ", "    "))
    if r["fora_das_etapas"]:
        linhas.append(_par(f"Outros {mil(r['fora_das_etapas'])} alunos (EJA, educação profissional...) não entram na conta."))
    if r["aviso_fluvial"]:
        linhas.append(_par("Parte do transporte escolar nesta UF é por rio: a rota por estrada pode não ser o caminho das crianças."))
    if r["ficha_fecha"]:
        linhas.append(_par(f"Para {pl(r['ficha_fecha'], 'criança', 'crianças')}, a escola indicada na ficha individual "
                           "também fecha neste plano: a ficha sozinha não serve para elas."))
    if r["com_destino"]:
        linhas.append("")
        linhas.append(_par("Estrada entre a escola fechada e a receptora, por dia, ida e volta (é PISO do caminho do "
                           "ônibus que sai da comunidade, não o quanto cada criança anda a mais):"))
        linhas.append("  Distância:")
        for k, n in r["faixas_km"].items():
            if n:
                linhas.append(f"    {ROTULO_FAIXA_KM[k]:<16} {pl(n, 'criança', 'crianças')}")
        linhas.append("  Tempo de ônibus:")
        for k, n in r["faixas_min"].items():
            if n:
                linhas.append(f"    {ROTULO_FAIXA_MIN[k]:<16} {pl(n, 'criança', 'crianças')}")
        if r["metade_chao"]:
            linhas.append(_par(f"{pl(r['metade_chao'], 'criança vai', 'crianças vão')} por estrada com metade ou mais de chão."))
        if r["outro_municipio"]:
            linhas.append(_par(f"{pl(r['outro_municipio'], 'criança vai', 'crianças vão')} para escola de OUTRO município "
                               "(a mais próxima que oferece a etapa; a prefeitura pode indicar outra)."))
    linhas.append("")
    linhas.append("Para onde vai cada etapa:")
    for a in r["alocacoes"]:
        o = nomes.get(a["origem"], a["origem"])
        if a["destino"] is None:
            d = f"sem destino ({MOTIVO.get(a['motivo'], a['motivo'])})"
        else:
            d = (f"{nomes.get(a['destino'], a['destino'])}, pelo menos {km_piso(a['km'])} km por dia"
                 + (", outro município" if a["outro_municipio"] else "") + (", indicada" if a["indicada"] else ""))
            if a["aviso"] == "indicada_fecha":
                d += " (a indicada também fecha)"
            elif a["aviso"] == "indicada_invalida":
                d += " (a indicada não oferece a etapa)"
        linhas.append(_par(f"{o}, {ETAPA[a['etapa']]}, {pl(a['n'], 'criança', 'crianças')}: {d}.", "  - ", "    "))
    if r["receptoras"]:
        linhas.append("")
        linhas.append("Quem recebe (a vaga real não é publicada; o aumento é sobre a matrícula de hoje):")
        for x in r["receptoras"]:
            pct = f", +{_pct(x['recebe'] / x['mat'])}" if x["mat"] else ""
            linhas.append(_par(f"{x['n']}: +{mil(x['recebe'])} alunos (tem {mil(x['mat'] or 0)}{pct}).", "  - ", "    "))
    if len(r["escolas"]) > 1:
        linhas.append("")
        linhas.append("Cada escola do plano:")
        for x in r["escolas"]:
            partes = [f"{x['n']}: " + (pl(x['criancas'], 'criança', 'crianças') if x["criancas"] else
                                       "sem alunos da creche ao ensino médio (só EJA ou outra modalidade)")]
            if x["pre_iniciais"]:
                partes.append(f"{mil(x['pre_iniciais'])} de pré-escola e anos iniciais, que a Res. CNE/CEB 2/2008, "
                              "art. 3º, pede que estudem na própria comunidade")
            if x["acolheria"]:
                partes.append(f"se ficar aberta, é a mais próxima para {pl(x['acolheria'], 'criança', 'crianças')} "
                              "de outras escolas do plano")
            if x["ficha_fecha"]:
                partes.append("a escola indicada na ficha dela também fecha")
            linhas.append(_par("; ".join(partes) + ".", "  - ", "    "))
    linhas.append("")
    linhas.append(_par("A regra: cada etapa vai para a escola mais próxima por estrada que a oferece. A ficha de cada "
                       "escola usa outra pergunta (a mais próxima que recebe TODAS as etapas), por isso os km podem diferir."))
    linhas.append(_par(NAO_OFICIAL))
    return "\n".join(linhas)
