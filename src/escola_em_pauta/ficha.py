"""A ficha da escola: HTML leve e imprimível (A4, frente e verso).

Separação de responsabilidades: `contexto()` decide TODO o texto (plurais,
porcentagens, qual receptora vai para a manchete) em Python, onde dá para
testar; o template Jinja2 (templates/ficha.html.j2) só posiciona. O CSS é o
do mockup aprovado (docs/design/ficha-mockup.html), sem mudança de design.

Regras de texto: o número é sempre PISO ("pelo menos"); nada de "deve" ou
"não deve" fechar; a frente informa e o verso é da comunidade.
"""

from __future__ import annotations

import math
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .modelos import Diagnostico, Receptora

TEMPLATES = Path(__file__).parent / "templates"

UF_NOME = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

ETAPA_ROTULO = {"creche": "creche", "pre_escola": "pré-escola", "anos_iniciais": "anos iniciais",
                "anos_finais": "anos finais", "medio": "ensino médio"}
ETAPA_INICIO = {"creche": "da creche", "pre_escola": "da pré-escola", "anos_iniciais": "do 1º ano",
                "anos_finais": "do 6º ano", "medio": "do ensino médio"}
ETAPA_FIM = {"creche": "à creche", "pre_escola": "à pré-escola", "anos_iniciais": "ao 5º ano",
             "anos_finais": "ao 9º ano", "medio": "ao ensino médio"}
ORDEM_ETAPAS = list(ETAPA_ROTULO)
ANOS_DA_ETAPA = {"anos_iniciais": range(1, 6), "anos_finais": range(6, 10)}

# Validação em Muniz Freire (validacao.py, 04/11/2026): TCE mediu 52 km/dia; de escola a
# escola, nossa rota deu de 24,9 a 45,0 km. Atualizar se houver mais casos medidos.
MARGEM_TEXTO = ("por enquanto há um único caso com medição de campo (Muniz Freire, ES). O Tribunal de Contas "
                "mediu 52 km por dia; o cálculo de escola a escola deu de 25 a 45 km, ou seja, o real foi de "
                "16% a 109% maior. A margem será revista quando houver mais casos medidos.")

SIGLAS = {"EMEF", "EEEFM", "CEEFMTI", "CEI", "EPM", "EEEM", "EMEI", "EMEIEF", "CMEI", "CEF", "CED", "EC",
          "CAIC", "EE", "EM", "EMEB", "EMEFM", "EEF", "EEM", "EEFM", "CIEP", "CE", "UE", "ETEC", "IF", "JI"}
MINUSCULAS = {"de", "da", "do", "das", "dos", "e", "em", "na", "no"}


def nome_legivel(nome: str) -> str:
    """O Censo grava nomes em caixa alta e sem acento; devolvemos siglas em maiúscula e o resto capitalizado."""
    saida = []
    for i, p in enumerate(nome.split()):
        if p in SIGLAS or not any(c in "AEIOU" for c in p):
            saida.append(p)
        elif i > 0 and p.lower() in MINUSCULAS:
            saida.append(p.lower())
        else:
            saida.append(p.capitalize())
    return " ".join(saida)


def km(x: float) -> str:
    return f"{x:.0f}" if x >= 10 else f"{x:.1f}".replace(".", ",")


