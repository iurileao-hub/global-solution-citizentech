/**
 * O simulador "e se estas escolas fecharem?": o diagnóstico de um PLANO de fechamento num município.
 *
 * Rotas:
 *   #/simular                        escolher o município
 *   #/simular?f=<código>             vindo da ficha: descobre o município da escola e abre o plano com ela
 *   #/simular/<lugar>?f=...&i=...    o plano (escolas que fecham) e as indicações da prefeitura, no link
 *
 * A conta é a de src/assistente/simulacao.py (espelho em ../nucleo/simulacao.ts, preso ao contrato). Regras de texto
 * do projeto: o número é PISO ("pelo menos"); a distância é da estrada entre a escola fechada e a receptora, não o
 * quanto cada criança anda a mais; crianças sem destino calculado aparecem ANTES de qualquer número; sem "deve" ou
 * "não deve" fechar.
 */

import { lugarDaEscola, lugares, municipioSim, versao } from "../dados";
import { h, trocar } from "../dom";
import { vivo } from "../estado";
import { ETAPA_ANOS, ETAPA_ROTULO, horas, km, listaPt, mil, nomeLegivel, ordenarEtapas, pct, plural, UF_NOME } from "../formato";
import { data, RODAPE } from "../nucleo/respostas";
import {
  type Alocacao, escreverCenario, type EscolaSim, ESGOTADA, lerCenario, menoresQue, type Municipio, NENHUMA_OFERECE,
  type Resultado, type ResumoEscola, simular,
} from "../nucleo/simulacao";
import { normalizar } from "../nucleo/texto";
import { botaoCompartilhar, carregando } from "./componentes";
import { mapaPlano, mapaPronto, marcas, MAX_MAPA } from "./mapa-plano";

/** Abaixo de 1 km por dia é a mesma coordenada pública (o mesmo critério da ficha, MESMO_LUGAR_KM em ficha.ts). */
const MESMO_LUGAR_KM = 1;
const kmDia = (x: number) => (x < MESMO_LUGAR_KM ? "menos de 1 km" : `${km(x)} km`);

const MOTIVO: Readonly<Record<string, string>> = {
  sem_coordenada: "a escola não tem coordenada pública no Catálogo de Escolas do INEP",
  origem_longe: "a escola fica longe da estrada mapeada no OpenStreetMap",
  sem_rota: "não há rota por estrada na malha viária pública",
  sem_candidata: "não há escola receptora num raio calculável",
  sem_matricula: "sem alunos nas etapas que a busca usa",
  nao_calculada: "a rota não foi calculada",
  [ESGOTADA]: "todas as receptoras calculadas que oferecem a etapa também fecham neste plano",
  [NENHUMA_OFERECE]: "nenhuma das 10 receptoras calculadas oferece a etapa",
};
const ROTULO_KM: Readonly<Record<string, string>> = {
  ate_10: "até 10 km", "10_a_30": "de 10 a 30 km", "30_a_50": "de 30 a 50 km", "50_a_100": "de 50 a 100 km",
  "100_ou_mais": "100 km ou mais",
};
const ROTULO_MIN: Readonly<Record<string, string>> = {
  ate_30: "até 30 min", "30_a_60": "de 30 min a 1 h", "60_a_120": "de 1 h a 2 h", "120_ou_mais": "2 h ou mais",
};
const ATALHO_PADRAO = 30;

// No papel, toda escola do plano sai aberta (um <details> fechado não imprime o conteúdo); depois volta como estava.
// Registrado uma vez, quando o módulo carrega.
window.addEventListener("beforeprint", () => {
  for (const d of document.querySelectorAll<HTMLDetailsElement>("details.sim-escola:not([open])")) {
    d.open = true;
    d.dataset.reabrir = "1";
  }
});
window.addEventListener("afterprint", () => {
  for (const d of document.querySelectorAll<HTMLDetailsElement>("details.sim-escola[data-reabrir]")) {
    d.open = false;
    delete d.dataset.reabrir;
  }
});

const criancas = (q: number) => plural(q, "criança", "crianças");
const etapaRotulo = (k: string) => ETAPA_ROTULO[k] + (ETAPA_ANOS[k] ? ` (${ETAPA_ANOS[k]})` : "");
const lugarTexto = (m: Municipio) => (m.uf === "DF" ? "Distrito Federal" : `${m.municipio}, ${UF_NOME[m.uf] ?? m.uf}`);

interface Estado {
  mun: Municipio;
  fechar: Set<number>;
  indicacoes: Record<string, number>;
  /** escolas do plano já mostradas e as que a pessoa deixou abertas: refazer a tela não fecha o que ela abriu */
  vistas: Set<number>;
  abertas: Set<number>;
  /** escolas do plano com o quadro "a prefeitura já indicou?" aberto */
  indicarAbertas: Set<number>;
  /** o plano de antes do atalho ou do "desmarcar todas", para o botão Desfazer */
  desfazer: { fechar: Set<number>; indicacoes: Record<string, number> } | null;
  /** o que mudou por último, para o leitor de tela (trocar uma indicação não muda a contagem do plano) */
  anuncio: string;
}

function link(e: Estado): string {
  const q = escreverCenario(e.fechar, e.indicacoes);
  return `#/simular/${e.mun.lugar}${q ? "?" + q : ""}`;
}

// ---------- escolher o município ----------

