"""Os dois MODELOS DE INSTRUÇÃO de resposta e as mensagens de limite.

Cada modelo é uma especificação explícita (papel, formato, regras), escrita como se fosse o prompt
de um modelo de linguagem, e uma função que a CUMPRE de forma determinística. Assim a mesma
especificação serve para documentar, para comparar os dois modelos nos testes e, se um dia um
modelo de linguagem for usado, para instruí-lo (e conferir a saída dele contra a base).

As respostas nunca saem da base: o texto da orientação é o do registro, palavra por palavra.
"""

from __future__ import annotations

import math
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


def _par(texto: str, recuo: str = "", seguinte: str | None = None) -> str:
    """Quebra em LARGURA colunas sem cortar palavra nem endereço: um link cortado no meio não se copia
    (achado da 3ª rodada, num terminal mais largo que o texto, que o cortava sozinho)."""
    return textwrap.fill(texto, LARGURA, initial_indent=recuo,
                         subsequent_indent=recuo if seguinte is None else seguinte,
                         break_long_words=False, break_on_hyphens=False)


def _item(rid: str, pergunta: str) -> str:
    return _par(f"[{rid}] {pergunta}", "  ", "       ")


def _fonte(r: dict) -> str:
    ref = r["referencia"]
    if r.get("dados"):      # número contado pelo projeto: "conferida em" soaria como número publicado pelo órgão
        return (f"Fonte: {ref['titulo']}: {ref['url']} . Os totais foram contados pelo projeto; o texto desta "
                f"orientação foi conferido em {_data(r['data_verificacao'])}.")
    return f"Fonte: {ref['titulo']}. Conferida em {_data(r['data_verificacao'])} em {ref['url']}"


