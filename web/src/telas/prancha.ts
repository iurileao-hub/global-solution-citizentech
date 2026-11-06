/**
 * A PRANCHA: o mapa da escola desenhado como uma prancha de atlas, sem fundo de mapa baixado da internet.
 * Só o traçado real das estradas (segunda passada do pré-cálculo), com moldura, graus nas bordas, escala gráfica,
 * o N e as convenções. Estrada pavimentada em traço cheio; estrada de chão tracejada (a cor não é a única pista).
 *
 * Sem traçado (dados só da primeira passada), a prancha vira um esquema de distâncias: barras de km por dia.
 */

import type { Tracado } from "../dados";
import { h, s } from "../dom";
import { km } from "../formato";
import { decodificar } from "../polyline";
import type { Escola, Receptora } from "../nucleo/respostas";

export const LETRAS = "ABCDEFGHIJ";

const L = 600; // largura do desenho, em unidades do SVG
const MARGEM = 30; // faixa da moldura onde vão os graus

interface Rota {
  r: Receptora;
  letra: string;
  pontos: [number, number][];
  chao: number[];
}

function passoGraus(span: number): number {
  const passos = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.25, 0.5, 1];
  return passos.find((p) => span / p <= 4) ?? 1;
}

function grau(v: number, eixo: "lat" | "lon"): string {
  const a = Math.abs(v);
  let g = Math.floor(a);
  let m = Math.round((a - g) * 60);
  if (m === 60) {
    g += 1;
    m = 0;
  }
  const lado = eixo === "lat" ? (v < 0 ? "S" : "N") : v < 0 ? "O" : "L";
  return `${g}°${m ? String(m).padStart(2, "0") + "′" : ""} ${lado}`;
}

function escalaKm(kmPorUnidade: number): number {
  const alvo = (L * 0.28) * kmPorUnidade;
  return [0.5, 1, 2, 5, 10, 20, 50, 100].reduce((a, b) => (Math.abs(b - alvo) < Math.abs(a - alvo) ? b : a));
}

/** Trechos [i, j] do traçado: os de chão vêm nos pares; o resto é pavimentado. */
export function trechos(n: number, pares: number[]): { i: number; j: number; chao: boolean }[] {
  const saida: { i: number; j: number; chao: boolean }[] = [];
  let pos = 0;
  for (let k = 0; k + 1 < pares.length; k += 2) {
    const [i, j] = [pares[k], pares[k + 1]];
    if (i > pos) saida.push({ i: pos, j: i, chao: false });
    saida.push({ i, j, chao: true });
    pos = j;
  }
  if (pos < n - 1) saida.push({ i: pos, j: n - 1, chao: false });
  return saida;
}

