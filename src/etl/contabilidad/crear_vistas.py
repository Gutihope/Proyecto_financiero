from src.core.sql_runner import aplicar_sql_dir


def crear_vistas(con) -> None:
    aplicar_sql_dir(con, "sql")
