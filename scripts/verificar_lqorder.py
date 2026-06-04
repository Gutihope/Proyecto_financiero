"""Verifica que el grupo LQORDER sume cero por anio (regla de negocio)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)

    print("LQORDER por anio (deberia sumar ~0):")
    print(f"  {'anio':>6} {'n':>10} {'suma':>20} {'abs_max':>20}")
    for r in con.execute("""
        SELECT anio, COUNT(*) AS n, SUM(movimiento) AS suma, MAX(ABS(movimiento)) AS abs_max
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = 'LQORDER'
        GROUP BY anio
        ORDER BY anio
    """).fetchall():
        print(f"  {r[0]:>6} {r[1]:>10,} {r[2]:>20,.2f} {r[3]:>20,.2f}")

    print("\nSubgrupos dentro de LQORDER:")
    for r in con.execute("""
        SELECT subgrupo, anio, COUNT(*) AS n, SUM(movimiento) AS suma
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = 'LQORDER'
        GROUP BY subgrupo, anio
        ORDER BY anio, subgrupo
    """).fetchall():
        print(f"  {(r[0] or '')[:20]:20s} {r[1]:>6} {r[2]:>10,} {r[3]:>20,.2f}")

    con.close()


if __name__ == "__main__":
    main()
