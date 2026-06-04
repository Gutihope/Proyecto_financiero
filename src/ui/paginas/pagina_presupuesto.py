"""Pagina del modulo Presupuesto: lista los submodulos disponibles."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from src.ui.widgets.navegacion import BarraNavegacion, TarjetaModulo


class PaginaPresupuesto(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(BarraNavegacion(
            "Presupuesto",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        sub = QLabel("Selecciona un submódulo")
        sub.setStyleSheet("color: #666;")
        layout.addWidget(sub)
        layout.addSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        from src.ui.paginas.pagina_crear_presupuesto_mensual import (
            PaginaCrearPresupuestoMensual,
        )
        from src.ui.paginas.pagina_placeholder import PaginaPlaceholder

        submodulos = [
            ("Crear presupuesto\nmensual", True, lambda: self.navegador.navegar_a(
                PaginaCrearPresupuestoMensual(self.navegador))),
            ("Ejecución\npresupuestal", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Ejecución presupuestal"))),
            ("Comparativo\npresupuesto vs ejecución", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Comparativo presupuesto vs ejecución"))),
            ("Variaciones y\nalertas", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Variaciones y alertas"))),
            ("Forecast /\ncierre proyectado", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Forecast / cierre proyectado"))),
        ]

        for idx, (nombre, habilitado, accion) in enumerate(submodulos):
            row, col = divmod(idx, 4)
            tarjeta = TarjetaModulo(
                titulo=nombre,
                descripcion=("" if habilitado else "Próximamente"),
                habilitado=habilitado,
                on_click=accion,
            )
            grid.addWidget(tarjeta, row, col)

        layout.addLayout(grid)
        layout.addStretch()
