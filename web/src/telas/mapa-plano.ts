/**
 * O MAPA DO PLANO: a prancha da ficha, com o plano inteiro. Só as rotas que o plano usa (da escola que fecha até a
 * escola que receberia cada etapa), pelo traçado real das estradas. Escola do plano com letra (A, B...), escola que
 * recebe com número (1, 2...): as mesmas marcas dos cartões e da tabela "Quem recebe".
 *
 * Teto de MAX_MAPA escolas no plano: acima disso as rotas se sobrepõem e os downloads pesam no celular. Escola sem
 * traçado fica fora do desenho e a legenda diz quantas; sem nenhum traçado, não há mapa (os cartões bastam).
 */

import { type Tracado, tracados } from "../dados";
import { h, s } from "../dom";
import { decodificar } from "../polyline";
import type { Resultado } from "../nucleo/simulacao";
import { amostra, L, MARGEM, quadro, trechos } from "./prancha";

export const MAX_MAPA = 12;
/** Marcas que se encostam no desenho: acima disso o mapa engana mais do que ajuda e não é desenhado. */
const MAX_COLISOES = 2;
/** Receptoras a menos disto (km) dividem uma marca só: é o mesmo lugar, não duas escolas vizinhas. */
const MESMO_PONTO_KM = 1.5;

let pronto: Promise<void> = Promise.resolve();
/** Resolve quando o último mapa pedido terminou de carregar (o botão de imprimir espera por ele). */
export const mapaPronto = (): Promise<void> => pronto;
export const LETRAS_PLANO = "ABCDEFGHIJKL";

interface Rota {
  origem: number;
  destino: number;
  pontos: [number, number][];
  chao: number[];
}

/** Letra de cada escola do plano e número de cada escola que recebe, na ordem da tela. */
export function marcas(r: Resultado): { letra: Map<number, string>; numero: Map<number, number> } {
  return {
    // a mesma ordem dos cartões (pelo nome); acima de MAX_MAPA escolas não há mapa, e sem mapa a letra não serve
    letra: new Map(r.escolas.length > MAX_MAPA ? [] : [...r.escolas].sort((a, b) => a.n.localeCompare(b.n, "pt-BR"))
      .map((x, i) => [x.c, LETRAS_PLANO[i]])),
    numero: new Map(r.receptoras.map((x, i) => [x.c, i + 1])),
  };
}

/** Lugar do mapa na página: devolve já o elemento e o preenche quando os traçados chegam (sem segurar a tela). */
export function mapaPlano(r: Resultado, nomes: Map<number, string>): HTMLElement | null {
  const pares = new Map<string, { origem: number; destino: number }>();
  for (const a of r.alocacoes) if (a.destino !== null) pares.set(`${a.origem}:${a.destino}`, { origem: a.origem, destino: a.destino });
  if (!pares.size) return null;
  const origens = [...new Set([...pares.values()].map((p) => p.origem))];
  const lugar = h("div", { class: "sim-mapa" });
  if (r.fechadas.length > MAX_MAPA) {
    lugar.append(h("p", { class: "legenda" }, `O mapa aparece para planos de até ${MAX_MAPA} escolas: com mais, as estradas se ` +
      "sobrepõem. Os cartões têm todos os destinos."));
    return lugar;
  }
  lugar.append(h("p", { class: "legenda" }, "Carregando o mapa das estradas..."));
  pronto = Promise.all(origens.map((c) => tracados(c).catch(() => null))).then((lista) => {
    const porOrigem = new Map<number, Tracado[] | null>(origens.map((c, i) => [c, lista[i]]));
    const rotas: Rota[] = [];
    let faltam = 0;
    for (const p of pares.values()) {
      const t = porOrigem.get(p.origem)?.find((x) => x[0] === p.destino);
      if (t) rotas.push({ ...p, pontos: decodificar(t[1]), chao: t[2] ?? [] });
      else faltam++;
    }
    lugar.replaceChildren();
    const fig = rotas.length ? desenhar(r, rotas, nomes, faltam) : null;
    if (fig) lugar.append(fig);
    else if (rotas.length) {
      lugar.append(h("p", { class: "legenda" }, "As escolas deste plano ficam perto demais umas das outras para um mapa legível " +
        "nesta escala. Os cartões têm todos os destinos."));
    } else lugar.remove();
  });
  return lugar;
}