async function telaEscolher(main: HTMLElement, g: number, nota: string | null = null): Promise<void> {
  trocar(main, carregando("Abrindo a lista de municípios..."));
  const tabela = await lugares();
  if (!vivo(g)) return;
  const entrada = h("input", { id: "sim-municipio", type: "search", autocomplete: "off", spellcheck: "false",
    placeholder: "Ex.: Muniz Freire, Monte Santo BA" });
  const lista = h("ul", { class: "sim-municipios", "aria-live": "polite" });
  const atualizar = () => {
    const termos = normalizar(entrada.value).split(" ").filter(Boolean);
    if (!termos.length) {
      trocar(lista);
      return;
    }
    const achados = tabela.map(([uf, m], i) => ({ uf, m, i, alvo: normalizar(`${m} ${uf} ${UF_NOME[uf] ?? ""}`) }))
      .filter((x) => x.m && termos.every((t) => x.alvo.split(" ").some((p) => p.startsWith(t))))
      .slice(0, 12);
    trocar(lista, achados.length
      ? achados.map((x) => h("li", null, h("a", { href: `#/simular/${x.i}` }, `${x.m}, ${UF_NOME[x.uf] ?? x.uf}`)))
      : h("li", null, "Nenhum município com escola do campo no índice tem esse nome."));
  };
  entrada.addEventListener("input", atualizar);
  document.title = "E se estas escolas fecharem? Escola em Pauta";
  trocar(main, h("section", { class: "simulador" },
    h("h1", null, "E se estas escolas fecharem?"),
    h("p", { class: "manchete" }, "Fechamento de escola costuma vir em plano: a Secretaria reordena a rede e fecha várias de " +
      "uma vez. Aqui você monta o plano e vê para onde iria cada etapa de cada escola, e quanta estrada."),
    nota ? h("p", { class: "aviso", role: "note" }, nota) : null,
    h("form", { class: "busca", role: "search", onsubmit: (ev: Event) => {
      ev.preventDefault();
      // "Ir" no teclado do celular: abre o primeiro município da lista
      const primeiro = lista.querySelector("a");
      if (primeiro) location.hash = primeiro.getAttribute("href")!;
    } },
      h("label", { for: "sim-municipio" }, "Município"), h("div", { class: "busca-linha" }, entrada)),
    lista,
    h("p", { class: "legenda" }, "Também dá para começar pela ficha de uma escola: no fim dela, \"E se outras escolas também fecharem?\".")));
  entrada.focus();
}

// ---------- o plano ----------

const alunos = (q: number) => plural(q, "aluno", "alunos");
const somaEtapas = (x: EscolaSim) => Object.values(x.e).reduce((s, v) => s + v, 0);
const maiuscula = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

/** "56 alunos: pré-escola, anos iniciais e anos finais". O número é o total do Censo, o mesmo do atalho "menos de N
 * alunos"; quando a conta usa menos (EJA e outras modalidades ficam fora), a diferença aparece escrita. */
function descreverEscola(x: EscolaSim): string {
  const soma = somaEtapas(x);
  const etapas = listaPt(ordenarEtapas(Object.keys(x.e)).map((k) => ETAPA_ROTULO[k]));
  if (!soma) return `${alunos(x.t)}, nenhum da creche ao ensino médio regular`;
  return soma === x.t ? `${alunos(x.t)}: ${etapas}` : `${alunos(x.t)}, ${mil(soma)} da creche ao ensino médio regular: ${etapas}`;
}

interface Montagem {
  el: HTMLDetailsElement;
  /** depois de qualquer mudança: marca as caixas e atualiza o resumo do topo da lista */
  sincronizar: () => void;
  abrir: () => void;
}

/** Fecha a lista e leva a tela (e o foco) ao começo do resultado. */
function irAoResultado(): void {
  const m = document.getElementById("sim-montagem") as HTMLDetailsElement | null;
  // plano vazio: a lista fica aberta (o resultado só pede para marcar uma escola nela)
  if (m && m.querySelector("input[type=checkbox][id^='sim-']:checked")) m.open = false;
  const alvo = document.getElementById("sim-resultado");
  alvo?.scrollIntoView({ block: "start" });
  alvo?.focus({ preventScroll: true });
}

