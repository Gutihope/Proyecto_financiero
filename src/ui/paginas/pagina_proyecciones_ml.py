"""Pagina del modulo 'Proyecciones con Machine Learning'."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from src.ui.widgets.navegacion import BarraNavegacion, TarjetaModulo


class PaginaProyeccionesML(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(BarraNavegacion(
            "Proyecciones con Machine Learning",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        sub = QLabel(
            "Modelos predictivos para proyectar ingresos, gastos y "
            "matrícula a partir de la historia. Usar para forecast de cierre, "
            "escenarios de presupuesto y detección temprana de anomalías."
        )
        sub.setStyleSheet("color: #666;")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        from src.ui.paginas.pagina_placeholder import PaginaPlaceholder

        submodulos = [
            ("Proyección de\ningresos x grupo", False,
             "Serie temporal por grupo de ingreso, próximos N meses",
             "Proyección de Ingresos"),
            ("Proyección de\ngastos x grupo", False,
             "Serie temporal por grupo de gasto, próximos N meses",
             "Proyección de Gastos"),
            ("Comparativo\nreal vs modelo", False,
             "Backtesting: lo que el modelo predijo vs lo que realmente pasó",
             "Real vs Modelo"),
            ("Modelos\nentrenados", False,
             "Inventario de modelos, métricas (MAE, RMSE) y reentrenamiento",
             "Modelos Entrenados"),
        ]

        for idx, (nombre, habilitado, descripcion, ph_name) in enumerate(submodulos):
            row, col = divmod(idx, 4)
            tarjeta = TarjetaModulo(
                titulo=nombre,
                descripcion=("" if habilitado else "Próximamente"),
                habilitado=habilitado,
                on_click=(lambda n=ph_name: self.navegador.navegar_a(
                    PaginaPlaceholder(self.navegador, n))),
            )
            tarjeta.setToolTip(descripcion)
            grid.addWidget(tarjeta, row, col)

        layout.addLayout(grid)
        layout.addStretch()
