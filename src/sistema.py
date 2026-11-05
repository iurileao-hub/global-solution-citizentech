"""Assistente Escola em Pauta: interface de texto.

Executar (na raiz do repositório):   python src/sistema.py
Opções:  --modelo A|B   escolhe o modelo de resposta (padrão: B)
         --avaliar      roda as perguntas de teste e grava data/resultados_testes.csv

Só usa a biblioteca padrão do Python (3.10 ou mais recente) e funciona sem internet.
Não pede nem guarda nenhum dado pessoal.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
RAIZ = SRC.parent
sys.path.insert(0, str(SRC))

from assistente import base as base_mod          # noqa: E402
from assistente import escolas as escolas_mod    # noqa: E402
from assistente import respostas                 # noqa: E402
from assistente.nucleo import Contexto, escola, lista_escolas, montar, responder  # noqa: E402

ARQ_BASE = RAIZ / "data" / "base_orientacoes.json"
ARQ_ESCOLAS = RAIZ / "data" / "escolas_campo.json.gz"

MENU = """
O que você quer fazer?
  1  Escolher um assunto
  2  Fazer uma pergunta
  3  Consultar uma escola pelo nome ou código INEP
  4  Sobre este assistente (limites, privacidade, fontes)
  0  Sair"""


def ler(rotulo: str) -> str:
    try:
        return input(rotulo).strip()
    except EOFError:            # entrada fechada (ex.: Ctrl+D): sair sem erro
        print()
        raise SystemExit(0)


def continuar(ctx: Contexto, modelo: str, ultimo: str = "") -> None:
    """Depois de uma resposta: aceita um código [X] para seguir no grafo de assuntos, ou outra pergunta.

    O convite só fala em "código" quando a tela mostrou algum (achado do teste de usabilidade)."""
    while True:
        convite = ("\nDigite um código entre colchetes, outra pergunta, ou Enter para voltar ao menu: "
                   if "  [" in ultimo else "\nEscreva outra pergunta, ou aperte Enter para voltar ao menu: ")
        cod = ler(convite)
        if not cod:
            return
        r = responder(ctx, cod, modelo)
        print("\n" + r.texto)
        ultimo = r.texto
        if r.tipo == "escola_ambigua":
            ultimo = escolher_escola(ctx, modelo, [ctx.escolas.por_codigo[c] for c in r.escolas])


def por_assunto(ctx: Contexto, modelo: str) -> None:
    base = ctx.base
    temas = list(base.temas)
    print()
    for i, t in enumerate(temas, 1):
        print(f"  {i}  {base.temas[t]['nome']}: {base.temas[t].get('descricao', '')}")
    op = ler("Número do assunto (Enter volta): ")
    if not op:
        return
    if not op.isdigit() or not 1 <= int(op) <= len(temas):
        print(f"Opção inexistente: '{op}'. Escolha um número de 1 a {len(temas)}.")
        return
    tema = temas[int(op) - 1]
    info = base.temas[tema]
    print(f"\n{info['nome']}")
    for sub, nome in info["subtemas"].items():
        ids = [x for x in base.por_tema[tema] if base.registros[x]["subtema"] == sub]
        if ids:
            print(f"  {nome}")
            for x in ids:
                print(f"    [{x}] {base.registros[x]['pergunta']}")
    rel = [base.temas[t]["nome"] for t in info.get("relacionados", [])]
    if rel:
        print(f"  (Assuntos relacionados: {', '.join(rel)})")
    continuar(ctx, modelo, "  [")


def escolher_escola(ctx: Contexto, modelo: str, candidatas: list[dict]) -> str:
    """Desempata nomes repetidos. Devolve o texto mostrado (para o convite seguinte saber se houve códigos)."""
    mun = ler("Município ou código INEP (Enter para pular): ")
    if mun.isdigit():                       # a tela mandou "digite o código INEP": aceitar aqui também
        e = next((x for x in candidatas if x["c"] == int(mun)), None) or ctx.escolas.por_codigo.get(int(mun))
        texto = escola(ctx, e, modelo).texto if e else f"Não há escola com o código {mun} nesta lista."
        print("\n" + texto)
        return texto
    uf = ler("UF, ex.: ES (Enter para pular): ")
    if not mun and not uf:
        return ""
    filtradas = escolas_mod.filtrar(candidatas, municipio=mun, uf=uf)
    achado = {"escolas": filtradas, "total": len(filtradas)}
    if achado["total"] == 1:
        texto = escola(ctx, achado["escolas"][0], modelo).texto
    elif achado["total"] > 1:
        texto = lista_escolas(achado, ja_filtrado=True).texto
    else:
        texto = "Nenhuma das escolas com essas palavras no nome fica nesse município/UF."
    print("\n" + texto)
    return texto


def por_escola(ctx: Contexto, modelo: str) -> None:
    if not ctx.escolas:
        print("A consulta de escolas está indisponível nesta instalação (arquivo de escolas ausente ou ilegível).")
        return
    txt = ler("Nome ou código INEP da escola: ")
    achado = ctx.escolas.buscar(txt)
    if achado["tipo"] == "vazia":
        print("Digite ao menos uma palavra do nome (além de 'escola', 'municipal'...) ou o código INEP.")
    elif achado["tipo"] == "nenhuma":
        print(respostas._par("Não encontrei uma escola do campo com essas palavras no nome. A base tem só as "
                             "escolas públicas do campo em atividade no Censo Escolar 2025; escolas urbanas não "
                             "aparecem. Tente escrever só o nome da escola, ou use o código INEP."))
    elif achado["tipo"] in ("unica", "codigo"):
        ultimo = escola(ctx, achado["escolas"][0], modelo).texto
        print("\n" + ultimo)
        continuar(ctx, modelo, ultimo)
        return
    else:
        print("\n" + lista_escolas(achado).texto)
        continuar(ctx, modelo, escolher_escola(ctx, modelo, achado["escolas"]))
        return
    continuar(ctx, modelo)


def sobre(ctx: Contexto) -> None:
    base = ctx.base
    n = len(base.registros)
    print("\n" + respostas._par(respostas.NAO_OFICIAL))
    print(respostas._par(
        f"Conhece {n} orientações em {len(base.temas)} assuntos, cada uma com a fonte e a data em que foi conferida. "
        "Quando a pergunta não está na base, o assistente diz que não sabe, em vez de inventar."))
    print(respostas._par(
        "Privacidade: não pede nome, endereço nem documento, e não grava o que você digita. Os números das escolas "
        "são públicos (Censo Escolar do INEP) e contam escolas, nunca identificam crianças."))
    if ctx.escolas:
        n_esc = f"{len(ctx.escolas.por_codigo):,}".replace(",", ".")   # separador de milhar brasileiro
        print(respostas._par(f"Escolas consultáveis: {n_esc} ({ctx.escolas.doc['fonte']})."))


def main(argv: list[str] | None = None) -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # terminal do Windows: acentos sem erro
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser(description="Assistente Escola em Pauta (não oficial)")
    ap.add_argument("--modelo", choices=["A", "B"], default="B")
    ap.add_argument("--avaliar", action="store_true", help="roda as perguntas de teste e calcula os indicadores")
    ap.add_argument("--perguntas", default="perguntas_teste.json",
                    help="arquivo de perguntas em data/ (ex.: perguntas_cegas.json)")
    ap.add_argument("--base", default=str(ARQ_BASE))
    ap.add_argument("--escolas", default=str(ARQ_ESCOLAS))
    args = ap.parse_args(argv)

    try:
        base = base_mod.carregar(args.base)
    except base_mod.ErroBase as e:
        print(f"Não foi possível iniciar o assistente.\n{e}", file=sys.stderr)
        return 1
    try:
        doc_escolas = escolas_mod.carregar(args.escolas)
    except escolas_mod.ErroEscolas as e:
        print(f"Aviso: {e}\nO assistente funciona, mas sem a consulta de escolas.", file=sys.stderr)
        doc_escolas = None
    ctx = montar(base, doc_escolas)

    if args.avaliar:
        from assistente import avaliacao
        return avaliacao.main(ctx, RAIZ, args.perguntas)

    print("=" * respostas.LARGURA)
    print("ESCOLA EM PAUTA: assistente sobre o fechamento de escolas do campo")
    print("=" * respostas.LARGURA)
    print(respostas._par(respostas.NAO_OFICIAL))
    acoes = {"1": por_assunto, "3": por_escola}
    try:
        while True:
            print(MENU)
            op = ler("Opção: ")
            if op == "0":
                print("Até logo.")
                return 0
            if op in acoes:
                acoes[op](ctx, args.modelo)
            elif op == "2":
                r = responder(ctx, ler("Sua pergunta: "), args.modelo)
                print("\n" + r.texto)
                ultimo = r.texto
                if r.tipo == "escola_ambigua":
                    ultimo = escolher_escola(ctx, args.modelo, [ctx.escolas.por_codigo[c] for c in r.escolas])
                continuar(ctx, args.modelo, ultimo)
            elif op == "4":
                sobre(ctx)
            elif not op:
                print("Digite o número de uma opção.")
            else:
                print(f"Opção inexistente: '{op}'. Use 0, 1, 2, 3 ou 4.")
    except KeyboardInterrupt:
        print("\nAté logo.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