function montagem(e: Estado, mudou: () => void): Montagem {
  const escolas = [...e.mun.escolas].sort((a, b) => a.n.localeCompare(b.n, "pt-BR"));
  const caixas = new Map<number, HTMLInputElement>();
  const itens = escolas.map((x) => {
    const id = `sim-${x.c}`;
    const cx = h("input", { type: "checkbox", id });
    cx.checked = e.fechar.has(x.c);
    cx.addEventListener("change", () => {
      if (cx.checked) e.fechar.add(x.c);
      else e.fechar.delete(x.c);
      e.desfazer = null;
      mudou();
    });
    caixas.set(x.c, cx);
    return h("li", { "data-nome": normalizar(x.n), "data-c": String(x.c) }, cx,
      h("label", { for: id }, h("span", { class: "sim-nome" }, nomeLegivel(x.n)),
        h("span", { class: "legenda" }, descreverEscola(x)),
        x.r.length ? null : h("span", { class: "sim-selo" }, "sem rota calculada")));
  });
  const ul = h("ul", { class: "sim-escolas" + (escolas.length > 12 ? " longa" : "") }, itens);

  // filtros: pelo nome e "só as marcadas" (municípios grandes, como Santarém com 317 escolas)
  const texto = escolas.length > 12
    ? h("input", { type: "search", class: "sim-filtro", "aria-label": "Filtrar as escolas pelo nome", placeholder: "Filtrar pelo nome" })
    : null;
  const soMarcadas = h("input", { type: "checkbox", id: "sim-so-marcadas" });
  const contagem = h("span", { class: "legenda", "aria-live": "polite" });
  const filtrar = () => {
    const t = texto ? normalizar(texto.value) : "";
    let vis = 0;
    for (const li of ul.children as HTMLCollectionOf<HTMLElement>) {
      const c = Number(li.dataset.c);
      li.hidden = (Boolean(t) && !li.dataset.nome!.includes(t)) || (soMarcadas.checked && !e.fechar.has(c));
      if (!li.hidden) vis++;
    }
    contagem.textContent = vis === escolas.length ? "" : `Mostrando ${mil(vis)} de ${mil(escolas.length)}.`;
  };
  texto?.addEventListener("input", filtrar);
  soMarcadas.addEventListener("change", filtrar);

  // atalho: mostra antes o que vai marcar, porque substitui o que já está marcado
  const n = h("input", { type: "number", id: "sim-menos", min: "1", max: "9999", value: String(ATALHO_PADRAO), inputmode: "numeric" });
  const previa = h("p", { class: "legenda sim-previa", "aria-live": "polite" });
  const marcar = h("button", { type: "button", class: "botao secundario" }, "Marcar");
  const desfazer = h("button", { type: "button", class: "botao-texto", hidden: true }, "Desfazer");
  const limite = () => Math.max(1, Math.floor(Number(n.value) || ATALHO_PADRAO));
  const atualizarPrevia = () => {
    const cs = new Set(menoresQue(e.mun, limite()));
    const sel = e.mun.escolas.filter((x) => cs.has(x.c));
    const semRota = sel.filter((x) => !x.r.length).length;
    const igual = sel.length > 0 && sel.length === e.fechar.size && sel.every((x) => e.fechar.has(x.c));
    marcar.disabled = !sel.length || igual;
    marcar.textContent = sel.length && !igual ? `Marcar ${plural(sel.length, "escola", "escolas")}` : "Marcar";
    previa.textContent = !sel.length ? `Nenhuma escola com menos de ${mil(limite())} alunos.`
      : igual ? `${sel.length === 1 ? "É a escola marcada" : "São as escolas marcadas"} agora.`
      : `${plural(sel.length, "escola", "escolas")}, ${alunos(sel.reduce((s, x) => s + x.t, 0))}` +
        (semRota ? `; ${semRota === sel.length ? (sel.length === 1 ? "ela não tem" : "nenhuma tem") : `${mil(semRota)} sem`} rota calculada` : "") +
        ". Substitui o que está marcado agora.";
  };
  n.addEventListener("input", atualizarPrevia);
  marcar.addEventListener("click", () => {
    e.desfazer = { fechar: new Set(e.fechar), indicacoes: { ...e.indicacoes } };
    e.fechar = new Set(menoresQue(e.mun, limite()));
    mudou();
  });
  desfazer.addEventListener("click", () => {
    if (e.desfazer) [e.fechar, e.indicacoes] = [e.desfazer.fechar, e.desfazer.indicacoes];
    e.desfazer = null;
    mudou();
  });
  const limpar = h("button", { type: "button", class: "botao-texto", onclick: () => {
    e.desfazer = e.fechar.size ? { fechar: new Set(e.fechar), indicacoes: { ...e.indicacoes } } : null;
    e.fechar.clear();
    e.indicacoes = {};
    mudou();
  } }, "Desmarcar todas");

  const resumo = h("span", { class: "legenda" });
  const el = h("details", { class: "sim-montagem nao-imprime", id: "sim-montagem", open: e.fechar.size ? null : true },
    h("summary", null, h("span", { class: "sim-montagem-t" }, "Escolas do plano"), resumo),
    h("p", null, `As ${mil(escolas.length)} escolas do campo de ${e.mun.municipio} no índice. Marque as que fechariam: o resultado ` +
      "muda na hora."),
    h("div", { class: "sim-atalho" },
      h("label", { for: "sim-menos" }, "Atalho: todas com menos de"), n, h("span", null, "alunos"), marcar, desfazer),
    previa,
    escolas.length > 12 ? h("div", { class: "sim-filtros" }, texto,
      h("label", { class: "sim-so" }, soMarcadas, " Só as marcadas"), contagem) : null,
    ul,
    h("p", { class: "sim-fim-lista" }, limpar, h("button", { type: "button", class: "botao", onclick: () => irAoResultado() },
      "Ver o resultado")));
  const sincronizar = () => {
    for (const [c, cx] of caixas) cx.checked = e.fechar.has(c);
    resumo.textContent = ` ${mil(e.fechar.size)} de ${mil(escolas.length)} marcadas`;
    desfazer.hidden = !e.desfazer;
    if (soMarcadas.checked) filtrar();
    atualizarPrevia();
  };
  sincronizar();
  const abrir = () => {
    el.open = true;
    el.scrollIntoView({ block: "start" });
    (texto ?? caixas.values().next().value)?.focus({ preventScroll: true });
  };
  return { el, sincronizar, abrir };
}

function semDestino(r: Resultado): HTMLElement | null {
  const total = Object.values(r.sem_destino).reduce((a, b) => a + b, 0);
  if (!total) return null;
  return h("div", { class: "sem-numero", role: "note" },
    h("p", { style: "margin:0" }, h("b", null, `${total === r.criancas ? "Nenhuma" : mil(total)} das ${criancas(r.criancas)} `),
      total === r.criancas ? "tem destino calculado." : total === 1 ? "fica sem destino calculado e não entra nas contas abaixo." :
        "ficam sem destino calculado e não entram nas contas abaixo."),
    h("ul", { style: "margin:.4rem 0 0" }, Object.entries(r.sem_destino).sort((a, b) => b[1] - a[1])
      .map(([m, q]) => h("li", null, `${mil(q)}: ${MOTIVO[m] ?? m}.`))),
    r.sem_destino[ESGOTADA] ? h("p", { style: "margin:.4rem 0 0" }, "Para essas, o plano fecha também as escolas que as " +
      "receberiam. Calculamos as 10 receptoras mais próximas de cada escola; além delas, a conta não vai.") : null);
}

/** Os números do plano em cartões: o que muda, o trajeto, para onde (outro município ou chão) e quem mais cresce. */
function cartoes(r: Resultado): HTMLElement {
  const sem = r.criancas - r.com_destino;
  // com crianças sem destino, os outros cartões falam só das que têm: o texto diz de quantas
  const das = sem && r.com_destino ? `Das ${mil(r.com_destino)} com destino: ` : "";
  const itens: [string, string][] = [[mil(r.criancas),
    `${r.criancas === 1 ? "criança" : "crianças"} de ${plural(r.fechadas.length, "escola", "escolas")} mudariam de escola` +
    (sem ? `; ${mil(sem)} sem destino calculado` : "") +
    (r.fora_das_etapas ? ` (e ${mil(r.fora_das_etapas)} de EJA ou outra modalidade, fora da conta)` : "")]];
  const com = r.alocacoes.filter((a) => a.destino !== null && a.min !== null && a.km !== null);
  if (com.length) {
    // sempre a mesma pergunta (o maior trajeto), para dois planos serem comparáveis; a contagem por faixa está em "Quanta estrada"
    const max = com.reduce((m, a) => (a.min! > m.min! ? a : m));
    itens.push(max.km! < MESMO_LUGAR_KM
      ? ["menos de 1 km", `${das}todas iriam para escola no mesmo lugar ou quase`]
      : [horas(max.min!), `${das}o maior trajeto de ônibus do plano, ida e volta por dia, de escola a escola (${kmDia(max.km!)}). ` +
        "Pelo menos isso"]);
  }
  if (r.outro_municipio) itens.push([mil(r.outro_municipio), `${das}${r.outro_municipio === 1 ? "iria" : "iriam"} para escola de outro município`]);
  else if (r.metade_chao) itens.push([mil(r.metade_chao), `${das}${r.metade_chao === 1 ? "iria" : "iriam"} por estrada com metade ou mais de chão`]);
  const maior = r.receptoras.filter((x) => x.mat).sort((a, b) => b.recebe / b.mat! - a.recebe / a.mat! || b.recebe - a.recebe)[0];
  if (maior) {
    itens.push([`+${pct(maior.recebe / maior.mat!)}`, `o maior aumento proporcional de matrícula: ${nomeLegivel(maior.n)} tem ` +
      `${mil(maior.mat!)} e ganharia mais ${mil(maior.recebe)} (passaria a ${mil(maior.mat! + maior.recebe)}). Não sabemos se cabe`]);
  }
  return h("ul", { class: "sim-cartoes" }, itens.map(([num, txt]) => h("li", null, h("b", null, num), h("span", null, txt))));
}

