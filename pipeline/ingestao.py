"""Ingestão fiel dos nove CSVs da Olist no schema ``raw``.

Nenhum tipo, coluna, valor ou linha é alterado nesta etapa. Os arquivos são
lidos diretamente como CSV gzip e todas as colunas entram como texto, porque
a fronteira entre dado recebido e dado transformado precisa ficar na etapa
seguinte. As tabelas são recriadas para que uma execução repetida produza o
mesmo resultado, sem duplicação.

Antes de abrir o banco, todos os arquivos são conferidos. Assim, um arquivo
ausente interrompe a execução sem produzir uma ingestão parcial.
"""

from __future__ import annotations

import sys

import pandas as pd

from .db import PASTA_RAW, conectar, criar_schema, gravar

ARQUIVOS_TABELAS = {
    "olist_orders_dataset.csv.gz": "pedidos",
    "olist_order_items_dataset.csv.gz": "itens_pedido",
    "olist_order_payments_dataset.csv.gz": "pagamentos",
    "olist_order_reviews_dataset.csv.gz": "avaliacoes",
    "olist_customers_dataset.csv.gz": "clientes",
    "olist_sellers_dataset.csv.gz": "vendedores",
    "olist_products_dataset.csv.gz": "produtos",
    "product_category_name_translation.csv.gz": "traducao_categorias",
    "olist_geolocation_dataset.csv.gz": "geolocalizacao",
}


def _arquivos_faltantes() -> list[str]:
    return [
        arquivo
        for arquivo in ARQUIVOS_TABELAS
        if not (PASTA_RAW / arquivo).is_file()
    ]


def main() -> None:
    """Valida os arquivos, ingere as tabelas e imprime suas contagens."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    faltantes = _arquivos_faltantes()
    if faltantes:
        print(f"Arquivos ausentes em {PASTA_RAW}:")
        for arquivo in faltantes:
            print(f"- {arquivo}")
        raise SystemExit(1)

    con = conectar()
    try:
        criar_schema(con, "raw")
        total = 0
        for arquivo, tabela in ARQUIVOS_TABELAS.items():
            df = pd.read_csv(
                PASTA_RAW / arquivo,
                encoding="utf-8",
                dtype=str,
                keep_default_na=True,
            )
            quantidade = gravar(con, df, "raw", tabela)
            total += quantidade
            print(f"raw.{tabela:<22} {quantidade:,}".replace(",", "."))
        print(f"{'TOTAL':<26} {total:,}".replace(",", "."))
    finally:
        con.close()


if __name__ == "__main__":
    main()
