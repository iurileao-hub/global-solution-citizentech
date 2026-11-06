/**
 * O fluxo de uma consulta, do texto digitado à resposta. Reescrita de src/assistente/nucleo.py (modelo B, o
 * "orientador com limites", que é o padrão do terminal e o que o contrato prende).
 *
 * Ordem das regras (a primeira que se aplica decide):
 *   1. entrada vazia                                  -> pede para digitar algo
 *   2. código de orientação ("D1", "ce um")           -> resposta direta
 *   3. o texto nomeia uma escola (todas as palavras estão no nome de alguma) -> ficha ou lista de escolas
 *   4. busca nas orientações (palavras do LUGAR citado não contam como assunto), com o desvio para os números de
 *      fechamento quando a pergunta pede contagem
 *   5. nada                                           -> "sem base suficiente", com os temas disponíveis
 *
 * A diferença para o Python: aqui a resposta é um OBJETO, não um texto. A tela monta o HTML a partir dele, e
 * respostas.ts monta o texto do terminal (o contrato confere esse texto, palavra por palavra).
 */

import type { Base } from "./base";
import { IndiceOrientacoes, type Resultado, resultado } from "./busca";
import { type AchadoEscolas, type EscolaNome, IndiceEscolas } from "./escolas";
import {
  acharLugar, type BlocoFechamentos, dadosBloco, type Fechamentos, palavrasDoLugar, pedeNumero,
} from "./fechamentos";
import { codigoFalado, ehNumero, normalizar, termos } from "./texto";

export const MAX_ESCOLAS_LISTA = 8;

export const MENSAGEM = {
  vazia: "Você não digitou nada. Escreva uma pergunta, um código como D1, ou o nome da escola.",
  soComuns: "Não entendi a pergunta: ela só tem palavras muito comuns. Tente com outras palavras.",
  numero: (n: string) => `Não reconheci o número ${n}. Digite um código como D1, o código INEP de uma escola, ` +
    "ou escreva sua pergunta. (No menu, as opções vão de 0 a 4.)",
} as const;

export interface Contexto<E extends EscolaNome = EscolaNome> {
  base: Base;
  indice: IndiceOrientacoes;
  escolas: IndiceEscolas<E> | null;
  fechamentos: Fechamentos | null;
}

interface Comum {
  /** orientações mostradas (para a avaliação e o contrato) */
  ids: string[];
  /** escolas mostradas */
  escolas: number[];
  /** respondeu avisando que parte da pergunta ficou sem cobertura */
  parcial: boolean;
}

export type Resposta<E extends EscolaNome = EscolaNome> = Comum & (
  | { tipo: "vazia"; mensagem: string }
  | { tipo: "codigo"; rid: string; numeros: BlocoFechamentos | null }
  | { tipo: "unica"; rid: string; extras: string[]; fora: string[]; numeros: BlocoFechamentos | null }
  | { tipo: "ambigua" }
  | { tipo: "escola"; codigo: number; extras: string[] }
  | { tipo: "escola_ambigua"; achado: AchadoEscolas<E>; jaFiltrado: boolean; mostra: E[] }
  | { tipo: "nenhuma" }
);

export function montar<E extends EscolaNome>(base: Base, escolas: E[] | null, fechamentos: Fechamentos | null):
  Contexto<E> {
  return { base, indice: new IndiceOrientacoes(base), escolas: escolas ? new IndiceEscolas(escolas) : null, fechamentos };
}

function registroDeFechamentos(base: Base): string | undefined {
  for (const [rid, reg] of base.registros) if (reg.dados === "fechamentos") return rid;
  return undefined;
}

function ordenarPorPontuacao(p: Map<string, number>): string[] {
  return [...p.keys()].sort((a, b) => p.get(b)! - p.get(a)!); // estável: mantém a ordem do ranking no empate
}

/** Pergunta que cita um lugar e empata com a orientação de números por lugar: ela responde. */
function lugarDesempata(ctx: Contexto, r: Resultado, texto: string): Resultado {
  if (!ctx.fechamentos || !["ambigua", "unica"].includes(r.tipo) || r.pontuacoes.size === 0) return r;
  const alvo = [...r.pontuacoes.keys()].find((rid) => ctx.base.registros.get(rid)!.dados === "fechamentos");
  const topo = Math.max(...r.pontuacoes.values());
  if (!alvo || r.pontuacoes.get(alvo)! < topo - 1 || (r.tipo === "unica" && r.ids.length === 1 && r.ids[0] === alvo)) {
    return r;
  }
  if (!acharLugar(ctx.fechamentos, texto)) return r;
  const outros = ordenarPorPontuacao(r.pontuacoes).filter((x) => x !== alvo).slice(0, 2);
  const lugar = palavrasDoLugar(ctx.fechamentos, texto);
  return { ...r, tipo: "unica", ids: [alvo], sugestoes: outros, fora: ctx.indice.foraDe(texto, alvo, lugar) };
}

/** "quantas escolas fecharam no Piauí?", "está aumentando?": é pergunta de contagem, e só a orientação F5 conta. */
function pedeFechamentos(ctx: Contexto, r: Resultado, texto: string, lugar: Set<string>): Resultado {
  if (!ctx.fechamentos || !termos(texto).includes("fecha")) return r;
  const alvo = registroDeFechamentos(ctx.base);
  if (!alvo || (r.tipo === "unica" && r.ids.length === 1 && r.ids[0] === alvo)) return r;
  const comLugar = acharLugar(ctx.fechamentos, texto) !== null;
  if (!(pedeNumero(texto) || (comLugar && r.tipo === "nenhuma"))) return r;
  const outros = ordenarPorPontuacao(r.pontuacoes).filter((x) => x !== alvo).slice(0, 2);
  // o que a contagem NÃO responde continua avisado ("quantos ALUNOS": F5 conta escolas, não alunos)
  return resultado("unica", {
    ids: [alvo], sugestoes: outros, pontuacoes: r.pontuacoes, cobertura: 1, fora: ctx.indice.foraDe(texto, alvo, lugar),
  });
}

