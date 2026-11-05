"""Pré-cálculo das rotas de todas as escolas do campo (etapa 4 do plano de 05/11/2026).

POR QUE PRÉ-CALCULAR
Calcular a rota de uma escola "na hora", com a malha fora do cache, custou 107 s e 4,6 GB de RAM
(medido em 05/11), e quase tudo isso é UMA passada pelo recorte regional do OpenStreetMap (PBF).
A passada custa praticamente o mesmo para 1 área ou para 100, porque `osm_local.extrair` recorta
muitas áreas de uma vez. Então o caminho barato é: agrupar as escolas, extrair as malhas de um
grupo inteiro numa passada, e depois rodar `diagnosticar` escola por escola com a malha pronta.

O QUE ESTE SCRIPT FAZ, POR UF (regiões na ordem SE -> S -> CO -> NE -> N)
1. Planeja: para cada escola com coordenada, calcula a área (bbox) que `diagnosticar` vai precisar,
   com AS MESMAS funções que ele usa (pré-filtro em linha reta + margem de 5 km). As escolas são
   agrupadas por célula de grade de 0,25 grau (~28 km); a área da célula é a UNIÃO das áreas das
   suas escolas, então contém cada uma delas por construção.
2. Extrai, em lotes de células: uma passada no PBF por lote. Para a passada ficar mais leve,
   usamos um PBF "só com vias" gerado uma vez por região (`osm_local.pbf_so_vias`).
3. Diagnostica: escola por escola, célula por célula, passando o grafo da célula pronto
   (`diagnosticar(..., grafo_area=g)`): cada grafo é construído uma vez só.
4. Resume e grava: uma linha JSON por escola em dados/processados/rotas/<UF>.jsonl, escrita e
   sincronizada com o disco (fsync) na hora. Se o processo cair de madrugada, perde-se no máximo
   a escola que estava em curso; rodar de novo continua de onde parou (RETOMADA).
5. `fundir` junta todos os .jsonl no índice data/escolas_campo.json.gz (campo "rota"), que o
   assistente de terminal lê só com a biblioteca padrão.

Uma escola que falha (exceção) vira uma linha com "erro" e o lote segue: uma escola nunca derruba
as outras. Interromper com Ctrl+C é seguro pelo mesmo motivo.

O RESUMO NUNCA INVENTA NÚMERO
Só entram receptoras com rota calculada na malha (km "piso": pelo menos isso). Quando nenhuma tem
rota, o resumo leva lista vazia e um aviso que diz o porquê (escola longe da estrada mapeada,
malha sem caminho, nenhuma candidata a 60 km), e nunca uma linha reta disfarçada de estrada.

USO (de dentro do repo, com o .venv ativo; nice -n 19 = prioridade mínima de CPU)
  nice -n 19 python scripts/precalcular_rotas.py rodar                  # o país todo, retomável
  nice -n 19 python scripts/precalcular_rotas.py rodar --ufs ES MG      # só algumas UFs
  python scripts/precalcular_rotas.py rodar --ufs AM PA --amostra 30 --dir dados/processados/rotas_amostra
  python scripts/precalcular_rotas.py status [--dir ...]               # contagens, tempos, motivos
  python scripts/precalcular_rotas.py fundir                            # grava as rotas no índice
"""

from __future__ import annotations

import argparse
import gzip
import inspect
import json
import math
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

INDICE = RAIZ / "data" / "escolas_campo.json.gz"
DIR_ROTAS = RAIZ / "dados" / "processados" / "rotas"
CACHE_CELULAS = RAIZ / "dados" / "processados" / "osm_celulas"  # separado do cache do site (ver _celula_em_cache)

ORDEM_REGIOES = ("sudeste", "sul", "centro-oeste", "nordeste", "norte")
CELULA = 0.25  # graus; o mesmo passo de site.preparar_malhas
CELULAS_POR_LOTE = 60  # ES inteiro em 05/11: pico de 2,4 GB de RAM com 60 por lote; --celulas-por-lote muda
MAX_RECEPTORAS = 4  # no resumo; a ficha completa (site/servidor) continua mostrando até 6
ESQUEMA_ROTA = 1

