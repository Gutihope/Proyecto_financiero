"""CLI para generar el presupuesto mensualizado de un anio.

Ejemplos:
  python scripts/generar_presupuesto.py --anio 2026 --metodo prom3
  python scripts/generar_presupuesto.py --anio 2026 --metodo prom2 --grupos "5. Ingresos Pregrado" "51. Personal"
  python scripts/generar_presupuesto.py --anio 2026 --metodo anio_anterior --salida C:/tmp/2026.xlsx
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    generar, exportar, ruta_salida_default,
)


METODOS_CORTOS = {
    "anio_anterior": "ejecucion_ultimo_anio",
    "prom2":         "promedio_2_anios",
    "prom3":         "promedio_3_anios",
    "aprobado":      "valor_aprobado_anio_anterior",
}


def main():
    p = argparse.ArgumentParser(
        description="Genera el presupuesto mensualizado por (cuenta, ceco, grupo, subgrupo, mes)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--anio", type=int, required=True,
                   help="Anio destino del presupuesto (ej. 2026)")
    p.add_argument("--metodo", choices=list(METODOS_CORTOS), default="prom3",
                   help="Metodo de generacion")
    p.add_argument("--grupos", nargs="*", default=None,
                   help="Filtrar a estos grupos (separados por espacios, entre comillas si tienen espacios). "
                        "Vacio = todos los grupos.")
    p.add_argument("--salida", type=Path, default=None,
                   help="Ruta del .xlsx de salida. Vacio = carpeta Presupuesto por defecto.")
    args = p.parse_args()

    metodo_full = METODOS_CORTOS[args.metodo]
    print(f"Generando presupuesto anio={args.anio}, metodo='{args.metodo}' ({metodo_full})")
    if args.grupos:
        print(f"  Filtro de grupos: {args.grupos}")

    df = generar(args.anio, metodo_full, args.grupos)

    salida = args.salida or ruta_salida_default(args.anio, args.metodo)
    ruta = exportar(df, salida)

    print(f"\nArchivo generado: {ruta}")
    print(f"Filas: {len(df):,}")
    print(f"Suma movimiento (raw):    {df['movimiento'].sum():>20,.0f}")
    print(f"Suma absoluta:            {df['movimiento'].abs().sum():>20,.0f}")

    print("\nDistribucion por grupo (en MILLONES, signo crudo):")
    resumen = df.groupby("grupo")["movimiento"].agg(["sum", "count"]).sort_values(
        "sum", key=lambda s: s.abs(), ascending=False
    )
    print(f"  {'grupo':45s} {'millones':>14}  {'filas':>10}")
    for grupo, fila in resumen.iterrows():
        print(f"  {grupo[:45]:45s} {fila['sum']/1e6:>14,.0f}  {fila['count']:>10,}")


if __name__ == "__main__":
    main()
