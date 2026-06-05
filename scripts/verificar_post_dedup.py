"""Verifica que el excedente sigue cuadrando tras filtrar LQORDE en la vista base."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar
from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    obtener_ejecucion_pivot,
)


REF_USUARIO = {2023: 348, 2024: 2541, 2025: 1760}


def main():
    con = conectar(read_only=True)

    print("Excedente P&L (M) tras filtrar LQORDE en la vista base:")
    p = obtener_ejecucion_pivot([2023, 2024, 2025], 1, 12, True)
    exc = p[p["grupo"] == "Excedente"]
    for anio in (2023, 2024, 2025):
        v = -exc[anio].iloc[0] / 1e6
        ref = REF_USUARIO[anio]
        diff = v - ref
        marca = "EXACTO" if abs(diff) < 1 else f"diff {diff:+,.0f} M"
        print(f"  {anio}: {v:>10,.0f}  vs Power BI {ref:>5,}  -> {marca}")

    print("\nVerificacion de que no quedan filas LQORDE en la vista:")
    n_lqorde = con.execute(
        "SELECT COUNT(*) FROM contabilidad.fact_ejecucion_clasificada "
        "WHERE UPPER(fuente) LIKE 'LQORDE%'"
    ).fetchone()[0]
    n_lqorder = con.execute(
        "SELECT COUNT(*) FROM contabilidad.fact_ejecucion_clasificada "
        "WHERE grupo = 'LQORDER'"
    ).fetchone()[0]
    n_total = con.execute(
        "SELECT COUNT(*) FROM contabilidad.fact_ejecucion_clasificada"
    ).fetchone()[0]
    print(f"  Filas LQORDE en vista:  {n_lqorde:>10,}")
    print(f"  Filas LQORDER grupo:    {n_lqorder:>10,}")
    print(f"  Total filas en vista:   {n_total:>10,}")

    print("\nFilas en fact_movimiento_contable (base con TODO):")
    n_base = con.execute(
        "SELECT COUNT(*) FROM contabilidad.fact_movimiento_contable"
    ).fetchone()[0]
    n_base_lqorde = con.execute(
        "SELECT COUNT(*) FROM contabilidad.fact_movimiento_contable "
        "WHERE UPPER(fuente) LIKE 'LQORDE%'"
    ).fetchone()[0]
    print(f"  Total filas base:         {n_base:>10,}")
    print(f"  Filas LQORDE en base:     {n_base_lqorde:>10,}")
    print(f"  Diff (lo que se excluyo): {n_base - n_total + n_base_lqorde - n_base_lqorde:>10,}")

    con.close()


if __name__ == "__main__":
    main()
