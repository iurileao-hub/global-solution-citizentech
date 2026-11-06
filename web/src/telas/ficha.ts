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
  avisoRota, data, type Escola, NAO_CALCULADA, ONDE, type Receptora, recebeTodas, RODAPE, SEM_COORDENADA, textoEscola,
} from "../nucleo/respostas";
import { botaoCompartilhar, botaoCopiar, caixaBusca, carregando } from "./componentes";
import { caminhos } from "./resposta";
import { LETRAS, prancha } from "./prancha";

const DURVAL = 32049501;

/** A única referência externa até agora é de OUTRA escola (a Durval Máximo): fora da ficha dela, o texto diz isso,
 * senão o "24 km" pareceria o número da escola aberta. */
function margem(e: Escola): string {
  return e.c === DURVAL
    ? "Nesta escola há uma referência externa: para a escola indicada pela prefeitura (EEEFM Arquimimo Mattos), a área " +
      "técnica do Tribunal de Contas do ES estimou até 52 km por dia, pensando em quem mora mais longe; o cálculo de escola " +
      "a escola dá pelo menos 24 km. O caminho real de parte das crianças pode passar do dobro do piso."
    : "Para dar a medida do piso: na única escola com estimativa oficial até agora, a EMEF Durval Máximo (Muniz Freire, " +
      "ES), a área técnica do Tribunal de Contas estimou até 52 km por dia até a escola indicada pela prefeitura, e o " +
      "cálculo de escola a escola deu pelo menos 24 km. O caminho real de parte das crianças pode passar do dobro do piso.";
}

/** "1 criança", "2 crianças": o número decide o plural. */
const n = (q: number, um: string, varios: string) => `${mil(q)} ${q === 1 ? um : varios}`;

/** Metade da distância por dia mostrada, para a ida: 29 km por dia dá 14,5 km na ida (e não 15, que somaria 30). */
function ida(xDia: number): string {
  const dia = xDia >= 10 ? Math.floor(xDia + 1e-9) : Math.floor(xDia * 10 + 1e-9) / 10;
  return (dia / 2).toLocaleString("pt-BR", { maximumFractionDigits: 2 });
}

/** A receptora da frase de abertura: a mais próxima que recebe TODAS as etapas; senão, a mais próxima. */
export function principal(e: Escola): Receptora | null {
  const rs = e.rota?.receptoras ?? [];
  const todas = rs.filter((r) => recebeTodas(r, e));
  const lista = todas.length ? todas : rs;
  return lista.length ? lista.reduce((a, b) => (b.km < a.km ? b : a)) : null;
}

/** Abaixo de 1 km por dia, ida e volta, é a mesma coordenada (escolas que dividem prédio ou endereço no Catálogo
 * do INEP): dizer "0,1 km, 1 min de ônibus" seria precisão falsa. */
export const MESMO_LUGAR_KM = 1;

export function kmDia(x: number): string {
  return x < MESMO_LUGAR_KM ? "menos de 1 km" : `${km(x)} km`;
}

export function lugarDe(e: Escola): string {
  if (!e.m || !e.uf) return "Município não informado no Censo";
  return e.uf === "DF" ? "Distrito Federal" : `${e.m}, ${UF_NOME[e.uf] ?? e.uf}`;
}

function quem(e: Escola): string {
  const etapas = Object.keys(e.e);
  const adol = etapas.some((x) => x === "anos_finais" || x === "medio");
  if (e.t === 1) return adol ? "estudante" : "criança";
  return adol ? "crianças e adolescentes" : "crianças";
}

