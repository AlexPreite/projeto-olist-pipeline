CREATE OR REPLACE TABLE marts.ticket_medio_por_estado AS
SELECT c.uf,
       count(DISTINCT p.pedido_id) AS pedidos,
       round(sum(i.preco + i.frete) / count(DISTINCT p.pedido_id), 2) AS ticket_medio
FROM refined.pedidos p
JOIN refined.clientes c ON c.cliente_id = p.cliente_id
JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id
GROUP BY c.uf
ORDER BY ticket_medio DESC;
