CREATE OR REPLACE TABLE marts.entrega_no_prazo AS
SELECT
    count(*) FILTER (WHERE data_entrega <= data_estimada) AS no_prazo,
    count(*) FILTER (WHERE data_entrega > data_estimada) AS atrasados,
    count(*) FILTER (WHERE data_entrega IS NOT NULL) AS entregues,
    round(100.0 * count(*) FILTER (WHERE data_entrega <= data_estimada)
        / nullif(count(*) FILTER (WHERE data_entrega IS NOT NULL), 0), 2) AS percentual_no_prazo
FROM refined.pedidos
WHERE status = 'delivered';
