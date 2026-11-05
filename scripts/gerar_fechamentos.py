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
           "IN_LOCAL_FUNC_PRISIONAL_SOCIO": "em_prisional_socio"}


def main() -> None:
    extintas = defaultdict(Counter)            # (uf, municipio) -> {ano: n extintas}
    situacao_por_escola: dict[int, dict[int, int]] = defaultdict(dict)
    ultimo: dict[int, tuple] = {}              # código -> (uf, município, situação) no último ano visto
    for ano in ANOS:
        df = censo.ler_ano(ano, COLUNAS)
        df = df[(df["localizacao"] == 2) & censo.fora_de_privacao(df)].copy()
        sem_lugar = int(df["uf"].isna().sum())
        if sem_lugar:
            print(f"  {ano}: {sem_lugar} escola(s) rural(is) sem UF no Censo: fora da contagem por lugar")
        df = df.dropna(subset=["uf"])
        df["municipio"] = df["municipio"].fillna("(município não informado)")
        for x in df[["codigo_inep", "uf", "municipio", "situacao"]].itertuples(index=False):
            c, s = int(x.codigo_inep), int(x.situacao)
            situacao_por_escola[c][ano] = s
            ultimo[c] = (x.uf, x.municipio, s, ano)
            if s == 3:
                extintas[(x.uf, x.municipio)][ano] += 1
        print(ano, len(df), "rurais;", int((df["situacao"] == 3).sum()), "extintas no ano")

    # retrato de 2025: ativas e paralisadas (com há quantos anos seguidos)
    lugares: dict[tuple, Counter] = defaultdict(Counter)
    for c, (uf, mun, s, ano) in ultimo.items():
        if ano != 2025:
            continue
        if s == 1:
            lugares[(uf, mun)]["ativas_2025"] += 1
        elif s == 2:
            lugares[(uf, mun)]["paralisadas_2025"] += 1
            seguidos = 0
            for a in sorted(ANOS, reverse=True):
                if situacao_por_escola[c].get(a) != 2:
                    break
                seguidos += 1
            if seguidos >= 5:
                lugares[(uf, mun)]["paralisadas_5_anos_ou_mais"] += 1
    for lugar, por_ano in extintas.items():
        lugares[lugar]["extintas_2019_2025"] += sum(por_ano.values())

    def resumo(cont: Counter) -> dict:
        return {k: int(cont.get(k, 0)) for k in
                ("ativas_2025", "paralisadas_2025", "paralisadas_5_anos_ou_mais", "extintas_2019_2025")}

    por_uf: dict[str, Counter] = defaultdict(Counter)
    for (uf, _), cont in lugares.items():
        por_uf[uf].update(cont)
    brasil = Counter()
    for cont in por_uf.values():
        brasil.update(cont)
    extintas_por_ano = Counter()
    for por_ano in extintas.values():
        extintas_por_ano.update(por_ano)

    doc = {
        "esquema": 1,
        "fonte": "Censo Escolar 2019 a 2025, INEP (microdados por escola)",
        "data_verificacao": "2026-11-04",
        "criterio": ("escolas públicas com localização rural no ano do Censo, fora de unidade prisional ou "
                     "socioeducativa; extinta = situação 3 no ano (contada uma vez, no ano da extinção); "
                     "paralisada = situação 2 em 2025 (atividades temporariamente suspensas, sem extinção formal)"),
        "brasil": {**resumo(brasil), "extintas_por_ano": {str(a): int(extintas_por_ano[a]) for a in ANOS}},
        "uf": {uf: resumo(c) for uf, c in sorted(por_uf.items())},
        "municipio": {f"{mun}/{uf}": resumo(c) for (uf, mun), c in sorted(lugares.items(), key=lambda kv: (kv[0][0], kv[0][1]))},
    }
    SAIDA.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("Brasil:", doc["brasil"], "|", len(doc["municipio"]), "municípios |", f"{SAIDA.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
