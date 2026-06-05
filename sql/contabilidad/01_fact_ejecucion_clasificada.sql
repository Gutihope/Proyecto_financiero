-- Vista base de los analisis del modulo de Presupuesto.
-- Une cada movimiento contable con su Grupo/Subgrupo via clave_grupo.
--
-- Reglas aplicadas AQUI (filtrado y normalizacion previa a toda metrica):
--
-- 1) Exclusion de LQORDE
--    fuente LIKE 'LQORDE%' se excluye antes de cualquier calculo.
--    Por regla de negocio, las liquidaciones de ordenes siempre suman
--    cero (cada movimiento positivo tiene su contrapartida negativa) y
--    no aportan informacion analitica.
--
-- 2) Dedup de stg_grupos_subgrupos
--    El archivo Grupos&Subgrupos trae 191-332 filas duplicadas por anio
--    (misma clave, mismo grupo, repetidas). Sin SELECT DISTINCT el LEFT
--    JOIN multiplicaba los movimientos. El DISTINCT garantiza una sola
--    fila por (clave_grupo, anio).
--
-- Despues de estas dos reglas, todas las queries downstream solo necesitan
-- filtrar grupo IS NOT NULL (para excluir anios sin Grupos cargados).

CREATE OR REPLACE VIEW contabilidad.fact_ejecucion_clasificada AS
SELECT
    m.*,
    g.grupo,
    g.subgrupo
FROM contabilidad.fact_movimiento_contable m
LEFT JOIN (
    SELECT DISTINCT id, anio_archivo, grupo, subgrupo
    FROM contabilidad.stg_grupos_subgrupos
) g ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
WHERE UPPER(m.fuente) NOT LIKE 'LQORDE%';
