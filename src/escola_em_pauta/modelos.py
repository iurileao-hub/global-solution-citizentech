"""Os tipos de dado que circulam entre os módulos (separados para evitar import circular).

Também define o CONTRATO DE DADOS: `Diagnostico.to_dict()` / `Diagnostico.from_dict()`. O mesmo
JSON alimenta as três camadas (assistente de terminal offline, site estático, servidor), então
este módulo só usa a biblioteca padrão: quem lê o JSON não precisa de pandas nem de numpy.

Regras do formato (versão `ESQUEMA_VERSAO`):
  - chaves de dict são sempre texto (JSON não tem chave inteira): `serie_matricula`,
    `perfil["por_ano_escolar"]` e `tendencia["backtest"]["previsto_*"]` saem como "2019", "1"...
    e `from_dict` as devolve como int;
  - tuplas viram listas (`etapas_cobertas`, `tendencia["primeiro"/"ultimo"]`) e voltam como tupla;
  - NaN e infinito viram null (JSON não os tem; `json.dumps(..., allow_nan=False)` passa);
  - escalares do numpy (int64, float64, bool_) viram int/float/bool do Python.
Mudou o formato de um jeito que um leitor antigo leria errado? Suba `ESQUEMA_VERSAO`.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field


# Prefixo do aviso de rota quando a ESCOLA DE ORIGEM está longe da estrada mapeada: vale para todas
# as receptoras, então a ficha o mostra uma vez no quadro "Atenção" (rota.py escreve, diagnostico/ficha leem).
ORIGEM_LONGE = "a escola de origem fica a"
SEM_ROTA = "rota não encontrada na malha do OpenStreetMap"

# Versão do formato serializado. `from_dict` recusa qualquer outra (melhor falhar alto que ler errado).
ESQUEMA_VERSAO = 1


def _puro(x, caminho: str = "diagnostico"):
    """Converte recursivamente para tipos que o `json` da stdlib aceita sem ajuda.

    Reconhece o numpy por duck typing (módulo do tipo + método `.item()`), sem importá-lo.
    Tipo desconhecido levanta TypeError com o caminho do campo: falha alta, nunca dado torto.
    """
    if x is None or isinstance(x, (str, bool)):
        return x
    if type(x).__module__ == "numpy" and hasattr(x, "item"):  # np.int64, np.float64, np.bool_
        return _puro(x.item(), caminho)
    if isinstance(x, int):
        return int(x)
    if isinstance(x, float):
        return float(x) if math.isfinite(x) else None  # NaN/inf não existem em JSON
    if isinstance(x, dict):
        return {_chave(k, caminho): _puro(v, f"{caminho}.{k}") for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_puro(v, f"{caminho}[{i}]") for i, v in enumerate(x)]
    raise TypeError(f"{caminho}: tipo {type(x).__module__}.{type(x).__name__} não serializável")


def _chave(k, caminho: str) -> str:
    if isinstance(k, str):
        return k
    if type(k).__module__ == "numpy" and hasattr(k, "item"):
        k = k.item()
    if isinstance(k, int) and not isinstance(k, bool):
        return str(k)
    raise TypeError(f"{caminho}: chave {k!r} ({type(k).__name__}) não serializável")


def _chaves_int(d: dict | None) -> dict | None:
    return None if d is None else {int(k): v for k, v in d.items()}

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

    def to_dict(self) -> dict:
        return _puro(asdict(self), "escola")

    @classmethod
    def from_dict(cls, d: dict) -> Escola:
        return cls(**d)


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

    def to_dict(self) -> dict:
        return _puro(asdict(self), "receptora")

    @classmethod
    def from_dict(cls, d: dict) -> Receptora:
        campos = dict(d)
        campos["escola"] = Escola.from_dict(campos["escola"])
        campos["etapas_cobertas"] = tuple(campos["etapas_cobertas"])
        return cls(**campos)


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
    perfil: dict = field(default_factory=dict)  # rede, matrícula por ano escolar, professores, salas, infraestrutura
    referencia_externa: dict | None = None  # estimativa/medição externa conhecida (ex.: TCE), linha de referência

    def to_dict(self) -> dict:
        """Dict só com str/int/float/bool/None/list/dict, pronto para `json.dumps(..., allow_nan=False)`."""
        return {"esquema": ESQUEMA_VERSAO, **_puro(asdict(self))}

    @classmethod
    def from_dict(cls, d: dict) -> Diagnostico:
        """Inverso de `to_dict`, aceitando o dict que sai de `json.loads` (chaves texto, listas)."""
        versao = d.get("esquema")
        if type(versao) is not int or versao != ESQUEMA_VERSAO:  # `type`: True == 1 em Python
            raise ValueError(f"Esquema do diagnóstico {versao!r} desconhecido; este código lê a versão "
                             f"{ESQUEMA_VERSAO}. Gere o JSON de novo ou atualize o programa.")
        campos = {k: v for k, v in d.items() if k != "esquema"}
        campos["escola"] = Escola.from_dict(campos["escola"])
        campos["receptoras"] = [Receptora.from_dict(r) for r in campos.get("receptoras", [])]
        campos["serie_matricula"] = _chaves_int(campos["serie_matricula"])
        campos["tendencia"] = _tendencia_de_json(campos.get("tendencia"))
        perfil = dict(campos.get("perfil") or {})
        if "por_ano_escolar" in perfil:
            perfil["por_ano_escolar"] = _chaves_int(perfil["por_ano_escolar"])
        campos["perfil"] = perfil
        return cls(**campos)


def _tendencia_de_json(t: dict | None) -> dict | None:
    """Desfaz o que o JSON muda em `tendencia.ajustar()`: tuplas (ano, matrícula) e anos como chave."""
    if t is None:
        return None
    t = dict(t)
    for k in ("primeiro", "ultimo"):
        if t.get(k) is not None:
            t[k] = tuple(t[k])
    if t.get("backtest") is not None:
        bt = dict(t["backtest"])
        for k in ("previsto_reta", "previsto_base"):
            if k in bt:
                bt[k] = _chaves_int(bt[k])
        t["backtest"] = bt
    return t
