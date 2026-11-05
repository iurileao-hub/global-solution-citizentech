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

Dois ajustes vieram da 3ª rodada de teste (uma persona dita as perguntas no celular):
  - GRAFIA: "x" vira "ch" antes do radical, nos DOIS lados (base e pergunta). O ditado escreve "fexar",
    e "fexar" e "fechar" passam a ser a mesma palavra. Como a troca vale para a base também, ela não
    cria erro novo: "exige" vira "echige" na base e na pergunta, e as duas continuam iguais.
  - SIGLA FALADA: "elê dê bê" vira "ldb". Só as siglas do tema, numa lista fechada: juntar qualquer
    sequência de letras faria "o que é que a" virar sigla.
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
obrigada obrigado obg viu ta to favor gostaria ainda tipo exemplo algumas alguns alguem cada todo toda
todos todas foram existe existem desde querer pergunta sou estou somos neto neta netos netas sobrinho sobrinha
""".split())

# sigla do tema dita letra a letra (o reconhecimento de voz escreve "elê dê bê")
SIGLAS_FALADAS = {
    "ele de be": "ldb", "e ce a": "eca", "ce ene e": "cne", "eme e ce": "mec", "eme pe efe": "mpf",
    "eme pe": "mp", "esse i ce": "sic", "ele a i": "lai", "efe ene de e": "fnde", "pe ene a e": "pnae",
    "i ene e pe": "inep", "pe ele": "pl",
}
# número por extenso (menu e código falado: "dois", "ce um")
NUMEROS = {"zero": 0, "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "quatro": 4, "cinco": 5,
           "seis": 6, "sete": 7, "oito": 8, "nove": 9}
LETRA_DE_CODIGO = {"de": "D", "d": "D", "ce": "C", "c": "C", "te": "T", "t": "T", "efe": "F", "f": "F"}


def codigo_falado(texto: str) -> str | None:
    """"ce um" -> "C1"; "dê quatro" -> "D4". Só quando o texto é exatamente letra + número."""
    partes = normalizar(texto).split()
    if len(partes) != 2 or partes[0] not in LETRA_DE_CODIGO:
        return None
    num = partes[1] if partes[1].isdigit() else str(NUMEROS.get(partes[1], ""))
    return LETRA_DE_CODIGO[partes[0]] + num if num else None


def grafia(p: str) -> str:
    return p.replace("x", "ch")


def _siglas(t: str) -> str:
    t = f" {t} "
    for falada, sigla in sorted(SIGLAS_FALADAS.items(), key=lambda kv: -len(kv[0])):
        t = t.replace(f" {falada} ", f" {sigla} ")
    return t.strip()


def normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras/números separados por um espaço."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(re.findall(r"[a-z0-9]+", sem_acento.lower()))


def radical(palavra: str) -> str:
    return palavra[:TAMANHO_RADICAL]


def palavras(texto: str) -> list[str]:
    """Palavras inteiras que importam (sem radical, já com a grafia unificada): servem para premiar o
    casamento EXATO."""
    return [grafia(p) for p in originais(texto)]


def originais(texto: str) -> list[str]:
    """As mesmas palavras, como a pessoa escreveu (sem acento): é o que se MOSTRA a ela."""
    return [p for p in _siglas(normalizar(texto)).split() if _conta(p)]


def _conta(p: str) -> bool:
    # números ("25", "2024") quase nunca dizem o ASSUNTO; o código "D1" é tratado antes da busca
    return p not in PALAVRAS_VAZIAS and len(p) > 1 and not p.isdigit()


def termos(texto: str) -> list[str]:
    """Radicais das palavras que importam, na ordem em que aparecem (com repetição)."""
    return [radical(p) for p in palavras(texto)]
