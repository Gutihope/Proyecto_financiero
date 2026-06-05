"""Pagina inicial: tarjetas para los 5 modulos del modelo financiero."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from src.ui.widgets.navegacion import TarjetaModulo


class PaginaHome(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("Modelo Financiero Unicafam")
        font = titulo.font()
        font.setPointSize(font.pointSize() + 10)
        font.setBold(True)
        titulo.setFont(font)
        titulo.setAlignment(Qt.AlignLeft)
        layout.addWidget(titulo)

        subtitulo = QLabel("Selecciona un módulo")
        subtitulo.setStyleSheet("color: #666;")
        layout.addWidget(subtitulo)
        layout.addSpacing(20)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        from src.ui.paginas.pagina_estados_financieros import PaginaEstadosFinancieros
        from src.ui.paginas.pagina_placeholder import PaginaPlaceholder
        from src.ui.paginas.pagina_presupuesto import PaginaPresupuesto
        from src.ui.paginas.pagina_proyecciones_ml import PaginaProyeccionesML

        modulos = [
            ("Estados Financieros\nde Prueba", True, lambda: self.navegador.navegar_a(
                PaginaEstadosFinancieros(self.navegador))),
            ("Proyecciones con\nMachine Learning", True, lambda: self.navegador.navegar_a(
                PaginaProyeccionesML(self.navegador))),
            ("Modelo Financiero", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Modelo Financiero"))),
            ("Presupuesto", True, lambda: self.navegador.navegar_a(
                PaginaPresupuesto(self.navegador))),
            ("Estudiantes", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Estudiantes"))),
            ("Contabilidad y Tesorería", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Contabilidad y Tesorería"))),
            ("Espacios Físicos", False, lambda: self.navegador.navegar_a(
                PaginaPlaceholder(self.navegador, "Espacios Físicos"))),
        ]

        for idx, (nombre, habilitado, accion) in enumerate(modulos):
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

        barra_inf = QHBoxLayout()
        barra_inf.addStretch()
        btn_salir = QPushButton("✕ Salir")
        btn_salir.setMinimumWidth(110)
        btn_salir.setCursor(Qt.PointingHandCursor)
        btn_salir.clicked.connect(self.navegador.salir)
        barra_inf.addWidget(btn_salir)
        layout.addLayout(barra_inf)
