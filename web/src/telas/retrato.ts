/**
 * O retrato nacional (data/retrato_rotas.json, scripts/gerar_retrato_rotas.py): o mapa por UF em degraus de cor
 * (nunca gradiente contínuo: o número é piso, e o degrau não finge precisão), a tabela por região e UF, e os
 * números do Brasil. Onde parte do transporte é por rio (Amazonas, Amapá, Pará), a UF fica hachurada em azul e sem
 * cor de classe: a rota por estrada não é o caminho das crianças.
 */

import { retrato } from "../dados";
import { h, s, trocar } from "../dom";
import { vivo } from "../estado";
import { mil, pct, UF_NOME } from "../formato";
import { NOME_UF } from "../nucleo/fechamentos";
import { carregando } from "./componentes";

interface Faixa { escolas: number; alunos: number }
interface Recorte {
  regiao?: string;
  escolas: number;
  alunos: number;
  com_rota: number;
  alunos_com_rota: number;
  sem_rota: Record<string, number>;
  km_ida_volta: { mediana: number | null; p90: number | null };
  min_ida_volta: { mediana: number | null; p90: number | null };
  faixas_km?: Record<string, Faixa>;
  faixas_min?: Record<string, Faixa>;
  receptora_urbana: number;
  alunos_receptora_urbana?: number;
  outro_municipio: number;
  nenhuma_recebe_todas: number;
  metade_ou_mais_em_chao: number;
  aviso_fluvial?: boolean;
}
interface Retrato {
  fonte: string;
  data_osm: string[];
  criterio: string;
  receptoras_por_escola?: number;
  brasil: Recorte;
  regiao: Record<string, Recorte>;
  uf: Record<string, Recorte>;
}
interface Mapa {
  largura: number;
  altura: number;
  fonte: string;
  ufs: Record<string, { d: string; x: number; y: number }>;
}

const NOME_REGIAO: Record<string, string> = {
  norte: "Norte", nordeste: "Nordeste", "centro-oeste": "Centro-Oeste", sudeste: "Sudeste", sul: "Sul",
};

interface Indicador {
  id: string;
  rotulo: string;
  titulo: string;
  valor: (r: Recorte) => number | null;
  texto: (v: number) => string;
  limites: number[]; // 4 cortes -> 5 classes
}

const longe = (r: Recorte) => r.com_rota
  ? ((r.faixas_km?.["50_a_100"]?.escolas ?? 0) + (r.faixas_km?.["100_ou_mais"]?.escolas ?? 0)) / r.com_rota : null;

const INDICADORES: Indicador[] = [
  { id: "longe", rotulo: "50 km ou mais", titulo: "Escolas a 50 km ou mais por dia da escola que receberia os alunos",
    valor: longe, texto: pct, limites: [0.02, 0.05, 0.1, 0.2] },
  { id: "duas-horas", rotulo: "2 horas ou mais", titulo: "Escolas a 2 horas ou mais de ônibus por dia",
    valor: (r) => (r.com_rota ? (r.faixas_min?.["120_ou_mais"]?.escolas ?? 0) / r.com_rota : null), texto: pct,
    limites: [0.005, 0.01, 0.025, 0.05] },
  { id: "mediana", rotulo: "Distância mediana", titulo: "Distância mediana por dia, ida e volta, pelo menos",
    valor: (r) => r.km_ida_volta.mediana, texto: (v) => `${String(Math.round(v * 10) / 10).replace(".", ",")} km`,
    limites: [8, 11, 14, 18] },
  { id: "urbana", rotulo: "Iriam para a cidade", titulo: "Escolas cujos alunos iriam para uma escola urbana",
    valor: (r) => (r.com_rota ? r.receptora_urbana / r.com_rota : null), texto: pct, limites: [0.15, 0.25, 0.35, 0.5] },
];

/** A lista de estados ao lado do mapa: DF, Sergipe e Alagoas têm poucos milímetros no celular, e a lista também serve
 * a quem não usa o mapa. */
