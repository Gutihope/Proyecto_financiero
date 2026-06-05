-- Vista que une cada movimiento contable con su Grupo/Subgrupo.
-- Es la base de todos los analisis del modulo de Presupuesto.
--
-- Dos detalles criticos para que el excedente cuadre con el reporte
-- transformado del usuario:
--
-- 1) Dedup de stg_grupos_subgrupos:
--    El archivo Grupos&Subgrupos trae 191-332 filas duplicadas por anio
--    (misma clave, mismo grupo, repetidas). Sin SELECT DISTINCT el LEFT JOIN
--    multiplicaba los movimientos por la cantidad de duplicados. La regla
--    "una clave -> un grupo" la garantiza el SELECT DISTINCT.
--
-- 2) Override por fuente LQORDE:
--    Regla de negocio: si fuente es LQORDE el grupo debe ser LQORDER
--    siempre, sin importar lo que diga el archivo de Grupos. Se aplica
--    como CASE de seguridad (aunque hoy la regla ya viene cumplida desde
--    el archivo de Grupos, asi se sostiene si cambian los datos).

CREATE OR REPLACE VIEW contabilidad.fact_ejecucion_clasificada AS
SELECT
    m.*,
    CASE
        WHEN UPPER(m.fuente) LIKE 'LQORDE%' THEN 'LQORDER'
        ELSE g.grupo
    END AS grupo,
    CASE
        WHEN UPPER(m.fuente) LIKE 'LQORDE%' THEN 'Lqorder'
        ELSE g.subgrupo
    END AS subgrupo
FROM contabilidad.fact_movimiento_contable m
LEFT JOIN (
    SELECT DISTINCT id, anio_archivo, grupo, subgrupo
    FROM contabilidad.stg_grupos_subgrupos
) g ON m.clave_grupo = g.id AND m.anio = g.anio_archivo;