function fichaFecha(r: Resultado): HTMLElement | null {
  if (!r.ficha_fecha) return null;
  return h("p", { class: "aviso", role: "note" }, h("strong", null, "A ficha sozinha não basta: "),
    `para ${criancas(r.ficha_fecha)}, a escola que a ficha individual aponta como destino também fecha neste plano.`);
}

const KM_ALEM: Readonly<Record<string, string>> = {
  ate_10: "a mais de 10 km", "10_a_30": "a mais de 30 km", "30_a_50": "a mais de 50 km", "50_a_100": "a 100 km ou mais",
};
const MIN_ALEM: Readonly<Record<string, string>> = { ate_30: "a mais de 30 min", "30_a_60": "a 1 h ou mais", "60_a_120": "a 2 h ou mais" };

function faixas(r: Resultado): HTMLElement | null {
  if (!r.com_destino) return null;
  const sem = r.criancas - r.com_destino;
  const tabela = (titulo: string, dados: Record<string, number>, rotulos: Readonly<Record<string, string>>,
    alem: Readonly<Record<string, string>>) => {
    const chaves = Object.keys(dados);
    let ultima = chaves.length - 1;
    while (ultima > 0 && !dados[chaves[ultima]]) ultima--;
    const maior = Math.max(1, ...Object.values(dados));
    // faixas vazias no fim viram uma frase: "nenhuma a mais de 30 km" é argumento, não linha de zero
    const nenhuma = ultima < chaves.length - 1 ? `Nenhuma ${alem[chaves[ultima]]}.` : null;
    return h("div", null, h("table", { class: "quadro sim-faixas" }, h("caption", null, titulo),
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Por dia, ida e volta"), h("th", { scope: "col", class: "num" }, "Crianças"),
        h("th", { scope: "col", "aria-hidden": "true" }))),
      h("tbody", null, chaves.slice(0, ultima + 1).map((k) => h("tr", null, h("th", { scope: "row" }, rotulos[k]),
        h("td", { class: "num" }, mil(dados[k])),
        h("td", { class: "sim-barra-cel", "aria-hidden": "true" },
          dados[k] ? h("span", { class: "sim-barra", style: `width:${(100 * dados[k]) / maior}%` }) : null))))),
      nenhuma ? h("p", { class: "sim-nenhuma" }, nenhuma) : null);
  };
  const extras: string[] = [];
  if (r.metade_chao) extras.push(`${criancas(r.metade_chao)} ${r.metade_chao === 1 ? "iria" : "iriam"} por estrada com metade ou mais de chão.`);
  if (r.outro_municipio) {
    extras.push(`${criancas(r.outro_municipio)} ${r.outro_municipio === 1 ? "iria" : "iriam"} para escola de outro município. ` +
      "A prefeitura pode indicar outra.");
  }
  return h("section", { class: "sim-s-faixas" },
    h("h2", null, "Quanta estrada"),
    h("p", null, sem ? `Das ${criancas(r.com_destino)} com destino calculado. ` : "",
      "Estrada entre a escola fechada e a que receberia: ", h("b", null, "é o mínimo do caminho do ônibus"),
      ", não o quanto cada criança anda a mais."),
    h("div", { class: "sim-faixas-par" }, tabela("Distância", r.faixas_km, ROTULO_KM, KM_ALEM),
      tabela("Tempo de ônibus", r.faixas_min, ROTULO_MIN, MIN_ALEM)),
    extras.map((x) => h("p", null, x)));
}

function nomeDe(mun: Municipio, c: number): string {
  for (const e of mun.escolas) {
    if (e.c === c) return e.n;
    const r = e.r.find((x) => x[0] === c);
    if (r) return r[1];
  }
  return String(c);
}

const marcaLetra = (l: string | undefined) => (l ? h("span", { class: "sim-letra", "aria-hidden": "true" }, l) : null);
const marcaNumero = (n: number | undefined) => (n ? h("span", { class: "sim-num", "aria-hidden": "true" }, String(n)) : null);

/** O select da indicação de uma etapa (só existe quando alguma das 10 receptoras oferece a etapa). */
function seletor(e: Estado, x: EscolaSim, a: Alocacao, mudou: () => void): HTMLElement | null {
  const chave = `${a.origem}:${a.etapa}`;
  const opcoes = x.r.filter((r) => r[6].includes(a.etapa));
  if (!opcoes.length) return null;
  const id = `ind-${chave.replace(":", "-")}`;
  const sel = h("select", { id }, h("option", { value: "" }, "A mais próxima que oferece a etapa (regra)"),
    opcoes.map((r) => h("option", { value: String(r[0]), disabled: e.fechar.has(r[0]) || null },
      `${nomeLegivel(r[1])}, ${r[3] < MESMO_LUGAR_KM ? "no mesmo lugar" : `${kmDia(r[3])}/dia`}${r[9] || r[10] ? ", outro município" : ""}` +
      (e.fechar.has(r[0]) ? ", fecha neste plano" : ""))));
  const ind = e.indicacoes[chave];
  sel.value = ind !== undefined && opcoes.some((r) => r[0] === ind) ? String(ind) : "";
  sel.addEventListener("change", () => {
    if (sel.value) e.indicacoes[chave] = Number(sel.value);
    else delete e.indicacoes[chave];
    e.anuncio = `${maiuscula(ETAPA_ROTULO[a.etapa])} de ${nomeLegivel(x.n)}: ` +
      (sel.value ? `destino indicado, ${sel.selectedOptions[0].textContent}.` : "volta a valer a regra.");
    mudou();
  });
  return h("div", { class: "sim-indicar-linha" }, h("label", { for: id }, `${maiuscula(etapaRotulo(a.etapa))}, ${criancas(a.n)}`), sel);
}