# UFs em que a falta de rota por estrada é, na maior parte, sinal de transporte FLUVIAL. PROPOSTA
# medida em 05/11/2026 (amostras sorteadas, semente 7), a confirmar por Iúri:
#   sem rota por estrada: AM 14/15, PA 8/15, AP 3/10 | AC 2/10, RO 2/10, TO 1/10, RR 0/10
#   controles: MA 2/15, BA 1/15, ES 1/928 (o estado inteiro)
# Critério: UF com 30% ou mais da amostra sem rota. Abaixo disso a taxa se parece com a dos controles,
# e o aviso genérico ("estrada não mapeada") é o honesto. Em todas as UFs vale a regra maior: sem rota
# calculada, nenhum número aparece. Amostras pequenas (10 a 15 por UF): rever com o lote completo.
UFS_FLUVIAIS = frozenset({"AM", "PA", "AP"})

AVISOS = {
    "origem_longe": "A escola fica a {acesso} km da estrada mapeada mais próxima no OpenStreetMap, "
                    "então não há rota por estrada calculada.",
    "sem_rota": "A malha do OpenStreetMap não liga esta escola por estrada às escolas próximas que "
                "poderiam receber os alunos, então não há rota calculada.",
    "sem_candidata": "Não há escola pública ativa com as mesmas etapas a até {raio} km em linha reta.",
    "sem_matricula": "A escola não tem matrícula no ano de referência: não há receptoras a calcular.",
    "sem_coordenada": "A escola não tem coordenada pública (Catálogo de Escolas do INEP e base do Ipea): não há rota calculada.",
}
AVISO_FLUVIAL = "Rota por estrada não se aplica ou estrada não mapeada; o transporte pode ser fluvial."
NOTA_FLUVIAL = ("Nesta região parte do transporte escolar é fluvial: a rota por estrada pode não ser o "
                "caminho que as crianças fazem.")


# ----------------------------------------------------------------------------------------------
# Resumo compacto (o que vai para o índice nacional)
# ----------------------------------------------------------------------------------------------
def resumir(d, max_receptoras: int = MAX_RECEPTORAS) -> dict:
    """Projeta um Diagnostico num dict pequeno, só com tipos JSON (str/int/float/bool/None/list/dict).

    Campos curtos porque se repetem ~50 mil vezes no índice. Legenda em CAMPOS_ROTA.
    """
    from escola_em_pauta.modelos import ORIGEM_LONGE
    from escola_em_pauta.receptoras import RAIO_MAX_KM

    com_rota = [r for r in d.receptoras if r.km_ida_volta_piso is not None]
    saida: dict = {"v": ESQUEMA_ROTA, "receptoras": []}
    for r in com_rota[:max_receptoras]:
        x = {"c": int(r.escola.codigo_inep), "n": str(r.escola.nome),
             "rural": bool(r.rural), "km": round(float(r.km_ida_volta_piso), 1),
             "min": round(float(r.minutos_ida_volta_piso)),
             "chao": round(float(r.km_chao_ida_volta or 0.0), 1),
             "etapas": [str(e) for e in r.etapas_cobertas]}
        if (r.escola.municipio, r.escola.uf) != (d.escola.municipio, d.escola.uf):
            x["m"] = str(r.escola.municipio)  # só quando é OUTRO município (economiza ~15% do índice)
        if r.escola.uf != d.escola.uf:
            x["uf"] = str(r.escola.uf)
        saida["receptoras"].append(x)
    sem = len(d.receptoras) - len(com_rota)
    if sem:
        saida["sem_rota"] = sem  # candidatas próximas que ficaram sem rota (não entram na lista)
    if d.malha.get("data_osm"):
        saida["osm"] = str(d.malha["data_osm"])[:10]
    if com_rota and d.escola.uf in UFS_FLUVIAIS:
        saida["aviso"] = NOTA_FLUVIAL  # há estrada, mas o barco pode ser o caminho real: dizer, sem tirar o número
    if not com_rota:
        if d.escola.lat is None:
            motivo = "sem_coordenada"
        elif not d.matriculas_por_etapa:
            motivo = "sem_matricula"
        elif not d.receptoras:
            motivo = "sem_candidata"
        elif any(r.aviso and r.aviso.startswith(ORIGEM_LONGE) for r in d.receptoras):
            motivo = "origem_longe"
            achado = next(re.search(r"([\d]+,?\d*) km", r.aviso) for r in d.receptoras
                          if r.aviso and r.aviso.startswith(ORIGEM_LONGE))
            saida["acesso_km"] = float(achado.group(1).replace(",", ".")) if achado else None
        else:
            motivo = "sem_rota"
        saida["motivo"] = motivo
        saida["aviso"] = aviso(motivo, d.escola.uf, saida.get("acesso_km"), RAIO_MAX_KM)
    return saida


