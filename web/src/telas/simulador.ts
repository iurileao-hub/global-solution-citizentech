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
  type Resultado, simular,
} from "../nucleo/simulacao";
import { normalizar } from "../nucleo/texto";
import { botaoCompartilhar, carregando } from "./componentes";

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

function montagem(e: Estado, mudou: () => void): HTMLElement {
  const escolas = [...e.mun.escolas].sort((a, b) => a.n.localeCompare(b.n, "pt-BR"));
  const caixas = new Map<number, HTMLInputElement>();
  const itens = escolas.map((x) => {
    const id = `sim-${x.c}`;
    const cx = h("input", { type: "checkbox", id, checked: e.fechar.has(x.c) || null });
    cx.checked = e.fechar.has(x.c);
    cx.addEventListener("change", () => {
      if (cx.checked) e.fechar.add(x.c);
      else e.fechar.delete(x.c);
      mudou();
    });
    caixas.set(x.c, cx);
    const total = Object.values(x.e).reduce((s, v) => s + v, 0);
    const detalhe = total
      ? `${criancas(total)}, ${listaPt(ordenarEtapas(Object.keys(x.e)).map((k) => ETAPA_ROTULO[k]))}`
      : `sem alunos da creche ao ensino médio${x.t ? ` (${mil(x.t)} de EJA ou outra modalidade)` : ""}`;
    return h("li", { "data-nome": normalizar(x.n) }, cx,
      h("label", { for: id }, nomeLegivel(x.n), h("span", { class: "legenda" }, ` ${detalhe}${x.r.length ? "" : "; sem rota calculada"}`)));
  });
  const ul = h("ul", { class: "sim-escolas" }, itens);
  const sincronizar = () => {
    for (const [c, cx] of caixas) cx.checked = e.fechar.has(c);
  };
  const n = h("input", { type: "number", id: "sim-menos", min: "1", max: "9999", value: String(ATALHO_PADRAO), inputmode: "numeric" });
  const filtro = escolas.length > 12
    ? h("input", { type: "search", class: "sim-filtro", "aria-label": "Filtrar as escolas pelo nome", placeholder: "Filtrar pelo nome",
      oninput: (ev: Event) => {
        const t = normalizar((ev.target as HTMLInputElement).value);
        for (const li of ul.children as HTMLCollectionOf<HTMLElement>) li.hidden = Boolean(t) && !li.dataset.nome!.includes(t);
      } })
    : null;
  return h("section", { class: "sim-montagem nao-imprime" },
    h("h2", null, "Monte o plano"),
    h("p", null, `As ${mil(escolas.length)} escolas do campo de ${e.mun.municipio} no índice. Marque as que fechariam.`),
    h("div", { class: "sim-atalho" },
      h("label", { for: "sim-menos" }, "Marcar só as escolas com menos de"), n, h("span", null, "alunos"),
      h("button", { type: "button", class: "botao secundario", onclick: () => {
        const lim = Math.max(1, Math.floor(Number(n.value) || ATALHO_PADRAO));
        e.fechar = new Set(menoresQue(e.mun, lim));
        sincronizar();
        mudou();
      } }, "Marcar"),
      h("button", { type: "button", class: "botao-texto", onclick: () => {
        e.fechar.clear();
        e.indicacoes = {};
        sincronizar();
        mudou();
      } }, "Limpar o plano")),
    filtro, ul);
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

function manchete(r: Resultado): HTMLElement {
  const longe = r.faixas_min["60_a_120"] + r.faixas_min["120_ou_mais"];
  const partes: (string | HTMLElement)[] = ["Neste plano, ", h("b", null, criancas(r.criancas)),
    r.fechadas.length === 1 ? " da escola mudariam de escola." : ` de ${mil(r.fechadas.length)} escolas mudariam de escola.`];
  if (r.com_destino && longe) {
    partes.push(` Para ${mil(longe)} delas, `, h("b", { class: "piso" }, "a escola que receberia fica a 1 hora ou mais " +
      "de ônibus da escola de hoje"), ", ida e volta, por dia, pelo menos.");
  }
  return h("p", { class: "manchete" }, partes);
}

function fichaFecha(r: Resultado): HTMLElement | null {
  if (!r.ficha_fecha) return null;
  return h("p", { class: "aviso", role: "note" }, h("strong", null, "A ficha sozinha não basta: "),
    `para ${criancas(r.ficha_fecha)}, a escola que a ficha individual aponta como destino também fecha neste plano.`);
}

function faixas(r: Resultado): HTMLElement | null {
  if (!r.com_destino) return null;
  const tabela = (titulo: string, dados: Record<string, number>, rotulos: Readonly<Record<string, string>>) => {
    const maior = Math.max(1, ...Object.values(dados));
    return h("table", { class: "quadro sim-faixas" }, h("caption", null, titulo),
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Por dia, ida e volta"), h("th", { scope: "col", class: "num" }, "Crianças"),
        h("th", { scope: "col", "aria-hidden": "true" }))),
      h("tbody", null, Object.entries(dados).map(([k, q]) => h("tr", null, h("th", { scope: "row" }, rotulos[k]),
        h("td", { class: "num" }, mil(q)),
        h("td", { class: "sim-barra-cel", "aria-hidden": "true" }, q ? h("span", { class: "sim-barra", style: `width:${(100 * q) / maior}%` }) : null)))));
  };
  const extras: string[] = [];
  if (r.metade_chao) extras.push(`${criancas(r.metade_chao)} ${r.metade_chao === 1 ? "iria" : "iriam"} por estrada com metade ou mais de chão.`);
  if (r.outro_municipio) {
    extras.push(`${criancas(r.outro_municipio)} ${r.outro_municipio === 1 ? "iria" : "iriam"} para escola de outro município, por ser a ` +
      "mais próxima que oferece a etapa. A prefeitura pode indicar outra.");
  }
  return h("section", { class: "sim-s-faixas" },
    h("h2", null, "Quanta estrada"),
    h("p", null, "A estrada medida é a que liga a escola fechada à escola que receberia a etapa. ", h("b", null, "É o mínimo do caminho do " +
      "ônibus que sai da comunidade."), " Não é quanto cada criança anda a mais: quem mora entre as duas escolas anda menos, " +
      "quem mora do outro lado anda mais."),
    h("div", { class: "sim-faixas-par" }, tabela("Distância", r.faixas_km, ROTULO_KM), tabela("Tempo de ônibus", r.faixas_min, ROTULO_MIN)),
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

function linhaEtapa(e: Estado, x: EscolaSim, a: Alocacao, mudou: () => void): HTMLElement {
  const chave = `${a.origem}:${a.etapa}`;
  const opcoes = x.r.filter((r) => r[6].includes(a.etapa));
  let destino: (string | HTMLElement)[];
  if (a.destino === null) destino = [h("span", { class: "sim-sem" }, `Sem destino: ${MOTIVO[a.motivo!] ?? a.motivo}.`)];
  else {
    const marcas = [a.outro_municipio ? "outro município" : "", a.indicada ? "indicada pela prefeitura" : ""].filter(Boolean);
    destino = [h("b", null, nomeLegivel(nomeDe(e.mun, a.destino))), marcas.length ? h("span", { class: "sim-marca" }, ` (${marcas.join("; ")})`) : "",
      h("br"), a.km! < MESMO_LUGAR_KM ? "no mesmo lugar ou quase" : `pelo menos ${kmDia(a.km!)} por dia`,
      a.km! >= MESMO_LUGAR_KM && a.min !== null ? `, ${horas(a.min)} de ônibus` : ""];
  }
  if (a.aviso) {
    const naLista = x.r.some((r) => r[0] === e.indicacoes[chave]);
    destino.push(h("span", { class: "sim-aviso" }, a.aviso === "indicada_fecha"
      ? " A escola indicada também fecha neste plano: valeu a regra."
      : naLista ? " A escola indicada não oferece esta etapa: valeu a regra."
      : " A escola indicada não está entre as 10 calculadas para esta escola: valeu a regra."));
  }
  let escolha: HTMLElement | null = null;
  if (opcoes.length) {
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
      mudou();
    });
    escolha = h("div", { class: "sim-indicar nao-imprime" }, h("label", { for: id }, "Destino indicado pela prefeitura"), sel);
  }
  // papéis explícitos: no celular a tabela vira blocos (display: block), e alguns navegadores esquecem que é tabela
  return h("tr", { role: "row" },
    h("th", { scope: "row", role: "rowheader" }, etapaRotulo(a.etapa), h("br"), h("span", { class: "legenda" }, criancas(a.n))),
    h("td", { role: "cell" }, destino, escolha));
}