function desenhar(r: Resultado, rotas: Rota[], nomes: Map<number, string>, faltam: number): HTMLElement | null {
  const { letra, numero } = marcas(r);
  const { x, y, H, kmPorUnidade, grade, escalaENorte } = quadro(rotas.flatMap((rt) => rt.pontos));
  const descricao = [...new Set(rotas.map((rt) => rt.origem))].map((o) =>
    `${letra.get(o) ?? ""}, ${nomes.get(o) ?? o}, para ` +
    rotas.filter((rt) => rt.origem === o).map((rt) => `${numero.get(rt.destino)}, ${nomes.get(rt.destino) ?? rt.destino}`).join(" e "))
    .join("; ");
  const svg = s("svg", { viewBox: `0 0 ${L} ${H}`, role: "img", "aria-labelledby": "sim-mapa-t sim-mapa-d" },
    s("title", { id: "sim-mapa-t" }, "Mapa das estradas do plano: de cada escola que fecha até a escola que receberia"),
    s("desc", { id: "sim-mapa-d" }, descricao),
    s("rect", { class: "p-fundo", x: MARGEM, y: MARGEM, width: L - 2 * MARGEM, height: H - 2 * MARGEM }));
  grade(svg);
  const caminho = (pts: [number, number][]) => "M" + pts.map((p) => `${x(p[1]).toFixed(1)},${y(p[0]).toFixed(1)}`).join("L");
  for (const rt of rotas) {
    for (const t of trechos(rt.pontos.length, rt.chao)) {
      svg.append(s("path", { class: `p-rota${t.chao ? " chao" : ""}`, "data-origem": String(rt.origem),
        d: caminho(rt.pontos.slice(t.i, t.j + 1)) }));
    }
  }
  // escolas que recebem: círculo com o número (as que caem no mesmo ponto dividem a marca, "1 3")
  const grupos: { cx: number; cy: number; rot: string[] }[] = [];
  const juntar = (cx: number, cy: number, rot: string) => {
    const perto = grupos.find((g) => Math.hypot(g.cx - cx, g.cy - cy) * kmPorUnidade < MESMO_PONTO_KM);
    if (perto) {
      if (!perto.rot.includes(rot)) perto.rot.push(rot);
    } else grupos.push({ cx, cy, rot: [rot] });
  };
  const fim = new Map<number, [number, number]>();
  for (const rt of rotas) fim.set(rt.destino, rt.pontos[rt.pontos.length - 1]);
  for (const [c, [la, lo]] of [...fim].sort((a, b) => (numero.get(a[0]) ?? 0) - (numero.get(b[0]) ?? 0))) {
    juntar(x(lo), y(la), String(numero.get(c) ?? "?"));
  }
  // legibilidade: marcas (receptoras e escolas do plano) que se encostam no desenho; muitas, e o mapa não sai
  const inicio = new Map<number, [number, number]>();
  for (const rt of rotas) inicio.set(rt.origem, rt.pontos[0]);
  const pontos = [...grupos.map((g) => [g.cx, g.cy]), ...[...inicio.values()].map(([la, lo]) => [x(lo), y(la)])];
  let colisoes = 0;
  for (let i = 0; i < pontos.length; i++) {
    for (let j = i + 1; j < pontos.length; j++) if (Math.hypot(pontos[i][0] - pontos[j][0], pontos[i][1] - pontos[j][1]) < 30) colisoes++;
  }
  if (colisoes > MAX_COLISOES) return null;
  for (const g of grupos) {
    const larg = 30 + (g.rot.join(" ").length - 1) * 10;
    svg.append(s("rect", { class: "p-receptora", x: g.cx - larg / 2, y: g.cy - 15, width: larg, height: 30, rx: 15 }),
      s("text", { class: "p-rotulo", x: g.cx, y: g.cy + 7, "text-anchor": "middle" }, g.rot.join(" ")));
  }
  // escolas do plano por cima: losango escuro com a letra ao lado
  for (const [c, [la, lo]] of inicio) {
    const [cx, cy] = [x(lo), y(la)];
    svg.append(s("rect", { class: "p-origem", x: cx - 9, y: cy - 9, width: 18, height: 18, transform: `rotate(45 ${cx} ${cy})` }),
      s("text", { class: "p-rotulo-origem", x: cx + 13, y: cy - 10 }, letra.get(c) ?? ""));
  }
  escalaENorte(svg);
  const temChao = rotas.some((rt) => rt.chao.length);
  const fig = h("figure", { class: "prancha", style: "margin:0" },
    h("div", { class: "prancha-moldura" }, svg),
    h("div", { class: "convencoes" },
      h("h3", { class: "sr" }, "Legenda"),
      amostra("origem"), h("span", null, "escola do plano (a letra é a do cartão)"),
      amostra("receptora"), h("span", null, "escola que receberia (o número é o de \"Quem recebe\")"),
      amostra("pav"), h("span", null, "estrada pavimentada"),
      temChao ? amostra("chao") : null, temChao ? h("span", null, "estrada de chão") : null),
    h("figcaption", null, "Traçado da ida, de escola a escola, pela malha do OpenStreetMap. O ônibus passa de casa em casa: o " +
      "caminho das crianças é maior." + (faltam ? ` ${faltam === 1 ? "Uma rota não tem" : `${faltam} rotas não têm`} traçado e ` +
      `${faltam === 1 ? "fica" : "ficam"} só nos cartões.` : "")));
  return fig; // sem animação: a área se refaz a cada mudança do plano e o desenho piscaria
}
