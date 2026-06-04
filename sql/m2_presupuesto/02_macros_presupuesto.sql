-- Macros (table-valued functions) para generar el presupuesto del anio destino.
-- Se invocan desde DuckDB CLI o cualquier conexion:
--   SELECT * FROM presupuesto.proyectar_promedio(2026, 3);
--   SELECT * FROM presupuesto.proyectar_promedio(2026, 1);  -- solo anio anterior

------------------------------------------------------------
-- Promedio mensual de ejecucion sobre los ULTIMOS n_anios
-- por (cuenta, centro_de_responsabilidad, grupo, subgrupo, mes).
-- Filtros estandar: excluye LQORDER y movimientos sin grupo.
-- Divisor estricto = n_anios. El total del presupuesto generado equivale al
-- promedio aritmetico de los totales anuales de los n_anios historicos.
------------------------------------------------------------
CREATE OR REPLACE MACRO presupuesto.proyectar_promedio(anio_destino, n_anios) AS TABLE
SELECT
    anio_destino                                  AS anio,
    cuenta,
    centro_de_responsabilidad,
    grupo,
    subgrupo,
    mes,
    SUM(movimiento) / n_anios::DOUBLE             AS movimiento
FROM contabilidad.fact_ejecucion_clasificada
WHERE anio BETWEEN anio_destino - n_anios AND anio_destino - 1
  AND grupo IS NOT NULL
  AND grupo != 'LQORDER'
GROUP BY cuenta, centro_de_responsabilidad, grupo, subgrupo, mes;
