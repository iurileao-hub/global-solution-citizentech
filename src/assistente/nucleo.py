"""O fluxo de uma consulta, do texto digitado à resposta. Usado pelo menu E pela avaliação.

Ordem das regras (condicionais em sequência; a primeira que se aplica decide):
  1. entrada vazia (ou só palavras vazias)       -> pede para digitar algo
  2. código de orientação digitado ("D1", "t3")  -> resposta direta por identificador
  3. TODAS as palavras do texto estão no nome de alguma escola -> a pessoa está nomeando uma escola:
     se só UMA escola casa ("Durval Máximo"), ela vence sempre; se o nome se repete ("Escola Municipal
     São José"), vence só quando a orientação não cobre a pergunta inteira. A orientação vira sugestão.
  4. busca nas orientações (as palavras do LUGAR citado não contam como assunto):
       única    -> responde (+ sugestões)
       ambígua  -> lista as opções empatadas
     com uma exceção: pergunta que fala de fechar E pede número ("quantas", "está aumentando?") vai para a
     orientação de números por lugar (F5), e as outras viram sugestão; com lugar citado, ela também
     desempata e substitui o "não sei"
  5. nada em lugar nenhum -> "sem base suficiente", com os temas disponíveis
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import fechamentos as fech_mod
from . import respostas
from .base import Base
from .busca import IndiceOrientacoes
from .escolas import IndiceEscolas
from .busca import Resultado
from .texto import codigo_falado, normalizar, termos

MAX_ESCOLAS_LISTA = 8


@dataclass
class Contexto:
    base: Base
    indice: IndiceOrientacoes
    escolas: IndiceEscolas | None = None          # None = índice de escolas indisponível (degrada)
    fechamentos: dict | None = None               # números de fechamento por lugar (F5); None = indisponível


@dataclass
class Resposta:
    tipo: str            # vazia | codigo | unica | ambigua | escola | escola_ambigua | nenhuma
    texto: str
    ids: list[str] = field(default_factory=list)  # orientações mostradas (para a avaliação)
    escolas: list[int] = field(default_factory=list)
    parcial: bool = False  # respondeu avisando que parte da pergunta ficou sem cobertura


def montar(base: Base, doc_escolas: dict | None, doc_fechamentos: dict | None = None) -> Contexto:
    return Contexto(base, IndiceOrientacoes(base), IndiceEscolas(doc_escolas) if doc_escolas else None,
                    doc_fechamentos)


def _lugar_desempata(ctx: Contexto, r, texto: str):
    """Pergunta que cita um lugar ("aqui em Minas", "em Muniz Freire") e empata com a orientação de números
    por lugar: ela responde, e as outras viram sugestão. Só ela sabe responder POR LUGAR."""
    if not ctx.fechamentos or r.tipo not in ("ambigua", "unica") or not r.pontuacoes:
        return r
    alvo = next((rid for rid in r.pontuacoes if ctx.base.registros[rid].get("dados") == "fechamentos"), None)
    topo = max(r.pontuacoes.values())
    if not alvo or r.pontuacoes[alvo] < topo - 1 or (r.tipo == "unica" and r.ids == [alvo]):
        return r
    if not fech_mod.achar_lugar(ctx.fechamentos, texto):
        return r
    outros = [x for x in sorted(r.pontuacoes, key=lambda x: -r.pontuacoes[x]) if x != alvo][:2]
    lugar = frozenset(fech_mod.palavras_do_lugar(ctx.fechamentos, texto))
    r.tipo, r.ids, r.sugestoes, r.fora = "unica", [alvo], outros, ctx.indice.fora_de(texto, alvo, lugar)
    return r


def _pede_fechamentos(ctx: Contexto, r, texto: str, lugar: frozenset[str] = frozenset()):
    """"quantas escolas fecharam no Piauí?", "está aumentando?": é pergunta de contagem, e só F5 conta."""
    if not ctx.fechamentos or "fecha" not in termos(texto):
        return r
    alvo = next((rid for rid, reg in ctx.base.registros.items() if reg.get("dados") == "fechamentos"), None)
    if not alvo or (r.tipo == "unica" and r.ids == [alvo]):
        return r
    com_lugar = fech_mod.achar_lugar(ctx.fechamentos, texto) is not None
    if not (fech_mod.pede_numero(texto) or (com_lugar and r.tipo == "nenhuma")):
        return r
    outros = [x for x in sorted(r.pontuacoes, key=lambda x: -r.pontuacoes[x]) if x != alvo][:2]
    # o que a contagem NÃO responde continua avisado ("quantos ALUNOS": F5 conta escolas, não alunos)
    return Resultado("unica", ids=[alvo], sugestoes=outros, pontuacoes=r.pontuacoes, cobertura=1.0,
                     fora=ctx.indice.fora_de(texto, alvo, lugar))


def _numeros(ctx: Contexto, rid: str, texto: str) -> str:
    """Bloco de dados do registro, quando ele pede ("dados": "fechamentos") e o arquivo existe."""
    if ctx.base.registros[rid].get("dados") == "fechamentos" and ctx.fechamentos:
        return fech_mod.bloco(ctx.fechamentos, texto)
    return ""


_CONTA_ALUNOS = re.compile(r"\bquant[oa]s (alunos|alunas|criancas|estudantes|matriculas|matriculados)\b")
MENSAGEM_ALUNOS = ("Para saber quantos alunos uma escola tem, escreva o nome dela ou o código INEP. Por exemplo: "
                   "Durval Máximo, ou 32049501.")


def _pede_alunos(texto: str, lugar: frozenset) -> bool:
    """"quantos alunos tem?" sem dizer a escola: a resposta é a ficha da escola, e falta saber qual. Sem esta
    regra, a pergunta casava com a orientação sobre PREVER a matrícula. Pergunta de fechamento ou com lugar
    ("quantos alunos no Piauí") segue o caminho normal."""
    # a contagem tem de vir colada ("quantas crianças"): "quanto tempo as crianças ficam no ônibus" é outra pergunta
    return bool(_CONTA_ALUNOS.search(normalizar(texto))) and "fecha" not in termos(texto) and not lugar


def responder(ctx: Contexto, texto: str, modelo: str = "B") -> Resposta:
    base = ctx.base
    bruto = normalizar(texto)
    if not bruto:
        return Resposta("vazia", respostas._par("Você não digitou nada. Escreva uma pergunta, um código como D1, "
                                                "ou o nome da escola."))

    codigo = codigo_falado(bruto) or bruto.replace(" ", "").upper()     # "ce um" = "C1"
    if codigo in base.registros:
        return Resposta("codigo", respostas.orientacao(base, codigo, modelo, numeros=_numeros(ctx, codigo, "")),
                        [codigo])

    if bruto.isdigit() and not (ctx.escolas and int(bruto) in ctx.escolas.por_codigo):
        return Resposta("vazia", respostas._par(f"Não reconheci o número {bruto}. Digite um código como D1, o código "
                                                "INEP de uma escola, ou escreva sua pergunta. (No menu, as opções "
                                                "vão de 0 a 4.)"))

    lugar = frozenset(fech_mod.palavras_do_lugar(ctx.fechamentos, texto)) if ctx.fechamentos else frozenset()
    r = ctx.indice.buscar(texto, lugar)
    achado = ctx.escolas.buscar(texto) if ctx.escolas else {"tipo": "nenhuma"}
    # Escola identificada sem dúvida (um só nome casa) vence sempre; nome repetido só vence se a orientação
    # não cobrir a pergunta inteira ("quilombo" sozinho: 10 escolas, mas é pergunta sobre D5). Aqui a
    # cobertura é medida COM as palavras de lugar: em "Escola Municipal São José", "São José" é nome de
    # escola, e sem ele sobrava só "municipal", que casava inteiro com a orientação de números por lugar.
    cob_nome = ctx.indice.buscar(texto).cobertura if lugar else r.cobertura
    if achado["tipo"] in ("unica", "codigo") or (achado["tipo"] == "ambigua" and cob_nome < 1.0):
        extras = r.ids if r.tipo == "unica" and modelo == "B" else []
        if achado["tipo"] == "ambigua":
            return lista_escolas(achado)
        resp = escola(ctx, achado["escolas"][0], modelo, extras)
        return resp
    if _pede_alunos(texto, lugar):
        return Resposta("vazia", respostas._par(MENSAGEM_ALUNOS))
    r = _pede_fechamentos(ctx, _lugar_desempata(ctx, r, texto), texto, lugar)
    if r.tipo == "vazia":
        return Resposta("vazia", respostas._par("Não entendi a pergunta: ela só tem palavras muito comuns. Tente com "
                                                "outras palavras."))
    if r.tipo == "unica":
        ja = set(base.registros[r.ids[0]].get("relacionados", [])[:3])
        extras = [x for x in r.sugestoes if x not in ja] if modelo == "B" else []
        fora = r.fora                     # as palavras do lugar já saíram da conta na busca
        return Resposta("unica", respostas.orientacao(base, r.ids[0], modelo, extras, fora,
                                                      _numeros(ctx, r.ids[0], texto)), r.ids, parcial=bool(fora))
    if r.tipo == "ambigua":
        return Resposta("ambigua", respostas.ambigua(base, r.ids), r.ids)

    return Resposta("nenhuma", respostas.sem_resposta(base))


def escola(ctx: Contexto, e: dict, modelo: str = "B", extras: list[str] | None = None) -> Resposta:
    doc = ctx.escolas.doc
    lig = set(ctx.base.ligacoes_escola.get("sempre", [])) | set(ctx.base.ligacoes_escola.get(e["d"] or "", []))
    extras = [x for x in (extras or []) if x not in lig]          # não repetir o que "Para continuar" já mostra
    return Resposta("escola", respostas.escola(ctx.base, e, doc["fonte"], doc["data_verificacao"], modelo, extras),
                    escolas=[e["c"]])


def _amostra(es: list[dict], n: int) -> list[dict]:
    """Uma escola de cada UF por vez, da UF com mais escolas para a com menos. A lista em ordem alfabética
    mostrava só escolas do Acre para "Escola Municipal São José" (546 achadas): não ajudava ninguém."""
    por_uf: dict[str, list[dict]] = {}
    for e in es:
        por_uf.setdefault(e["uf"], []).append(e)
    filas = sorted(por_uf.values(), key=len, reverse=True)
    saida: list[dict] = []
    while len(saida) < n and any(filas):
        for f in filas:
            if f and len(saida) < n:
                saida.append(f.pop(0))
    return saida


def lista_escolas(achado: dict, ja_filtrado: bool = False) -> Resposta:
    es = achado["escolas"]
    lugares = {(e["m"], e["uf"]) for e in es}
    # todas no mesmo município: pedir o município de novo não ajuda (a pessoa já disse); só a ficha distingue
    mesmo = len(es) > 1 and len(lugares) == 1 and all(next(iter(lugares)))
    pedido = (f", todas em {es[0]['m']}/{es[0]['uf']}. Para saber qual é a sua, abra a ficha de cada uma" if mesmo
              else "" if ja_filtrado else ". Para escolher, informe o município e a UF")
    mostra = _amostra(es, MAX_ESCOLAS_LISTA) if len(es) > MAX_ESCOLAS_LISTA else es
    n_ufs = len({e["uf"] for e in es})
    onde = f", em {n_ufs} UFs" if n_ufs > 1 and len(es) > MAX_ESCOLAS_LISTA else ""
    linhas = [respostas._par(f"Encontrei {achado['total']} escolas com essas palavras no nome{onde}{pedido}"
                             + (f". Algumas delas ({len(mostra)} de {achado['total']}):" if len(es) > len(mostra)
                                else ":"))]
    linhas += [f"  {e['c']}  {e['n']}, {respostas.lugar_escola(e)}" for e in mostra]
    linhas.append("Digite o código INEP (o número da esquerda) para abrir a ficha." if mesmo
                  else "Ou digite o código INEP (o número da esquerda).")
    return Resposta("escola_ambigua", "\n".join(linhas), escolas=[e["c"] for e in es])
