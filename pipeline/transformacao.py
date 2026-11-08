"""Converte o schema ``raw`` para o schema tipado ``refined``.

Esta etapa é a fronteira de confiança do pipeline: datas viram TIMESTAMP,
valores monetários viram DECIMAL, identificadores continuam texto e nulos são
preservados. Cada tabela é recriada, portanto a execução é repetível.
"""

from __future__ import annotations

import sys

from .db import conectar, criar_schema

QUERIES = {
    "pedidos": """
        SELECT
            order_id AS pedido_id,
            customer_id AS cliente_id,
            order_status AS status,
            try_strptime(order_purchase_timestamp, '%Y-%m-%d %H:%M:%S') AS data_compra,
            try_strptime(order_approved_at, '%Y-%m-%d %H:%M:%S') AS data_aprovacao,
            try_strptime(order_delivered_carrier_date, '%Y-%m-%d %H:%M:%S') AS data_envio,
            try_strptime(order_delivered_customer_date, '%Y-%m-%d %H:%M:%S') AS data_entrega,
            try_strptime(order_estimated_delivery_date, '%Y-%m-%d %H:%M:%S') AS data_estimada
        FROM raw.pedidos
    """,
    "itens_pedido": """
        SELECT
            order_id AS pedido_id,
            CAST(order_item_id AS INTEGER) AS item_seq,
            product_id AS produto_id,
            seller_id AS vendedor_id,
            try_cast(price AS DECIMAL(12, 2)) AS preco,
            try_cast(freight_value AS DECIMAL(12, 2)) AS frete
        FROM raw.itens_pedido
    """,
    "pagamentos": """
        SELECT
            order_id AS pedido_id,
            CAST(payment_sequential AS INTEGER) AS pagamento_seq,
            payment_type AS tipo,
            CAST(payment_installments AS INTEGER) AS parcelas,
            try_cast(payment_value AS DECIMAL(12, 2)) AS valor
        FROM raw.pagamentos
    """,
    "avaliacoes": """
        SELECT
            review_id AS avaliacao_id,
            order_id AS pedido_id,
            CAST(review_score AS INTEGER) AS nota,
            try_strptime(review_creation_date, '%Y-%m-%d %H:%M:%S') AS data_criacao
        FROM raw.avaliacoes
    """,
    "clientes": """
        SELECT
            customer_id AS cliente_id,
            customer_unique_id AS cliente_unico_id,
            customer_zip_code_prefix AS cep,
            customer_city AS cidade,
            customer_state AS uf
        FROM raw.clientes
    """,
    "vendedores": """
        SELECT
            seller_id AS vendedor_id,
            seller_zip_code_prefix AS cep,
            seller_city AS cidade,
            seller_state AS uf
        FROM raw.vendedores
    """,
    "produtos": """
        SELECT
            product_id AS produto_id,
            product_category_name AS categoria,
            try_cast(product_name_lenght AS INTEGER) AS nome_comprimento,
            try_cast(product_description_lenght AS INTEGER) AS descricao_comprimento,
            try_cast(product_photos_qty AS INTEGER) AS fotos,
            try_cast(product_weight_g AS DECIMAL(12, 2)) AS peso_g,
            try_cast(product_length_cm AS DECIMAL(12, 2)) AS comprimento_cm,
            try_cast(product_height_cm AS DECIMAL(12, 2)) AS altura_cm,
            try_cast(product_width_cm AS DECIMAL(12, 2)) AS largura_cm
        FROM raw.produtos
    """,
    "traducao_categorias": """
        SELECT
            product_category_name AS categoria,
            product_category_name_english AS categoria_ingles
        FROM raw.traducao_categorias
    """,
}


def main() -> None:
    """Cria as oito tabelas confiáveis e imprime as contagens."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    con = conectar()
    try:
        criar_schema(con, "refined")
        total = 0
        for tabela, query in QUERIES.items():
            con.execute(f'CREATE OR REPLACE TABLE refined."{tabela}" AS {query}')
            quantidade = con.execute(
                f'SELECT count(*) FROM refined."{tabela}"'
            ).fetchone()[0]
            total += quantidade
            print(f"refined.{tabela:<22} {quantidade:,}".replace(",", "."))
        print(f"{'TOTAL':<29} {total:,}".replace(",", "."))
    finally:
        con.close()


if __name__ == "__main__":
    main()
