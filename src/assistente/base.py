"""Carrega e VALIDA a base de orientações (data/base_orientacoes.json).

A base é dado, não código: acrescentar ou corrigir uma orientação é editar o JSON, sem tocar
nas regras do programa. Por isso a validação é rigorosa — um registro torto é recusado com uma
mensagem que diz QUAL registro e QUAL campo, em vez de virar uma resposta errada mais tarde.

Estrutura (hierarquia de dois níveis + grafo):
  temas      -> {id_tema: {"nome", "descricao", "subtemas": {id_subtema: nome}, "relacionados": [id_tema]}}
  registros  -> lista de orientações; cada uma pertence a um tema/subtema e aponta, em
                "relacionados", para outras orientações (as opções de "quer saber também?").
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

ESQUEMA_BASE = 1
CAMPOS_OBRIGATORIOS = ("id", "tema", "subtema", "pergunta", "palavras_chave", "orientacao",
                       "referencia", "data_verificacao")
DATA_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ErroBase(Exception):
    """Base ausente, vazia ou inconsistente. A mensagem é para uma pessoa ler."""


@dataclass
class Base:
    temas: dict[str, dict]
    registros: dict[str, dict]                      # id -> registro (busca por identificador: O(1))
    por_tema: dict[str, list[str]] = field(default_factory=dict)  # tema -> ids, na ordem do arquivo
    aviso_geral: str = ""
    # ligações da consulta de escola com as orientações: {"sempre": [ids], "indígena": [ids], ...}
    ligacoes_escola: dict[str, list[str]] = field(default_factory=dict)


def carregar(caminho: str | Path) -> Base:
    caminho = Path(caminho)
    if not caminho.exists():
        raise ErroBase(f"Arquivo da base não encontrado: {caminho}")
    bruto = caminho.read_text(encoding="utf-8").strip()
    if not bruto:
        raise ErroBase(f"O arquivo da base está vazio: {caminho}")
    try:
        doc = json.loads(bruto)
    except json.JSONDecodeError as e:
        raise ErroBase(f"O arquivo da base não é um JSON válido (linha {e.lineno}, coluna {e.colno}): {e.msg}") from None
    return validar(doc)


def validar(doc: dict) -> Base:
    erros: list[str] = []
    if not isinstance(doc, dict):
        raise ErroBase("A base deve ser um objeto JSON com 'temas' e 'registros'.")
    if doc.get("esquema") != ESQUEMA_BASE:
        erros.append(f"versão de esquema desconhecida: {doc.get('esquema')!r} (esperado {ESQUEMA_BASE})")
    temas = doc.get("temas")
    lista = doc.get("registros")
    if not isinstance(temas, dict) or not temas:
        erros.append("'temas' ausente ou vazio")
        temas = {}
    if not isinstance(lista, list) or not lista:
        raise ErroBase("; ".join(erros + ["'registros' ausente ou vazio"]))

    registros: dict[str, dict] = {}
    for i, r in enumerate(lista, start=1):
        onde = f"registro nº {i}" + (f" ({r.get('id')})" if isinstance(r, dict) and r.get("id") else "")
        if not isinstance(r, dict):
            erros.append(f"{onde}: não é um objeto")
            continue
        faltando = [c for c in CAMPOS_OBRIGATORIOS if not r.get(c)]
        if faltando:
            erros.append(f"{onde}: campo(s) obrigatório(s) ausente(s) ou vazio(s): {', '.join(faltando)}")
            continue
        if r["id"] in registros:
            erros.append(f"{onde}: id repetido")
        if r["tema"] not in temas:
            erros.append(f"{onde}: tema '{r['tema']}' não existe em 'temas'")
        elif r["subtema"] not in temas[r["tema"]].get("subtemas", {}):
            erros.append(f"{onde}: subtema '{r['subtema']}' não existe no tema '{r['tema']}'")
        if not isinstance(r["palavras_chave"], list):
            erros.append(f"{onde}: 'palavras_chave' deve ser uma lista")
        ref = r["referencia"]
        if not (isinstance(ref, dict) and ref.get("titulo") and str(ref.get("url", "")).startswith("http")):
            erros.append(f"{onde}: 'referencia' precisa de 'titulo' e de 'url' começando por http")
        if not DATA_ISO.match(str(r["data_verificacao"])):
            erros.append(f"{onde}: 'data_verificacao' deve estar no formato AAAA-MM-DD")
        registros[r["id"]] = r

    for r in registros.values():                      # o grafo não pode apontar para o vazio
        for alvo in r.get("relacionados", []):
            if alvo not in registros:
                erros.append(f"registro {r['id']}: relacionado '{alvo}' não existe")
    for t, info in temas.items():
        for alvo in info.get("relacionados", []):
            if alvo not in temas:
                erros.append(f"tema {t}: relacionado '{alvo}' não existe")

    ligacoes = doc.get("ligacoes_escola", {})
    for chave, alvos in ligacoes.items():
        for alvo in alvos:
            if alvo not in registros:
                erros.append(f"ligacoes_escola[{chave}]: registro '{alvo}' não existe")

    if erros:
        raise ErroBase("Base inconsistente:\n  - " + "\n  - ".join(erros))

    por_tema: dict[str, list[str]] = {t: [] for t in temas}
    for r in registros.values():
        por_tema[r["tema"]].append(r["id"])
    return Base(temas=temas, registros=registros, por_tema=por_tema, aviso_geral=doc.get("aviso_geral", ""),
                ligacoes_escola=ligacoes)
