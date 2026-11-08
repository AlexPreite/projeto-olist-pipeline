CREATE OR REPLACE TABLE marts.top_categorias AS
SELECT coalesce(t.categoria_ingles, pr.categoria, 'sem_categoria') AS categoria,
       count(*) AS itens,
       round(sum(i.preco), 2) AS receita
FROM refined.itens_pedido i
JOIN refined.produtos pr ON pr.produto_id = i.produto_id
LEFT JOIN refined.traducao_categorias t ON t.categoria = pr.categoria
GROUP BY 1
ORDER BY receita DESC;
