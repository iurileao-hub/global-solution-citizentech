"""Números de fechamento de escolas rurais por lugar (data/fechamentos.json, gerado do Censo).

Acha o LUGAR citado na pergunta ("aqui em minas", "no pará", "em Muniz Freire") e monta um bloco de
texto com os números do lugar. Sem lugar, mostra o Brasil e pede o estado ou o município.

Cuidados achados no desenho e nos testes:
  - "Pará", sem acento, vira "para", a preposição mais comum da língua. Por isso o estado do Pará só é
    reconhecido depois de "no", "do", "em", "pro" ou "estado do".
  - "Rio Grande do Sul" CONTÉM "Rio Grande", que é município do RS (achado na 3ª rodada: a pergunta sobre
    o estado devolvia o município, sem aviso). O nome do estado é APAGADO do texto antes de procurar
    município; só "município de X" ou "cidade de X" fazem um nome de estado valer como município.
"""

from __future__ import annotations

import json
import re
import textwrap
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
# nome por extenso, com a preposição certa ("no Piauí", "em Goiás"): o teste leu "em RS" e "em PI"
NOME_UF = {
    "AC": "no Acre", "AL": "em Alagoas", "AP": "no Amapá", "AM": "no Amazonas", "BA": "na Bahia",
    "CE": "no Ceará", "DF": "no Distrito Federal", "ES": "no Espírito Santo", "GO": "em Goiás",
    "MA": "no Maranhão", "MT": "em Mato Grosso", "MS": "em Mato Grosso do Sul", "MG": "em Minas Gerais",
    "PA": "no Pará", "PB": "na Paraíba", "PR": "no Paraná", "PE": "em Pernambuco", "PI": "no Piauí",
    "RJ": "no Rio de Janeiro", "RN": "no Rio Grande do Norte", "RS": "no Rio Grande do Sul",
    "RO": "em Rondônia", "RR": "em Roraima", "SC": "em Santa Catarina", "SP": "em São Paulo",
    "SE": "em Sergipe", "TO": "no Tocantins",
}
PARA_DEPOIS_DE = ("no", "do", "em", "pro", "estado do")
UFS = {v.lower() for v in ESTADOS.values()} | {"pa"}
SIGLAS_AMBIGUAS = ("pa", "es", "se", "to")        # também são palavras comuns
EXPLICITO_MUNICIPIO = ("municipio de", "cidade de", "prefeitura de")
# palavras que pedem NÚMERO (com um lugar e "fechar" na pergunta, o assunto é a contagem, F5)
# ("quanto", "anos" e "número" ficaram de fora: "quanto tempo de ônibus", "meu filho de 5 anos" e "número
# mínimo de alunos" não pedem contagem)
PEDE_NUMERO = frozenset("quantas quantos dados estatistica estatisticas total aumentando "
                        "aumentou diminuindo diminuiu desde ritmo taxa".split())


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


def _estado(t: str) -> tuple[str | None, str]:
    """-> (UF citada ou None, texto com o nome do estado apagado)."""
    for nome, uf in sorted(ESTADOS.items(), key=lambda kv: -len(kv[0])):
        if f" {nome} " in t and not any(f" {pre} {nome} " in t for pre in EXPLICITO_MUNICIPIO):
            return uf, t.replace(f" {nome} ", " ")
    if any(f" {pre} para " in t for pre in PARA_DEPOIS_DE):
        return "PA", t
    sigla = next((p for p in t.split() if len(p) == 2 and p in UFS and p not in SIGLAS_AMBIGUAS), None)
    if sigla:
        return sigla.upper(), re.sub(rf" {sigla} ", " ", t)
    return None, t


ANTES_DE_LUGAR = ("em", "de", "do", "da", "no", "na", "pra", "para", "pro")


def _municipios(doc: dict, t: str) -> list[tuple[str, str]]:
    """Municípios citados no texto: [(nome normalizado, chave "Nome/UF")].

    O nome só conta como LUGAR com um sinal de lugar: preposição antes ("em Oeiras") ou a UF depois
    ("Oeiras PI"). Sem isso, palavra comum que também é município sumia da pergunta: "escola própria"
    (Propriá/SE) e "modelo de diagnóstico" (Modelo/SC), achado ao medir as correções da 3ª rodada."""
    achados = []
    for nome_norm, chaves in doc["_mun_norm"].items():
        if len(nome_norm) < 4 or f" {nome_norm} " not in t:
            continue
        preposto = any(f" {p} {nome_norm} " in t for p in ANTES_DE_LUGAR)
        achados += [(nome_norm, c) for c in chaves
                    if preposto or f" {nome_norm} {c.rsplit('/', 1)[1].lower()} " in t]
    return achados


