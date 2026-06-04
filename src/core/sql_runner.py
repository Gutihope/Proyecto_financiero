from pathlib import Path

from src.core.config import PROJECT_ROOT


def aplicar_sql_dir(con, ruta_relativa: str = "sql") -> list[str]:
    """Ejecuta todos los archivos .sql bajo `ruta_relativa` en orden alfabetico (depth-first).

    DuckDB soporta scripts multi-statement separados por ';'.
    """
    base = PROJECT_ROOT / ruta_relativa
    archivos = sorted(base.rglob("*.sql"))
    aplicados: list[str] = []
    for archivo in archivos:
        sql = archivo.read_text(encoding="utf-8")
        con.execute(sql)
        rel = str(archivo.relative_to(PROJECT_ROOT)).replace("\\", "/")
        aplicados.append(rel)
        print(f"  sql aplicado: {rel}")
    return aplicados
