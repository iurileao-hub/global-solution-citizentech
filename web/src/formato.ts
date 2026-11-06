/** Formatação de texto da ficha (como em src/escola_em_pauta/ficha.py, o protótipo impresso). */
import { redondo } from "./nucleo/respostas";

export const UF_NOME: Readonly<Record<string, string>> = {
  AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará", DF: "Distrito Federal",
  ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais",
  PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro",
  RN: "Rio Grande do Norte", RS: "Rio Grande do Sul", RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina",
  SP: "São Paulo", SE: "Sergipe", TO: "Tocantins",
};
export const ORDEM_ETAPAS = ["creche", "pre_escola", "anos_iniciais", "anos_finais", "medio"] as const;
export const ETAPA_ROTULO: Readonly<Record<string, string>> = {
  creche: "creche", pre_escola: "pré-escola", anos_iniciais: "anos iniciais", anos_finais: "anos finais",
  medio: "ensino médio",
};
export const ETAPA_ANOS: Readonly<Record<string, string>> = {
  anos_iniciais: "1º ao 5º ano", anos_finais: "6º ao 9º ano",
};
const ETAPA_INICIO: Readonly<Record<string, string>> = {
  creche: "da creche", pre_escola: "da pré-escola", anos_iniciais: "do 1º ano", anos_finais: "do 6º ano",
  medio: "do ensino médio",
};
const ETAPA_FIM: Readonly<Record<string, string>> = {
  creche: "à creche", pre_escola: "à pré-escola", anos_iniciais: "ao 5º ano", anos_finais: "ao 9º ano",
  medio: "ao ensino médio",
};

const SIGLAS = new Set(("EMEF EEEFM CEEFMTI CEI EPM EEEM EMEI EMEIEF CMEI CEF CED EC CAIC EE EM EMEB EMEFM EEF EEM " +
  "EEFM CIEP CE UE ETEC IF JI").split(" "));
const MINUSCULAS = new Set("de da do das dos e em na no".split(" "));

/** O Censo grava nomes em caixa alta; siglas ficam em maiúscula e o resto ganha a inicial maiúscula. */
export function nomeLegivel(nome: string): string {
  return nome.split(/\s+/).filter(Boolean).map((p, i) => {
    if (SIGLAS.has(p) || !/[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/i.test(p)) return p;
    if (i > 0 && MINUSCULAS.has(p.toLowerCase())) return p.toLowerCase();
    return p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
  }).join(" ");
}

/** "25" a partir de 10 km; "4,5" abaixo (uma casa decimal ajuda quando a distância é curta). */
export function km(x: number): string {
  return x >= 10 ? String(redondo(x)) : (Math.round(x * 10) / 10).toFixed(1).replace(".", ",");
}

export function mil(n: number): string {
  return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
}

export function pct(x: number): string {
  const v = x * 100;
  const t = v >= 10 || v === 0 ? String(Math.round(v)) : v.toFixed(1).replace(/\.0$/, "").replace(".", ",");
  return t + "%";
}

export function listaPt(itens: string[]): string {
  if (itens.length <= 1) return itens.join("");
  return itens.slice(0, -1).join(", ") + " e " + itens[itens.length - 1];
}

export function ordenarEtapas(etapas: string[]): string[] {
  return [...etapas].sort((a, b) => ORDEM_ETAPAS.indexOf(a as never) - ORDEM_ETAPAS.indexOf(b as never));
}

/** "da pré-escola ao 9º ano", "nos anos iniciais", "na creche". */
export function faixaEtapas(etapas: string[]): string {
  const e = ordenarEtapas(etapas);
  if (e.length === 1) return (e[0] === "creche" || e[0] === "pre_escola" ? "na " : e[0] === "medio" ? "no " : "nos ") +
    ETAPA_ROTULO[e[0]];
  return `${ETAPA_INICIO[e[0]]} ${ETAPA_FIM[e[e.length - 1]]}`;
}

export function horas(min: number): string {
  const t = redondo(min);
  const h = Math.floor(t / 60);
  const m = t % 60;
  return h ? `${h} h${m ? ` ${String(m).padStart(2, "0")} min` : ""}` : `${m} min`;
}

export function plural(n: number, um: string, varios: string): string {
  return `${mil(n)} ${n === 1 ? um : varios}`;
}
