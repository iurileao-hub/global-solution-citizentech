"""O fluxo de uma consulta, do texto digitado à resposta. Usado pelo menu E pela avaliação.

Ordem das regras (condicionais em sequência; a primeira que se aplica decide):
  1. entrada vazia (ou só palavras vazias)       -> pede para digitar algo
  2. código de orientação digitado ("D1", "t3")  -> resposta direta por identificador
  3. TODAS as palavras do texto estão no nome de alguma escola -> a pessoa está nomeando uma escola:
     se só UMA escola casa ("Durval Máximo"), ela vence sempre; se o nome se repete ("Escola Municipal
     São José"), vence só quando a orientação não cobre a pergunta inteira. A orientação vira sugestão.
  4. busca nas orientações:
       única    -> responde (+ sugestões)
       ambígua  -> lista as opções empatadas
  5. nada em lugar nenhum -> "sem base suficiente", com os temas disponíveis
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import respostas
from .base import Base
from .busca import IndiceOrientacoes
from .escolas import IndiceEscolas
from .texto import normalizar

MAX_ESCOLAS_LISTA = 8


@dataclass
class Contexto:
    base: Base
    indice: IndiceOrientacoes
    escolas: IndiceEscolas | None = None          # None = índice de escolas indisponível (degrada)


@dataclass
class Resposta:
    tipo: str            # vazia | codigo | unica | ambigua | escola | escola_ambigua | nenhuma
    texto: str
    ids: list[str] = field(default_factory=list)  # orientações mostradas (para a avaliação)
    escolas: list[int] = field(default_factory=list)
    parcial: bool = False  # respondeu avisando que parte da pergunta ficou sem cobertura


def montar(base: Base, doc_escolas: dict | None) -> Contexto:
    return Contexto(base, IndiceOrientacoes(base), IndiceEscolas(doc_escolas) if doc_escolas else None)


def responder(ctx: Contexto, texto: str, modelo: str = "B") -> Resposta:
    base = ctx.base
    bruto = normalizar(texto)
    if not bruto:
        return Resposta("vazia", respostas._par("Você não digitou nada. Escreva uma pergunta, um código como D1, "
                                                "ou o nome da escola."))

    codigo = bruto.replace(" ", "").upper()
    if codigo in base.registros:
        return Resposta("codigo", respostas.orientacao(base, codigo, modelo), [codigo])

    if bruto.isdigit() and not (ctx.escolas and int(bruto) in ctx.escolas.por_codigo):
        return Resposta("vazia", respostas._par(f"Não reconheci o número {bruto}. Digite um código como D1, o código "
                                                "INEP de uma escola, ou escreva sua pergunta. (No menu, as opções "
                                                "vão de 0 a 4.)"))

    r = ctx.indice.buscar(texto)
    achado = ctx.escolas.buscar(texto) if ctx.escolas else {"tipo": "nenhuma"}
    # Escola identificada sem dúvida (um só nome casa) vence sempre; nome repetido só vence se a orientação
    # não cobrir a pergunta inteira ("quilombo" sozinho: 10 escolas, mas é pergunta sobre D5).
    if achado["tipo"] in ("unica", "codigo") or (achado["tipo"] == "ambigua" and r.cobertura < 1.0):
        extras = r.ids if r.tipo == "unica" and modelo == "B" else []
        if achado["tipo"] == "ambigua":
            return lista_escolas(achado)
        resp = escola(ctx, achado["escolas"][0], modelo, extras)
        return resp
    if r.tipo == "vazia":
        return Resposta("vazia", respostas._par("Não entendi a pergunta: ela só tem palavras muito comuns. Tente com "
                                                "outras palavras."))
    if r.tipo == "unica":
        ja = set(base.registros[r.ids[0]].get("relacionados", [])[:3])
        extras = [x for x in r.sugestoes if x not in ja] if modelo == "B" else []
        return Resposta("unica", respostas.orientacao(base, r.ids[0], modelo, extras, r.fora), r.ids,
                        parcial=bool(r.fora))
    if r.tipo == "ambigua":
        return Resposta("ambigua", respostas.ambigua(base, r.ids), r.ids)

    return Resposta("nenhuma", respostas.sem_resposta(base))


def escola(ctx: Contexto, e: dict, modelo: str = "B", extras: list[str] | None = None) -> Resposta:
    doc = ctx.escolas.doc
    lig = set(ctx.base.ligacoes_escola.get("sempre", [])) | set(ctx.base.ligacoes_escola.get(e["d"] or "", []))
    extras = [x for x in (extras or []) if x not in lig]          # não repetir o que "Para continuar" já mostra
    return Resposta("escola", respostas.escola(ctx.base, e, doc["fonte"], doc["data_verificacao"], modelo, extras),
                    escolas=[e["c"]])


def lista_escolas(achado: dict, ja_filtrado: bool = False) -> Resposta:
    es = achado["escolas"]
    pedido = "" if ja_filtrado else ". Para escolher, informe o município e a UF"
    linhas = [respostas._par(f"Encontrei {achado['total']} escolas com essas palavras no nome{pedido}"
                             + (" (algumas delas):" if len(es) > MAX_ESCOLAS_LISTA else ":"))]
    linhas += [f"  {e['c']}  {e['n']}, {e['m']}/{e['uf']}" for e in es[:MAX_ESCOLAS_LISTA]]
    linhas.append("Ou digite o código INEP (o número da esquerda).")
    return Resposta("escola_ambigua", "\n".join(linhas), escolas=[e["c"] for e in es])
