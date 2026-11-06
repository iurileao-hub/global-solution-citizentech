/**
 * A ficha da escola: a versão de tela da folha impressa do protótipo (src/escola_em_pauta/ficha.py), para
 * QUALQUER uma das 53.759 escolas do campo, com o que o índice nacional traz. Frente: quem estuda, para onde as
 * crianças iriam e quanta estrada, o que a lei pede. Verso (na impressão, segunda página): o que a ficha não mede,
 * para a comunidade escrever na assembleia.
 *
 * Regras de texto (as mesmas do protótipo): o número é sempre PISO ("pelo menos"); nada de "deve" ou "não deve"
 * fechar; sem número quando não há base.
 */

import { base, escola as baixarEscola, tracados, versao } from "../dados";
import { h, trocar } from "../dom";
import { vivo } from "../estado";
import {
  ETAPA_ANOS, ETAPA_ROTULO, faixaEtapas, horas, km, listaPt, mil, nomeLegivel, ordenarEtapas, UF_NOME,
} from "../formato";
import { ligacoesDaEscola } from "../nucleo/nucleo";
import {
  data, type Escola, NAO_CALCULADA, ONDE, type Receptora, recebeTodas, RODAPE, SEM_COORDENADA, textoEscola,
} from "../nucleo/respostas";
import { botaoCompartilhar, botaoCopiar, caixaBusca, carregando } from "./componentes";
import { caminhos } from "./resposta";
import { LETRAS, prancha } from "./prancha";

const MARGEM_TEXTO = "Por enquanto há uma única referência externa (Muniz Freire, ES). Para a escola receptora indicada " +
  "pela prefeitura, a área técnica do Tribunal de Contas estimou até 52 km por dia, pensando em quem mora mais longe; " +
  "o cálculo de escola a escola dá 25 km. O caminho real de parte das crianças pode passar do dobro do piso.";

/** A receptora da frase de abertura: a mais próxima que recebe TODAS as etapas; senão, a mais próxima. */
export function principal(e: Escola): Receptora | null {
  const rs = e.rota?.receptoras ?? [];
  const todas = rs.filter((r) => recebeTodas(r, e));
  const lista = todas.length ? todas : rs;
  return lista.length ? lista.reduce((a, b) => (b.km < a.km ? b : a)) : null;
}

function quem(e: Escola): string {
  const etapas = Object.keys(e.e);
  return etapas.some((x) => x === "anos_finais" || x === "medio") ? "crianças e adolescentes" : "crianças";
}

function manchete(e: Escola): HTMLElement {
  const etapas = ordenarEtapas(Object.keys(e.e));
  const p = principal(e);
  const partes: (string | HTMLElement)[] = [];
  if (etapas.length) partes.push("Aqui estudam ", h("b", null, `${mil(e.t)} ${quem(e)}`), `, ${faixaEtapas(etapas)}. `);
  else partes.push("No Censo mais recente, esta escola não tinha matrícula. ");
  if (e.tp) partes.push(h("b", null, `${mil(e.tp)} ${e.tp === 1 ? "chega" : "chegam"} de transporte escolar público.`), " ");
  if (p) {
    const todas = recebeTodas(p, e);
    partes.push(`Se a escola fechar, a mais perto que oferece ${todas ? "as mesmas etapas" : "parte das etapas"} fica a ` +
      `pelo menos ${km(p.km / 2)} km por estrada: `,
    h("b", { class: "piso" }, `pelo menos ${km(p.km)} km por dia`), ", ida e volta",
    p.min ? `, cerca de ${horas(p.min)} de ônibus` : "", ".");
  }
  return h("p", { class: "manchete" }, partes);
}

function semNumero(e: Escola): HTMLElement | null {
  const rota = e.rota;
  if (rota && rota.receptoras && rota.receptoras.length) return null;
  const texto = rota
    ? (rota.aviso || "Nenhuma rota por estrada foi calculada para esta escola.") + " Não vou estimar um número sem base."
    : !e.geo ? SEM_COORDENADA : NAO_CALCULADA;
  return h("div", { class: "sem-numero", role: "note" }, h("p", { style: "margin:0" }, texto),
    !rota && !e.geo ? h("p", { style: "margin:.6rem 0 0" }, h("a", { href: "#/orientacao/C1" },
      "Como pedir informação pela Lei de Acesso à Informação")) : null);
}