function cadaEtapa(e: Estado, r: Resultado, mudou: () => void): HTMLElement {
  const porEscola = new Map<number, Alocacao[]>();
  for (const a of r.alocacoes) porEscola.set(a.origem, [...(porEscola.get(a.origem) ?? []), a]);
  const abrir = r.fechadas.length <= 4;
  const blocos = r.escolas.map((s) => {
    const aberta = e.vistas.has(s.c) ? e.abertas.has(s.c) : abrir;
    if (aberta) e.abertas.add(s.c);
    e.vistas.add(s.c);
    const x = e.mun.escolas.find((y) => y.c === s.c)!;
    const al = porEscola.get(s.c) ?? [];
    const resumo = !s.criancas ? "sem alunos da creche ao ensino médio"
      : al.every((a) => a.destino === null) ? `${criancas(s.criancas)}, sem destino calculado`
      : `${criancas(s.criancas)}, ${s.destinos === 1 ? "um destino" : `${s.destinos} destinos`}`;
    const d = h("details", { class: "sim-escola", open: aberta || null },
      h("summary", null, h("b", null, nomeLegivel(s.n)), h("span", { class: "legenda" }, ` ${resumo}`)),
      al.length ? h("table", { class: "quadro sim-etapas", role: "table" },
        h("thead", { role: "rowgroup" }, h("tr", { role: "row" }, h("th", { scope: "col", role: "columnheader" }, "Etapa"),
          h("th", { scope: "col", role: "columnheader" }, "Para onde iria"))),
        h("tbody", { role: "rowgroup" }, al.map((a) => linhaEtapa(e, x, a, mudou)))) : null,
      h("p", { class: "nao-imprime", style: "margin:.3rem 0 .6rem" }, h("a", { href: `#/escola/${s.c}` }, "Abrir a ficha desta escola")));
    d.addEventListener("toggle", () => {
      if (d.dataset.reabrir) return; // aberta só para imprimir (beforeprint): não é escolha da pessoa
      if (d.open) e.abertas.add(s.c);
      else e.abertas.delete(s.c);
    });
    return d;
  });
  return h("section", { class: "sim-s-etapas" },
    h("h2", null, "Para onde iria cada etapa"),
    h("p", null, "Cada etapa vai para a escola mais próxima por estrada que a oferece e não fecha neste plano. ",
      h("span", { class: "nao-imprime" }, "Se a prefeitura já indicou outra, escolha em \"Destino indicado pela prefeitura\": a conta " +
        "passa a usar a indicada."), h("span", { class: "so-impressao-inline" }, "\"Indicada pela prefeitura\" marca o destino que " +
        "a prefeitura informou.")),
    blocos);
}

