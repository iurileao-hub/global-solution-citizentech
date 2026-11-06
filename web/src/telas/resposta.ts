/** Desenha a resposta do assistente (o objeto do núcleo) como um "verbete". O texto é o da base, palavra por
 * palavra; o que muda do terminal é só a diagramação (links no lugar de "[C1]", tabela no lugar das linhas).
 * O código da orientação ("D1") não aparece na tela: é atalho de teclado do terminal, e para quem lê no celular
 * o nome da orientação é a própria pergunta. A busca continua aceitando "D1", e o texto copiado é o do terminal. */

import { h } from "../dom";
import type { Base } from "../nucleo/base";
import { filtrar, type EscolaNome } from "../nucleo/escolas";
import { type BlocoFechamentos, mil, NOME_POVO, nomeLugar } from "../nucleo/fechamentos";
import { amostra, type Contexto, MAX_ESCOLAS_LISTA, MENSAGEM, type Resposta } from "../nucleo/nucleo";
import { avisoParcial, data, mesmoMunicipio, RODAPE, textoResposta } from "../nucleo/respostas";
import { escola as baixarEscola } from "../dados";
import { faixaEtapas, nomeLegivel, ordenarEtapas } from "../formato";
import { botaoCompartilhar, botaoCopiar, comCodigos } from "./componentes";

type Ctx = Contexto<EscolaNome>;

function linkOrientacao(base: Base, rid: string): HTMLElement {
  return h("li", null, h("a", { href: `#/orientacao/${rid}` }, base.registros.get(rid)!.pergunta));
}

export function caminhos(base: Base, titulo: string, ids: string[]): HTMLElement | null {
  if (!ids.length) return null;
  return h("nav", { class: "caminhos", "aria-label": titulo }, h("h2", null, titulo),
    h("ul", null, ids.map((x) => linkOrientacao(base, x))));
}

export function quadroFechamentos(b: BlocoFechamentos): HTMLElement {
  const n = b.numeros;
  const serie = n.extintas_por_ano ?? {};
  const maior = Math.max(1, ...b.anos.map((a) => serie[a] ?? 0));
  const onde = nomeLugar(b.lugar);
  return h("div", { class: "numeros" },
    h("table", { class: "quadro" },
      h("caption", null, `Escolas públicas rurais ${onde}, pelo Censo Escolar`),
      h("tbody", null,
        h("tr", null, h("th", { scope: "row" }, "Em atividade em 2025"), h("td", { class: "num" }, mil(n.ativas_2025))),
        h("tr", null, h("th", { scope: "row" }, `Extintas (encerradas de vez) de ${b.anos[0]} a ${b.anos[b.anos.length - 1]}`),
          h("td", { class: "num" }, mil(n.extintas_2019_2025))),
        h("tr", null, h("th", { scope: "row" }, "Paralisadas em 2025 (sem aulas, mas sem extinção formal)"),
          h("td", { class: "num" }, n.paralisadas_2025 ? mil(n.paralisadas_2025) : "nenhuma")),
        n.paralisadas_2025 ? h("tr", null, h("th", { scope: "row" }, "das quais paralisadas há 5 anos ou mais"),
          h("td", { class: "num" }, mil(n.paralisadas_5_anos_ou_mais))) : null)),
    h("figure", { style: "margin:0 0 1rem" },
      h("div", { class: "serie", role: "img", "aria-label": "Extinções por ano: " +
        b.anos.map((a) => `${a}, ${mil(serie[a] ?? 0)}`).join("; ") },
      b.anos.map((a) => h("div", { class: "barra", style: `height:${(100 * (serie[a] ?? 0)) / maior}%`,
        title: `${a}: ${mil(serie[a] ?? 0)}` }))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, b.anos.map((a) => h("span", null, a.slice(2)))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, b.anos.map((a) => h("span", null, mil(serie[a] ?? 0)))),
      h("figcaption", null, "Escolas extintas por ano")),
    b.anoPico ? h("p", { class: "aviso" }, `Mais da metade das extinções caiu em ${b.anoPico}. Uma concentração assim pode ` +
      "ser regularização (a rede registra de uma vez o fim de escolas que já estavam paradas); a Secretaria de " +
      "Educação sabe dizer.") : null,
    povos(b),
    b.lugar === null ? h("p", null, "Para ver o seu estado ou município, escreva o nome dele na pergunta (por exemplo: ",
      h("a", { href: "#/pergunta/" + encodeURIComponent("quantas escolas fecharam em Minas Gerais?") },
        "quantas escolas fecharam em Minas Gerais?"), ").") : null,
    h("p", { class: "legenda" }, "Para citar: \"levantamento do projeto Escola em Pauta com os microdados do Censo " +
      "Escolar (INEP)\". O INEP publica os dados por escola; estes totais são contados pelo projeto."));
}