function selos(e: Escola): HTMLElement {
  return h("ul", { class: "selos", "aria-label": "Características" },
    h("li", null, `Rede ${e.r ?? "pública"}`),
    h("li", null, e.z === "rural" ? "Zona rural" : "Zona urbana, alunos do campo"),
    e.d ? h("li", null, (ONDE[e.d] ?? e.d).replace(/^em /, "Em ")) : null,
    h("li", null, `Código INEP ${e.c}`));
}

function receptoraItem(r: Receptora, e: Escola, i: number, p: Receptora | null, maior: number): HTMLElement {
  const onde = [r.rural ? "rural" : "urbana"];
  if (r.m || r.uf) onde.push(`em ${r.m || e.m}${r.uf && r.uf !== e.uf ? "/" + r.uf : ""}`);
  const chao = Math.min(r.chao ?? 0, r.km);
  const etapas = r.etapas && r.etapas.length
    ? recebeTodas(r, e)
      ? h("span", { class: "rec-todas" }, "recebe todas as etapas desta escola")
      : "recebe só " + listaPt(ordenarEtapas(r.etapas).map((x) => ETAPA_ROTULO[x] ?? x))
    : null;
  return h("li", { class: r === p ? "rec-principal" : null },
    h("span", { class: "rec-letra", "aria-hidden": "true" }, LETRAS[i]),
    h("span", { class: "rec-nome" }, h("span", { class: "sr" }, `${LETRAS[i]}. `), nomeLegivel(r.n)),
    h("span", { class: "rec-km" }, `${km(r.km)} km`, h("small", null, "por dia, pelo menos")),
    h("span", { class: "rec-info" }, onde.join(", "),
      r.min !== undefined && r.min !== null ? `; ${horas(r.min)} de ônibus por dia` : "",
      chao >= 0.5 ? `; ${km(chao)} km de estrada de chão` : "", etapas ? "; " : "", etapas),
    // barra na escala da mais longe da lista: dá para comparar as distâncias de relance
    h("span", { class: "rec-barra", "aria-hidden": "true" },
      h("span", { class: "pav", style: `width:${(100 * (r.km - chao)) / maior}%` }),
      h("span", { class: "chao", style: `width:${(100 * chao) / maior}%` })));
}

function receptoras(e: Escola, p: Receptora | null): HTMLElement | null {
  const rota = e.rota;
  if (!rota || !rota.receptoras || !rota.receptoras.length) return null;
  const rs = rota.receptoras;
  const rurais = rs.filter((r) => r.rural).length;
  const quando = rota.osm ? `, dados de ${data(rota.osm)}` : "";
  return h("section", { class: "s-receptoras" },
    h("h2", null, "Para onde as crianças iriam, e quanta estrada a mais"),
    h("p", null, "Medimos a estrada de escola a escola, ida e volta, por dia. ", h("b", null, "É o mínimo."),
      " O ônibus real passa de casa em casa, por isso o caminho de verdade é maior. ",
      `Das ${rs.length} escolas mais próximas que oferecem alguma das mesmas etapas, `,
      rurais === 0 ? "nenhuma é rural." : `${rurais} ${rurais === 1 ? "é rural" : "são rurais"}.`),
    h("ol", { class: "receptoras", "aria-label": "Escolas que poderiam receber os alunos, da mais perto à mais longe" },
      rs.map((r, i) => receptoraItem(r, e, i, p, Math.max(...rs.map((x) => x.km))))),
    p ? h("p", { class: "legenda nao-imprime" }, `A faixa amarela marca a escola da frase de abertura: a mais perto que ` +
      `${recebeTodas(p, e) ? "recebe todas as etapas desta escola" : "recebe parte das etapas (nenhuma das listadas recebe todas)"}.`) : null,
    rota.sem_rota ? h("p", null, `Outras ${rota.sem_rota} escola(s) próxima(s) ficaram sem rota na malha viária e não entram na lista.`) : null,
    h("p", { class: "legenda" }, `Conta feita pela malha do OpenStreetMap${quando}, com velocidade de ônibus escolar. ` +
      "A casa de cada criança, as paradas do ônibus e a estrada na chuva deixam o trajeto real maior. " + MARGEM_TEXTO),
    h("p", { class: "legenda" }, "Vagas em cada escola: a calcular (o número de vagas não é publicado)."));
}

