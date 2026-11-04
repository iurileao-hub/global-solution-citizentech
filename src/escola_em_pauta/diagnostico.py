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

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Escola:
    codigo_inep: int
    nome: str
    municipio: str
    uf: str
    rural: bool
    localizacao_diferenciada: str | None  # quilombola, indígena, assentamento
    lat: float | None
    lon: float | None
    precisao_coordenada: str  # "ipea_geobr", "geocodificada_endereco", "ausente"


@dataclass(frozen=True)
class Receptora:
    escola: Escola
    rural: bool
    km_ida_volta_piso: float | None  # None = rota não encontrada (nunca inventar)
    minutos_ida_volta_piso: float | None
    ocupacao_estimada: str  # proxy: matrícula / salas; rotulado como estimativa


@dataclass
class Diagnostico:
    escola: Escola
    ano_referencia: int
    matriculas_por_etapa: dict[str, int]
    moram_zona_rural: int
    usam_transporte_publico: int
    serie_matricula: dict[int, int]  # ano -> matrícula total
    tendencia: dict | None  # coeficientes, previsão e MAE/RMSE do backtest
    receptoras: list[Receptora] = field(default_factory=list)
    checklist: list[dict] = field(default_factory=list)  # item, norma, situação
    avisos: list[str] = field(default_factory=list)  # lacunas declaradas na ficha


def diagnosticar(codigo_inep: int) -> Diagnostico:
    """Monta o diagnóstico completo de uma escola.

    Ordem prevista (cada passo num módulo próprio):
      1. censo.escola_e_serie(codigo)        -> matrículas, etapas, transporte, série
      2. geo.coordenada(codigo)              -> coordenada (Ipea) ou geocodificação
      3. receptoras.candidatas(escola, k=6)  -> mesmas etapas, mais próximas em linha reta
      4. rota.piso(origem, destino)          -> Dijkstra no grafo OSM com velocidade por piso
      5. tendencia.ajustar(serie)            -> regressão + backtest
      6. checklist.avaliar(diagnostico)      -> LDB 28, PL 3.091/2024, Res. CNE/CEB 2/2008, CME Santa Cruz
    """
    raise NotImplementedError("Implementação começa na próxima sessão (ver docs/HANDOFF.md).")
