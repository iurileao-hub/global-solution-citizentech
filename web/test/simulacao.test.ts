/**
 * O CONTRATO do simulador: web/src/nucleo/simulacao.ts tem de devolver, para cada plano de
 * data/regressao_simulacao.json (gerado por scripts/exportar_simulacao.py), o MESMO resultado que o Python.
 * Mais as propriedades (conservação, ninguém em escola fechada, ordem irrelevante) e o cenário no link.
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { escreverCenario, lerCenario, type Municipio, simular } from "../src/nucleo/simulacao";

const DADOS = new URL("../../data/", import.meta.url);
const ler = (nome: string) => readFileSync(new URL(nome, DADOS));
const contrato = JSON.parse(ler("regressao_simulacao.json").toString("utf-8"));
const doc = JSON.parse(gunzipSync(ler("simulacao.json.gz")).toString("utf-8"));

function municipio(lugar: number): Municipio {
  const [uf, m] = doc.lugares[lugar];
  return { lugar, uf, municipio: m, escolas: doc.municipios[String(lugar)] ?? [] };
}

describe("contrato com o simulador Python", () => {
  it("foi gerado com os mesmos dados que este teste lê", () => {
    for (const [arq, hash] of Object.entries(contrato.insumos as Record<string, string>)) {
      expect(createHash("sha256").update(ler(arq)).digest("hex"), `${arq} mudou: rode scripts/exportar_simulacao.py`)
        .toBe(hash);
    }
  });

  for (const caso of contrato.casos) {
    it(`${caso.id} (${caso.resultado.municipio}/${caso.resultado.uf}, ${caso.fechar.length} escolas)`, () => {
      expect(simular(municipio(caso.lugar), caso.fechar, caso.indicacoes)).toEqual(caso.resultado);
    });
  }
});

describe("propriedades", () => {
  const casos = contrato.casos.filter((c: { fechar: number[] }) => c.fechar.length > 1);

  it("a ordem do plano não importa", () => {
    for (const c of casos) {
      const mun = municipio(c.lugar);
      expect(simular(mun, [...c.fechar].reverse(), c.indicacoes)).toEqual(simular(mun, c.fechar, c.indicacoes));
    }
  });

  it("toda criança aparece uma vez, e ninguém vai para escola fechada", () => {
    for (const c of contrato.casos) {
      const r = simular(municipio(c.lugar), c.fechar, c.indicacoes);
      const fechadas = new Set(r.fechadas);
      expect(r.com_destino + Object.values(r.sem_destino).reduce((a, b) => a + b, 0)).toBe(r.criancas);
      expect(r.receptoras.reduce((s, x) => s + x.recebe, 0)).toBe(r.com_destino);
      for (const a of r.alocacoes) if (a.destino !== null) expect(fechadas.has(a.destino)).toBe(false);
    }
  });
});

describe("cenário no link", () => {
  it("ida e volta sem perder nada", () => {
    const ind = { "32049501:anos_iniciais": 32050364, "32049501:pre_escola": 32071175 };
    const q = escreverCenario([32049501, 32049501, 32000001], ind);
    expect(q).toBe("f=32000001,32049501&i=32049501:anos_iniciais:32050364,32049501:pre_escola:32071175");
    expect(lerCenario(new URLSearchParams(q))).toEqual({ fechar: [32000001, 32049501], indicacoes: ind });
  });

  it("ignora lixo no link", () => {
    expect(lerCenario(new URLSearchParams("f=abc,-3,12&i=1:voo:2,3:creche:x,4:creche:5")))
      .toEqual({ fechar: [12], indicacoes: { "4:creche": 5 } });
  });

  it("indicação de escola fora do plano não vai para o link", () => {
    expect(escreverCenario([1], { "2:creche": 3 })).toBe("f=1");
  });
});
