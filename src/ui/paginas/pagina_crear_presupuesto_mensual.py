"""Pagina envoltura del Submodulo 1 con barra de navegacion encima."""
from PySide6.QtWidgets import QVBoxLayout, QWidget

from src.ui.tabs.tab_crear_presupuesto import TabCrearPresupuesto
from src.ui.widgets.navegacion import BarraNavegacion


class PaginaCrearPresupuestoMensual(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(4)

        layout.addWidget(BarraNavegacion(
            "Crear presupuesto mensual",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        self.contenido = TabCrearPresupuesto()
        layout.addWidget(self.contenido, 1)
