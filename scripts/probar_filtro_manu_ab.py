"""Verifica si excluir 'origen=MANU AND fuente LIKE AB%' acerca el excedente al del usuario."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


REF_USUARIO_PYG_MILL = {2023: 348, 2024: 2541, 2025: 1760}


def excedente_con_filtro(con, filtro_extra: str = ""):
    """Excedente por anio con un filtro WHERE adicional opcional."""
    where_extra = f"AND ({filtro_extra})" if filtro_extra else ""
    rows = con.execute(f"""
        SELECT anio, ROUND(-SUM(movimiento)/1e6, 0) AS pyl_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE anio IN (2023, 2024, 2025)
          AND grupo IS NOT NULL AND grupo != 'LQORDER'
          {where_extra}
        GROUP BY anio ORDER BY anio
    """).fetchall()
    return {int(r[0]): float(r[1]) for r in rows}


def comparar(titulo, valores):
    print(f"\n  {titulo}")
    print(f"    {'anio':>4s}  {'mio':>10s}  {'usuario':>10s}  {'diff':>10s}")
    for anio in (2023, 2024, 2025):
        m = valores.get(anio, 0)
        u = REF_USUARIO_PYG_MILL[anio]
        diff = m - u
        print(f"    {anio:>4}  {m:>10,.0f}  {u:>10,.0f}  {diff:>10,.0f}")


def main():
    con = conectar(read_only=True)

    base = excedente_con_filtro(con)
    comparar("BASE (sin filtro extra)", base)

    f1 = excedente_con_filtro(
        con, "NOT (origen = 'MANU' AND fuente LIKE 'AB%')"
    )
    comparar("Excluir origen=MANU AND fuente LIKE 'AB%'", f1)

    f2 = excedente_con_filtro(con, "NOT (origen = 'MANU')")
    comparar("Excluir origen=MANU (todos los manuales)", f2)

    f3 = excedente_con_filtro(con, "NOT (fuente LIKE 'AB%')")
    comparar("Excluir fuente LIKE 'AB%' (cualquier origen)", f3)

    f4 = excedente_con_filtro(
        con, "NOT (origen = 'MANU' AND (fuente LIKE 'AB%' OR fuente LIKE 'SA%'))"
    )
    comparar("Excluir origen=MANU AND (fuente AB* OR SA*)", f4)

    con.close()


if __name__ == "__main__":
    main()