export function prancha(e: Escola, receptoras: Receptora[], tracados: Tracado[] | null, principal: Receptora | null):
  HTMLElement {
  const porCodigo = new Map((tracados ?? []).map((t) => [t[0], t]));
  const rotas: Rota[] = [];
  receptoras.forEach((r, i) => {
    const t = porCodigo.get(r.c);
    if (t) rotas.push({ r, letra: LETRAS[i], pontos: decodificar(t[1]), chao: t[2] ?? [] });
  });
  if (!rotas.length) return esquema(e, receptoras, principal);

  // enquadramento: todos os pontos, com folga, e proporção entre 3:4 e 4:3
  const todos = rotas.flatMap((x) => x.pontos);
  let [la0, la1] = [Math.min(...todos.map((p) => p[0])), Math.max(...todos.map((p) => p[0]))];
  let [lo0, lo1] = [Math.min(...todos.map((p) => p[1])), Math.max(...todos.map((p) => p[1]))];
  const cos = Math.cos(((la0 + la1) / 2) * Math.PI / 180);
  let w = (lo1 - lo0) * cos;
  let alt = la1 - la0;
  const minimo = 0.01;
  if (w < minimo) [lo0, lo1, w] = [lo0 - (minimo - w) / 2 / cos, lo1 + (minimo - w) / 2 / cos, minimo];
  if (alt < minimo) [la0, la1, alt] = [la0 - (minimo - alt) / 2, la1 + (minimo - alt) / 2, minimo];
  const prop = Math.min(Math.max(alt / w, 0.75), 1.25);
  if (alt / w < prop) {
    const extra = (w * prop - alt) / 2;
    la0 -= extra;
    la1 += extra;
    alt = w * prop;
  } else if (alt / w > prop) {
    const extra = (alt / prop - w) / 2 / cos;
    lo0 -= extra;
    lo1 += extra;
    w = alt / prop;
  }
  const folga = 0.12;
  const dentroL = L - 2 * MARGEM;
  const k = dentroL / (w * (1 + 2 * folga));
  const H = Math.round(alt * (1 + 2 * folga) * k + 2 * MARGEM);
  const x = (lon: number) => MARGEM + ((lon - lo0) * cos + w * folga) * k;
  const y = (lat: number) => MARGEM + ((la1 - lat) + alt * folga) * k;
  const kmPorUnidade = 111.32 / k;

  const idTitulo = "prancha-t-" + e.c;
  const idDesc = "prancha-d-" + e.c;
  const svg = s("svg", { viewBox: `0 0 ${L} ${H}`, role: "img", "aria-labelledby": `${idTitulo} ${idDesc}` },
    s("title", { id: idTitulo }, `Mapa das estradas desta escola até ${rotas.length} escolas que poderiam receber os alunos`),
    s("desc", { id: idDesc }, rotas.map((x) => `${x.letra}: ${x.r.n}, ${km(x.r.km)} km por dia, ida e volta`).join("; ")),
    s("rect", { class: "p-fundo", x: MARGEM, y: MARGEM, width: L - 2 * MARGEM, height: H - 2 * MARGEM }));

  // gratícula e graus na moldura
  const lat0 = la0 - alt * folga;
  const lat1 = la1 + alt * folga;
  const lon0 = lo0 - (w * folga) / cos;
  const lon1 = lo1 + (w * folga) / cos;
  const pLat = passoGraus(lat1 - lat0);
  const pLon = passoGraus(lon1 - lon0);
  for (let g = Math.ceil(lat0 / pLat) * pLat; g <= lat1; g += pLat) {
    const yy = y(g);
    svg.append(s("line", { class: "p-grade", x1: MARGEM, x2: L - MARGEM, y1: yy, y2: yy }),
      s("text", { class: "p-grau", x: MARGEM - 9, y: yy, "text-anchor": "middle", transform: `rotate(-90 ${MARGEM - 9} ${yy})` },
        grau(g, "lat").replace(" ", "")));
  }
  for (let g = Math.ceil(lon0 / pLon) * pLon; g <= lon1; g += pLon) {
    const xx = x(g);
    svg.append(s("line", { class: "p-grade", y1: MARGEM, y2: H - MARGEM, x1: xx, x2: xx }),
      s("text", { class: "p-grau", x: xx, y: MARGEM - 9, "text-anchor": "middle" }, grau(g, "lon").replace(" ", "")));
  }

  // linhas retas de referência (só para quem não é a principal) e as rotas
  const caminho = (pts: [number, number][]) =>
    "M" + pts.map((p) => `${x(p[1]).toFixed(1)},${y(p[0]).toFixed(1)}`).join("L");
  const ordem = [...rotas].sort((a, b) => Number(a.r === principal) - Number(b.r === principal)); // principal por cima
  for (const rt of ordem) {
    const sec = rt.r !== principal && principal !== null;
    for (const t of trechos(rt.pontos.length, rt.chao)) {
      svg.append(s("path", {
        class: `p-rota${t.chao ? " chao" : ""}${sec ? " secundaria" : ""}`, d: caminho(rt.pontos.slice(t.i, t.j + 1)),
      }));
    }
  }
  // marcadores: receptoras com letra (as que caem no mesmo ponto, como duas escolas no mesmo prédio, dividem
  // uma marca só, "B C"), depois a escola de origem por cima
  const grupos: { cx: number; cy: number; letras: string[] }[] = [];
  for (const rt of rotas) {
    const [la, lo] = rt.pontos[rt.pontos.length - 1];
    const [cx, cy] = [x(lo), y(la)];
    const perto = grupos.find((gr) => Math.hypot(gr.cx - cx, gr.cy - cy) < 34);
    if (perto) perto.letras.push(rt.letra);
    else grupos.push({ cx, cy, letras: [rt.letra] });
  }
  for (const gr of grupos) {
    const larg = 24 + (gr.letras.length - 1) * 13;
    svg.append(s("rect", { class: "p-receptora", x: gr.cx - larg / 2, y: gr.cy - 12, width: larg, height: 24, rx: 12 }),
      s("text", { class: "p-rotulo", x: gr.cx, y: gr.cy + 5, "text-anchor": "middle" }, gr.letras.join(" ")));
  }
  const [oa, oo] = rotas[0].pontos[0];
  svg.append(s("rect", { class: "p-origem", x: x(oo) - 9, y: y(oa) - 9, width: 18, height: 18, transform: `rotate(45 ${x(oo)} ${y(oa)})` }),
    s("text", { class: "p-rotulo-origem", x: x(oo) + 15, y: y(oa) - 12 }, "esta escola"));

  // escala gráfica alternada e o N
  const ek = escalaKm(kmPorUnidade);
  const eL = ek / kmPorUnidade;
  const ex = MARGEM + 12;
  const ey = H - MARGEM - 16;
  svg.append(s("rect", { class: "p-escala-b", x: ex - 4, y: ey - 15, width: eL + 30, height: 26, opacity: 0.85 }));
  for (let i = 0; i < 4; i++) {
    svg.append(s("rect", { class: i % 2 ? "p-escala-b" : "p-escala-a", x: ex + (i * eL) / 4, y: ey, width: eL / 4, height: 5 }));
  }
  svg.append(s("text", { class: "p-escala-txt", x: ex, y: ey - 4 }, "0"),
    s("text", { class: "p-escala-txt", x: ex + eL, y: ey - 4, "text-anchor": "middle" }, `${String(ek).replace(".", ",")} km`));
  const nx = L - MARGEM - 20;
  const ny = MARGEM + 14;
  svg.append(s("path", { class: "p-norte", d: `M${nx},${ny - 8}l6,16l-6,-4l-6,4z` }),
    s("text", { class: "p-norte", x: nx, y: ny + 22, "text-anchor": "middle" }, "N"));

  const temChao = rotas.some((r) => r.chao.length);
  const fig = h("figure", { class: "prancha", style: "margin:0" },
    h("div", { class: "prancha-titulo" }, h("h2", null, "Prancha da escola"), h("span", null, `${e.m}, ${e.uf}`)),
    h("div", { class: "prancha-moldura" }, svg),
    h("div", { class: "convencoes" },
      h("h3", null, "Convenções"),
      amostra("origem"), h("span", null, "esta escola"),
      amostra("receptora"), h("span", null, "escola que poderia receber os alunos (a letra é a da lista)"),
      amostra("pav"), h("span", null, "estrada pavimentada"),
      temChao ? amostra("chao") : null, temChao ? h("span", null, "estrada de chão") : null),
    h("figcaption", null, "Traçado da ida, de escola a escola, pela malha do OpenStreetMap. O ônibus de verdade passa de " +
      "casa em casa: o caminho das crianças é maior."));
  animar(fig);
  return fig;
}

