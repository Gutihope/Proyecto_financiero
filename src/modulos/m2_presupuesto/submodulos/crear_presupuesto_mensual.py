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
    "promedio_4_anios",
    "promedio_5_anios",
    "valor_aprobado_anio_anterior",
]

N_ANIOS_POR_METODO: dict[str, int] = {
    "ejecucion_ultimo_anio": 1,
    "promedio_2_anios": 2,
    "promedio_3_anios": 3,
    "promedio_4_anios": 4,
    "promedio_5_anios": 5,
}

ETIQUETA_METODO: dict[str, str] = {
    "ejecucion_ultimo_anio": "Ejecución año anterior",
    "promedio_2_anios":      "Promedio últimos 2 años",
    "promedio_3_anios":      "Promedio últimos 3 años",
    "promedio_4_anios":      "Promedio últimos 4 años",
    "promedio_5_anios":      "Promedio últimos 5 años",
    "valor_aprobado_anio_anterior": "Valor año aprobado (manual)",
}

MESES_NOMBRES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                 "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

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


def listar_grupos() -> list[str]:
    """Devuelve la lista de grupos unicos disponibles, excluyendo LQORDER y nulos."""
    con = conectar(read_only=True)
    try:
        rows = con.execute(
            """
            SELECT DISTINCT grupo
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE grupo IS NOT NULL AND grupo != 'LQORDER'
            ORDER BY grupo
            """
        ).fetchall()
        return [r[0] for r in rows]
    finally:
        con.close()


def mensualizar_aprobado(
    df_calculado: pd.DataFrame,
    aprobado_por_grupo_pesos: dict[str, float],
) -> pd.DataFrame:
    """Reescala movimientos por grupo para que coincidan con el aprobado anual.

    Para cada grupo con valor aprobado:
       factor = |aprobado_pesos| / |sum(movimiento_calculado)|
       movimiento_final = movimiento_calculado * factor   (preserva signo)

    Grupos sin aprobado se dejan tal cual.
    Grupos con calculado = 0 se ignoran (no se puede reescalar).
    """
    if not aprobado_por_grupo_pesos or df_calculado.empty:
        return df_calculado.copy()

    df = df_calculado.copy()
    totales_abs = df.groupby("grupo")["movimiento"].sum().abs()

    factores: dict[str, float] = {}
    for grupo, aprobado in aprobado_por_grupo_pesos.items():
        total_abs = totales_abs.get(grupo, 0)
        if total_abs == 0 or aprobado is None:
            continue
        factores[grupo] = abs(float(aprobado)) / float(total_abs)

    if not factores:
        return df

    df["__factor"] = df["grupo"].map(factores).fillna(1.0)
    df["movimiento"] = df["movimiento"] * df["__factor"]
    return df.drop(columns="__factor")


def pivot_mensual_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot: filas = grupo, columnas = Ene..Dic, valores = SUM(movimiento).

    Devuelve DataFrame con columnas: grupo, Ene, Feb, ..., Dic, Total.
    """
    pivot = df.pivot_table(
        index="grupo",
        columns="mes",
        values="movimiento",
        aggfunc="sum",
        fill_value=0.0,
    )
    for m in range(1, 13):
        if m not in pivot.columns:
            pivot[m] = 0.0
    pivot = pivot[list(range(1, 13))]
    pivot.columns = MESES_NOMBRES
    pivot["Total"] = pivot.sum(axis=1)
    return pivot.reset_index()


def pivot_acumulado_por_grupo(df: pd.DataFrame) -> pd.DataFrame:
    """Pivot acumulado mes a mes: cada celda = suma de meses 1..mes actual."""
    mensual = pivot_mensual_por_grupo(df)
    acum = mensual.copy()
    for i in range(1, len(MESES_NOMBRES)):
        acum[MESES_NOMBRES[i]] = acum[MESES_NOMBRES[i]] + acum[MESES_NOMBRES[i - 1]]
    return acum
