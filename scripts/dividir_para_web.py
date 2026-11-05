"""Divide os dados do assistente em arquivos pequenos para o navegador (camada 1): site/dados/ por padrão.

Por que dividir: o índice nacional (data/escolas_campo.json.gz) passa de 5 MB comprimido com as rotas. Num
celular com internet rural, baixar tudo para abrir UMA escola levaria minutos. Medido em 05/11 (rotas de 15
UFs): um arquivo por UF ainda daria ~800 KB no MA e na BA. Por isso as escolas vão em PEDAÇOS POR CÓDIGO:

  escolas/NNN.json   pedaço = código INEP % PEDACOS. Abrir uma escola, inclusive por link compartilhado
                     (?escola=32049501), baixa um arquivo de ~200 escolas, sem precisar de mais nada: o
                     navegador calcula o pedaço a partir do código.
  nomes.json         código, nome, município e UF de TODAS as escolas: é o que a busca por nome e a regra
                     "a pergunta nomeia uma escola" do assistente precisam. Município e UF vão numa tabela à
                     parte (cada escola guarda só o número da linha): ~20% menor que repetir os textos.
  base_orientacoes.json, fechamentos.json, retrato_rotas.json   cópias sem mudança (pequenos).
  manifesto.json     esquema, fonte, legendas dos campos, PEDACOS e o hash e o tamanho de cada arquivo. O hash
                     serve de versão: o navegador pode guardar os arquivos e só baixar de novo o que mudou.

Os registros de escola saem IGUAIS aos do índice (mesmas chaves, mesmos valores): a versão web lê o mesmo
formato que o assistente de terminal, e tests/test_dados_web.py confere que juntar os pedaços devolve o índice.
O ORCAMENTO abaixo é verificado a cada geração: arquivo comprimido acima do limite faz o script falhar.

Uso:  python scripts/dividir_para_web.py [--saida site/dados]
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DADOS = RAIZ / "data"
INDICE = DADOS / "escolas_campo.json.gz"
SAIDA = RAIZ / "site" / "dados"
COPIAS = ("base_orientacoes.json", "fechamentos.json", "retrato_rotas.json")  # o retrato só existe após o fundir
PEDACOS = 256
SEM_UF = ""  # 1 escola do índice vem sem UF/município no Censo: entra na tabela como ("", "")

# Orçamento de transferência (bytes comprimidos com gzip, que é como o GitHub Pages serve JSON).
# Referência (HIPÓTESE, não medida no campo): ~1 Mbit/s efetivo no celular rural -> 125 KB por segundo.
# Conferido em 05/11: o GitHub Pages serve JSON com content-encoding gzip.
ORCAMENTO = {
    "pedaco": 60_000,          # abrir uma escola: < 0,5 s
    "nomes.json": 800_000,     # busca por nome: < 7 s, baixado em segundo plano depois da primeira tela
    "base_orientacoes.json": 30_000,
    "fechamentos.json": 90_000,
    "retrato_rotas.json": 30_000,
}


def compacto(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def pedaco_de(codigo: int) -> int:
    return codigo % PEDACOS


def nome_pedaco(i: int) -> str:
    return f"escolas/{i:03d}.json"


def dividir(doc: dict) -> dict[str, bytes]:
    """Índice -> {caminho relativo: conteúdo}. Sem tocar em disco (o teste usa direto)."""
    arquivos: dict[str, bytes] = {}
    pedacos: list[list[dict]] = [[] for _ in range(PEDACOS)]
    for e in sorted(doc["escolas"], key=lambda e: e["c"]):
        pedacos[pedaco_de(e["c"])].append(e)
    for i, es in enumerate(pedacos):
        arquivos[nome_pedaco(i)] = compacto({"pedaco": i, "escolas": es})
    lugares = sorted({(e["uf"] or SEM_UF, e["m"] or SEM_UF) for e in doc["escolas"]})
    linha = {lugar: i for i, lugar in enumerate(lugares)}
    arquivos["nomes.json"] = compacto({
        "colunas": ["c", "n", "lugar"],
        "lugares": [list(x) for x in lugares],
        "escolas": [[e["c"], e["n"], linha[(e["uf"] or SEM_UF, e["m"] or SEM_UF)]]
                    for e in sorted(doc["escolas"], key=lambda e: e["c"])],
    })
    return arquivos


def juntar(arquivos: dict[str, bytes]) -> list[dict]:
    """O inverso de dividir() para as escolas: o que o navegador reconstruiria lendo todos os pedaços."""
    es = []
    for i in range(PEDACOS):
        es += json.loads(arquivos[nome_pedaco(i)])["escolas"]
    return sorted(es, key=lambda e: e["c"])


def manifesto(doc: dict, arquivos: dict[str, bytes]) -> dict:
    return {
        "esquema": 1,
        "fonte": doc["fonte"], "data_verificacao": doc["data_verificacao"], "criterio": doc["criterio"],
        "campos": doc["campos"], "campos_rota": doc.get("campos_rota"),
        "pedacos": PEDACOS, "regra_pedaco": "codigo_inep % pedacos, arquivo escolas/NNN.json com 3 dígitos",
        "escolas": len(doc["escolas"]),
        "arquivos": {k: {"sha256": hashlib.sha256(v).hexdigest()[:16], "bytes": len(v),
                         "gzip": len(gzip.compress(v, 9))} for k, v in sorted(arquivos.items())},
    }


def estouros(man: dict) -> list[str]:
    saida = []
    for k, info in man["arquivos"].items():
        limite = ORCAMENTO["pedaco"] if k.startswith("escolas/") else ORCAMENTO.get(k)
        if limite is not None and info["gzip"] > limite:
            saida.append(f"{k}: {info['gzip'] / 1e3:.0f} KB comprimido > orçamento de {limite / 1e3:.0f} KB")
    return saida


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--indice", type=Path, default=INDICE)
    a = p.parse_args(argv)
    doc = json.loads(gzip.decompress(a.indice.read_bytes()))
    arquivos = dividir(doc)
    for nome in COPIAS:
        if (DADOS / nome).exists():
            arquivos[nome] = (DADOS / nome).read_bytes()
        else:
            print(f"  aviso: data/{nome} não existe ainda; fica fora desta geração")
    man = manifesto(doc, arquivos)
    if a.saida.exists():
        shutil.rmtree(a.saida)  # pasta gerada: sobra de pedaço velho não pode ficar
    for k, v in {**arquivos, "manifesto.json": compacto(man)}.items():
        (a.saida / k).parent.mkdir(parents=True, exist_ok=True)
        (a.saida / k).write_bytes(v)
    gz = [v["gzip"] for k, v in man["arquivos"].items() if k.startswith("escolas/")]
    print(f"{a.saida}: {len(man['arquivos'])} arquivos | pedaço de escolas: maior {max(gz) / 1e3:.0f} KB, "
          f"média {sum(gz) / len(gz) / 1e3:.0f} KB comprimido | nomes {man['arquivos']['nomes.json']['gzip'] / 1e3:.0f} KB")
    problemas = estouros(man)
    for x in problemas:
        print("  ORÇAMENTO:", x)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
