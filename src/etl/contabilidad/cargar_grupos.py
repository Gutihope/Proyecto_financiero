from pathlib import Path
import re

import pandas as pd

from src.core.config import cargar_config


def _anio_desde_nombre(archivo: Path) -> int | None:
    m = re.search(r"(20\d{2})", archivo.stem)
    return int(m.group(1)) if m else None


def cargar_grupos_subgrupos(con) -> dict[int, int]:
    cfg = cargar_config()
    base = Path(cfg["fuentes"]["ruta_base"])
    patron = cfg["fuentes"]["grupos_subgrupos"]["archivos_glob"]
    archivos = sorted(base.glob(patron))
    if not archivos:
        print(f"  (sin archivos para patron {patron})")
        return {}

    con.execute("""
        CREATE TABLE IF NOT EXISTS contabilidad.stg_grupos_subgrupos (
            id VARCHAR,
            grupo VARCHAR,
            subgrupo VARCHAR,
            anio_archivo INTEGER
        )
    """)

    resultados: dict[int, int] = {}
    for archivo in archivos:
        anio = _anio_desde_nombre(archivo)
        if anio is None:
            print(f"  ! sin año detectable en {archivo.name}, se omite")
            continue

        df = pd.read_excel(archivo)
        df.columns = [c.strip().lower() for c in df.columns]
        df = df[["id", "grupo", "subgrupo"]].copy()
        df["anio_archivo"] = anio

        con.execute(
            "DELETE FROM contabilidad.stg_grupos_subgrupos WHERE anio_archivo = ?",
            [anio],
        )
        con.register("df_tmp", df)
        con.execute("INSERT INTO contabilidad.stg_grupos_subgrupos SELECT * FROM df_tmp")
        con.unregister("df_tmp")

        resultados[anio] = len(df)
        print(f"  stg_grupos_subgrupos      anio={anio}  {len(df):>10,}  <- {archivo.name}")
    return resultados
