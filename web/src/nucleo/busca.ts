/**
 * Busca de orientações: índice invertido com pontuação por peso do campo. Reescrita de src/assistente/busca.py,
 * onde estão a explicação de cada regra e o histórico dos ajustes (pesos, cobertura, termos neutros).
 *
 * Resumo: cada termo (radical) aponta para os registros onde aparece, com o peso do campo (palavras-chave 3,
 * pergunta modelo 2, subtema 1, título da norma 1), mais 1 de bônus por palavra que casa inteira. A COBERTURA
 * (fração dos termos da pergunta que o registro casou) decide entre responder, responder avisando o que ficou de
 * fora, ou dizer "não sei".
 */

import type { Base } from "./base";
import { grafia, originais, palavras, radical, termos } from "./texto";

const PESOS = { palavras_chave: 3, pergunta: 2, subtema: 1, referencia: 1 } as const;
export const NEUTROS: ReadonlySet<string> = new Set(["fecha", "campo", "rural", "escol"]);
export const LIMIAR_MINIMO = 3;
const BONUS_EXATA = 1;
export const COBERTURA_MINIMA = 0.34;
export const COBERTURA_PLENA = 0.6;
const FRACAO_COMUM = 0.5;
const MAX_SUGESTOES = 2;

export type TipoResultado = "unica" | "ambigua" | "nenhuma" | "vazia";

export interface Resultado {
  tipo: TipoResultado;
  ids: string[];
  sugestoes: string[];
  /** id -> pontuação, na ordem do ranking (Map guarda a ordem, como o dict do Python). */
  pontuacoes: Map<string, number>;
  cobertura: number;
  fora: string[];
}

export function resultado(tipo: TipoResultado, extra: Partial<Resultado> = {}): Resultado {
  return { tipo, ids: [], sugestoes: [], pontuacoes: new Map(), cobertura: 0, fora: [], ...extra };
}

const VAZIO: ReadonlySet<string> = new Set();

export class IndiceOrientacoes {
  readonly ordem = new Map<string, number>();
  readonly indice = new Map<string, Map<string, number>>(); // termo -> {id: peso}
  readonly exatas = new Map<string, Set<string>>(); // palavra inteira -> {id}
  readonly termosDe = new Map<string, Set<string>>(); // id -> termos que ele tem
  readonly comuns: Set<string>;

  constructor(readonly base: Base) {
    let i = 0;
    for (const [rid, r] of base.registros) {
      this.ordem.set(rid, i++);
      const subtema = base.temas[r.tema].subtemas[r.subtema];
      const fontes: [keyof typeof PESOS, string][] = [
        ["palavras_chave", r.palavras_chave.join(" ")], ["pergunta", r.pergunta], ["subtema", subtema],
        ["referencia", r.referencia.titulo],
      ];
      for (const [campo, texto] of fontes) {
        for (const pal of palavras(texto)) {
          const t = radical(pal);
          let pesos = this.indice.get(t);
          if (!pesos) this.indice.set(t, (pesos = new Map()));
          pesos.set(rid, Math.max(pesos.get(rid) ?? 0, PESOS[campo]));
          let ex = this.exatas.get(pal);
          if (!ex) this.exatas.set(pal, (ex = new Set()));
          ex.add(rid);
          let td = this.termosDe.get(rid);
          if (!td) this.termosDe.set(rid, (td = new Set()));
          td.add(t);
        }
      }
    }
    const limite = FRACAO_COMUM * base.registros.size;
    this.comuns = new Set([...this.indice].filter(([, regs]) => regs.size > limite).map(([t]) => t));
  }

  /** `ignorar`: palavras inteiras (normalizadas) que não contam, como o nome do lugar citado. */
  termosUteis(pergunta: string, ignorar: ReadonlySet<string> = VAZIO): Set<string> {
    const ign = new Set([...ignorar].map((p) => radical(grafia(p))));
    return new Set(termos(pergunta).filter((t) => !this.comuns.has(t) && !ign.has(t)));
  }

