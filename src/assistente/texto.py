"""Normalização de texto: o primeiro passo de qualquer busca.

A pessoa escreve "Fechamento", "fecharam" ou "FECHAR"; a base diz "fechar". Para o computador
comparar, todos viram a mesma forma:
  1. minúsculas e sem acento ("Município" -> "municipio");
  2. só letras e números (pontuação vira espaço);
  3. sem palavras vazias ("de", "a", "que"...), que aparecem em toda frase e não distinguem nada;
  4. RADICAL de até 5 letras ("fechamento", "fecharam" e "fechar" -> "fecha").

O radical é um corte grosseiro, escolhido por ser simples e explicável. Ele junta palavras da
mesma família (bom) e às vezes junta palavras diferentes que começam igual: "quilombola" e
"quilômetros" -> "quilo"; "particular" e "participar" -> "parti" (achado no primeiro teste).
Por isso a busca dá um BÔNUS à palavra exata: o radical acha a família, a palavra inteira desempata.
"""

from __future__ import annotations

import re
import unicodedata

TAMANHO_RADICAL = 5

PALAVRAS_VAZIAS = frozenset("""
a o as os um uma uns umas de da do das dos em na no nas nos por pela pelo pelas pelos para pra pro
com sem sob sobre e ou mas se que qual quais quando como onde quem cujo ja nao sim mais menos muito
meu minha meus minhas seu sua seus suas nosso nossa nossos nossas ele ela eles elas eu voce voces gente
isso isto esse essa este esta aquele aquela ser estar ter ha tem foi vai vou sao era sera esta estao
me te lhe nos vos ao aos à às la le lo ai entao tambem so ate apos antes depois agora aqui ali
pode podem gente mesmo coisa alguma algum algo quero queria saber sei dizer diz quer
posso podemos poder precisa precisam preciso deve devem devia feita feito acontece acontecer aconteceu
forem for fosse outra outro outras outros vao tinha adianta ne oi ola bom dia boa tarde noite
""".split())


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras/números separados por um espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.findall(r"[a-z0-9]+", sem_acento.lower()))


def radical(palavra: str) -> str:
    return palavra[:TAMANHO_RADICAL]


def palavras(texto: str) -> list[str]:
    """Palavras inteiras que importam (sem radical): servem para premiar o casamento EXATO."""
    return [p for p in normalizar(texto).split() if _conta(p)]


def _conta(p: str) -> bool:
    # números ("25", "2024") quase nunca dizem o ASSUNTO; o código "D1" é tratado antes da busca
    return p not in PALAVRAS_VAZIAS and len(p) > 1 and not p.isdigit()


def termos(texto: str) -> list[str]:
    """Radicais das palavras que importam, na ordem em que aparecem (com repetição)."""
    return [radical(p) for p in palavras(texto)]
