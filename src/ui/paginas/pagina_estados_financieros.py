"""Pagina del modulo 'Estados Financieros de Prueba'."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from src.ui.widgets.navegacion import BarraNavegacion, TarjetaModulo


class PaginaEstadosFinancieros(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(BarraNavegacion(
            "Estados Financieros de Prueba",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        sub = QLabel(
            "Reportes financieros tipo borrador, construidos sobre los "
            "movimientos contables que ya tienes cargados."
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
            ("Estado de\nResultados (P&G)", False,
             "Ingresos, gastos y excedente por jerarquía contable",
             "Estado de Resultados"),
            ("Balance General\n(de prueba)", False,
             "Activos / Pasivos / Patrimonio a una fecha de corte",
             "Balance General"),
            ("Flujo de Caja\n(estimado)", False,
             "Entradas y salidas por mes y origen",
             "Flujo de Caja"),
            ("Indicadores\nfinancieros", False,
             "Liquidez, margen, ROA, ROE",
             "Indicadores Financieros"),
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