function quemEstuda(e: Escola): HTMLElement {
  const etapas = ordenarEtapas(Object.keys(e.e));
  const maior = Math.max(1, ...Object.values(e.e));
  const zr = e.zr ?? null;
  return h("section", { class: "s-quem" },
    h("h2", null, "Quem estuda aqui"),
    etapas.length ? h("div", { class: "etapas", role: "list" }, etapas.map((x) => [
      h("span", { role: "listitem" }, ETAPA_ROTULO[x].charAt(0).toUpperCase() + ETAPA_ROTULO[x].slice(1),
        ETAPA_ANOS[x] ? h("span", { class: "legenda", style: "font-size:.85rem" }, ` (${ETAPA_ANOS[x]})`) : null),
      h("span", { class: "barra", style: `width:${(100 * e.e[x]) / maior}%`, "aria-hidden": "true" }),
      h("span", { class: "v" }, mil(e.e[x]))])) : h("p", null, "Sem matrícula informada no Censo."),
    zr !== null && e.t ? h("p", null, zr === e.t ? h("b", null, `Todas as ${mil(e.t)}`) : h("b", null, `${mil(zr)} de ${mil(e.t)}`),
      " moram na zona rural.", e.tp ? [" ", h("b", null, mil(e.tp)), " usam transporte escolar público."] : null) : null);
}

function serie(e: Escola): HTMLElement | null {
  const anos = Object.keys(e.s).sort();
  if (anos.length < 2) return null;
  const maior = Math.max(1, ...anos.map((a) => e.s[a]));
  const [a0, a1] = [anos[0], anos[anos.length - 1]];
  return h("section", { class: "s-serie" },
    h("h2", null, "A matrícula ao longo dos anos"),
    h("p", null, `De ${a0} a ${a1}, a matrícula foi de ${mil(e.s[a0])} para ${mil(e.s[a1])} alunos.`),
    h("figure", { style: "margin:0" },
      h("div", { class: "serie", role: "img", "aria-label": anos.map((a) => `${a}: ${e.s[a]}`).join("; ") },
        anos.map((a) => h("div", { class: "barra", style: `height:${(100 * e.s[a]) / maior}%;background:var(--mata)`, title: `${a}: ${e.s[a]}` }))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, anos.map((a) => h("span", null, `${a.slice(2)}`))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, anos.map((a) => h("span", null, `${e.s[a]}`))),
      h("figcaption", null, "Alunos matriculados por ano, Censo Escolar. Não projetamos o futuro: num teste com quase 2 mil " +
        "escolas rurais, projetar pela tendência errou mais do que supor que a matrícula se repete.")));
}

type Situacao = "pronto" | "preencher" | "calcular";
const SIMBOLO: Record<Situacao, string> = { pronto: "■", preencher: "□", calcular: "◇" };
const NOME_SITUACAO: Record<Situacao, string> = { pronto: "Pronto", preencher: "A preencher", calcular: "A calcular" };
const LDB = "LDB, art. 28, parágrafo único";
const PL = "PL 3.091/2024, em tramitação";
const CME = "CME Santa Cruz do Sul (RS), Res. 03/2016, modelo local";

