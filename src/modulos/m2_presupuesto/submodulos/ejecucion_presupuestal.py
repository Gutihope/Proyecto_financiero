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
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.core.config import PROJECT_ROOT
from src.core.db import conectar
from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    _agregar_columna_clave,
)


def _obtener_presupuesto_por_anio(
    anio: int,
    mes_desde: int = 1,
    mes_hasta: int = 12,
) -> dict[str, dict[str, float]] | None:
    """Lee data/aprobado_<anio>.json y calcula presupuesto anual y por periodo.

    Returns dict[clave_aprobado, {'anual': pesos, 'periodo': pesos}] o None si
    no existe el JSON o esta vacio.

    El periodo se calcula prorrateando el aprobado anual con el patron de
    ejecucion del anio anterior (anio-1). Si no hay datos, prorrateo lineal.
    """
    ruta = PROJECT_ROOT / "data" / f"aprobado_{anio}.json"
    if not ruta.exists():
        return None
    try:
        aprobado_millones = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return None
    aprobado_pesos = {k: float(v) * 1_000_000 for k, v in aprobado_millones.items()}
    if not aprobado_pesos:
        return None

    patron_anio = anio - 1
    con = conectar(read_only=True)
    try:
        df_patron = con.execute(
            """
            SELECT grupo, subgrupo, mes, SUM(movimiento) AS valor
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE anio = ?
              AND grupo IS NOT NULL AND grupo != 'LQORDER'
            GROUP BY grupo, subgrupo, mes
            """,
            [patron_anio],
        ).df()
    finally:
        con.close()

    if df_patron.empty:
        df_patron = pd.DataFrame(columns=["grupo", "subgrupo", "mes", "valor"])
    else:
        df_patron = _agregar_columna_clave(df_patron)
        df_patron["valor_abs"] = df_patron["valor"].abs()

    if not df_patron.empty:
        suma_full = df_patron.groupby("__clave")["valor_abs"].sum()
        suma_per = df_patron[
            df_patron["mes"].between(mes_desde, mes_hasta)
        ].groupby("__clave")["valor_abs"].sum()
    else:
        suma_full = pd.Series(dtype=float)
        suma_per = pd.Series(dtype=float)

    ratio_default = (mes_hasta - mes_desde + 1) / 12.0
    out: dict[str, dict[str, float]] = {}
    for clave, anual_pesos in aprobado_pesos.items():
        full = float(suma_full.get(clave, 0.0))
        periodo = float(suma_per.get(clave, 0.0))
        ratio = periodo / full if full > 0 else ratio_default
        out[clave] = {
            "anual": float(anual_pesos),
            "periodo": float(anual_pesos) * ratio,
        }
    return out


def _agregar_variaciones(
    pivot: pd.DataFrame,
    anios: list[int],
    presupuesto_por_anio: dict[int, dict] | None = None,
    incluir_variaciones: bool = True,
) -> pd.DataFrame:
    """Inserta columnas calculadas (vs presupuesto + variaciones interanuales).

    Por cada anio inserta, en este orden:
      year_n
      %Año <n>, %Mes <n>           (si presupuesto_por_anio[n] existe)
      %Δ <prev>→<n>, Δ <prev>→<n>  (si i > 0 e incluir_variaciones)

    Formulas (todas en magnitudes |x|):
      %Año <n> = |ejec_n_periodo| / presupuesto_anual_n * 100
      %Mes <n> = |ejec_n_periodo| / presupuesto_periodo_n * 100
      %Δ      = (|n| - |n-1|) / |n-1| * 100
      Δ        =  |n| - |n-1|
    """
    if not anios:
        return pivot

    pivot = pivot.copy()
    nuevas_cols = ["grupo"]

    for i, anio in enumerate(anios):
        nuevas_cols.append(anio)

        if presupuesto_por_anio and anio in presupuesto_por_anio:
            preset = presupuesto_por_anio[anio]
            col_pa = f"%Año {anio}"
            col_pm = f"%Mes {anio}"
            ejec_abs = pivot[anio].abs()
            pres_anual = pivot["grupo"].map(
                lambda k: preset.get(k, {}).get("anual")
            )
            pres_periodo = pivot["grupo"].map(
                lambda k: preset.get(k, {}).get("periodo")
            )
            with np.errstate(divide="ignore", invalid="ignore"):
                pivot[col_pa] = np.where(
                    pres_anual.notna() & (pres_anual > 0),
                    ejec_abs / pres_anual * 100,
                    np.nan,
                )
                pivot[col_pm] = np.where(
                    pres_periodo.notna() & (pres_periodo > 0),
                    ejec_abs / pres_periodo * 100,
                    np.nan,
                )
            nuevas_cols.append(col_pa)
            nuevas_cols.append(col_pm)

        if i > 0 and incluir_variaciones:
            prev = anios[i - 1]
            col_pct = f"%Δ {prev}→{anio}"
            col_abs = f"Δ {prev}→{anio}"
            prev_abs = pivot[prev].abs()
            curr_abs = pivot[anio].abs()
            with np.errstate(divide="ignore", invalid="ignore"):
                pivot[col_pct] = np.where(
                    prev_abs > 0,
                    (curr_abs - prev_abs) / prev_abs * 100,
                    np.nan,
                )
            pivot[col_abs] = curr_abs - prev_abs
            nuevas_cols.append(col_pct)
            nuevas_cols.append(col_abs)

    if "Total" in pivot.columns:
        nuevas_cols.append("Total")
    return pivot[nuevas_cols]