/** Uma escola do plano: as etapas agrupadas por destino ("pré-escola e anos iniciais, 36 crianças → 1 Alto Monforte"). */
function cartaoOrigem(e: Estado, s: ResumoEscola, al: Alocacao[], letra: string | undefined, numero: Map<number, number>,
  abrir: boolean, mudou: () => void): HTMLElement {
  const aberta = e.vistas.has(s.c) ? e.abertas.has(s.c) : abrir;
  if (aberta) e.abertas.add(s.c);
  e.vistas.add(s.c);
  const x = e.mun.escolas.find((y) => y.c === s.c)!;
  const grupos = new Map<string, Alocacao[]>();
  for (const a of al) {
    // mesma escola por motivos diferentes (regra e indicação) fica em linhas separadas: a etiqueta é de cada linha
    const k = a.destino === null ? `sem:${a.motivo}` : `${a.destino}:${a.indicada}`;
    grupos.set(k, [...(grupos.get(k) ?? []), a]);
  }
  const fluxos = [...grupos.values()].map((g) => {
    const a = g[0];
    const quantas = g.reduce((t, y) => t + y.n, 0);
    const de = h("div", { class: "sim-de" }, maiuscula(listaPt(g.map((y) => etapaRotulo(y.etapa)))), h("span", { class: "legenda" }, `, ${criancas(quantas)}`));
    let para: HTMLElement;
    if (a.destino === null) {
      para = h("div", { class: "sim-para sim-sem" }, h("span", { class: "sim-seta", "aria-hidden": "true" }, "→"),
        h("span", null, `Sem destino calculado: ${MOTIVO[a.motivo!] ?? a.motivo}.`));
    } else {
      const marcas = [a.outro_municipio ? "outro município" : "", a.indicada ? "indicada pela prefeitura" : ""].filter(Boolean);
      para = h("div", { class: "sim-para" }, h("span", { class: "sim-seta", "aria-hidden": "true" }, "→"),
        h("div", null, h("span", { class: "sr" }, "iriam para "), marcaNumero(numero.get(a.destino)),
          h("b", null, nomeLegivel(nomeDe(e.mun, a.destino))),
          marcas.map((m) => h("span", { class: "sim-etiqueta" }, m)),
          h("div", { class: "sim-km" }, a.km! < MESMO_LUGAR_KM ? "No mesmo lugar ou quase."
            : `Pelo menos ${kmDia(a.km!)}${a.min !== null ? ` e ${horas(a.min)} de ônibus` : ""} por dia, ida e volta.`)));
    }
    const avisos = g.filter((y) => y.aviso).map((y) => {
      const naLista = x.r.some((r) => r[0] === e.indicacoes[`${y.origem}:${y.etapa}`]);
      return h("p", { class: "sim-aviso" }, `${maiuscula(ETAPA_ROTULO[y.etapa])}: ` + (y.aviso === "indicada_fecha"
        ? "a escola indicada também fecha neste plano, valeu a regra."
        : naLista ? "a escola indicada não oferece esta etapa, valeu a regra."
        : "a escola indicada não está entre as 10 calculadas para esta escola, valeu a regra."));
    });
    return h("li", null, de, para, avisos);
  });
  const seletores = al.map((a) => seletor(e, x, a, mudou)).filter((y): y is HTMLElement => y !== null);
  const temIndicacao = al.some((a) => e.indicacoes[`${a.origem}:${a.etapa}`] !== undefined);
  let indicar: HTMLElement | null = null;
  if (seletores.length) {
    const d = h("details", { class: "sim-indicar nao-imprime", open: temIndicacao || e.indicarAbertas.has(s.c) || null },
      h("summary", null, "A prefeitura já indicou outro destino?"),
      h("p", { class: "legenda" }, "Escolha a escola indicada: a conta passa a usá-la."), seletores);
    d.addEventListener("toggle", () => (d.open ? e.indicarAbertas.add(s.c) : e.indicarAbertas.delete(s.c)));
    indicar = d;
  }
  const resumo = !s.criancas ? "sem alunos da creche ao ensino médio"
    : al.every((a) => a.destino === null) ? `${criancas(s.criancas)}, sem destino calculado`
    : `${criancas(s.criancas)}, ${s.destinos === 1 ? "um destino" : `${s.destinos} destinos`}` +
      (al.some((a) => a.destino === null) ? ", parte sem destino calculado" : "");
  const d = h("details", { class: "sim-escola", open: aberta || null },
    h("summary", null, marcaLetra(letra), h("span", null, h("b", null, nomeLegivel(s.n)), h("span", { class: "legenda" }, ` ${resumo}`))),
    s.ficha_fecha ? h("p", { class: "sim-aviso" }, "A escola que a ficha dela aponta também fecha neste plano.") : null,
    al.length ? h("ul", { class: "sim-fluxos" }, fluxos) : null,
    indicar,
    h("p", { class: "nao-imprime sim-ficha" }, h("a", { href: `#/escola/${s.c}` }, "Abrir a ficha desta escola")));
  d.addEventListener("toggle", () => {
    if (d.dataset.reabrir) return; // aberta só para imprimir (beforeprint): não é escolha da pessoa
    if (d.open) e.abertas.add(s.c);
    else e.abertas.delete(s.c);
  });
  return d;
}

