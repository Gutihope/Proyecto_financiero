"""Tab UI del Submodulo 1: Crear presupuesto mensualizado.

Layout:
  +---------------------------------------------------------+
  | Anio destino  Metodo  [Calcular]                        |
  | Vista: o Mensual  o Acumulada mensual                   |
  +--------------------+------------------------------------+
  | Grupo | $ Aprobado |  Pivot calculado (Ene..Dic, Total) |
  | (29   | (editable) |                                    |
  |  rows | tu digitas)|                                    |
  +--------------------+------------------------------------+
  | Status                                  [Exportar Excel]|
  +---------------------------------------------------------+

La columna "$ Aprobado" es donde el usuario digita el presupuesto aprobado
por el consejo (no es calculado). El pivot de la derecha viene del metodo
de ejecucion historica seleccionado.
"""
import json
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QRadioButton, QSpinBox, QSplitter,
    QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.core.config import PROJECT_ROOT
from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    ETIQUETA_METODO, MESES_NOMBRES,
    exportar, generar, listar_grupos,
    pivot_acumulado_por_grupo, pivot_mensual_por_grupo,
    ruta_salida_default,
)
from src.ui.modelos_qt import PandasModel


METODOS_UI = [
    "ejecucion_ultimo_anio",
    "promedio_2_anios",
    "promedio_3_anios",
    "promedio_4_anios",
    "promedio_5_anios",
]


def _ruta_aprobado(anio: int) -> Path:
    return PROJECT_ROOT / "data" / f"aprobado_{anio}.json"


