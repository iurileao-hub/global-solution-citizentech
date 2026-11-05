"""Consulta ao índice nacional de escolas do campo (data/escolas_campo.json.gz).

Duas estratégias, de propósito, para MEDIR a diferença (o README traz os tempos):
  - busca_linear: percorre as ~54 mil escolas e testa se todos os termos estão no nome. O(n) por consulta.
  - IndiceEscolas.buscar: índice invertido termo -> conjunto de códigos; a resposta é a
    INTERSEÇÃO dos conjuntos dos termos digitados. Só toca as escolas que têm o termo mais raro.

Palavras genéricas de nome de escola ("escola", "municipal", "EMEF"...) são ignoradas: todo nome
tem, e elas não ajudam a achar nenhuma. Um nome pode se repetir muito ("Escola Municipal São José"
existe 77 vezes no campo): aí a resposta é "ambigua" e o assistente pede município e UF.

Aqui não se usa radical: nome próprio se compara inteiro ("Rui" não pode casar com "Ruiz").
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from .texto import normalizar

ESQUEMA_ESCOLAS = 1
# Conectivos de NOME PRÓPRIO. Não usar a lista de palavras vazias das perguntas: lá "sao" é o verbo
# "são" e seria descartado, e aqui é "São José" (bug achado no primeiro teste interativo).
CONECTIVOS = frozenset("de da do das dos e".split())
GENERICAS = frozenset("""
escola escolas municipal estadual federal emef emeif emei eef eeef eeefm eeem eem ee em ef ce cef cem ceef
colegio centro educacional ensino fundamental medio infantil basica rural unidade nucleo creche
pre integral tempo pm prof professor professora dr dona
""".split())
MAX_LISTA = 8


class ErroEscolas(Exception):
    pass


def palavras_nome(texto: str) -> list[str]:
    return [p for p in normalizar(texto).split() if p not in GENERICAS and p not in CONECTIVOS]


def carregar(caminho: str | Path) -> dict:
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroEscolas(f"Índice de escolas não encontrado: {caminho}")
    try:
        doc = json.loads(gzip.decompress(caminho.read_bytes()).decode("utf-8"))
    except (OSError, EOFError, json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ErroEscolas(f"Índice de escolas ilegível ({caminho.name}): {e}") from None
    if doc.get("esquema") != ESQUEMA_ESCOLAS or not doc.get("escolas"):
        raise ErroEscolas("Índice de escolas vazio ou de versão desconhecida.")
    return doc


def filtrar(escolas: list[dict], municipio: str = "", uf: str = "") -> list[dict]:
    """Desempate de nomes repetidos: por município (trecho do nome, sem acento) e/ou UF. Ordena por UF/município/nome."""
    m, u = normalizar(municipio), uf.strip().lower()
    saida = [e for e in escolas
             if (not m or m in normalizar(e["m"] or "")) and (not u or (e["uf"] or "").lower() == u)]
    return sorted(saida, key=lambda e: (e["uf"] or "", e["m"] or "", e["n"] or ""))


def busca_linear(escolas: list[dict], consulta: str) -> list[dict]:
    alvo = palavras_nome(consulta)
    if not alvo:
        return []
    return [e for e in escolas if set(alvo) <= set(normalizar(e["n"] or "").split())]


class IndiceEscolas:
    def __init__(self, doc: dict):
        self.doc = doc
        self.por_codigo = {e["c"]: e for e in doc["escolas"]}       # busca por identificador
        self.indice: dict[str, set[int]] = {}
        for e in doc["escolas"]:
            for p in set(normalizar(e["n"] or "").split()):
                self.indice.setdefault(p, set()).add(e["c"])

    def buscar(self, consulta: str, municipio: str = "", uf: str = "") -> dict:
        """-> {"tipo": "codigo"|"unica"|"ambigua"|"nenhuma"|"vazia", "escolas": [...], "total": n}"""
        bruto = normalizar(consulta)
        if not bruto:
            return {"tipo": "vazia", "escolas": [], "total": 0}
        if bruto.isdigit():
            e = self.por_codigo.get(int(bruto))
            return {"tipo": "codigo" if e else "nenhuma", "escolas": [e] if e else [], "total": int(bool(e))}
        alvo = palavras_nome(consulta)
        if not alvo:
            return {"tipo": "vazia", "escolas": [], "total": 0}
        conjuntos = sorted((self.indice.get(p, set()) for p in alvo), key=len)   # o menor primeiro
        codigos = set.intersection(*conjuntos) if conjuntos else set()
        achadas = filtrar([self.por_codigo[c] for c in codigos], municipio, uf)
        tipo = "nenhuma" if not achadas else "unica" if len(achadas) == 1 else "ambigua"
        return {"tipo": tipo, "escolas": achadas, "total": len(achadas)}
