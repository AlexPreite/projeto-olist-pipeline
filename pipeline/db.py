"""Infraestrutura DuckDB da primeira etapa do pipeline Olist.

Esta etapa expõe somente a conexão, a criação de schemas e a gravação de
DataFrames. Ela não lê arquivos nem conhece regras de negócio, porque as
etapas seguintes precisam decidir tipos e transformações explicitamente.

As paths são calculadas a partir deste arquivo, e não do diretório corrente,
para que uma execução iniciada em outra pasta não crie um banco vazio no local
errado. As tabelas são recriadas para que reexecutar o pipeline seja seguro.
"""

from pathlib import Path

import duckdb
import pandas as pd

_PASTA_PROJETO = Path(__file__).resolve().parent.parent
PASTA_RAW = _PASTA_PROJETO / "raw"
_CAMINHO_BANCO = _PASTA_PROJETO / "olist.duckdb"


def conectar() -> duckdb.DuckDBPyConnection:
    """Abre o banco da raiz do projeto; quem chama deve fechá-lo."""
    return duckdb.connect(str(_CAMINHO_BANCO))


def criar_schema(con: duckdb.DuckDBPyConnection, nome: str) -> None:
    """Cria um schema se ele ainda não existir."""
    con.execute(f'CREATE SCHEMA IF NOT EXISTS "{nome}"')


def gravar(
    con: duckdb.DuckDBPyConnection,
    df: pd.DataFrame,
    schema: str,
    tabela: str,
) -> int:
    """Recria uma tabela com os dados e tipos presentes no DataFrame."""
    nome_temporario = "_dados_para_gravar"
    con.register(nome_temporario, df)
    try:
        con.execute(
            f'CREATE OR REPLACE TABLE "{schema}"."{tabela}" '
            f"AS SELECT * FROM {nome_temporario}"
        )
    finally:
        con.unregister(nome_temporario)

    try:
        linhas = con.execute(
            f'SELECT count(*) FROM "{schema}"."{tabela}"'
        ).fetchall()
        return int(linhas[0][0])
    finally:
        df = None
