"""Busca de orientações: índice invertido com pontuação por peso do campo.

ÍNDICE INVERTIDO é o índice remissivo de um livro: para cada termo (radical), a lista dos
registros onde ele aparece. Montá-lo custa uma passada na base; depois, cada pergunta só olha
os registros que têm algum termo dela, em vez de comparar com todos.

PONTUAÇÃO de um registro para uma pergunta = soma, para cada termo DISTINTO da pergunta, do maior
peso em que esse termo aparece no registro:
    palavras-chave = 3   (vocabulário escolhido de propósito, inclusive sinônimos populares)
    pergunta modelo = 2
    nome do subtema = 1
  + BONUS_EXATA por palavra que casa INTEIRA (não só pelo radical): "quilombola" casa inteira com
    a orientação sobre escolas quilombolas e só pelo radical com a que fala de "quilômetros".
Termos que aparecem em mais da metade dos registros ("escol", por exemplo) não distinguem nada e
são ignorados.

COBERTURA de um registro = fração dos termos da pergunta que ele casou. Abaixo de COBERTURA_MINIMA,
uma palavra solta estaria decidindo a resposta ("melhor escola particular da CIDADE" casava só
"cidade" com a orientação sobre escola na cidade): o registro é descartado.

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
from .texto import palavras, radical, termos

PESOS = {"palavras_chave": 3, "pergunta": 2, "subtema": 1}
LIMIAR_MINIMO = 3          # equivale a casar ao menos uma palavra-chave
BONUS_EXATA = 1
COBERTURA_MINIMA = 0.4     # ajustada nas perguntas de teste (limitação declarada no README)
FRACAO_COMUM = 0.5         # termo em mais da metade dos registros = ruído
MAX_SUGESTOES = 2


@dataclass
class Resultado:
    tipo: str                                       # "unica" | "ambigua" | "nenhuma" | "vazia"
    ids: list[str] = field(default_factory=list)    # unica: [resposta]; ambigua: as empatadas
    sugestoes: list[str] = field(default_factory=list)
    pontuacoes: dict[str, int] = field(default_factory=dict)
    cobertura: float = 0.0                          # do registro respondido (ou do 1º empatado)


class IndiceOrientacoes:
    def __init__(self, base: Base):
        self.base = base
        self.ordem = {rid: i for i, rid in enumerate(base.registros)}
        self.indice: dict[str, dict[str, int]] = {}   # termo -> {id_registro: peso}
        self.exatas: dict[str, set[str]] = {}         # palavra inteira -> {id_registro}
        for rid, r in base.registros.items():
            subtema = base.temas[r["tema"]]["subtemas"][r["subtema"]]
            fontes = {"palavras_chave": " ".join(r["palavras_chave"]), "pergunta": r["pergunta"], "subtema": subtema}
            for campo, texto in fontes.items():
                for pal in palavras(texto):
                    t = radical(pal)
                    pesos = self.indice.setdefault(t, {})
                    pesos[rid] = max(pesos.get(rid, 0), PESOS[campo])
                    self.exatas.setdefault(pal, set()).add(rid)
        limite = FRACAO_COMUM * len(base.registros)
        self.comuns = {t for t, regs in self.indice.items() if len(regs) > limite}

    def termos_uteis(self, pergunta: str) -> set[str]:
        return set(termos(pergunta)) - self.comuns

    def pontuar(self, pergunta: str) -> dict[str, tuple[int, int]]:
        """id -> (pontuação, nº de termos casados)."""
        placar: dict[str, list[int]] = {}
        for t in self.termos_uteis(pergunta):
            for rid, peso in self.indice.get(t, {}).items():
                p = placar.setdefault(rid, [0, 0])
                p[0] += peso
                p[1] += 1
        for pal in set(palavras(pergunta)):
            if radical(pal) in self.comuns:
                continue
            for rid in self.exatas.get(pal, ()):
                placar[rid][0] += BONUS_EXATA
        return {rid: (p[0], p[1]) for rid, p in placar.items()}

    def buscar(self, pergunta: str) -> Resultado:
        if not termos(pergunta):
            return Resultado("vazia")
        n_termos = len(self.termos_uteis(pergunta)) or 1
        placar = {rid: v for rid, v in self.pontuar(pergunta).items() if v[1] / n_termos >= COBERTURA_MINIMA}
        if not placar:
            return Resultado("nenhuma")
        ordenados = sorted(placar, key=lambda rid: (-placar[rid][0], -placar[rid][1], self.ordem[rid]))
        pont = {rid: placar[rid][0] for rid in ordenados}
        topo = pont[ordenados[0]]
        if topo < LIMIAR_MINIMO:
            return Resultado("nenhuma", pontuacoes=pont)
        cob = placar[ordenados[0]][1] / n_termos
        empatados = [rid for rid in ordenados if pont[rid] == topo]
        subtemas = {(self.base.registros[r]["tema"], self.base.registros[r]["subtema"]) for r in empatados}
        if len(empatados) > 1 and len(subtemas) > 1:
            return Resultado("ambigua", ids=empatados, pontuacoes=pont, cobertura=cob)
        resto = [rid for rid in ordenados[1:] if pont[rid] >= LIMIAR_MINIMO][:MAX_SUGESTOES]
        return Resultado("unica", ids=[ordenados[0]], sugestoes=resto, pontuacoes=pont, cobertura=cob)
