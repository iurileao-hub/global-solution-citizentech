import { createReadStream, existsSync, statSync } from "node:fs";
import { join, normalize } from "node:path";
import type { Plugin } from "vite";
import { defineConfig } from "vitest/config";

// Os dados (site/dados/, gerados por scripts/dividir_para_web.py) NÃO passam pelo Vite: são 100+ MB de pedaços
// que o navegador baixa sob demanda. No desenvolvimento, este plugin serve a pasta em /dados; no build, o
// scripts/montar_site.mjs junta o app compilado e os dados em site/.
const DADOS = join(import.meta.dirname, "..", "site", "dados");

function dadosLocais(): Plugin {
  return {
    name: "dados-locais",
    configureServer(server) {
      server.middlewares.use("/dados", (req, res, next) => {
        const caminho = normalize(join(DADOS, decodeURIComponent((req.url ?? "/").split("?")[0])));
        if (!caminho.startsWith(DADOS) || !existsSync(caminho) || !statSync(caminho).isFile()) return next();
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        createReadStream(caminho).pipe(res);
      });
    },
  };
}

export default defineConfig({
  base: "./", // caminhos relativos: o mesmo build serve em /global-solution-citizentech/ e em qualquer pasta
  plugins: [dadosLocais()],
  build: { outDir: "dist", emptyOutDir: true, target: "es2020", assetsInlineLimit: 0 },
  test: { include: ["test/**/*.test.ts"], testTimeout: 60_000 },
});
