"""Censo Escolar (INEP): matrícula, etapas, transporte, zona de residência e série histórica.

Fonte: microdados por escola, um zip por ano,
https://download.inep.gov.br/dados_abertos/microdados_censo_escolar_<ano>.zip
(2025 tem um sublinhado a mais no nome: ..._2025_.zip). O servidor tem
certificado SSL quebrado: baixar com verificação desligada é aceitável por ser
dado público. CSV com sep=";" e encoding latin1.

Harmonização entre anos (conferida nos cabeçalhos em 04/11/2026):
- 2019 a 2024: UMA tabela por escola (370 a 426 colunas), com tudo.
- 2025: o INEP dividiu em tabelas. A escola (situação, salas, infraestrutura)
  está em Tabela_Escola; as contagens de matrícula, em Tabela_Matricula.
  Juntamos as duas pelo código INEP (CO_ENTIDADE).
- QT_MAT_ZR_RUR/URB (onde o aluno mora) e QT_TRANSP_PUBLICO só existem a
  partir de 2023. Por isso a série histórica leva só matrícula por etapa, e o
  retrato do ano mais recente leva o resto.

Cuidado: TP_SITUACAO_FUNCIONAMENTO 2 = "paralisada" quer dizer escola JÁ
fechada (sem matrícula), e não escola "em risco".

Saídas em dados/processados/ (só escolas públicas, só colunas usadas):
- censo_serie.parquet   ano × escola, matrícula por etapa (2019-2025)
- censo_retrato.parquet uma linha por escola, ano mais recente
Gerar com: python -m escola_em_pauta.censo
"""

from __future__ import annotations

import zipfile
from functools import lru_cache
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
BRUTOS = RAIZ / "dados" / "brutos"
PROCESSADOS = RAIZ / "dados" / "processados"

ANOS = tuple(range(2019, 2026))
ANO_RETRATO = ANOS[-1]

# Rede pública: 1 federal, 2 estadual, 3 municipal (4 = privada, fica de fora).
DEPENDENCIAS_PUBLICAS = (1, 2, 3)

# Etapas na unidade da criança. Nomes curtos usados no resto do código.
ETAPAS = {
    "QT_MAT_INF_CRE": "creche",
    "QT_MAT_INF_PRE": "pre_escola",
    "QT_MAT_FUND_AI": "anos_iniciais",
    "QT_MAT_FUND_AF": "anos_finais",
    "QT_MAT_MED": "medio",
}

IDENTIFICACAO = {
    "CO_ENTIDADE": "codigo_inep",
    "NO_ENTIDADE": "nome",
    "CO_MUNICIPIO": "codigo_municipio",
    "NO_MUNICIPIO": "municipio",
    "SG_UF": "uf",
    "TP_DEPENDENCIA": "dependencia",
    "TP_LOCALIZACAO": "localizacao",  # 1 urbana, 2 rural
    "TP_LOCALIZACAO_DIFERENCIADA": "localizacao_diferenciada",
}

SITUACAO = {"TP_SITUACAO_FUNCIONAMENTO": "situacao"}  # 1 ativa, 2 paralisada, 3 extinta

MATRICULA = {"QT_MAT_BAS": "matricula_total", **ETAPAS}

SO_RETRATO = {
    "QT_MAT_ZR_RUR": "moram_zona_rural",
    "QT_MAT_ZR_URB": "moram_zona_urbana",
    "QT_TRANSP_PUBLICO": "usam_transporte_publico",
    "QT_SALAS_UTILIZADAS": "salas_utilizadas",
    "IN_AGUA_POTAVEL": "agua_potavel",
    "IN_ENERGIA_INEXISTENTE": "sem_energia",
    "IN_INTERNET": "internet",
}

# Códigos de TP_LOCALIZACAO_DIFERENCIADA (dicionário do INEP).
LOCALIZACAO_DIFERENCIADA = {
    1: "área de assentamento",
    2: "terra indígena",
    3: "comunidade quilombola",
    8: "área de povos e comunidades tradicionais",
}

ROTULO_SITUACAO = {1: "ativa", 2: "paralisada (já fechada)", 3: "extinta", 4: "extinta no ano anterior"}


def _zip_do_ano(ano: int, brutos: Path = BRUTOS) -> Path:
    return brutos / f"microdados_censo_escolar_{ano}.zip"


def _membro(zf: zipfile.ZipFile, padrao: str) -> str:
    """Acha o CSV dentro do zip pelo nome, sem depender da pasta (que muda a cada ano)."""
    candidatos = [n for n in zf.namelist() if Path(n).name.lower() == padrao.lower()]
    if len(candidatos) != 1:
        raise FileNotFoundError(f"{padrao} não encontrado (ou ambíguo) em {zf.filename}: {candidatos}")
    return candidatos[0]


def _ler_csv(zf: zipfile.ZipFile, membro: str, colunas: dict[str, str]) -> pd.DataFrame:
    """Lê só as colunas pedidas, que existirem no arquivo, e já renomeia."""
    with zf.open(membro) as f:
        cabecalho = f.readline().decode("latin1").strip().split(";")
    usar = [c for c in colunas if c in cabecalho]
    with zf.open(membro) as f:
        df = pd.read_csv(f, sep=";", encoding="latin1", usecols=usar, low_memory=False)
    return df.rename(columns=colunas)


