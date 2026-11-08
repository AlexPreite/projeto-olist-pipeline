"""Dashboard Streamlit da operação Olist.

O aplicativo somente lê ``olist.duckdb`` e os marts já materializados. Rode
primeiro ingestão, transformação e marts; assim a tela não contém regra de
negócio escondida e pode ser auditada diretamente no SQL.
"""

from pathlib import Path

import duckdb
import streamlit as st

CAMINHO_BANCO = Path(__file__).resolve().parent / "olist.duckdb"

st.set_page_config(page_title="Olist | Visão da operação", layout="wide")
st.title("Olist · visão da operação")
st.caption("Indicadores calculados a partir da camada marts")


@st.cache_resource
def conectar():
    if not CAMINHO_BANCO.is_file():
        raise FileNotFoundError(
            "Banco não encontrado. Execute o pipeline antes do dashboard."
        )
    return duckdb.connect(str(CAMINHO_BANCO), read_only=True)


@st.cache_data
def consultar(sql: str):
    return conectar().execute(sql).fetchdf()


def moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


try:
    receita = consultar(
        "SELECT coalesce(sum(receita), 0) AS valor FROM marts.vendas_mensais"
    ).iloc[0, 0]
    pedidos = consultar(
        "SELECT coalesce(sum(pedidos), 0) AS valor FROM marts.vendas_mensais"
    ).iloc[0, 0]
    prazo = consultar(
        "SELECT percentual_no_prazo FROM marts.entrega_no_prazo"
    ).iloc[0, 0]
    nota = consultar(
        "SELECT avg(nota_media) AS valor FROM marts.nota_por_categoria"
    ).iloc[0, 0]
    tempo = consultar(
        "SELECT avg(dias_medio) AS valor FROM marts.tempo_entrega_por_estado"
    ).iloc[0, 0]
    recompra = consultar(
        "SELECT clientes FROM marts.recompra WHERE faixa <> '1'"
    )["clientes"].sum()
    total_clientes = consultar(
        "SELECT count(DISTINCT cliente_unico_id) FROM refined.clientes"
    ).iloc[0, 0]

    cards = st.columns(7)
    cards[0].metric("Receita", moeda(receita))
    cards[1].metric("Pedidos", f"{pedidos:,.0f}".replace(",", "."))
    cards[2].metric("No prazo", f"{prazo:.1f}%")
    cards[3].metric("Nota média", f"{nota:.2f}")
    cards[4].metric("Dias até entregar", f"{tempo:.1f}")
    cards[5].metric("Recompra", f"{100 * recompra / total_clientes:.1f}%")
    cards[6].metric("Clientes", f"{total_clientes:,.0f}".replace(",", "."))

    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("01 · Faturamento mensal")
        mensal = consultar(
            "SELECT mes, receita FROM marts.vendas_mensais ORDER BY mes"
        ).set_index("mes")
        st.line_chart(mensal)
    with direita:
        st.subheader("02 · Receita por categoria")
        categorias = consultar(
            "SELECT categoria, receita FROM marts.top_categorias "
            "ORDER BY receita DESC LIMIT 15"
        ).set_index("categoria")
        st.bar_chart(categorias)

    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("06 · Ticket médio por estado")
        estados = consultar(
            "SELECT uf, ticket_medio FROM marts.ticket_medio_por_estado "
            "ORDER BY ticket_medio DESC"
        ).set_index("uf")
        st.bar_chart(estados)
    with direita:
        st.subheader("07 · Mix de pagamento")
        pagamentos = consultar(
            "SELECT tipo, valor FROM marts.mix_pagamento ORDER BY valor DESC"
        ).set_index("tipo")
        st.bar_chart(pagamentos)

    st.subheader("09 · Concentração de receita por vendedor")
    pareto = consultar(
        "SELECT posicao, percentual_acumulado FROM marts.vendedores_pareto "
        "WHERE posicao <= 1000 ORDER BY posicao"
    ).set_index("posicao")
    st.line_chart(pareto)
except FileNotFoundError as erro:
    st.error(str(erro))
except duckdb.Error as erro:
    mensagem = str(erro)
    if "already being used" in mensagem or "already open" in mensagem:
        mensagem = (
            "O banco está aberto por outro processo. Feche o ui.py ou qualquer "
            "execução do pipeline e atualize esta página."
        )
    st.error(f"Não foi possível ler os marts: {mensagem}")
