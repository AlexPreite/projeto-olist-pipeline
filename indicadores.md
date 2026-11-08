# Indicadores do projeto

1. Receita e pedidos por mês — `pedidos` + `itens_pedido` — evolução da operação.
2. Categorias com maior receita — `itens_pedido` + `produtos` — mix vendido.
3. Percentual entregue no prazo — `pedidos` — qualidade logística.
4. Nota média por categoria — `avaliacoes` + `pedidos` + `itens_pedido` + `produtos`.
5. Clientes com recompra — `clientes` + `pedidos` — retenção por pessoa real.
6. Ticket médio por estado — `clientes` + `pedidos` + `itens_pedido`.
7. Mix de pagamentos — `pagamentos` — formas e valor transacionado.
8. Nota por prazo — `pedidos` + `avaliacoes` — relação entre atraso e satisfação.
9. Pareto de vendedores — `itens_pedido` + `vendedores` — concentração da receita.
10. Tempo de entrega por estado — `clientes` + `pedidos` — experiência regional.

Margem de lucro, custo de aquisição e estoque não entram: o dataset não possui
custo, investimento de marketing ou saldo de inventário.