/** O que a lei pede e o que a ficha já cobre (src/escola_em_pauta/checklist.py, com os dados do índice). */
function lei(e: Escola): HTMLElement {
  const comRota = Boolean(e.rota?.receptoras?.length);
  const rural = e.z === "rural";
  const dif = e.d === "indígena" || e.d === "quilombola";
  const fracaoRural = e.t && e.zr ? e.zr / e.t : 0;
  const campo = rural || dif || fracaoRural > 0.5;
  const motivo = rural ? "escola em área rural" : dif ? `escola ${ONDE[e.d!]}`
    : `escola urbana, mas ${Math.round(fracaoRural * 100)}% dos alunos moram na zona rural (indício de que atende ` +
      "predominantemente a populações do campo)";
  const criancas = (e.e["pre_escola"] ?? 0) + (e.e["anos_iniciais"] ?? 0);
  const rurais = (e.rota?.receptoras ?? []).filter((r) => r.rural && (r.etapas ?? []).some((x) => x === "pre_escola" || x === "anos_iniciais"));
  const maisPerto = rurais.length ? rurais.reduce((a, b) => (b.km < a.km ? b : a)) : null;
  const anos = Object.keys(e.s).sort();
  const itens: [string, string, Situacao, string][] = [
    ["A lei de fechamento se aplica a esta escola", "Decreto 7.352/2010, art. 1º", "pronto",
      (campo ? "Sim: " : "Não pelos dados do Censo: ") + (campo ? motivo : "escola urbana com maioria de alunos da zona urbana")],
    ["Justificativa da Secretaria de Educação", LDB, "preencher", "pela Secretaria"],
    ["Diagnóstico do impacto", LDB, "pronto", "esta ficha é um começo: os números com base pública"],
    ["Manifestação da comunidade escolar", LDB, "preencher", "na assembleia (verso da ficha impressa)"],
    ["Manifestação do Conselho de Educação", LDB, "preencher", "pelo Conselho"],
    ["Distância a ser percorrida pelos alunos realocados", PL, comRota ? "pronto" : "calcular",
      comRota ? "nesta ficha, como piso" : "sem rota calculada pela malha viária pública"],
    ["Função social da escola", PL, "preencher", "na assembleia"],
    ["Percurso educativo: onde cada aluno continua, em que etapa, com vaga", PL, "calcular",
      "as etapas de cada escola estão na lista; a vaga real não é publicada"],
    ["Matrícula dos últimos cinco anos", CME, anos.length >= 5 ? "pronto" : "calcular",
      anos.length ? `de ${anos[0]} a ${anos[anos.length - 1]}, nesta ficha` : "sem série no Censo"],
    ["Mapa de distâncias até as escolas receptoras", CME, comRota ? "pronto" : "calcular",
      comRota ? "a prancha desta ficha" : "sem rota calculada"],
    ["Ata da assembleia por segmento", CME, "preencher", "anexar à ficha"],
    ["Pré-escola e anos iniciais na própria comunidade", "Res. CNE/CEB 2/2008, art. 3º", "pronto",
      !criancas ? "a escola não tem essas etapas"
        : `${mil(criancas)} das ${mil(e.t)} crianças estão nessas etapas; ` + (maisPerto
          ? `a escola rural mais próxima com essas etapas é ${nomeLegivel(maisPerto.n)} (${km(maisPerto.km / 2)} km por estrada)`
          : "nenhuma das escolas próximas com essas etapas é rural")],
  ];
  return h("section", { class: "s-lei" },
    h("h2", null, "O que a lei pede e o que já está pronto"),
    h("p", { class: "convencoes-lei" }, "■ pronto: está nesta ficha. □ a preencher: depende de pessoas. ◇ a calcular: " +
      "depende de dado que não é público."),
    h("ul", { class: "lei" }, itens.map(([item, norma, sit, detalhe]) => h("li", null,
      h("span", { class: `marca-lei ${sit}`, "aria-label": NOME_SITUACAO[sit] }, SIMBOLO[sit]),
      h("span", null, h("b", null, item), `: ${detalhe}.`, h("span", { class: "norma" }, norma))))),
    h("p", null, h("a", { href: "#/orientacao/D1" }, "O que a lei exige antes de fechar uma escola do campo"), "."));
}

const PERGUNTAS_VERSO = [
  "O que acontece nesta escola além da aula?",
  "Quem usa a escola além dos alunos?",
  "Como fica a estrada quando chove?",
  "Quem mora mais longe, e quanto tempo já leva hoje?",
  "O que a comunidade perderia?",
  "O que poderia melhorar com a mudança?",
  "O que mais o Conselho precisa saber antes de decidir?",
];

