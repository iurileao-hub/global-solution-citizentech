#!/usr/bin/env bash
# Publica a pasta site/ (montada por web/scripts/montar_site.mjs) na branch gh-pages, servida pelo GitHub Pages.
# A branch gh-pages só tem o site gerado; o código fica na main. Uso: scripts/publicar_pages.sh
set -euo pipefail
raiz=$(git rev-parse --show-toplevel)
[ -f "$raiz/site/index.html" ] || { echo "site/ vazio: rode scripts/dividir_para_web.py e, em web/, npm run build && node scripts/montar_site.mjs" >&2; exit 1; }
tmp=$(mktemp -d)
trap 'git -C "$raiz" worktree remove --force "$tmp" 2>/dev/null || true' EXIT
if git -C "$raiz" ls-remote --exit-code --heads origin gh-pages >/dev/null; then
  git -C "$raiz" fetch -q origin gh-pages
  git -C "$raiz" worktree add -q "$tmp" -B gh-pages origin/gh-pages
else
  git -C "$raiz" worktree add -q --orphan -b gh-pages "$tmp"
fi
rsync -a --delete --exclude .git --exclude falhas.json "$raiz/site/" "$tmp/"
git -C "$tmp" add -A
if git -C "$tmp" diff --cached --quiet; then echo "nada mudou no site"; exit 0; fi
git -C "$tmp" commit -q -m "Site gerado em $(date +%F)"
git -C "$tmp" push -q origin gh-pages
echo "publicado na branch gh-pages"