BONIF_MAPPING: dict[str, str] = {
    "11 Gastos FOSFEC Empresarial Personal": "12. Gastos FOSFEC Empresarial",
    "21. Gastos Fosfec Personal":            "22. Gastos Fosfec CEC",
    "31. Gastos  Extensión y CEC Personal":  "32. Gastos  Extensión y CEC",
}
FACTOR_BONIF_DEFAULT = 1.52


# Perspectivas de la Ejecucion Presupuestal.
# Cada perspectiva filtra el pivot a un conjunto de claves (grupo o
# "grupo · subgrupo"). La perspectiva 'Institucional' (None) muestra todo.
PERSPECTIVAS: dict[str, list[str] | None] = {
    "Fosfec Empresarial": [
        "1. Ingresos FOSFEC Empresarial",
        "11 Gastos FOSFEC Empresarial Personal",
        "12. Gastos FOSFEC Empresarial",
    ],
    "Fosfec CEC": [
        "2. Ingresos FOSFEC",
        "21. Gastos Fosfec Personal",
        "22. Gastos Fosfec CEC",
    ],
    "Extensión": [
        "3. Ingresos Extensión y CEC",
        "31. Gastos  Extensión y CEC Personal",
        "32. Gastos  Extensión y CEC",
    ],
    "Posgrado": [
        "4. Ingresos Posgrado",
        "41. Gastos Posgrado Personal",
        "42. Gastos Posgrados",
    ],
    "Ingresos Pregrado": [
        "5. Ingresos Pregrado",
    ],
    "Centralizados Cafam": [
        "52. Centralizados · Centralizados Cafam",
    ],
    "Centralizados Unicafam": [
        "52. Centralizados · Centralizados Unicafam",
    ],
    "Generales": [
        "55. Generales",
    ],
    "Mercadeo": [
        "57. Publicidad y Mercadeo",
    ],
    "Institucional": None,
}


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
    mes_desde: int = 1,
    mes_hasta: int = 12,
    ajustar_bonificaciones: bool = True,
    factor_bonif: float = FACTOR_BONIF_DEFAULT,
    incluir_variaciones: bool = True,
    incluir_vs_presupuesto: bool = False,
    claves_filter: list[str] | None = None,
) -> pd.DataFrame:
    """Devuelve el pivot ejecución × año, con desagregado de 51 y 52.

    - Filtra por rango de meses [mes_desde, mes_hasta] (ambos inclusive).
    - Aplica el ajuste de bonificaciones (×factor_bonif) si se pide.
    - Inserta columnas de %Δ entre anios consecutivos si incluir_variaciones.

    Columnas: grupo, <anio1>, [%Δ a1→a2], <anio2>, ..., Total
    Valores: PESOS con signo contable (raw). Las variaciones ya son porcentaje.
    """
    if not anios:
        return pd.DataFrame()

    # Normalizar rango de meses
    if mes_desde > mes_hasta:
        mes_desde, mes_hasta = mes_hasta, mes_desde
    mes_desde = max(1, min(12, mes_desde))
    mes_hasta = max(1, min(12, mes_hasta))
    anios = sorted(anios)

    con = conectar(read_only=True)
    try:
        ph_anios = ",".join(["?"] * len(anios))
        df = con.execute(
            f"""
            SELECT grupo, subgrupo, anio, SUM(movimiento) AS valor
            FROM contabilidad.fact_ejecucion_clasificada
            WHERE anio IN ({ph_anios})
              AND mes BETWEEN ? AND ?
              AND grupo IS NOT NULL AND grupo != 'LQORDER'
            GROUP BY grupo, subgrupo, anio
            """,
            anios + [mes_desde, mes_hasta],
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
                  AND mes BETWEEN ? AND ?
                  AND grupo IN ({ph_grp})
                GROUP BY grupo, anio
                """,
                anios + [mes_desde, mes_hasta] + grupos_origen,
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

    presupuesto_por_anio: dict[int, dict] | None = None
    if incluir_vs_presupuesto:
        presupuesto_por_anio = {}
        for anio in anios:
            data = _obtener_presupuesto_por_anio(anio, mes_desde, mes_hasta)
            if data:
                presupuesto_por_anio[anio] = data
        if not presupuesto_por_anio:
            presupuesto_por_anio = None

    if incluir_variaciones or presupuesto_por_anio:
        pivot = _agregar_variaciones(
            pivot, anios,
            presupuesto_por_anio=presupuesto_por_anio,
            incluir_variaciones=incluir_variaciones,
        )

    # Filtrar a perspectiva (set de claves) antes de calcular el excedente,
    # asi el excedente refleja la perspectiva, no el total institucional.
    if claves_filter:
        pivot = pivot[pivot["grupo"].isin(claves_filter)].reset_index(drop=True)

    pivot = _agregar_fila_excedente(pivot, anios)
    return pivot


def _agregar_fila_excedente(pivot: pd.DataFrame, anios: list[int]) -> pd.DataFrame:
    """Agrega una fila al final con el Excedente (sumatoria de todos los grupos).

    - Columnas de año: suma cruda (raw signed). En P&L queda + si hubo utilidad.
    - %Δ y Δ entre años: recomputa usando magnitudes de los excedentes totales.
    - %Año y %Mes: vacíos (el excedente combina ingresos y gastos, comparar contra
      presupuesto requeriría definir el "excedente aprobado" — sin claridad aún).
    """
    if pivot.empty or "grupo" not in pivot.columns:
        return pivot

    fila: dict = {"grupo": "Excedente"}

    for anio in anios:
        if anio in pivot.columns:
            fila[anio] = float(pivot[anio].sum())
    if "Total" in pivot.columns:
        fila["Total"] = float(pivot["Total"].sum())

    if len(anios) >= 2:
        for i in range(1, len(anios)):
            prev = anios[i - 1]
            curr = anios[i]
            col_pct = f"%Δ {prev}→{curr}"
            col_abs = f"Δ {prev}→{curr}"
            prev_abs = abs(fila.get(prev, 0.0))
            curr_abs = abs(fila.get(curr, 0.0))
            if col_pct in pivot.columns:
                fila[col_pct] = ((curr_abs - prev_abs) / prev_abs * 100
                                 if prev_abs > 0 else np.nan)
            if col_abs in pivot.columns:
                fila[col_abs] = curr_abs - prev_abs

    for col in pivot.columns:
        if isinstance(col, str) and (col.startswith("%Año") or col.startswith("%Mes")):
            fila[col] = np.nan

    fila_df = pd.DataFrame([fila]).reindex(columns=pivot.columns)
    return pd.concat([pivot, fila_df], ignore_index=True)


def exportar_ejecucion_excel(pivot: pd.DataFrame, ruta: Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df = pivot.copy()
    df = df.rename(columns={"grupo": "Grupo / Detalle"})
    df.to_excel(ruta, index=False, sheet_name="Ejecución")
    return ruta
