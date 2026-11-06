/**
 * Números de fechamento de escolas rurais por lugar (data/fechamentos.json). Reescrita de
 * src/assistente/fechamentos.py, onde estão os cuidados achados nos testes ("Pará" sem acento é a preposição
 * "para"; "Rio Grande do Sul" contém o município "Rio Grande"; palavra comum que também é município).
 *
 * Aqui o bloco sai em duas formas: DADOS (para a tela montar a tabela) e TEXTO (igual ao do terminal, para o
 * contrato e para o botão de copiar).
 */

import { normalizar } from "./texto";

export interface NumerosLugar {
  ativas_2025: number;
  paralisadas_2025: number;
  paralisadas_5_anos_ou_mais: number;
  extintas_2019_2025: number;
  extintas_por_ano: Record<string, number>;
  povos?: Record<string, NumerosLugar>;
}

export interface DocFechamentos {
  esquema: number;
  fonte?: string;
  data_verificacao?: string;
  criterio?: string;
  brasil: NumerosLugar;
  uf: Record<string, NumerosLugar>;
  municipio: Record<string, NumerosLugar>;
}

export interface Fechamentos {
  doc: DocFechamentos;
  /** nome normalizado -> chaves "Nome/UF", na ordem do arquivo */
  munNorm: Map<string, string[]>;
}

export type Lugar = ["municipio", string] | ["uf", string];

const ESTADOS: ReadonlyArray<readonly [string, string]> = [
  ["acre", "AC"], ["alagoas", "AL"], ["amapa", "AP"], ["amazonas", "AM"], ["bahia", "BA"], ["ceara", "CE"],
  ["distrito federal", "DF"], ["espirito santo", "ES"], ["goias", "GO"], ["maranhao", "MA"],
  ["mato grosso do sul", "MS"], ["mato grosso", "MT"], ["minas gerais", "MG"], ["minas", "MG"],
  ["paraiba", "PB"], ["parana", "PR"], ["pernambuco", "PE"], ["piaui", "PI"], ["rio de janeiro", "RJ"],
  ["rio grande do norte", "RN"], ["rio grande do sul", "RS"], ["rondonia", "RO"], ["roraima", "RR"],
  ["santa catarina", "SC"], ["sao paulo", "SP"], ["sergipe", "SE"], ["tocantins", "TO"],
];
const ESTADOS_POR_TAMANHO = [...ESTADOS].sort((a, b) => b[0].length - a[0].length);

export const NOME_UF: Readonly<Record<string, string>> = {
  AC: "no Acre", AL: "em Alagoas", AP: "no Amapá", AM: "no Amazonas", BA: "na Bahia",
  CE: "no Ceará", DF: "no Distrito Federal", ES: "no Espírito Santo", GO: "em Goiás",
  MA: "no Maranhão", MT: "em Mato Grosso", MS: "em Mato Grosso do Sul", MG: "em Minas Gerais",
  PA: "no Pará", PB: "na Paraíba", PR: "no Paraná", PE: "em Pernambuco", PI: "no Piauí",
  RJ: "no Rio de Janeiro", RN: "no Rio Grande do Norte", RS: "no Rio Grande do Sul",
  RO: "em Rondônia", RR: "em Roraima", SC: "em Santa Catarina", SP: "em São Paulo",
  SE: "em Sergipe", TO: "no Tocantins",
};
const PARA_DEPOIS_DE = ["no", "do", "em", "pro", "estado do"];
const UFS_FECH: ReadonlySet<string> = new Set([...ESTADOS.map(([, uf]) => uf.toLowerCase()), "pa"]);
const SIGLAS_AMBIGUAS = ["pa", "es", "se", "to"];
const EXPLICITO_MUNICIPIO = ["municipio de", "cidade de", "prefeitura de"];
const PEDE_NUMERO: ReadonlySet<string> = new Set(
  "quantas quantos dados estatistica estatisticas total aumentando aumentou diminuindo diminuiu desde ritmo taxa"
    .split(" "),
);
const ANTES_DE_LUGAR = ["em", "de", "do", "da", "no", "na", "pra", "para", "pro"];
const CONTA_PESSOAS: ReadonlySet<string> = new Set(
  "aluno alunos crianca criancas estudante estudantes professor professora professores familia familias".split(" "),
);

export class ErroFechamentos extends Error {}

export function preparar(doc: DocFechamentos): Fechamentos {
  if (doc?.esquema !== 1 || !doc.uf || !Object.keys(doc.uf).length) {
    throw new ErroFechamentos("Arquivo de fechamentos vazio ou de versão desconhecida.");
  }
  const munNorm = new Map<string, string[]>();
  for (const chave of Object.keys(doc.municipio)) {
    const nome = chave.slice(0, chave.lastIndexOf("/"));
    const n = normalizar(nome);
    const l = munNorm.get(n);
    if (l) l.push(chave);
    else munNorm.set(n, [chave]);
  }
  return { doc, munNorm };
}

