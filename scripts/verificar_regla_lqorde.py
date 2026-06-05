"""Verifica la regla: fuente=LQORDE -> grupo=LQORDER (override).

Compara el grupo asignado por el JOIN actual contra lo que dice esta regla.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)

    print("=" * 90)
    print("1) Filas de Movimiento con fuente=LQORDE pero grupo asignado != LQORDER")
    print("=" * 90)
    rows = con.execute("""
        SELECT m.anio, ANY_VALUE(g.grupo) AS grupo_actual,
               COUNT(*) AS n,
               ROUND(SUM(m.movimiento)/1e6, 1) AS mill_raw
        FROM contabilidad.fact_movimiento_contable m
        LEFT JOIN contabilidad.stg_grupos_subgrupos g
               ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
        WHERE UPPER(m.fuente) LIKE 'LQORDE%'
          AND (g.grupo IS NULL OR g.grupo != 'LQORDER')
        GROUP BY m.anio, g.grupo
        ORDER BY m.anio, ABS(SUM(m.movimiento)) DESC
    """).fetchall()
    print(f"  {'anio':>4s}  {'grupo':<35s}  {'n':>8s}  {'mill':>12s}")
    for r in rows:
        print(f"  {r[0]:>4}  {(r[1] or 'NULL')[:35]:<35s}  {r[2]:>8,}  {r[3]:>12,.1f}")
    if not rows:
        print("  (ninguna - el JOIN ya respeta esta regla)")

    print("\n" + "=" * 90)
    print("2) Duplicados en stg_grupos_subgrupos: misma clave con grupos distintos")
    print("=" * 90)
    rows = con.execute("""
        WITH duplicados AS (
            SELECT id, anio_archivo, COUNT(*) AS n_apariciones,
                   COUNT(DISTINCT grupo) AS n_grupos_distintos
            FROM contabilidad.stg_grupos_subgrupos
            GROUP BY id, anio_archivo
            HAVING COUNT(*) > 1
        )
        SELECT anio_archivo,
               COUNT(*) AS claves_duplicadas,
               SUM(n_apariciones) AS total_filas_duplicadas,
               COUNT(*) FILTER (WHERE n_grupos_distintos > 1) AS claves_con_grupos_diferentes
        FROM duplicados
        GROUP BY anio_archivo ORDER BY anio_archivo
    """).fetchall()
    print(f"  {'anio':>4s}  {'claves_dup':>12s}  {'filas_dup':>12s}  {'con_grupos_diferentes':>22s}")
    for r in rows:
        print(f"  {r[0]:>4}  {r[1]:>12,}  {r[2]:>12,}  {r[3]:>22,}")

    print("\n" + "=" * 90)
    print("3) Impacto de aplicar la regla LQORDE=>LQORDER sobre el excedente 2024")
    print("=" * 90)
    sin_regla = con.execute("""
        SELECT ROUND(-SUM(m.movimiento)/1e6, 0) AS pyl
        FROM contabilidad.fact_movimiento_contable m
        LEFT JOIN contabilidad.stg_grupos_subgrupos g
               ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
        WHERE m.anio = 2024
          AND g.grupo IS NOT NULL AND g.grupo != 'LQORDER'
    """).fetchone()[0]

    con_regla = con.execute("""
        WITH clasificado AS (
            SELECT
                m.*,
                CASE
                    WHEN UPPER(m.fuente) LIKE 'LQORDE%' THEN 'LQORDER'
                    ELSE g.grupo
                END AS grupo_final
            FROM contabilidad.fact_movimiento_contable m
            LEFT JOIN contabilidad.stg_grupos_subgrupos g
                   ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
        )
        SELECT ROUND(-SUM(movimiento)/1e6, 0) AS pyl
        FROM clasificado
        WHERE anio = 2024
          AND grupo_final IS NOT NULL AND grupo_final != 'LQORDER'
    """).fetchone()[0]

    print(f"  Sin regla (actual):     {sin_regla:>10,.0f} M  (usuario tiene 2,541)")
    print(f"  Con regla LQORDE override: {con_regla:>10,.0f} M")
    print(f"  Diff vs usuario:         {con_regla - 2541:>10,.0f} M")

    con.close()


if __name__ == "__main__":
    main()
