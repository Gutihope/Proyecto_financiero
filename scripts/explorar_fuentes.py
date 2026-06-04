"""Inspecciona las columnas y unas filas de las fuentes para verificar el modelo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from src.core.config import cargar_config, ruta_fuente


def mostrar(nombre: str, df: pd.DataFrame, n: int = 3):
    print(f"\n{'='*80}\n{nombre}\n{'='*80}")
    print(f"Shape: {df.shape}")
    print(f"\nColumnas ({len(df.columns)}):")
    for i, c in enumerate(df.columns, 1):
        print(f"  {i:2d}. {c!r}")
    print(f"\nPrimeras {n} filas:")
    with pd.option_context("display.max_columns", None, "display.width", 200):
        print(df.head(n))


def main():
    cfg = cargar_config()

    base = Path(cfg["fuentes"]["ruta_base"])
    print(f"Base de fuentes: {base}\nExiste: {base.exists()}")

    movim_dir = base / "datos" / "Estado resultado Movimiento contable"
    archivos_mov = sorted(movim_dir.glob("*.xlsx"))
    print(f"\nArchivos Movimiento Contable encontrados: {len(archivos_mov)}")
    for a in archivos_mov:
        print(f"  - {a.name}")

    grupos_dir = base / "datos" / "Estado de Resultado Grupos y Subgrupos"
    archivos_grp = sorted(grupos_dir.glob("*.xlsx"))
    print(f"\nArchivos Grupos y Subgrupos encontrados: {len(archivos_grp)}")
    for a in archivos_grp:
        print(f"  - {a.name}")

    if archivos_mov:
        df_mov = pd.read_excel(archivos_mov[-1], nrows=3)
        mostrar(f"Movimiento Contable — {archivos_mov[-1].name}", df_mov)

    if archivos_grp:
        df_grp = pd.read_excel(archivos_grp[-1], nrows=3)
        mostrar(f"Grupos y Subgrupos — {archivos_grp[-1].name}", df_grp)

    txt_id = grupos_dir / "id de grupo.txt"
    if txt_id.exists():
        contenido = txt_id.read_text(encoding="utf-8").strip()
        print(f"\n{'='*80}\nid de grupo.txt:\n{'='*80}\n{contenido!r}")
        cols_clave = [c.strip() for c in contenido.split(",")]
        print(f"Columnas clave normalizadas ({len(cols_clave)}): {cols_clave}")


if __name__ == "__main__":
    main()