function ufDaChave(chave: string): string {
  return chave.slice(chave.lastIndexOf("/") + 1);
}

/** -> [UF citada ou null, texto com o nome do estado apagado]. `t` vem com espaço nas pontas. */
function estado(t: string): [string | null, string] {
  for (const [nome, uf] of ESTADOS_POR_TAMANHO) {
    if (t.includes(` ${nome} `) && !EXPLICITO_MUNICIPIO.some((pre) => t.includes(` ${pre} ${nome} `))) {
      return [uf, t.split(` ${nome} `).join(" ")];
    }
  }
  if (PARA_DEPOIS_DE.some((pre) => t.includes(` ${pre} para `))) return ["PA", t];
  const sigla = t.split(" ").find((p) => p.length === 2 && UFS_FECH.has(p) && !SIGLAS_AMBIGUAS.includes(p));
  if (sigla) return [sigla.toUpperCase(), t.split(` ${sigla} `).join(" ")];
  return [null, t];
}

/** Municípios citados: [nome normalizado, chave "Nome/UF"], só com sinal de lugar (preposição antes ou UF depois). */
function municipios(f: Fechamentos, t: string): [string, string][] {
  const achados: [string, string][] = [];
  for (const [nomeNorm, chaves] of f.munNorm) {
    if (nomeNorm.length < 4 || !t.includes(` ${nomeNorm} `)) continue;
    const preposto = ANTES_DE_LUGAR.some((p) => t.includes(` ${p} ${nomeNorm} `));
    for (const c of chaves) {
      if (preposto || t.includes(` ${nomeNorm} ${ufDaChave(c).toLowerCase()} `)) achados.push([nomeNorm, c]);
    }
  }
  return achados;
}

/** -> ["municipio", "Muniz Freire/ES"] | ["uf", "MG"] | null. O município mais longo citado vence. */
export function acharLugar(f: Fechamentos, pergunta: string): Lugar | null {
  const [uf, t] = estado(" " + normalizar(pergunta) + " ");
  const achados = municipios(f, t);
  if (achados.length) {
    const maior = Math.max(...achados.map(([n]) => n.length));
    let chaves = achados.filter(([n]) => n.length === maior).map(([, c]) => c);
    if (uf) {
      const daUf = chaves.filter((c) => c.endsWith("/" + uf));
      if (daUf.length) chaves = daUf;
    }
    if (chaves.length === 1) return ["municipio", chaves[0]];
  }
  return uf ? ["uf", uf] : null;
}

/** Palavras do nome do lugar citado: dizem ONDE, não o ASSUNTO. */
export function palavrasDoLugar(f: Fechamentos, pergunta: string): Set<string> {
  const t = " " + normalizar(pergunta) + " ";
  const nomes = new Set<string>();
  for (const [nome] of ESTADOS) if (t.includes(` ${nome} `)) nome.split(" ").forEach((p) => nomes.add(p));
  const [uf, resto] = estado(t);
  if (uf) nomes.add(uf.toLowerCase());
  for (const [n] of municipios(f, resto)) n.split(" ").forEach((p) => nomes.add(p));
  return nomes;
}

/** Pede contagem DE ESCOLAS. "Quantos alunos" pede outra coisa, que a contagem não tem. */
export function pedeNumero(pergunta: string): boolean {
  const p = new Set(normalizar(pergunta).split(" "));
  return [...p].some((x) => PEDE_NUMERO.has(x)) && ![...p].some((x) => CONTA_PESSOAS.has(x));
}

export function nomeLugar(lugar: Lugar | null): string {
  if (lugar === null) return "no Brasil";
  return lugar[0] === "uf" ? NOME_UF[lugar[1]] : `em ${lugar[1]}`;
}

