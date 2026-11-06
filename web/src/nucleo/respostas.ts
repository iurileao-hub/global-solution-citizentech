/**
 * O TEXTO de cada resposta, igual ao do terminal (src/assistente/respostas.py, modelo B). Serve ao contrato
 * (data/regressao_web.json confere palavra por palavra) e ao botão "Copiar texto", para colar no WhatsApp.
 * A tela não usa este texto: monta o HTML a partir dos mesmos dados (src/app/).
 */

import type { Base, Registro } from "./base";
import type { EscolaNome } from "./escolas";
import { type BlocoFechamentos, textoBloco } from "./fechamentos";
import { ligacoesDaEscola, type Resposta } from "./nucleo";

export const NAO_OFICIAL = "Assistente NÃO OFICIAL, feito por estudantes. Não fala em nome de nenhum órgão público. " +
  "Confira sempre com a Secretaria de Educação, o Conselho de Educação, o Ministério Público ou a Defensoria.";
export const RODAPE = "(Não oficial: confira com o órgão responsável.)";

export const ONDE: Readonly<Record<string, string>> = {
  assentamento: "em área de assentamento", "indígena": "em terra indígena",
  quilombola: "em comunidade quilombola", "comunidade tradicional": "em área de comunidade tradicional",
};
export const ETAPA: Readonly<Record<string, string>> = {
  creche: "creche", pre_escola: "pré-escola", anos_iniciais: "anos iniciais (1º ao 5º ano)",
  anos_finais: "anos finais (6º ao 9º ano)", medio: "ensino médio",
};

export interface Receptora {
  c: number;
  n: string;
  rural: boolean;
  km: number;
  min?: number | null;
  chao?: number | null;
  etapas?: string[];
  m?: string | null;
  uf?: string | null;
}

export interface Rota {
  v: number;
  receptoras?: Receptora[];
  aviso?: string;
  sem_rota?: number;
  osm?: string;
  motivo?: string;
}

/** Registro completo de uma escola (data/escolas_campo.json.gz e os pedaços escolas/NNN.json). */
export interface Escola extends EscolaNome {
  n: string;
  m: string;
  uf: string;
  r: string | null;
  z: string;
  d: string | null;
  t: number;
  e: Record<string, number>;
  zr?: number | null;
  tp?: number | null;
  s: Record<string, number>;
  geo: boolean;
  rota: Rota | null;
}

/**
 * Arredondamento do `f"{x:.0f}"` e do `round()` do Python: no empate exato (12,5) vai para o PAR. O toFixed e o
 * Math.round do JavaScript sobem no empate, e "13 km" no lugar de "12 km" quebraria o contrato.
 */
export function redondo(x: number): number {
  const f = Math.floor(x);
  const d = x - f;
  if (d > 0.5) return f + 1;
  if (d < 0.5) return f;
  return f % 2 === 0 ? f : f + 1;
}

