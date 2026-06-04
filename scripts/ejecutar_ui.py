"""Lanza la UI de escritorio (PySide6)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from src.ui.main_window import VentanaPrincipal


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ventana = VentanaPrincipal()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