function quemRecebe(r: Resultado): HTMLElement | null {
  if (!r.receptoras.length) return null;
  return h("section", { class: "sim-s-recebe" },
    h("h2", null, "Quem recebe"),
    h("p", null, "O aumento é sobre a matrícula de hoje. O número de vagas e de turnos não é publicado: ",
      h("b", null, "não sabemos se cabe"), ", só quanto a escola cresceria."),
    h("div", { class: "tabela-rolagem" }, h("table", { class: "quadro" },
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Escola"), h("th", { scope: "col", class: "num" }, "Recebe"),
        h("th", { scope: "col", class: "num" }, "Tem hoje"), h("th", { scope: "col", class: "num" }, "Aumento"))),
      h("tbody", null, r.receptoras.map((x) => {
        const dobra = x.mat !== null && x.mat > 0 && x.recebe >= x.mat;
        const onde = [x.rural ? "rural" : "urbana", x.m || x.uf ? `em ${x.m ?? ""}${x.uf ? "/" + x.uf : ""}` : ""].filter(Boolean).join(", ");
        return h("tr", { class: dobra ? "destaque" : null },
          h("th", { scope: "row" }, nomeLegivel(x.n), h("br"), h("span", { class: "legenda" },
            `${onde}; ${listaPt(x.etapas.map((k) => ETAPA_ROTULO[k]))}`)),
          h("td", { class: "num" }, `+${mil(x.recebe)}`),
          h("td", { class: "num" }, x.mat === null ? "?" : mil(x.mat)),
          h("td", { class: "num" }, x.mat ? `+${pct(x.recebe / x.mat)}` : "?", dobra ? h("span", { class: "sim-marca" }, h("br"), "dobra ou mais") : null));
      })))));
}

