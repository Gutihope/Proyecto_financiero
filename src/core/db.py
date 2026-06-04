import duckdb
from .config import ruta_db

ESQUEMAS = ("dim", "contabilidad", "presupuesto", "estudiantes", "tesoreria", "espacios")


def conectar(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    db = ruta_db()
    db.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=read_only)
    if not read_only:
        for esq in ESQUEMAS:
            con.execute(f'CREATE SCHEMA IF NOT EXISTS {esq}')
    return con
