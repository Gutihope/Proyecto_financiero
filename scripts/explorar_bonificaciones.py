"""Identifica las cuentas contables de bonificaciones y su impacto por grupo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)

    print("=" * 90)
    print("1) Cuentas en dim_cuentacontable que contienen 'bonif' (cualquier mayuscula)")
    print("=" * 90)
    rows = con.execute("""
        SELECT cuecodilimiinfe, cuenombre, digitos
        FROM dim.cuenta_contable
        WHERE LOWER(cuenombre) LIKE '%bonif%'
        ORDER BY cuecodilimiinfe
    """).fetchall()
    print(f"  {'codigo':>15s}  {'digitos':>3s}  nombre")
    for r in rows:
        print(f"  {r[0]:>15}  {r[2]:>3}  {r[1]}")

    print("\n" + "=" * 90)
    print("2) Cuentas en MOVIMIENTO 2023-2025 con 'bonif' en nombre")
    print("=" * 90)
    rows = con.execute("""
        SELECT cuenta, ANY_VALUE(nombre_cuenta) AS nombre,
               grupo, ANY_VALUE(subgrupo) AS subgrupo,
               COUNT(*) AS n,
               ROUND(SUM(movimiento)/1e6, 0) AS millones
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE LOWER(nombre_cuenta) LIKE '%bonif%'
          AND anio BETWEEN 2023 AND 2025
          AND grupo IS NOT NULL AND grupo != 'LQORDER'
        GROUP BY cuenta, grupo
        ORDER BY ABS(SUM(movimiento)) DESC
        LIMIT 30
    """).fetchall()
    print(f"  {'cuenta':>12s}  {'grupo':<32s}  {'subgrupo':<20s}  {'n':>6s}  {'mill':>8s}  nombre_cuenta")
    for r in rows:
        nombre = (r[1] or "")[:40]
        grupo = (r[2] or "")[:32]
        subg = (r[3] or "")[:20]
        print(f"  {r[0]:>12s}  {grupo:<32s}  {subg:<20s}  {r[4]:>6,}  {r[5]:>8,.0f}  {nombre}")

    print("\n" + "=" * 90)
    print("3) Total bonificaciones por grupo de personal (11, 21, 31) y anio")
    print("=" * 90)
    rows = con.execute("""
        SELECT anio, grupo,
               COUNT(*) AS n,
               ROUND(SUM(movimiento)/1e6, 0) AS millones
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE LOWER(nombre_cuenta) LIKE '%bonif%'
          AND grupo IN ('11 Gastos FOSFEC Empresarial Personal',
                        '21. Gastos Fosfec Personal',
                        '31. Gastos  Extensión y CEC Personal',
                        '51. Personal')
          AND anio BETWEEN 2023 AND 2025
        GROUP BY anio, grupo
        ORDER BY grupo, anio
    """).fetchall()
    print(f"  {'anio':>4s}  {'grupo':<45s}  {'n':>6s}  {'millones':>10s}")
    for r in rows:
        grupo = (r[1] or "")[:45]
        print(f"  {r[0]:>4}  {grupo:<45s}  {r[2]:>6,}  {r[3]:>10,.0f}")

    con.close()


if __name__ == "__main__":
    main()
