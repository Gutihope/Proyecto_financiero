def crear_vistas(con) -> None:
    con.execute("""
        CREATE OR REPLACE VIEW contabilidad.fact_ejecucion_clasificada AS
        SELECT m.*, g.grupo, g.subgrupo
        FROM contabilidad.fact_movimiento_contable m
        LEFT JOIN contabilidad.stg_grupos_subgrupos g
               ON m.clave_grupo = g.id
              AND m.anio = g.anio_archivo
    """)
    print("  vista contabilidad.fact_ejecucion_clasificada")
