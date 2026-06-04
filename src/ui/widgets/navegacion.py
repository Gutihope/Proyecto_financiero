"""Widgets reutilizables para la navegacion entre paginas."""
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget


class BarraNavegacion(QWidget):
    """Barra superior con botones Atras + Salir + titulo de la pagina."""

    def __init__(
        self,
        titulo: str,
        on_atras: Callable | None = None,
        on_salir: Callable | None = None,
        mostrar_atras: bool = True,
    ):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 8)
        layout.setSpacing(8)

        if mostrar_atras:
            btn_atras = QPushButton("← Atrás")
            btn_atras.setMinimumWidth(100)
            btn_atras.setCursor(Qt.PointingHandCursor)
            if on_atras:
                btn_atras.clicked.connect(on_atras)
            layout.addWidget(btn_atras)

        btn_salir = QPushButton("✕ Salir")
        btn_salir.setMinimumWidth(90)
        btn_salir.setCursor(Qt.PointingHandCursor)
        if on_salir:
            btn_salir.clicked.connect(on_salir)
        layout.addWidget(btn_salir)

        layout.addSpacing(20)
        lbl = QLabel(titulo)
        font = lbl.font()
        font.setPointSize(font.pointSize() + 5)
        font.setBold(True)
        lbl.setFont(font)
        layout.addWidget(lbl)

        layout.addStretch()


class TarjetaModulo(QPushButton):
    """Tarjeta clickeable para representar un modulo o submodulo en la pagina."""

    def __init__(
        self,
        titulo: str,
        descripcion: str = "",
        habilitado: bool = True,
        on_click: Callable | None = None,
    ):
        texto = titulo if not descripcion else f"{titulo}\n\n{descripcion}"
        super().__init__(texto)
        self.setEnabled(habilitado)
        self.setMinimumSize(220, 140)
        self.setMaximumWidth(280)
        self.setCursor(Qt.PointingHandCursor if habilitado else Qt.ArrowCursor)
        self.setStyleSheet("""
            QPushButton {
                font-size: 13px;
                font-weight: bold;
                border: 2px solid #5d8aa8;
                border-radius: 10px;
                background-color: #f4f8fb;
                color: #234;
                padding: 10px;
                text-align: center;
            }
            QPushButton:hover:enabled {
                background-color: #dceaf3;
                border-color: #3a5d72;
            }
            QPushButton:pressed:enabled {
                background-color: #c1d6e3;
            }
            QPushButton:disabled {
                background-color: #f7f7f7;
                color: #aaa;
                border-color: #ddd;
                border-style: dashed;
            }
        """)
        if on_click and habilitado:
            self.clicked.connect(on_click)