function amostra(tipo: "origem" | "receptora" | "pav" | "chao"): SVGElement {
  const svg = s("svg", { viewBox: "0 0 40 16", "aria-hidden": "true" });
  if (tipo === "origem") svg.append(s("rect", { class: "p-origem", x: 15, y: 3, width: 10, height: 10, transform: "rotate(45 20 8)" }));
  if (tipo === "receptora") svg.append(s("circle", { class: "p-receptora", cx: 20, cy: 8, r: 6 }));
  if (tipo === "pav") svg.append(s("path", { class: "p-rota", d: "M2,8H38" }));
  if (tipo === "chao") svg.append(s("path", { class: "p-rota chao", d: "M2,8H38" }));
  return svg;
}

/** O único movimento da página: as estradas se desenham uma vez quando a prancha aparece. */
function animar(fig: HTMLElement): void {
  if (!matchMedia("(prefers-reduced-motion: no-preference)").matches || !("IntersectionObserver" in window)) return;
  const obs = new IntersectionObserver((itens) => {
    if (!itens.some((i) => i.isIntersecting)) return;
    obs.disconnect();
    for (const p of fig.querySelectorAll<SVGPathElement>(".p-rota")) {
      if (p.classList.contains("chao")) {
        p.animate([{ opacity: 0 }, { opacity: 1 }], { duration: 500, delay: 700, fill: "backwards" });
        continue;
      }
      const c = p.getTotalLength();
      p.animate([{ strokeDasharray: `${c} ${c}`, strokeDashoffset: c }, { strokeDasharray: `${c} ${c}`, strokeDashoffset: 0 }],
        { duration: 1100, easing: "ease-out" });
    }
  }, { threshold: 0.3 });
  obs.observe(fig);
}

