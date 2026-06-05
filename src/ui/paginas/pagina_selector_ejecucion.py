"""Pagina selector de perspectiva de la Ejecucion Presupuestal.

Muestra una tarjeta por perspectiva (Fosfec Emp, Fosfec CEC, Extension,
Posgrado, etc.) y una para Institucional (vista completa con todos los
grupos). Al hacer click navega a PaginaEjecucionPresupuestal con el
filtro de claves correspondiente.
"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    PERSPECTIVAS,
)
from src.ui.widgets.navegacion import BarraNavegacion, TarjetaModulo


ORDEN_PERSPECTIVAS = [
    "Fosfec Empresarial",
    "Fosfec CEC",
    "Extensión",
    "Posgrado",
    "Ingresos Pregrado",
    "Centralizados Cafam",
    "Centralizados Unicafam",
    "Generales",
    "Mercadeo",
    "Institucional",
]


DESCRIPCIONES = {
    "Fosfec Empresarial": "Ingresos + personal + no personal del programa FOSFEC Empresarial (grupos 1, 11, 12)",
    "Fosfec CEC":         "Ingresos + personal + no personal de FOSFEC CEC (grupos 2, 21, 22)",
    "Extensión":          "Ingresos + personal + no personal de Extensión y CEC (grupos 3, 31, 32)",
    "Posgrado":           "Ingresos + personal + no personal de Posgrado (grupos 4, 41, 42)",
    "Ingresos Pregrado":  "Solo ingresos de Pregrado (grupo 5)",
    "Centralizados Cafam":   "Gastos centralizados de Cafam (52 · Cafam)",
    "Centralizados Unicafam":"Gastos centralizados de Unicafam (52 · Unicafam)",
    "Generales":          "Gastos generales (55)",
    "Mercadeo":           "Publicidad y mercadeo (57)",
    "Institucional":      "Vista consolidada con TODOS los grupos (P&G institucional completo)",
}


class PaginaSelectorEjecucion(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(BarraNavegacion(
            "Ejecución Presupuestal — selecciona perspectiva",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        sub = QLabel(
            "Cada perspectiva muestra solo sus grupos relevantes. "
            "El excedente que aparece al final es el aporte de esa "
            "perspectiva al excedente institucional. "
            "‘Institucional’ es el consolidado con todos los grupos."
        )
        sub.setStyleSheet("color: #666;")
        sub.setWordWrap(True)
        layout.addWidget(sub)
        layout.addSpacing(8)

        from src.ui.paginas.pagina_ejecucion_presupuestal import (
            PaginaEjecucionPresupuestal,
        )

        grid = QGridLayout()
        grid.setSpacing(14)
        grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        for idx, nombre in enumerate(ORDEN_PERSPECTIVAS):
            row, col = divmod(idx, 4)
            claves = PERSPECTIVAS[nombre]
            es_institucional = nombre == "Institucional"

            def crear_handler(n=nombre, c=claves):
                def handler():
                    self.navegador.navegar_a(PaginaEjecucionPresupuestal(
                        self.navegador,
                        claves_filter=c,
                        titulo_perspectiva=n,
                    ))
                return handler

            tarjeta = TarjetaModulo(
                titulo=nombre,
                descripcion=("Vista completa" if es_institucional else ""),
                habilitado=True,
                on_click=crear_handler(),
            )
            tarjeta.setToolTip(DESCRIPCIONES[nombre])

            if es_institucional:
                tarjeta.setStyleSheet(tarjeta.styleSheet() + """
                    QPushButton {
                        background-color: #fff5d6;
                        border-color: #c89a3a;
                    }
                    QPushButton:hover:enabled {
                        background-color: #ffe89a;
                    }
                """)

            grid.addWidget(tarjeta, row, col)

        layout.addLayout(grid)
        layout.addStretch()
