"""Gera data/regressao_web.json: o que o núcleo Python responde às 130 perguntas rotuladas e a buscas de escola.

É o CONTRATO da versão web: qualquer implementação da busca no navegador (o mesmo Python rodando lá, ou a busca
reescrita em JavaScript) tem de devolver, para cada pergunta, o mesmo tipo de resposta, as mesmas orientações
na mesma ordem e o mesmo texto. Sem isso, a web daria respostas diferentes das que foram medidas e rotuladas.

O que vai para cada pergunta:
  - o gabarito dos juízes ("esperado" ou "esperado_tipo") e a classificação que o núcleo Python obteve hoje;
  - a resposta do Python no modelo B (o padrão): tipo, ids, escolas, aviso de parcial e o texto com os
    espaços normalizados. A quebra de linha a 72 colunas é coisa do terminal: na web o navegador quebra a linha,
    então o contrato compara as palavras, não a diagramação.
Mais as buscas de escola por nome e código (a caixa de busca da web), com a lista completa de códigos.

"insumos" guarda o hash dos arquivos de dados: tests/test_regressao.py refaz tudo em memória e falha se o arquivo
ficou velho (base, números de fechamento ou índice mudaram e ninguém regenerou). Depois do `fundir` das rotas, as
respostas de escola mudam (a ficha passa a listar receptoras): é só rodar este script de novo.

Uso:  python scripts/exportar_regressao.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from assistente import base as base_mod  # noqa: E402
from assistente import escolas as escolas_mod  # noqa: E402
from assistente import fechamentos as fech_mod  # noqa: E402
from assistente.avaliacao import classificar  # noqa: E402
from assistente.nucleo import montar, responder  # noqa: E402
from assistente.texto import normalizar  # noqa: E402

DADOS = RAIZ / "data"
SAIDA = DADOS / "regressao_web.json"
CONJUNTOS = (("equipe", "perguntas_teste.json"), ("cegas", "perguntas_cegas.json"), ("r3", "perguntas_r3.json"))
ARQ_BASE, ARQ_FECH, ARQ_ESCOLAS = (DADOS / n for n in ("base_orientacoes.json", "fechamentos.json",
                                                       "escolas_campo.json.gz"))
MODELO = "B"
# Buscas de escola: as 5 da avaliação (linear x índice) + casos de borda que a tela da web também terá.
BUSCAS_ESCOLA = (
    {"consulta": "Durval Maximo"}, {"consulta": "Escola Municipal Sao Jose"}, {"consulta": "Santo Antonio"},
    {"consulta": "Rui Barbosa"}, {"consulta": "Quilombo"},
    {"consulta": "durval máximo"},                       # minúscula e acento
    {"consulta": "32049501"},                            # código INEP
    {"consulta": "escola municipal"},                    # só palavras genéricas
    {"consulta": "zzqx"},                                # nada
    {"consulta": "Sao Jose", "municipio": "Muniz Freire", "uf": "ES"},  # filtro que zera a lista
    {"consulta": "Sao Jose", "uf": "ES"},
    {"consulta": "Santo Antonio", "uf": "ba"},
)


def sha256(arq: Path) -> str:
    return hashlib.sha256(arq.read_bytes()).hexdigest()


def contexto():
    return montar(base_mod.carregar(ARQ_BASE), escolas_mod.carregar(ARQ_ESCOLAS), fech_mod.carregar(ARQ_FECH))


def gabarito(p: dict) -> dict:
    return {k: p[k] for k in ("esperado", "esperado_tipo", "esperado_escola") if k in p}


def gerar() -> dict:
    ctx = contexto()
    perguntas = []
    for conjunto, arq in CONJUNTOS:
        for p in json.loads((DADOS / arq).read_text(encoding="utf-8"))["perguntas"]:
            r = responder(ctx, p["pergunta"], MODELO)
            perguntas.append({
                "conjunto": conjunto, "id": p["id"], "pergunta": p["pergunta"], "gabarito": gabarito(p),
                "classificacao_python": classificar(p, r),
                "resposta": {"tipo": r.tipo, "ids": r.ids, "escolas": r.escolas, "parcial": r.parcial,
                             "texto": " ".join(r.texto.split())},
            })
    escolas = []
    for b in BUSCAS_ESCOLA:
        achado = ctx.escolas.buscar(b["consulta"], b.get("municipio", ""), b.get("uf", ""))
        escolas.append({**b, "tipo": achado["tipo"], "total": achado.get("total", len(achado.get("escolas", []))),
                        "codigos": [e["c"] for e in achado.get("escolas", [])]})
    return {
        "esquema": 1,
        "descricao": __doc__.splitlines()[0],
        "modelo": MODELO,
        "insumos": {a.name: sha256(a) for a in (ARQ_BASE, ARQ_FECH, ARQ_ESCOLAS)}
                   | {arq: sha256(DADOS / arq) for _, arq in CONJUNTOS},
        "perguntas": perguntas,
        "buscas_escola": escolas,
        "normalizacao": normalizacao(ctx),
    }


BLOCO_NORMALIZACAO = 1000


def normalizacao(ctx) -> dict:
    """Hash de normalizar() aplicado ao nome e ao município de cada escola, em blocos de BLOCO_NORMALIZACAO escolas
    na ordem do índice. A versão web refaz a conta com a sua normalização: bloco com hash diferente aponta onde
    as duas divergem (acento, cedilha, caractere raro) sem guardar 53 mil nomes no contrato."""
    nomes = [f"{normalizar(e['n'] or '')}|{normalizar(e['m'] or '')}" for e in ctx.escolas.doc["escolas"]]
    blocos = [nomes[i:i + BLOCO_NORMALIZACAO] for i in range(0, len(nomes), BLOCO_NORMALIZACAO)]
    return {"descricao": "sha256 de normalizar(nome)|normalizar(município), uma escola por linha, por bloco",
            "escolas": len(nomes), "por_bloco": BLOCO_NORMALIZACAO,
            "hashes": [hashlib.sha256("\n".join(b).encode("utf-8")).hexdigest() for b in blocos]}


def main() -> None:
    doc = gerar()
    SAIDA.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cont: dict = {}
    for p in doc["perguntas"]:
        cont[p["classificacao_python"]] = cont.get(p["classificacao_python"], 0) + 1
    print(f"{SAIDA.name}: {len(doc['perguntas'])} perguntas {cont} | {len(doc['buscas_escola'])} buscas de escola | "
          f"{SAIDA.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()
