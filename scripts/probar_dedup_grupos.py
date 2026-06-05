"""Verifica si deduplicar stg_grupos_subgrupos cierra el gap del excedente."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


REF_USUARIO = {2023: 348, 2024: 2541, 2025: 1760}


def main():
    con = conectar(read_only=True)

    print("=" * 90)
    print("Excedente con dedup en stg_grupos_subgrupos vs sin dedup")
    print("=" * 90)

    sin_dedup = con.execute("""
        SELECT m.anio, ROUND(-SUM(m.movimiento)/1e6, 0) AS pyl
        FROM contabilidad.fact_movimiento_contable m
        LEFT JOIN contabilidad.stg_grupos_subgrupos g
               ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
        WHERE g.grupo IS NOT NULL AND g.grupo != 'LQORDER'
          AND m.anio BETWEEN 2023 AND 2025
        GROUP BY m.anio ORDER BY m.anio
    """).fetchall()

    con_dedup = con.execute("""
        WITH g_unico AS (
            SELECT DISTINCT id, anio_archivo, grupo, subgrupo
            FROM contabilidad.stg_grupos_subgrupos
        )
        SELECT m.anio, ROUND(-SUM(m.movimiento)/1e6, 0) AS pyl
        FROM contabilidad.fact_movimiento_contable m
        LEFT JOIN g_unico g
               ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
        WHERE g.grupo IS NOT NULL AND g.grupo != 'LQORDER'
          AND m.anio BETWEEN 2023 AND 2025
        GROUP BY m.anio ORDER BY m.anio
    """).fetchall()

    print(f"  {'anio':>4s}  {'sin_dedup':>10s}  {'con_dedup':>10s}  {'usuario':>10s}  {'diff_dedup':>11s}")
    sd = {int(r[0]): float(r[1]) for r in sin_dedup}
    cd = {int(r[0]): float(r[1]) for r in con_dedup}
    for anio in (2023, 2024, 2025):
        diff = cd[anio] - REF_USUARIO[anio]
        print(f"  {anio:>4}  {sd[anio]:>10,.0f}  {cd[anio]:>10,.0f}  {REF_USUARIO[anio]:>10,.0f}  {diff:>11,.0f}")

    con.close()


if __name__ == "__main__":
    main()
