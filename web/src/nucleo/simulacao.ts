/**
 * Simulador "e se estas escolas fecharem?": o espelho de src/assistente/simulacao.py (leia lá o porquê de cada
 * regra). O contrato data/regressao_simulacao.json confere que os dois devolvem o MESMO resultado, campo por campo.
 *
 * Regra de destino: por etapa, a mais próxima por estrada, entre as 10 receptoras pré-calculadas da escola, que
 * oferece a etapa e não fecha no plano; a indicação da prefeitura substitui a regra (se a indicada fecha ou não
 * oferece a etapa, volta à regra com aviso). A origem é sempre a escola de origem: a ordem do plano não importa.
 */

export const FAIXAS_KM: ReadonlyArray<readonly [number | null, string]> = [
  [10, "ate_10"], [30, "10_a_30"], [50, "30_a_50"], [100, "50_a_100"], [null, "100_ou_mais"],
];
export const FAIXAS_MIN: ReadonlyArray<readonly [number | null, string]> = [
  [30, "ate_30"], [60, "30_a_60"], [120, "60_a_120"], [null, "120_ou_mais"],
];
export const UFS_FLUVIAIS: ReadonlySet<string> = new Set(["AM", "PA", "AP"]);
export const ETAPAS_NA_COMUNIDADE = ["pre_escola", "anos_iniciais"] as const;
const ORDEM_ETAPAS = ["creche", "pre_escola", "anos_iniciais", "anos_finais", "medio"];
export const ESGOTADA = "lista_esgotada";
export const NENHUMA_OFERECE = "nenhuma_oferece";

/** Linha de receptora em simulacao/LLLL.json: [c, n, rural, km, min, chao, etapas, mat, salas, m, uf]. */
export type LinhaReceptora = [number, string, boolean, number, number, number | null, string[], number | null,
  number | null, string | null, string | null];

export interface EscolaSim {
  c: number;
  n: string;
  t: number;
  e: Record<string, number>;
  r: LinhaReceptora[];
  motivo?: string;
  todas?: boolean;
}

export interface Municipio {
  lugar: number;
  uf: string;
  municipio: string;
  escolas: EscolaSim[];
}

export interface Alocacao {
  origem: number;
  etapa: string;
  n: number;
  destino: number | null;
  km: number | null;
  min: number | null;
  chao: number | null;
  outro_municipio: boolean;
  indicada: boolean;
  aviso: "indicada_fecha" | "indicada_invalida" | null;
  motivo: string | null;
}

export interface Carga {
  c: number;
  n: string;
  rural: boolean;
  mat: number | null;
  salas: number | null;
  m: string | null;
  uf: string | null;
  recebe: number;
  etapas: string[];
}

export interface ResumoEscola {
  c: number;
  n: string;
  criancas: number;
  pre_iniciais: number;
  destinos: number;
  ficha: number | null;
  ficha_fecha: boolean;
  acolheria: number;
}

export interface Resultado {
  lugar: number;
  uf: string;
  municipio: string;
  fechadas: number[];
  ignoradas: number[];
  criancas: number;
  com_destino: number;
  sem_destino: Record<string, number>;
  fora_das_etapas: number;
  faixas_km: Record<string, number>;
  faixas_min: Record<string, number>;
  metade_chao: number;
  outro_municipio: number;
  ficha_fecha: number;
  aviso_fluvial: boolean;
  alocacoes: Alocacao[];
  receptoras: Carga[];
  escolas: ResumoEscola[];
}

export function faixa(valor: number, faixas: ReadonlyArray<readonly [number | null, string]>): string {
  for (const [limite, nome] of faixas) if (limite === null || valor < limite) return nome;
  throw new Error("a última faixa não tem limite");
}

const etapasDe = (e: EscolaSim) => ORDEM_ETAPAS.filter((k) => e.e[k]);
const outroMunicipio = (r: LinhaReceptora) => r[9] !== null || r[10] !== null;
const porNumero = (a: number, b: number) => a - b;

/** A receptora da manchete da ficha (regra b): a mais próxima que recebe TODAS as etapas; senão, a mais próxima. */
export function principalFicha(e: EscolaSim): number | null {
  const precisa = Object.keys(e.e);
  const todas = e.r.filter((r) => precisa.every((k) => r[6].includes(k)));
  const lista = todas.length ? todas : e.r;
  return lista.length ? lista[0][0] : null;
}

