CREATE OR REPLACE TABLE marts.recompra AS
SELECT cast(faixa AS VARCHAR) AS faixa,
       count(*) AS clientes
FROM (
    SELECT c.cliente_unico_id,
           count(*) AS faixa
    FROM refined.clientes c
    JOIN refined.pedidos p ON p.cliente_id = c.cliente_id
    GROUP BY c.cliente_unico_id
) clientes_por_pessoa
GROUP BY faixa
ORDER BY faixa;
