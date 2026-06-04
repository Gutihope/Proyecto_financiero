"""Submódulo: Ejecución presupuestal × grupo × años.

Muestra la ejecución acumulada por grupo (desagregando Personal y
Centralizados por subgrupo) para los años seleccionados. Aplica
opcionalmente el ajuste de bonificaciones:

Regla de negocio:
  Las cuentas contables 'BONIFICACIONES' (y 'BONIFICACIONES- IBC')
  están cargadas dentro de los grupos de PERSONAL (11, 21, 31) pero
  contablemente deben reportarse en su par de gastos NO personal
  (12, 22, 32), con un factor 1.52 que incluye prestaciones sociales.

  Para cada par y por anio:
    bonif_G = SUM(movimiento) WHERE grupo=G_personal AND nombre_cuenta LIKE 'bonif%'
    ajuste   = bonif_G * 1.52
    G_personal_ajustado     = G_personal     - ajuste
    G_no_personal_ajustado  = G_no_personal  + ajuste

Pares (configurable en BONIF_MAPPING):
  11. Gastos FOSFEC Empresarial Personal -> 12. Gastos FOSFEC Empresarial
  21. Gastos Fosfec Personal             -> 22. Gastos Fosfec CEC
  31. Gastos Extensión y CEC Personal    -> 32. Gastos Extensión y CEC

(El ajuste NO se aplica en el submódulo de Crear presupuesto — solo aquí.)
"""
from pathlib import Path

import pandas as pd

from src.core.db import conectar
from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    _agregar_columna_clave,
)


BONIF_MAPPING: dict[str, str] = {
    "11 Gastos FOSFEC Empresarial Personal": "12. Gastos FOSFEC Empresarial",
    "21. Gastos Fosfec Personal":            "22. Gastos Fosfec CEC",
    "31. Gastos  Extensión y CEC Personal":  "32. Gastos  Extensión y CEC",
}
FACTOR_BONIF_DEFAULT = 1.52


def listar_anios_disponibles() -> list[int]:
    """Devuelve los años que tienen datos clasificados por grupo."""
    con = conectar(read_only=True)
    try:
        rows = con.execute("""
            SELECT DISTINCT anio
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE grupo IS NOT NULL AND grupo != 'LQORDER'
            ORDER BY anio
        """).fetchall()
        return [int(r[0]) for r in rows]
    finally:
        con.close()


def obtener_ejecucion_pivot(
    anios: list[int],
    ajustar_bonificaciones: bool = True,
    factor_bonif: float = FACTOR_BONIF_DEFAULT,
) -> pd.DataFrame:
    """Devuelve el pivot ejecución × año, con desagregado de 51 y 52.

    Columnas: grupo, <anio_1>, <anio_2>, ..., Total
    Valores: en PESOS, con signo contable (raw).
    """
    if not anios:
        return pd.DataFrame()

    con = conectar(read_only=True)
    try:
        ph_anios = ",".join(["?"] * len(anios))
        df = con.execute(
            f"""
            SELECT grupo, subgrupo, anio, SUM(movimiento) AS valor
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE anio IN ({ph_anios})
              AND grupo IS NOT NULL AND grupo != 'LQORDER'
            GROUP BY grupo, subgrupo, anio
            """,
            anios,
        ).df()

        if ajustar_bonificaciones:
            grupos_origen = list(BONIF_MAPPING.keys())
            ph_grp = ",".join(["?"] * len(grupos_origen))
            df_bonif = con.execute(
                f"""
                SELECT grupo, anio, SUM(movimiento) AS bonif
                FROM contabilidad.fact_ejecucion_clasificada
                WHERE LOWER(nombre_cuenta) LIKE 'bonif%'
                  AND anio IN ({ph_anios})
                  AND grupo IN ({ph_grp})
                GROUP BY grupo, anio
                """,
                anios + grupos_origen,
            ).df()
        else:
            df_bonif = pd.DataFrame(columns=["grupo", "anio", "bonif"])
    finally:
        con.close()

    if df.empty:
        return pd.DataFrame()

    df = _agregar_columna_clave(df)
    pivot = df.pivot_table(
        index="__clave",
        columns="anio",
        values="valor",
        aggfunc="sum",
        fill_value=0.0,
    )

    if not df_bonif.empty:
        for clave in set(BONIF_MAPPING.keys()) | set(BONIF_MAPPING.values()):
            if clave not in pivot.index:
                pivot.loc[clave] = 0.0
        for _, row in df_bonif.iterrows():
            grupo_o = row["grupo"]
            grupo_d = BONIF_MAPPING[grupo_o]
            anio = int(row["anio"])
            ajuste = float(row["bonif"]) * factor_bonif
            if anio in pivot.columns:
                pivot.loc[grupo_o, anio] -= ajuste
                pivot.loc[grupo_d, anio] += ajuste

    pivot["Total"] = pivot.sum(axis=1)
    pivot = pivot.sort_index().reset_index().rename(columns={"__clave": "grupo"})
    return pivot


def exportar_ejecucion_excel(pivot: pd.DataFrame, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df = pivot.copy()
    df = df.rename(columns={"grupo": "Grupo / Detalle"})
    df.to_excel(ruta, index=False, sheet_name="Ejecución")
    return ruta
