"""Test rapido de obtener_ejecucion_pivot con filtro de meses y variaciones."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    obtener_ejecucion_pivot,
)


def imprimir(df, titulo):
    print(f"\n=== {titulo} ===")
    print("Columnas:", [str(c) for c in df.columns])
    # Filter to a few groups for legibility
    mask = df["grupo"].str.startswith(("5.", "11", "12", "21", "22", "31", "32", "51"))
    sub = df[mask].copy()
    # Format numbers in millions for display; convert pct columns to readable
    for col in sub.columns:
        if col == "grupo":
            continue
        col_str = str(col)
        if col_str.startswith(("%", "Δ")):
            sub[col] = sub[col].apply(lambda x: f"{x:+,.1f}%" if x == x else "")
        else:
            sub[col] = sub[col].apply(lambda x: f"{x/1e6:,.0f}" if x == x else "")
    out = sub.to_string(index=False)
    # Replace Delta with 'D' so it prints in cp1252
    out_safe = out.replace("Δ", "D").replace("→", "->")
    print(out_safe)


def main():
    print("=== Año completo 1-12, 2023-2025, con bonif ===")
    p = obtener_ejecucion_pivot([2023, 2024, 2025], 1, 12, True, incluir_variaciones=True)
    imprimir(p, "Año completo 1-12")

    print("\n\n=== Q1 (mes 1-3), 2023-2025, con bonif ===")
    p = obtener_ejecucion_pivot([2023, 2024, 2025], 1, 3, True, incluir_variaciones=True)
    imprimir(p, "Q1 (Ene-Mar)")

    print("\n\n=== Abr-Jul, 2024 y 2025 ===")
    p = obtener_ejecucion_pivot([2024, 2025], 4, 7, True, incluir_variaciones=True)
    imprimir(p, "Abr-Jul 2024-2025")


if __name__ == "__main__":
    main()