  /** id -> [pontuação, nº de termos casados]. */
  pontuar(pergunta: string, ignorar: ReadonlySet<string> = VAZIO): Map<string, [number, number]> {
    const placar = new Map<string, [number, number]>();
    const uteis = this.termosUteis(pergunta, ignorar);
    for (const t of uteis) {
      for (const [rid, peso] of this.indice.get(t) ?? []) {
        let p = placar.get(rid);
        if (!p) placar.set(rid, (p = [0, 0]));
        p[0] += peso;
        p[1] += 1;
      }
    }
    for (const pal of new Set(palavras(pergunta))) {
      if (!uteis.has(radical(pal))) continue;
      for (const rid of this.exatas.get(pal) ?? []) placar.get(rid)![0] += BONUS_EXATA;
    }
    return placar;
  }

  private ranking(placar: Map<string, [number, number]>, ids: Iterable<string>): string[] {
    return [...ids].sort((a, b) => {
      const [pa, ca] = placar.get(a)!;
      const [pb, cb] = placar.get(b)!;
      return pb - pa || cb - ca || this.ordem.get(a)! - this.ordem.get(b)!;
    });
  }

  buscar(pergunta: string, ignorar: ReadonlySet<string> = VAZIO): Resultado {
    if (termos(pergunta).length === 0) return resultado("vazia");
    const uteis = this.termosUteis(pergunta, ignorar);
    const todos = this.pontuar(pergunta, ignorar);
    const cobDe = new Map<string, number>();
    for (const [rid, v] of todos) cobDe.set(rid, v[1] / Math.max(uteis.size, 1));
    // a cobertura mínima vale para QUEM RESPONDE; as sugestões só precisam do limiar de pontuação
    const elegiveis = [...todos.keys()].filter((rid) => cobDe.get(rid)! >= COBERTURA_MINIMA);
    if (elegiveis.length === 0) return resultado("nenhuma");
    const ordenados = this.ranking(todos, elegiveis);
    const pont = new Map(ordenados.map((rid) => [rid, todos.get(rid)![0]] as [string, number]));
    const topo = pont.get(ordenados[0])!;
    if (topo < LIMIAR_MINIMO) return resultado("nenhuma", { pontuacoes: pont });
    const cob = cobDe.get(ordenados[0])!;
    const empatados = ordenados.filter((rid) => pont.get(rid) === topo);
    const subtemas = new Set(empatados.map((r) => {
      const reg = this.base.registros.get(r)!;
      return `${reg.tema}\u0000${reg.subtema}`;
    }));
    if (empatados.length > 1 && subtemas.size > 1) {
      return resultado("ambigua", { ids: empatados, pontuacoes: pont, cobertura: cob });
    }
    const outros = this.ranking(todos, [...todos.keys()].filter(
      (r) => r !== ordenados[0] && todos.get(r)![0] >= LIMIAR_MINIMO,
    ));
    const fora = cob < COBERTURA_PLENA ? this.foraDe(pergunta, ordenados[0], ignorar) : [];
    return resultado("unica", {
      ids: [ordenados[0]], sugestoes: outros.slice(0, MAX_SUGESTOES), pontuacoes: pont, cobertura: cob, fora,
    });
  }

  /** Palavras da pergunta (como a pessoa escreveu, sem repetir) que o registro não cobre. */
  foraDe(pergunta: string, rid: string, ignorar: ReadonlySet<string> = VAZIO): string[] {
    const temTermo = this.termosDe.get(rid) ?? new Set<string>();
    const uteis = this.termosUteis(pergunta, ignorar);
    for (const n of NEUTROS) uteis.delete(n);
    const vistas: string[] = [];
    for (const pal of originais(pergunta)) {
      const t = radical(grafia(pal));
      if (uteis.has(t) && !temTermo.has(t) && !vistas.includes(pal)) vistas.push(pal);
    }
    return vistas;
  }
}
