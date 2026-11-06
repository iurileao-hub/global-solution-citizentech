/** Como funciona: o que o Escola em Pauta é, de onde vêm os números, os limites e a privacidade. */

import { base, versao } from "../dados";
import { h, trocar } from "../dom";
import { vivo } from "../estado";
import { mil } from "../formato";
import { data, NAO_OFICIAL } from "../nucleo/respostas";

/** As palavras que a ficha e as orientações usam, em linguagem de todo dia (pedido do teste com a persona de uma
 * agricultora: "PL", "INEP", "piso" e "receptora" apareciam sem explicação). */
const PALAVRAS: [string, string][] = [
  ["Ação civil pública", "Processo na Justiça para defender um direito de muita gente ao mesmo tempo. Podem entrar com ela o Ministério Público, a Defensoria Pública e associações, como a de pais."],
  ["Censo Escolar", "Levantamento feito todo ano, em que cada escola do país informa seus alunos, turmas, transporte e prédio. É a fonte dos números das fichas."],
  ["Código INEP", "O número de cada escola no Censo Escolar. Serve para achar a escola sem confusão de nomes parecidos."],
  ["Conselho de Educação", "O órgão que faz as regras do ensino e precisa se manifestar antes do fechamento. É o Conselho Municipal, se o município tem sistema próprio de ensino; senão, o Conselho Estadual."],
  ["Convenção 169 da OIT", "Tratado internacional assinado pelo Brasil. Garante a povos indígenas e comunidades quilombolas o direito de serem consultados antes de decisões que os afetam."],
  ["Defensoria Pública", "Órgão público que dá orientação e defesa na Justiça, de graça, a quem não pode pagar advogado."],
  ["Diagnóstico do impacto", "O estudo que a LDB exige antes de fechar uma escola do campo: o que muda para os alunos e para a comunidade. A lei não diz como ele deve ser feito."],
  ["EJA", "Educação de Jovens e Adultos: turmas para quem não estudou na idade certa. As fichas não usam essas turmas para achar as escolas que receberiam os alunos."],
  ["Escola do campo", "A escola em área rural, ou a escola da cidade que atende principalmente gente do campo (Decreto 7.352/2010). É a ela que a regra do fechamento se aplica."],
  ["Escola receptora", "A escola que receberia os alunos se a escola deles fechasse."],
  ["Etapa", "Cada fase do estudo: creche, pré-escola, anos iniciais (1º ao 5º ano), anos finais (6º ao 9º ano) e ensino médio."],
  ["Extinta, paralisada", "No Censo, escola extinta é a que foi encerrada de vez. Paralisada é a que está sem aulas, mas ainda não foi encerrada oficialmente."],
  ["INEP", "Instituto do Ministério da Educação que faz o Censo Escolar."],
  ["LAI e SIC", "LAI é a Lei de Acesso à Informação (Lei 12.527/2011), que garante a qualquer pessoa o direito de pedir documentos ao governo. O SIC é o balcão, na internet ou presencial, onde se faz o pedido."],
  ["LDB", "Lei de Diretrizes e Bases da Educação (Lei 9.394/1996), a lei que organiza a educação no país. O art. 28 trata das escolas do campo e do fechamento."],
  ["Ministério Público", "Órgão que defende os direitos da sociedade, inclusive o direito à educação. Recebe denúncias e pode levar o caso à Justiça."],
  ["Nucleação", "Juntar os alunos de várias escolas pequenas numa escola maior, o \"núcleo\". É o nome técnico mais comum do fechamento."],
  ["Piso, \"pelo menos\"", "O menor valor possível. A distância da ficha vai de escola a escola; o caminho real das crianças começa em casa e é maior."],
  ["PL", "Projeto de lei: uma proposta que ainda está sendo discutida no Congresso. Só vale como lei depois de aprovada e sancionada."],
  ["Resolução CNE/CEB", "Regra nacional do Conselho Nacional de Educação, na parte da educação básica."],
];

