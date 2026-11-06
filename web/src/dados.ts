/**
 * Os dados que o navegador baixa, sob demanda (gerados por scripts/dividir_para_web.py em site/dados/):
 *   versao.json               ~1 KB, ao abrir: fonte, data e a versão que vai em todo pedido (?v=)
 *   base_orientacoes.json     ~12 KB, ao abrir
 *   nomes.json                ~720 KB, em segundo plano: a busca por nome e a regra "a pergunta nomeia uma escola"
 *   fechamentos.json          ~60 KB, junto com os nomes (números de fechamento por lugar)
 *   escolas/NNN.json          ~30 KB, ao abrir uma escola (NNN = código INEP % 256)
 *   tracados/NNNN.json        ao abrir a prancha de uma escola (NNNN = código % 2048); pode não existir
 *   retrato_rotas.json        na página do retrato
 * Cada arquivo é pedido uma vez por sessão (a promessa fica guardada).
 */

import { type Base, validar } from "./nucleo/base";
import type { EscolaNome } from "./nucleo/escolas";
import { type DocFechamentos, type Fechamentos, preparar } from "./nucleo/fechamentos";
import { type Contexto, montar } from "./nucleo/nucleo";
import type { Escola } from "./nucleo/respostas";

export interface Versao {
  esquema: number;
  fonte: string;
  data_verificacao: string;
  pedacos: number;
  escolas: number;
  versao: string;
  pedacos_tracado?: number;
}

/** [código da receptora, polyline da ida, pares de índices dos trechos de chão] */
export type Tracado = [number, string, number[]];

const RAIZ = new URL("dados/", document.baseURI);
const guardados = new Map<string, Promise<unknown>>();

export class ErroDados extends Error {
  constructor(readonly arquivo: string, readonly status: number) {
    super(status === 0
      ? `Sem conexão para baixar ${arquivo}. Se você já abriu esta página antes, tente de novo quando houver sinal.`
      : `Não foi possível baixar ${arquivo} (erro ${status}).`);
  }
}

async function baixar<T>(arquivo: string, versao: string | null): Promise<T> {
  const url = new URL(arquivo, RAIZ);
  if (versao) url.searchParams.set("v", versao);
  let resp: Response;
  try {
    resp = await fetch(url);
  } catch {
    throw new ErroDados(arquivo, 0);
  }
  if (!resp.ok) throw new ErroDados(arquivo, resp.status);
  return resp.json() as Promise<T>;
}

function uma<T>(chave: string, fazer: () => Promise<T>): Promise<T> {
  let p = guardados.get(chave) as Promise<T> | undefined;
  if (!p) {
    p = fazer();
    guardados.set(chave, p);
    p.catch(() => guardados.delete(chave)); // erro de rede: a próxima tentativa baixa de novo
  }
  return p;
}

export function versao(): Promise<Versao> {
  // sem ?v=: é este arquivo que diz qual é a versão (o GitHub Pages guarda em cache por 10 minutos)
  return uma("versao", () => baixar<Versao>("versao.json", null));
}

async function arquivo<T>(nome: string): Promise<T> {
  const v = await versao();
  return uma(nome, () => baixar<T>(nome, v.versao));
}

export function base(): Promise<Base> {
  return uma("base:validada", async () => validar(await arquivo("base_orientacoes.json")));
}

export function fechamentos(): Promise<Fechamentos> {
  return uma("fech:preparado", async () => preparar(await arquivo<DocFechamentos>("fechamentos.json")));
}

interface DocNomes {
  colunas: string[];
  lugares: [string, string][];
  escolas: [number, string, number][];
}

/** Lista de todas as escolas (código, nome, município, UF), no formato que a busca do núcleo usa. */
export function nomes(): Promise<EscolaNome[]> {
  return uma("nomes:lista", async () => {
    const doc = await arquivo<DocNomes>("nomes.json");
    return doc.escolas.map(([c, n, l]) => {
      const [uf, m] = doc.lugares[l];
      return { c, n, m: m || null, uf: uf || null };
    });
  });
}

/** O contexto completo do assistente (base + nomes + fechamentos). A busca só responde com os três. */
export function contexto(): Promise<Contexto> {
  return uma("contexto", async () => {
    const [b, n, f] = await Promise.all([base(), nomes(), fechamentos()]);
    return montar(b, n, f);
  });
}

export function nomesProntos(): boolean {
  return guardados.has("contexto");
}

export async function escola(codigo: number): Promise<Escola | null> {
  const v = await versao();
  const nome = `escolas/${String(codigo % v.pedacos).padStart(3, "0")}.json`;
  const doc = await arquivo<{ escolas: Escola[] }>(nome);
  return doc.escolas.find((e) => e.c === codigo) ?? null;
}

/** Traçados das rotas da escola, ou null quando esta geração dos dados não tem traçados (só a 1ª passada). */
export async function tracados(codigo: number): Promise<Tracado[] | null> {
  const v = await versao();
  if (!v.pedacos_tracado) return null;
  const nome = `tracados/${String(codigo % v.pedacos_tracado).padStart(4, "0")}.json`;
  try {
    const doc = await arquivo<{ pedaco: number; escolas: Record<string, Tracado[]> }>(nome);
    return doc.escolas[String(codigo)] ?? null;
  } catch {
    return null; // sem traçado a ficha continua; a prancha cai para o esquema de distâncias
  }
}

export function retrato<T>(): Promise<T> {
  return arquivo<T>("retrato_rotas.json");
}
