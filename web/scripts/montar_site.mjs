// Monta a pasta site/ que vai para o GitHub Pages (scripts/publicar_pages.sh publica):
//   1. o app compilado (web/dist, de `npm run build`);
//   2. os dados (site/dados, de scripts/dividir_para_web.py; ficam onde estão);
//   3. uma PRÉVIA por escola, escola/<código>.html: HTML mínimo com o nome e os números já escritos, para o
//      link colado no WhatsApp mostrar um cartão (o robô que monta o cartão não roda JavaScript). Quem abre
//      o link é levado para a ficha do app. Também mantém vivos os links antigos das 256 fichas do protótipo.
//   4. o service worker com a versão e a lista da casca.
// Uso (em web/):  npm run build && node scripts/montar_site.mjs
import { createHash } from "node:crypto";
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { gzipSync } from "node:zlib";

const WEB = join(import.meta.dirname, "..");
const DIST = join(WEB, "dist");
const SITE = join(WEB, "..", "site");
const DADOS = join(SITE, "dados");
// o robô que monta o cartão do link (WhatsApp, Facebook) nem sempre resolve endereço relativo na og:image
const URL_SITE = process.env.URL_SITE ?? "https://iurileao-hub.github.io/global-solution-citizentech/";
const ORCAMENTO_PRIMEIRA_TELA = 100_000; // bytes comprimidos, sem as fontes (docs/orcamento_web.md)

if (!existsSync(join(DIST, "index.html"))) throw new Error("web/dist vazio: rode `npm run build` antes");
if (!existsSync(join(DADOS, "versao.json"))) throw new Error("site/dados sem versao.json: rode scripts/dividir_para_web.py");

// 1. limpa site/ (menos os dados) e copia o app
for (const nome of readdirSync(SITE)) if (nome !== "dados") rmSync(join(SITE, nome), { recursive: true, force: true });
cpSync(DIST, SITE, { recursive: true });
const indexHtml = readFileSync(join(SITE, "index.html"), "utf-8")
  .replace('content="previa.png"', `content="${URL_SITE}previa.png"`)
  .replace('<meta property="og:type" content="website">', `<meta property="og:type" content="website"><meta property="og:url" content="${URL_SITE}">`);
writeFileSync(join(SITE, "index.html"), indexHtml);
writeFileSync(join(SITE, ".nojekyll"), "");

function arquivos(dir) {
  return readdirSync(dir).flatMap((n) => {
    const c = join(dir, n);
    return statSync(c).isDirectory() ? arquivos(c) : [c];
  });
}

// 4. service worker: versão = hash do app + versão dos dados
const versaoDados = JSON.parse(readFileSync(join(DADOS, "versao.json"), "utf-8")).versao;
const doApp = arquivos(DIST).filter((f) => !f.endsWith("sw.js")).sort();
const hash = createHash("sha256");
for (const f of doApp) hash.update(relative(DIST, f)).update(readFileSync(f));
const versao = `${hash.digest("hex").slice(0, 10)}-${versaoDados}`;
// previa.png (105 KB) é só para o cartão do link: o app nunca mostra, então não entra na instalação
const casca = ["./", ...doApp.map((f) => relative(DIST, f).split("\\").join("/"))
  .filter((f) => f !== "index.html" && f !== "previa.png" && !f.endsWith(".md"))];
const sw = readFileSync(join(DIST, "sw.js"), "utf-8").replace("__VERSAO__", versao).replace("__CASCA__", JSON.stringify(casca));
writeFileSync(join(SITE, "sw.js"), sw);

// 3. prévias por escola
const UF_NOME = {
  AC: "Acre", AL: "Alagoas", AP: "Amapá", AM: "Amazonas", BA: "Bahia", CE: "Ceará", DF: "Distrito Federal",
  ES: "Espírito Santo", GO: "Goiás", MA: "Maranhão", MT: "Mato Grosso", MS: "Mato Grosso do Sul", MG: "Minas Gerais",
  PA: "Pará", PB: "Paraíba", PR: "Paraná", PE: "Pernambuco", PI: "Piauí", RJ: "Rio de Janeiro", RN: "Rio Grande do Norte",
  RS: "Rio Grande do Sul", RO: "Rondônia", RR: "Roraima", SC: "Santa Catarina", SP: "São Paulo", SE: "Sergipe", TO: "Tocantins",
};
const SIGLAS = new Set(("EMEF EEEFM CEEFMTI CEI EPM EEEM EMEI EMEIEF CMEI CEF CED EC CAIC EE EM EMEB EMEFM EEF EEM " +
  "EEFM CIEP CE UE ETEC IF JI").split(" "));
