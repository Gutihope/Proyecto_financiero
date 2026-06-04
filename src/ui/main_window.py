"""Ventana principal: stack de paginas con navegacion."""
from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget

from src.ui.paginas.pagina_home import PaginaHome


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modelo Financiero Unicafam")
        self.resize(1400, 800)

        self.stack = QStackedWidget()
        self._historial: list[QWidget] = []
        self.setCentralWidget(self.stack)

        home = PaginaHome(navegador=self)
        self.stack.addWidget(home)
        self.stack.setCurrentWidget(home)

    def navegar_a(self, widget: QWidget) -> None:
        actual = self.stack.currentWidget()
        if actual is not None:
            self._historial.append(actual)
        self.stack.addWidget(widget)
        self.stack.setCurrentWidget(widget)

    def volver(self) -> None:
        if not self._historial:
            return
        previa = self._historial.pop()
        actual = self.stack.currentWidget()
        self.stack.setCurrentWidget(previa)
        if actual is not None and actual is not previa:
            self.stack.removeWidget(actual)
            actual.deleteLater()

    def salir(self) -> None:
        self.close()
