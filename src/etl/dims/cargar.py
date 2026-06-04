from pathlib import Path
import pandas as pd

from src.core.config import cargar_config
from src.core.utils import normalizar_columnas


def _cargar_un_dim(con, ruta_excel: Path, tabla: str) -> int:
    df = normalizar_columnas(pd.read_excel(ruta_excel))
    con.register("df_tmp", df)
    con.execute(f"CREATE OR REPLACE TABLE dim.{tabla} AS SELECT * FROM df_tmp")
    con.unregister("df_tmp")
    return len(df)


def cargar_dims(con) -> dict[str, int]:
    cfg = cargar_config()
    base = Path(cfg["fuentes"]["ruta_base"])
    dim_cfg = cfg["fuentes"]["dim"]

    tablas = ["centros_costos", "cuenta_contable", "fecha", "periodo", "tercero"]
    resultados: dict[str, int] = {}
    for tabla in tablas:
        archivo = base / dim_cfg[tabla]
        n = _cargar_un_dim(con, archivo, tabla)
        resultados[tabla] = n
        print(f"  dim.{tabla:18s}  {n:>8,}  <- {archivo.name}")
    return resultados