def _data(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{d}/{m}/{a}"


def aviso_parcial(fora: list[str]) -> str:
    return _par("Atenção: respondi com a orientação mais próxima, mas ela não fala de "
                + ", ".join(f'"{p}"' for p in fora) + ". Se a sua dúvida é sobre isso, esta base não tem a "
                "resposta: confirme com o órgão responsável.")


def orientacao(base: Base, rid: str, modelo: str = "B", extras: list[str] | None = None,
               fora: list[str] | None = None, numeros: str = "") -> str:
    """`numeros`: bloco calculado de dados (ex.: fechamentos do lugar citado), mostrado antes da fonte."""
    r = base.registros[rid]
    if fora:
        return aviso_parcial(fora) + "\n\n" + orientacao(base, rid, modelo, extras, numeros=numeros)
    if modelo == "A":
        return "\n".join([_par(r["orientacao"])] + ([numeros] if numeros else []) + [_par(_fonte(r)), RODAPE])
    tema = base.temas[r["tema"]]
    linhas = [_par(f"Assunto: {r['pergunta']}  [{tema['nome']}]", "", "  "), "", _par(r["orientacao"])]
    if numeros:
        linhas += ["", numeros]
    linhas += ["", _par(_fonte(r))]
    if r.get("confirmar"):
        linhas += ["", _par("Confirme: " + r["confirmar"])]
    rel = r.get("relacionados", [])[:3]
    if rel:
        linhas += ["", "Para continuar:"] + [_item(x, base.registros[x]["pergunta"]) for x in rel]
    if extras:
        linhas += ["", sugestoes(base, extras)]
    return "\n".join(linhas + ["", RODAPE])


def ambigua(base: Base, ids: list[str]) -> str:
    linhas = ["Sua pergunta combina com mais de um assunto. Qual deles?"]
    linhas += [_item(x, base.registros[x]["pergunta"]) for x in ids]
    return "\n".join(linhas + ["Digite o código entre colchetes, ou reformule a pergunta."])


def sem_resposta(base: Base) -> str:
    temas = ", ".join(t["nome"] for t in base.temas.values())
    return "\n".join([
        _par("Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. "
             "Prefiro dizer isso a inventar uma resposta."),
        _par(f"Os assuntos que conheço são: {temas}. Você pode escolher um deles no menu, reformular a "
             "pergunta com outras palavras, ou consultar uma escola pelo nome."),
        _par("Para uma dúvida fora desses assuntos: a Secretaria de Educação responde pela escola e pela "
             "rede; a Defensoria Pública dá orientação jurídica de graça."),
        RODAPE])


def sugestoes(base: Base, ids: list[str]) -> str:
    return "Talvez também interesse:\n" + "\n".join(_item(x, base.registros[x]["pergunta"]) for x in ids)


def _tempo(minutos: float) -> str:
    h, m = divmod(round(minutos), 60)
    return f"{m} min" if not h else f"{h} h" if not m else f"{h} h {m:02d} min"


MESMO_LUGAR_KM = 1.0  # abaixo disso, ida e volta, é a mesma coordenada pública (prédio ou endereço dividido)


def km_piso(x: float) -> str:
    """Distância para dizer "pelo menos": arredonda PARA BAIXO, senão o piso passaria do valor calculado
    (24,9 km viraria "pelo menos 25"). Inteiro a partir de 10 km; uma casa decimal abaixo disso."""
    if x >= 10:
        return f"{math.floor(x + 1e-9)}"
    return f"{math.floor(x * 10 + 1e-9) / 10:.1f}".replace(".", ",")


def lugar_escola(e: dict) -> str:
    return f"{e['m']}/{e['uf']}" if e.get("m") and e.get("uf") else "município não informado no Censo"


def aviso_rota(rota: dict, e: dict) -> str:
    """O aviso gravado no pré-cálculo, corrigido onde ele dizia "sem matrícula" de escola que tem alunos, mas só
    fora das etapas que a busca de receptoras usa (EJA ou educação profissional, por exemplo)."""
    if rota.get("motivo") == "sem_matricula" and e.get("t"):
        return ("A escola não tem alunos nas etapas da creche ao ensino médio regular, que a busca de escolas "
                "receptoras usa: não há receptoras a calcular.")
    return rota.get("aviso") or ""


def _receptora(r: dict, origem: dict) -> str:
    """Uma linha da lista de receptoras: nome, tipo, lugar, km e tempo (piso), chão e etapas cobertas.

    Campos além de n/rural/km são opcionais (o resumo da 1ª versão só tinha esses três).
    """
    onde = ["rural" if r["rural"] else "urbana"]
    if r.get("m") or r.get("uf"):
        onde.append(f"{r.get('m') or origem['m']}/{r.get('uf') or origem['uf']}")
    if r["km"] < MESMO_LUGAR_KM:  # "0 km e 1 min" seria precisão falsa: é a mesma coordenada pública
        texto = f"{r['n']} ({', '.join(onde)}): no mesmo lugar ou quase (mesma localização pública)"
    else:
        partes = [f"{km_piso(r['km'])} km"]
        if r.get("min") is not None:
            partes.append(_tempo(r["min"]))
        texto = f"{r['n']} ({', '.join(onde)}): {' e '.join(partes)}"
        if (r.get("chao") or 0) >= 0.5:
            texto += f", dos quais {km_piso(min(r['chao'], r['km']))} km de estrada de chão"
    etapas = r.get("etapas")
    if etapas:
        if set(etapas) >= set(origem["e"]):
            texto += "; recebe todas as etapas desta escola"
        else:
            texto += "; recebe só " + ", ".join(ETAPA.get(x, x) for x in etapas)
    return texto + "."


def escola(base: Base, e: dict, fonte: str, data_verif: str, modelo: str = "B",
           extras: list[str] | None = None) -> str:
    local = "rural" if e["z"] == "rural" else "urbana, mas a maioria dos alunos mora na zona rural"
    etapas = "; ".join(f"{ETAPA[k]}: {v}" for k, v in e["e"].items()) or (
        "nenhum da creche ao ensino médio regular; podem ser de EJA ou de educação profissional" if e["t"]
        else "sem matrícula informada")
    serie = e["s"]
    anos = sorted(serie)
    linhas = [f"{e['n']}, {lugar_escola(e)} (código INEP {e['c']})",
              _par(f"Escola {e['r'] or 'pública'} {local}" + (f", {ONDE.get(e['d'], e['d'])}" if e["d"] else "") + ".")]
    linhas.append(_par(f"Alunos em {anos[-1] if anos else 'último ano'}: {e['t']} ({etapas})."))
    if e.get("tp") is not None:
        linhas.append(_par(f"Usam transporte escolar público: {e['tp']}. Moram na zona rural: {e['zr']}."))
    if len(anos) > 1:
        linhas.append(_par("Matrícula por ano: " + ", ".join(f"{a}: {serie[a]}" for a in anos) + "."))
    rota = e.get("rota")
    if rota and rota.get("receptoras"):
        linhas.append("Escolas que poderiam receber os alunos (estrada por dia, ida e volta, PELO MENOS):")
        for r in rota["receptoras"]:
            linhas.append(textwrap.fill(_receptora(r, e), LARGURA, initial_indent="  - ", subsequent_indent="    "))
        if aviso_rota(rota, e):
            linhas.append(_par(aviso_rota(rota, e)))
        if rota.get("sem_rota"):
            linhas.append(_par(f"Outras {rota['sem_rota']} escola(s) próxima(s) ficaram sem rota na malha viária "
                               "e não entram na lista."))
        quando = f", dados de {_data(rota['osm'])}" if rota.get("osm") else ""
        linhas.append(_par(f"Conta feita de escola a escola pela malha do OpenStreetMap{quando}. A casa de cada "
                           "criança, as paradas do ônibus e a estrada na chuva deixam o trajeto real maior."))
    elif rota:  # calculada, mas nenhuma receptora tem rota: o aviso diz por quê, e nenhum número aparece
        linhas.append(_par((aviso_rota(rota, e) or "Nenhuma rota por estrada foi calculada para esta escola.")
                           + " Não vou estimar um número sem base."))
    elif not e["geo"]:
        linhas.append(_par("A localização desta escola não é pública: o Catálogo de Escolas do INEP não traz a "
                           "coordenada dela (nem a base do Ipea, que copia o Catálogo). Sem isso, a distância até "
                           "outras escolas não pode ser calculada. Não vou estimar um número sem base. A localização "
                           "pode ser pedida ao INEP pela Lei de Acesso à Informação."))
    else:
        linhas.append(_par("A distância até as escolas que poderiam receber os alunos ainda não foi calculada para "
                           "esta escola. Não vou estimar um número sem base."))
    linhas.append(_par(f"Fonte: {fonte} (dados baixados em {_data(data_verif)})."))
    if modelo == "B":
        lig = base.ligacoes_escola
        chaves = ["sempre"] + (["com_rota"] if e.get("rota") and e["rota"].get("receptoras") else []) + [e["d"] or ""]
        ids: list[str] = []
        for k in chaves:
            ids += [x for x in lig.get(k, []) if x not in ids]
        if ids:
            linhas += ["", "Para continuar:"] + [_item(x, base.registros[x]["pergunta"]) for x in ids]
    if extras:
        linhas += ["", sugestoes(base, extras)]
    return "\n".join(linhas + ["", RODAPE])
