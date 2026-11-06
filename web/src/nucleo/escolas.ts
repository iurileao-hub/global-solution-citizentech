/**
 * Busca de escolas por nome ou código INEP. Reescrita de src/assistente/escolas.py.
 *
 * Índice invertido palavra -> códigos; a resposta é a INTERSEÇÃO dos conjuntos das palavras digitadas, a partir
 * do menor. Palavras genéricas de nome de escola ("escola", "municipal", "EMEF") são ignoradas. Nome próprio se
 * compara inteiro, sem radical: "Rui" não pode casar com "Ruiz".
 *
 * Na web a lista de nomes (nomes.json) traz só código, nome, município e UF. O resto da ficha vem do pedaço da
 * escola, baixado quando ela é aberta. Por isso o índice aceita qualquer registro que tenha esses quatro campos.
 */

import { ehNumero, normalizar } from "./texto";

const CONECTIVOS: ReadonlySet<string> = new Set("de da do das dos e".split(" "));
const GENERICAS: ReadonlySet<string> = new Set(
  `escola escolas municipal estadual federal emef emeif emei eef eeef eeefm eeem eem ee em ef ce cef cem ceef
colegio centro educacional ensino fundamental medio infantil basica rural unidade nucleo creche
pre integral tempo pm prof professor professora dr dona`.split(/\s+/),
);
export const UFS: ReadonlySet<string> = new Set(
  "ac al ap am ba ce df es go ma mt ms mg pa pb pr pe pi rj rn rs ro rr sc sp se to".split(" "),
);

export interface EscolaNome {
  c: number;
  n: string | null;
  m: string | null;
  uf: string | null;
}

export type TipoBuscaEscola = "codigo" | "unica" | "ambigua" | "nenhuma" | "vazia";

export interface AchadoEscolas<E extends EscolaNome = EscolaNome> {
  tipo: TipoBuscaEscola;
  escolas: E[];
  total: number;
  nomeELugar?: boolean;
}

export function palavrasNome(texto: string): string[] {
  return normalizar(texto).split(" ").filter((p) => p && !GENERICAS.has(p) && !CONECTIVOS.has(p));
}

/** Comparação de texto como a do Python (por ponto de código), sem regras de idioma. */
function cmp(a: string, b: string): number {
  return a < b ? -1 : a > b ? 1 : 0;
}

/** Desempate de nomes repetidos: por município (trecho do nome, sem acento) e/ou UF. */
export function filtrar<E extends EscolaNome>(escolas: E[], municipio = "", uf = ""): E[] {
  const m = normalizar(municipio);
  const u = uf.trim().toLowerCase();
  const saida = escolas.filter((e) =>
    (!m || normalizar(e.m ?? "").includes(m)) && (!u || (e.uf ?? "").toLowerCase() === u));
  return saida.sort((a, b) =>
    cmp(a.uf ?? "", b.uf ?? "") || cmp(a.m ?? "", b.m ?? "") || cmp(a.n ?? "", b.n ?? "") || a.c - b.c);
}

export class IndiceEscolas<E extends EscolaNome = EscolaNome> {
  readonly porCodigo = new Map<number, E>();
  readonly indice = new Map<string, Set<number>>();

  constructor(readonly escolas: E[]) {
    for (const e of escolas) {
      this.porCodigo.set(e.c, e);
      for (const p of new Set(normalizar(e.n ?? "").split(" "))) {
        if (!p) continue;
        let s = this.indice.get(p);
        if (!s) this.indice.set(p, (s = new Set()));
        s.add(e.c);
      }
    }
  }

  buscar(consulta: string, municipio = "", uf = ""): AchadoEscolas<E> {
    const bruto = normalizar(consulta);
    if (!bruto) return { tipo: "vazia", escolas: [], total: 0 };
    if (ehNumero(bruto)) {
      const e = this.porCodigo.get(Number(bruto));
      return { tipo: e ? "codigo" : "nenhuma", escolas: e ? [e] : [], total: e ? 1 : 0 };
    }
    const alvo = palavrasNome(consulta);
    if (!alvo.length) return { tipo: "vazia", escolas: [], total: 0 };
    let achadas = filtrar(this.codigosDe(this.intersecao(alvo)), municipio, uf);
    let dividida = false;
    if (!achadas.length && !municipio && alvo.length >= 2) {
      const d = this.nomeELugar(alvo);
      if (d.length) {
        achadas = d;
        dividida = true;
      }
    }
    const tipo = !achadas.length ? "nenhuma" : achadas.length === 1 ? "unica" : "ambigua";
    return { tipo, escolas: achadas, total: achadas.length, nomeELugar: dividida };
  }

  private codigosDe(codigos: Set<number>): E[] {
    return [...codigos].map((c) => this.porCodigo.get(c)!);
  }

  private intersecao(palavras: string[]): Set<number> {
    const conjuntos = palavras.map((p) => this.indice.get(p) ?? new Set<number>()).sort((a, b) => a.size - b.size);
    if (!conjuntos.length) return new Set();
    const [menor, ...resto] = conjuntos;
    return new Set([...menor].filter((c) => resto.every((s) => s.has(c))));
  }

  /** "sao jose carlos chagas mg": as primeiras palavras são o nome, as últimas o município e/ou a UF. */
  private nomeELugar(alvo: string[]): E[] {
    for (let k = alvo.length - 1; k > 0; k--) {
      const nome = alvo.slice(0, k);
      let lugar = alvo.slice(k);
      let uf = "";
      const ult = lugar[lugar.length - 1];
      if (ult.length === 2 && UFS.has(ult)) {
        uf = ult;
        lugar = lugar.slice(0, -1);
      }
      const codigos = this.intersecao(nome);
      if (!codigos.size) continue;
      const achadas = filtrar(this.codigosDe(codigos), lugar.join(" "), uf);
      if (achadas.length) return achadas;
    }
    return [];
  }
}
