from PySide6.QtWidgets import QMainWindow, QTabWidget

from src.ui.tabs.tab_crear_presupuesto import TabCrearPresupuesto


class VentanaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Modelo Financiero Unicafam")
        self.resize(1400, 800)

        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        tabs.addTab(TabCrearPresupuesto(), "1. Crear presupuesto mensual")

        self.setCentralWidget(tabs)
