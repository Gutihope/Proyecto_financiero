-- Vistas base de Ejecucion Presupuestal por GRUPO
-- Construidas sobre contabilidad.fact_ejecucion_clasificada.
-- WHERE grupo IS NOT NULL excluye movimientos sin clasificar (anios sin archivo de Grupos).

------------------------------------------------------------
-- 1) Por anio: el agregado mas simple, util para tendencias
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_x_grupo_anio AS
SELECT
    anio,
    grupo,
    subgrupo,
    COUNT(*)        AS n_movimientos,
    SUM(movimiento) AS valor_total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY anio, grupo, subgrupo;

------------------------------------------------------------
-- 2) Por anio y mes: granularidad mensual
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_x_grupo_anio_mes AS
SELECT
    anio,
    mes,
    grupo,
    subgrupo,
    COUNT(*)        AS n_movimientos,
    SUM(movimiento) AS valor_total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY anio, mes, grupo, subgrupo;

------------------------------------------------------------
-- 3) Por tercero: quien aporta/cuesta dentro de cada grupo
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_x_grupo_tercero AS
SELECT
    anio,
    grupo,
    subgrupo,
    tercero,
    ANY_VALUE(nombre_tercero) AS nombre_tercero,
    COUNT(*)        AS n_movimientos,
    SUM(movimiento) AS valor_total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY anio, grupo, subgrupo, tercero;

------------------------------------------------------------
-- 4) Por cuenta contable
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_x_grupo_cuenta AS
SELECT
    anio,
    grupo,
    subgrupo,
    cuenta,
    ANY_VALUE(nombre_cuenta) AS nombre_cuenta,
    COUNT(*)        AS n_movimientos,
    SUM(movimiento) AS valor_total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY anio, grupo, subgrupo, cuenta;

------------------------------------------------------------
-- 5) Por centro de costo (CeCo / Centro de Responsabilidad)
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_x_grupo_ceco AS
SELECT
    anio,
    grupo,
    subgrupo,
    centro_de_responsabilidad           AS centro_costo,
    ANY_VALUE(nombre_centro_de_responsabilidad) AS nombre_centro_costo,
    COUNT(*)        AS n_movimientos,
    SUM(movimiento) AS valor_total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY anio, grupo, subgrupo, centro_de_responsabilidad;

------------------------------------------------------------
-- 6) Pivot Grupo x Anio: cada grupo en una fila, anios como columnas
--    (vista que alimenta el submodulo "Ejecucion x grupo y x anios")
------------------------------------------------------------
CREATE OR REPLACE VIEW presupuesto.vw_ejecucion_pivot_grupo_anio AS
SELECT
    grupo,
    subgrupo,
    SUM(CASE WHEN anio = 2017 THEN movimiento ELSE 0 END) AS y2017,
    SUM(CASE WHEN anio = 2018 THEN movimiento ELSE 0 END) AS y2018,
    SUM(CASE WHEN anio = 2019 THEN movimiento ELSE 0 END) AS y2019,
    SUM(CASE WHEN anio = 2020 THEN movimiento ELSE 0 END) AS y2020,
    SUM(CASE WHEN anio = 2021 THEN movimiento ELSE 0 END) AS y2021,
    SUM(CASE WHEN anio = 2022 THEN movimiento ELSE 0 END) AS y2022,
    SUM(CASE WHEN anio = 2023 THEN movimiento ELSE 0 END) AS y2023,
    SUM(CASE WHEN anio = 2024 THEN movimiento ELSE 0 END) AS y2024,
    SUM(CASE WHEN anio = 2025 THEN movimiento ELSE 0 END) AS y2025,
    SUM(movimiento)                                       AS total
FROM contabilidad.fact_ejecucion_clasificada
WHERE grupo IS NOT NULL
GROUP BY grupo, subgrupo
ORDER BY grupo, subgrupo;
