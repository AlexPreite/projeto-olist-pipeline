"""Dashboard Streamlit da operação Olist."""

from pathlib import Path

import altair as alt
import duckdb
import streamlit as st

CAMINHO_BANCO = Path(__file__).resolve().parent / "olist.duckdb"
PALETA = ["#6C5CE7", "#00B894", "#FDCB6E", "#E17055", "#0984E3", "#A29BFE"]

st.set_page_config(
    page_title="Olist | Centro de performance",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

    :root { --ink: #1f2340; --muted: #737895; --purple: #6c5ce7; }
    .stApp { background: #f7f8fc; color: var(--ink); }
    [data-testid="stHeader"] { background: rgba(247,248,252,.9); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #211d4d 0%, #30286d 100%); }
    [data-testid="stSidebar"] * { color: #f7f8fc !important; }
    .block-container { max-width: 1440px; padding: 2.5rem 3.5rem 4rem; }
    h1, h2, h3, [data-testid="stMetricValue"] { font-family: 'Space Grotesk', sans-serif; }
    h1 { font-size: 2.35rem; letter-spacing: -0.05em; margin-bottom: .2rem; }
    h2 { font-size: 1.15rem; letter-spacing: -0.02em; }
    [data-testid="stMetric"] {
        background: white; border: 1px solid #ececf5; border-radius: 16px;
        padding: 1rem 1.15rem; box-shadow: 0 7px 22px rgba(37,34,83,.06);
    }
    [data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ink); font-size: 1.55rem; }
    .hero {
        background: linear-gradient(112deg, #28235e 0%, #5949bd 58%, #7b6ff0 100%);
        border-radius: 22px; color: white; padding: 1.8rem 2rem; margin-bottom: 1.6rem;
        box-shadow: 0 16px 35px rgba(71,58,158,.2);
    }
    .hero h1 { color: white; margin: 0; }
    .hero p { color: #e5e3ff; margin: .45rem 0 0; }
    .section-label {
        color: var(--purple); font-size: .73rem; font-weight: 700;
        letter-spacing: .12em; text-transform: uppercase; margin: 1.9rem 0 .45rem;
    }
    .chart-card {
        background: white; border: 1px solid #ececf5; border-radius: 18px;
        padding: .8rem 1rem .35rem; box-shadow: 0 7px 22px rgba(37,34,83,.05);
    }
    .chart-card h3 { margin: 0; font-size: 1.02rem; }
    .chart-card p { color: var(--muted); font-size: .78rem; margin: .2rem 0 0; }
    footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


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


def grafico(base: alt.Chart, altura: int = 280) -> None:
    st.altair_chart(
        base.properties(height=altura)
        .configure_view(stroke=None)
        .configure_axis(
            labelColor="#737895",
            titleColor="#737895",
            gridColor="#eeeef5",
            domain=False,
        )
        .configure_legend(labelColor="#737895", titleColor="#737895"),
        use_container_width=True,
    )


def lista_sql(valores: list[str]) -> str:
    """Converte opções escolhidas em uma lista SQL segura."""
    return ", ".join("'" + valor.replace("'", "''") + "'" for valor in valores)


@st.cache_data
def opcoes_filtros():
    return {
        "categorias": consultar(
            "SELECT DISTINCT categoria FROM refined.produtos "
            "WHERE categoria IS NOT NULL ORDER BY categoria"
        )["categoria"].tolist(),
        "produtos": consultar(
            "SELECT produto_id FROM refined.produtos ORDER BY produto_id"
        )["produto_id"].tolist(),
        "estados": consultar(
            "SELECT DISTINCT uf FROM refined.clientes WHERE uf IS NOT NULL ORDER BY uf"
        )["uf"].tolist(),
        "pagamentos": consultar(
            "SELECT DISTINCT tipo FROM refined.pagamentos ORDER BY tipo"
        )["tipo"].tolist(),
    }


def pedidos_filtrados_sql() -> str:
    """CTE comum: filtros são aplicados no nível do pedido, sem duplicar métricas."""
    filtros = [
        f"p.data_compra::DATE BETWEEN DATE '{data_inicio}' AND DATE '{data_fim}'"
    ]
    if categorias_selecionadas:
        filtros.append(f"pr.categoria IN ({lista_sql(categorias_selecionadas)})")
    if produtos_selecionados:
        filtros.append(f"pr.produto_id IN ({lista_sql(produtos_selecionados)})")
    if estados_selecionados:
        filtros.append(f"c.uf IN ({lista_sql(estados_selecionados)})")
    if pagamentos_selecionados:
        filtros.append(f"(pg.tipo IN ({lista_sql(pagamentos_selecionados)}) OR pg.tipo IS NULL)")
    return f"""
        WITH pedidos_filtrados AS (
            SELECT DISTINCT p.*
            FROM refined.pedidos p
            JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id
            JOIN refined.produtos pr ON pr.produto_id = i.produto_id
            JOIN refined.clientes c ON c.cliente_id = p.cliente_id
            LEFT JOIN refined.pagamentos pg ON pg.pedido_id = p.pedido_id
            WHERE {" AND ".join(filtros)}
        )
    """


def consultar_filtrada(sql: str):
    return consultar(pedidos_filtrados_sql() + sql)


try:
    opcoes = opcoes_filtros()
    limites = consultar(
        "SELECT min(data_compra)::DATE AS inicio, max(data_compra)::DATE AS fim, "
        "year(min(data_compra)) AS ano_inicio, year(max(data_compra)) AS ano_fim "
        "FROM refined.pedidos"
    ).iloc[0]
    with st.sidebar:
        st.markdown("## OLIST **INSIGHTS**")
        st.caption("Centro de performance operacional")
        st.divider()
        st.markdown("### Filtros da análise")
        anos = ["Todas"] + list(
            range(int(limites["ano_inicio"]), int(limites["ano_fim"]) + 1)
        )
        safra = st.selectbox(
            "Safra / ano de compra",
            anos,
            format_func=lambda ano: "Todas as safras" if ano == "Todas" else str(ano),
            help="Selecione um ano para recalcular todos os indicadores.",
        )
        if safra == "Todas":
            data_inicio, data_fim = limites["inicio"], limites["fim"]
        else:
            data_inicio = f"{safra}-01-01"
            data_fim = f"{safra}-12-31"
        categorias_selecionadas = st.multiselect(
            "Categorias de produto",
            opcoes["categorias"],
            placeholder="Clique para carregar e selecionar",
            help="Deixe vazio para considerar todas as categorias.",
        )
        produtos_selecionados = st.multiselect(
            "Produtos",
            opcoes["produtos"],
            placeholder="Clique para carregar e selecionar",
            help="Digite no campo da lista para pesquisar por ID. Vazio = todos.",
        )
        estados_selecionados = st.multiselect(
            "Estados do cliente",
            opcoes["estados"],
            placeholder="Clique para carregar e selecionar",
            help="Vazio = todos os estados.",
        )
        pagamentos_selecionados = st.multiselect(
            "Forma de pagamento",
            opcoes["pagamentos"],
            placeholder="Clique para carregar e selecionar",
            help="Vazio = todas as formas de pagamento.",
        )
        st.divider()
        filtros_ativos = sum(
            bool(filtro)
            for filtro in (
                categorias_selecionadas,
                produtos_selecionados,
                estados_selecionados,
                pagamentos_selecionados,
            )
        )
        st.caption(
            f"{filtros_ativos} filtro(s) de lista ativo(s). "
            "Os gráficos são recalculados a cada seleção."
        )

    receita = consultar(
        pedidos_filtrados_sql()
        + "SELECT coalesce(sum(i.preco), 0) AS valor FROM pedidos_filtrados p "
        "JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id"
    ).iloc[0, 0]
    pedidos = consultar(
        pedidos_filtrados_sql()
        + "SELECT count(*) AS valor FROM pedidos_filtrados"
    ).iloc[0, 0]
    prazo = consultar(
        pedidos_filtrados_sql()
        + "SELECT 100.0 * count(*) FILTER (WHERE data_entrega <= data_estimada) "
        " / NULLIF(count(*) FILTER (WHERE data_entrega IS NOT NULL), 0) FROM pedidos_filtrados"
    ).iloc[0, 0]
    nota = consultar(
        pedidos_filtrados_sql()
        + "SELECT avg(a.nota) FROM refined.avaliacoes a "
        "JOIN pedidos_filtrados p ON p.pedido_id = a.pedido_id"
    ).iloc[0, 0]
    tempo = consultar(
        pedidos_filtrados_sql()
        + "SELECT avg(date_diff('day', data_compra, data_entrega)) "
        "FROM pedidos_filtrados WHERE data_entrega IS NOT NULL"
    ).iloc[0, 0]
    recompra = consultar(
        pedidos_filtrados_sql()
        + "SELECT count(*) FROM (SELECT p.cliente_id FROM pedidos_filtrados p "
        "GROUP BY p.cliente_id HAVING count(*) > 1)"
    ).iloc[0, 0]
    total_clientes = consultar(
        pedidos_filtrados_sql()
        + "SELECT count(DISTINCT c.cliente_unico_id) FROM refined.clientes c "
        "JOIN pedidos_filtrados p ON p.cliente_id = c.cliente_id"
    ).iloc[0, 0]

    with st.sidebar:
        st.markdown("### Navegação")
        st.markdown("**Visão geral**\n\nDesempenho comercial\n\nExperiência do cliente")
        st.divider()
        st.caption("Fonte: marts no DuckDB\nAtualização conforme o pipeline")

    st.markdown(
        '<div class="hero"><h1>Centro de performance</h1>'
        "<p>Uma visão executiva da operação, vendas e experiência dos clientes.</p></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Resumo executivo</div>', unsafe_allow_html=True)
    cards = st.columns(4)
    cards[0].metric("Receita total", moeda(receita), "vendas consolidadas")
    cards[1].metric("Pedidos", f"{pedidos:,.0f}".replace(",", "."), "volume processado")
    cards[2].metric("Entrega no prazo", f"{prazo:.1f}%", "nível de serviço")
    cards[3].metric("Clientes ativos", f"{total_clientes:,.0f}".replace(",", "."), "base identificada")
    cards = st.columns(3)
    cards[0].metric("Nota média", f"{nota:.2f} / 5", "avaliações")
    cards[1].metric("Tempo de entrega", f"{tempo:.1f} dias", "média por estado")
    cards[2].metric("Taxa de recompra", f"{100 * recompra / total_clientes:.1f}%", "clientes recorrentes")

    mensal = consultar(
        pedidos_filtrados_sql()
        + "SELECT date_trunc('month', p.data_compra)::DATE AS mes, "
        "sum(i.preco) AS receita, count(DISTINCT p.pedido_id) AS pedidos "
        "FROM pedidos_filtrados p JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id "
        "GROUP BY 1 ORDER BY 1"
    )
    categorias = consultar(
        pedidos_filtrados_sql()
        + "SELECT pr.categoria, sum(i.preco) AS receita "
        "FROM pedidos_filtrados p JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id "
        "JOIN refined.produtos pr ON pr.produto_id = i.produto_id "
        "GROUP BY 1 ORDER BY receita DESC LIMIT 12"
    )
    st.markdown('<div class="section-label">Performance comercial</div>', unsafe_allow_html=True)
    esquerda, direita = st.columns(2)
    with esquerda:
        st.markdown(
            '<div class="chart-card"><h3>Evolução de faturamento</h3>'
            "<p>Receita mensal ao longo do período analisado</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(mensal).mark_area(
                line={"color": PALETA[0], "strokeWidth": 3},
                color=alt.Gradient(
                    gradient="linear",
                    stops=[
                        alt.GradientStop(color="#6C5CE7", offset=0),
                        alt.GradientStop(color="#E9E6FF", offset=1),
                    ],
                    x1=1, x2=1, y1=0, y2=1,
                ),
            ).encode(
                x=alt.X("mes:T", title=None, axis=alt.Axis(format="%b %Y")),
                y=alt.Y("receita:Q", title="Receita (R$)", axis=alt.Axis(format="~s")),
                tooltip=[
                    alt.Tooltip("mes:T", title="Mês", format="%b %Y"),
                    alt.Tooltip("receita:Q", title="Receita", format=",.2f"),
                    alt.Tooltip("pedidos:Q", title="Pedidos", format=","),
                ],
            )
        )
    with direita:
        st.markdown(
            '<div class="chart-card"><h3>Categorias líderes</h3>'
            "<p>As 12 categorias com maior receita</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(categorias).mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6).encode(
                y=alt.Y("categoria:N", sort="-x", title=None),
                x=alt.X("receita:Q", title="Receita (R$)", axis=alt.Axis(format="~s")),
                color=alt.Color("receita:Q", scale=alt.Scale(range=PALETA), legend=None),
                tooltip=[
                    alt.Tooltip("categoria:N", title="Categoria"),
                    alt.Tooltip("receita:Q", title="Receita", format=",.2f"),
                ],
            )
        )

    st.markdown('<div class="section-label">Experiência e distribuição</div>', unsafe_allow_html=True)
    esquerda, direita = st.columns(2)
    with esquerda:
        estados = consultar(
            pedidos_filtrados_sql()
            + "SELECT c.uf, avg(date_diff('day', p.data_compra, p.data_entrega)) AS dias_medio, "
            "median(date_diff('day', p.data_compra, p.data_entrega)) AS dias_mediana "
            "FROM pedidos_filtrados p JOIN refined.clientes c ON c.cliente_id = p.cliente_id "
            "WHERE p.data_entrega IS NOT NULL GROUP BY c.uf ORDER BY dias_medio DESC"
        )
        st.markdown(
            '<div class="chart-card"><h3>Prazo médio por estado</h3>'
            "<p>Onde a operação precisa ganhar velocidade</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(estados).mark_bar(cornerRadiusTopRight=6).encode(
                y=alt.Y("uf:N", sort="-x", title=None),
                x=alt.X("dias_medio:Q", title="Dias", scale=alt.Scale(zero=False)),
                color=alt.condition(
                    alt.datum.dias_medio > tempo, alt.value("#E17055"), alt.value("#00B894")
                ),
                tooltip=[
                    alt.Tooltip("uf:N", title="Estado"),
                    alt.Tooltip("dias_medio:Q", title="Média", format=".1f"),
                    alt.Tooltip("dias_mediana:Q", title="Mediana", format=".1f"),
                ],
            )
        )
    with direita:
        pagamentos = consultar(
            pedidos_filtrados_sql()
            + "SELECT pg.tipo, sum(pg.valor) AS valor, "
            "100.0 * sum(pg.valor) / sum(sum(pg.valor)) OVER () AS percentual "
            "FROM refined.pagamentos pg JOIN pedidos_filtrados p ON p.pedido_id = pg.pedido_id "
            "GROUP BY pg.tipo ORDER BY valor DESC"
        )
        st.markdown(
            '<div class="chart-card"><h3>Mix de pagamentos</h3>'
            "<p>Participação no valor transacionado</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(pagamentos).mark_arc(innerRadius=62, outerRadius=105).encode(
                theta=alt.Theta("valor:Q"),
                color=alt.Color("tipo:N", scale=alt.Scale(range=PALETA), title="Método"),
                tooltip=[
                    alt.Tooltip("tipo:N", title="Método"),
                    alt.Tooltip("valor:Q", title="Valor", format=",.2f"),
                    alt.Tooltip("percentual:Q", title="Participação", format=".1f"),
                ],
            ),
            altura=280,
        )

    st.markdown('<div class="section-label">Retenção e concentração</div>', unsafe_allow_html=True)
    esquerda, direita = st.columns(2)
    with esquerda:
        prazo_nota = consultar(
            pedidos_filtrados_sql()
            + "SELECT CASE WHEN p.data_entrega <= p.data_estimada THEN 'no_prazo' "
            "ELSE 'atrasado' END AS prazo, avg(a.nota) AS nota_media "
            "FROM pedidos_filtrados p JOIN refined.avaliacoes a ON a.pedido_id = p.pedido_id "
            "WHERE p.data_entrega IS NOT NULL GROUP BY 1"
        )
        st.markdown(
            '<div class="chart-card"><h3>Satisfação x prazo</h3>'
            "<p>A experiência muda quando o pedido atrasa</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(prazo_nota).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
                x=alt.X("prazo:N", title=None),
                y=alt.Y("nota_media:Q", title="Nota média", scale=alt.Scale(domain=[0, 5])),
                color=alt.Color("prazo:N", scale=alt.Scale(range=["#00B894", "#E17055"]), legend=None),
                tooltip=[alt.Tooltip("prazo:N", title="Prazo"), alt.Tooltip("nota_media:Q", title="Nota", format=".2f")],
            )
        )
    with direita:
        pareto = consultar(
            pedidos_filtrados_sql()
            + ", receita_vendedor AS (SELECT i.vendedor_id, sum(i.preco) AS receita "
            "FROM pedidos_filtrados p JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id "
            "GROUP BY i.vendedor_id), ranking AS (SELECT row_number() OVER "
            "(ORDER BY receita DESC) AS posicao, receita FROM receita_vendedor) "
            "SELECT posicao, 100.0 * sum(receita) OVER (ORDER BY posicao) / sum(receita) OVER () "
            "AS percentual_acumulado FROM ranking WHERE posicao <= 1000 ORDER BY posicao"
        )
        st.markdown(
            '<div class="chart-card"><h3>Pareto de vendedores</h3>'
            "<p>Concentração acumulada da receita nos 1.000 principais</p></div>",
            unsafe_allow_html=True,
        )
        grafico(
            alt.Chart(pareto).mark_line(color=PALETA[4], strokeWidth=3).encode(
                x=alt.X("posicao:Q", title="Posição"),
                y=alt.Y("percentual_acumulado:Q", title="% acumulado", scale=alt.Scale(domain=[0, 100])),
                tooltip=[
                    alt.Tooltip("posicao:Q", title="Posição"),
                    alt.Tooltip("percentual_acumulado:Q", title="Acumulado", format=".1f"),
                ],
            )
        )
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