function verso(e: Escola): HTMLElement {
  return h("section", { class: "verso" },
    h("p", { class: "so-impressao" }, h("b", null, nomeLegivel(e.n)), `, ${e.m}/${e.uf}. Verso da ficha: a parte que a comunidade escreve.`),
    h("h2", null, "O que esta ficha não mede"),
    h("p", null, "Os números não dizem o que esta escola é para a comunidade. A lei pede a manifestação da comunidade, e ",
      h("b", null, "esta parte vale tanto quanto os números"), ". Na ficha impressa, estas perguntas ficam com espaço para " +
      "escrever na assembleia; a folha vai ao Conselho com a ata."),
    h("ul", { class: "verso-perguntas" }, PERGUNTAS_VERSO.map((p) => h("li", null, p))),
    h("p", { class: "so-impressao" }, "Assembleia realizada em ____/____/________. Quem escreveu: ______________________. " +
      "Pessoas presentes, por grupo (pais, professores, alunos, funcionários): ______________________________."));
}

export async function telaFicha(main: HTMLElement, g: number, codigo: number, mais: string[]): Promise<void> {
  trocar(main, carregando("Abrindo a ficha da escola..."));
  if (!Number.isInteger(codigo) || codigo <= 0) {
    trocar(main, h("p", { class: "erro" }, "Código de escola inválido. ", h("a", { href: "#/" }, "Buscar uma escola"), "."));
    return;
  }
  const [b, e, v] = await Promise.all([base(), baixarEscola(codigo), versao()]);
  if (!vivo(g)) return;
  if (!e) {
    trocar(main, h("article", { class: "verbete" }, h("h1", null, `Não há escola do campo com o código ${codigo}`),
      h("p", null, "A base tem as escolas públicas do campo em atividade no Censo Escolar 2025. Escolas urbanas não aparecem."),
      caixaBusca({ titulo: false })));
    return;
  }
  const nome = nomeLegivel(e.n);
  document.title = `${nome}, ${e.m}/${e.uf}: Escola em Pauta`;
  const p = principal(e);
  const rs = e.rota?.receptoras ?? [];
  const lado = h("aside", { class: "ficha-lado", "aria-label": "Mapa" });
  const extras = mais.filter((x) => b.registros.has(x) && !ligacoesDaEscola(b, e).includes(x));
  const urlPrevia = new URL(`escola/${e.c}.html`, document.baseURI).href;
  const lugar = e.uf === "DF" ? "Distrito Federal" : `${e.m}, ${UF_NOME[e.uf] ?? e.uf}`;
  trocar(main, h("div", { class: "ficha" },
    h("header", { class: "ficha-cabeca" },
      h("a", { class: "voltar nao-imprime", href: "#/" }, "Buscar outra escola"),
      h("h1", null, nome),
      h("p", { class: "ficha-onde" }, lugar),
      selos(e),
      manchete(e),
      // o aviso (transporte por rio, por exemplo) fica colado no número que ele qualifica
      rs.length && e.rota?.aviso ? h("p", { class: "aviso", role: "note" }, h("strong", null, "Atenção: "), e.rota.aviso) : null,
      semNumero(e)),
    rs.length ? lado : null,
    receptoras(e, p),
    quemEstuda(e),
    serie(e),
    lei(e),
    verso(e),
    h("section", { class: "nao-imprime" },
      caminhos(b, "Para continuar", ligacoesDaEscola(b, e)),
      caminhos(b, "Talvez também interesse", extras),
      h("div", { class: "acoes" },
        h("button", { type: "button", class: "botao", onclick: () => window.print() }, "Imprimir para a assembleia"),
        botaoCopiar("Copiar o texto da ficha", () => textoEscola(b, e, v.fonte, v.data_verificacao, extras)),
        botaoCompartilhar(`${nome}, ${e.m}/${e.uf}`, urlPrevia))),
    h("p", { class: "fonte s-fonte" }, `Fonte: ${v.fonte} (dados baixados em ${data(v.data_verificacao)}). Estradas: © colaboradores ` +
      "do OpenStreetMap (ODbL). ", RODAPE)));
  if (rs.length) {
    const t = await tracados(codigo);
    if (!vivo(g)) return;
    trocar(lado, prancha(e, rs, t, p));
  }
}
