"""Página UI del submódulo 'Ejecución presupuestal'.

- Checkboxes por año (multi-select).
- Toggle "Ajustar bonificaciones (×1.52)" (default ON).
- Toggle "Mostrar P&L" (ingresos positivos, default ON).
- Tabla pivot grupo × años + Total.
- Botón Exportar Excel.
"""
from pathlib import Path

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox, QFileDialog, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from src.modulos.m2_presupuesto.submodulos.ejecucion_presupuestal import (
    exportar_ejecucion_excel, listar_anios_disponibles, obtener_ejecucion_pivot,
)
from src.ui.modelos_qt import PandasModel
from src.ui.widgets.navegacion import BarraNavegacion


class PaginaEjecucionPresupuestal(QWidget):
    def __init__(self, navegador):
        super().__init__()
        self.navegador = navegador
        self._pivot_actual: pd.DataFrame | None = None
        self._anio_checks: dict[int, QCheckBox] = {}
        self._construir_ui()
        self._refrescar()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        layout.addWidget(BarraNavegacion(
            "Ejecución presupuestal",
            on_atras=self.navegador.volver,
            on_salir=self.navegador.salir,
        ))

        try:
            anios = listar_anios_disponibles()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los años: {e}")
            anios = []

        year_row = QHBoxLayout()
        year_row.addWidget(QLabel("Años:"))
        max_anio = max(anios) if anios else 0
        for anio in anios:
            cb = QCheckBox(str(anio))
            cb.setChecked(anio >= max_anio - 2)  # default: últimos 3
            cb.stateChanged.connect(self._refrescar)
            self._anio_checks[anio] = cb
            year_row.addWidget(cb)
        year_row.addStretch()
        layout.addLayout(year_row)

        toggles_row = QHBoxLayout()
        self.cb_bonif = QCheckBox(
            "Ajustar bonificaciones (×1.52)  ·  11→12, 21→22, 31→32"
        )
        self.cb_bonif.setChecked(True)
        self.cb_bonif.setToolTip(
            "Mueve las bonificaciones cargadas en grupos de personal "
            "(11, 21, 31) hacia su par de gastos no personal (12, 22, 32), "
            "aplicando el factor 1.52 (prestaciones)."
        )
        self.cb_bonif.stateChanged.connect(self._refrescar)
        toggles_row.addWidget(self.cb_bonif)

        toggles_row.addSpacing(24)
        self.cb_pyg = QCheckBox("Mostrar P&L (ingresos en positivo)")
        self.cb_pyg.setChecked(True)
        self.cb_pyg.setToolTip(
            "Multiplica los valores por -1 para que los ingresos aparezcan "
            "positivos y los gastos negativos, como en tu reporte de Power BI."
        )
        self.cb_pyg.stateChanged.connect(self._refrescar)
        toggles_row.addWidget(self.cb_pyg)

        toggles_row.addStretch()
        layout.addLayout(toggles_row)

        self.tabla = QTableView()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self.tabla, 1)

        bottom = QHBoxLayout()
        self.lbl_estado = QLabel("")
        self.lbl_estado.setStyleSheet("color: #555;")
        bottom.addWidget(self.lbl_estado, 1)
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setMinimumWidth(150)
        self.btn_exportar.clicked.connect(self._on_exportar)
        bottom.addWidget(self.btn_exportar)
        layout.addLayout(bottom)

    def _anios_seleccionados(self) -> list[int]:
        return sorted(a for a, cb in self._anio_checks.items() if cb.isChecked())

    def _refrescar(self):
        anios = self._anios_seleccionados()
        if not anios:
            self.tabla.setModel(None)
            self.lbl_estado.setText("Selecciona al menos un año.")
            self._pivot_actual = None
            return

        try:
            pivot = obtener_ejecucion_pivot(
                anios=anios,
                ajustar_bonificaciones=self.cb_bonif.isChecked(),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error al consultar", str(e))
            return

        self._pivot_actual = pivot.copy()

        display = pivot.copy()
        sign = -1.0 if self.cb_pyg.isChecked() else 1.0
        anio_cols = [c for c in display.columns if c != "grupo"]
        for col in anio_cols:
            display[col] = display[col] * sign / 1e6

        display.columns = [str(c) for c in display.columns]
        num_cols = {str(c) for c in anio_cols}
        self.tabla.setModel(PandasModel(display, columnas_numericas=num_cols))
        self.tabla.resizeColumnsToContents()
        self.tabla.setColumnWidth(0, max(self.tabla.columnWidth(0), 280))

        bonif = "con ajuste bonif" if self.cb_bonif.isChecked() else "sin ajuste bonif"
        signo = "P&L" if self.cb_pyg.isChecked() else "contable"
        self.lbl_estado.setText(
            f"{len(pivot)} grupos · Años: {', '.join(str(a) for a in anios)} · "
            f"{bonif} · Signo {signo} · Valores en millones"
        )

    def _on_exportar(self):
        if self._pivot_actual is None or self._pivot_actual.empty:
            QMessageBox.warning(self, "Sin datos", "No hay datos para exportar.")
            return
        anios = self._anios_seleccionados()
        sufijo = "_".join(str(a) for a in anios)
        nombre = f"ejecucion_{sufijo}.xlsx"
        ruta_str, _ = QFileDialog.getSaveFileName(
            self, "Exportar ejecución", nombre, "Excel (*.xlsx)"
        )
        if not ruta_str:
            return
        try:
            ruta = exportar_ejecucion_excel(self._pivot_actual, Path(ruta_str))
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(
            self, "Exportado",
            f"Guardado: {ruta}\n\n"
            f"Valores en PESOS, signo contable raw. "
            f"Para tu reporte podés multiplicar por -1 en Excel.",
        )
