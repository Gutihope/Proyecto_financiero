"""Pagina placeholder generica para modulos/submodulos aun no implementados."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.ui.widgets.navegacion import BarraNavegacion


class PaginaPlaceholder(QWidget):
    def __init__(self, navegador, nombre: str):
        super().__init__()
        self.navegador = navegador
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(BarraNavegacion(
            nombre,
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        msg = QLabel(f"El módulo \"{nombre}\" está en construcción.")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet("color: #888; font-size: 16px;")
        layout.addStretch()
        layout.addWidget(msg)
        layout.addStretch()