def aviso(motivo: str, uf: str, acesso_km: float | None = None, raio: float = 60.0) -> str:
    """Texto curto para o assistente. No Norte, sem rota por estrada costuma querer dizer barco."""
    if motivo in ("origem_longe", "sem_rota") and uf in UFS_FLUVIAIS:
        return AVISO_FLUVIAL
    acesso = "?" if acesso_km is None else f"{acesso_km:.1f}".replace(".", ",")
    return AVISOS[motivo].format(acesso=acesso, raio=f"{raio:.0f}")


CAMPOS_ROTA = {
    "v": "versão do formato do resumo de rota",
    "receptoras": "até 4 escolas que poderiam receber os alunos, com rota na malha, da mais perto à mais longe",
    "receptoras[].c/n/m/uf": "código INEP, nome; município e UF só quando diferem dos da escola de origem",
    "receptoras[].rural": "a receptora é rural",
    "receptoras[].km": "km de estrada por dia, ida e volta, de escola a escola: PISO (pelo menos isso)",
    "receptoras[].min": "minutos por dia, ida e volta, com velocidade de ônibus escolar: PISO",
    "receptoras[].chao": "quantos desses km são estrada sem pavimento (marcada no OSM)",
    "receptoras[].etapas": "quais etapas da escola de origem a receptora também oferece",
    "sem_rota": "quantas candidatas próximas ficaram sem rota calculada (não entram na lista)",
    "osm": "data da malha do OpenStreetMap (Geofabrik)",
    "motivo/aviso": "por que não há nenhuma rota (origem_longe, sem_rota, sem_candidata, sem_matricula); "
                    "com rota, aviso = nota sobre transporte fluvial nas UFs da Amazônia",
    "acesso_km": "distância da escola à estrada mapeada mais próxima, quando é o motivo",
}


# ----------------------------------------------------------------------------------------------
# Arquivo de progresso (uma linha JSON por escola; retomável)
# ----------------------------------------------------------------------------------------------
def abrir_progresso(arq: Path, aparar: bool = True) -> dict[int, dict]:
    """Escolas já processadas neste arquivo: {código: última linha}.

    Se o processo morreu no meio de uma escrita, a última linha fica cortada (sem o "\\n" final).
    Ela é descartada, e o arquivo é aparado até a última linha completa: sem isso, a próxima linha
    gravada grudaria no pedaço quebrado e as duas se perderiam.

    aparar=False é a leitura de CONSULTA (status, fundir, retrato): só ignora a linha cortada, sem mexer no
    arquivo. Quem só lê pode estar lendo enquanto o lote grava: uma linha da segunda passada passa de 8 KB e
    pode chegar ao disco em mais de uma escrita; aparar nesse instante apagaria o começo da linha que o lote
    está terminando de escrever. Só a retomada (rodar_uf, com o lote parado nesta UF) apara.
    """
    if not arq.exists():
        return {}
    bruto = arq.read_bytes()
    if bruto and not bruto.endswith(b"\n"):
        corte = bruto.rfind(b"\n") + 1
        if aparar:
            with open(arq, "r+b") as f:
                f.truncate(corte)
        bruto = bruto[:corte]
    feitos: dict[int, dict] = {}
    for linha in bruto.decode("utf-8").splitlines():
        try:
            x = json.loads(linha)
            feitos[int(x["c"])] = x  # se a escola aparece duas vezes (refeita), vale a última
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return feitos


