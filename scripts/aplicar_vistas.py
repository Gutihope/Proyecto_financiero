"""Aplica todos los archivos SQL bajo sql/ y muestra un sample de cada vista."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar
from src.core.sql_runner import aplicar_sql_dir


def main():
    con = conectar()
    try:
        print("=" * 80)
        print("Aplicando SQL bajo sql/")
        print("=" * 80)
        aplicar_sql_dir(con, "sql")

        print("\n" + "=" * 80)
        print("Sample: presupuesto.vw_ejecucion_pivot_grupo_anio")
        print("=" * 80)
        for r in con.execute("""
            SELECT grupo, subgrupo, y2023, y2024, y2025, total
            FROM presupuesto.vw_ejecucion_pivot_grupo_anio
            ORDER BY ABS(total) DESC
            LIMIT 12
        """).fetchall():
            grp = (r[0] or "")[:35]
            sub = (r[1] or "")[:18]
            print(f"  {grp:35s} {sub:18s}  2023={r[2]:>16,.0f}  2024={r[3]:>16,.0f}  2025={r[4]:>16,.0f}")

        print("\n" + "=" * 80)
        print("Sample: presupuesto.vw_ejecucion_x_grupo_anio (2024, top 10)")
        print("=" * 80)
        for r in con.execute("""
            SELECT grupo, subgrupo, valor_total, n_movimientos
            FROM presupuesto.vw_ejecucion_x_grupo_anio
            WHERE anio = 2024
            ORDER BY ABS(valor_total) DESC
            LIMIT 10
        """).fetchall():
            grp = (r[0] or "")[:35]
            sub = (r[1] or "")[:18]
            print(f"  {grp:35s} {sub:18s}  ${r[2]:>16,.0f}  n={r[3]:>6,}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