function ordenadas(r: Resultado): ResumoEscola[] {
  return [...r.escolas].sort((a, b) => a.n.localeCompare(b.n, "pt-BR"));
}

/** Escolas sem nenhum destino, agrupadas pelo motivo (o do plano, como "as receptoras também fecham", que a ficha
 * individual não conhece). Escola com motivos diferentes por etapa entra em cada grupo. */
function porMotivo(juntas: ResumoEscola[], porEscola: Map<number, Alocacao[]>): HTMLElement {
  const grupos = new Map<string, ResumoEscola[]>();
  for (const s of juntas) {
    for (const m of new Set((porEscola.get(s.c) ?? []).map((a) => a.motivo ?? ""))) grupos.set(m, [...(grupos.get(m) ?? []), s]);
  }
  return h("div", null, [...grupos].sort((a, b) => b[1].length - a[1].length).map(([m, lista]) => h("div", null,
    h("p", { class: "sim-motivo" }, `${maiuscula(MOTIVO[m] ?? m)} (${plural(lista.length, "escola", "escolas")}):`),
    h("ul", null, lista.map((s) => h("li", null, h("a", { href: `#/escola/${s.c}` }, nomeLegivel(s.n)), `, ${criancas(s.criancas)}`))))));
}

function paraOnde(e: Estado, r: Resultado, mudou: () => void): HTMLElement {
  const porEscola = new Map<number, Alocacao[]>();
  for (const a of r.alocacoes) porEscola.set(a.origem, [...(porEscola.get(a.origem) ?? []), a]);
  const { letra, numero } = marcas(r);
  const abrir = r.fechadas.length <= MAX_MAPA;
  const nomes = new Map<number, string>();
  for (const s of r.escolas) nomes.set(s.c, nomeLegivel(s.n));
  for (const x of r.receptoras) nomes.set(x.c, nomeLegivel(x.n));
  const mapa = mapaPlano(r, nomes);
  // plano grande: as escolas sem nenhum destino calculado viram uma lista só no fim, em vez de um cartão cada
  const grande = r.fechadas.length > MAX_MAPA;
  const semNenhum = (s: ResumoEscola) => s.criancas > 0 && (porEscola.get(s.c) ?? []).every((a) => a.destino === null);
  const comCartao = ordenadas(r).filter((s) => !grande || !semNenhum(s));
  const juntas = grande ? ordenadas(r).filter(semNenhum) : [];
  return h("section", { class: "sim-s-etapas" },
    h("h2", { id: "sim-para-onde", tabindex: "-1" }, "Para onde iriam"),
    h("p", null, "Cada etapa vai para a escola mais próxima por estrada que a oferece e não fecha neste plano" +
      (r.alocacoes.some((a) => a.indicada) ? ", menos onde a prefeitura indicou outra (está marcado). " : ". "),
      h("span", { class: "so-impressao-inline" }, "\"Indicada pela prefeitura\" marca o destino que a prefeitura informou.")),
    grande ? mapa : null,
    h("div", { class: "sim-destinos" + (mapa && !grande ? " com-mapa" : "") }, grande ? null : mapa,
      h("div", { class: "sim-origens" }, comCartao.map((s) => cartaoOrigem(e, s, porEscola.get(s.c) ?? [], letra.get(s.c), numero, abrir, mudou)))),
    juntas.length ? h("div", { class: "sem-numero sim-juntas" },
      h("p", { style: "margin:0" }, h("b", null, `${plural(juntas.length, "escola", "escolas")} do plano sem nenhum destino calculado`),
        ` (${criancas(juntas.reduce((t, s) => t + s.criancas, 0))}), agrupadas pelo motivo.`),
      porMotivo(juntas, porEscola)) : null);
}

const CORTE = 20;

/** Tabela longa (municípios grandes): as primeiras CORTE linhas e um botão para o resto. No papel saem todas. */
function cortar(tabela: HTMLTableElement, oque: string): HTMLElement[] {
  // papéis explícitos: no celular a tabela vira blocos (display: block), e alguns navegadores esquecem que é tabela
  tabela.setAttribute("role", "table");
  for (const g of tabela.querySelectorAll("thead, tbody")) g.setAttribute("role", "rowgroup");
  for (const tr of tabela.querySelectorAll("tr")) tr.setAttribute("role", "row");
  for (const th of tabela.querySelectorAll("thead th")) th.setAttribute("role", "columnheader");
  for (const th of tabela.querySelectorAll("tbody th")) th.setAttribute("role", "rowheader");
  for (const td of tabela.querySelectorAll("td")) td.setAttribute("role", "cell");
  const linhas = [...tabela.tBodies[0].rows];
  if (linhas.length <= CORTE + 5) return [tabela];
  for (const tr of linhas.slice(CORTE)) tr.classList.add("sim-mais");
  const b = h("button", { type: "button", class: "botao-texto nao-imprime" }, `Mostrar ${oque} (${mil(linhas.length)})`);
  b.addEventListener("click", () => {
    tabela.classList.add("sim-todas");
    const primeira = linhas[CORTE].querySelector("th") ?? linhas[CORTE];
    primeira.setAttribute("tabindex", "-1");
    primeira.focus(); // o botão some: o foco vai para a primeira linha que apareceu
    b.remove();
  });
  return [tabela, b];
}

