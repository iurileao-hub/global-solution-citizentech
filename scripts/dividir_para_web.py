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

Com --rotas-v2 (segunda passada, scripts/precalcular_rotas_v2.py), mais dois conjuntos para a camada 2:

  simulacao/LLLL.json  um por município (LLLL = linha da tabela "lugares" de nomes.json): as escolas do campo
                       do município com matrícula por etapa e até 10 receptoras SEM traçado. É tudo de que o
                       simulador "e se estas escolas fecharem?" precisa, no navegador, sem servidor: a cascata
                       percorre a lista de cada escola pulando as que também fecham. Receptora de outro
                       município não fecha na simulação (o simulador é por município).
  tracados/NNNN.json   traçado da ida de cada rota (polyline do Google, precisão 5) e trechos de chão, em
                       PEDACOS_TRACADO pedaços por código INEP. Só baixa quando a pessoa abre o mapa da escola.

Os pedaços escolas/ continuam com a rota da PRIMEIRA passada (até 4 receptoras): é o que o assistente de
terminal lê e o que o contrato data/regressao_web.json prende.

Os registros de escola saem IGUAIS aos do índice (mesmas chaves, mesmos valores): a versão web lê o mesmo
formato que o assistente de terminal, e tests/test_dados_web.py confere que juntar os pedaços devolve o índice.
O ORCAMENTO abaixo é verificado a cada geração: arquivo comprimido acima do limite faz o script falhar.

Uso:  python scripts/dividir_para_web.py [--saida site/dados] [--rotas-v2 dados/processados/rotas_v2]
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
PEDACOS_TRACADO = 2048  # ~18 escolas com rota por pedaço; ~1,4 KB comprimido por escola (amostra de 05/11)
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
    "simulacao": 60_000,       # abrir o simulador de um município
    "tracado": 60_000,         # abrir o mapa de uma escola
}
# Colunas de cada receptora em simulacao/: as mesmas chaves da segunda passada, sem o traçado (p, pc).
# m e uf só quando a receptora é de outro município ou UF (null quando é do mesmo), como na segunda passada.
COLUNAS_RECEPTORA = ["c", "n", "rural", "km", "min", "chao", "etapas", "mat", "salas", "m", "uf"]