function manchete(e: Escola): HTMLElement {
  const etapas = ordenarEtapas(Object.keys(e.e));
  const p = principal(e);
  const partes: (string | HTMLElement)[] = [];
  if (etapas.length) partes.push(e.t === 1 ? "Aqui estuda " : "Aqui estudam ", h("b", null, `${mil(e.t)} ${quem(e)}`), `, ${faixaEtapas(etapas)}. `);
  else if (e.t) {
    partes.push(e.t === 1 ? "Aqui estuda " : "Aqui estudam ", h("b", null, n(e.t, "aluno", "alunos")),
      ", fora das etapas da creche ao ensino médio regular (podem ser de EJA ou de educação profissional). ");
  } else partes.push("No Censo mais recente, esta escola não tinha matrícula. ");
  if (e.tp) partes.push(h("b", null, `${mil(e.tp)} ${e.tp === 1 ? "chega" : "chegam"} de transporte escolar público.`), " ");
  if (p && p.km < MESMO_LUGAR_KM) {
    const todas = recebeTodas(p, e);
    partes.push(`Se a escola fechar, a mais perto que oferece ${todas ? "as mesmas etapas" : "parte das etapas"} fica ` +
      "no mesmo lugar ou quase: ", h("b", { class: "piso" }, "menos de 1 km por dia"), " pela localização pública. " +
      "Confira se é o mesmo prédio: escolas que dividem o endereço aparecem com a mesma coordenada.");
  } else if (p) {
    const todas = recebeTodas(p, e);
    partes.push(`Se a escola fechar, a mais perto que oferece ${todas ? "as mesmas etapas" : "parte das etapas"} fica a `,
      h("b", { class: "piso" }, `pelo menos ${km(p.km)} km por dia`), ` de estrada, ida e volta (${ida(p.km)} km na ida)`,
      p.min ? `: cerca de ${horas(p.min)} de ônibus por dia` : "", ".");
  }
  return h("p", { class: "manchete" }, partes);
}

function semNumero(e: Escola): HTMLElement | null {
  const rota = e.rota;
  if (rota && rota.receptoras && rota.receptoras.length) return null;
  const texto = rota
    ? (avisoRota(rota, e) || "Nenhuma rota por estrada foi calculada para esta escola.") + " Não vou estimar um número sem base."
    : !e.geo ? SEM_COORDENADA : NAO_CALCULADA;
  return h("div", { class: "sem-numero", role: "note" }, h("p", { style: "margin:0" }, texto),
    !rota && !e.geo ? h("p", { style: "margin:.6rem 0 0" }, h("a", { href: "#/orientacao/C1" },
      "Como pedir informação pela Lei de Acesso à Informação"),
    // no papel o link não leva a lugar nenhum: a ficha impressa diz onde achar
    h("span", { class: "so-impressao" }, " (no site do Escola em Pauta, pergunte \"como pedir os números à prefeitura\")")) : null);
}

function selos(e: Escola): HTMLElement {
  return h("ul", { class: "selos", "aria-label": "Características" },
    h("li", null, `Rede ${e.r ?? "pública"}`),
    h("li", null, e.z === "rural" ? "Zona rural" : "Zona urbana, alunos do campo"),
    e.d ? h("li", null, (ONDE[e.d] ?? e.d).replace(/^em /, "Em ")) : null,
    h("li", { title: "O número da escola no Censo Escolar do INEP, o instituto do MEC que faz o Censo" }, `Código INEP ${e.c}`));
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
    h("span", { class: "rec-km" }, kmDia(r.km), h("small", null, r.km < MESMO_LUGAR_KM ? "mesma coordenada" : "por dia, pelo menos")),
    h("span", { class: "rec-info" }, onde.join(", "),
      r.min !== undefined && r.min !== null && r.km >= MESMO_LUGAR_KM ? `; ${horas(r.min)} de ônibus por dia` : "",
      chao >= 0.5 ? `; ${km(chao)} km de estrada de chão` : "", etapas ? "; " : "", etapas),
    // barra na escala da mais longe da lista: dá para comparar as distâncias de relance
    h("span", { class: "rec-barra", "aria-hidden": "true" },
      h("span", { class: "pav", style: `width:${(100 * Math.max(0, r.km - chao)) / Math.max(maior, MESMO_LUGAR_KM)}%` }),
      h("span", { class: "chao", style: `width:${(100 * chao) / Math.max(maior, MESMO_LUGAR_KM)}%` })));
}

/** Quantas das escolas listadas são rurais. A 5ª da lista, quando existe, não é a 5ª mais próxima: é a mais próxima
 * que recebe todas as etapas, acrescentada porque nenhuma das 4 recebe. */
function ruraisTexto(rs: Receptora[]): string {
  const quinta = rs.length > 4 ? rs[4] : null;
  const perto = quinta ? rs.slice(0, 4) : rs;
  const rurais = perto.filter((r) => r.rural).length;
  const conta = perto.length === 1
    ? `A escola mais próxima que oferece alguma das mesmas etapas é ${perto[0].rural ? "rural" : "urbana"}.`
    : `Das ${perto.length} escolas mais próximas que oferecem alguma das mesmas etapas, ` +
      (rurais === 0 ? "nenhuma é rural." : rurais === perto.length ? "todas são rurais." : `${rurais} ${rurais === 1 ? "é rural" : "são rurais"}.`);
  return quinta ? conta + ` Nenhuma delas recebe todas as etapas desta escola; a 5ª da lista, ${quinta.rural ? "rural" : "urbana"}, é ` +
    "a mais próxima que recebe." : conta;
}