function destino(e: EscolaSim, etapa: string, fechadas: ReadonlySet<number>, indicada: number | undefined):
  [LinhaReceptora | null, string | null, Alocacao["aviso"]] {
  if (!e.r.length) return [null, e.motivo || "nao_calculada", null];
  let aviso: Alocacao["aviso"] = null;
  if (indicada !== undefined) {
    const r = e.r.find((x) => x[0] === indicada);
    if (!r || !r[6].includes(etapa)) aviso = "indicada_invalida";
    else if (fechadas.has(r[0])) aviso = "indicada_fecha";
    else return [r, null, null];
  }
  const oferecem = e.r.filter((r) => r[6].includes(etapa));
  if (!oferecem.length) return [null, NENHUMA_OFERECE, aviso];
  const aberta = oferecem.find((r) => !fechadas.has(r[0]));
  if (!aberta) return [null, ESGOTADA, aviso];
  return [aberta, null, aviso];
}

function alocar(escolas: Map<number, EscolaSim>, fechadas: ReadonlySet<number>, ind: Record<string, number>): Alocacao[] {
  const aloc: Alocacao[] = [];
  for (const c of [...fechadas].sort(porNumero)) {
    const e = escolas.get(c)!;
    for (const etapa of etapasDe(e)) {
      const i = ind[`${c}:${etapa}`];
      const [r, motivo, aviso] = destino(e, etapa, fechadas, i);
      aloc.push({
        origem: c, etapa, n: e.e[etapa],
        destino: r ? r[0] : null, km: r ? r[3] : null, min: r ? r[4] : null, chao: r ? r[5] : null,
        outro_municipio: Boolean(r && outroMunicipio(r)),
        indicada: Boolean(r && i !== undefined && aviso === null),
        aviso, motivo,
      });
    }
  }
  return aloc;
}

/** Quantas crianças de OUTRAS escolas do plano teriam cada escola fechada como destino se só ela ficasse aberta, numa
 * passada só (ver _acolheria em simulacao.py: toda fechada antes da primeira aberta que oferece a etapa, mais a
 * indicada válida que fecha; indicada válida e aberta não dá nada a ninguém). */
function acolheriaDe(escolas: Map<number, EscolaSim>, fechadas: ReadonlySet<number>, ind: Record<string, number>):
  Map<number, number> {
  const ganha = new Map<number, number>();
  for (const o of fechadas) {
    const e = escolas.get(o)!;
    for (const etapa of etapasDe(e)) {
      const candidatas = new Set<number>();
      const x = ind[`${o}:${etapa}`];
      const r = x !== undefined ? e.r.find((l) => l[0] === x) : undefined;
      if (r && r[6].includes(etapa)) {
        if (!fechadas.has(r[0])) continue;
        candidatas.add(r[0]);
      }
      for (const l of e.r) {
        if (!l[6].includes(etapa)) continue;
        if (!fechadas.has(l[0])) break;
        candidatas.add(l[0]);
      }
      candidatas.delete(o);
      for (const c of candidatas) ganha.set(c, (ganha.get(c) ?? 0) + e.e[etapa]);
    }
  }
  return ganha;
}

const soma = (o: Record<string, number>) => Object.values(o).reduce((a, b) => a + b, 0);

