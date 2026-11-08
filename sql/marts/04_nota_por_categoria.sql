CREATE OR REPLACE TABLE marts.nota_por_categoria AS
WITH notas_por_pedido_categoria AS (
    SELECT DISTINCT
           a.pedido_id,
           a.nota,
           coalesce(t.categoria_ingles, pr.categoria, 'sem_categoria') AS categoria
    FROM refined.avaliacoes a
    JOIN refined.pedidos p ON p.pedido_id = a.pedido_id
    JOIN refined.itens_pedido i ON i.pedido_id = p.pedido_id
    JOIN refined.produtos pr ON pr.produto_id = i.produto_id
    LEFT JOIN refined.traducao_categorias t ON t.categoria = pr.categoria
)
SELECT categoria,
       round(avg(nota), 2) AS nota_media,
       count(*) AS avaliacoes
FROM notas_por_pedido_categoria
GROUP BY 1
ORDER BY nota_media;
