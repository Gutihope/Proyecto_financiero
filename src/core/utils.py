import re
import unicodedata
import pandas as pd

RENOMBRES_ESPECIALES = {
    "ano": "anio",
    "año": "anio",
}


def normalizar_columna(s: str) -> str:
    raw = s.strip().lower()
    if raw in RENOMBRES_ESPECIALES:
        return RENOMBRES_ESPECIALES[raw]
    s = s.replace("ñ", "n").replace("Ñ", "N")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()
    if s in RENOMBRES_ESPECIALES:
        s = RENOMBRES_ESPECIALES[s]
    return s


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [normalizar_columna(c) for c in df.columns]
    return df


def valor_a_id_str(x) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, float):
        if x == int(x):
            return str(int(x))
        s = f"{x:.2f}".rstrip("0").rstrip(".")
        return s.replace(".", ",")
    return str(x)


def valor_texto_db(x):
    if pd.isna(x):
        return None
    if isinstance(x, float):
        if x == int(x):
            return str(int(x))
        return str(x)
    return str(x)
