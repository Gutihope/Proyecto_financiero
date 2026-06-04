# Modelo Financiero Unicafam

Herramienta de escritorio para integrar la información financiera y administrativa de la Fundación Universitaria Cafam.

## Módulos

1. **Modelo financiero** (`src/modulos/m1_modelo_financiero/`)
2. **Presupuesto y ejecución** (`src/modulos/m2_presupuesto/`) — en construcción
3. **Estudiantes** (`src/modulos/m3_estudiantes/`)
4. **Contabilidad y tesorería** (`src/modulos/m4_contabilidad_tesoreria/`)
5. **Espacios físicos** (`src/modulos/m5_espacios/`)

Todos los módulos comparten una única base **DuckDB** (`data/unicafam.duckdb`) con dimensiones reutilizables.

## Estructura

```
unicafam_modelo_financiero/
├── config.yaml                 # rutas de archivos fuente y módulos activos
├── data/                       # unicafam.duckdb (ignorado por git)
├── sql/                        # SQL puro: vistas, migraciones, agregados
│   ├── dim/                    # creación de tablas dimensión
│   ├── contabilidad/           # fact_movimiento_contable, fact_grupos_subgrupos
│   ├── m1_modelo_financiero/
│   ├── m2_presupuesto/
│   ├── m3_estudiantes/
│   ├── m4_contabilidad_tesoreria/
│   └── m5_espacios/
├── src/
│   ├── core/                   # conexión db, config, logging
│   ├── etl/                    # un subpaquete por fuente
│   │   ├── dims/
│   │   ├── contabilidad/
│   │   ├── grupos_subgrupos/
│   │   ├── presupuesto/
│   │   ├── estudiantes/
│   │   ├── tesoreria/
│   │   └── espacios/
│   ├── modulos/                # lógica de negocio de cada módulo
│   │   ├── m1_modelo_financiero/
│   │   ├── m2_presupuesto/submodulos/
│   │   └── ...
│   └── ui/                     # PySide6 — ventana principal + tabs
├── scripts/                    # utilidades (cargar todo, exportar, etc.)
├── tests/
└── docs/
```

## Cómo agregar datos

- **Nuevo año de Movimiento contable**: copiar el `.xlsx` en `datos/Estado resultado Movimiento contable/` y correr el ETL.
- **Nuevo año de Grupos y Subgrupos**: copiar el `.xlsx` en `datos/Estado de Resultado Grupos y Subgrupos/`.
- **Presupuesto aprobado**: dejar el `.xlsx` en `datos/Estado de Resultado Presupuesto/`.
- **Nueva fuente académica**: agregar la ruta en `config.yaml > fuentes.estudiantes` y crear el ETL correspondiente en `src/etl/estudiantes/`.

El ETL es **idempotente**: re-cargar un archivo reemplaza ese año/dimensión sin duplicar.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m scripts.cargar_todo
```
