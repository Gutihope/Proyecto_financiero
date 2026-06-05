"""Orquestador del ETL — carga todas las fuentes al DuckDB de forma idempotente."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar
from src.etl.dims.cargar import cargar_dims
from src.etl.contabilidad.cargar_movimiento import cargar_movimiento_contable
from src.etl.contabilidad.cargar_grupos import cargar_grupos_subgrupos
from src.etl.contabilidad.crear_vistas import crear_vistas


def banner(titulo: str) -> None:
    print("\n" + "=" * 80)
    print(titulo)
    print("=" * 80)


def main():
    t0 = time.perf_counter()
    con = conectar()
    try:
        banner("DIMENSIONES")
        cargar_dims(con)

        banner("MOVIMIENTO CONTABLE (Excel raw del aplicativo)")
        cargar_movimiento_contable(con)

        banner("GRUPOS Y SUBGRUPOS")
        cargar_grupos_subgrupos(con)

        banner("VISTAS")
        crear_vistas(con)

        banner("VERIFICACION")
        total_mov = con.execute(
            "SELECT COUNT(*) FROM contabilidad.fact_movimiento_contable"
        ).fetchone()[0]
        total_grp = con.execute(
            "SELECT COUNT(*) FROM contabilidad.stg_grupos_subgrupos"
        ).fetchone()[0]
        print(f"  fact_movimiento_contable: {total_mov:>12,} filas")
        print(f"  stg_grupos_subgrupos:     {total_grp:>12,} filas")

        anios_grp = [r[0] for r in con.execute(
            "SELECT DISTINCT anio_archivo FROM contabilidad.stg_grupos_subgrupos "
            "ORDER BY 1"
        ).fetchall()]
        print(f"  Años con Grupos cargados: {anios_grp}")

        print("\n  Cobertura del join clave_grupo por año:")
        cobertura = con.execute("""
            SELECT m.anio,
                   COUNT(*) AS filas_mov,
                   COUNT(g.id) AS con_grupo,
                   ROUND(100.0 * COUNT(g.id) / COUNT(*), 2) AS pct
            FROM contabilidad.fact_movimiento_contable m
            LEFT JOIN contabilidad.stg_grupos_subgrupos g
                   ON m.clave_grupo = g.id AND m.anio = g.anio_archivo
            GROUP BY m.anio
            ORDER BY m.anio
        """).fetchall()
        print(f"    {'anio':>6}  {'filas_mov':>12}  {'con_grupo':>12}  {'pct':>8}")
        for fila in cobertura:
            print(f"    {fila[0]:>6}  {fila[1]:>12,}  {fila[2]:>12,}  {fila[3]:>7}%")
    finally:
        con.close()

    print(f"\nETL completado en {time.perf_counter() - t0:.1f}s")


if __name__ == "__main__":
    main()
