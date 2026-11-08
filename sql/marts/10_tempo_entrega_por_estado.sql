CREATE OR REPLACE TABLE marts.tempo_entrega_por_estado AS
SELECT c.uf,
       count(*) AS entregues,
       round(avg(date_diff('day', p.data_compra, p.data_entrega)), 1) AS dias_medio,
       median(date_diff('day', p.data_compra, p.data_entrega)) AS dias_mediana
FROM refined.pedidos p
JOIN refined.clientes c ON c.cliente_id = p.cliente_id
WHERE p.status = 'delivered' AND p.data_entrega IS NOT NULL
GROUP BY c.uf
ORDER BY dias_medio;
