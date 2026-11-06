// @vitest-environment node
import { describe, expect, it, vi } from "vitest";

vi.stubGlobal("document", { baseURI: "http://localhost/" }); // dados.ts lê document.baseURI ao carregar
const { principal } = await import("../src/telas/ficha");
const { trechos } = await import("../src/telas/prancha");
const { partesComCodigos } = await import("../src/telas/componentes");
const { readFileSync } = await import("node:fs");

const rec = (c: number, km: number, etapas: string[]) => ({ c, n: "X", rural: true, km, etapas });

describe("receptora da frase de abertura", () => {
  const escola = (rs: ReturnType<typeof rec>[]) =>
    ({ e: { pre_escola: 5, anos_iniciais: 9 }, rota: { v: 1, receptoras: rs } }) as never;
  it("a mais próxima que recebe TODAS as etapas, mesmo com outra parcial mais perto", () => {
    expect(principal(escola([rec(1, 5, ["pre_escola"]), rec(2, 20, ["pre_escola", "anos_iniciais"])]))?.c).toBe(2);
  });
  it("sem nenhuma completa, a mais próxima", () => {
    expect(principal(escola([rec(1, 9, ["pre_escola"]), rec(2, 4, ["anos_iniciais"])]))?.c).toBe(2);
  });
  it("sem rota, nenhuma", () => expect(principal({ e: {}, rota: null } as never)).toBeNull());
});

describe("trechos de chão do traçado", () => {
  it("intercala pavimentado e chão pelos pares de índices", () => {
    expect(trechos(10, [2, 4, 6, 9])).toEqual([
      { i: 0, j: 2, chao: false }, { i: 2, j: 4, chao: true }, { i: 4, j: 6, chao: false }, { i: 6, j: 9, chao: true },
    ]);
  });
  it("sem pares, tudo pavimentado", () => expect(trechos(5, [])).toEqual([{ i: 0, j: 4, chao: false }]));
});

describe("citação de outra orientação no texto (veja C1)", () => {
  const base = JSON.parse(readFileSync(new URL("../../data/base_orientacoes.json", import.meta.url), "utf-8"));
  const pergunta = new Map<string, string>(base.registros.map((r: { id: string; pergunta: string }) => [r.id, r.pergunta]));
  const textos: string[] = base.registros.flatMap((r: { orientacao: string; confirmar?: string }) =>
    [r.orientacao, r.confirmar ?? ""]);
  it("nenhum trecho se perde: juntar as partes com o código de volta dá o texto original, em todas as orientações", () => {
    for (const t of textos) {
      const partes = partesComCodigos(t, (c) => pergunta.get(c));
      expect(partes.map((x) => (typeof x === "string" ? x : x.rid)).join("")).toBe(t);
    }
  });
  it("toda citação de orientação que existe vira link com a pergunta", () => {
    for (const t of textos) {
      const citadas = [...t.matchAll(/\b([CDFT]\d{1,2})\b/g)].map((m) => m[1]).filter((c) => pergunta.has(c));
      const links = partesComCodigos(t, (c) => pergunta.get(c)).filter((x) => typeof x !== "string");
      expect(links).toEqual(citadas.map((rid) => ({ rid, pergunta: pergunta.get(rid) })));
    }
    expect(textos.some((t) => partesComCodigos(t, (c) => pergunta.get(c)).length > 1)).toBe(true);
  });
  it("código que não existe na base fica como texto", () =>
    expect(partesComCodigos("veja D99", (c) => pergunta.get(c))).toEqual(["veja D99"]));
});