function povos(b: BlocoFechamentos): HTMLElement | null {
  if (!b.povos) return null;
  if (b.povos === "so_estado") {
    return h("p", null, "O recorte de escolas indígenas e quilombolas existe só por estado e para o Brasil; pergunte " +
      "pelo estado para ver.");
  }
  return h("div", null, b.povos.map(({ grupo, numeros: x }) => {
    if (!x) return h("p", null, `Escolas ${NOME_POVO[grupo]}: nenhuma registrada aqui pelo Censo.`);
    return h("p", null, h("strong", null, `Só escolas ${NOME_POVO[grupo]}: `),
      `${mil(x.ativas_2025)} em atividade em 2025; `,
      x.extintas_2019_2025 ? `pelo menos ${mil(x.extintas_2019_2025)} ${x.extintas_2019_2025 === 1 ? "extinta" : "extintas"}`
        : "nenhuma extinta registrada",
      " de 2019 a 2025; ",
      x.paralisadas_2025 ? `${mil(x.paralisadas_2025)} ${x.paralisadas_2025 === 1 ? "paralisada" : "paralisadas"}`
        : "nenhuma paralisada", " em 2025.");
  }), h("p", { class: "legenda" }, "\"Pelo menos\": o Censo só marca terra indígena ou comunidade quilombola enquanto " +
    "a escola funciona, e a escola parada desde antes de 2019 fica fora desta conta."));
}

function verbeteOrientacao(ctx: Ctx, r: Extract<Resposta, { tipo: "unica" | "codigo" }>): HTMLElement {
  const base = ctx.base;
  const reg = base.registros.get(r.rid)!;
  const tema = base.temas[reg.tema];
  const pergunta = (c: string) => base.registros.get(c)?.pergunta;
  const fora = r.tipo === "unica" ? r.fora : [];
  const extras = r.tipo === "unica" ? r.extras : [];
  const rel = (reg.relacionados ?? []).slice(0, 3);
  const ref = reg.referencia;
  const url = location.href;
  return h("article", { class: "verbete" },
    fora.length ? h("p", { class: "aviso", role: "note" }, h("strong", null, "Atenção: "),
      avisoParcial(fora).replace(/^Atenção: /, "")) : null,
    h("a", { class: "tema-rotulo", href: `#/assunto/${reg.tema}` }, tema.nome),
    h("h1", null, reg.pergunta),
    h("p", null, comCodigos(reg.orientacao, pergunta)),
    r.numeros ? quadroFechamentos(r.numeros) : null,
    reg.confirmar ? h("div", { class: "confirme" }, h("strong", null, "Confirme"), h("span", null, comCodigos(reg.confirmar, pergunta))) : null,
    h("p", { class: "fonte" },
      reg.dados
        ? ["Fonte: ", h("a", { href: ref.url, rel: "noopener" }, ref.titulo), ". Os totais foram contados pelo projeto; o texto ",
          `desta orientação foi conferido em ${data(reg.data_verificacao)}.`]
        : ["Fonte: ", h("a", { href: ref.url, rel: "noopener" }, ref.titulo), `. Conferida em ${data(reg.data_verificacao)}.`],
      ref.outras && ref.outras.length ? [" Outras fontes conferidas: ", ref.outras.map((u, i) =>
        [i ? ", " : "", h("a", { href: u, rel: "noopener" }, dominio(u))]), "."] : null),
    caminhos(base, "Para continuar", rel),
    caminhos(base, "Talvez também interesse", extras),
    h("div", { class: "acoes" },
      botaoCopiar("Copiar o texto", () => textoResposta(base, r, () => { throw new Error("sem escola"); }, "", "")),
      botaoCompartilhar(reg.pergunta, url)),
    h("p", { class: "legenda" }, RODAPE));
}

function verbeteAmbigua(ctx: Ctx, ids: string[]): HTMLElement {
  return h("article", { class: "verbete" },
    h("h1", null, "Sua pergunta combina com mais de um assunto. Qual deles?"),
    h("ul", { class: "opcoes" }, ids.map((x) => h("li", null, h("a", { href: `#/orientacao/${x}` },
      ctx.base.registros.get(x)!.pergunta)))),
    h("p", null, "Ou reformule a pergunta com outras palavras."));
}

function verbeteNenhuma(ctx: Ctx): HTMLElement {
  return h("article", { class: "verbete" },
    h("h1", null, "Não encontrei uma orientação confiável para essa pergunta"),
    h("p", null, "A base deste assistente não tem uma resposta segura para isso. Prefiro dizer isso a inventar uma resposta."),
    h("p", null, "Você pode reformular a pergunta com outras palavras, consultar uma escola pelo nome ou escolher um dos assuntos que conheço:"),
    h("ul", { class: "opcoes" }, Object.entries(ctx.base.temas).map(([id, t]) =>
      h("li", null, h("a", { href: `#/assunto/${id}` }, t.nome)))),
    h("p", null, "Para uma dúvida fora desses assuntos: a Secretaria de Educação responde pela escola e pela rede; a " +
      "Defensoria Pública dá orientação jurídica de graça."),
    h("p", { class: "legenda" }, RODAPE));
}

