"""Top movimientos por grupo+año donde el usuario detecto diferencia."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


CASOS = [
    ("3. Ingresos Extensión y CEC", 2023, -5),
    ("32. Gastos  Extensión y CEC", 2023, -3),
    ("5. Ingresos Pregrado", 2023, -24),
    ("58. Deterioro", 2023, -34),
    ("5. Ingresos Pregrado", 2024, -64),
    ("3. Ingresos Extensión y CEC", 2025, -132),
    ("42. Gastos Posgrados", 2025, -68),
    ("5. Ingresos Pregrado", 2025, -51),
    ("6. Otros Ingresos no operacionales", 2025, -3),
    ("61. Otros Gastos No Operacionales", 2025, -5),
]


def main():
    con = conectar(read_only=True)

    for grupo, anio, diff_esperado in CASOS:
        print("\n" + "=" * 110)
        print(f"{grupo} | {anio} | diff esperado (mio - tuyo) = {diff_esperado} M")
        print("=" * 110)

        rows = con.execute("""
            SELECT mes, fecha, cuenta, ANY_VALUE(nombre_cuenta) AS nombre,
                   tercero, ANY_VALUE(nombre_tercero) AS nombre_t,
                   origen, fuente,
                   ROUND(-SUM(movimiento)/1e6, 1) AS pyl_mill
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE grupo = ? AND anio = ?
              AND LOWER(COALESCE(origen, '')) IN ('manu', 'manual',
                                                  'cxc', 'ajte', 'ajuste',
                                                  'ajusteconsorcio', 'consorcio2023')
            GROUP BY mes, fecha, cuenta, tercero, origen, fuente
            HAVING ABS(SUM(movimiento)) > 1e6
            ORDER BY ABS(SUM(movimiento)) DESC
            LIMIT 8
        """, [grupo, anio]).fetchall()

        if not rows:
            print("  (sin movimientos MANU/ajuste significativos)")
        else:
            print(f"  {'mes':>3s}  {'fecha':<11s}  {'origen':<10s}  {'fuente':<10s}  "
                  f"{'pyl_mill':>10s}  tercero")
            for r in rows:
                print(f"  {r[0]:>3}  {str(r[1])[:11]:<11s}  "
                      f"{(r[6] or '')[:10]:<10s}  {(r[7] or '')[:10]:<10s}  "
                      f"{r[8]:>10,.1f}  {(r[5] or '')[:35]}")

    con.close()


if __name__ == "__main__":
    main()
