"""Linha de comando.

  escola-em-pauta dados                 processa os arquivos já baixados em dados/brutos/ (Censo e Ipea)
  escola-em-pauta ficha <codigo_inep>   gera site/escola/<codigo>.html para UMA escola qualquer do Brasil
  escola-em-pauta site [territorio...]  gera o site dos territórios (muniz-freire, df, vale-do-ribeira)
  escola-em-pauta validar               tabela de erro contra a medição de campo (Muniz Freire)
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help"):
        raise SystemExit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "dados":
        from . import censo, geo
        censo.processar()
        geo.processar()
    elif cmd == "ficha" and len(args) == 1:
        from . import ficha
        from .diagnostico import diagnosticar
        from .site import SITE
        d = diagnosticar(int(args[0]))
        destino = SITE / "escola" / f"{args[0]}.html"
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(ficha.renderizar(d))
        print(destino)
        for a in d.avisos:
            print("aviso:", a)
    elif cmd == "site":
        from . import site
        site.gerar(args or None)
    elif cmd == "validar":
        from . import validacao
        print(validacao.resumo(validacao.validar_muniz_freire()))
    else:
        raise SystemExit(__doc__)
