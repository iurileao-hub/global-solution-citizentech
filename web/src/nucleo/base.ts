/**
 * Base de orientações (data/base_orientacoes.json): tipos e validação. Reescrita de src/assistente/base.py.
 *
 * A base é dado, não código. Um registro torto é recusado com uma mensagem que diz QUAL registro e QUAL campo,
 * em vez de virar uma resposta errada mais tarde. Na web isso protege contra um arquivo pela metade no cache.
 */

export interface Referencia {
  titulo: string;
  url: string;
  /** outras fontes oficiais conferidas para a mesma orientação */
  outras?: string[];
}

export interface Registro {
  id: string;
  tema: string;
  subtema: string;
  pergunta: string;
  palavras_chave: string[];
  orientacao: string;
  referencia: Referencia;
  data_verificacao: string;
  confirmar?: string;
  relacionados?: string[];
  dados?: string; // "fechamentos": a orientação mostra números calculados do lugar citado
}

export interface Tema {
  nome: string;
  descricao?: string;
  subtemas: Record<string, string>;
  relacionados?: string[];
}

export interface DocBase {
  esquema: number;
  descricao?: string;
  aviso_geral?: string;
  temas: Record<string, Tema>;
  ligacoes_escola?: Record<string, string[]>;
  registros: Registro[];
}

export interface Base {
  temas: Record<string, Tema>;
  /** Na ordem do arquivo (Map guarda a ordem de inserção, como o dict do Python). */
  registros: Map<string, Registro>;
  porTema: Map<string, string[]>;
  avisoGeral: string;
  ligacoesEscola: Record<string, string[]>;
}

export const ESQUEMA_BASE = 1;
const CAMPOS_OBRIGATORIOS = [
  "id", "tema", "subtema", "pergunta", "palavras_chave", "orientacao", "referencia", "data_verificacao",
] as const;
const DATA_ISO = /^\d{4}-\d{2}-\d{2}$/;

export class ErroBase extends Error {}

function vazio(v: unknown): boolean {
  return v === undefined || v === null || v === "" || v === false || v === 0 ||
    (Array.isArray(v) && v.length === 0) ||
    (typeof v === "object" && !Array.isArray(v) && Object.keys(v as object).length === 0);
}

export function validar(doc: unknown): Base {
  const erros: string[] = [];
  if (typeof doc !== "object" || doc === null || Array.isArray(doc)) {
    throw new ErroBase("A base deve ser um objeto JSON com 'temas' e 'registros'.");
  }
  const d = doc as Partial<DocBase>;
  if (d.esquema !== ESQUEMA_BASE) {
    erros.push(`versão de esquema desconhecida: ${JSON.stringify(d.esquema)} (esperado ${ESQUEMA_BASE})`);
  }
  let temas = d.temas;
  if (typeof temas !== "object" || temas === null || Object.keys(temas).length === 0) {
    erros.push("'temas' ausente ou vazio");
    temas = {};
  }
  const lista = d.registros;
  if (!Array.isArray(lista) || lista.length === 0) {
    throw new ErroBase([...erros, "'registros' ausente ou vazio"].join("; "));
  }

  const registros = new Map<string, Registro>();
  lista.forEach((r: Registro, i) => {
    const rid = typeof r === "object" && r && r.id ? ` (${r.id})` : "";
    const onde = `registro nº ${i + 1}${rid}`;
    if (typeof r !== "object" || r === null) {
      erros.push(`${onde}: não é um objeto`);
      return;
    }
    const faltando = CAMPOS_OBRIGATORIOS.filter((c) => vazio(r[c]));
    if (faltando.length) {
      erros.push(`${onde}: campo(s) obrigatório(s) ausente(s) ou vazio(s): ${faltando.join(", ")}`);
      return;
    }
    if (registros.has(r.id)) erros.push(`${onde}: id repetido`);
    if (!(r.tema in temas!)) erros.push(`${onde}: tema '${r.tema}' não existe em 'temas'`);
    else if (!(r.subtema in (temas![r.tema].subtemas ?? {}))) {
      erros.push(`${onde}: subtema '${r.subtema}' não existe no tema '${r.tema}'`);
    }
    if (!Array.isArray(r.palavras_chave)) erros.push(`${onde}: 'palavras_chave' deve ser uma lista`);
    const ref = r.referencia;
    if (!(typeof ref === "object" && ref.titulo && String(ref.url ?? "").startsWith("http"))) {
      erros.push(`${onde}: 'referencia' precisa de 'titulo' e de 'url' começando por http`);
    }
    if (!DATA_ISO.test(String(r.data_verificacao))) {
      erros.push(`${onde}: 'data_verificacao' deve estar no formato AAAA-MM-DD`);
    }
    registros.set(r.id, r);
  });

  for (const r of registros.values()) {
    for (const alvo of r.relacionados ?? []) {
      if (!registros.has(alvo)) erros.push(`registro ${r.id}: relacionado '${alvo}' não existe`);
    }
  }
  for (const [t, info] of Object.entries(temas!)) {
    for (const alvo of info.relacionados ?? []) {
      if (!(alvo in temas!)) erros.push(`tema ${t}: relacionado '${alvo}' não existe`);
    }
  }
  const ligacoes = d.ligacoes_escola ?? {};
  for (const [chave, alvos] of Object.entries(ligacoes)) {
    for (const alvo of alvos) {
      if (!registros.has(alvo)) erros.push(`ligacoes_escola[${chave}]: registro '${alvo}' não existe`);
    }
  }
  if (erros.length) throw new ErroBase("Base inconsistente:\n  - " + erros.join("\n  - "));

  const porTema = new Map<string, string[]>(Object.keys(temas!).map((t) => [t, []]));
  for (const r of registros.values()) porTema.get(r.tema)!.push(r.id);
  return { temas: temas!, registros, porTema, avisoGeral: d.aviso_geral ?? "", ligacoesEscola: ligacoes };
}