const MINUSCULAS = new Set("de da do das dos e em na no".split(" "));
const legivel = (nome) => nome.split(/\s+/).filter(Boolean).map((p, i) => {
  if (SIGLAS.has(p) || !/[AEIOUÁÉÍÓÚÂÊÔÃÕÀ]/i.test(p)) return p;
  if (i > 0 && MINUSCULAS.has(p.toLowerCase())) return p.toLowerCase();
  return p.charAt(0).toUpperCase() + p.slice(1).toLowerCase();
}).join(" ");
const esc = (t) => String(t).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const mil = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const km = (x) => (x >= 10 ? String(Math.round(x)) : x.toFixed(1).replace(".", ","));

function resumo(e) {
  const partes = [];
  if (e.t) partes.push(`${mil(e.t)} ${e.t === 1 ? "aluno" : "alunos"}${e.tp ? `, ${mil(e.tp)} de transporte escolar` : ""}.`);
  const rs = e.rota?.receptoras ?? [];
  const etapas = Object.keys(e.e);
  const todas = rs.filter((r) => etapas.every((x) => (r.etapas ?? []).includes(x)));
  const lista = todas.length ? todas : rs;
  if (lista.length) {
    const p = lista.reduce((a, b) => (b.km < a.km ? b : a));
    const qual = todas.length ? "as mesmas etapas" : "parte das etapas";
    partes.push(p.km < 1
      ? `Se fechar: a escola mais perto que oferece ${qual} fica no mesmo lugar ou quase (mesma coordenada pública).`
      : `Se fechar: pelo menos ${km(p.km)} km por dia de estrada até a escola mais perto que oferece ${qual}.`);
    if (e.rota.aviso) partes.push("Atenção: na região, parte do transporte escolar é por rio.");
  } else if (!e.geo) {
    partes.push("A localização desta escola não é pública no INEP.");
  }
  partes.push("Ficha com dados públicos para a reunião sobre o fechamento.");
  return partes.join(" ");
}

function previa(e) {
  const nome = legivel(e.n);
  const lugar = !e.m || !e.uf ? "município não informado no Censo"
    : e.uf === "DF" ? "Distrito Federal" : `${e.m}, ${UF_NOME[e.uf] ?? e.uf}`;
  const titulo = `${nome}, ${lugar}`;
  const desc = resumo(e);
  const destino = `../#/escola/${e.c}`;
  return `<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(titulo)}: Escola em Pauta</title><meta name="description" content="${esc(desc)}">
<meta property="og:title" content="${esc(titulo)}"><meta property="og:description" content="${esc(desc)}">
<meta property="og:type" content="article"><meta property="og:site_name" content="Escola em Pauta">
<meta property="og:image" content="${URL_SITE}previa.png"><meta property="og:url" content="${URL_SITE}escola/${e.c}.html"><meta name="twitter:card" content="summary_large_image">
<meta http-equiv="refresh" content="0; url=${destino}"><link rel="canonical" href="${destino}">
<style>body{font:17px/1.5 system-ui,sans-serif;margin:2rem auto;max-width:36rem;padding:0 16px;color:#1e2b2f;background:#f8f9f4}a{color:#255f8a}</style>
</head><body><h1>${esc(nome)}</h1><p>${esc(lugar)}. Código INEP ${e.c}.</p><p>${esc(desc)}</p>
<p><a href="${destino}">Abrir a ficha da escola</a></p><script>location.replace(${JSON.stringify(destino)})</script></body></html>`;
}

mkdirSync(join(SITE, "escola"), { recursive: true });
let n = 0;
let bytes = 0;
for (const f of readdirSync(join(DADOS, "escolas"))) {
  for (const e of JSON.parse(readFileSync(join(DADOS, "escolas", f), "utf-8")).escolas) {
    const html = previa(e);
    writeFileSync(join(SITE, "escola", `${e.c}.html`), html);
    n += 1;
    bytes += Buffer.byteLength(html);
  }
}

// orçamento da primeira tela: index.html + o JS e o CSS de entrada (sem fontes, que chegam depois)
const index = readFileSync(join(SITE, "index.html"), "utf-8");
const entrada = [...index.matchAll(/(?:src|href)="\.\/(assets\/[^"]+\.(?:js|css))"/g)].map((m) => m[1]);
const gz = (b) => gzipSync(b, { level: 9 }).length;
const primeira = gz(Buffer.from(index)) + entrada.reduce((s, a) => s + gz(readFileSync(join(SITE, a))), 0);
const base = JSON.parse(readFileSync(join(DADOS, "manifesto.json"), "utf-8")).arquivos["base_orientacoes.json"].gzip;
console.log(`site/: app ${versao} | ${n} prévias (${(bytes / 1e6).toFixed(1)} MB) | primeira tela ${(primeira / 1e3).toFixed(0)} KB ` +
  `+ base ${(base / 1e3).toFixed(0)} KB comprimidos (orçamento ${ORCAMENTO_PRIMEIRA_TELA / 1e3} KB)`);
if (primeira + base > ORCAMENTO_PRIMEIRA_TELA) {
  console.error("ORÇAMENTO: a primeira tela passou do limite");
  process.exit(1);
}