function escolhaUf(aoEscolher: (uf: string) => void, atual: () => string | null): HTMLElement {
  const sel = h("select", { class: "escolha-uf", id: `uf-${Math.random().toString(36).slice(2, 7)}` },
    h("option", { value: "" }, "Escolha o estado"),
    Object.entries(UF_NOME).sort((a, b) => a[1].localeCompare(b[1], "pt-BR")).map(([uf, nome]) => h("option", { value: uf }, nome)));
  sel.value = atual() ?? "";
  sel.addEventListener("change", () => { if (sel.value) aoEscolher(sel.value); });
  return h("p", { class: "escolha-uf-linha" }, h("label", { for: sel.id }, "Ou escolha na lista: "), sel);
}

/** Rolagem suave, menos para quem pediu menos movimento ao sistema. */
const suave = (): ScrollBehavior => (matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth");

function encher<T extends HTMLElement>(el: T, ...filhos: Parameters<typeof trocar>[1][]): T {
  trocar(el, ...filhos);
  return el;
}

function classe(v: number, limites: number[]): number {
  return 1 + limites.filter((l) => v >= l).length;
}

function faixaTexto(ind: Indicador, k: number): string {
  const l = ind.limites;
  if (k === 1) return `menos de ${ind.texto(l[0])}`;
  if (k === 5) return `${ind.texto(l[3])} ou mais`;
  return `${ind.texto(l[k - 2])} a menos de ${ind.texto(l[k - 1])}`;
}

function hachura(): SVGElement {
  return s("defs", null, s("pattern", { id: "hachura-rio", width: 8, height: 8, patternUnits: "userSpaceOnUse", patternTransform: "rotate(45)" },
    s("rect", { width: 8, height: 8, fill: "var(--rio-claro)" }),
    s("line", { x1: 0, y1: 0, x2: 0, y2: 8, stroke: "var(--rio)", "stroke-width": 2 })));
}

/** `aoEscolher`: o que tocar numa UF faz. `escolhida`: a UF marcada. `siglasPequenas`: escrever a sigla das UFs
 * pequenas do litoral (no mapa pequeno do início, elas se atropelam). */
function desenharMapa(mapa: Mapa, dados: Retrato, ind: Indicador, aoEscolher: (uf: string) => void,
  escolhida: string | null, siglasPequenas: boolean): SVGElement {
  const svg = s("svg", { viewBox: `0 0 ${mapa.largura} ${mapa.altura}`, role: "group",
    "aria-label": `Mapa do Brasil por UF: ${ind.titulo.toLowerCase()}. Escolha uma UF para ver os números dela.` }, hachura());
  for (const [uf, g] of Object.entries(mapa.ufs)) {
    const r = dados.uf[uf];
    const v = r ? ind.valor(r) : null;
    const fluvial = Boolean(r?.aviso_fluvial);
    const cls = fluvial ? "uf fluvial" : v === null ? "uf k1" : `uf k${classe(v, ind.limites)}`;
    const rotulo = `${UF_NOME[uf]}: ${fluvial ? "transporte em parte por rio, sem número no mapa" : v === null ? "sem dado" : ind.texto(v)}`;
    const path = s("path", { class: cls + (uf === escolhida ? " escolhida" : ""), d: g.d, "data-uf": uf, tabindex: "0",
      role: "button", "aria-label": rotulo, "aria-pressed": String(uf === escolhida) }, s("title", null, rotulo));
    path.addEventListener("click", () => aoEscolher(uf));
    path.addEventListener("keydown", (ev) => {
      if ((ev as KeyboardEvent).key === "Enter" || (ev as KeyboardEvent).key === " ") {
        ev.preventDefault();
        aoEscolher(uf);
      }
    });
    svg.append(path);
  }
  for (const [uf, g] of Object.entries(mapa.ufs)) {
    if (["DF", "SE", "AL", "RN", "PB", "ES", "RJ"].includes(uf) && !siglasPequenas) continue;
    svg.append(s("text", { class: "uf-sigla", x: g.x, y: g.y + 4, "text-anchor": "middle" }, uf));
  }
  return svg;
}

function legenda(ind: Indicador): HTMLElement {
  return h("ul", { class: "mapa-legenda", "aria-label": "Legenda do mapa" },
    [1, 2, 3, 4, 5].map((k) => h("li", null, h("span", { class: `amostra k${k}`, style: `background:var(--c${k})` }), faixaTexto(ind, k))),
    h("li", null, h("span", { class: "amostra", style: "background:repeating-linear-gradient(45deg,var(--rio) 0 2px,var(--rio-claro) 2px 6px)" }),
      "transporte em parte por rio: sem número"));
}

/** A prancha pequena do início: o Brasil pelo indicador principal, com link para o retrato. */
export async function pranchaBrasil(alvo: HTMLElement, texto: HTMLElement): Promise<void> {
  const [dados, mapa] = await Promise.all([retrato<Retrato>(), import("../mapa/ufs.json").then((m) => m.default as Mapa)]);
  const ind = INDICADORES[0];
  const b = dados.brasil;
  const abrir = (uf: string) => { location.hash = `#/retrato/${uf}`; };
  trocar(alvo,
    h("figure", { class: "prancha", style: "margin:0" },
      h("div", { class: "prancha-titulo" }, h("h2", null, "O Brasil, por UF"), h("span", null, "escolas a 50 km ou mais por dia")),
      h("div", { class: "prancha-moldura" }, desenharMapa(mapa, dados, ind, abrir, null, false)),
      legenda(ind),
      escolhaUf(abrir, () => null),
      h("figcaption", null, "Toque numa UF para abrir o retrato dela.")));
  trocar(texto, h("section", { class: "coluna" },
    h("h2", null, "O retrato do país"),
    h("p", null, `Calculamos a rota por estrada de ${mil(b.com_rota)} escolas do campo até as escolas que poderiam receber ` +
      `os alunos. A distância mediana é de pelo menos ${String(b.km_ida_volta.mediana).replace(".", ",")} km por dia, ida e volta.`),
    h("p", null, `${mil(b.faixas_min?.["120_ou_mais"]?.escolas ?? 0)} escolas, com ${mil(b.faixas_min?.["120_ou_mais"]?.alunos ?? 0)} ` +
      "alunos, passariam a ter duas horas ou mais de ônibus por dia. E para " +
      `${mil(b.sem_rota["sem_coordenada"] ?? 0)} escolas o INEP não publica a localização.`),
    h("p", null, h("a", { class: "botao secundario", href: "#/retrato" }, "Ver o retrato completo"))));
}

const MOTIVO_SEM_ROTA: Record<string, string> = {
  sem_coordenada: "sem localização pública", origem_longe: "longe da estrada mapeada",
  sem_rota: "sem ligação na malha viária", sem_matricula: "sem alunos nas etapas regulares",
  sem_candidata: "sem escola receptora a até 60 km",
};

const km1 = (v: number | null) => (v === null ? "" : `${v.toFixed(1).replace(".", ",")} km`);
/** Menos da metade das escolas com rota: a mediana vale para as que têm, e a tabela marca. */
const poucaCobertura = (r: Recorte) => r.escolas > 0 && r.com_rota / r.escolas < 0.5;

function linhaTabela(nome: string, r: Recorte, tipo: "regiao" | "uf" | "brasil", uf?: string): HTMLElement {
  const fluvial = r.aviso_fluvial;
  return h("tr", { class: tipo === "uf" ? null : "regiao", "data-uf": uf ?? null },
    h("th", { scope: "row", class: tipo === "uf" ? "sub" : null }, nome, fluvial ? h("span", { title: "transporte em parte por rio" }, " (rio)") : null),
    h("td", { class: "num" }, `${mil(r.com_rota)} de ${mil(r.escolas)}`, h("small", { class: "cobertura" }, ` (${pct(r.escolas ? r.com_rota / r.escolas : 0)})`)),
    h("td", { class: "num" }, km1(r.km_ida_volta.mediana), poucaCobertura(r) && r.km_ida_volta.mediana !== null ? " †" : ""),
    h("td", { class: "num" }, km1(r.km_ida_volta.p90)),
    h("td", { class: "num" }, longe(r) === null ? "" : pct(longe(r)!)),
    h("td", { class: "num" }, mil(r.faixas_min?.["120_ou_mais"]?.escolas ?? 0)),
    h("td", { class: "num" }, r.com_rota ? pct(r.receptora_urbana / r.com_rota) : ""));
}

/** O painel da UF escolhida: os números dela e o passo seguinte (os fechamentos do estado, a linha da tabela). */
function detalheUf(uf: string, r: Recorte | undefined, verNaTabela: () => void): (string | HTMLElement)[] {
  const pergunta = `Quantas escolas do campo fecharam ${NOME_UF[uf]}?`; // "na Bahia", "no Paraná": a forma do núcleo
  const acoes = h("p", { class: "acoes-uf" },
    h("a", { href: `#/pergunta/${encodeURIComponent(pergunta)}` }, pergunta),
    r ? h("button", { type: "button", class: "botao-texto", onclick: verNaTabela }, "Ver a linha na tabela") : null);
  return [h("p", null, detalheNumeros(uf, r)), acoes];
}

function detalheNumeros(uf: string, r: Recorte | undefined): (string | HTMLElement)[] {
  if (!r) return [`${UF_NOME[uf]}: sem dado.`];
  const partes: (string | HTMLElement)[] = [h("b", null, UF_NOME[uf]), `: ${mil(r.escolas)} escolas do campo, ${mil(r.alunos)} alunos. `,
    `Rota calculada para ${mil(r.com_rota)}. `];
  if (r.km_ida_volta.mediana !== null) {
    partes.push(`Distância mediana de pelo menos ${String(r.km_ida_volta.mediana).replace(".", ",")} km por dia; ` +
      `uma em cada dez passa de ${String(r.km_ida_volta.p90).replace(".", ",")} km. `);
  }
  if (r.aviso_fluvial) partes.push(h("b", null, "Parte do transporte escolar é por rio: "), "a rota por estrada pode não ser o caminho das crianças. ");
  if (poucaCobertura(r)) {
    partes.push(h("b", null, `Só ${pct(r.com_rota / r.escolas)} das escolas têm rota: `), "a mediana vale para elas, não para o estado todo. ");
  }
  const motivos = Object.entries(r.sem_rota).filter(([, q]) => q > 0).sort((a, b) => b[1] - a[1]);
  if (motivos.length) {
    partes.push(`Sem rota (${mil(r.escolas - r.com_rota)}): ` +
      motivos.map(([k, q]) => `${mil(q)} ${MOTIVO_SEM_ROTA[k] ?? k}`).join(", ") + ".");
  }
  return partes;
}

/** Devolve o painel da UF quando o endereço já traz uma (#/retrato/MT): a tela abre ali, e não no topo. */
export async function telaRetrato(main: HTMLElement, g: number, ufPedida: string | null = null): Promise<HTMLElement | void> {
  document.title = "Retrato do Brasil: Escola em Pauta";
  trocar(main, carregando("Carregando o retrato..."));
  const [dados, mapa] = await Promise.all([retrato<Retrato>(), import("../mapa/ufs.json").then((m) => m.default as Mapa)]);
  if (!vivo(g)) return;
  const b = dados.brasil;
  let ind = INDICADORES[0];
  const lugarMapa = h("div", { class: "prancha-moldura" });
  const lugarLegenda = h("div");
  const tituloMapa = h("span");
  const detalhe = h("div", { class: "uf-detalhe", "aria-live": "polite" }, "Toque numa UF no mapa para ver os números dela.");
  const pedida = ufPedida ? ufPedida.toUpperCase() : null;
  let escolhida: string | null = pedida && UF_NOME[pedida] ? pedida : null;
  const corpoTabela = h("tbody");
  const verNaTabela = (uf: string) => {
    const linha = corpoTabela.querySelector<HTMLElement>(`tr[data-uf="${uf}"]`);
    if (!linha) return;
    corpoTabela.querySelectorAll("tr.destaque").forEach((tr) => tr.classList.remove("destaque"));
    linha.classList.add("destaque");
    linha.scrollIntoView({ block: "center", behavior: suave() });
  };
  const marcarLinha = (uf: string) => {
    corpoTabela.querySelectorAll("tr.destaque").forEach((tr) => tr.classList.remove("destaque"));
    corpoTabela.querySelector(`tr[data-uf="${uf}"]`)?.classList.add("destaque");
  };
  const mostrar = (uf: string) => trocar(detalhe, detalheUf(uf, dados.uf[uf], () => verNaTabela(uf)));
  const escolher = (uf: string) => {
    escolhida = uf;
    for (const p of lugarMapa.querySelectorAll<SVGElement>("path[data-uf]")) {
      const sim = p.dataset.uf === uf;
      p.classList.toggle("escolhida", sim);
      p.setAttribute("aria-pressed", String(sim));
      // a escolhida por cima das vizinhas, para o contorno não ficar escondido (as siglas continuam por cima)
      if (sim) p.parentNode!.insertBefore(p, p.parentNode!.querySelector("text"));
    }
    mostrar(uf);
    marcarLinha(uf);
    const sel = lugarMapa.parentElement?.querySelector<HTMLSelectElement>("select.escolha-uf");
    if (sel) sel.value = uf;
    // o endereço passa a ter a UF (dá para compartilhar), sem redesenhar a tela
    history.replaceState(null, "", `#/retrato/${uf}`);
    const r = detalhe.getBoundingClientRect();
    if (r.top < 0 || r.bottom > window.innerHeight) detalhe.scrollIntoView({ block: "nearest", behavior: suave() });
  };
  const botoes = INDICADORES.map((x) => h("button", { type: "button", "aria-pressed": String(x === ind) }, x.rotulo));
  const desenhar = () => {
    trocar(lugarMapa, desenharMapa(mapa, dados, ind, escolher, escolhida, true));
    trocar(lugarLegenda, legenda(ind));
    tituloMapa.textContent = ind.titulo;
    botoes.forEach((bt, i) => bt.setAttribute("aria-pressed", String(INDICADORES[i] === ind)));
  };
  botoes.forEach((bt, i) => bt.addEventListener("click", () => {
    ind = INDICADORES[i];
    desenhar();
  }));
  const sc = b.sem_rota["sem_coordenada"] ?? 0;
  const duas = b.faixas_min?.["120_ou_mais"];
  trocar(main,
    h("section", { class: "abertura", style: "padding-bottom:0" },
      h("h1", null, "Se as escolas do campo fechassem, quanto as crianças passariam a viajar?"),
      h("p", { class: "sub" }, `A conta foi feita para as ${mil(b.com_rota)} escolas do campo com rota calculada ` +
        `(${pct(b.com_rota / b.escolas)} das ${mil(b.escolas)}): a estrada até a escola mais próxima que recebe todas as etapas ` +
        "dela, de escola a escola, ida e volta. É um piso: o caminho real das crianças é maior.")),
    h("ul", { class: "brasil-numeros" },
      h("li", null, h("b", null, `${String(b.km_ida_volta.mediana).replace(".", ",")} km`), "por dia é a distância mediana, pelo menos"),
      h("li", null, h("b", null, mil(duas?.escolas ?? 0)), `escolas, com ${mil(duas?.alunos ?? 0)} alunos, passariam a ter duas horas ou mais de ônibus por dia`),
      h("li", null, h("b", null, mil(b.receptora_urbana)), `escolas mandariam os alunos para uma escola urbana (${mil(b.alunos_receptora_urbana ?? 0)} alunos)`),
      h("li", null, h("b", null, mil(sc)), `escolas não têm localização pública no INEP, e outras ${mil(b.escolas - b.com_rota - sc)} ` +
        "ficaram sem rota por outros motivos (a maioria longe da estrada mapeada, no Norte). Para elas, o assistente não estima")),
    h("div", { class: "duas" },
      h("figure", { class: "prancha", style: "margin:1rem 0" },
        h("div", { class: "prancha-titulo" }, h("h2", null, "Mapa do Brasil"), tituloMapa),
        h("div", { class: "indicadores", role: "group", "aria-label": "O que o mapa mostra" }, botoes),
        lugarMapa, escolhaUf(escolher, () => escolhida), detalhe, lugarLegenda,
        h("figcaption", null, "Cores em degraus. A conta usa a escola mais próxima que recebe todas as etapas; quando nenhuma das " +
          `${dados.receptoras_por_escola ?? 4} mais próximas recebe, usa a mais próxima (${mil(b.nenhuma_recebe_todas)} escolas). ` +
          `Malha de UFs: ${mapa.fonte}.`)),
      h("div", null, h("h2", null, "No país todo"),
        h("p", null, `Em ${mil(b.outro_municipio)} escolas, a escola que receberia os alunos fica em outro município. Em `,
          `${mil(b.metade_ou_mais_em_chao)}, metade ou mais da estrada é de chão.`),
        h("p", { class: "legenda" }, "Como contamos: para cada escola, a mais próxima por estrada que recebe todas as etapas dela " +
          `(senão, a mais próxima), entre até ${dados.receptoras_por_escola ?? 4} escolas com rota. Km e minutos de ida e volta por dia, ` +
          "de escola a escola, como piso. A mediana é o valor do meio: metade das escolas fica acima dele."))),
    h("h2", null, "Por região e por UF"),
    h("div", { class: "tabela-rolagem" }, h("table", { class: "quadro" },
      h("thead", null, h("tr", null, h("th", null, "Lugar"), h("th", { class: "num" }, "Com rota"), h("th", { class: "num" }, "Mediana"),
        h("th", { class: "num" }, "1 em 10 passa de"), h("th", { class: "num" }, "50 km ou mais"), h("th", { class: "num" }, "2 h ou mais"),
        h("th", { class: "num" }, "Para a cidade"))),
      encher(corpoTabela,
        linhaTabela("Brasil", b, "brasil"),
        Object.entries(dados.regiao).flatMap(([reg, r]) => [
          linhaTabela(NOME_REGIAO[reg] ?? reg, r, "regiao"),
          ...Object.entries(dados.uf).filter(([, u]) => u.regiao === reg).sort((a, c) => UF_NOME[a[0]].localeCompare(UF_NOME[c[0]], "pt-BR"))
            .map(([uf, u]) => linhaTabela(UF_NOME[uf], u, "uf", uf)),
        ])))),
    h("p", { class: "legenda" }, "Km e minutos por dia, ida e volta, de escola a escola, sempre como piso. \"Com rota\": escolas com " +
      "rota calculada, do total de escolas do campo. \"1 em 10 passa de\": o percentil 90. \"†\": menos da metade das escolas tem rota, e a mediana vale só para " +
      "as que têm. \"(rio)\": parte do transporte é " +
      `fluvial. Fonte: ${dados.fonte}; estradas do OpenStreetMap de ${dados.data_osm.map((d) => d.split("-").reverse().join("/")).join(", ")}.`));
  desenhar();
  if (!escolhida) return;
  mostrar(escolhida);
  marcarLinha(escolhida);
  const sel = lugarMapa.parentElement?.querySelector<HTMLSelectElement>("select.escolha-uf");
  if (sel) sel.value = escolhida;
  return lugarMapa.closest("figure") as HTMLElement;
}
