"""Submódulo 1 del módulo Presupuesto: Crear presupuesto mensualizado.

Genera el presupuesto del anio destino al nivel de
(cuenta, centro_de_responsabilidad, grupo, subgrupo, mes) usando uno de
estos metodos:

  - 'ejecucion_ultimo_anio'        : copia la ejecucion del anio anterior
  - 'promedio_2_anios'             : promedio anual de los ultimos 2 anios
  - 'promedio_3_anios'             : promedio anual de los ultimos 3 anios
  - 'valor_aprobado_anio_anterior' : copia el presupuesto APROBADO del anio
                                     anterior (requiere fact_presupuesto cargado)

El divisor del promedio = COUNT(DISTINCT anio) con datos en cada combinacion,
asi una cuenta que solo existio un anio no se promedia con ceros artificiales.
"""
from pathlib import Path
from typing import Literal

import pandas as pd

from src.core.config import cargar_config
from src.core.db import conectar

Metodo = Literal[
    "ejecucion_ultimo_anio",
    "promedio_2_anios",
    "promedio_3_anios",
    "valor_aprobado_anio_anterior",
]

N_ANIOS_POR_METODO: dict[str, int] = {
    "ejecucion_ultimo_anio": 1,
    "promedio_2_anios": 2,
    "promedio_3_anios": 3,
}

COLUMNAS_EXPORT = [
    "anio", "cuenta", "centro_de_responsabilidad",
    "grupo", "subgrupo", "movimiento", "mes",
]
NOMBRES_EXPORT = [
    "Año", "Cuenta", "Centro de Responsabilidad",
    "Grupo", "Subgrupo", "Movimiento", "Mes",
]


def generar(
    anio_destino: int,
    metodo: Metodo = "promedio_3_anios",
    grupos: list[str] | None = None,
) -> pd.DataFrame:
    """Genera el presupuesto mensualizado del `anio_destino` segun `metodo`."""
    if metodo == "valor_aprobado_anio_anterior":
        return _desde_presupuesto_aprobado(anio_destino, grupos)

    if metodo not in N_ANIOS_POR_METODO:
        raise ValueError(f"Metodo desconocido: {metodo}")

    n_anios = N_ANIOS_POR_METODO[metodo]
    con = conectar(read_only=True)
    try:
        anios_disponibles = con.execute(
            """
            SELECT COUNT(DISTINCT anio)
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE anio BETWEEN ? AND ?
              AND grupo IS NOT NULL AND grupo != 'LQORDER'
            """,
            [anio_destino - n_anios, anio_destino - 1],
        ).fetchone()[0]
        if anios_disponibles < n_anios:
            print(
                f"  ADVERTENCIA: solo {anios_disponibles} anios tienen datos en el rango "
                f"{anio_destino - n_anios}-{anio_destino - 1} (pediste {n_anios}). "
                f"El promedio quedara subestimado para items que existian en los anios sin datos."
            )

        sql = """
            SELECT
                ?::INTEGER AS anio,
                cuenta,
                centro_de_responsabilidad,
                grupo,
                subgrupo,
                mes,
                SUM(movimiento) / ?::DOUBLE AS movimiento
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE anio BETWEEN ? AND ?
              AND grupo IS NOT NULL
              AND grupo != 'LQORDER'
        """
        params: list = [anio_destino, n_anios, anio_destino - n_anios, anio_destino - 1]

        if grupos:
            placeholders = ",".join(["?"] * len(grupos))
            sql += f" AND grupo IN ({placeholders})"
            params.extend(grupos)

        sql += """
            GROUP BY cuenta, centro_de_responsabilidad, grupo, subgrupo, mes
            ORDER BY grupo, subgrupo, cuenta, centro_de_responsabilidad, mes
        """
        return con.execute(sql, params).df()
    finally:
        con.close()


def _desde_presupuesto_aprobado(
    anio_destino: int, grupos: list[str] | None
) -> pd.DataFrame:
    con = conectar(read_only=True)
    try:
        existe = con.execute(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema='presupuesto' AND table_name='fact_presupuesto'"
        ).fetchone()
        if not existe:
            raise RuntimeError(
                "No existe presupuesto.fact_presupuesto. Carga primero el "
                "presupuesto aprobado de anios anteriores en la carpeta "
                "'datos/Estado de Resultado Presupuesto/' y corre el ETL."
            )

        sql = """
            SELECT
                ?::INTEGER AS anio,
                cuenta,
                centro_de_responsabilidad,
                grupo,
                subgrupo,
                mes,
                SUM(movimiento) AS movimiento
            FROM presupuesto.fact_presupuesto
            WHERE anio = ?
        """
        params: list = [anio_destino, anio_destino - 1]
        if grupos:
            placeholders = ",".join(["?"] * len(grupos))
            sql += f" AND grupo IN ({placeholders})"
            params.extend(grupos)
        sql += """
            GROUP BY cuenta, centro_de_responsabilidad, grupo, subgrupo, mes
            ORDER BY grupo, subgrupo, cuenta, centro_de_responsabilidad, mes
        """
        return con.execute(sql, params).df()
    finally:
        con.close()


def exportar(df: pd.DataFrame, ruta: Path) -> Path:
    """Exporta el DataFrame al formato Excel listo para recarga."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)

    df_export = df[COLUMNAS_EXPORT].copy()
    df_export.columns = NOMBRES_EXPORT
    df_export.to_excel(ruta, index=False, sheet_name="Presupuesto")
    return ruta


def ruta_salida_default(anio_destino: int, metodo: str) -> Path:
    cfg = cargar_config()
    base = Path(cfg["fuentes"]["ruta_base"])
    carpeta = base / "datos" / "Estado de Resultado Presupuesto"
    return carpeta / f"presupuesto_{anio_destino}_{metodo}.xlsx"