function cadaEscola(r: Resultado): HTMLElement | null {
  if (r.escolas.length < 2) return null;
  const linhas = [...r.escolas].sort((a, b) => a.n.localeCompare(b.n, "pt-BR"));
  return h("section", { class: "sim-s-escolas" },
    h("h2", null, "O que cada escola do plano sustenta"),
    h("p", null, "Pré-escola e anos iniciais: a Res. CNE/CEB 2/2008, art. 3º, pede que essas crianças estudem na própria " +
      "comunidade. \"Se ficar aberta\": quantas crianças de outras escolas do plano iriam para ela (pela regra ou pela indicação " +
      "da prefeitura) se só ela deixasse de fechar. " +
      "A tabela não diz qual escola fechar."),
    h("div", { class: "tabela-rolagem" }, h("table", { class: "quadro" },
      h("thead", null, h("tr", null, h("th", { scope: "col" }, "Escola"), h("th", { scope: "col", class: "num" }, "Crianças"),
        h("th", { scope: "col", class: "num" }, "Pré-escola e anos iniciais"), h("th", { scope: "col", class: "num" }, "Se ficar aberta, receberia"))),
      h("tbody", null, linhas.map((s) => h("tr", null,
        h("th", { scope: "row" }, nomeLegivel(s.n), s.ficha_fecha ? h("span", { class: "sim-marca" }, h("br"), "a escola da ficha dela também fecha") : null),
        h("td", { class: "num" }, mil(s.criancas)), h("td", { class: "num" }, mil(s.pre_iniciais)),
        h("td", { class: "num" }, s.acolheria ? `+${mil(s.acolheria)}` : "0")))))));
}

function comoContamos(r: Resultado): HTMLElement {
  return h("section", { class: "sim-s-como" },
    h("h2", null, "Como contamos"),
    h("ul", null,
      h("li", null, "Para cada escola fechada, olhamos as 10 escolas mais próximas por estrada (pré-cálculo pela malha do " +
        "OpenStreetMap). Cada etapa vai para a primeira delas que oferece a etapa e não fecha no plano."),
      h("li", null, "A ficha de cada escola responde outra pergunta: a escola mais próxima que recebe TODAS as etapas de uma vez " +
        "(a família inteira num destino só). Por isso a distância aqui pode ser menor que a da ficha."),
      h("li", null, "A ordem dos fechamentos não muda nada: a conta parte sempre da escola de origem da criança, não de uma escola " +
        "que a receberia e também fecha."),
      h("li", null, "Não realocamos por falta de vaga, porque vagas e turnos não são públicos. Escolas urbanas e de outro município " +
        "não entram no plano: os alunos delas não estão no índice."),
      r.fora_das_etapas ? h("li", null, `${mil(r.fora_das_etapas)} alunos de EJA, educação profissional ou outra modalidade das ` +
        "escolas do plano não entram na conta (a busca de receptoras usa da creche ao ensino médio regular).") : null));
}