export function data(iso: string): string {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

export function tempo(minutos: number): string {
  const total = redondo(minutos);
  const h = Math.floor(total / 60);
  const m = total % 60;
  return !h ? `${m} min` : !m ? `${h} h` : `${h} h ${String(m).padStart(2, "0")} min`;
}

/** Abaixo disso, ida e volta, é a mesma coordenada pública (escolas que dividem prédio ou endereço). */
export const MESMO_LUGAR_KM = 1;

/**
 * Distância para dizer "pelo menos": arredonda PARA BAIXO, senão o piso passaria do valor calculado (24,9 km viraria
 * "pelo menos 25"). Inteiro a partir de 10 km; uma casa decimal abaixo disso. Igual a respostas.km_piso do Python.
 */
export function kmPiso(x: number): string {
  if (x >= 10) return String(Math.floor(x + 1e-9));
  return (Math.floor(x * 10 + 1e-9) / 10).toFixed(1).replace(".", ",");
}

export function lugarEscola(e: { m: string | null; uf: string | null }): string {
  return e.m && e.uf ? `${e.m}/${e.uf}` : "município não informado no Censo";
}

/** O aviso do pré-cálculo, corrigido onde dizia "sem matrícula" de escola que tem alunos, mas só fora das etapas
 * que a busca de receptoras usa (EJA ou educação profissional, por exemplo). */
export function avisoRota(rota: Rota, e: Escola): string {
  if (rota.motivo === "sem_matricula" && e.t) {
    return "A escola não tem alunos nas etapas da creche ao ensino médio regular, que a busca de escolas " +
      "receptoras usa: não há receptoras a calcular.";
  }
  return rota.aviso || "";
}

export function fonte(r: Registro): string {
  const ref = r.referencia;
  if (r.dados) {
    return `Fonte: ${ref.titulo}: ${ref.url} . Os totais foram contados pelo projeto; o texto desta ` +
      `orientação foi conferido em ${data(r.data_verificacao)}.`;
  }
  return `Fonte: ${ref.titulo}. Conferida em ${data(r.data_verificacao)} em ${ref.url}`;
}

function item(base: Base, rid: string): string {
  return `  [${rid}] ${base.registros.get(rid)!.pergunta}`;
}

export function avisoParcial(fora: string[]): string {
  return "Atenção: respondi com a orientação mais próxima, mas ela não fala de " +
    fora.map((p) => `"${p}"`).join(", ") + ". Se a sua dúvida é sobre isso, esta base não tem a " +
    "resposta: confirme com o órgão responsável.";
}

export function sugestoes(base: Base, ids: string[]): string {
  return "Talvez também interesse:\n" + ids.map((x) => item(base, x)).join("\n");
}

export function orientacao(base: Base, rid: string, extras: string[] = [], fora: string[] = [],
  numeros: BlocoFechamentos | null = null): string {
  const r = base.registros.get(rid)!;
  if (fora.length) return avisoParcial(fora) + "\n\n" + orientacao(base, rid, extras, [], numeros);
  const tema = base.temas[r.tema];
  const linhas = [`Assunto: ${r.pergunta}  [${tema.nome}]`, "", r.orientacao];
  if (numeros) linhas.push("", textoBloco(numeros));
  linhas.push("", fonte(r));
  if (r.confirmar) linhas.push("", "Confirme: " + r.confirmar);
  const rel = (r.relacionados ?? []).slice(0, 3);
  if (rel.length) linhas.push("", "Para continuar:", ...rel.map((x) => item(base, x)));
  if (extras.length) linhas.push("", sugestoes(base, extras));
  return [...linhas, "", RODAPE].join("\n");
}

export function ambigua(base: Base, ids: string[]): string {
  return ["Sua pergunta combina com mais de um assunto. Qual deles?", ...ids.map((x) => item(base, x)),
    "Digite o código entre colchetes, ou reformule a pergunta."].join("\n");
}

export function semResposta(base: Base): string {
  const temas = Object.values(base.temas).map((t) => t.nome).join(", ");
  return [
    "Não encontrei, na base deste assistente, uma orientação confiável para essa pergunta. " +
    "Prefiro dizer isso a inventar uma resposta.",
    `Os assuntos que conheço são: ${temas}. Você pode escolher um deles no menu, reformular a ` +
    "pergunta com outras palavras, ou consultar uma escola pelo nome.",
    "Para uma dúvida fora desses assuntos: a Secretaria de Educação responde pela escola e pela " +
    "rede; a Defensoria Pública dá orientação jurídica de graça.",
    RODAPE,
  ].join("\n");
}

export function receptora(r: Receptora, origem: Escola): string {
  const onde = [r.rural ? "rural" : "urbana"];
  if (r.m || r.uf) onde.push(`${r.m || origem.m}/${r.uf || origem.uf}`);
  let texto: string;
  if (r.km < MESMO_LUGAR_KM) {
    // "0 km e 1 min" seria precisão falsa: é a mesma coordenada pública
    texto = `${r.n} (${onde.join(", ")}): no mesmo lugar ou quase (mesma localização pública)`;
  } else {
    const partes = [`${kmPiso(r.km)} km`];
    if (r.min !== undefined && r.min !== null) partes.push(tempo(r.min));
    texto = `${r.n} (${onde.join(", ")}): ${partes.join(" e ")}`;
    if ((r.chao ?? 0) >= 0.5) texto += `, dos quais ${kmPiso(Math.min(r.chao!, r.km))} km de estrada de chão`;
  }
  if (r.etapas && r.etapas.length) {
    texto += recebeTodas(r, origem)
      ? "; recebe todas as etapas desta escola"
      : "; recebe só " + r.etapas.map((x) => ETAPA[x] ?? x).join(", ");
  }
  return texto + ".";
}

export function recebeTodas(r: Receptora, origem: Escola): boolean {
  const tem = new Set(r.etapas ?? []);
  return Object.keys(origem.e).every((k) => tem.has(k));
}

export function textoEscola(base: Base, e: Escola, fonteDados: string, dataVerif: string, extras: string[] = []):
  string {
  const local = e.z === "rural" ? "rural" : "urbana, mas a maioria dos alunos mora na zona rural";
  const etapas = Object.entries(e.e).map(([k, v]) => `${ETAPA[k]}: ${v}`).join("; ") || (e.t
    ? "nenhum da creche ao ensino médio regular; podem ser de EJA ou de educação profissional"
    : "sem matrícula informada");
  const anos = Object.keys(e.s).sort();
  const linhas = [
    `${e.n}, ${lugarEscola(e)} (código INEP ${e.c})`,
    `Escola ${e.r || "pública"} ${local}` + (e.d ? `, ${ONDE[e.d] ?? e.d}` : "") + ".",
    `Alunos em ${anos.length ? anos[anos.length - 1] : "último ano"}: ${e.t} (${etapas}).`,
  ];
  if (e.tp !== undefined && e.tp !== null) {
    linhas.push(`Usam transporte escolar público: ${e.tp}. Moram na zona rural: ${e.zr}.`);
  }
  if (anos.length > 1) linhas.push("Matrícula por ano: " + anos.map((a) => `${a}: ${e.s[a]}`).join(", ") + ".");
  const rota = e.rota;
  if (rota && rota.receptoras && rota.receptoras.length) {
    linhas.push("Escolas que poderiam receber os alunos (estrada por dia, ida e volta, PELO MENOS):");
    for (const r of rota.receptoras) linhas.push("  - " + receptora(r, e));
    if (avisoRota(rota, e)) linhas.push(avisoRota(rota, e));
    if (rota.sem_rota) {
      linhas.push(`Outras ${rota.sem_rota} escola(s) próxima(s) ficaram sem rota na malha viária ` +
        "e não entram na lista.");
    }
    const quando = rota.osm ? `, dados de ${data(rota.osm)}` : "";
    linhas.push(`Conta feita de escola a escola pela malha do OpenStreetMap${quando}. A casa de cada ` +
      "criança, as paradas do ônibus e a estrada na chuva deixam o trajeto real maior.");
  } else if (rota) {
    linhas.push((avisoRota(rota, e) || "Nenhuma rota por estrada foi calculada para esta escola.") +
      " Não vou estimar um número sem base.");
  } else if (!e.geo) {
    linhas.push(SEM_COORDENADA);
  } else {
    linhas.push(NAO_CALCULADA);
  }
  linhas.push(`Fonte: ${fonteDados} (dados baixados em ${data(dataVerif)}).`);
  const ids = ligacoesDaEscola(base, e);
  if (ids.length) linhas.push("", "Para continuar:", ...ids.map((x) => item(base, x)));
  if (extras.length) linhas.push("", sugestoes(base, extras));
  return [...linhas, "", RODAPE].join("\n");
}

export const SEM_COORDENADA = "A localização desta escola não é pública: o Catálogo de Escolas do INEP não traz a " +
  "coordenada dela (nem a base do Ipea, que copia o Catálogo). Sem isso, a distância até " +
  "outras escolas não pode ser calculada. Não vou estimar um número sem base. A localização " +
  "pode ser pedida ao INEP pela Lei de Acesso à Informação.";
export const NAO_CALCULADA = "A distância até as escolas que poderiam receber os alunos ainda não foi calculada para " +
  "esta escola. Não vou estimar um número sem base.";

/** Todas as escolas da lista no mesmo município (conhecido): a busca já filtrou pelo lugar. */
export function mesmoMunicipio(es: { m: string | null; uf: string | null }[]): boolean {
  return es.length > 1 && Boolean(es[0].m && es[0].uf) && es.every((e) => e.m === es[0].m && e.uf === es[0].uf);
}

export function textoListaEscolas<E extends EscolaNome>(resp: Extract<Resposta<E>, { tipo: "escola_ambigua" }>):
  string {
  const { achado, jaFiltrado, mostra } = resp;
  const es = achado.escolas;
  // todas no mesmo município: pedir o município de novo não ajuda (a pessoa já disse); só a ficha distingue
  const mesmo = mesmoMunicipio(es);
  const pedido = mesmo ? `, todas em ${es[0].m}/${es[0].uf}. Para saber qual é a sua, abra a ficha de cada uma`
    : jaFiltrado ? "" : ". Para escolher, informe o município e a UF";
  const nUfs = new Set(es.map((e) => e.uf)).size;
  const onde = nUfs > 1 && es.length > 8 ? `, em ${nUfs} UFs` : "";
  const cauda = es.length > mostra.length ? `. Algumas delas (${mostra.length} de ${achado.total}):` : ":";
  return [
    `Encontrei ${achado.total} escolas com essas palavras no nome${onde}${pedido}${cauda}`,
    ...mostra.map((e) => `  ${e.c}  ${e.n}, ${lugarEscola(e)}`),
    mesmo ? "Digite o código INEP (o número da esquerda) para abrir a ficha." : "Ou digite o código INEP (o número da esquerda).",
  ].join("\n");
}

/**
 * Texto completo de uma resposta. `escolaDe` devolve o registro completo (na web, do pedaço já baixado).
 */
export function textoResposta<E extends EscolaNome>(base: Base, resp: Resposta<E>,
  escolaDe: (c: number) => Escola, fonteDados: string, dataVerif: string): string {
  switch (resp.tipo) {
    case "vazia": return resp.mensagem;
    case "codigo": return orientacao(base, resp.rid, [], [], resp.numeros);
    case "unica": return orientacao(base, resp.rid, resp.extras, resp.fora, resp.numeros);
    case "ambigua": return ambigua(base, resp.ids);
    case "escola": return textoEscola(base, escolaDe(resp.codigo), fonteDados, dataVerif, resp.extras);
    case "escola_ambigua": return textoListaEscolas(resp);
    case "nenhuma": return semResposta(base);
  }
}