function receptoras(e: Escola, p: Receptora | null): HTMLElement | null {
  const rota = e.rota;
  if (!rota || !rota.receptoras || !rota.receptoras.length) return null;
  const rs = rota.receptoras;
  const quando = rota.osm ? `, dados de ${data(rota.osm)}` : "";
  return h("section", { class: "s-receptoras" },
    h("h2", null, "Para onde as crianças iriam, e quanta estrada a mais"),
    h("p", null, "Medimos a estrada de escola a escola, ida e volta, por dia. ", h("b", null, "É o mínimo."),
      " O ônibus real passa de casa em casa, por isso o caminho de verdade é maior. ", ruraisTexto(rs)),
    h("ol", { class: "receptoras", "aria-label": "Escolas que poderiam receber os alunos, da mais perto à mais longe" },
      rs.map((r, i) => receptoraItem(r, e, i, p, Math.max(...rs.map((x) => x.km))))),
    p ? h("p", { class: "legenda nao-imprime" }, `A faixa amarela marca a escola da frase de abertura: a mais perto que ` +
      `${recebeTodas(p, e) ? "recebe todas as etapas desta escola" : "recebe parte das etapas (nenhuma das listadas recebe todas)"}.`) : null,
    rota.sem_rota ? h("p", null, `Outras ${rota.sem_rota} escola(s) próxima(s) ficaram sem rota na malha viária e não entram na lista.`) : null,
    h("p", { class: "legenda" }, `Conta feita pela malha do OpenStreetMap${quando}, com velocidade de ônibus escolar. ` +
      "A casa de cada criança, as paradas do ônibus e a estrada na chuva deixam o trajeto real maior. " + margem(e)),
    h("p", { class: "legenda" }, "Vagas em cada escola: a calcular (o número de vagas não é publicado)."),
    h("p", { class: "sim-chamada nao-imprime" }, h("a", { href: `#/simular?f=${e.c}` }, "E se outras escolas do município também fecharem?"),
      " Fechamento costuma vir em plano, e a escola indicada aqui pode fechar também: simule o plano."));
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
      h("span", { class: "v" }, mil(e.e[x]))]))
      : h("p", null, e.t ? `${e.t === 1 ? "O aluno está" : `Os ${mil(e.t)} alunos estão`} fora das etapas da creche ao ensino ` +
        "médio regular (podem ser de EJA ou de educação profissional)." : "Sem matrícula informada no Censo."),
    zr !== null && e.t ? h("p", null,
      e.t === 1 ? (zr ? h("b", null, "O único aluno mora") : h("b", null, "O único aluno não mora")) : zr === e.t
        ? h("b", null, `Todos os ${mil(e.t)}`) : h("b", null, `${mil(zr)} de ${mil(e.t)}`),
      e.t === 1 ? " na zona rural." : zr === 1 && zr !== e.t ? " mora na zona rural." : " moram na zona rural.",
      e.tp ? [" ", h("b", null, mil(e.tp)), e.tp === 1 ? " usa transporte escolar público." : " usam transporte escolar público."] : null) : null);
}

/** A maior variação de um ano para o seguinte, quando passa da metade: pode ser mudança real (turmas transferidas)
 * ou correção de registro, e quem lê na reunião precisa saber que vale perguntar. */
function saltoTexto(e: Escola, anos: string[]): HTMLElement | null {
  let maior: [string, string, number] | null = null;
  for (let i = 1; i < anos.length; i++) {
    const [a, b] = [e.s[anos[i - 1]], e.s[anos[i]]];
    if (Math.max(a, b) < 10) continue;
    const v = Math.abs(b - a) / Math.max(a, 1);
    if (v > 0.5 && (!maior || v > maior[2])) maior = [anos[i - 1], anos[i], v];
  }
  if (!maior) return null;
  const [a, b] = [e.s[maior[0]], e.s[maior[1]]];
  return h("p", { class: "aviso" }, `Entre ${maior[0]} e ${maior[1]} a matrícula ${b < a ? "caiu" : "subiu"} de ${mil(a)} para ` +
    `${mil(b)}. Uma mudança grande assim pode ser real (turmas transferidas, por exemplo) ou correção do registro no Censo: ` +
    "a Secretaria de Educação sabe dizer.");
}