/** Sem traçado: um esquema de distâncias, na mesma moldura (barras de km por dia, chão tracejado). */
function esquema(e: Escola, receptoras: Receptora[], principal: Receptora | null): HTMLElement {
  const maior = Math.max(1, ...receptoras.map((r) => r.km));
  const passo = maior <= 30 ? 10 : maior <= 80 ? 20 : 50;
  const fim = Math.ceil((maior * 1.1) / passo) * passo;
  const linha = 40;
  const esq = 34;
  const H = receptoras.length * linha + 46;
  const larg = L - esq - 20;
  const svg = s("svg", { viewBox: `0 0 ${L} ${H}`, role: "img", "aria-label": "Esquema das distâncias por estrada, ida e volta por dia" },
    s("rect", { class: "p-fundo", x: 0, y: 0, width: L, height: H }));
  for (let v = 0; v <= fim; v += passo) {
    const xx = esq + (v / fim) * larg;
    svg.append(s("line", { class: "p-grade", x1: xx, x2: xx, y1: 8, y2: H - 26 }),
      s("text", { class: "p-grau", x: xx, y: H - 10, "text-anchor": "middle" }, `${v} km`));
  }
  receptoras.forEach((r, i) => {
    const yy = 22 + i * linha;
    const total = (r.km / fim) * larg;
    const chao = Math.min(total, ((r.chao ?? 0) / fim) * larg);
    const sec = principal !== null && r !== principal;
    svg.append(s("path", { class: `p-rota${sec ? " secundaria" : ""}`, d: `M${esq},${yy}h${(total - chao).toFixed(1)}` }));
    if (chao > 0.5) svg.append(s("path", { class: `p-rota chao${sec ? " secundaria" : ""}`, d: `M${(esq + total - chao).toFixed(1)},${yy}h${chao.toFixed(1)}` }));
    svg.append(s("circle", { class: "p-receptora", cx: esq + total, cy: yy, r: 12 }),
      s("text", { class: "p-rotulo", x: esq + total, y: yy + 5, "text-anchor": "middle" }, LETRAS[i]));
  });
  svg.append(s("rect", { class: "p-origem", x: 6, y: H / 2 - 20, width: 12, height: 12, transform: `rotate(45 12 ${H / 2 - 14})` }));
  return h("figure", { class: "prancha", style: "margin:0" },
    h("div", { class: "prancha-titulo" }, h("h2", null, "Esquema das distâncias"), h("span", null, `${e.m}, ${e.uf}`)),
    h("div", { class: "prancha-moldura" }, svg),
    h("figcaption", null, "Estrada por dia, ida e volta, de escola a escola: pelo menos isso. O traçado no mapa ainda não " +
      "está disponível para esta escola."));
}
