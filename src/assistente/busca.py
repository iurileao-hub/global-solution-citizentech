"""Busca de orientações: índice invertido com pontuação por peso do campo.

ÍNDICE INVERTIDO é o índice remissivo de um livro: para cada termo (radical), a lista dos
registros onde ele aparece. Montá-lo custa uma passada na base; depois, cada pergunta só olha
os registros que têm algum termo dela, em vez de comparar com todos.

PONTUAÇÃO de um registro para uma pergunta = soma, para cada termo DISTINTO da pergunta, do maior
peso em que esse termo aparece no registro:
    palavras-chave = 3   (vocabulário escolhido de propósito, inclusive sinônimos populares)
    pergunta modelo = 2
    nome do subtema = 1
    título da norma citada = 1  (a 3ª rodada perguntou pela "Resolução CNE/CEB 2/2008" e pelo "Decreto
                                 7.352/2010", que a base cita como fonte sem repetir no texto)
  + BONUS_EXATA por palavra que casa INTEIRA (não só pelo radical): "quilombola" casa inteira com
    a orientação sobre escolas quilombolas e só pelo radical com a que fala de "quilômetros".
Termos que aparecem em mais da metade dos registros ("escol", por exemplo) não distinguem nada e
são ignorados. Termos NEUTROS ("fechar", "campo", "rural") são o tema da base inteira: nunca aparecem no
aviso de cobertura (na 3ª rodada, o aviso dizia que a resposta "não trata de 'fechar'"), mas continuam
na CONTA da cobertura. Tirá-los da conta foi testado e piorou: subiu o acerto nas perguntas novas (+1) e
derrubou o das antigas (-4), porque perguntas fora da base passaram a receber resposta tangencial.
As palavras do LUGAR citado ("Piauí") não contam em nada: dizem onde, não o assunto.

COBERTURA de um registro = fração dos termos da pergunta que ele casou. Três faixas:
    >= COBERTURA_PLENA                  -> resposta normal;
    entre COBERTURA_MINIMA e a plena    -> resposta PARCIAL: responde e lista as palavras da pergunta
                                           que a orientação não cobre ("deficiência", "monitor"),
                                           para a pessoa saber que essa parte ficou sem resposta;
    < COBERTURA_MINIMA                  -> descartado: uma palavra solta estaria decidindo
                                           ("melhor escola particular da CIDADE" casava só "cidade").
Histórico (README, seção 4): com um corte único de 40%, ajustado em perguntas curtas escritas pela
equipe, o assistente acertou 68% de 50 perguntas escritas às cegas: 10 "não sei" em pergunta longa
que a base respondia, e 6 respostas erradas dadas com segurança.

DECISÃO (o que fazer com a lista ordenada):
    - maior pontuação < LIMIAR_MINIMO         -> "nenhuma": sem base suficiente; o assistente diz
                                                 isso e sugere temas, nunca inventa;
    - dois ou mais registros EMPATADOS no topo -> se todos são do MESMO subtema, eles se completam
                                                 ("quem paga o ônibus?": responsável e verba):
                                                 responde o primeiro e sugere os outros;
                                                 se são de subtemas diferentes -> "ambigua":
                                                 mostra as opções e pede para escolher;
    - senão                                    -> "unica": responde o primeiro e sugere até 2
                                                 outros que pontuaram (desempate estável: pontuação,
                                                 depois número de termos casados, depois ordem da base).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .base import Base
from .texto import grafia, originais, palavras, radical, termos

PESOS = {"palavras_chave": 3, "pergunta": 2, "subtema": 1, "referencia": 1}
NEUTROS = frozenset({"fecha", "campo", "rural", "escol"})
LIMIAR_MINIMO = 3          # equivale a casar ao menos uma palavra-chave
BONUS_EXATA = 1
COBERTURA_MINIMA = 0.34    # abaixo disso: "não sei"
COBERTURA_PLENA = 0.6      # acima disso: resposta sem ressalva
FRACAO_COMUM = 0.5         # termo em mais da metade dos registros = ruído
MAX_SUGESTOES = 2


@dataclass
class Resultado:
    tipo: str                                       # "unica" | "ambigua" | "nenhuma" | "vazia"
    ids: list[str] = field(default_factory=list)    # unica: [resposta]; ambigua: as empatadas
    sugestoes: list[str] = field(default_factory=list)
    pontuacoes: dict[str, int] = field(default_factory=dict)
    cobertura: float = 0.0                          # do registro respondido (ou do 1º empatado)
    fora: list[str] = field(default_factory=list)   # palavras da pergunta que a resposta NÃO cobre


class IndiceOrientacoes:
    def __init__(self, base: Base):
        self.base = base
        self.ordem = {rid: i for i, rid in enumerate(base.registros)}
        self.indice: dict[str, dict[str, int]] = {}   # termo -> {id_registro: peso}
        self.exatas: dict[str, set[str]] = {}         # palavra inteira -> {id_registro}
        self.termos_de: dict[str, set[str]] = {}      # id_registro -> termos que ele tem
        for rid, r in base.registros.items():
            subtema = base.temas[r["tema"]]["subtemas"][r["subtema"]]
            fontes = {"palavras_chave": " ".join(r["palavras_chave"]), "pergunta": r["pergunta"], "subtema": subtema,
                      "referencia": r["referencia"]["titulo"]}
            for campo, texto in fontes.items():
                for pal in palavras(texto):
                    t = radical(pal)
                    pesos = self.indice.setdefault(t, {})
                    pesos[rid] = max(pesos.get(rid, 0), PESOS[campo])
                    self.exatas.setdefault(pal, set()).add(rid)
                    self.termos_de.setdefault(rid, set()).add(t)
        limite = FRACAO_COMUM * len(base.registros)
        self.comuns = {t for t, regs in self.indice.items() if len(regs) > limite}

    def termos_uteis(self, pergunta: str, ignorar: frozenset[str] = frozenset()) -> set[str]:
        """`ignorar`: palavras inteiras (normalizadas) que não contam, como o nome do lugar citado."""
        ign = {radical(grafia(p)) for p in ignorar}
        return set(termos(pergunta)) - self.comuns - ign

    def cobertura(self, rid: str, uteis: set[str], casados: int) -> float:
        """Fração dos termos úteis que o registro casou."""
        return casados / max(len(uteis), 1)

    def pontuar(self, pergunta: str, ignorar: frozenset[str] = frozenset()) -> dict[str, tuple[int, int]]:
        """id -> (pontuação, nº de termos casados)."""
        placar: dict[str, list[int]] = {}
        uteis = self.termos_uteis(pergunta, ignorar)
        for t in uteis:
            for rid, peso in self.indice.get(t, {}).items():
                p = placar.setdefault(rid, [0, 0])
                p[0] += peso
                p[1] += 1
        for pal in set(palavras(pergunta)):
            if radical(pal) not in uteis:
                continue
            for rid in self.exatas.get(pal, ()):
                placar[rid][0] += BONUS_EXATA
        return {rid: (p[0], p[1]) for rid, p in placar.items()}

    def buscar(self, pergunta: str, ignorar: frozenset[str] = frozenset()) -> Resultado:
        if not termos(pergunta):
            return Resultado("vazia")
        uteis = self.termos_uteis(pergunta, ignorar)
        todos = self.pontuar(pergunta, ignorar)
        cob_de = {rid: self.cobertura(rid, uteis, v[1]) for rid, v in todos.items()}
        # a cobertura mínima vale para QUEM RESPONDE; as sugestões só precisam do limiar de pontuação
        placar = {rid: v for rid, v in todos.items() if cob_de[rid] >= COBERTURA_MINIMA}
        if not placar:
            return Resultado("nenhuma")
        ordenados = sorted(placar, key=lambda rid: (-placar[rid][0], -placar[rid][1], self.ordem[rid]))
        pont = {rid: placar[rid][0] for rid in ordenados}
        topo = pont[ordenados[0]]
        if topo < LIMIAR_MINIMO:
            return Resultado("nenhuma", pontuacoes=pont)
        cob = cob_de[ordenados[0]]
        empatados = [rid for rid in ordenados if pont[rid] == topo]
        subtemas = {(self.base.registros[r]["tema"], self.base.registros[r]["subtema"]) for r in empatados}
        if len(empatados) > 1 and len(subtemas) > 1:
            return Resultado("ambigua", ids=empatados, pontuacoes=pont, cobertura=cob)
        outros = sorted((r for r in todos if r != ordenados[0] and todos[r][0] >= LIMIAR_MINIMO),
                        key=lambda r: (-todos[r][0], -todos[r][1], self.ordem[r]))
        fora = self.fora_de(pergunta, ordenados[0], ignorar) if cob < COBERTURA_PLENA else []
        return Resultado("unica", ids=[ordenados[0]], sugestoes=outros[:MAX_SUGESTOES], pontuacoes=pont,
                         cobertura=cob, fora=fora)

    def fora_de(self, pergunta: str, rid: str, ignorar: frozenset[str] = frozenset()) -> list[str]:
        """Palavras da pergunta (como a pessoa escreveu, sem repetir) que o registro não cobre."""
        tem = self.termos_de.get(rid, set())
        uteis = self.termos_uteis(pergunta, ignorar) - NEUTROS
        vistas: list[str] = []
        for pal in originais(pergunta):
            t = radical(grafia(pal))
            if t in uteis and t not in tem and pal not in vistas:
                vistas.append(pal)
        return vistas
