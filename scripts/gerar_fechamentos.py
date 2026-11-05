"""Gera data/fechamentos.json: quantas escolas públicas RURAIS pararam ou foram extintas, por UF e município.

Responde à pergunta mais feita no teste de usabilidade que a base não cobria ("quantas escolas do campo
já fecharam aqui?"). Roda do nosso lado (pandas + microdados do INEP em dados/brutos/); o assistente lê
o JSON pronto, só com a biblioteca padrão.

O que o Censo permite afirmar, e com que palavra (ver data/base_orientacoes.json, F4):
  - "extinta"   (TP_SITUACAO_FUNCIONAMENTO = 3): encerrada de vez NAQUELE ano, por ato da Secretaria.
                No arquivo do ano seguinte ela já não aparece; por isso as extinções de 2019 a 2025
                são contadas ano a ano, com a localização (rural/urbana) DO PRÓPRIO ano.
  - "paralisada" (= 2): atividades temporariamente suspensas, sem extinção formal. Paralisada por
                muitos anos seguidos é fechamento de fato sem o ato formal.
Escolas em unidade prisional ou socioeducativa ficam de fora (mesmo critério do resto do projeto).
Recorte por povo (pedido da 3ª rodada, persona guarani-kaiowá): por UF e no Brasil, os mesmos números só
das escolas em terra indígena e em comunidade quilombola (TP_LOCALIZACAO_DIFERENCIADA = 2 e 3).
CUIDADO medido: o Censo só preenche essa coluna para escola EM ATIVIDADE (paralisada e extinta vêm com 0 ou
vazio; 2019: 0 de 25.906 paralisadas marcadas). A primeira versão do recorte deu zero fechamento indígena
no Brasil inteiro. Por isso vale a localização do ÚLTIMO ANO EM QUE A ESCOLA FUNCIONOU; escola paralisada
desde antes de 2019 fica sem ela, e o recorte é um PISO ("pelo menos"), nunca o total.

Uso:  python scripts/gerar_fechamentos.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from escola_em_pauta import censo  # noqa: E402

ANOS = range(2019, 2026)
SAIDA = RAIZ / "data" / "fechamentos.json"
COLUNAS = {"CO_ENTIDADE": "codigo_inep", "NO_MUNICIPIO": "municipio", "SG_UF": "uf",
           "TP_DEPENDENCIA": "dependencia", "TP_LOCALIZACAO": "localizacao",
           "TP_SITUACAO_FUNCIONAMENTO": "situacao",
           "IN_LOCAL_FUNC_UNID_PRISIONAL": "em_prisional", "IN_LOCAL_FUNC_SOCIOEDUCATIVO": "em_socioeducativo",
           "IN_LOCAL_FUNC_PRISIONAL_SOCIO": "em_prisional_socio",
           "TP_LOCALIZACAO_DIFERENCIADA": "dif"}
GRUPOS = {2: "indigena", 3: "quilombola"}


def main() -> None:
    extintas = defaultdict(Counter)            # (uf, municipio) -> {ano: n extintas}
    situacao_por_escola: dict[int, dict[int, int]] = defaultdict(dict)
    ultimo: dict[int, tuple] = {}              # código -> (uf, município, situação, ano, grupo) no último ano visto
    extintas_grupo = defaultdict(Counter)      # (uf, grupo) -> {ano: n extintas}
    grupo_quando_ativa: dict[int, str | None] = {}   # código -> grupo informado no último ano em atividade
    for ano in ANOS:
        df = censo.ler_ano(ano, COLUNAS)
        df = df[(df["localizacao"] == 2) & censo.fora_de_privacao(df)].copy()
        sem_lugar = int(df["uf"].isna().sum())
        if sem_lugar:
            print(f"  {ano}: {sem_lugar} escola(s) rural(is) sem UF no Censo: fora da contagem por lugar")
        df = df.dropna(subset=["uf"])
        df["municipio"] = df["municipio"].fillna("(município não informado)")
        for x in df[["codigo_inep", "uf", "municipio", "situacao", "dif"]].itertuples(index=False):
            c, s = int(x.codigo_inep), int(x.situacao)
            if s == 1:                                                  # x == x: falso só para NaN
                grupo_quando_ativa[c] = GRUPOS.get(int(x.dif)) if x.dif == x.dif else None
            g = grupo_quando_ativa.get(c)
            situacao_por_escola[c][ano] = s
            ultimo[c] = (x.uf, x.municipio, s, ano, g)
            if s == 3:
                extintas[(x.uf, x.municipio)][ano] += 1
                if g:
                    extintas_grupo[(x.uf, g)][ano] += 1
        print(ano, len(df), "rurais;", int((df["situacao"] == 3).sum()), "extintas no ano")

    # retrato de 2025: ativas e paralisadas (com há quantos anos seguidos)
    lugares: dict[tuple, Counter] = defaultdict(Counter)
    grupos: dict[tuple, Counter] = defaultdict(Counter)     # (uf, grupo) -> contagens
    for c, (uf, mun, s, ano, g) in ultimo.items():
        if ano != 2025:
            continue
        alvos = [lugares[(uf, mun)]] + ([grupos[(uf, g)]] if g else [])
        if s == 1:
            for a in alvos:
                a["ativas_2025"] += 1
        elif s == 2:
            seguidos = 0
            for a in sorted(ANOS, reverse=True):
                if situacao_por_escola[c].get(a) != 2:
                    break
                seguidos += 1
            for a in alvos:
                a["paralisadas_2025"] += 1
                a["paralisadas_5_anos_ou_mais"] += seguidos >= 5
    for lugar, por_ano in extintas.items():
        lugares[lugar]["extintas_2019_2025"] += sum(por_ano.values())
    for chave, por_ano in extintas_grupo.items():
        grupos[chave]["extintas_2019_2025"] += sum(por_ano.values())

    def resumo(cont: Counter, por_ano: Counter | None = None) -> dict:
        d = {k: int(cont.get(k, 0)) for k in
             ("ativas_2025", "paralisadas_2025", "paralisadas_5_anos_ou_mais", "extintas_2019_2025")}
        if por_ano is not None:   # série das extinções (pedido do teste: "está aumentando?"), sem os anos zerados
            d["extintas_por_ano"] = {str(a): int(por_ano[a]) for a in ANOS if por_ano.get(a)}
        return d

    por_uf: dict[str, Counter] = defaultdict(Counter)
    for (uf, _), cont in lugares.items():
        por_uf[uf].update(cont)
    brasil = Counter()
    for cont in por_uf.values():
        brasil.update(cont)
    extintas_por_ano = Counter()
    extintas_uf: dict[str, Counter] = defaultdict(Counter)
    for (uf, _), por_ano in extintas.items():
        extintas_por_ano.update(por_ano)
        extintas_uf[uf].update(por_ano)

    def povos(uf: str | None) -> dict:
        saida = {}
        for g in GRUPOS.values():
            cont, ano = Counter(), Counter()
            for (u, gg), cc in grupos.items():
                if gg == g and (uf is None or u == uf):
                    cont.update(cc)
                    ano.update(extintas_grupo.get((u, g), Counter()))
            if sum(cont.values()):
                saida[g] = resumo(cont, ano)
        return saida

    doc = {
        "esquema": 1,
        "fonte": "Censo Escolar 2019 a 2025, INEP (microdados por escola)",
        "data_verificacao": "2026-11-04",
        "criterio": ("escolas públicas com localização rural no ano do Censo, fora de unidade prisional ou "
                     "socioeducativa; extinta = situação 3 no ano (contada uma vez, no ano da extinção); "
                     "paralisada = situação 2 em 2025 (atividades temporariamente suspensas, sem extinção formal); "
                     "povos = localização diferenciada no último ano em atividade desde 2019 (piso)"),
        "brasil": {**resumo(brasil, extintas_por_ano), "povos": povos(None)},
        "uf": {uf: {**resumo(c, extintas_uf[uf]), "povos": povos(uf)} for uf, c in sorted(por_uf.items())},
        "municipio": {f"{mun}/{uf}": resumo(c, extintas.get((uf, mun), Counter()))
                      for (uf, mun), c in sorted(lugares.items(), key=lambda kv: (kv[0][0], kv[0][1]))},
    }
    SAIDA.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Brasil:", doc["brasil"], "|", len(doc["municipio"]), "municípios |", f"{SAIDA.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
