"""Analiza el 10% de Movimiento 2023-2025 que no encuentra match en Grupos."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)

    print("=" * 80)
    print("Distribucion de los unmatched por columna (anio 2023-2025)")
    print("=" * 80)

    for col in ("fuente", "tipo_comprobante", "clase_cuenta", "grupo_cuenta", "origen", "moneda"):
        print(f"\nTop 8 valores de '{col}' en los UNMATCHED:")
        rows = con.execute(f"""
            SELECT m.{col}, COUNT(*) AS n
            FROM contabilidad.fact_movimiento_contable m
            WHERE m.anio IN (2023, 2024, 2025)
              AND NOT EXISTS (
                SELECT 1 FROM contabilidad.stg_grupos_subgrupos g
                WHERE g.id = m.clave_grupo AND g.anio_archivo = m.anio
              )
            GROUP BY m.{col} ORDER BY n DESC LIMIT 8
        """).fetchall()
        for r in rows:
            print(f"  {str(r[0]):30s}  {r[1]:>8,}")

    print("\n" + "=" * 80)
    print("5 ejemplos de Grupos 2023 SIN match en Movimiento 2023 (y su prefijo)")
    print("=" * 80)
    rows = con.execute("""
        SELECT g.id, g.grupo, g.subgrupo
        FROM contabilidad.stg_grupos_subgrupos g
        WHERE g.anio_archivo = 2023
          AND NOT EXISTS (
            SELECT 1 FROM contabilidad.fact_movimiento_contable m
            WHERE m.clave_grupo = g.id AND m.anio = 2023
          )
        LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"  ID={r[0]!r}\n     Grupo={r[1]!r}  Subgrupo={r[2]!r}\n")

    print("=" * 80)
    print("5 ejemplos de Movimiento 2023 SIN match en Grupos 2023")
    print("=" * 80)
    rows = con.execute("""
        SELECT m.cuenta, m.centro_de_responsabilidad, m.tercero, m.comprobante,
               m.documento_referencia, m.mes, m.movimiento, m.fuente, m.clave_grupo,
               m.tipo_comprobante, m.clase_cuenta
        FROM contabilidad.fact_movimiento_contable m
        WHERE m.anio = 2023
          AND NOT EXISTS (
            SELECT 1 FROM contabilidad.stg_grupos_subgrupos g
            WHERE g.id = m.clave_grupo AND g.anio_archivo = m.anio
          )
        LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"  cta={r[0]} cr={r[1]} terc={r[2]} comp={r[3]} doc={r[4]}")
        print(f"  mes={r[5]} mov={r[6]} fnt={r[7]} tipo={r[9]} clase={r[10]}")
        print(f"  clave={r[8]!r}\n")

    print("=" * 80)
    print("Cuentas duplicadas (mismo clave_grupo aparece mas de 1 vez en Mov 2023)")
    print("=" * 80)
    rows = con.execute("""
        SELECT clave_grupo, COUNT(*) AS n
        FROM contabilidad.fact_movimiento_contable
        WHERE anio = 2023
        GROUP BY clave_grupo
        HAVING COUNT(*) > 1
        ORDER BY n DESC LIMIT 5
    """).fetchall()
    for r in rows:
        print(f"  n={r[1]}  clave={r[0]!r}")

    con.close()


if __name__ == "__main__":
    main()