def gravar(f, linha: dict) -> None:
    """Acrescenta uma linha e força a ida ao disco (flush + fsync): a garantia da retomada."""
    f.write(json.dumps(linha, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
    f.flush()
    os.fsync(f.fileno())


# ----------------------------------------------------------------------------------------------
# Planejamento: que área cada escola vai pedir, e células de grade
# ----------------------------------------------------------------------------------------------
def area_da_escola(codigo: int, pre_filtro: int | None = None) -> tuple[float, float, float, float] | None:
    """A bbox que receptoras.candidatas vai montar para esta escola, ou None se não houver rota a fazer.

    Usa as mesmas funções e os MESMOS parâmetros padrão de candidatas (lidos da assinatura dela,
    para não divergir em silêncio se alguém mudar o pré-filtro). A segunda passada
    (precalcular_rotas_v2.py) passa o pré-filtro dela, maior.
    """
    from escola_em_pauta import censo, grafo, receptoras

    info, _ = censo.escola_e_serie(codigo)
    e = receptoras.escola(codigo)
    etapas = list(info["matriculas_por_etapa"])
    if e.lat is None or not etapas:
        return None
    n = pre_filtro or inspect.signature(receptoras.candidatas).parameters["pre_filtro"].default
    perto = receptoras.pre_filtrar(e, etapas, n)
    if perto.empty:
        return None
    return grafo.bbox_ao_redor([(e.lat, e.lon)] + list(zip(perto["lat"], perto["lon"])))


def celula_de(lat: float, lon: float) -> tuple[int, int]:
    """Célula de grade (índices inteiros) onde a escola está."""
    return (math.floor(lat / CELULA), math.floor(lon / CELULA))


def uniao(bboxes: list[tuple]) -> tuple[float, float, float, float]:
    return (min(b[0] for b in bboxes), min(b[1] for b in bboxes), max(b[2] for b in bboxes), max(b[3] for b in bboxes))


def contem(fora: tuple, dentro: tuple) -> bool:
    return fora[0] <= dentro[0] and fora[1] <= dentro[1] and fora[2] >= dentro[2] and fora[3] >= dentro[3]


def _arquivo_da_celula(bbox: tuple, cache: Path) -> Path:
    s, o, n, l = bbox
    return cache / f"{s:.3f}_{o:.3f}_{n:.3f}_{l:.3f}.json.gz"  # o mesmo nome que osm_local.extrair grava


def _celula_em_cache(bbox: tuple, cache: Path) -> bool:
    """Procuramos a malha EXATA da célula (pelo nome), num diretório só nosso.

    Por que não o cache do site (dados/processados/osm)? Lá a busca é "a menor malha que contém a
    área", e cada consulta lista o diretório inteiro: com milhares de células, o site ficaria lento
    e as escolas de uma célula poderiam pegar malhas diferentes umas das outras.
    """
    return _arquivo_da_celula(bbox, cache).exists()


# ----------------------------------------------------------------------------------------------
# Execução
# ----------------------------------------------------------------------------------------------
def _log(msg: str) -> None:
    print(time.strftime("%H:%M:%S"), msg, file=sys.stderr, flush=True)


def carregar_indice(caminho: Path = INDICE) -> dict:
    with gzip.open(caminho, "rt", encoding="utf-8") as f:
        return json.load(f)


def ufs_em_ordem(doc: dict, ufs: list[str] | None) -> list[str]:
    from escola_em_pauta.osm_local import REGIAO_POR_UF

    presentes = {e["uf"] for e in doc["escolas"]}
    ordem = [uf for reg in ORDEM_REGIOES for uf in sorted(u for u, r in REGIAO_POR_UF.items() if r == reg)]
    if ufs:
        desconhecidas = set(ufs) - set(ordem)
        if desconhecidas:
            raise SystemExit(f"UF desconhecida: {', '.join(sorted(desconhecidas))}")
        ordem = [u for u in ordem if u in ufs]
    return [u for u in ordem if u in presentes]


def processar_escola(codigo: int, uf: str, g=None) -> dict:
    """Diagnostica uma escola e devolve a linha do arquivo de progresso. NUNCA levanta exceção comum."""
    from escola_em_pauta.diagnostico import diagnosticar

    t0 = time.perf_counter()
    try:
        d = diagnosticar(codigo, grafo_area=g)
        return {"c": codigo, "uf": uf, "rota": resumir(d), "s": round(time.perf_counter() - t0, 2)}
    except Exception as e:  # noqa: BLE001  (uma escola com problema não derruba o lote)
        return {"c": codigo, "uf": uf, "erro": f"{type(e).__name__}: {e}"[:300], "s": round(time.perf_counter() - t0, 2)}


def rodar_uf(uf: str, codigos: list[int], arq: Path, celulas_por_lote: int, cache: Path = CACHE_CELULAS,
             processar=processar_escola, refazer_erros: bool = False, area=None) -> Counter:
    """Processa as escolas de uma UF que ainda não estão no arquivo de progresso.

    Com refazer_erros, as que falharam antes entram de novo (útil depois de corrigir um defeito);
    a linha nova é acrescentada e, na leitura, a última linha de cada escola é a que vale.
    `processar` e `area` são trocados pela segunda passada (precalcular_rotas_v2.py).
    """
    from escola_em_pauta import grafo, osm_local

    area = area or area_da_escola  # resolvido na chamada (os testes trocam area_da_escola no módulo)
    cont: Counter = Counter()
    arq.parent.mkdir(parents=True, exist_ok=True)
    feitos = abrir_progresso(arq)
    pendentes = [c for c in codigos if c not in feitos or (refazer_erros and "erro" in feitos[c])]
    cont["ja_feitas"] = len(codigos) - len(pendentes)
    if not pendentes:
        _log(f"{uf}: {len(codigos)} escolas, todas já feitas")
        return cont
    _log(f"{uf}: {len(pendentes)} escolas a fazer ({cont['ja_feitas']} já feitas); planejando áreas...")

    from escola_em_pauta import receptoras

    por_celula: dict[tuple[int, int], list[tuple[int, tuple]]] = {}
    sem_area: list[int] = []
    with open(arq, "a", encoding="utf-8") as f:
        for c in pendentes:
            try:
                b = area(c)
            except Exception:  # noqa: BLE001  (o diagnóstico vai registrar o erro com a mensagem)
                b = None
            if b is None:
                sem_area.append(c)
                continue
            e = receptoras.escola(c)
            por_celula.setdefault(celula_de(e.lat, e.lon), []).append((c, b))
        # Escolas sem área (sem coordenada, sem matrícula, nenhuma candidata a 60 km) não precisam
        # de malha: o diagnóstico é rápido e já diz o motivo.
        for c in sem_area:
            linha = processar(c, uf)
            gravar(f, linha)
            cont["erro" if "erro" in linha else "ok"] += 1

        pbf = osm_local.pbf_da_uf(uf)
        celulas = sorted(por_celula)
        if celulas and pbf is None:
            _log(f"{uf}: AVISO, recorte da Geofabrik ausente; {sum(len(v) for v in por_celula.values())} escolas adiadas")
            cont["adiadas"] += sum(len(v) for v in por_celula.values())
            return cont
        n_lotes = math.ceil(len(celulas) / celulas_por_lote) if celulas else 0
        for i in range(n_lotes):
            lote = celulas[i * celulas_por_lote:(i + 1) * celulas_por_lote]
            areas = {cel: uniao([b for _, b in por_celula[cel]]) for cel in lote}
            faltam = [b for b in areas.values() if not _celula_em_cache(b, cache)]
            t0 = time.perf_counter()
            if faltam:
                osm_local.extrair(osm_local.pbf_so_vias(pbf), faltam, cache)
            t_ext = time.perf_counter() - t0
            t1, n_esc = time.perf_counter(), 0
            for cel in lote:
                arq_malha = _arquivo_da_celula(areas[cel], cache)
                try:
                    with gzip.open(arq_malha, "rt") as fm:
                        g = grafo.construir(json.load(fm))
                except Exception as e:  # noqa: BLE001
                    for c, _ in por_celula[cel]:
                        gravar(f, {"c": c, "uf": uf, "erro": f"malha da célula: {type(e).__name__}: {e}"[:300]})
                        cont["erro"] += 1
                    continue
                for c, b in por_celula[cel]:
                    if contem(areas[cel], b):  # sempre, por construção (união); senão é bug do planejamento
                        linha = processar(c, uf, g)
                    else:
                        linha = {"c": c, "uf": uf, "erro": "área da escola fora da malha da célula (bug)"}
                    gravar(f, linha)
                    cont["erro" if "erro" in linha else "ok"] += 1
                    n_esc += 1
                del g
            _log(f"{uf} lote {i + 1}/{n_lotes}: {len(lote)} células ({len(faltam)} extraídas em {t_ext:.0f} s), "
                 f"{n_esc} escolas em {time.perf_counter() - t1:.0f} s")
    return cont


def cmd_rodar(a) -> None:
    doc = carregar_indice()
    dir_rotas = Path(a.dir)
    total: Counter = Counter()
    t0 = time.perf_counter()
    for uf in ufs_em_ordem(doc, a.ufs):
        codigos = sorted(e["c"] for e in doc["escolas"] if e["uf"] == uf and e["geo"])
        if a.amostra:
            codigos = sorted(random.Random(a.semente).sample(codigos, min(a.amostra, len(codigos))))
        if a.limite:
            codigos = codigos[:a.limite]
        total += rodar_uf(uf, codigos, dir_rotas / f"{uf}.jsonl", a.celulas_por_lote, refazer_erros=a.refazer_erros)
    _log(f"fim: {dict(total)} em {time.perf_counter() - t0:.0f} s")


def ler_todas(dir_rotas: Path) -> dict[int, dict]:
    """Todas as linhas da pasta, só para leitura (não apara: pode rodar com o lote gravando)."""
    linhas: dict[int, dict] = {}
    for arq in sorted(dir_rotas.glob("*.jsonl")):
        linhas.update(abrir_progresso(arq, aparar=False))
    return linhas


def cmd_status(a) -> None:
    linhas = ler_todas(Path(a.dir))
    por_uf: dict[str, Counter] = {}
    for x in linhas.values():
        c = por_uf.setdefault(x["uf"], Counter())
        c["escolas"] += 1
        c["s"] += x.get("s", 0)
        if "erro" in x:
            c["erro"] += 1
        elif x["rota"]["receptoras"]:
            c["com_rota"] += 1
        else:
            c[x["rota"]["motivo"]] += 1
    for uf, c in por_uf.items():
        n = c.pop("escolas")
        s = c.pop("s")
        print(f"{uf}: {n} escolas, {s / n:.2f} s/escola no diagnóstico | " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))


def rederivar_aviso(rota: dict, uf: str) -> dict:
    """Recalcula o aviso a partir do motivo e da UF, com as regras ATUAIS (UFS_FLUVIAIS, AVISOS).

    O aviso é texto derivado; o que foi caro de calcular (as rotas) não depende dele. Assim, mudar o
    critério fluvial ou a redação exige só um novo `fundir`, nunca recalcular as rotas.
    """
    from escola_em_pauta.receptoras import RAIO_MAX_KM  # import local, como no cálculo (carrega pandas)

    rota = dict(rota)
    if rota.get("motivo"):
        rota["aviso"] = aviso(rota["motivo"], uf, rota.get("acesso_km"), RAIO_MAX_KM)
    elif rota.get("receptoras") and uf in UFS_FLUVIAIS:
        rota["aviso"] = NOTA_FLUVIAL
    else:
        rota.pop("aviso", None)
    return rota


def fundir(indice: Path = INDICE, dir_rotas: Path = DIR_ROTAS) -> Counter:
    """Grava o resumo de cada escola processada no campo "rota" do índice nacional.

    Escola com erro ou ainda não processada fica como estava (null = "ainda não calculada").
    O gzip sai com mtime=0: mesmo conteúdo, mesmo arquivo byte a byte (o git não vê mudança falsa).
    """
    doc = carregar_indice(indice)
    linhas = ler_todas(dir_rotas)
    cont: Counter = Counter()
    for e in doc["escolas"]:
        x = linhas.get(e["c"])
        if x is None:
            cont["sem_linha"] += 1
        elif "erro" in x:
            cont["erro"] += 1
        else:
            e["rota"] = rederivar_aviso(x["rota"], e.get("uf") or "")
            cont["com_rota" if x["rota"]["receptoras"] else "sem_rota_com_aviso"] += 1
    doc["campos"]["rota"] = ("resumo das receptoras com rota calculada (preenchido pelo pré-cálculo, "
                             "scripts/precalcular_rotas.py) ou null")
    doc["campos_rota"] = CAMPOS_ROTA
    bruto = json.dumps(doc, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
    tmp = indice.with_name(indice.name + ".parcial")
    tmp.write_bytes(gzip.compress(bruto, mtime=0))
    os.replace(tmp, indice)  # troca atômica: o índice nunca fica pela metade
    return cont


def cmd_fundir(a) -> None:
    cont = fundir(dir_rotas=Path(a.dir))
    print(f"índice atualizado: {dict(cont)} | {INDICE.stat().st_size / 1e6:.1f} MB")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rodar", help="calcula as rotas (retomável)")
    r.add_argument("--ufs", nargs="+", help="só estas UFs (padrão: todas, SE -> S -> CO -> NE -> N)")
    r.add_argument("--limite", type=int, help="no máximo N escolas por UF (as de menor código)")
    r.add_argument("--amostra", type=int, help="N escolas sorteadas por UF")
    r.add_argument("--semente", type=int, default=1)
    r.add_argument("--celulas-por-lote", type=int, default=CELULAS_POR_LOTE,
                   help="células de grade extraídas por passada no PBF (menos = menos RAM, mais passadas)")
    r.add_argument("--refazer-erros", action="store_true", help="tenta de novo as escolas que falharam")
    for s in (r, sub.add_parser("status", help="resumo do progresso"), sub.add_parser("fundir", help="grava no índice")):
        s.add_argument("--dir", default=str(DIR_ROTAS), help="diretório dos .jsonl de progresso")
    a = p.parse_args(argv)
    {"rodar": cmd_rodar, "status": cmd_status, "fundir": cmd_fundir}[a.cmd](a)


if __name__ == "__main__":
    main()