def compacto(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")


def pedaco_de(codigo: int) -> int:
    return codigo % PEDACOS


def nome_pedaco(i: int) -> str:
    return f"escolas/{i:03d}.json"


def nome_tracado(i: int) -> str:
    return f"tracados/{i:04d}.json"


def nome_simulacao(lugar: int) -> str:
    return f"simulacao/{lugar:04d}.json"


def lugares_de(doc: dict) -> list[tuple[str, str]]:
    """Tabela (UF, município) de nomes.json, na ordem: o número da linha identifica o município."""
    return sorted({(e["uf"] or SEM_UF, e["m"] or SEM_UF) for e in doc["escolas"]})


def dividir_v2(doc_v2: dict, lugares: list[tuple[str, str]]) -> dict[str, bytes]:
    """Índice com a rota da segunda passada (gerar_retrato_rotas.aplicar_v2) -> simulacao/ e tracados/.

    Escola sem rota entra na simulação com a lista vazia e o motivo (sem coordenada, origem longe...): o
    simulador conta essas crianças como "não calculado", em vez de sumir com elas."""
    linha = {lugar: i for i, lugar in enumerate(lugares)}
    por_lugar: dict[int, list] = {}
    tracados: list[dict] = [{} for _ in range(PEDACOS_TRACADO)]
    for e in sorted(doc_v2["escolas"], key=lambda e: e["c"]):
        lugar = linha[(e["uf"] or SEM_UF, e["m"] or SEM_UF)]
        rota = e.get("rota") or {}
        rs = rota.get("receptoras") or []
        item = {"c": e["c"], "n": e["n"], "t": e["t"], "e": e["e"],
                "r": [[r["c"], r["n"], r["rural"], r["km"], r["min"], r["chao"], r["etapas"], r.get("mat"),
                       r.get("salas"), r.get("m"), r.get("uf")] for r in rs]}
        if rota.get("todas"):
            item["todas"] = True
        if not rs:
            item["motivo"] = rota.get("motivo") or ("sem_coordenada" if not e.get("geo") else "nao_calculada")
        por_lugar.setdefault(lugar, []).append(item)
        if rs:
            tracados[e["c"] % PEDACOS_TRACADO][str(e["c"])] = [[r["c"], r["p"], r.get("pc") or []] for r in rs]  # sem chão, sem pc
    arquivos = {nome_simulacao(i): compacto({"lugar": i, "uf": lugares[i][0], "municipio": lugares[i][1],
                                             "colunas_receptora": COLUNAS_RECEPTORA, "escolas": es})
                for i, es in sorted(por_lugar.items())}
    for i, t in enumerate(tracados):
        arquivos[nome_tracado(i)] = compacto({"pedaco": i, "escolas": t})
    return arquivos


def dividir(doc: dict) -> dict[str, bytes]:
    """Índice -> {caminho relativo: conteúdo}. Sem tocar em disco (o teste usa direto)."""
    arquivos: dict[str, bytes] = {}
    pedacos: list[list[dict]] = [[] for _ in range(PEDACOS)]
    for e in sorted(doc["escolas"], key=lambda e: e["c"]):
        pedacos[pedaco_de(e["c"])].append(e)
    for i, es in enumerate(pedacos):
        arquivos[nome_pedaco(i)] = compacto({"pedaco": i, "escolas": es})
    lugares = lugares_de(doc)
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
        limite = ORCAMENTO.get({"escolas": "pedaco", "simulacao": "simulacao", "tracados": "tracado"}.get(
            k.split("/")[0], k))
        if limite is not None and info["gzip"] > limite:
            saida.append(f"{k}: {info['gzip'] / 1e3:.0f} KB comprimido > orçamento de {limite / 1e3:.0f} KB")
    return saida


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--saida", type=Path, default=SAIDA)
    p.add_argument("--indice", type=Path, default=INDICE)
    p.add_argument("--rotas-v2", type=Path, help="pasta da segunda passada: gera simulacao/ e tracados/")
    a = p.parse_args(argv)
    doc = json.loads(gzip.decompress(a.indice.read_bytes()))
    arquivos = dividir(doc)
    v2 = None
    if a.rotas_v2:
        sys.path.insert(0, str(RAIZ / "scripts"))
        from gerar_retrato_rotas import aplicar_v2
        from precalcular_rotas import ler_todas
        v2 = json.loads((a.rotas_v2 / "meta.json").read_text())
        arquivos.update(dividir_v2(aplicar_v2(doc, ler_todas(a.rotas_v2)), lugares_de(doc)))
    for nome in COPIAS:
        if (DADOS / nome).exists():
            arquivos[nome] = (DADOS / nome).read_bytes()
        else:
            print(f"  aviso: data/{nome} não existe ainda; fica fora desta geração")
    man = manifesto(doc, arquivos)
    if v2:
        man["rotas_v2"] = {"k": v2["k"], "tolerancia_m": v2["tolerancia_m"], "precisao": v2["precisao"],
                           "campos": v2["campos"], "colunas_receptora": COLUNAS_RECEPTORA,
                           "pedacos_tracado": PEDACOS_TRACADO,
                           "regra_tracado": "codigo_inep % pedacos_tracado, arquivo tracados/NNNN.json com 4 dígitos",
                           "regra_simulacao": "simulacao/LLLL.json, LLLL = linha de lugares em nomes.json, 4 dígitos"}
    if a.saida.exists():
        shutil.rmtree(a.saida)  # pasta gerada: sobra de pedaço velho não pode ficar
    for k, v in {**arquivos, "manifesto.json": compacto(man)}.items():
        (a.saida / k).parent.mkdir(parents=True, exist_ok=True)
        (a.saida / k).write_bytes(v)
    gz = [v["gzip"] for k, v in man["arquivos"].items() if k.startswith("escolas/")]
    print(f"{a.saida}: {len(man['arquivos'])} arquivos | pedaço de escolas: maior {max(gz) / 1e3:.0f} KB, "
          f"média {sum(gz) / len(gz) / 1e3:.0f} KB comprimido | nomes {man['arquivos']['nomes.json']['gzip'] / 1e3:.0f} KB")
    for pasta in ("simulacao/", "tracados/") if v2 else ():
        gz = [v["gzip"] for k, v in man["arquivos"].items() if k.startswith(pasta)]
        print(f"  {pasta} {len(gz)} arquivos, maior {max(gz) / 1e3:.0f} KB, média {sum(gz) / len(gz) / 1e3:.1f} KB, "
              f"total {sum(gz) / 1e6:.1f} MB comprimido")
    problemas = estouros(man)
    for x in problemas:
        print("  ORÇAMENTO:", x)
    return 1 if problemas else 0


if __name__ == "__main__":
    sys.exit(main())