function resultado(e: Estado, r: Resultado, mudou: () => void): HTMLElement[] {
  if (!r.fechadas.length) {
    return [h("p", { class: "sem-numero", role: "note" }, "Marque ao menos uma escola no plano para ver para onde iriam as crianças.")];
  }
  return [
    h("p", { class: "so-impressao" }, h("b", null, `Escolas do plano (${r.fechadas.length}): `),
      listaPt(r.escolas.map((s) => nomeLegivel(s.n))) + "."),
    r.aviso_fluvial ? h("p", { class: "aviso", role: "note" }, h("strong", null, "Atenção: "), "parte do transporte escolar " +
      "neste estado é por rio. A rota por estrada pode não ser o caminho das crianças.") : null,
    semDestino(r),
    manchete(r),
    fichaFecha(r),
    faixas(r),
    cadaEtapa(e, r, mudou),
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
    vistas: new Set(), abertas: new Set() };
  const area = h("div", { class: "sim-resultado" });
  // o resumo é o que o leitor de tela anuncia a cada mudança (a área inteira passaria de 100 mil caracteres)
  const status = h("p", { class: "sim-status", role: "status" });
  const rodapeLink = h("span", { class: "so-impressao" });
  const urlAtual = () => new URL(link(estado), location.href).href;
  const compartilhar = h("div", { class: "acoes" },
    h("button", { type: "button", class: "botao", onclick: () => window.print() }, "Imprimir o diagnóstico do plano"));
  const mudou = (primeira = false) => {
    if (!primeira) history.replaceState(null, "", link(estado));
    const r = simular(mun, estado.fechar, estado.indicacoes);
    // indicação que o plano tornou sem efeito (escola desmarcada) sai do estado: o link fica igual ao que se vê
    estado.indicacoes = Object.fromEntries(Object.entries(estado.indicacoes).filter(([k]) => estado.fechar.has(Number(k.split(":")[0]))));
    // refazer a área não pode levar o foco embora (quem usa teclado perderia o lugar)
    const ativo = document.activeElement instanceof HTMLElement && area.contains(document.activeElement) ? document.activeElement.id : "";
    trocar(area, resultado(estado, r, () => mudou()));
    if (ativo) document.getElementById(ativo)?.focus({ preventScroll: true });
    const sem = r.criancas - r.com_destino;
    status.textContent = r.fechadas.length
      ? `Plano: ${plural(r.fechadas.length, "escola", "escolas")}, ${criancas(r.criancas)}` + (sem ? `, ${mil(sem)} sem destino calculado.` : ".")
      : "Plano vazio.";
    rodapeLink.textContent = ` Este plano no site: ${urlAtual().replace(/^https?:\/\//, "")}`;
    trocar(compartilhar, h("button", { type: "button", class: "botao", onclick: () => window.print() }, "Imprimir o diagnóstico do plano"),
      botaoCompartilhar(`E se estas escolas fecharem? ${lugarTexto(mun)}`, urlAtual()));
  };
  // veio da ficha (ou de link com código de outro município): o link passa a ter o município e só o que vale
  if (lugarTexto_ === null || estado.fechar.size !== cenario.fechar.length) history.replaceState(null, "", link(estado));
  document.title = `E se estas escolas fecharem? ${lugarTexto(mun)}: Escola em Pauta`;
  trocar(main, h("div", { class: "simulador" },
    h("header", null,
      h("a", { class: "voltar nao-imprime", href: "#/simular" }, "Outro município"),
      h("h1", null, "E se estas escolas fecharem?"),
      h("p", { class: "ficha-onde" }, lugarTexto(mun)),
      h("p", { class: "legenda" }, "Simulação de um plano de fechamento: não é previsão. Mostra para onde iria cada etapa, pela regra " +
        "descrita no fim da página, e quanta estrada no mínimo.")),
    mun.escolas.length ? montagem(estado, () => mudou()) : h("p", null, "Este município não tem escola do campo no índice."),
    status,
    area,
    compartilhar,
    h("p", { class: "fonte" }, `Fonte: ${v.fonte} (dados baixados em ${data(v.data_verificacao)}). Estradas: © colaboradores do ` +
      "OpenStreetMap (ODbL). ", RODAPE, rodapeLink)));
  mudou(true);
  const ignoradas = cenario.fechar.filter((c) => !doMunicipio.has(c));
  if (ignoradas.length) {
    area.prepend(h("p", { class: "aviso", role: "note" }, `${plural(ignoradas.length, "código ficou", "códigos ficaram")} fora do plano ` +
      `por não ${ignoradas.length === 1 ? "ser escola" : "serem escolas"} do campo de ${mun.municipio} no índice: ${ignoradas.join(", ")}.`));
  }
}
