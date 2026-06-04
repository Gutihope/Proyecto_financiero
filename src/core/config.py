from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


def cargar_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ruta_fuente(relativa: str) -> Path:
    cfg = cargar_config()
    return Path(cfg["fuentes"]["ruta_base"]) / relativa


def ruta_db() -> Path:
    cfg = cargar_config()
    return PROJECT_ROOT / cfg["db"]["ruta"]
