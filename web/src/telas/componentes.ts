/** Peças repetidas entre as telas: a caixa de busca, os botões de copiar e compartilhar, o aviso de carregamento. */

import { contexto, nomesProntos } from "../dados";
import { h } from "../dom";

export const EXEMPLOS = [
  "Durval Máximo",
  "A prefeitura pode fechar a escola sem consultar a gente?",
  "Quem paga o ônibus escolar?",
  "Quantas escolas fecharam no Piauí?",
];

export function irPara(hash: string): void {
  if (location.hash === hash) window.dispatchEvent(new HashChangeEvent("hashchange"));
  else location.hash = hash;
}

export function perguntar(texto: string): void {
  irPara("#/pergunta/" + encodeURIComponent(texto.trim()));
}

/** A caixa única: o núcleo decide se o texto é escola, código ou pergunta (como no terminal). */
export function caixaBusca(opcoes: { valor?: string; titulo?: boolean; exemplos?: boolean } = {}): HTMLElement {
  const id = "caixa-" + Math.random().toString(36).slice(2, 8);
  const entrada = h("input", {
    id, type: "search", name: "q", autocomplete: "off", enterkeyhint: "search", spellcheck: "false",
    placeholder: "Ex.: Durval Máximo, 32049501, quem paga o ônibus?",
  });
  if (opcoes.valor) entrada.value = opcoes.valor;
  const estado = h("p", { class: "estado", "aria-live": "polite" });
  const form = h("form", {
    class: "busca", role: "search",
    onsubmit: (ev: Event) => {
      ev.preventDefault();
      if (!entrada.value.trim()) {
        estado.textContent = "Escreva o nome da escola, o código INEP ou uma pergunta.";
        entrada.focus();
        return;
      }
      perguntar(entrada.value);
    },
  },
  h("label", { for: id }, opcoes.titulo === false ? "Outra escola ou outra pergunta" : "Nome da escola, código INEP ou sua pergunta"),
  h("div", { class: "busca-linha" }, entrada, h("button", { class: "botao", type: "submit" }, "Buscar")),
  opcoes.exemplos ? h("ul", { class: "exemplos", "aria-label": "Exemplos para experimentar" },
    EXEMPLOS.map((x) => h("li", null, h("button", { type: "button", class: "exemplo", onclick: () => perguntar(x) }, x)))) : null,
  estado);
  if (!nomesProntos()) {
    estado.textContent = "Preparando a lista das 53.759 escolas do campo...";
    contexto().then(() => {
      if (estado.textContent?.startsWith("Preparando")) estado.textContent = "";
    }).catch(() => {
      estado.textContent = "Sem conexão para baixar a lista de escolas. As orientações já abertas continuam aqui.";
    });
  }
  return form;
}

export function carregando(texto = "Carregando..."): HTMLElement {
  return h("p", { class: "carregando", role: "status" }, texto);
}

async function copiarTexto(texto: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(texto);
    return true;
  } catch {
    const area = h("textarea", { readonly: true, style: "position:fixed;opacity:0" });
    area.value = texto;
    document.body.append(area);
    area.select();
    const ok = document.execCommand("copy");
    area.remove();
    return ok;
  }
}

/** Botão que copia um texto (para colar no WhatsApp) e diz que copiou. */
export function botaoCopiar(rotulo: string, texto: () => string): HTMLButtonElement {
  const b = h("button", { type: "button", class: "botao secundario" }, rotulo);
  b.addEventListener("click", async () => {
    const ok = await copiarTexto(texto());
    b.textContent = ok ? "Texto copiado" : "Não foi possível copiar";
    setTimeout(() => (b.textContent = rotulo), 2500);
  });
  return b;
}

/** Compartilhar pelo menu do celular (WhatsApp, e-mail...) ou, sem ele, copiar o link. */
export function botaoCompartilhar(titulo: string, url: string): HTMLButtonElement {
  const rotulo = "Compartilhar o link";
  const b = h("button", { type: "button", class: "botao secundario" }, rotulo);
  b.addEventListener("click", async () => {
    if (navigator.share) {
      try {
        await navigator.share({ title: titulo, url });
        return;
      } catch (e) {
        if ((e as DOMException).name === "AbortError") return;
      }
    }
    const ok = await copiarTexto(url);
    b.textContent = ok ? "Link copiado" : "Não foi possível copiar";
    setTimeout(() => (b.textContent = rotulo), 2500);
  });
  return b;
}

/** Corta o texto da base nas citações de outra orientação ("veja C1"): trechos de texto e, entre eles, a orientação
 * citada com a sua pergunta. Código que não existe na base fica como texto. Parte pura: os testes conferem que
 * nenhum trecho se perde. */
export function partesComCodigos(texto: string, pergunta: (c: string) => string | undefined):
  (string | { rid: string; pergunta: string })[] {
  const partes: (string | { rid: string; pergunta: string })[] = [];
  let ultimo = 0;
  for (const m of texto.matchAll(/\b([CDFT]\d{1,2})\b/g)) {
    const p = pergunta(m[1]);
    if (!p) continue;
    partes.push(texto.slice(ultimo, m.index), { rid: m[1], pergunta: p });
    ultimo = m.index! + m[0].length;
  }
  partes.push(texto.slice(ultimo));
  return partes;
}

/** "(veja C1)" vira "(veja “Como pedir à prefeitura…?”)", com link: o código só faz sentido no terminal. */
export function comCodigos(texto: string, pergunta: (c: string) => string | undefined): (string | HTMLElement)[] {
  return partesComCodigos(texto, pergunta).map((x) =>
    typeof x === "string" ? x : h("a", { href: `#/orientacao/${x.rid}` }, `“${x.pergunta}”`));
}
