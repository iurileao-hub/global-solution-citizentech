"""Os tipos de dado que circulam entre os módulos (separados para evitar import circular)."""

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
    etapas_cobertas: tuple[str, ...]  # quais etapas da escola de origem ela também oferece
    km_linha_reta_ida_volta: float
    km_ida_volta_piso: float | None  # None = rota não encontrada (nunca inventar)
    minutos_ida_volta_piso: float | None
    km_chao_ida_volta: float | None
    alunos_por_sala: float | None  # proxy de ocupação: matrícula / salas utilizadas (estimativa)
    aviso: str | None = None


@dataclass
class Diagnostico:
    escola: Escola
    situacao: str
    ano_referencia: int
    matriculas_por_etapa: dict[str, int]
    matricula_total: int
    moram_zona_rural: int
    usam_transporte_publico: int
    serie_matricula: dict[int, int]  # ano -> matrícula total
    tendencia: dict | None  # coeficientes, previsão e MAE/RMSE do backtest
    receptoras: list[Receptora] = field(default_factory=list)
    checklist: list[dict] = field(default_factory=list)  # item, norma, situação
    avisos: list[str] = field(default_factory=list)  # lacunas declaradas na ficha
    malha: dict = field(default_factory=dict)  # data do OSM e km por tipo de piso na área
