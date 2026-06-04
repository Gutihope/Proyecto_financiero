"""Diagnostica por que la cobertura del join clave_grupo es baja."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.core.db import conectar


def main():
    con = conectar(read_only=True)

    print("=" * 80)
    print("Distintos vs totales (2023)")
    print("=" * 80)
    for tabla, col, anio_col in [
        ("contabilidad.fact_movimiento_contable", "clave_grupo", "anio"),
        ("contabilidad.stg_grupos_subgrupos", "id", "anio_archivo"),
    ]:
        for anio in (2023, 2024, 2025):
            total, distintos = con.execute(
                f"SELECT COUNT(*), COUNT(DISTINCT {col}) "
                f"FROM {tabla} WHERE {anio_col} = {anio}"
            ).fetchone()
            print(f"  {tabla} {anio}: total={total:>8,}  distintos={distintos:>8,}")
        print()

    print("=" * 80)
    print("Interseccion (claves de Movimiento que existen en Grupos, por anio)")
    print("=" * 80)
    for anio in (2023, 2024, 2025):
        en_ambos = con.execute(f"""
            SELECT COUNT(DISTINCT m.clave_grupo)
            FROM contabilidad.fact_movimiento_contable m
            WHERE m.anio = {anio}
              AND EXISTS (
                SELECT 1 FROM contabilidad.stg_grupos_subgrupos g
                WHERE g.id = m.clave_grupo AND g.anio_archivo = {anio}
              )
        """).fetchone()[0]
        distintos_mov = con.execute(f"""
            SELECT COUNT(DISTINCT clave_grupo)
            FROM contabilidad.fact_movimiento_contable WHERE anio = {anio}
        """).fetchone()[0]
        print(f"  {anio}: claves distintas en mov={distintos_mov:>8,}, "
              f"con match en grupos={en_ambos:>8,}, "
              f"pct={100.0*en_ambos/distintos_mov:.1f}%")

    print("\n" + "=" * 80)
    print("3 filas de Grupos 2023 que NO tienen match en Movimiento 2023")
    print("=" * 80)
    sin_match = con.execute("""
        SELECT g.id, g.grupo, g.subgrupo
        FROM contabilidad.stg_grupos_subgrupos g
        WHERE g.anio_archivo = 2023
          AND NOT EXISTS (
            SELECT 1 FROM contabilidad.fact_movimiento_contable m
            WHERE m.clave_grupo = g.id AND m.anio = 2023
          )
        LIMIT 3
    """).fetchall()
    for r in sin_match:
        print(f"  ID={r[0]!r}\n    Grupo={r[1]!r}  Subgrupo={r[2]!r}")

    print("\n" + "=" * 80)
    print("3 filas de Movimiento 2023 que NO tienen match en Grupos 2023")
    print("=" * 80)
    sin_match_mov = con.execute("""
        SELECT m.cuenta, m.centro_de_responsabilidad, m.tercero, m.comprobante,
               m.documento_referencia, m.mes, m.movimiento, m.fuente, m.clave_grupo
        FROM contabilidad.fact_movimiento_contable m
        WHERE m.anio = 2023
          AND NOT EXISTS (
            SELECT 1 FROM contabilidad.stg_grupos_subgrupos g
            WHERE g.id = m.clave_grupo AND g.anio_archivo = 2023
          )
        LIMIT 3
    """).fetchall()
    for r in sin_match_mov:
        print(f"  cuenta={r[0]!r} cr={r[1]!r} tercero={r[2]!r}")
        print(f"  comprobante={r[3]!r} doc_ref={r[4]!r} mes={r[5]!r}")
        print(f"  movimiento={r[6]!r} fuente={r[7]!r}")
        print(f"  clave_grupo={r[8]!r}\n")

    print("=" * 80)
    print("Comparar: 1 ID de Grupos vs todos los Movimientos donde EXACTAMENTE igualen 6 de los 8 campos")
    print("=" * 80)
    g_sample = sin_match[0][0]
    print(f"  ID Grupo: {g_sample!r}")
    parecidos = con.execute("""
        SELECT m.cuenta, m.centro_de_responsabilidad, m.tercero, m.comprobante,
               m.documento_referencia, m.mes, m.movimiento, m.fuente, m.clave_grupo
        FROM contabilidad.fact_movimiento_contable m
        WHERE m.anio = 2023
          AND m.cuenta || m.centro_de_responsabilidad || m.tercero = SUBSTR(?, 1, LENGTH(m.cuenta) + LENGTH(m.centro_de_responsabilidad) + LENGTH(m.tercero))
        LIMIT 3
    """, [g_sample]).fetchall()
    for r in parecidos:
        print(f"  cuenta={r[0]!r} cr={r[1]!r} tercero={r[2]!r}")
        print(f"  comprobante={r[3]!r} doc_ref={r[4]!r} mes={r[5]!r}")
        print(f"  movimiento={r[6]!r} fuente={r[7]!r}")
        print(f"  clave_grupo computada={r[8]!r}")

    con.close()


if __name__ == "__main__":
    main()
