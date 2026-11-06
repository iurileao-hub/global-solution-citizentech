/**
 * Normalização de texto: o primeiro passo de qualquer busca. Reescrita de src/assistente/texto.py.
 *
 * A pessoa escreve "Fechamento", "fecharam" ou "FECHAR"; a base diz "fechar". Para comparar, todos viram a
 * mesma forma: minúsculas e sem acento, só letras e números, sem palavras vazias, e o RADICAL de até 5 letras
 * ("fechamento", "fecharam" e "fechar" -> "fecha"). Os detalhes (grafia "x" = "ch", sigla falada "elê dê bê")
 * estão explicados no módulo Python; aqui a regra é ser IGUAL a ele, e o contrato data/regressao_web.json confere.
 */

export const TAMANHO_RADICAL = 5;

export const PALAVRAS_VAZIAS: ReadonlySet<string> = new Set(
  `
a o as os um uma uns umas de da do das dos em na no nas nos por pela pelo pelas pelos para pra pro
com sem sob sobre e ou mas se que qual quais quando como onde quem cujo ja nao sim mais menos muito
meu minha meus minhas seu sua seus suas nosso nossa nossos nossas ele ela eles elas eu voce voces gente
isso isto esse essa este esta aquele aquela ser estar ter ha tem foi vai vou sao era sera esta estao
me te lhe nos vos ao aos à às la le lo ai entao tambem so ate apos antes depois agora aqui ali
pode podem gente mesmo coisa alguma algum algo quero queria saber sei dizer diz quer
posso podemos poder precisa precisam preciso deve devem devia feita feito acontece acontecer aconteceu
forem for fosse outra outro outras outros vao tinha adianta ne oi ola bom dia boa tarde noite
obrigada obrigado obg viu ta to favor gostaria ainda tipo exemplo algumas alguns alguem cada todo toda
todos todas foram existe existem desde querer pergunta sou estou somos neto neta netos netas sobrinho sobrinha
`
    .split(/\s+/)
    .filter(Boolean),
);

/** Sigla do tema dita letra a letra (o reconhecimento de voz escreve "elê dê bê"). A ordem é a do Python. */
export const SIGLAS_FALADAS: ReadonlyArray<readonly [string, string]> = [
  ["ele de be", "ldb"], ["e ce a", "eca"], ["ce ene e", "cne"], ["eme e ce", "mec"], ["eme pe efe", "mpf"],
  ["eme pe", "mp"], ["esse i ce", "sic"], ["ele a i", "lai"], ["efe ene de e", "fnde"], ["pe ene a e", "pnae"],
  ["i ene e pe", "inep"], ["pe ele", "pl"],
];

/** Número por extenso (menu e código falado: "dois", "ce um"). */
export const NUMEROS: Readonly<Record<string, number>> = {
  zero: 0, um: 1, uma: 1, dois: 2, duas: 2, tres: 3, quatro: 4, cinco: 5, seis: 6, sete: 7, oito: 8, nove: 9,
};
const LETRA_DE_CODIGO: Readonly<Record<string, string>> = {
  de: "D", d: "D", ce: "C", c: "C", te: "T", t: "T", efe: "F", f: "F",
};

const SO_DIGITOS = /^[0-9]+$/;

/** O `str.isdigit()` do Python para texto já normalizado (só sobram dígitos ASCII). */
export function ehNumero(t: string): boolean {
  return SO_DIGITOS.test(t);
}

function tem<K extends string>(obj: Readonly<Record<K, unknown>>, chave: string): chave is K {
  return Object.prototype.hasOwnProperty.call(obj, chave);
}

/** "ce um" -> "C1"; "dê quatro" -> "D4". Só quando o texto é exatamente letra + número. */
export function codigoFalado(texto: string): string | null {
  const partes = normalizar(texto).split(" ").filter(Boolean);
  if (partes.length !== 2 || !tem(LETRA_DE_CODIGO, partes[0])) return null;
  const num = ehNumero(partes[1]) ? partes[1] : tem(NUMEROS, partes[1]) ? String(NUMEROS[partes[1]]) : "";
  return num ? LETRA_DE_CODIGO[partes[0]] + num : null;
}

export function grafia(p: string): string {
  return p.replaceAll("x", "ch");
}

// do mais longo para o mais curto ("eme pe efe" antes de "eme pe"); sort é estável, como o sorted do Python
const SIGLAS_POR_TAMANHO = [...SIGLAS_FALADAS].sort((a, b) => b[0].length - a[0].length);

function siglas(t: string): string {
  let s = ` ${t} `;
  for (const [falada, sigla] of SIGLAS_POR_TAMANHO) s = s.replaceAll(` ${falada} `, ` ${sigla} `);
  return s.trim();
}

/**
 * Minúsculas, sem acento, só letras/números separados por um espaço.
 * Igual ao Python: decompõe (NFKD), descarta o que não é ASCII (o acento solto), e só então põe em minúsculas.
 */
export function normalizar(texto: string): string {
  // eslint-disable-next-line no-control-regex
  const semAcento = texto.normalize("NFKD").replace(/[^\x00-\x7f]/g, "");
  return (semAcento.toLowerCase().match(/[a-z0-9]+/g) ?? []).join(" ");
}

export function radical(palavra: string): string {
  return palavra.slice(0, TAMANHO_RADICAL);
}

function conta(p: string): boolean {
  // números ("25", "2024") quase nunca dizem o ASSUNTO; o código "D1" é tratado antes da busca
  return !PALAVRAS_VAZIAS.has(p) && p.length > 1 && !ehNumero(p);
}

/** As palavras que importam, como a pessoa escreveu (sem acento): é o que se MOSTRA a ela. */
export function originais(texto: string): string[] {
  return siglas(normalizar(texto)).split(" ").filter((p) => p && conta(p));
}

/** Palavras inteiras que importam, já com a grafia unificada: premiam o casamento EXATO. */
export function palavras(texto: string): string[] {
  return originais(texto).map(grafia);
}

/** Radicais das palavras que importam, na ordem em que aparecem (com repetição). */
export function termos(texto: string): string[] {
  return palavras(texto).map(radical);
}

/** O " ".join(texto.split()) do Python: o contrato compara palavras, não a quebra de linha. */
export function espacos(texto: string): string {
  return texto.split(/\s+/).filter(Boolean).join(" ");
}