function quemRecebe(r: Resultado): HTMLElement | null {
  if (!r.receptoras.length) return null;
  return h("section", { class: "sim-s-recebe" },
    h("h2", null, "Quem recebe"),
    h("p", null, "O aumento é sobre a matrícula de hoje. O número de vagas e de turnos não é publicado: ",
      h("b", null, "não sabemos se cabe"), ", só quanto a escola cresceria."),
    cortar(h("table", { class: "quadro sim-empilha" },
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Escola"), h("th", { scope: "col", class: "num" }, "Recebe"),
        h("th", { scope: "col", class: "num" }, "Tem hoje"), h("th", { scope: "col", class: "num" }, "Aumento"))),
      h("tbody", null, r.receptoras.map((x, i, todas) => {
        const homonima = todas.some((y) => y !== x && y.n === x.n);
        const dobra = x.mat !== null && x.mat > 0 && x.recebe >= x.mat;
        const onde = [x.rural ? "rural" : "urbana", x.m || x.uf ? `em ${x.m ?? ""}${x.uf ? "/" + x.uf : ""}` : ""].filter(Boolean).join(", ");
        return h("tr", { class: dobra ? "destaque" : null },
          h("th", { scope: "row" }, marcaNumero(i + 1), nomeLegivel(x.n), h("br"), h("span", { class: "legenda" },
            `${onde}; ${listaPt(x.etapas.map((k) => ETAPA_ROTULO[k]))}${homonima ? `; código INEP ${x.c}` : ""}`)),
          h("td", { class: "num", "data-rotulo": "Recebe" }, `+${mil(x.recebe)}`),
          h("td", { class: "num", "data-rotulo": "Tem hoje" }, x.mat === null ? "?" : mil(x.mat)),
          h("td", { class: "num", "data-rotulo": "Aumento" }, x.mat ? `+${pct(x.recebe / x.mat)}` : "?",
            dobra ? h("span", { class: "sim-marca" }, " dobra ou mais") : null));
      }))), "todas as que recebem"));
}

function cadaEscola(r: Resultado): HTMLElement | null {
  if (r.escolas.length < 2) return null;
  const { letra } = marcas(r);
  const grande = r.escolas.length > CORTE + 5;
  const linhas = grande ? [...r.escolas].sort((a, b) => b.acolheria - a.acolheria || b.criancas - a.criancas || a.c - b.c) : ordenadas(r);
  return h("section", { class: "sim-s-escolas" },
    h("h2", null, "O que cada escola do plano sustenta"),
    h("p", null, "Pré-escola e anos iniciais: a Res. CNE/CEB 2/2008, art. 3º, pede que essas crianças estudem na própria " +
      "comunidade. A última coluna: se só esta escola saísse do plano (as outras marcadas continuam fechando), quantas crianças " +
      "das outras escolas marcadas iriam para ela, pela regra ou pela indicação da prefeitura. A tabela não diz qual escola fechar." +
      (grande ? " Em ordem do que receberia, depois do número de crianças." : "")),
    cortar(h("table", { class: "quadro sim-empilha" },
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Escola"), h("th", { scope: "col", class: "num" }, "Crianças"),
        h("th", { scope: "col", class: "num" }, "Pré-escola e anos iniciais"),
        h("th", { scope: "col", class: "num" }, "Se saísse do plano, receberia de outras escolas marcadas"))),
      h("tbody", null, linhas.map((s) => h("tr", null,
        h("th", { scope: "row" }, marcaLetra(letra.get(s.c)), nomeLegivel(s.n),
          s.ficha_fecha ? h("span", { class: "sim-marca" }, h("br"), "a escola da ficha dela também fecha") : null),
        h("td", { class: "num", "data-rotulo": "Crianças" }, mil(s.criancas)),
        h("td", { class: "num", "data-rotulo": "Pré-escola e anos iniciais" }, mil(s.pre_iniciais)),
        h("td", { class: "num", "data-rotulo": "Se saísse do plano, receberia" },
          s.acolheria ? `+${mil(s.acolheria)}` : "nenhuma de outra escola do plano"))))), "todas as escolas do plano"));
}

function comoContamos(r: Resultado): HTMLElement {
  return h("section", { class: "sim-s-como" },
    h("h2", null, "Como contamos"),
    h("ul", null,
      h("li", null, "Para cada escola fechada, olhamos as 10 escolas mais próximas por estrada (pré-cálculo pela malha do " +
        "OpenStreetMap). Cada etapa vai para a primeira delas que oferece a etapa e não fecha no plano."),
      h("li", null, "A distância é a da estrada entre a escola fechada e a que receberia, ida e volta por dia. É o mínimo do " +
        "caminho do ônibus: quem mora entre as duas escolas anda menos, quem mora do outro lado anda mais."),
      h("li", null, "A ficha de cada escola responde outra pergunta: a escola mais próxima que recebe TODAS as etapas de uma vez " +
        "(a família inteira num destino só). Por isso a distância aqui pode ser menor que a da ficha."),
      h("li", null, "A ordem dos fechamentos não muda nada: a conta parte sempre da escola de origem da criança, não de uma escola " +
        "que a receberia e também fecha."),
      h("li", null, "Não realocamos por falta de vaga, porque vagas e turnos não são públicos. Escolas urbanas e de outro município " +
        "não entram no plano: os alunos delas não estão no índice."),
      r.fora_das_etapas ? h("li", null, `${mil(r.fora_das_etapas)} alunos de EJA, educação profissional ou outra modalidade das ` +
        "escolas do plano não entram na conta (a busca de receptoras usa da creche ao ensino médio regular).") : null));
}

function resultado(e: Estado, r: Resultado, acoes: HTMLElement, mudou: () => void): HTMLElement[] {
  if (!r.fechadas.length) {
    return [h("p", { class: "sem-numero", role: "note" }, "Marque ao menos uma escola na lista para ver para onde iriam as crianças.")];
  }
  const { letra } = marcas(r);
  return [
    h("p", { class: "so-impressao" }, h("b", null, `Escolas do plano (${r.fechadas.length}): `),
      listaPt(ordenadas(r).map((s) => `${letra.get(s.c) ? letra.get(s.c) + ". " : ""}${nomeLegivel(s.n)}`)) + "."),
    r.aviso_fluvial ? h("p", { class: "aviso", role: "note" }, h("strong", null, "Atenção: "), "parte do transporte escolar " +
      "neste estado é por rio. A rota por estrada pode não ser o caminho das crianças.") : null,
    semDestino(r),
    cartoes(r),
    fichaFecha(r),
    acoes,
    paraOnde(e, r, mudou),
    faixas(r),
    quemRecebe(r),
    cadaEscola(r),
    comoContamos(r),
  ].filter((x): x is HTMLElement => x !== null);
}

