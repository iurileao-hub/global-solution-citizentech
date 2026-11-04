"""O que a lei pede e o que a ficha já cobre.

Normas (textos conferidos na fonte em 04/11/2026):
- LDB art. 28, parágrafo único (Lei 12.960/2014): o fechamento de escola do
  campo, indígena ou quilombola é precedido de manifestação do órgão normativo,
  que considera a justificativa da Secretaria, o diagnóstico do impacto e a
  manifestação da comunidade escolar.
- Decreto 7.352/2010, art. 1º, §1º, II: escola do campo é a situada em área
  rural OU a urbana que atende predominantemente a populações do campo.
- Res. CNE/CEB 2/2008, art. 3º: pré-escola e anos iniciais na própria comunidade.
- PL 3.091/2024 (em tramitação; aprovado na CE do Senado em 12/05/2026, na
  Câmara desde 21/05/2026): distância, função social, percurso educativo.
- Res. CME Santa Cruz do Sul/RS 03/2016 (modelo local): matrícula de 5 anos,
  mapa de distâncias, ata por segmento.

Situação de cada item: "pronto" (está na ficha), "a preencher" (depende de
pessoas) ou "a calcular" (depende de dado que não é público ou não foi processado).
"""

from __future__ import annotations

from .modelos import Diagnostico

LDB = "LDB art. 28, parágrafo único"
DECRETO = "Decreto 7.352/2010, art. 1º, §1º, II"
CNE = "Res. CNE/CEB 2/2008, art. 3º"
PL = "PL 3.091/2024, em tramitação"
CME = "CME Santa Cruz do Sul, Res. 03/2016"

ETAPAS_NA_COMUNIDADE = ("pre_escola", "anos_iniciais")


def _item(item: str, norma: str, situacao: str, detalhe: str) -> dict:
    return {"item": item, "norma": norma, "situacao": situacao, "detalhe": detalhe}


def escola_do_campo(d: Diagnostico) -> tuple[bool, str]:
    """A proteção do art. 28 se aplica? Rural, quilombola/indígena, ou urbana com maioria de alunos do campo (indício)."""
    if d.escola.rural:
        return True, "escola em área rural"
    if d.escola.localizacao_diferenciada in ("terra indígena", "comunidade quilombola"):
        return True, f"escola em {d.escola.localizacao_diferenciada}"
    if d.matricula_total and d.moram_zona_rural / d.matricula_total > 0.5:
        pct = d.moram_zona_rural / d.matricula_total
        return True, (f"escola urbana, mas {pct:.0%} dos alunos moram na zona rural: indício de que atende "
                      "predominantemente a populações do campo (o decreto fala em trabalho no meio rural, não em endereço)")
    return False, "escola urbana com maioria de alunos da zona urbana"


def avaliar(d: Diagnostico) -> list[dict]:
    com_rota = [r for r in d.receptoras if r.km_ida_volta_piso is not None]
    campo, motivo = escola_do_campo(d)
    itens = [
        _item("A lei de fechamento se aplica a esta escola (escola do campo, indígena ou quilombola)",
              DECRETO, "pronto", ("Sim: " if campo else "Não pelos dados do Censo: ") + motivo),
        _item("Justificativa da Secretaria de Educação", LDB, "a preencher", "pela Secretaria"),
        _item("Diagnóstico do impacto", LDB, "pronto", "frente desta folha"),
        _item("Manifestação da comunidade escolar", LDB, "a preencher", "item 4, na assembleia"),
        _item("Manifestação do Conselho de Educação", LDB, "a preencher", "pelo Conselho"),
        _item("Distância a ser percorrida pelos alunos realocados", PL,
              "pronto" if com_rota else "a calcular",
              "item 3, como piso" if com_rota else "rota não encontrada na malha viária pública"),
        _item("Função social da escola", PL, "a preencher", "item 4"),
        _item("Percurso educativo: onde cada aluno continua, em que etapa, com vaga", PL, "a calcular",
              "as etapas de cada receptora estão no item 3; a vaga real não é publicada"),
        _item("Matrícula dos últimos cinco anos", CME,
              "pronto" if len(d.serie_matricula) >= 5 else "a calcular",
              f"item 2 ({min(d.serie_matricula)} a {max(d.serie_matricula)})" if d.serie_matricula else "sem série"),
        _item("Mapa de distâncias até as escolas receptoras", CME,
              "pronto" if com_rota else "a calcular", "item 3"),
        _item("Ata da assembleia por segmento", CME, "a preencher", "anexar à folha"),
        _item_na_comunidade(d),
    ]
    return itens


def _item_na_comunidade(d: Diagnostico) -> dict:
    nome = "Pré-escola e anos iniciais na própria comunidade"
    criancas = sum(d.matriculas_por_etapa.get(e, 0) for e in ETAPAS_NA_COMUNIDADE)
    if criancas == 0:
        return _item(nome, CNE, "pronto", "a escola não tem essas etapas")
    rurais = [r for r in d.receptoras if r.rural and r.km_ida_volta_piso is not None
              and any(e in r.etapas_cobertas for e in ETAPAS_NA_COMUNIDADE)]
    if rurais:
        r = min(rurais, key=lambda x: x.km_ida_volta_piso)
        alt = f"a receptora rural mais próxima com essas etapas é {r.escola.nome} ({r.km_ida_volta_piso / 2:.0f} km por estrada)"
    else:
        alt = "nenhuma das receptoras próximas com essas etapas é rural"
    return _item(nome, CNE, "pronto", f"{criancas} das {d.matricula_total} crianças estão nessas etapas; {alt}")
