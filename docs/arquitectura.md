# Arquitectura

## Base de datos

Una sola base **DuckDB** (`data/unicafam.duckdb`) con schemas separados por módulo:

| Schema | Contenido |
|---|---|
| `dim` | Dimensiones compartidas: centros_costos, cuenta_contable, fecha, periodo, tercero |
| `contabilidad` | `fact_movimiento_contable`, `stg_grupos_subgrupos`, `fact_ejecucion_clasificada` (vista) |
| `presupuesto` | `fact_presupuesto`, vistas de comparativo, forecast, alertas |
| `estudiantes` | (futuro) matrículas, programas, notas, deserción |
| `tesoreria` | (futuro) flujo de caja, cartera, pagos |
| `espacios` | (futuro) salones, ocupación, mantenimiento |

## Llave de Grupos y Subgrupos

El archivo `id de grupo.txt` define las 9 columnas que conforman el ID:

```
Cuenta + Centro de Responsabilidad + Tercero + Comprobante + Documento + Referencia + Mes + Movimiento + Fuente
```

Esta concatenación permite unir `Movimiento contable` (39 cols) con `Grupos y Subgrupos` (ID, Grupo, Subgrupo).

## ETL — idempotencia

Cada cargador (`src/etl/<fuente>/`) sigue el patrón:

1. Listar archivos del glob configurado.
2. Por cada archivo, derivar la "partición" (año, o nombre de archivo).
3. `DELETE FROM tabla WHERE particion = X` + `INSERT` desde Excel.

Re-cargar un archivo no duplica filas.

## Flujo

```
Excel (OneDrive/Downloads)
        │
        ▼  ETL idempotente
   unicafam.duckdb  ──── vistas SQL ────  módulos UI (PySide6)
                                                │
                                                ▼
                                       Exportar Excel
```
