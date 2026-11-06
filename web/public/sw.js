/* Service worker do Escola em Pauta: a página funciona sem sinal depois da primeira visita.
 *
 * O que guarda:
 *   - a casca do app (HTML, JS, CSS, fontes, ícones), na instalação;
 *   - os dados que a pessoa já abriu (base, lista de nomes, pedaços de escola, traçados), na hora em que abre.
 * Estratégia:
 *   - página (navegação) e dados/versao.json: rede primeiro; sem rede, o que está guardado;
 *   - arquivos com hash no nome (assets/) e dados com ?v=<versão>: o guardado primeiro (o nome muda quando o
 *     conteúdo muda, então o guardado nunca fica velho).
 * Desligar (kill switch): publicar um arquivo "desligar-sw.txt" na raiz do site. Na próxima vez que a página abrir
 * com sinal, o service worker apaga o que guardou e se remove. Sem o arquivo, nada muda.
 */
const VERSAO = "__VERSAO__"; // trocado pelo scripts/montar_site.mjs a cada build
const CASCA = "casca-" + VERSAO;
const DADOS = "dados";
const ARQUIVOS_CASCA = __CASCA__; // lista trocada pelo scripts/montar_site.mjs

self.addEventListener("install", (ev) => {
  ev.waitUntil(caches.open(CASCA).then((c) => c.addAll(ARQUIVOS_CASCA)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (ev) => {
  ev.waitUntil((async () => {
    for (const nome of await caches.keys()) {
      if (nome.startsWith("casca-") && nome !== CASCA) await caches.delete(nome);
    }
    await self.clients.claim();
  })());
});

let ultimaChecagem = 0;
async function talvezDesligar() {
  if (Date.now() - ultimaChecagem < 3600e3) return;
  ultimaChecagem = Date.now();
  try {
    const r = await fetch(new URL("desligar-sw.txt", self.registration.scope), { cache: "no-store" });
    if (!r.ok) return;
    for (const nome of await caches.keys()) await caches.delete(nome);
    await self.registration.unregister();
    for (const c of await self.clients.matchAll({ type: "window" })) c.navigate(c.url);
  } catch {
    /* sem rede: fica como está */
  }
}

async function redePrimeiro(req, cache) {
  try {
    const resp = await fetch(req);
    if (resp.ok) (await caches.open(cache)).put(req, resp.clone());
    return resp;
  } catch (e) {
    const guardado = await caches.match(req, { ignoreSearch: req.mode === "navigate" });
    if (guardado) return guardado;
    if (req.mode === "navigate") {
      // link de prévia (escola/<código>.html) sem rede: manda para a ficha no app, que está guardado. Servir a casca
      // ali quebraria, porque os caminhos relativos dela (./assets/) apontariam para escola/assets/.
      const escola = new URL(req.url).pathname.match(/\/escola\/(\d+)\.html$/);
      if (escola) return Response.redirect(new URL(`./#/escola/${escola[1]}`, self.registration.scope).href, 302);
      const casca = await caches.match(new URL("./", self.registration.scope));
      if (casca) return casca;
    }
    throw e;
  }
}

/** Dados de uma versão anterior (outro ?v=) não servem mais: apaga, para o aparelho não acumular. */
async function limparDadosVelhos(versao) {
  const cache = await caches.open(DADOS);
  for (const req of await cache.keys()) {
    const v = new URL(req.url).searchParams.get("v");
    if (v && v !== versao) await cache.delete(req);
  }
}

async function guardadoPrimeiro(req, cache) {
  const guardado = await caches.match(req);
  if (guardado) return guardado;
  const resp = await fetch(req);
  if (resp.ok) (await caches.open(cache)).put(req, resp.clone());
  return resp;
}

self.addEventListener("fetch", (ev) => {
  const req = ev.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const caminho = url.pathname.slice(new URL(self.registration.scope).pathname.length);
  if (req.mode === "navigate") {
    ev.waitUntil(talvezDesligar());
    ev.respondWith(redePrimeiro(req, CASCA));
  } else if (caminho === "dados/versao.json") {
    const resp = redePrimeiro(req, DADOS);
    ev.respondWith(resp.then((r) => r.clone()));
    ev.waitUntil(resp.then((r) => r.clone().json()).then((v) => limparDadosVelhos(v.versao)).catch(() => undefined));
  } else if (caminho.startsWith("dados/") && url.searchParams.has("v")) {
    ev.respondWith(guardadoPrimeiro(req, DADOS));
  } else if (caminho.startsWith("assets/")) {
    ev.respondWith(guardadoPrimeiro(req, CASCA));
  }
});
