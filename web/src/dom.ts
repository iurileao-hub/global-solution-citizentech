/** Construção de elementos sem innerHTML: todo texto entra como nó de texto, então nome de escola ou pergunta
 * digitada nunca vira HTML (proteção contra injeção, mesmo vindo de um link compartilhado). */

type Filho = Node | string | number | null | undefined | false | Filho[];
type Atributos = Record<string, string | number | boolean | null | undefined | EventListener>;

function anexar(el: Element, filhos: Filho[]): void {
  for (const f of filhos) {
    if (f === null || f === undefined || f === false) continue;
    if (Array.isArray(f)) anexar(el, f);
    else el.append(f instanceof Node ? f : String(f));
  }
}

function aplicar(el: Element, attrs: Atributos | null | undefined): void {
  for (const [k, v] of Object.entries(attrs ?? {})) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v as EventListener);
    else el.setAttribute(k, v === true ? "" : String(v));
  }
}

export function h<K extends keyof HTMLElementTagNameMap>(tag: K, attrs?: Atributos | null, ...filhos: Filho[]):
  HTMLElementTagNameMap[K] {
  const el = document.createElement(tag);
  aplicar(el, attrs);
  anexar(el, filhos);
  return el;
}

const NS = "http://www.w3.org/2000/svg";
export function s(tag: string, attrs?: Atributos | null, ...filhos: Filho[]): SVGElement {
  const el = document.createElementNS(NS, tag) as SVGElement;
  aplicar(el, attrs);
  anexar(el, filhos);
  return el;
}

export function trocar(alvo: Element, ...filhos: Filho[]): void {
  alvo.replaceChildren();
  anexar(alvo, filhos);
}