def ler_ano(ano: int, colunas: dict[str, str], brutos: Path = BRUTOS) -> pd.DataFrame:
    """Uma linha por escola pública, com as colunas pedidas (as ausentes no ano não aparecem)."""
    with zipfile.ZipFile(_zip_do_ano(ano, brutos)) as zf:
        if ano <= 2024:
            df = _ler_csv(zf, _membro(zf, f"microdados_ed_basica_{ano}.csv"), colunas)
        else:
            # 2025 em diante: escola e matrícula em tabelas separadas.
            escola = _ler_csv(zf, _membro(zf, f"Tabela_Escola_{ano}_V2.csv"), colunas)
            so_matricula = {k: v for k, v in colunas.items() if v not in escola.columns or k == "CO_ENTIDADE"}
            mat = _ler_csv(zf, _membro(zf, f"Tabela_Matricula_{ano}_V2.csv"), so_matricula)
            df = escola.merge(mat, on="codigo_inep", how="left", validate="one_to_one")
            # Escola sem linha na tabela de matrícula = nenhuma matrícula naquele ano.
            contagens = [c for c in mat.columns if c != "codigo_inep"]
            df[contagens] = df[contagens].fillna(0)
    df = df[df["dependencia"].isin(DEPENDENCIAS_PUBLICAS)].copy()
    df.insert(0, "ano", ano)
    return df


def processar(brutos: Path = BRUTOS, processados: Path = PROCESSADOS) -> None:
    """Gera os dois arquivos leves a partir dos zips brutos (alguns minutos; ~1 GB de RAM no pico)."""
    processados.mkdir(parents=True, exist_ok=True)
    serie = []
    for ano in ANOS:
        cols = {"CO_ENTIDADE": "codigo_inep", "TP_DEPENDENCIA": "dependencia", **SITUACAO, **MATRICULA}
        df = ler_ano(ano, cols, brutos)
        serie.append(df.drop(columns="dependencia"))
        print(f"  {ano}: {len(df):,} escolas públicas")
    serie = pd.concat(serie, ignore_index=True)
    inteiros = [c for c in serie.columns if c not in ("ano", "codigo_inep")]
    serie[inteiros] = serie[inteiros].fillna(0).astype("int32")
    serie.to_parquet(processados / "censo_serie.parquet", index=False)

    retrato = ler_ano(ANO_RETRATO, {**IDENTIFICACAO, **SITUACAO, **MATRICULA, **SO_RETRATO}, brutos)
    # O merge de 2025 transforma contagens em float (por causa do NaN antes do fillna).
    # Int32 com maiúscula é o inteiro do pandas que aceita ausência (pd.NA).
    contagens = [v for v in {**MATRICULA, **SO_RETRATO}.values() if v in retrato.columns]
    retrato[contagens] = retrato[contagens].astype("Int32")
    retrato.to_parquet(processados / "censo_retrato.parquet", index=False)
    print(f"  série: {len(serie):,} linhas; retrato {ANO_RETRATO}: {len(retrato):,} escolas")


@lru_cache(maxsize=1)
def _serie() -> pd.DataFrame:
    return pd.read_parquet(PROCESSADOS / "censo_serie.parquet")


@lru_cache(maxsize=1)
def retrato() -> pd.DataFrame:
    """Uma linha por escola pública no ano mais recente, indexada pelo código INEP."""
    return pd.read_parquet(PROCESSADOS / "censo_retrato.parquet").set_index("codigo_inep", drop=False)


def _int(valor) -> int:
    return 0 if pd.isna(valor) else int(valor)


def escola_e_serie(codigo_inep: int) -> tuple[dict, dict[int, int]]:
    """Retrato da escola no ano mais recente + série de matrícula total por ano.

    Levanta KeyError se a escola não for pública ou não existir no ano mais recente.
    """
    r = retrato()
    if codigo_inep not in r.index:
        raise KeyError(f"Escola {codigo_inep} não encontrada entre as públicas do Censo {ANO_RETRATO}.")
    linha = r.loc[codigo_inep]
    dif = linha["localizacao_diferenciada"]
    info = {
        "codigo_inep": int(codigo_inep),
        "nome": str(linha["nome"]),
        "municipio": str(linha["municipio"]),
        "uf": str(linha["uf"]),
        "rural": _int(linha["localizacao"]) == 2,
        "localizacao_diferenciada": None if pd.isna(dif) or int(dif) == 0 else LOCALIZACAO_DIFERENCIADA.get(int(dif), f"código {int(dif)}"),
        "situacao": ROTULO_SITUACAO.get(_int(linha["situacao"]), "desconhecida"),
        "ano_referencia": ANO_RETRATO,
        "matriculas_por_etapa": {nome: _int(linha[nome]) for nome in ETAPAS.values() if _int(linha[nome]) > 0},
        "matricula_total": _int(linha["matricula_total"]),
        "moram_zona_rural": _int(linha["moram_zona_rural"]),
        "usam_transporte_publico": _int(linha["usam_transporte_publico"]),
        "salas_utilizadas": _int(linha["salas_utilizadas"]),
    }
    s = _serie()
    s = s[s["codigo_inep"] == codigo_inep].sort_values("ano")
    serie = {int(a): int(m) for a, m in zip(s["ano"], s["matricula_total"])}
    return info, serie


def etapas_do_ano(codigo_inep: int, ano: int) -> dict[str, int]:
    """Matrícula por etapa num ano qualquer da série (útil para conferir contra fontes externas)."""
    s = _serie()
    linha = s[(s["codigo_inep"] == codigo_inep) & (s["ano"] == ano)]
    if linha.empty:
        raise KeyError(f"Escola {codigo_inep} sem registro no Censo {ano}.")
    linha = linha.iloc[0]
    return {"matricula_total": int(linha["matricula_total"]), **{n: int(linha[n]) for n in ETAPAS.values()}}


if __name__ == "__main__":
    processar()
