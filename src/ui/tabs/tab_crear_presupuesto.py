"""Tab UI del Submodulo 1: Crear presupuesto mensualizado."""
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QRadioButton, QSpinBox,
    QTableView, QVBoxLayout, QWidget,
)

from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    ETIQUETA_METODO, MESES_NOMBRES,
    exportar, generar, pivot_acumulado_por_grupo,
    pivot_mensual_por_grupo, ruta_salida_default,
)
from src.ui.modelos_qt import PandasModel


METODOS_UI = [
    "ejecucion_ultimo_anio",
    "promedio_2_anios",
    "promedio_3_anios",
    "promedio_4_anios",
    "promedio_5_anios",
]


class TabCrearPresupuesto(QWidget):
    def __init__(self):
        super().__init__()
        self._df_raw: pd.DataFrame | None = None
        self._construir_ui()

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # ---------- Controles ----------
        controles = QHBoxLayout()

        controles.addWidget(QLabel("Año destino:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2018, 2050)
        self.spin_anio.setValue(2026)
        self.spin_anio.setFixedWidth(80)
        controles.addWidget(self.spin_anio)

        controles.addSpacing(24)
        controles.addWidget(QLabel("Método:"))
        self.combo_metodo = QComboBox()
        for clave in METODOS_UI:
            self.combo_metodo.addItem(ETIQUETA_METODO[clave], clave)
        self.combo_metodo.setCurrentIndex(2)
        self.combo_metodo.setMinimumWidth(240)
        controles.addWidget(self.combo_metodo)

        controles.addSpacing(24)
        self.btn_calcular = QPushButton("Calcular")
        self.btn_calcular.setMinimumWidth(110)
        self.btn_calcular.clicked.connect(self._on_calcular)
        controles.addWidget(self.btn_calcular)

        controles.addStretch()
        layout.addLayout(controles)

        # ---------- Vista (mensual / acumulada) ----------
        vista = QHBoxLayout()
        vista.addWidget(QLabel("Vista:"))
        self.rb_mensual = QRadioButton("Mensual")
        self.rb_acumulado = QRadioButton("Acumulada mensual")
        self.rb_mensual.setChecked(True)
        grupo = QButtonGroup(self)
        grupo.addButton(self.rb_mensual)
        grupo.addButton(self.rb_acumulado)
        self.rb_mensual.toggled.connect(self._on_vista_cambia)
        vista.addWidget(self.rb_mensual)
        vista.addWidget(self.rb_acumulado)
        vista.addStretch()
        layout.addLayout(vista)

        # ---------- Tabla ----------
        self.tabla = QTableView()
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSortingEnabled(False)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.tabla.verticalHeader().setDefaultSectionSize(22)
        layout.addWidget(self.tabla, 1)

        # ---------- Estado y exportar ----------
        barra = QHBoxLayout()
        self.lbl_estado = QLabel("Sin datos. Pulsa 'Calcular' para generar el presupuesto.")
        self.lbl_estado.setStyleSheet("color: #555;")
        barra.addWidget(self.lbl_estado, 1)
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setMinimumWidth(150)
        self.btn_exportar.clicked.connect(self._on_exportar)
        barra.addWidget(self.btn_exportar)
        layout.addLayout(barra)

    # ---------- Callbacks ----------
    def _on_calcular(self):
        anio = self.spin_anio.value()
        metodo = self.combo_metodo.currentData()
        self.btn_calcular.setEnabled(False)
        self.lbl_estado.setText(f"Calculando {anio} — {ETIQUETA_METODO[metodo]}...")
        self.repaint()
        try:
            self._df_raw = generar(anio, metodo, grupos=None)
        except Exception as e:
            QMessageBox.critical(self, "Error al calcular", str(e))
            self.lbl_estado.setText(f"Error: {e}")
            self.btn_calcular.setEnabled(True)
            return

        self._refrescar_tabla()
        self.btn_exportar.setEnabled(not self._df_raw.empty)
        self.btn_calcular.setEnabled(True)
        total = self._df_raw["movimiento"].sum()
        self.lbl_estado.setText(
            f"Generado: {len(self._df_raw):,} filas · Suma raw: "
            f"${total:,.0f} ({total/1e6:,.0f} M)"
        )

    def _on_vista_cambia(self):
        if self._df_raw is not None and not self._df_raw.empty:
            self._refrescar_tabla()

    def _refrescar_tabla(self):
        if self._df_raw is None or self._df_raw.empty:
            return
        pivot = (
            pivot_mensual_por_grupo(self._df_raw)
            if self.rb_mensual.isChecked()
            else pivot_acumulado_por_grupo(self._df_raw)
        )
        num_cols = set(MESES_NOMBRES) | {"Total"}
        self.tabla.setModel(PandasModel(pivot, columnas_numericas=num_cols))
        self.tabla.resizeColumnsToContents()
        self.tabla.setColumnWidth(0, max(self.tabla.columnWidth(0), 260))

    def _on_exportar(self):
        if self._df_raw is None or self._df_raw.empty:
            return
        anio = self.spin_anio.value()
        metodo = self.combo_metodo.currentData()
        sugerido = str(ruta_salida_default(anio, metodo))
        ruta_str, _ = QFileDialog.getSaveFileName(
            self, "Exportar presupuesto", sugerido, "Excel (*.xlsx)"
        )
        if not ruta_str:
            return
        try:
            ruta = exportar(self._df_raw, Path(ruta_str))
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        QMessageBox.information(
            self, "Exportado",
            f"Presupuesto guardado en:\n{ruta}\n\n{len(self._df_raw):,} filas."
        )
        self.lbl_estado.setText(f"Exportado a: {ruta}")