class TabCrearPresupuesto(QWidget):
    def __init__(self):
        super().__init__()
        self._df_raw: pd.DataFrame | None = None
        self._construir_ui()
        self._poblar_grupos()
        self._cargar_aprobado(self.spin_anio.value())

    # ---------- UI ----------
    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Controles
        controles = QHBoxLayout()
        controles.addWidget(QLabel("Año destino:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2018, 2050)
        self.spin_anio.setValue(2026)
        self.spin_anio.setFixedWidth(80)
        self.spin_anio.valueChanged.connect(self._on_anio_cambia)
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

        # Vista mensual / acumulada
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

        # Splitter: aprobado (izq) + calculado (der)
        splitter = QSplitter(Qt.Horizontal)

        # Izquierda: tabla aprobado
        self.tabla_aprobado = QTableWidget()
        self.tabla_aprobado.setColumnCount(2)
        self.tabla_aprobado.setHorizontalHeaderLabels(["Grupo", "$ Aprobado"])
        self.tabla_aprobado.verticalHeader().setVisible(False)
        self.tabla_aprobado.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tabla_aprobado.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tabla_aprobado.setColumnWidth(1, 150)
        self.tabla_aprobado.setAlternatingRowColors(True)
        self.tabla_aprobado.setMinimumWidth(440)
        self.tabla_aprobado.itemChanged.connect(self._on_aprobado_cambia)
        splitter.addWidget(self.tabla_aprobado)

        # Derecha: pivot calculado
        self.tabla_calculado = QTableView()
        self.tabla_calculado.setAlternatingRowColors(True)
        self.tabla_calculado.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        splitter.addWidget(self.tabla_calculado)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([440, 1000])
        layout.addWidget(splitter, 1)

        # Estado + exportar
        barra = QHBoxLayout()
        self.lbl_estado = QLabel("Sin datos. Pulsa 'Calcular' para generar el presupuesto.")
        self.lbl_estado.setStyleSheet("color: #555;")
        barra.addWidget(self.lbl_estado, 1)
        self.btn_guardar_aprobado = QPushButton("Guardar aprobado")
        self.btn_guardar_aprobado.setMinimumWidth(140)
        self.btn_guardar_aprobado.clicked.connect(self._on_guardar_aprobado)
        barra.addWidget(self.btn_guardar_aprobado)
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setMinimumWidth(150)
        self.btn_exportar.clicked.connect(self._on_exportar)
        barra.addWidget(self.btn_exportar)
        layout.addLayout(barra)

    # ---------- Data ----------
    def _poblar_grupos(self):
        try:
            grupos = listar_grupos()
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar grupos", str(e))
            return

        self.tabla_aprobado.blockSignals(True)
        self.tabla_aprobado.setRowCount(len(grupos))
        for i, g in enumerate(grupos):
            item = QTableWidgetItem(g)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setForeground(QBrush(QColor("#333")))
            self.tabla_aprobado.setItem(i, 0, item)

            item_val = QTableWidgetItem("")
            item_val.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
            self.tabla_aprobado.setItem(i, 1, item_val)
        self.tabla_aprobado.blockSignals(False)

    def _cargar_aprobado(self, anio: int):
        ruta = _ruta_aprobado(anio)
        if not ruta.exists():
            return
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return
        self.tabla_aprobado.blockSignals(True)
        for i in range(self.tabla_aprobado.rowCount()):
            grupo = self.tabla_aprobado.item(i, 0).text()
            valor = datos.get(grupo)
            if valor is None:
                self.tabla_aprobado.item(i, 1).setText("")
                continue
            self.tabla_aprobado.item(i, 1).setText(f"{float(valor):,.0f}")
        self.tabla_aprobado.blockSignals(False)

    def _on_anio_cambia(self, nuevo_anio: int):
        self._cargar_aprobado(nuevo_anio)

    def _on_aprobado_cambia(self, item: QTableWidgetItem):
        if item.column() != 1:
            return
        txt = item.text().strip().replace(",", "").replace(" ", "").replace("$", "")
        if not txt:
            return
        try:
            valor = float(txt)
        except ValueError:
            QMessageBox.warning(self, "Valor invalido", f"'{item.text()}' no es un numero.")
            self.tabla_aprobado.blockSignals(True)
            item.setText("")
            self.tabla_aprobado.blockSignals(False)
            return
        self.tabla_aprobado.blockSignals(True)
        item.setText(f"{valor:,.0f}")
        self.tabla_aprobado.blockSignals(False)

    def _leer_aprobado(self) -> dict[str, float]:
        valores: dict[str, float] = {}
        for i in range(self.tabla_aprobado.rowCount()):
            grupo = self.tabla_aprobado.item(i, 0).text()
            txt = self.tabla_aprobado.item(i, 1).text().strip().replace(",", "")
            if not txt:
                continue
            try:
                valores[grupo] = float(txt)
            except ValueError:
                pass
        return valores

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

        self._refrescar_pivot()
        self.btn_exportar.setEnabled(not self._df_raw.empty)
        self.btn_calcular.setEnabled(True)
        total = self._df_raw["movimiento"].sum()
        self.lbl_estado.setText(
            f"Generado: {len(self._df_raw):,} filas · Suma raw: "
            f"${total:,.0f}  ({total/1e6:,.0f} M)"
        )

    def _on_vista_cambia(self):
        if self._df_raw is not None and not self._df_raw.empty:
            self._refrescar_pivot()

    def _refrescar_pivot(self):
        if self._df_raw is None or self._df_raw.empty:
            return
        pivot = (
            pivot_mensual_por_grupo(self._df_raw)
            if self.rb_mensual.isChecked()
            else pivot_acumulado_por_grupo(self._df_raw)
        )
        num_cols = set(MESES_NOMBRES) | {"Total"}
        self.tabla_calculado.setModel(PandasModel(pivot, columnas_numericas=num_cols))
        self.tabla_calculado.resizeColumnsToContents()
        self.tabla_calculado.setColumnWidth(0, max(self.tabla_calculado.columnWidth(0), 240))

    def _on_guardar_aprobado(self):
        anio = self.spin_anio.value()
        ruta = _ruta_aprobado(anio)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(self._leer_aprobado(), indent=2, ensure_ascii=False), encoding="utf-8")
        self.lbl_estado.setText(f"Aprobado {anio} guardado en {ruta.name}")
        QMessageBox.information(self, "Guardado", f"Valores aprobados de {anio} guardados.")

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
