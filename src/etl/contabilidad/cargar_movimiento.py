from pathlib import Path
import pandas as pd

from src.core.config import cargar_config
from src.core.utils import normalizar_columnas, valor_a_id_str, valor_texto_db

COLS_CLAVE_GRUPO = [
    "cuenta",
    "centro_de_responsabilidad",
    "tercero",
    "comprobante",
    "documento_referencia",
    "mes",
    "movimiento",
    "fuente",
]

COLS_TEXTO = [
    "nombre_mes", "division", "nombre_division", "fuente", "descripcion_fuente",
    "concepto", "nombre_concepto", "tipo_comprobante", "comprobante",
    "documento_referencia", "clase_cuenta", "nombre_clase_cuenta",
    "grupo_cuenta", "nombre_grupo_cuenta", "cuenta_mayor",
    "nombre_cuenta_mayor", "subcuenta", "nombre_subcuenta", "cuenta",
    "nombre_cuenta", "centro_de_responsabilidad",
    "nombre_centro_de_responsabilidad", "tercero", "nombre_tercero",
    "comentarios", "moneda", "origen", "estado",
]


def _coercer_textos(df: pd.DataFrame) -> pd.DataFrame:
    for col in COLS_TEXTO:
        if col in df.columns:
            df[col] = df[col].apply(valor_texto_db)
    return df


def _construir_clave_grupo(df: pd.DataFrame) -> pd.Series:
    return df[COLS_CLAVE_GRUPO].apply(
        lambda row: "".join(valor_a_id_str(v) for v in row),
        axis=1,
    )


def _tabla_existe(con, schema: str, tabla: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = ? AND table_name = ?",
        [schema, tabla],
    ).fetchone()
    return fila is not None


def cargar_movimiento_contable(con) -> dict[int, int]:
    cfg = cargar_config()
    base = Path(cfg["fuentes"]["ruta_base"])
    patron = cfg["fuentes"]["contabilidad"]["movimiento_glob"]
    archivos = sorted(base.glob(patron))
    if not archivos:
        print(f"  (sin archivos para patron {patron})")
        return {}

    resultados: dict[int, int] = {}
    for archivo in archivos:
        df = normalizar_columnas(pd.read_excel(archivo))
        df["clave_grupo"] = _construir_clave_grupo(df)
        df = _coercer_textos(df)
        anio = int(df["anio"].iloc[0])

        con.register("df_tmp", df)
        if not _tabla_existe(con, "contabilidad", "fact_movimiento_contable"):
            con.execute(
                "CREATE TABLE contabilidad.fact_movimiento_contable AS "
                "SELECT * FROM df_tmp"
            )
        else:
            con.execute(
                "DELETE FROM contabilidad.fact_movimiento_contable WHERE anio = ?",
                [anio],
            )
            con.execute(
                "INSERT INTO contabilidad.fact_movimiento_contable "
                "SELECT * FROM df_tmp"
            )
        con.unregister("df_tmp")
        resultados[anio] = len(df)
        print(f"  fact_movimiento_contable  anio={anio}  {len(df):>10,}  <- {archivo.name}")
    return resultados
