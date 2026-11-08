CREATE OR REPLACE TABLE marts.vendas_mensais AS
SELECT date_trunc('month', p.data_compra)::DATE AS mes,
       count(*) AS pedidos,
       round(sum(i.preco + i.frete), 2) AS receita,
       round(avg(i.preco + i.frete), 2) AS ticket_medio
FROM refined.pedidos p
JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY 1
ORDER BY 1;