function serie(e: Escola): HTMLElement | null {
  const anos = Object.keys(e.s).sort();
  if (anos.length < 2) return null;
  const maior = Math.max(1, ...anos.map((a) => e.s[a]));
  const [a0, a1] = [anos[0], anos[anos.length - 1]];
  return h("section", { class: "s-serie" },
    h("h2", null, "A matrícula ao longo dos anos"),
    h("p", null, `De ${a0} a ${a1}, a matrícula foi de ${mil(e.s[a0])} para ${n(e.s[a1], "aluno", "alunos")}.`),
    saltoTexto(e, anos),
    h("figure", { style: "margin:0" },
      h("div", { class: "serie", role: "img", "aria-label": anos.map((a) => `${a}: ${e.s[a]}`).join("; ") },
        anos.map((a) => h("div", { class: "barra", style: `height:${(100 * e.s[a]) / maior}%;background:var(--mata)`, title: `${a}: ${e.s[a]}` }))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, anos.map((a) => h("span", null, `${a.slice(2)}`))),
      h("div", { class: "serie-anos", "aria-hidden": "true" }, anos.map((a) => h("span", null, mil(e.s[a])))),
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
    ["Diagnóstico do impacto", LDB, "preencher", "pela Secretaria; esta ficha reúne os números públicos que ele pode usar"],
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
      comRota ? "o mapa desta ficha" : "sem rota calculada"],
    ["Ata da assembleia por segmento", CME, "preencher", "anexar à ficha"],
    ["Pré-escola e anos iniciais na própria comunidade", "Res. CNE/CEB 2/2008, art. 3º", !criancas || comRota ? "pronto" : "calcular",
      !criancas ? "a escola não tem essas etapas"
        : `${n(criancas, "aluno está", "alunos estão")} nessas etapas; ` + (!comRota
          ? "sem rota calculada, não dá para dizer onde fica a escola rural mais próxima com essas etapas"
          : maisPerto
            ? `a escola rural mais próxima com essas etapas é ${nomeLegivel(maisPerto.n)} (pelo menos ${km(maisPerto.km)} km por dia, ida e volta)`
            : "nenhuma das escolas próximas com rota que têm essas etapas é rural")],
    ...(dif ? [["Consulta prévia, livre e informada à comunidade", "Convenção 169 da OIT, art. 6º (Decreto 10.088/2019)",
      "preencher", `a escola fica ${ONDE[e.d!]}: o governo deve consultar a comunidade, pelas instituições dela, antes de ` +
      "decidir"] as [string, string, Situacao, string]] : []),
  ];
  return h("section", { class: "s-lei" },
    h("h2", null, "O que a lei pede e o que já está pronto"),
    h("p", { class: "convencoes-lei" }, "■ pronto: está nesta ficha. □ a preencher: depende de pessoas. ◇ a calcular: " +
      "depende de dado que não é público."),
    h("ul", { class: "lei" }, itens.map(([item, norma, sit, detalhe]) => h("li", null,
      h("span", { class: `marca-lei ${sit}`, "aria-label": NOME_SITUACAO[sit] }, SIMBOLO[sit]),
      h("span", null, h("b", null, item), `: ${detalhe}.`, h("span", { class: "norma" }, norma))))),
    h("p", null, h("a", { href: "#/orientacao/D1" }, "O que a lei exige antes de fechar uma escola do campo"),
      dif ? [" · ", h("a", { href: `#/orientacao/${e.d === "indígena" ? "D8" : "D5"}` },
        `As regras próprias das escolas ${e.d === "indígena" ? "indígenas" : "quilombolas"}`)] : null,
      " · ", h("a", { href: "#/sobre/palavras" }, "O que querem dizer LDB, PL, INEP e as outras siglas"), "."));
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
  const intro = h("p", null, "Os números não dizem o que esta escola é para a comunidade. A lei pede a manifestação da comunidade, e ",
    h("b", null, "esta parte vale tanto quanto os números"), ". Na ficha impressa, estas perguntas ficam com espaço para " +
    "escrever na assembleia; a folha vai ao Conselho com a ata.");
  return h("section", { class: "verso" },
    h("p", { class: "so-impressao" }, h("b", null, nomeLegivel(e.n)), `, ${lugarDe(e)}. Verso da ficha: a parte que a comunidade escreve.`),
    // na tela, recolhido (a ficha já é longa no celular); no papel, aberto e com linhas para escrever
    h("details", { class: "nao-imprime verso-tela" },
      h("summary", null, h("h2", null, "O que esta ficha não mede"), h("span", { class: "legenda" }, "Perguntas para a assembleia: saem no verso da ficha impressa")),
      intro.cloneNode(true) as HTMLElement,
      h("ul", { class: "verso-lista" }, PERGUNTAS_VERSO.map((p) => h("li", null, p)))),
    h("h2", { class: "so-impressao" }, "O que esta ficha não mede"),
    h("div", { class: "so-impressao" }, intro),
    h("ul", { class: "verso-perguntas so-impressao-bloco" }, PERGUNTAS_VERSO.map((p) => h("li", null, p))),
    h("p", { class: "so-impressao" }, "Assembleia realizada em ____/____/________. Quem escreveu: ______________________. " +
      "Pessoas presentes, por grupo (pais, professores, alunos, funcionários): ______________________________."));
}