/** "www.planalto.gov.br" a partir do endereço: curto, e diz de onde a fonte vem. */
function dominio(u: string): string {
  try {
    return new URL(u).hostname.replace(/^www\./, "");
  } catch {
    return u;
  }
}

/** Uma escola da lista de nomes repetidos. Com poucas na tela, cada uma ganha alunos e etapas (baixados do pedaço
 * dela): sem isso, três "Escola São José" no mesmo município só se distinguem abrindo uma por uma. */
function itemEscola(e: EscolaNome, detalhar: boolean): HTMLElement {
  const info = h("span", { class: "e-info" });
  if (detalhar) {
    void baixarEscola(e.c).then((x) => {
      if (!x) return;
      const et = ordenarEtapas(Object.keys(x.e));
      info.textContent = `${mil(x.t)} ${x.t === 1 ? "aluno" : "alunos"}${et.length ? `, ${faixaEtapas(et)}` : ""}`;
    }).catch(() => undefined);
  }
  return h("li", null, h("a", { href: `#/escola/${e.c}` },
    h("span", { class: "e-nome" }, nomeLegivel(e.n ?? "")),
    h("span", { class: "e-lugar" }, e.m && e.uf ? `${e.m}/${e.uf}` : "município não informado"),
    h("span", { class: "e-cod" }, e.c), info));
}

const MOSTRA_FILTRADA = 60;

/** Nome repetido: a lista e um filtro por município e UF (no terminal, o assistente pergunta um de cada vez). */
function verbeteEscolas(r: Extract<Resposta, { tipo: "escola_ambigua" }>, todas: EscolaNome[]): HTMLElement {
  const total = todas.length;
  const nUfs = new Set(todas.map((e) => e.uf)).size;
  const lista = h("ul", { class: "escolas-lista" });
  const resumo = h("p", { "aria-live": "polite" });
  const mostrar = (es: EscolaNome[], filtrada: boolean) => {
    const parte = filtrada ? es.slice(0, MOSTRA_FILTRADA) : es.length > MAX_ESCOLAS_LISTA ? amostra(es, MAX_ESCOLAS_LISTA) : es;
    lista.replaceChildren(...parte.map((e) => itemEscola(e, parte.length <= 12)));
    resumo.textContent = !es.length
      ? "Nenhuma dessas escolas fica nesse município ou UF. Confira o nome do município, ou digite o código INEP da escola."
      : es.length > parte.length
        ? `Mostrando ${parte.length} de ${mil(es.length)}${filtrada ? "" : ", uma de cada UF por vez"}.`
        : es.length === 1 ? "Uma escola." : `${mil(es.length)} escolas.`;
  };
  const mun = h("input", { id: "f-mun", name: "municipio", autocomplete: "address-level2" });
  const uf = h("input", { id: "f-uf", name: "uf", maxlength: 2, autocomplete: "off", style: "text-transform:uppercase" });
  const form = h("form", {
    class: "filtro",
    onsubmit: (ev: Event) => {
      ev.preventDefault();
      const f = filtrar(todas, mun.value, uf.value);
      if (f.length === 1) {
        location.hash = `#/escola/${f[0].c}`;
        return;
      }
      mostrar(f, Boolean(mun.value.trim() || uf.value.trim()));
    },
  },
  h("div", null, h("label", { for: "f-mun" }, "Município"), mun),
  h("div", null, h("label", { for: "f-uf" }, "UF"), uf),
  h("button", { class: "botao", type: "submit" }, "Filtrar"));
  mostrar(todas, false);
  void r;
  return h("article", { class: "verbete" },
    h("h1", null, `${mil(total)} escolas do campo têm essas palavras no nome`),
    h("p", null, mesmoMunicipio(todas)
      ? `Todas ficam em ${todas[0].m}/${todas[0].uf}. Para saber qual é a sua, compare os alunos e as etapas, ou abra cada ficha.`
      : [nUfs > 1 ? `Elas ficam em ${nUfs} UFs. ` : "", "Para achar a sua, informe o município e a UF, ou escolha na lista."]),
    form, resumo, lista);
}

export function desenharResposta(ctx: Ctx, r: Resposta): HTMLElement {
  switch (r.tipo) {
    case "vazia":
      // "quantos alunos tem?" sem a escola: o que falta é o nome dela, não a pergunta
      return h("article", { class: "verbete" }, h("h1", null, r.mensagem === MENSAGEM.alunos ? "Qual escola?" : "Faltou a pergunta"),
        h("p", null, r.mensagem));
    case "codigo":
    case "unica":
      return verbeteOrientacao(ctx, r);
    case "ambigua":
      return verbeteAmbigua(ctx, r.ids);
    case "escola_ambigua":
      return verbeteEscolas(r, r.achado.escolas);
    case "nenhuma":
      return verbeteNenhuma(ctx);
    case "escola":
      return h("p", null, h("a", { href: `#/escola/${r.codigo}` }, "Abrir a ficha da escola"));
  }
}
