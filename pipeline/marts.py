"""Executa os arquivos SQL da camada analítica ``marts``."""

from __future__ import annotations

import sys
from pathlib import Path

from .db import conectar, criar_schema

PASTA_MARTS = Path(__file__).resolve().parent.parent / "sql" / "marts"


def main() -> None:
    """Executa cada mart em ordem alfabética e mostra sua contagem."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    arquivos = sorted(PASTA_MARTS.glob("*.sql"))
    if not arquivos:
        print(f"Nenhum arquivo SQL encontrado em {PASTA_MARTS}.")
        raise SystemExit(1)

    con = conectar()
    try:
        criar_schema(con, "marts")
        total = 0
        for arquivo in arquivos:
            tabela = arquivo.stem.split("_", 1)[1]
            con.execute(arquivo.read_text(encoding="utf-8"))
            quantidade = con.execute(
                f'SELECT count(*) FROM marts."{tabela}"'
            ).fetchone()[0]
            total += quantidade
            print(f"marts.{tabela:<28} {quantidade:,}".replace(",", "."))
        print(f"{len(arquivos)} marts{'':<20} {total:,}".replace(",", "."))
    finally:
        con.close()


if __name__ == "__main__":
    main()