export async function telaFicha(main: HTMLElement, g: number, codigo: number, mais: string[]): Promise<void> {
  trocar(main, carregando("Abrindo a ficha da escola..."));
  if (!Number.isInteger(codigo) || codigo <= 0) {
    document.title = "Código inválido: Escola em Pauta";
    trocar(main, h("div", { class: "erro", role: "alert" }, h("h1", null, "Código de escola inválido"),
      h("p", null, h("a", { href: "#/" }, "Buscar uma escola"), ".")));
    return;
  }
  const [b, e, v] = await Promise.all([base(), baixarEscola(codigo), versao()]);
  if (!vivo(g)) return;
  if (!e) {
    document.title = "Escola não encontrada: Escola em Pauta";
    trocar(main, h("article", { class: "verbete", role: "alert" }, h("h1", null, `Não há escola do campo com o código ${codigo}`),
      h("p", null, "A base tem as escolas públicas do campo em atividade no Censo Escolar 2025. Escolas urbanas não aparecem."),
      caixaBusca({ titulo: false })));
    return;
  }
  const nome = nomeLegivel(e.n);
  const lugar = lugarDe(e);
  document.title = `${nome}, ${lugar}: Escola em Pauta`;
  const p = principal(e);
  const rs = e.rota?.receptoras ?? [];
  const lado = h("aside", { class: "ficha-lado", "aria-label": "Mapa" });
  const extras = mais.filter((x) => b.registros.has(x) && !ligacoesDaEscola(b, e).includes(x));
  const urlPrevia = new URL(`escola/${e.c}.html`, document.baseURI).href;
  trocar(main, h("div", { class: "ficha" },
    h("header", { class: "ficha-cabeca" },
      h("a", { class: "voltar nao-imprime", href: "#/" }, "Buscar outra escola"),
      h("h1", null, nome),
      h("p", { class: "ficha-onde" }, lugar),
      selos(e),
      // o aviso (transporte por rio, por exemplo) vem ANTES do número que ele qualifica
      rs.length && e.rota?.aviso ? h("p", { class: "aviso", role: "note" }, h("strong", null, "Atenção: "), e.rota.aviso) : null,
      manchete(e),
      // o aviso (transporte por rio, por exemplo) fica colado no número que ele qualifica
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
        botaoCompartilhar(`${nome}, ${lugar}`, urlPrevia))),
    h("p", { class: "fonte s-fonte" }, `Fonte: ${v.fonte} (dados baixados em ${data(v.data_verificacao)}). Estradas: © colaboradores ` +
      "do OpenStreetMap (ODbL). ", RODAPE,
      h("span", { class: "so-impressao" }, ` Esta ficha no site: ${urlPrevia.replace(/^https?:\/\//, "")}`))));
  // o traçado chega depois, sem segurar a tela: a página já pode rolar e receber o foco
  if (rs.length) {
    void tracados(codigo).then((t) => {
      if (vivo(g)) trocar(lado, prancha(e, rs, t, p));
    });
  }
}
