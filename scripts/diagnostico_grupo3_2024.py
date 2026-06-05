"""Desglosa el grupo '3. Ingresos Extensión y CEC' en 2024.

Mostrando subgrupo, top cuentas, top origenes y top movimientos individuales
para identificar la fuente de la diferencia de 1,410M con el Power BI del usuario.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)
    grupo = "3. Ingresos Extensión y CEC"
    anios = (2023, 2024, 2025)

    print("=" * 110)
    print(f"Desglose detallado de '{grupo}' para 2023, 2024, 2025")
    print("Convencion: valor en MILLONES, P&L (signo invertido)")
    print("=" * 110)

    print("\n1) Por SUBGRUPO y ANIO")
    print("-" * 80)
    rows = con.execute("""
        SELECT subgrupo, anio,
               COUNT(*) AS n,
               ROUND(-SUM(movimiento)/1e6, 0) AS pyl_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = ?
          AND anio IN (2023, 2024, 2025)
        GROUP BY subgrupo, anio
        ORDER BY subgrupo, anio
    """, [grupo]).fetchall()
    print(f"  {'subgrupo':40s}  {'anio':>4s}  {'n':>7s}  {'mill':>10s}")
    for r in rows:
        print(f"  {(r[0] or '')[:40]:40s}  {r[1]:>4}  {r[2]:>7,}  {r[3]:>10,.0f}")

    print("\n2) Por CUENTA (2024 solamente, top 15)")
    print("-" * 90)
    rows = con.execute("""
        SELECT cuenta, ANY_VALUE(nombre_cuenta) AS nombre,
               subgrupo, COUNT(*) AS n,
               ROUND(-SUM(movimiento)/1e6, 1) AS pyl_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = ?
          AND anio = 2024
        GROUP BY cuenta, subgrupo
        ORDER BY ABS(SUM(movimiento)) DESC
        LIMIT 15
    """, [grupo]).fetchall()
    print(f"  {'cuenta':>12s}  {'subgrupo':<22s}  {'n':>6s}  {'mill':>10s}  nombre_cuenta")
    for r in rows:
        print(f"  {r[0]:>12s}  {(r[2] or '')[:22]:<22s}  "
              f"{r[3]:>6,}  {r[4]:>10,.1f}  {(r[1] or '')[:40]}")

    print("\n3) Por ORIGEN (2024 solamente)")
    print("-" * 70)
    rows = con.execute("""
        SELECT origen, COUNT(*) AS n,
               ROUND(-SUM(movimiento)/1e6, 1) AS pyl_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = ?
          AND anio = 2024
        GROUP BY origen
        ORDER BY ABS(SUM(movimiento)) DESC
    """, [grupo]).fetchall()
    print(f"  {'origen':30s}  {'n':>8s}  {'mill':>10s}")
    for r in rows:
        print(f"  {(r[0] or '')[:30]:30s}  {r[1]:>8,}  {r[2]:>10,.1f}")

    print("\n4) Por FUENTE (2024 solamente)")
    print("-" * 70)
    rows = con.execute("""
        SELECT fuente, COUNT(*) AS n,
               ROUND(-SUM(movimiento)/1e6, 1) AS pyl_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = ?
          AND anio = 2024
        GROUP BY fuente
        ORDER BY ABS(SUM(movimiento)) DESC
    """, [grupo]).fetchall()
    print(f"  {'fuente':20s}  {'n':>8s}  {'mill':>10s}")
    for r in rows:
        print(f"  {(r[0] or '')[:20]:20s}  {r[1]:>8,}  {r[2]:>10,.1f}")

    print("\n5) TOP 10 movimientos individuales mas grandes (2024)")
    print("-" * 110)
    rows = con.execute("""
        SELECT mes, fecha, cuenta, ANY_VALUE(nombre_cuenta), tercero,
               ANY_VALUE(nombre_tercero), origen, fuente,
               ROUND(SUM(movimiento)/1e6, 1) AS raw_mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = ?
          AND anio = 2024
        GROUP BY mes, fecha, cuenta, tercero, origen, fuente
        ORDER BY ABS(SUM(movimiento)) DESC
        LIMIT 10
    """, [grupo]).fetchall()
    print(f"  {'mes':>3s}  {'fecha':<12s}  {'cuenta':>12s}  "
          f"{'origen':<15s}  {'fuente':<10s}  {'raw_mill':>10s}  tercero  nombre")
    for r in rows:
        nom_tercero = (r[5] or "")[:25]
        print(f"  {r[0]:>3}  {str(r[1])[:12]:<12s}  {r[2]:>12s}  "
              f"{(r[6] or '')[:15]:<15s}  {(r[7] or '')[:10]:<10s}  "
              f"{r[8]:>10,.1f}  {r[4]}  {nom_tercero}")

    con.close()


if __name__ == "__main__":
    main()
