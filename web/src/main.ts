/**
 * Escola em Pauta, camada 1: o assistente e as fichas no navegador, sem servidor.
 *
 * Rotas pelo "#" do endereço (funcionam no GitHub Pages sem configuração e o botão voltar do celular funciona):
 *   #/                         início: a caixa única (escola, código INEP ou pergunta) e os assuntos
 *   #/pergunta/<texto>         a resposta do assistente para o texto
 *   #/orientacao/<código>      uma orientação da base (D1, C3...)
 *   #/assunto/<tema>           as orientações de um tema
 *   #/escola/<código INEP>     a ficha da escola (?mais=D3,F2 acrescenta sugestões vindas da pergunta)
 *   #/retrato                  o retrato nacional
 *   #/retrato/<UF>             o retrato com uma UF escolhida (o mapa da página inicial leva para cá)
 *   #/sobre                    como funciona, limites, privacidade e fontes
 *   #/sobre/palavras           o glossário (LDB, INEP, PL, piso...), aberto direto nele
 */

import "./estilo.css";
import { ErroDados, versao } from "./dados";
import { h, trocar } from "./dom";
import { novaGeracao, vivo } from "./estado";
import { telaAssunto, telaInicio, telaPergunta } from "./telas/inicio";

const main = document.getElementById("conteudo") as HTMLElement;
let ultimaRota = "#/";

function marcarNav(primeiro: string): void {
  for (const a of document.querySelectorAll<HTMLAnchorElement>(".nav a")) {
    const alvo = a.getAttribute("href")!.slice(2);
    if (alvo === primeiro) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  }
}

function decodificar(t: string): string {
  try {
    return decodeURIComponent(t);
  } catch {
    return t; // "%E0" sozinho não é texto válido: usa como veio
  }
}

async function rota(): Promise<void> {
  // o link "Pular para o conteúdo" também mexe no "#": não é uma rota, só leva o foco ao conteúdo
  if (location.hash === "#conteudo") {
    history.replaceState(null, "", ultimaRota);
    main.focus();
    return;
  }
  ultimaRota = location.hash || "#/";
  const g = novaGeracao();
  const hash = location.hash.replace(/^#/, "") || "/";
  const [caminho, consulta = ""] = hash.split("?");
  const partes = caminho.split("/").filter(Boolean);
  const params = new URLSearchParams(consulta);
  marcarNav(partes[0] ?? "");
  const navegou = document.body.dataset.navegou === "1";
  document.body.dataset.navegou = "1";
  // a tela pode pedir para abrir num ponto que não é o topo (o retrato com uma UF escolhida abre no mapa)
  let abrirEm: HTMLElement | void = undefined;
  try {
    switch (partes[0]) {
      case undefined:
        await telaInicio(main, g);
        break;
      case "pergunta":
        await telaPergunta(main, g, decodificar(partes.slice(1).join("/")));
        break;
      case "orientacao":
        await telaPergunta(main, g, partes[1] ?? "", true);
        break;
      case "assunto":
        await telaAssunto(main, g, partes[1] ?? "");
        break;
      case "escola": {
        const { telaFicha } = await import("./telas/ficha");
        const mais = (params.get("mais") ?? "").split(",").filter(Boolean);
        await telaFicha(main, g, Number(partes[1]), mais);
        break;
      }
      case "retrato": {
        const { telaRetrato } = await import("./telas/retrato");
        abrirEm = await telaRetrato(main, g, partes[1] ?? null);
        break;
      }
      case "sobre": {
        const { telaSobre } = await import("./telas/sobre");
        abrirEm = await telaSobre(main, g, partes[1] ?? null);
        break;
      }
      default:
        trocar(main, h("section", { class: "verbete" }, h("h1", null, "Página não encontrada"),
          h("p", null, "Este endereço não existe no Escola em Pauta. ", h("a", { href: "#/" }, "Voltar ao início"), ".")));
    }
  } catch (e) {
    if (!vivo(g)) return;
    console.error(e);
    const semSinal = e instanceof ErroDados && e.status === 0;
    trocar(main, h("div", { class: "erro", role: "alert" },
      h("h1", { style: "font-size:var(--t2);margin-top:1rem" }, semSinal ? "Sem sinal para abrir esta página" : "Algo deu errado ao montar esta página"),
      // sem sinal, o nome do arquivo que faltou ("escolas/095.json") não ajuda ninguém: diz o que fazer
      h("p", null, semSinal ? "Sem internet, só abrem as fichas e páginas que você já abriu antes neste aparelho. Quando " +
        "tiver sinal, abra as fichas que vai precisar: elas ficam guardadas para depois." : e instanceof Error ? e.message : String(e)),
      h("p", null, h("a", { href: location.hash || "#/" }, "Tentar de novo"), " ou ", h("a", { href: "#/" }, "voltar ao início"), ".")));
  }
  if (!vivo(g)) return;
  if (abrirEm) {
    // leva a tela e o foco ao ponto pedido: quem usa leitor de tela ouve o que foi escolhido
    abrirEm.scrollIntoView({ block: "start" });
    abrirEm.tabIndex = -1;
    abrirEm.focus({ preventScroll: true });
  } else if (navegou) {
    window.scrollTo(0, 0);
    // leva o foco ao título da nova página: quem usa leitor de tela ouve onde chegou
    const titulo = main.querySelector<HTMLElement>("h1");
    if (titulo) {
      titulo.tabIndex = -1;
      titulo.focus({ preventScroll: true });
    }
  }
}

window.addEventListener("hashchange", () => void rota());
void rota();

versao().then((v) => {
  const el = document.getElementById("versao-dados");
  if (el) {
    const [a, m, d] = v.data_verificacao.split("-");
    el.textContent = `Versão dos dados ${v.versao}, baixados em ${d}/${m}/${a}.`;
  }
}).catch(() => undefined);

// funciona sem sinal depois da primeira visita (sw.js guarda a página e o que já foi aberto)
if ("serviceWorker" in navigator && window.isSecureContext) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch(() => undefined);
  });
}