/** O diagnóstico do plano. `indicacoes`: {"código:etapa": código da receptora indicada pela prefeitura}. */
export function simular(mun: Municipio, fechar: Iterable<number>, indicacoes: Record<string, number> = {}): Resultado {
  const escolas = new Map(mun.escolas.map((e) => [e.c, e]));
  const pedidas = new Set(fechar);
  const fechadas = new Set([...pedidas].filter((c) => escolas.has(c)));
  const ind: Record<string, number> = {};
  for (const [k, v] of Object.entries(indicacoes)) if (fechadas.has(Number(k.split(":")[0]))) ind[k] = v;
  const aloc = alocar(escolas, fechadas, ind);

  const sem: Record<string, number> = {};
  const fk = Object.fromEntries(FAIXAS_KM.map(([, n]) => [n, 0])) as Record<string, number>;
  const fm = Object.fromEntries(FAIXAS_MIN.map(([, n]) => [n, 0])) as Record<string, number>;
  let metadeChao = 0;
  let outro = 0;
  const carga = new Map<number, Carga>();
  for (const a of aloc) {
    if (a.destino === null) {
      sem[a.motivo!] = (sem[a.motivo!] ?? 0) + a.n;
      continue;
    }
    fk[faixa(a.km!, FAIXAS_KM)] += a.n;
    fm[faixa(a.min!, FAIXAS_MIN)] += a.n;
    if (a.km! > 0 && (a.chao ?? 0) / a.km! >= 0.5) metadeChao += a.n;
    if (a.outro_municipio) outro += a.n;
    let x = carga.get(a.destino);
    if (!x) {
      const r = escolas.get(a.origem)!.r.find((l) => l[0] === a.destino)!;
      x = { c: r[0], n: r[1], rural: r[2], mat: r[7], salas: r[8], m: r[9], uf: r[10], recebe: 0, etapas: [] };
      carga.set(a.destino, x);
    }
    x.recebe += a.n;
    if (!x.etapas.includes(a.etapa)) x.etapas.push(a.etapa);
  }
  for (const x of carga.values()) x.etapas = ORDEM_ETAPAS.filter((k) => x.etapas.includes(k));

  const acolheria = acolheriaDe(escolas, fechadas, ind);
  const resumo: ResumoEscola[] = [...fechadas].sort(porNumero).map((c) => {
    const e = escolas.get(c)!;
    const mesmas = aloc.filter((a) => a.origem === c);
    const p = principalFicha(e);
    return {
      c, n: e.n, criancas: soma(e.e),
      pre_iniciais: ETAPAS_NA_COMUNIDADE.reduce((s, k) => s + (e.e[k] ?? 0), 0),
      destinos: new Set(mesmas.filter((a) => a.destino !== null).map((a) => a.destino)).size,
      ficha: p, ficha_fecha: p !== null && fechadas.has(p), acolheria: acolheria.get(c) ?? 0,
    };
  });

  const criancas = aloc.reduce((s, a) => s + a.n, 0);
  return {
    lugar: mun.lugar, uf: mun.uf, municipio: mun.municipio,
    fechadas: [...fechadas].sort(porNumero),
    ignoradas: [...pedidas].filter((c) => !fechadas.has(c)).sort(porNumero),
    criancas,
    com_destino: criancas - soma(sem),
    sem_destino: Object.fromEntries(Object.entries(sem).sort(([a], [b]) => (a < b ? -1 : 1))),
    fora_das_etapas: [...fechadas].reduce((s, c) => s + Math.max(0, escolas.get(c)!.t - soma(escolas.get(c)!.e)), 0),
    faixas_km: fk, faixas_min: fm, metade_chao: metadeChao, outro_municipio: outro,
    ficha_fecha: resumo.filter((x) => x.ficha_fecha).reduce((s, x) => s + x.criancas, 0),
    aviso_fluvial: UFS_FLUVIAIS.has(mun.uf),
    alocacoes: aloc,
    receptoras: [...carga.values()].sort((a, b) => b.recebe - a.recebe || a.c - b.c),
    escolas: resumo,
  };
}

/** O atalho "todas as escolas do município com menos de N alunos" (o total do Censo, todas as etapas). */
export function menoresQue(mun: Municipio, alunos: number): number[] {
  return mun.escolas.filter((e) => e.t < alunos).map((e) => e.c).sort(porNumero);
}

/** Cenário no link: f=código,código & i=código:etapa:receptora,... (curto o bastante para o WhatsApp). */
export function lerCenario(params: URLSearchParams): { fechar: number[]; indicacoes: Record<string, number> } {
  const fechar = (params.get("f") ?? "").split(",").map(Number).filter((n) => Number.isInteger(n) && n > 0);
  const indicacoes: Record<string, number> = {};
  for (const x of (params.get("i") ?? "").split(",").filter(Boolean)) {
    const [c, etapa, r] = x.split(":");
    if (/^\d+$/.test(c ?? "") && ORDEM_ETAPAS.includes(etapa ?? "") && /^\d+$/.test(r ?? "")) {
      indicacoes[`${c}:${etapa}`] = Number(r);
    }
  }
  return { fechar: [...new Set(fechar)].sort(porNumero), indicacoes };
}

export function escreverCenario(fechar: Iterable<number>, indicacoes: Record<string, number>): string {
  const f = [...new Set(fechar)].sort(porNumero);
  const i = Object.entries(indicacoes).filter(([k]) => f.includes(Number(k.split(":")[0])))
    .sort(([a], [b]) => (a < b ? -1 : 1)).map(([k, v]) => `${k}:${v}`);
  const p = new URLSearchParams();
  if (f.length) p.set("f", f.join(","));
  if (i.length) p.set("i", i.join(","));
  return p.toString().replace(/%2C/g, ",").replace(/%3A/g, ":");
}
