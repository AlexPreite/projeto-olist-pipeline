from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BANCOS = RAIZ / "olist.duckdb"


def test_banco_tem_camadas_e_tabelas():
    con = duckdb.connect(str(BANCOS), read_only=True)
    tabelas = {
        row[0]
        for row in con.execute(
            "SELECT table_schema || '.' || table_name "
            "FROM information_schema.tables "
            "WHERE table_schema IN ('raw', 'refined', 'marts')"
        ).fetchall()
    }
    con.close()
    assert "raw.pedidos" in tabelas
    assert "refined.pedidos" in tabelas
    assert "marts.vendas_mensais" in tabelas


def test_refined_preserva_contagens_de_ingestao():
    con = duckdb.connect(str(BANCOS), read_only=True)
    contagens = con.execute(
        "SELECT (SELECT count(*) FROM raw.pedidos), "
        "(SELECT count(*) FROM refined.pedidos), "
        "(SELECT count(*) FROM raw.itens_pedido), "
        "(SELECT count(*) FROM refined.itens_pedido)"
    ).fetchone()
    con.close()
    assert contagens == (99441, 99441, 112650, 112650)


def test_raw_entra_como_varchar():
    con = duckdb.connect(str(BANCOS), read_only=True)
    tipos = con.execute(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema = 'raw' AND data_type <> 'VARCHAR'"
    ).fetchone()[0]
    con.close()
    assert tipos == 0


def test_marts_tem_linhas():
    con = duckdb.connect(str(BANCOS), read_only=True)
    vazios = con.execute(
        "SELECT count(*) FROM information_schema.tables t "
        "WHERE t.table_schema = 'marts' "
        "AND (SELECT count(*) FROM marts.vendas_mensais) = 0"
    ).fetchone()[0]
    con.close()
    assert vazios == 0
