"""Os dois MODELOS DE INSTRUÇÃO de resposta e as mensagens de limite.

Cada modelo é uma especificação explícita (papel, formato, regras), escrita como se fosse o prompt
de um modelo de linguagem, e uma função que a CUMPRE de forma determinística. Assim a mesma
especificação serve para documentar, para comparar os dois modelos nos testes e, se um dia um
modelo de linguagem for usado, para instruí-lo (e conferir a saída dele contra a base).

As respostas nunca saem da base: o texto da orientação é o do registro, palavra por palavra.
"""

from __future__ import annotations

import textwrap

from .base import Base

LARGURA = 78
NAO_OFICIAL = ("Assistente NÃO OFICIAL, feito por estudantes. Não fala em nome de nenhum órgão público. "
               "Confira sempre com a Secretaria de Educação, o Conselho de Educação, o Ministério Público "
               "ou a Defensoria.")
RODAPE = "(Não oficial: confira com o órgão responsável.)"

MODELOS = {
    "A": {
        "nome": "Direto",
        "papel": "Responder a pergunta com a orientação da base.",
        "formato": ["a orientação, em um parágrafo", "uma linha com a fonte e a data de verificação",
                    "rodapé curto de não oficial"],
        "regras": ["usar só o texto da base", "sempre citar a fonte"],
    },
    "B": {
        "nome": "Orientador com limites",
        "papel": ("Assistente não oficial que orienta a comunidade escolar diante do fechamento de uma escola "
                  "do campo, em linguagem simples, sem se passar por órgão público."),
        "formato": ["o assunto que o assistente entendeu (para a pessoa conferir)", "o que diz a fonte",
                    "fonte e data de verificação", "o que confirmar, quando a orientação exigir",
                    "até 3 caminhos para continuar (assuntos relacionados)", "rodapé curto de não oficial"],
        "regras": ["usar só o texto da base", "sempre citar a fonte e a data", "dizer o que precisa ser confirmado",
                   "oferecer continuidade", "nunca prometer atendimento oficial"],
    },
}

ONDE = {"assentamento": "em área de assentamento", "indígena": "em terra indígena",
        "quilombola": "em comunidade quilombola", "comunidade tradicional": "em área de comunidade tradicional"}
ETAPA = {"creche": "creche", "pre_escola": "pré-escola", "anos_iniciais": "anos iniciais (1º ao 5º ano)",
         "anos_finais": "anos finais (6º ao 9º ano)", "medio": "ensino médio"}


def _par(texto: str, recuo: str = "") -> str:
    return textwrap.fill(texto, LARGURA, initial_indent=recuo, subsequent_indent=recuo)


def _fonte(r: dict) -> str:
    ref = r["referencia"]
    return f"Fonte: {ref['titulo']} — {ref['url']} (conferida em {_data(r['data_verificacao'])})"


def _data(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def orientacao(base: Base, rid: str, modelo: str = "B", extras: list[str] | None = None) -> str:
    r = base.registros[rid]
    if modelo == "A":
        return "\n".join([_par(r["orientacao"]), _par(_fonte(r)), RODAPE])
    tema = base.temas[r["tema"]]
    linhas = [f"Assunto: {r['pergunta']}  [{tema['nome']}]", "", _par(r["orientacao"]), "", _par(_fonte(r))]
    if r.get("confirmar"):
        linhas += ["", _par("Confirme: " + r["confirmar"])]
    rel = r.get("relacionados", [])[:3]
    if rel:
        linhas += ["", "Para continuar:"] + [f"  [{x}] {base.registros[x]['pergunta']}" for x in rel]
    if extras:
        linhas += ["", sugestoes(base, extras)]
    return "\n".join(linhas + ["", RODAPE])


def ambigua(base: Base, ids: list[str]) -> str:
    linhas = ["Sua pergunta combina com mais de um assunto. Qual deles?"]
    linhas += [f"  [{x}] {base.registros[x]['pergunta']}" for x in ids]
    return "\n".join(linhas + ["Digite o código entre colchetes, ou reformule a pergunta."])


def sem_resposta(base: Base) -> str:
    temas = ", ".join(t["nome"] for t in base.temas.values())
    return "\n".join([
        _par("Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. "
             "Prefiro dizer isso a inventar uma resposta."),
        _par(f"Os assuntos que conheço são: {temas}. Você pode escolher um deles no menu, reformular a "
             "pergunta com outras palavras, ou consultar uma escola pelo nome."),
        RODAPE])


def sugestoes(base: Base, ids: list[str]) -> str:
    return "Talvez também interesse:\n" + "\n".join(f"  [{x}] {base.registros[x]['pergunta']}" for x in ids)


def escola(base: Base, e: dict, fonte: str, data_verif: str, modelo: str = "B") -> str:
    local = "rural" if e["z"] == "rural" else "urbana, mas a maioria dos alunos mora na zona rural"
    etapas = "; ".join(f"{ETAPA[k]}: {v}" for k, v in e["e"].items()) or "sem matrícula informada"
    serie = e["s"]
    anos = sorted(serie)
    linhas = [f"{e['n']} — {e['m']}/{e['uf']} (código INEP {e['c']})",
              _par(f"Escola {e['r'] or 'pública'} {local}" + (f", {ONDE.get(e['d'], e['d'])}" if e["d"] else "") + ".")]
    linhas.append(_par(f"Alunos em {anos[-1] if anos else 'último ano'}: {e['t']} ({etapas})."))
    if e.get("tp") is not None:
        linhas.append(_par(f"Usam transporte escolar público: {e['tp']}. Moram na zona rural: {e['zr']}."))
    if len(anos) > 1:
        linhas.append(_par("Matrícula por ano: " + ", ".join(f"{a}: {serie[a]}" for a in anos) + "."))
    if e.get("rota"):
        linhas.append("Escolas que poderiam receber os alunos (estrada por dia, ida e volta, PELO MENOS):")
        for r in e["rota"]["receptoras"]:
            linhas.append(f"  - {r['n']} ({'rural' if r['rural'] else 'urbana'}): {r['km']:.0f} km")
    elif not e["geo"]:
        linhas.append(_par("Esta escola não tem coordenada na base pública do Ipea, então a distância até outras "
                           "escolas não pode ser calculada. Não vou estimar um número sem base."))
    else:
        linhas.append(_par("A distância até as escolas que poderiam receber os alunos ainda não foi calculada para "
                           "esta escola. Não vou estimar um número sem base."))
    linhas.append(_par(f"Fonte: {fonte} (dados baixados em {_data(data_verif)})."))
    if modelo == "B":
        lig = base.ligacoes_escola
        ids = list(lig.get("sempre", [])) + [x for x in lig.get(e["d"] or "", []) if x not in lig.get("sempre", [])]
        if ids:
            linhas += ["", "Para continuar:"] + [f"  [{x}] {base.registros[x]['pergunta']}" for x in ids]
    return "\n".join(linhas + ["", RODAPE])
