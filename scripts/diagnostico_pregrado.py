"""Compara los valores de '5. Ingresos Pregrado' contra los del Excel del usuario."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar

REF_USUARIO = {
    "5. Ingresos Pregrado": {2023:  13096, 2024:  14182, 2025:  16118},
    "51. Personal":         {2023:  -9915, 2024: -11105, 2025: -11953},
}


def main():
    con = conectar(read_only=True)
    print("=" * 90)
    print("1) Subgrupos de '5. Ingresos Pregrado' por anio (valores en MILLONES, raw movimiento)")
    print("=" * 90)
    print(f"  {'subgrupo':30s} {'anio':>5} {'n':>8} {'valor_mill':>14}")
    rows = con.execute("""
        SELECT subgrupo, anio, COUNT(*) AS n, ROUND(SUM(movimiento)/1e6, 0) AS mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = '5. Ingresos Pregrado'
          AND anio BETWEEN 2023 AND 2025
        GROUP BY subgrupo, anio
        ORDER BY anio, ABS(mill) DESC
    """).fetchall()
    for r in rows:
        print(f"  {(r[0] or '')[:30]:30s} {r[1]:>5} {r[2]:>8,} {r[3]:>14,.0f}")

    print("\n" + "=" * 90)
    print("2) Comparativo NETO Pregrado vs referencia del usuario (sign-flipped para mostrar como ingreso)")
    print("=" * 90)
    print(f"  {'anio':>6} {'mi_neto_mill':>15} {'usuario_mill':>15} {'diff':>10} {'%':>6}")
    for anio in (2023, 2024, 2025):
        neto = con.execute(f"""
            SELECT ROUND(SUM(movimiento)/1e6, 0) FROM contabilidad.fact_ejecucion_clasificada
            WHERE grupo = '5. Ingresos Pregrado' AND anio = {anio}
        """).fetchone()[0]
        # User report shows ingresos positive; raw is negative; multiply by -1 to compare
        mi_visto = -neto
        ref = REF_USUARIO["5. Ingresos Pregrado"][anio]
        diff = mi_visto - ref
        pct = round(100.0 * diff / ref, 2)
        print(f"  {anio:>6} {mi_visto:>15,.0f} {ref:>15,} {diff:>10,.0f} {pct:>5}%")

    print("\n" + "=" * 90)
    print("3) Mismo desglose para '51. Personal' (control - aqui SI cuadra el usuario)")
    print("=" * 90)
    print(f"  {'subgrupo':30s} {'anio':>5} {'n':>8} {'valor_mill':>14}")
    rows = con.execute("""
        SELECT subgrupo, anio, COUNT(*) AS n, ROUND(SUM(movimiento)/1e6, 0) AS mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = '51. Personal'
          AND anio BETWEEN 2023 AND 2025
        GROUP BY subgrupo, anio
        ORDER BY anio, ABS(mill) DESC
    """).fetchall()
    for r in rows:
        print(f"  {(r[0] or '')[:30]:30s} {r[1]:>5} {r[2]:>8,} {r[3]:>14,.0f}")

    print("\n" + "=" * 90)
    print("4) Pregrado por Origen + Tipo Comprobante 2023 (para descartar filtros)")
    print("=" * 90)
    print(f"  {'origen':25s} {'tipo':6s} {'n':>8} {'valor_mill':>14}")
    rows = con.execute("""
        SELECT origen, tipo_comprobante, COUNT(*) AS n, ROUND(SUM(movimiento)/1e6, 0) AS mill
        FROM contabilidad.fact_ejecucion_clasificada
        WHERE grupo = '5. Ingresos Pregrado' AND anio = 2023
        GROUP BY origen, tipo_comprobante
        ORDER BY ABS(mill) DESC
    """).fetchall()
    for r in rows:
        print(f"  {(r[0] or '')[:25]:25s} {(r[1] or '')[:6]:6s} {r[2]:>8,} {r[3]:>14,.0f}")

    con.close()


if __name__ == "__main__":
    main()
