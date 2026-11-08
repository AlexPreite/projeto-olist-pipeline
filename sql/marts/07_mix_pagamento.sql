CREATE OR REPLACE TABLE marts.mix_pagamento AS
SELECT tipo,
       count(*) AS pagamentos,
       round(sum(valor), 2) AS valor,
       round(100.0 * sum(valor) / sum(sum(valor)) OVER (), 2) AS percentual
FROM refined.pagamentos
WHERE tipo <> 'not_defined'
GROUP BY tipo
ORDER BY valor DESC;
