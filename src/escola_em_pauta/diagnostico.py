"""O coração do Escola em Pauta: uma função que diagnostica UMA escola.

`diagnosticar(codigo_inep)` não sabe se está rodando num laço (v1: gerador de
site estático para os territórios de demonstração) ou num servidor (v2:
qualquer escola do Brasil, calculada na hora). Essa separação entre a lógica
("o quê") e a entrega ("onde") é o que permite à v2 ser um acréscimo e não uma
reescrita.

Unidade de saída: a CRIANÇA (quantas são afetadas, quantos km e minutos a
mais), nunca o custo por aluno. Distâncias são PISO ("pelo menos"), porque o
cálculo vai de escola a escola e não conhece a casa de cada criança nem a
estrada na chuva (ver docs/discussao/2026-11-04-passos-5-6.md).
"""

from __future__ import annotations

from .modelos import Diagnostico, Escola, Receptora

__all__ = ["Diagnostico", "Escola", "Receptora", "diagnosticar"]


def diagnosticar(codigo_inep: int, k: int = 6) -> Diagnostico:
    """Monta o diagnóstico completo de uma escola.

    Passos (cada um num módulo próprio):
      1. censo.escola_e_serie(codigo)        -> matrículas, etapas, transporte, série
      2. geo.coordenada(codigo)              -> coordenada (Ipea); sem ela, sem rota (aviso)
      3. receptoras.candidatas(escola, k)    -> mesmas etapas, pré-filtro em linha reta, rota real
         (rota.piso: Dijkstra no grafo OSM com velocidade de ônibus por superfície)
      4. tendencia.ajustar(serie)            -> descrição da série + backtest contra linha de base
      5. checklist.avaliar(diagnostico)      -> LDB 28, Decreto 7.352, CNE/CEB 2/2008, PL 3.091, CME Santa Cruz

    Levanta KeyError se a escola não for pública ou não estiver no Censo mais recente.
    """
    from . import censo, checklist, receptoras, tendencia

    info, serie = censo.escola_e_serie(codigo_inep)
    escola = receptoras.escola(codigo_inep)
    avisos: list[str] = []
    if info["situacao"] != "ativa":
        avisos.append(f"No Censo {info['ano_referencia']} a escola consta como {info['situacao']}.")

    etapas = list(info["matriculas_por_etapa"])
    lista, g = ([], None)
    if escola.lat is None:
        avisos.append("Escola sem coordenada na base do Ipea: distâncias não calculadas (plano B: geocodificar o endereço).")
    elif not etapas:
        avisos.append("Escola sem matrícula no ano de referência: não há receptoras a calcular.")
    else:
        lista, g = receptoras.candidatas(escola, etapas, k=k)
        if not any(r.km_ida_volta_piso is not None for r in lista):
            avisos.append("Nenhuma rota encontrada na malha do OpenStreetMap; a linha reta aparece como limite inferior.")

    d = Diagnostico(
        escola=escola,
        situacao=info["situacao"],
        ano_referencia=info["ano_referencia"],
        matriculas_por_etapa=info["matriculas_por_etapa"],
        matricula_total=info["matricula_total"],
        moram_zona_rural=info["moram_zona_rural"],
        usam_transporte_publico=info["usam_transporte_publico"],
        serie_matricula=serie,
        tendencia=tendencia.ajustar(serie),
        receptoras=lista,
        avisos=avisos,
        malha={"data_osm": g.data_osm, "km_por_piso": g.km_por_piso} if g else {},
    )
    d.checklist = checklist.avaliar(d)
    return d