export async function telaSobre(main: HTMLElement, g: number, secao: string | null = null): Promise<HTMLElement | void> {
  document.title = "Como funciona: Escola em Pauta";
  const [b, v] = await Promise.all([base(), versao()]);
  if (!vivo(g)) return;
  const n = b.registros.size;
  const temas = Object.values(b.temas).map((t) => t.nome);
  const palavras = h("section", { class: "glossario", id: "palavras" },
    h("h2", null, "O que querem dizer as palavras da ficha"),
    h("dl", null, PALAVRAS.map(([t, d]) => [h("dt", null, t), h("dd", null, d)])));
  trocar(main, h("article", { class: "coluna", style: "padding-top:1.5rem" },
    h("h1", null, "Como funciona"),
    h("p", { class: "sub" }, "A LDB, no art. 28, exige um diagnóstico do impacto e a manifestação da comunidade escolar antes do " +
      "fechamento de escolas do campo, indígenas e quilombolas. A lei não diz como medir. Na prática, os números costumam " +
      "aparecer só depois, no recurso ao Ministério Público ou no Tribunal de Contas. O Escola em Pauta põe os números públicos " +
      "na mão da comunidade antes da reunião."),
    h("aside", { class: "aviso" }, h("strong", null, "Não oficial. "), NAO_OFICIAL.replace(/^Assistente NÃO OFICIAL, feito/, "Feito")),

    h("h2", null, "O assistente"),
    h("p", null, `Responde a partir de uma base de ${n} orientações em ${temas.length} assuntos (${temas.join(", ")}), cada uma ` +
      "conferida no texto oficial, com a fonte e a data. O texto é o da base, palavra por palavra: o assistente não escreve " +
      "nada novo. Quando a base não tem uma resposta segura, ele diz que não sabe e indica outro caminho."),
    h("p", null, "A busca roda no seu próprio celular: normaliza o texto (sem acento, sem palavras vazias como \"de\" e \"que\"), " +
      "corta cada palavra no radical e consulta um índice invertido, como o índice remissivo de um livro. É a mesma busca da " +
      "versão de terminal, reescrita para o navegador e conferida nas mesmas 130 perguntas de teste e nos nomes das " +
      `${mil(v.escolas)} escolas.`),

    h("h2", null, "Os números de cada escola"),
    h("ul", null,
      h("li", null, h("b", null, "Escolas e matrículas: "), "Censo Escolar do INEP, 2019 a 2025, declarado pela própria escola. " +
        "Entram as escolas públicas ativas rurais e as urbanas em que mais da metade dos alunos mora na zona rural."),
      h("li", null, h("b", null, "Localização: "), "Catálogo de Escolas do INEP, pela base geolocalizada do Ipea. Escola sem " +
        "coordenada aparece com o aviso, sem distância inventada."),
      h("li", null, h("b", null, "Estradas: "), "OpenStreetMap, com o tipo de piso de cada via. O caminho mais rápido de escola a " +
        "escola é calculado pelo algoritmo de Dijkstra, com velocidades de ônibus escolar."),
      h("li", null, h("b", null, "Para onde as crianças iriam: "), "as escolas públicas mais próximas por estrada que oferecem " +
        "alguma das mesmas etapas. A abertura da ficha usa a mais próxima que recebe todas as etapas.")),

    h("h2", null, "Quando várias escolas fecham juntas"),
    h("p", null, "Fechamento costuma vir em lote: 93% das extinções de escolas rurais de 2019 a 2025 aconteceram em município e " +
      "ano com duas ou mais. Num plano assim, a escola que a ficha aponta pode fechar também. O ",
      h("a", { href: "#/simular" }, "simulador de plano"), " manda cada etapa para a escola mais próxima por estrada que a " +
      "oferece e não fecha no plano, entre as 10 calculadas para cada escola. A prefeitura pode indicar outro destino, e a " +
      "conta passa a usá-lo. Como a ficha responde outra pergunta (a escola que recebe todas as etapas de uma vez), o " +
      "simulador pode mostrar distâncias menores que as da ficha."),

    h("h2", null, "Quanto o cálculo fica abaixo do real"),
    h("p", null, "Em 2025, a prefeitura de Muniz Freire (ES) anunciou o fim do ensino fundamental na EMEF Durval Máximo. A área " +
      "técnica do Tribunal de Contas estimou que os alunos percorreriam até 52 km por dia até a escola indicada para " +
      "recebê-los. De escola a escola, o nosso cálculo dá 24,9 km (a ficha diz \"pelo menos 24 km\"): cerca da metade, porque o Tribunal pensa em quem mora mais " +
      "longe. Por isso a ficha fala sempre em \"pelo menos\". É uma referência só: mostra a ordem de grandeza, sem autorizar " +
      "um fator de correção. ", h("a", { href: "#/escola/32049501" }, "Ver a ficha da Durval Máximo"), "."),

    h("h2", null, "O que fica de fora"),
    h("ul", null,
      h("li", null, "Onde cada criança mora (é dado pessoal), a rota real do ônibus e a estrada na chuva. Essas perguntas vão " +
        "para o verso da ficha impressa, para a comunidade responder."),
      h("li", null, "No Norte, parte do transporte escolar é por rio: a rota por estrada pode não ser o caminho das crianças, e " +
        "a ficha avisa."),
      h("li", null, "As vagas de cada escola receptora não são publicadas."),
      h("li", null, `A base tem ${n} orientações. Fora delas, o assistente não responde.`)),

    palavras,

    h("h2", null, "Privacidade"),
    h("p", null, "Esta página não pede, não guarda e não envia nenhum dado pessoal. Não há cadastro, cookie de rastreamento ou " +
      "contador de visitas. O que você digita fica no seu aparelho: a busca acontece no próprio navegador. Depois da primeira " +
      "visita, a página e as fichas já abertas funcionam sem sinal."),

    h("h2", null, "Quem fez"),
    h("p", null, "Projeto acadêmico do Grupo 9 de Ciência da Computação da FIAP, na Global Solution 2026 (tema CitizenTech): " +
      "Gabriel Carmona Bittencourt, Gabrielly Drosda da Silva, Iúri Leão de Almeida, Márcio Francisco dos Santos Júnior e " +
      "Maria Sophia Domingues dos Santos. O código e os dados estão no ",
    h("a", { href: "https://github.com/iurileao-hub/global-solution-citizentech" }, "repositório do projeto"), "."),
    h("p", { class: "legenda" }, `Dados: ${v.fonte}, baixados em ${data(v.data_verificacao)}. Versão dos dados ${v.versao}. ` +
      "Estradas © colaboradores do OpenStreetMap (ODbL). Malha de UFs: IBGE.")));
  if (secao === "palavras") return palavras;
}
