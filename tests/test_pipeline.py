from pathlib import Path

import duckdb
import pytest

RAIZ = Path(__file__).resolve().parent.parent
BANCOS = RAIZ / "olist.duckdb"

pytestmark = pytest.mark.skipif(
    not BANCOS.exists(),
    reason="Banco local ausente; execute o pipeline antes dos testes de dados.",
)


@pytest.fixture
def con():
    connection = duckdb.connect(str(BANCOS), read_only=True)
    yield connection
    connection.close()


def test_banco_tem_todas_as_camadas(con):
    tabelas = {
        row[0]
        for row in con.execute(
            "SELECT table_schema || '.' || table_name "
            "FROM information_schema.tables "
            "WHERE table_schema IN ('raw', 'refined', 'marts')"
        ).fetchall()
    }

    esperadas = {
        "raw.pedidos",
        "raw.itens_pedido",
        "raw.pagamentos",
        "raw.avaliacoes",
        "raw.clientes",
        "raw.vendedores",
        "raw.produtos",
        "raw.traducao_categorias",
        "raw.geolocalizacao",
        "refined.pedidos",
        "refined.itens_pedido",
        "refined.pagamentos",
        "refined.avaliacoes",
        "refined.clientes",
        "refined.vendedores",
        "refined.produtos",
        "refined.traducao_categorias",
    }
    assert esperadas <= tabelas
    assert sum(tabela.startswith("marts.") for tabela in tabelas) == 10


def test_refined_preserva_contagens_de_ingestao(con):
    contagens = con.execute(
        "SELECT (SELECT count(*) FROM raw.pedidos), "
        "(SELECT count(*) FROM refined.pedidos), "
        "(SELECT count(*) FROM raw.itens_pedido), "
        "(SELECT count(*) FROM refined.itens_pedido), "
        "(SELECT count(*) FROM raw.geolocalizacao)"
    ).fetchone()
    assert contagens == (99441, 99441, 112650, 112650, 1000163)


def test_raw_entra_como_varchar(con):
    tipos = con.execute(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND data_type <> 'VARCHAR'"
    ).fetchone()[0]
    assert tipos == 0


@pytest.mark.parametrize(
    ("tabela", "chave"),
    (
        ("pedidos", "pedido_id"),
        ("itens_pedido", "(pedido_id, item_seq)"),
        ("pagamentos", "(pedido_id, pagamento_seq)"),
        ("avaliacoes", "(avaliacao_id, pedido_id)"),
        ("clientes", "cliente_id"),
        ("vendedores", "vendedor_id"),
        ("produtos", "produto_id"),
        ("traducao_categorias", "categoria"),
    ),
)
def test_chaves_primarias_sao_unicas(con, tabela, chave):
    duplicadas = con.execute(
        f'SELECT count(*) FROM (SELECT {chave}, count(*) AS n '
        f'FROM refined."{tabela}" GROUP BY {chave} HAVING n > 1)'
    ).fetchone()[0]
    assert duplicadas == 0, f"{tabela} possui chaves duplicadas"


def test_itens_referenciam_pedidos(con):
    orfas = con.execute(
        "SELECT count(*) FROM refined.itens_pedido i "
        "LEFT JOIN refined.pedidos p ON p.pedido_id = i.pedido_id "
        "WHERE p.pedido_id IS NULL"
    ).fetchone()[0]
    assert orfas == 0


def test_itens_referenciam_produtos_e_vendedores(con):
    orfas = con.execute(
        "SELECT count(*) FROM refined.itens_pedido i "
        "LEFT JOIN refined.produtos p ON p.produto_id = i.produto_id "
        "LEFT JOIN refined.vendedores v ON v.vendedor_id = i.vendedor_id "
        "WHERE p.produto_id IS NULL OR v.vendedor_id IS NULL"
    ).fetchone()[0]
    assert orfas == 0


def test_datas_e_valores_refined_tem_tipos_corretos(con):
    tipos = dict(
        con.execute(
            "SELECT table_name || '.' || column_name, data_type "
            "FROM information_schema.columns "
            "WHERE table_schema = 'refined' "
            "AND ((table_name = 'pedidos' AND column_name LIKE 'data_%') "
            "OR (table_name = 'itens_pedido' AND column_name IN "
            "('preco', 'frete')))"
        ).fetchall()
    )
    assert all(tipo == "TIMESTAMP" for chave, tipo in tipos.items() if "pedidos" in chave)
    assert tipos["itens_pedido.preco"] == "DECIMAL(12,2)"
    assert tipos["itens_pedido.frete"] == "DECIMAL(12,2)"


def test_marts_tem_linhas_e_colunas_de_contrato(con):
    contratos = {
        "vendas_mensais": {"mes", "pedidos", "receita", "ticket_medio"},
        "top_categorias": {"categoria", "itens", "receita"},
        "entrega_no_prazo": {"no_prazo", "atrasados", "entregues"},
        "mix_pagamento": {"tipo", "pagamentos", "valor", "percentual"},
        "vendedores_pareto": {"vendedor_id", "receita", "posicao"},
    }
    for tabela, colunas in contratos.items():
        existentes = {
            row[0]
            for row in con.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'marts' AND table_name = ?",
                [tabela],
            ).fetchall()
        }
        assert colunas <= existentes
        assert con.execute(f"SELECT count(*) FROM marts.{tabela}").fetchone()[0] > 0


def test_marts_de_operacao_tem_regras_validas(con):
    no_prazo = con.execute(
        "SELECT no_prazo, atrasados, entregues, percentual_no_prazo "
        "FROM marts.entrega_no_prazo"
    ).fetchone()
    assert no_prazo[0] + no_prazo[1] == no_prazo[2]
    assert 0 <= no_prazo[3] <= 100

    pareto = con.execute(
        "SELECT min(posicao), max(posicao), max(percentual_acumulado) "
        "FROM marts.vendedores_pareto"
    ).fetchone()
    assert pareto[0] == 1
    assert pareto[1] == 3095
    assert 99 <= pareto[2] <= 100