function numeros(ctx: Contexto, rid: string, texto: string): BlocoFechamentos | null {
  return ctx.base.registros.get(rid)!.dados === "fechamentos" && ctx.fechamentos
    ? dadosBloco(ctx.fechamentos, texto)
    : null;
}

const VAZIO: Set<string> = new Set();

export function responder<E extends EscolaNome>(ctx: Contexto<E>, texto: string): Resposta<E> {
  const base = ctx.base;
  const bruto = normalizar(texto);
  const nada = { ids: [], escolas: [], parcial: false };
  if (!bruto) return { ...nada, tipo: "vazia", mensagem: MENSAGEM.vazia };

  const codigo = codigoFalado(bruto) ?? bruto.replaceAll(" ", "").toUpperCase();
  if (base.registros.has(codigo)) {
    return { ...nada, tipo: "codigo", rid: codigo, numeros: numeros(ctx, codigo, ""), ids: [codigo] };
  }

  if (ehNumero(bruto) && !(ctx.escolas && ctx.escolas.porCodigo.has(Number(bruto)))) {
    return { ...nada, tipo: "vazia", mensagem: MENSAGEM.numero(bruto) };
  }

  const lugar = ctx.fechamentos ? palavrasDoLugar(ctx.fechamentos, texto) : VAZIO;
  let r = ctx.indice.buscar(texto, lugar);
  const achado: AchadoEscolas<E> = ctx.escolas ? ctx.escolas.buscar(texto) : { tipo: "nenhuma", escolas: [], total: 0 };
  // Escola identificada sem dúvida vence sempre; nome repetido só vence se a orientação não cobrir a pergunta
  // inteira. A cobertura aqui é medida COM as palavras de lugar (ver o comentário no Python).
  const cobNome = lugar.size ? ctx.indice.buscar(texto).cobertura : r.cobertura;
  if (achado.tipo === "unica" || achado.tipo === "codigo" || (achado.tipo === "ambigua" && cobNome < 1)) {
    if (achado.tipo === "ambigua") return listaEscolas(achado);
    return escola(ctx, achado.escolas[0], r.tipo === "unica" ? r.ids : []);
  }
  r = pedeFechamentos(ctx, lugarDesempata(ctx, r, texto), texto, lugar);
  if (r.tipo === "vazia") return { ...nada, tipo: "vazia", mensagem: MENSAGEM.soComuns };
  if (r.tipo === "unica") {
    const rid = r.ids[0];
    const ja = new Set((base.registros.get(rid)!.relacionados ?? []).slice(0, 3));
    const extras = r.sugestoes.filter((x) => !ja.has(x));
    return {
      tipo: "unica", rid, extras, fora: r.fora, numeros: numeros(ctx, rid, texto), ids: r.ids, escolas: [],
      parcial: r.fora.length > 0,
    };
  }
  if (r.tipo === "ambigua") return { ...nada, tipo: "ambigua", ids: r.ids };
  return { ...nada, tipo: "nenhuma" };
}

/** Ligações da ficha com as orientações ("Para continuar"), na ordem em que a ficha mostra. */
export function ligacoesDaEscola(base: Base, e: { d: string | null; rota?: { receptoras?: unknown[] } | null }):
  string[] {
  const lig = base.ligacoesEscola;
  const chaves = ["sempre", ...(e.rota && e.rota.receptoras?.length ? ["com_rota"] : []), e.d ?? ""];
  const ids: string[] = [];
  for (const k of chaves) for (const x of lig[k] ?? []) if (!ids.includes(x)) ids.push(x);
  return ids;
}

export function escola<E extends EscolaNome>(ctx: Contexto<E>, e: E, extras: string[] = []): Resposta<E> {
  const d = (e as unknown as { d?: string | null }).d ?? "";
  // não repetir o que "Para continuar" já mostra (o Python olha só "sempre" e a localização diferenciada)
  const lig = new Set([...(ctx.base.ligacoesEscola["sempre"] ?? []), ...(ctx.base.ligacoesEscola[d] ?? [])]);
  return { tipo: "escola", codigo: e.c, extras: extras.filter((x) => !lig.has(x)), ids: [], escolas: [e.c], parcial: false };
}

/** Uma escola de cada UF por vez, da UF com mais escolas para a com menos. */
export function amostra<E extends EscolaNome>(es: E[], n: number): E[] {
  const porUf = new Map<string | null, E[]>();
  for (const e of es) {
    const l = porUf.get(e.uf);
    if (l) l.push(e);
    else porUf.set(e.uf, [e]);
  }
  const filas = [...porUf.values()].map((f) => [...f]).sort((a, b) => b.length - a.length);
  const saida: E[] = [];
  while (saida.length < n && filas.some((f) => f.length)) {
    for (const f of filas) if (f.length && saida.length < n) saida.push(f.shift()!);
  }
  return saida;
}

export function listaEscolas<E extends EscolaNome>(achado: AchadoEscolas<E>, jaFiltrado = false): Resposta<E> {
  const es = achado.escolas;
  const mostra = es.length > MAX_ESCOLAS_LISTA ? amostra(es, MAX_ESCOLAS_LISTA) : es;
  return { tipo: "escola_ambigua", achado, jaFiltrado, mostra, ids: [], escolas: es.map((e) => e.c), parcial: false };
}
