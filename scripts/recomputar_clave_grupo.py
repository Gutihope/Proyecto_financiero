"""Recomputa clave_grupo en fact_movimiento_contable sin re-leer Excel.

Uso: cuando cambia la logica de construccion (p.ej., separador decimal),
permite actualizar en sitio sin re-ejecutar el ETL completo.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


SQL_RECOMPUTAR = """
UPDATE contabilidad.fact_movimiento_contable
SET clave_grupo =
    COALESCE(cuenta, '')
    || COALESCE(centro_de_responsabilidad, '')
    || COALESCE(tercero, '')
    || COALESCE(comprobante, '')
    || COALESCE(documento_referencia, '')
    || CAST(mes AS VARCHAR)
    || CASE
         WHEN movimiento IS NULL THEN ''
         WHEN movimiento = CAST(movimiento AS BIGINT)
              THEN CAST(CAST(movimiento AS BIGINT) AS VARCHAR)
         ELSE REPLACE(
                RTRIM(RTRIM(printf('%.2f', movimiento), '0'), '.'),
                '.', ','
              )
       END
    || COALESCE(fuente, '')
"""


def main():
    t0 = time.perf_counter()
    con = conectar()
    try:
        print("Recomputando clave_grupo en fact_movimiento_contable...")
        con.execute(SQL_RECOMPUTAR)
        print(f"  hecho en {time.perf_counter() - t0:.1f}s")

        print("\nCobertura del join por anio (semi-join, sin inflar):")
        rows = con.execute("""
            SELECT m.anio,
                   COUNT(*) AS filas,
                   SUM(CASE WHEN EXISTS (
                       SELECT 1 FROM contabilidad.stg_grupos_subgrupos g
                       WHERE g.id = m.clave_grupo AND g.anio_archivo = m.anio
                   ) THEN 1 ELSE 0 END) AS con_grupo
            FROM contabilidad.fact_movimiento_contable m
            GROUP BY m.anio
            ORDER BY m.anio
        """).fetchall()
        print(f"  {'anio':>6}  {'filas':>10}  {'con_grupo':>10}  {'pct':>7}")
        for r in rows:
            pct = round(100.0 * r[2] / r[1], 2) if r[1] else 0
            print(f"  {r[0]:>6}  {r[1]:>10,}  {r[2]:>10,}  {pct:>6}%")
    finally:
        con.close()


if __name__ == "__main__":
    main()