def achar_lugar(doc: dict, pergunta: str) -> tuple[str, str] | None:
    """-> ("municipio", "Muniz Freire/ES") | ("uf", "MG") | None. O município mais longo citado vence."""
    estado, t = _estado(" " + normalizar(pergunta) + " ")
    achados = _municipios(doc, t)
    if achados:
        maior = max(len(n) for n, _ in achados)
        chaves = [c for n, c in achados if len(n) == maior]
        if estado:
            chaves = [c for c in chaves if c.endswith("/" + estado)] or chaves
        if len(chaves) == 1:
            return ("municipio", chaves[0])
    return ("uf", estado) if estado else None


def palavras_do_lugar(doc: dict, pergunta: str) -> set[str]:
    """Palavras que formam o nome do lugar citado. Elas dizem ONDE, não o ASSUNTO, e não devem contar como
    "palavra que a base não cobre" (na 3ª rodada, "Piauí" e "Mato Grosso do Sul" derrubavam a pergunta)."""
    t = " " + normalizar(pergunta) + " "
    nomes: set[str] = set()
    for nome in ESTADOS:
        if f" {nome} " in t:
            nomes.update(nome.split())
    estado, resto = _estado(t)
    if estado:
        nomes.add(estado.lower())
    for n, _ in _municipios(doc, resto):
        nomes.update(n.split())
    return nomes


CONTA_PESSOAS = frozenset("aluno alunos crianca criancas estudante estudantes professor professora professores "
                          "familia familias".split())


def pede_numero(pergunta: str) -> bool:
    """Pede contagem DE ESCOLAS. "Quantos alunos" pede outra coisa, que F5 não tem (ela conta escolas)."""
    p = set(normalizar(pergunta).split())
    return bool(PEDE_NUMERO & p) and not (CONTA_PESSOAS & p)


def nome_lugar(lugar: tuple[str, str] | None) -> str:
    if lugar is None:
        return "no Brasil"
    return NOME_UF[lugar[1]] if lugar[0] == "uf" else f"em {lugar[1]}"


def bloco(doc: dict, pergunta: str) -> str:
    lugar = achar_lugar(doc, pergunta)
    if lugar is None:
        n = doc["brasil"]
    elif lugar[0] == "uf":
        n = doc["uf"][lugar[1]]
    else:
        n = doc["municipio"][lugar[1]]
    par = n["paralisadas_2025"]
    paralisadas = (f"{_mil(par)}, das quais {_mil(n['paralisadas_5_anos_ou_mais'])} estão paralisadas há 5 anos "
                   "ou mais" if par else "nenhuma")
    serie = n.get("extintas_por_ano", {})
    anos = sorted(doc["brasil"]["extintas_por_ano"])
    linhas = [f"Escolas públicas rurais {nome_lugar(lugar)}, pelo Censo Escolar:",
              f"  - em atividade em 2025: {_mil(n['ativas_2025'])}",
              f"  - extintas (encerradas de vez) de {anos[0]} a {anos[-1]}: {_mil(n['extintas_2019_2025'])}",
              _quebra("    por ano: " + ", ".join(f"{a}: {_mil(serie.get(a, 0))}" for a in anos), "      "),
              _quebra(f"  - paralisadas em 2025 (sem aulas, mas sem extinção formal): {paralisadas}", "    ")]
    if n["extintas_2019_2025"] and max(serie.values(), default=0) >= 0.5 * n["extintas_2019_2025"] >= 10:
        ano_pico = max(serie, key=serie.get)
        linhas.append(_quebra(f"  Mais da metade das extinções caiu em {ano_pico}. Uma concentração assim pode ser "
                              "regularização (a rede registra de uma vez o fim de escolas que já estavam paradas); "
                              "a Secretaria de Educação sabe dizer.", "  "))
    if lugar is None:
        linhas.append(_quebra("Para ver o seu estado ou município, escreva o nome dele na pergunta "
                              "(por exemplo: \"quantas escolas fecharam em Minas Gerais?\")."))
    linhas.append(_quebra("Para citar: \"levantamento do projeto Escola em Pauta com os microdados do Censo "
                          "Escolar (INEP)\". O INEP publica os dados por escola; estes totais são contados pelo "
                          "projeto."))
    return "\n".join(linhas)


def _quebra(texto: str, recuo: str = "") -> str:
    return textwrap.fill(texto, 78, subsequent_indent=recuo, break_long_words=False, break_on_hyphens=False)


def _mil(n: int) -> str:
    return f"{n:,}".replace(",", ".")
