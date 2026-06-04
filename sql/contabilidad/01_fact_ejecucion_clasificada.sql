-- Vista que une cada movimiento contable con su Grupo/Subgrupo via clave_grupo.
-- Es la base de todos los analisis del modulo de Presupuesto.

CREATE OR REPLACE VIEW contabilidad.fact_ejecucion_clasificada AS
SELECT
    m.*,
    g.grupo,
    g.subgrupo
FROM contabilidad.fact_movimiento_contable m
LEFT JOIN contabilidad.stg_grupos_subgrupos g
       ON m.clave_grupo = g.id
      AND m.anio = g.anio_archivo;
