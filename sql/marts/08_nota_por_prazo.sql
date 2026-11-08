CREATE OR REPLACE TABLE marts.nota_por_prazo AS
SELECT CASE WHEN p.data_entrega <= p.data_estimada THEN 'no_prazo'
            ELSE 'atrasado' END AS prazo,
       round(avg(a.nota), 2) AS nota_media,
       count(*) AS avaliacoes
FROM refined.pedidos p
JOIN refined.avaliacoes a ON a.pedido_id = p.pedido_id
WHERE p.status = 'delivered'
  AND p.data_entrega IS NOT NULL
  AND p.data_estimada IS NOT NULL
GROUP BY 1;
