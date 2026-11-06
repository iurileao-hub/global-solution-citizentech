/** Início, resposta a uma pergunta e lista de um assunto. */

import { base, contexto } from "../dados";
import { h, trocar } from "../dom";
import { vivo } from "../estado";
import { responder } from "../nucleo/nucleo";
import { caixaBusca, carregando } from "./componentes";
import { desenharResposta } from "./resposta";

const TITULO = "Escola em Pauta";

function preaquecer(): void {
  // a lista de nomes (~720 KB) baixa depois que a primeira tela já está desenhada
  const cedo = (fn: () => void) => ("requestIdleCallback" in window ? requestIdleCallback(fn, { timeout: 1500 }) : setTimeout(fn, 300));
  cedo(() => void contexto().catch(() => undefined));
}

export async function telaInicio(main: HTMLElement, g: number): Promise<void> {
  document.title = `${TITULO}: o impacto de fechar uma escola do campo`;
  const assuntos = h("div", null, carregando("Carregando os assuntos..."));
  const prancha = h("div", { class: "prancha-inicio" });
  const retratoTexto = h("div");
  trocar(main,
    h("div", { class: "inicio-topo" }, h("section", { class: "abertura" },
      h("h1", null, "Antes de uma escola do campo fechar, a lei manda medir o impacto."),
      h("p", { class: "sub" }, "Veja, para cada uma das 53.759 escolas do campo do país, quantas crianças estudam ali, para " +
        "onde elas iriam e quanta estrada isso significa, no mínimo. E pergunte o que a lei garante à comunidade."),
      caixaBusca({ exemplos: true })), prancha),
    h("div", { class: "duas" },
      h("section", null,
        h("h2", null, "Antes da reunião sobre o fechamento"),
        h("ol", { class: "passos" },
          h("li", null, h("div", null, h("strong", null, "Ache a escola."),
            "Pelo nome ou pelo código INEP (o número da escola no Censo Escolar). A ficha mostra os alunos, as escolas que poderiam recebê-los e a estrada até lá.")),
          h("li", null, h("div", null, h("strong", null, "Leve a ficha impressa."),
            "A frente traz os números; o verso fica em branco para a comunidade escrever o que nenhum dado mede.")),
          h("li", null, h("div", null, h("strong", null, "Peça o diagnóstico."),
            "A lei exige um diagnóstico do impacto antes de fechar. ",
            h("a", { href: "#/orientacao/C1" }, "Veja como pedir à prefeitura"), ".")))),
      h("section", null, h("h2", null, "Os assuntos que o assistente conhece"), assuntos)),
    retratoTexto);
  preaquecer();
  const b = await base();
  if (!vivo(g)) return;
  trocar(assuntos, listaAssuntos(b));
  const { pranchaBrasil } = await import("./retrato");
  if (!vivo(g)) return;
  await pranchaBrasil(prancha, retratoTexto).catch(() => prancha.remove());
}

function listaAssuntos(b: Awaited<ReturnType<typeof base>>): HTMLElement {
  return h("ul", { class: "assuntos" }, Object.entries(b.temas).map(([id, t]) => {
    const ids = b.porTema.get(id) ?? [];
    return h("li", null, h("details", null,
      h("summary", null, h("span", { class: "tema" }, t.nome), h("span", { class: "quantos" }, `${ids.length}`),
        t.descricao ? h("span", { class: "desc" }, t.descricao) : null),
      gruposDoTema(b, id)));
  }));
}

function gruposDoTema(b: Awaited<ReturnType<typeof base>>, tema: string): HTMLElement {
  const info = b.temas[tema];
  const ids = b.porTema.get(tema) ?? [];
  return h("div", null, Object.entries(info.subtemas).map(([sub, nome]) => {
    const deste = ids.filter((x) => b.registros.get(x)!.subtema === sub);
    if (!deste.length) return null;
    return [h("p", { class: "subtema" }, nome), h("ul", null, deste.map((x) =>
      h("li", null, h("a", { href: `#/orientacao/${x}` }, b.registros.get(x)!.pergunta))))];
  }));
}

export async function telaAssunto(main: HTMLElement, g: number, tema: string): Promise<void> {
  const b = await base();
  if (!vivo(g)) return;
  const info = b.temas[tema];
  if (!info) {
    document.title = "Assunto não encontrado: Escola em Pauta";
    trocar(main, h("div", { class: "erro", role: "alert" }, h("h1", null, "Assunto não encontrado"),
      h("p", null, h("a", { href: "#/" }, "Ver todos os assuntos"), ".")));
    return;
  }
  document.title = `${info.nome}: ${TITULO}`;
  const rel = (info.relacionados ?? []).filter((t) => b.temas[t]);
  trocar(main,
    h("a", { class: "voltar", href: "#/" }, "Início"),
    h("article", { class: "verbete" },
      h("h1", null, info.nome),
      info.descricao ? h("p", null, info.descricao) : null,
      h("div", { class: "assuntos-abertos" }, gruposDoTema(b, tema)),
      rel.length ? h("p", null, "Assuntos relacionados: ", rel.map((t, i) => [i ? ", " : "",
        h("a", { href: `#/assunto/${t}` }, b.temas[t].nome)]), ".") : null),
    caixaBusca({ titulo: false }));
}

export async function telaPergunta(main: HTMLElement, g: number, texto: string, codigo = false): Promise<void> {
  trocar(main, caixaBusca({ valor: codigo ? "" : texto, titulo: false }), carregando("Procurando na base..."));
  const ctx = await contexto();
  if (!vivo(g)) return;
  const r = responder(ctx, texto);
  if (r.tipo === "escola") {
    const mais = r.extras.length ? `?mais=${r.extras.join(",")}` : "";
    location.replace(`#/escola/${r.codigo}${mais}`);
    return;
  }
  const titulo = r.tipo === "unica" || r.tipo === "codigo" ? ctx.base.registros.get(r.rid)!.pergunta : "Resposta";
  document.title = `${titulo}: ${TITULO}`;
  trocar(main,
    caixaBusca({ valor: codigo ? "" : texto, titulo: false }),
    codigo ? null : h("p", { class: "pergunta-feita" }, `Você perguntou: “${texto}”`),
    desenharResposta(ctx, r));
}