def lista_pt(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def data_pt(d: date) -> str:
    meses = "jan fev mar abr maio jun jul ago set out nov dez".split()
    return f"{d.day} {meses[d.month - 1]}. {d.year}" if d.month != 5 else f"{d.day} maio {d.year}"


def _faixa_etapas(etapas: list[str]) -> str:
    etapas = sorted(etapas, key=ORDEM_ETAPAS.index)
    if len(etapas) == 1:
        return f"na {ETAPA_ROTULO[etapas[0]]}" if etapas[0] in ("creche", "pre_escola") else f"nos {ETAPA_ROTULO[etapas[0]]}"
    return f"{ETAPA_INICIO[etapas[0]]} {ETAPA_FIM[etapas[-1]]}"


def _manchete(d: Diagnostico) -> Receptora | None:
    """A receptora da frase de abertura: a mais próxima por estrada que cobre TODAS as etapas; senão, a mais próxima."""
    com_rota = [r for r in d.receptoras if r.km_ida_volta_piso is not None]
    todas = [r for r in com_rota if set(r.etapas_cobertas) >= set(d.matriculas_por_etapa)]
    return min(todas or com_rota, key=lambda r: r.km_ida_volta_piso, default=None)


def _rotulo_receptora(r: Receptora, d: Diagnostico) -> str:
    partes = ["rural" if r.rural else "urbana"]
    if r.escola.municipio != d.escola.municipio:
        partes.append(f"em {r.escola.municipio}")
    faltam = set(d.matriculas_por_etapa) - set(r.etapas_cobertas)
    if faltam:
        partes.append("só " + lista_pt([ETAPA_ROTULO[e] for e in sorted(r.etapas_cobertas, key=ORDEM_ETAPAS.index)]))
    if r.alunos_por_sala:
        partes.append(f"~{r.alunos_por_sala:.0f} alunos por sala, somando os turnos")
    return ", ".join(partes)


def _escala(d: Diagnostico) -> tuple[float, list[int]]:
    """Fim do eixo (km) e marcas: cabe a maior rota e a medição de campo, com folga para a seta."""
    maior = max([r.km_ida_volta_piso or r.km_linha_reta_ida_volta for r in d.receptoras] + [1.0])
    if d.medicao_campo:
        maior = max(maior, d.medicao_campo["km_dia"])
    passo = 10 if maior <= 30 else 20 if maior <= 80 else 50
    fim = math.ceil(maior * 1.15 / passo) * passo
    return fim, list(range(0, fim, passo))


def contexto(d: Diagnostico, hoje: date | None = None) -> dict:
    hoje = hoje or date.today()
    e, p = d.escola, d.perfil
    n = d.matricula_total
    etapas = sorted(d.matriculas_por_etapa, key=ORDEM_ETAPAS.index)

    # ---- abertura
    abre = [f"Aqui estudam <b>{n} crianças e adolescentes</b>, {_faixa_etapas(etapas)}." if etapas
            else f"No Censo {d.ano_referencia}, esta escola não tinha matrícula."]
    if d.usam_transporte_publico:
        abre.append(f"<b>{d.usam_transporte_publico} chegam de transporte escolar público.</b>")
    m = _manchete(d)
    if m:
        todas = set(m.etapas_cobertas) >= set(d.matriculas_por_etapa)
        qual = "que oferece as mesmas etapas" if todas else "que oferece parte das etapas"
        abre.append(f"A escola mais perto {qual} fica a pelo menos {km(m.km_ida_volta_piso / 2)} km por estrada: "
                    f"<b>pelo menos {km(m.km_ida_volta_piso)} km por dia</b>, ida e volta.")

    # ---- seção 1: quem estuda
    partes = [f"{d.matriculas_por_etapa[x]} {'na' if x in ('creche', 'pre_escola') else 'nos' if x != 'medio' else 'no'} "
              f"{ETAPA_ROTULO[x]}" for x in etapas]
    leia1 = f"Em {d.ano_referencia}, {n} matrículas" + (": " + lista_pt(partes) + "." if partes else ".")
    zeros = [f"{a}º" for x in etapas for a in ANOS_DA_ETAPA.get(x, []) if p["por_ano_escolar"].get(a, 0) == 0]
    if zeros:
        leia1 += f" Não havia turma de {lista_pt([z + ' ano' for z in zeros])}."
    linhas, maior = [], max([d.matriculas_por_etapa.get(x, 0) for x in ("creche", "pre_escola", "medio")]
                            + list(p["por_ano_escolar"].values()) + [1])
    for x in etapas:
        if x in ANOS_DA_ETAPA:
            linhas.append({"tipo": "etapa", "rotulo": ETAPA_ROTULO[x].capitalize(),
                           "sub": f"{ANOS_DA_ETAPA[x][0]}º ao {ANOS_DA_ETAPA[x][-1]}º ano"})
            for a in ANOS_DA_ETAPA[x]:
                v = p["por_ano_escolar"].get(a, 0)
                linhas.append({"tipo": "ano", "rotulo": f"{a}º ano", "v": v, "w": round(100 * v / maior, 1)})
        else:
            v = d.matriculas_por_etapa[x]
            linhas.append({"tipo": "etapa_valor", "rotulo": ETAPA_ROTULO[x].capitalize(), "v": v,
                           "w": round(100 * v / maior, 1)})
    zr = d.moram_zona_rural
    fatos = [(f"<b>Todas as {n}</b> moram" if zr == n and n else f"<b>{zr} de {n}</b> moram") + " na zona rural."]
    if d.usam_transporte_publico:
        fatos[0] += f" <b>{d.usam_transporte_publico}</b> usam transporte escolar público."
    if p.get("educacao_especial"):
        ee = p["educacao_especial"]
        fatos[0] += f" <b>{ee}</b> {'é aluno' if ee == 1 else 'são alunos'} da educação especial."
    estrutura = f"A escola tem <b>{p['professores']} professores</b> e <b>{p['salas_utilizadas']} salas</b>"
    infra = list(p.get("infraestrutura", []))
    if p.get("sem_energia"):
        infra.insert(0, "<b>sem energia elétrica</b>")
    fatos.append(estrutura + (", " + lista_pt(infra) if infra else "") + ".")

    # ---- seção 2: série
    serie = d.serie_matricula
    vmin, vmax = min(serie.values(), default=0), max(serie.values(), default=1)
    pontos = [{"ano": a, "v": v, "y": 15 + (55 * (v - vmin) / (vmax - vmin) if vmax > vmin else 27)}
              for a, v in sorted(serie.items())]
    t = d.tendencia
    if t:
        (a0, v0), (a1, v1) = t["primeiro"], t["ultimo"]
        b = t["inclinacao_alunos_ano"]
        ritmo = f"{'+' if b >= 0 else '−'}{abs(b):.1f}".replace(".", ",")
        leia2 = (f"De {a0} a {a1}, a matrícula foi de {v0} para {v1}: tendência <b>{t['sentido']}</b> "
                 f"({ritmo} aluno por ano).")
    else:
        leia2 = "Série curta demais para descrever uma tendência."
    nao_preve = ("Não projetamos o futuro: num teste com quase 2 mil escolas rurais (DF, SP e ES), projetar pela "
                 "tendência errou mais do que supor que a matrícula se repete.")

    # ---- seção 3: estradas
    fim, marcas = _escala(d)
    rows = []
    for r in d.receptoras:
        linha = {"nome": nome_legivel(r.escola.nome), "rotulo": _rotulo_receptora(r, d)}
        if r.km_ida_volta_piso is not None:
            w = 100 * r.km_ida_volta_piso / fim
            linha.update(ok=True, km=km(r.km_ida_volta_piso), min=f"{r.minutos_ida_volta_piso:.0f}",
                         w=round(w, 1), ext=round(min(0.4 * w, 100 - w), 1))
        else:
            linha.update(ok=False, reta=round(100 * r.km_linha_reta_ida_volta / fim, 1),
                         aviso=f"{r.aviso}; em linha reta, {km(r.km_linha_reta_ida_volta)} km")
        rows.append(linha)
    n_rurais = sum(r.rural for r in d.receptoras)
    chao = d.malha.get("km_por_piso", {})
    total_km = sum(chao.values())
    leia3 = ["Medimos a estrada de escola a escola. <b>É o mínimo.</b> O ônibus real passa de casa em casa, "
             "por isso o caminho de verdade é maior."]
    if total_km:
        leia3.append(f"Na região, {chao.get('sem pavimento', 0) / total_km:.0%} das estradas mapeadas são de chão.")
    if d.receptoras:
        leia3.append(f"Das {len(d.receptoras)} escolas mais próximas que oferecem alguma das mesmas etapas, "
                     + ("nenhuma é rural." if n_rurais == 0 else f"{n_rurais} {'é rural' if n_rurais == 1 else 'são rurais'}."))
    nota3 = []
    if d.medicao_campo:
        mc = d.medicao_campo
        nota3.append(f"Neste caso, o {mc['quem']} mediu {mc['km_dia']:.0f} km por dia {mc['detalhe']} ({mc['fonte']}).")
    nota3.append("Vagas em cada receptora: <b>a calcular</b> (o número de vagas não é publicado; alunos por sala é estimativa).")
    item_cne = next((i for i in d.checklist if i["item"].startswith("Pré-escola e anos iniciais")), None)
    if item_cne and "não tem essas etapas" not in item_cne["detalhe"]:
        nota3.append("As normas nacionais pedem que a pré-escola e os anos iniciais sejam oferecidos na própria "
                     f"comunidade (Res. CNE/CEB 2/2008, art. 3º). Nesta escola, {item_cne['detalhe']}.")

    # ---- verso
    simbolo = {"pronto": "■", "a preencher": "□", "a calcular": "◇"}
    lei = [{**i, "g": simbolo[i["situacao"]]} for i in d.checklist]
    data_osm = d.malha.get("data_osm")
    fonte_osm = f"OpenStreetMap ({data_osm[:10]})" if data_osm else "OpenStreetMap"

    return {
        "d": d, "e": e,
        "nome": nome_legivel(e.nome),
        "onde": f"Escola {p.get('dependencia', 'pública')} da zona {'rural' if e.rural else 'urbana'} de "
                f"{e.municipio}, {UF_NOME.get(e.uf, e.uf)}. Código INEP {e.codigo_inep}."
                + (f" Localizada em {e.localizacao_diferenciada}." if e.localizacao_diferenciada else ""),
        "carimbo": f"Censo Escolar {d.ano_referencia} e mapa de estradas, {data_pt(hoje)}",
        "abre": " ".join(abre),
        "avisos": d.avisos,
        "leia1": leia1, "linhas": linhas, "fatos": fatos,
        "pontos": pontos, "leia2": leia2, "nao_preve": nao_preve,
        "leia3": " ".join(leia3), "rows": rows, "fim": fim,
        "marcas": [{"km": k, "x": round(100 * k / fim, 1)} for k in marcas],
        "medicao": ({"x": round(100 * d.medicao_campo["km_dia"] / fim, 1), **d.medicao_campo}
                    if d.medicao_campo else None),
        "nota3": " ".join(nota3),
        "lei": lei, "fonte_osm": fonte_osm, "margem": MARGEM_TEXTO,
    }


def _ambiente() -> Environment:
    return Environment(loader=FileSystemLoader(TEMPLATES), autoescape=select_autoescape(["html", "j2"]),
                       trim_blocks=True, lstrip_blocks=True)


def renderizar(d: Diagnostico, hoje: date | None = None) -> str:
    ctx = contexto(d, hoje)
    ctx["css"] = (TEMPLATES / "ficha.css").read_text()
    return _ambiente().get_template("ficha.html.j2").render(**ctx)
