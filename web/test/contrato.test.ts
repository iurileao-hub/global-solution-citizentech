/**
 * O CONTRATO: a busca em TypeScript tem de responder como o núcleo Python (data/regressao_web.json, gerado por
 * scripts/exportar_regressao.py). Para cada uma das 130 perguntas rotuladas: o mesmo tipo de resposta, as mesmas
 * orientações na mesma ordem, as mesmas escolas, o mesmo aviso de parcial e o MESMO TEXTO (palavra por palavra).
 * Mais as 12 buscas de escola e a normalização dos nomes das 53.759 escolas.
 *
 * Se este teste falhar depois de mudar o Python, regenere o contrato e porte a mudança: as duas implementações
 * não podem divergir, porque os números de acerto do README foram medidos no Python.
 */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { validar } from "../src/nucleo/base";
import { preparar } from "../src/nucleo/fechamentos";
import { montar, responder } from "../src/nucleo/nucleo";
import { type Escola, textoResposta } from "../src/nucleo/respostas";
import { espacos, normalizar } from "../src/nucleo/texto";

const DADOS = new URL("../../data/", import.meta.url);
const ler = (nome: string) => readFileSync(new URL(nome, DADOS));

const contrato = JSON.parse(ler("regressao_web.json").toString("utf-8"));
const docEscolas = JSON.parse(gunzipSync(ler("escolas_campo.json.gz")).toString("utf-8"));
const base = validar(JSON.parse(ler("base_orientacoes.json").toString("utf-8")));
const fech = preparar(JSON.parse(ler("fechamentos.json").toString("utf-8")));
const escolas: Escola[] = docEscolas.escolas;
const ctx = montar(base, escolas, fech);
const porCodigo = new Map(escolas.map((e) => [e.c, e]));

function sha256(arq: string) {
  return createHash("sha256").update(ler(arq)).digest("hex");
}

describe("contrato com o núcleo Python", () => {
  it("foi gerado com os mesmos dados que este teste lê", () => {
    for (const [arq, hash] of Object.entries(contrato.insumos as Record<string, string>)) {
      expect(sha256(arq), `${arq} mudou: rode scripts/exportar_regressao.py`).toBe(hash);
    }
  });

  for (const p of contrato.perguntas) {
    it(`${p.conjunto}/${p.id}: ${p.pergunta}`, () => {
      const r = responder(ctx, p.pergunta);
      const texto = textoResposta(base, r, (c) => porCodigo.get(c)!, docEscolas.fonte, docEscolas.data_verificacao);
      expect({ tipo: r.tipo, ids: r.ids, escolas: r.escolas, parcial: r.parcial, texto: espacos(texto) })
        .toEqual(p.resposta);
    });
  }

  for (const b of contrato.buscas_escola) {
    it(`busca de escola: ${JSON.stringify(b.consulta)} ${b.municipio ?? ""} ${b.uf ?? ""}`, () => {
      const a = ctx.escolas!.buscar(b.consulta, b.municipio ?? "", b.uf ?? "");
      expect({ tipo: a.tipo, total: a.total, codigos: a.escolas.map((e) => e.c) })
        .toEqual({ tipo: b.tipo, total: b.total, codigos: b.codigos });
    });
  }

  it("normaliza o nome e o município das 53.759 escolas como o Python", () => {
    const n = contrato.normalizacao;
    expect(escolas.length).toBe(n.escolas);
    const linhas = escolas.map((e) => `${normalizar(e.n ?? "")}|${normalizar(e.m ?? "")}`);
    const divergentes: number[] = [];
    n.hashes.forEach((h: string, i: number) => {
      const bloco = linhas.slice(i * n.por_bloco, (i + 1) * n.por_bloco).join("\n");
      if (createHash("sha256").update(bloco, "utf8").digest("hex") !== h) divergentes.push(i);
    });
    expect(divergentes, "blocos de escolas com normalização diferente").toEqual([]);
  });
});