export function mil(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

const POVOS: ReadonlyArray<readonly [string, readonly string[]]> = [
  ["indigena", ["indigena", "indigenas", "aldeia", "aldeias", "indio", "indios", "guarani", "kaiowa"]],
  ["quilombola", ["quilombola", "quilombolas", "quilombo", "quilombos"]],
];
export const NOME_POVO: Readonly<Record<string, string>> = {
  indigena: "em terra indígena", quilombola: "em comunidade quilombola",
};

export interface PovoNumeros {
  grupo: string;
  numeros: NumerosLugar | null;
}

export interface BlocoFechamentos {
  lugar: Lugar | null;
  numeros: NumerosLugar;
  anos: string[];
  /** ano em que caiu mais da metade das extinções (possível regularização), ou null */
  anoPico: string | null;
  /** recorte indígena/quilombola pedido na pergunta; "so_estado" quando o lugar é município */
  povos: PovoNumeros[] | "so_estado" | null;
}

export function dadosBloco(f: Fechamentos, pergunta: string): BlocoFechamentos {
  const lugar = acharLugar(f, pergunta);
  const n = lugar === null ? f.doc.brasil : lugar[0] === "uf" ? f.doc.uf[lugar[1]] : f.doc.municipio[lugar[1]];
  const serie = n.extintas_por_ano ?? {};
  const anos = Object.keys(f.doc.brasil.extintas_por_ano).sort();
  let anoPico: string | null = null;
  const valores = Object.values(serie);
  const maxSerie = valores.length ? Math.max(...valores) : 0;
  if (n.extintas_2019_2025 && maxSerie >= 0.5 * n.extintas_2019_2025 && 0.5 * n.extintas_2019_2025 >= 10) {
    // a primeira chave com o maior valor, na ordem do arquivo (anos crescentes), como o max() do Python
    anoPico = Object.keys(serie).find((a) => serie[a] === maxSerie) ?? null;
  }
  const palavras = new Set(normalizar(pergunta).split(" "));
  const pedidos = POVOS.filter(([, t]) => t.some((x) => palavras.has(x))).map(([g]) => g);
  let povos: BlocoFechamentos["povos"] = null;
  if (pedidos.length) {
    povos = lugar && lugar[0] === "municipio"
      ? "so_estado"
      : pedidos.map((g) => ({ grupo: g, numeros: n.povos?.[g] ?? null }));
  }
  return { lugar, numeros: n, anos, anoPico, povos };
}

/** O bloco como o terminal mostra (sem a quebra de linha, que é coisa do terminal). */
export function textoBloco(b: BlocoFechamentos): string {
  const n = b.numeros;
  const serie = n.extintas_por_ano ?? {};
  const par = n.paralisadas_2025;
  const paralisadas = par
    ? `${mil(par)}, das quais ${mil(n.paralisadas_5_anos_ou_mais)} estão paralisadas há 5 anos ou mais`
    : "nenhuma";
  const anos = b.anos;
  const linhas = [
    `Escolas públicas rurais ${nomeLugar(b.lugar)}, pelo Censo Escolar:`,
    `  - em atividade em 2025: ${mil(n.ativas_2025)}`,
    `  - extintas (encerradas de vez) de ${anos[0]} a ${anos[anos.length - 1]}: ${mil(n.extintas_2019_2025)}`,
    "    por ano: " + anos.map((a) => `${a}: ${mil(serie[a] ?? 0)}`).join(", "),
    `  - paralisadas em 2025 (sem aulas, mas sem extinção formal): ${paralisadas}`,
  ];
  if (b.anoPico) {
    linhas.push(`  Mais da metade das extinções caiu em ${b.anoPico}. Uma concentração assim pode ser ` +
      "regularização (a rede registra de uma vez o fim de escolas que já estavam paradas); " +
      "a Secretaria de Educação sabe dizer.");
  }
  if (b.povos === "so_estado") {
    linhas.push("  O recorte de escolas indígenas e quilombolas existe só por estado e para o Brasil; " +
      "pergunte pelo estado para ver.");
  } else if (b.povos) {
    for (const { grupo, numeros: x } of b.povos) {
      if (!x) {
        linhas.push(`  Escolas ${NOME_POVO[grupo]}: nenhuma registrada aqui pelo Censo.`);
        continue;
      }
      const ext = x.extintas_2019_2025;
      const p = x.paralisadas_2025;
      const extintas = ext ? `pelo menos ${mil(ext)} ${ext === 1 ? "extinta" : "extintas"}` : "nenhuma extinta registrada";
      const paradas = p ? `${mil(p)} ${p === 1 ? "paralisada" : "paralisadas"}` : "nenhuma paralisada";
      linhas.push(`  Só escolas ${NOME_POVO[grupo]}: ${mil(x.ativas_2025)} em atividade em 2025; ` +
        `${extintas} de 2019 a 2025; ${paradas} em 2025.`);
    }
    linhas.push("  (\"Pelo menos\": o Censo só marca terra indígena ou comunidade quilombola enquanto a " +
      "escola funciona, e a escola parada desde antes de 2019 fica fora desta conta.)");
  }
  if (b.lugar === null) {
    linhas.push("Para ver o seu estado ou município, escreva o nome dele na pergunta " +
      "(por exemplo: \"quantas escolas fecharam em Minas Gerais?\").");
  }
  linhas.push("Para citar: \"levantamento do projeto Escola em Pauta com os microdados do Censo " +
    "Escolar (INEP)\". O INEP publica os dados por escola; estes totais são contados pelo projeto.");
  return linhas.join("\n");
}