export async function telaSimulador(main: HTMLElement, g: number, lugarTexto_: string | null, params: URLSearchParams):
  Promise<void> {
  const cenario = lerCenario(params);
  let lugar = lugarTexto_ !== null && /^\d+$/.test(lugarTexto_) ? Number(lugarTexto_) : null;
  if (lugar === null && cenario.fechar.length) {
    trocar(main, carregando("Procurando o município da escola..."));
    lugar = await lugarDaEscola(cenario.fechar[0]);
    if (!vivo(g)) return;
  }
  if (lugar === null) {
    await telaEscolher(main, g, cenario.fechar.length
      ? `O código ${cenario.fechar[0]} não é de escola do campo no índice. Escolha o município.` : null);
    return;
  }
  trocar(main, carregando("Abrindo as escolas do município..."));
  const tabela = await lugares();
  if (!vivo(g)) return;
  if (lugar <= 0 || lugar >= tabela.length) {
    document.title = "Município não encontrado: Escola em Pauta";
    trocar(main, h("div", { class: "erro", role: "alert" }, h("h1", null, "Município não encontrado"),
      h("p", null, "Este link não aponta para um município com escola do campo no índice. ",
        h("a", { href: "#/simular" }, "Escolher o município"), ".")));
    return;
  }
  const [mun, v] = await Promise.all([municipioSim(lugar), versao()]);
  if (!vivo(g)) return;
  const doMunicipio = new Set(mun.escolas.map((x) => x.c));
  const estado: Estado = { mun, fechar: new Set(cenario.fechar.filter((c) => doMunicipio.has(c))), indicacoes: cenario.indicacoes,
    vistas: new Set(), abertas: new Set(), indicarAbertas: new Set(), desfazer: null, anuncio: "" };
  const area = h("div", { class: "sim-resultado", id: "sim-resultado", tabindex: "-1", "aria-label": "Resultado do plano" });
  // o resumo é o que o leitor de tela anuncia a cada mudança (a área inteira passaria de 100 mil caracteres)
  const status = h("p", { class: "sim-status", role: "status" });
  // o que mudou numa indicação (a contagem do plano não muda): só para o leitor de tela
  const falar = h("p", { class: "sr", "aria-live": "polite" });
  const rodapeLink = h("span", { class: "so-impressao" });
  const urlAtual = () => new URL(link(estado), location.href).href;
  const acoes = h("div", { class: "acoes" });
  let mont: Montagem | null = null;
  const editar = h("button", { type: "button", class: "botao secundario", "aria-controls": "sim-montagem" }, "Editar o plano");
  editar.addEventListener("click", () => {
    if (!mont) return;
    if (mont.el.open) irAoResultado();
    else mont.abrir();
  });
  const mudou = (primeira = false) => {
    if (!primeira) history.replaceState(null, "", link(estado));
    const r = simular(mun, estado.fechar, estado.indicacoes);
    // indicação que o plano tornou sem efeito (escola desmarcada) sai do estado: o link fica igual ao que se vê
    estado.indicacoes = Object.fromEntries(Object.entries(estado.indicacoes).filter(([k]) => estado.fechar.has(Number(k.split(":")[0]))));
    mont?.sincronizar();
    trocar(acoes, h("button", { type: "button", class: "botao", onclick: () => void mapaPronto().then(() => window.print()) },
      "Imprimir o diagnóstico do plano"),
      botaoCompartilhar(`E se estas escolas fecharem? ${lugarTexto(mun)}`, urlAtual()));
    // refazer a área não pode levar o foco embora (quem usa teclado perderia o lugar)
    const ativo = document.activeElement instanceof HTMLElement && area.contains(document.activeElement) ? document.activeElement.id : "";
    trocar(area, resultado(estado, r, acoes, () => mudou()));
    if (ativo) document.getElementById(ativo)?.focus({ preventScroll: true });
    const sem = r.criancas - r.com_destino;
    const anuncio = estado.anuncio;
    estado.anuncio = "";
    falar.textContent = anuncio;
    trocar(status, r.fechadas.length
      ? [`${plural(r.fechadas.length, "escola", "escolas")} no plano`,
        h("span", { class: "sr" }, `, ${criancas(r.criancas)}` + (sem ? `, ${mil(sem)} sem destino calculado` : ""))]
      : "Nenhuma escola marcada.");
    rodapeLink.textContent = ` Este plano no site: ${urlAtual().replace(/^https?:\/\//, "")}`;
  };
  if (mun.escolas.length) {
    mont = montagem(estado, () => mudou());
    const nomear = () => {
      editar.textContent = mont!.el.open ? "Ver o resultado" : "Editar o plano";
      editar.setAttribute("aria-expanded", String(mont!.el.open));
    };
    mont.el.addEventListener("toggle", nomear);
    nomear();
  }
  // veio da ficha (ou de link com código de outro município): o link passa a ter o município e só o que vale
  if (lugarTexto_ === null || estado.fechar.size !== cenario.fechar.length) history.replaceState(null, "", link(estado));
  document.title = `E se estas escolas fecharem? ${lugarTexto(mun)}: Escola em Pauta`;
  trocar(main, h("div", { class: "simulador" },
    h("header", null,
      h("a", { class: "voltar nao-imprime", href: "#/simular" }, "Outro município"),
      h("h1", null, "E se estas escolas fecharem?"),
      h("p", { class: "ficha-onde" }, lugarTexto(mun)),
      h("p", { class: "legenda" }, "Simulação de um plano de fechamento, não previsão: para onde iria cada etapa de cada escola e " +
        "quanta estrada, no mínimo.")),
    mont ? h("div", { class: "sim-barra-plano nao-imprime" }, status, editar) : status,
    falar,
    mont ? mont.el : h("p", null, "Este município não tem escola do campo no índice."),
    area,
    h("p", { class: "fonte" }, `Fonte: ${v.fonte} (dados baixados em ${data(v.data_verificacao)}). Estradas: © colaboradores do ` +
      "OpenStreetMap (ODbL). ", RODAPE, rodapeLink)));
  mudou(true);
  const ignoradas = cenario.fechar.filter((c) => !doMunicipio.has(c));
  if (ignoradas.length) {
    area.prepend(h("p", { class: "aviso", role: "note" }, `${plural(ignoradas.length, "código ficou", "códigos ficaram")} fora do plano ` +
      `por não ${ignoradas.length === 1 ? "ser escola" : "serem escolas"} do campo de ${mun.municipio} no índice: ${ignoradas.join(", ")}.`));
  }
}
