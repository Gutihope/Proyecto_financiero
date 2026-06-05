"""Lista el aporte de cada grupo al excedente, por anio, en P&L convention.

Permite identificar que grupos contribuyen al excedente y cual genera la
discrepancia con el reporte del usuario.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    obtener_ejecucion_pivot,
)


REF_USUARIO_PYG_MILLONES = {2023: 348, 2024: 2541, 2025: 1760}


def main():
    p = obtener_ejecucion_pivot(
        [2023, 2024, 2025], 1, 12,
        ajustar_bonificaciones=True,
        incluir_variaciones=False,
        incluir_vs_presupuesto=False,
    )

    print("=" * 110)
    print("Aporte de cada grupo al excedente, en MILLONES y en CONVENCION P&L")
    print("(ingresos positivos, gastos negativos; sumatoria = excedente)")
    print("=" * 110)
    print(f"  {'Grupo / Detalle':45s}  {'2023':>14s}  {'2024':>14s}  {'2025':>14s}")
    print("  " + "-" * 100)

    grupos = p[p["grupo"] != "Excedente"]["grupo"].tolist()
    totales = {2023: 0.0, 2024: 0.0, 2025: 0.0}

    for g in grupos:
        fila = p[p["grupo"] == g].iloc[0]
        vals = {}
        for anio in (2023, 2024, 2025):
            # P&L convention: invertir signo
            raw = float(fila[anio])
            pyl_m = -raw / 1e6
            vals[anio] = pyl_m
            totales[anio] += pyl_m
        nombre = g.replace("·", "-").replace("Δ", "D")[:43]
        print(f"  {nombre:45s}  {vals[2023]:>14,.0f}  {vals[2024]:>14,.0f}  {vals[2025]:>14,.0f}")

    print("  " + "-" * 100)
    print(f"  {'EXCEDENTE (mi calculo)':45s}  "
          f"{totales[2023]:>14,.0f}  {totales[2024]:>14,.0f}  {totales[2025]:>14,.0f}")
    print(f"  {'EXCEDENTE (tu Power BI)':45s}  "
          f"{REF_USUARIO_PYG_MILLONES[2023]:>14,.0f}  "
          f"{REF_USUARIO_PYG_MILLONES[2024]:>14,.0f}  "
          f"{REF_USUARIO_PYG_MILLONES[2025]:>14,.0f}")
    print(f"  {'DIFERENCIA (mio - tuyo)':45s}  "
          f"{totales[2023] - REF_USUARIO_PYG_MILLONES[2023]:>14,.0f}  "
          f"{totales[2024] - REF_USUARIO_PYG_MILLONES[2024]:>14,.0f}  "
          f"{totales[2025] - REF_USUARIO_PYG_MILLONES[2025]:>14,.0f}")


if __name__ == "__main__":
    main()
