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
        print("Sample: presupuesto.vw_ejecucion_pivot_grupo_anio (consolidado, en MILLONES)")
        print("=" * 80)
        print(f"  {'grupo':40s}  {'2023':>10}  {'2024':>10}  {'2025':>10}")
        for r in con.execute("""
            SELECT grupo,
                   ROUND(y2023/1e6, 0) AS m23,
                   ROUND(y2024/1e6, 0) AS m24,
                   ROUND(y2025/1e6, 0) AS m25
            FROM presupuesto.vw_ejecucion_pivot_grupo_anio
            ORDER BY grupo
        """).fetchall():
            grp = (r[0] or "")[:40]
            print(f"  {grp:40s}  {r[1]:>10,.0f}  {r[2]:>10,.0f}  {r[3]:>10,.0f}")

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
