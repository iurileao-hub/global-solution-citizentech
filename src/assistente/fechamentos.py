"""Números de fechamento de escolas rurais por lugar (data/fechamentos.json, gerado do Censo).

Acha o LUGAR citado na pergunta ("aqui em minas", "no pará", "em Muniz Freire") e monta um bloco de
texto com os números do lugar. Sem lugar, mostra o Brasil e pede o estado ou o município.

Cuidado achado no desenho: "Pará", sem acento, vira "para", a preposição mais comum da língua. Por isso
o estado do Pará só é reconhecido depois de "no", "do", "em", "pro" ou "estado do".
"""

from __future__ import annotations

import json
from pathlib import Path

from .texto import normalizar

ESTADOS = {
    "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM", "bahia": "BA", "ceara": "CE",
    "distrito federal": "DF", "espirito santo": "ES", "goias": "GO", "maranhao": "MA",
    "mato grosso do sul": "MS", "mato grosso": "MT", "minas gerais": "MG", "minas": "MG",
    "paraiba": "PB", "parana": "PR", "pernambuco": "PE", "piaui": "PI", "rio de janeiro": "RJ",
    "rio grande do norte": "RN", "rio grande do sul": "RS", "rondonia": "RO", "roraima": "RR",
    "santa catarina": "SC", "sao paulo": "SP", "sergipe": "SE", "tocantins": "TO",
}
PARA_DEPOIS_DE = ("no", "do", "em", "pro", "estado do")
UFS = {v.lower() for v in ESTADOS.values()} | {"pa"}


class ErroFechamentos(Exception):
    pass


def carregar(caminho: str | Path) -> dict:
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroFechamentos(f"Arquivo de fechamentos não encontrado: {caminho}")
    try:
        doc = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ErroFechamentos(f"Arquivo de fechamentos ilegível: {e.msg}") from None
    if doc.get("esquema") != 1 or not doc.get("uf"):
        raise ErroFechamentos("Arquivo de fechamentos vazio ou de versão desconhecida.")
    doc["_mun_norm"] = {}
    for chave in doc["municipio"]:
        nome, uf = chave.rsplit("/", 1)
        doc["_mun_norm"].setdefault(normalizar(nome), []).append(chave)
    return doc


def achar_lugar(doc: dict, pergunta: str) -> tuple[str, str] | None:
    """-> ("municipio", "Muniz Freire/ES") | ("uf", "MG") | None. O município mais longo citado vence."""
    t = " " + normalizar(pergunta) + " "
    palavras = t.split()
    uf_citada = next((p.upper() for p in palavras if len(p) == 2 and p in UFS and p not in ("pa", "es", "se", "to")), None)
    estado = None
    for nome, uf in sorted(ESTADOS.items(), key=lambda kv: -len(kv[0])):
        if f" {nome} " in t:
            estado = uf
            break
    if estado is None and any(f" {pre} para " in t for pre in PARA_DEPOIS_DE):
        estado = "PA"
    estado = estado or uf_citada
    achados = []
    for nome_norm, chaves in doc["_mun_norm"].items():
        if len(nome_norm) >= 4 and f" {nome_norm} " in t and normalizar(nome_norm) not in ESTADOS:
            achados += [(len(nome_norm), c) for c in chaves]
    if achados:
        maior = max(n for n, _ in achados)
        chaves = [c for n, c in achados if n == maior]
        if estado:
            chaves = [c for c in chaves if c.endswith("/" + estado)] or chaves
        if len(chaves) == 1:
            return ("municipio", chaves[0])
    return ("uf", estado) if estado else None


def bloco(doc: dict, pergunta: str) -> str:
    lugar = achar_lugar(doc, pergunta)
    if lugar is None:
        n, nome = doc["brasil"], "no Brasil"
    elif lugar[0] == "uf":
        n, nome = doc["uf"][lugar[1]], f"em {lugar[1]}"
    else:
        n, nome = doc["municipio"][lugar[1]], f"em {lugar[1]}"
    linhas = [f"Escolas públicas rurais {nome}, pelo Censo Escolar:",
              f"  - em atividade em 2025: {_mil(n['ativas_2025'])}",
              f"  - extintas (encerradas de vez) de 2019 a 2025: {_mil(n['extintas_2019_2025'])}",
              f"  - paralisadas em 2025 (sem aulas, mas sem extinção formal): {_mil(n['paralisadas_2025'])}, "
              f"das quais {_mil(n['paralisadas_5_anos_ou_mais'])} estão paralisadas há 5 anos ou mais"]
    if lugar is None:
        linhas.append("Para ver o seu estado ou município, escreva o nome dele na pergunta "
                      "(por exemplo: \"quantas escolas fecharam em Minas Gerais?\").")
    return "\n".join(linhas)


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")
