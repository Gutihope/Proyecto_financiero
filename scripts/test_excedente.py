"""Verifica que la fila Excedente del pivot suma correctamente."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    obtener_ejecucion_pivot,
)


def main():
    p = obtener_ejecucion_pivot(
        [2023, 2024, 2025], 1, 12, True,
        incluir_variaciones=True,
        incluir_vs_presupuesto=False,
    )

    fila_exc = p[p["grupo"] == "Excedente"]
    if fila_exc.empty:
        print("ERROR: no se encontro fila Excedente")
        return

    print("Fila Excedente (raw signed, pesos):")
    for col in p.columns:
        val = fila_exc[col].iloc[0]
        col_str = str(col).replace("Δ", "D").replace("→", "->").replace("Año", "Ano")
        print(f"  {col_str:25s} = {val:>20,.0f}" if isinstance(val, (int, float))
              else f"  {col_str:25s} = {val}")

    print("\nEn MILLONES:")
    for anio in [2023, 2024, 2025]:
        v = fila_exc[anio].iloc[0]
        print(f"  {anio}: raw {v/1e6:>10,.0f} M   |  P&L (x-1) {-v/1e6:>10,.0f} M")

    print("\nNota: en P&L (x-1), POSITIVO = utilidad (ingresos > gastos).")


if __name__ == "__main__":
    main()
