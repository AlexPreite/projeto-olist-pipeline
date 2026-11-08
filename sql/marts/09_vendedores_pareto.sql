CREATE OR REPLACE TABLE marts.vendedores_pareto AS
WITH receita AS (
    SELECT vendedor_id, round(sum(preco + frete), 2) AS receita
    FROM refined.itens_pedido
    GROUP BY vendedor_id
)
SELECT vendedor_id,
       receita,
       row_number() OVER (ORDER BY receita DESC) AS posicao,
       round(100.0 * sum(receita) OVER (ORDER BY receita DESC)
           / sum(receita) OVER (), 2) AS percentual_acumulado
FROM receita
ORDER BY posicao;
