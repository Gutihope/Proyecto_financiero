"""Tab UI del Submodulo 1: Crear presupuesto mensualizado.

Layout:
  +---------------------------------------------------------+
  | Anio destino  Metodo  [Calcular]                        |
  | Vista: o Mensual  o Acumulada mensual                   |
  +-------------------------+-------------------------------+
  | Grupo/Detalle | Aprob.M | Calc.M |  Pivot Ene..Dic+Tot |
  | (1 fila por   |         |        |  (filas alineadas   |
  | clave; abre   |         |        |   con la tabla izq) |
  | 51. Personal  |         |        |                     |
  | y 52. Central |         |        |                     |
  | en subgrupos) |         |        |                     |
  +-------------------------+-------------------------------+
  | Status                  [Guardar aprobado] [Exportar]   |
  +---------------------------------------------------------+

El "Aprobado año" es el valor anual que aprueba el consejo. Para los grupos
51. Personal y 52. Centralizados se abre por subgrupo (Administrativo /
Profesores y Cafam / Unicafam). El sistema mensualiza ese aprobado con la
distribucion del metodo elegido, preservando el signo del calculado.

Persistencia: data/aprobado_<anio>.json (claves = display strings, valores = M).
"""
import json
from pathlib import Path

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QFileDialog, QHBoxLayout, QHeaderView,
    QLabel, QMessageBox, QPushButton, QRadioButton, QSpinBox, QSplitter,
    QTableView, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.core.config import PROJECT_ROOT
from src.modulos.m2_presupuesto.submodulos.crear_presupuesto_mensual import (
    ETIQUETA_METODO, GRUPOS_DESAGREGADOS, MESES_NOMBRES,
    _agregar_columna_clave,
    exportar, generar, listar_keys_aprobado,
    mensualizar_aprobado,
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

COL_GRUPO = 0
COL_APROBADO = 1
COL_CALCULADO = 2


def _ruta_aprobado(anio: int) -> Path:
    return PROJECT_ROOT / "data" / f"aprobado_{anio}.json"


class TabCrearPresupuesto(QWidget):
    def __init__(self):
        super().__init__()
        self._df_raw: pd.DataFrame | None = None
        self._keys: list[str] = []  # clave de aprobado por fila de la tabla izquierda
        self._construir_ui()
        self._poblar_grupos()
        self._cargar_aprobado(self.spin_anio.value())

    def _construir_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # Controles
        ctrl = QHBoxLayout()
        ctrl.addWidget(QLabel("Año destino:"))
        self.spin_anio = QSpinBox()
        self.spin_anio.setRange(2018, 2050)
        self.spin_anio.setValue(2026)
        self.spin_anio.setFixedWidth(80)
        self.spin_anio.valueChanged.connect(self._on_anio_cambia)
        ctrl.addWidget(self.spin_anio)

        ctrl.addSpacing(24)
        ctrl.addWidget(QLabel("Método distribución mensual:"))
        self.combo_metodo = QComboBox()
        for clave in METODOS_UI:
            self.combo_metodo.addItem(ETIQUETA_METODO[clave], clave)
        self.combo_metodo.setCurrentIndex(2)
        self.combo_metodo.setMinimumWidth(240)
        ctrl.addWidget(self.combo_metodo)

        ctrl.addSpacing(24)
        self.btn_calcular = QPushButton("Calcular")
        self.btn_calcular.setMinimumWidth(110)
        self.btn_calcular.clicked.connect(self._on_calcular)
        ctrl.addWidget(self.btn_calcular)

        ctrl.addStretch()
        layout.addLayout(ctrl)

        # Vista mensual / acumulada
        vista = QHBoxLayout()
        vista.addWidget(QLabel("Vista:"))
        self.rb_mensual = QRadioButton("Mensual")
        self.rb_acumulado = QRadioButton("Acumulada mensual")
        self.rb_mensual.setChecked(True)
        bg = QButtonGroup(self)
        bg.addButton(self.rb_mensual)
        bg.addButton(self.rb_acumulado)
        self.rb_mensual.toggled.connect(self._on_vista_cambia)
        vista.addWidget(self.rb_mensual)
        vista.addWidget(self.rb_acumulado)
        vista.addStretch()
        layout.addLayout(vista)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)

        # Izquierda: tabla aprobado
        self.tabla_aprobado = QTableWidget()
        self.tabla_aprobado.setColumnCount(3)
        self.tabla_aprobado.setHorizontalHeaderLabels(
            ["Grupo / Detalle", "Aprobado año (M)", "Calculado (M)"]
        )
        self.tabla_aprobado.verticalHeader().setVisible(False)
        h = self.tabla_aprobado.horizontalHeader()
        h.setSectionResizeMode(COL_GRUPO, QHeaderView.Stretch)
        h.setSectionResizeMode(COL_APROBADO, QHeaderView.Fixed)
        h.setSectionResizeMode(COL_CALCULADO, QHeaderView.Fixed)
        self.tabla_aprobado.setColumnWidth(COL_APROBADO, 130)
        self.tabla_aprobado.setColumnWidth(COL_CALCULADO, 130)
        self.tabla_aprobado.setAlternatingRowColors(True)
        self.tabla_aprobado.setMinimumWidth(580)
        self.tabla_aprobado.itemChanged.connect(self._on_aprobado_cambia)
        splitter.addWidget(self.tabla_aprobado)

        # Derecha: pivot
        self.tabla_pivot = QTableView()
        self.tabla_pivot.setAlternatingRowColors(True)
        self.tabla_pivot.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        splitter.addWidget(self.tabla_pivot)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([580, 1000])
        layout.addWidget(splitter, 1)

        # Estado + botones
        bottom = QHBoxLayout()
        self.lbl_estado = QLabel("Sin datos. Digita aprobados (en millones) y pulsa 'Calcular'.")
        self.lbl_estado.setStyleSheet("color: #555;")
        bottom.addWidget(self.lbl_estado, 1)
        self.btn_guardar_aprobado = QPushButton("Guardar aprobado")
        self.btn_guardar_aprobado.setMinimumWidth(140)
        self.btn_guardar_aprobado.clicked.connect(self._on_guardar_aprobado)
        bottom.addWidget(self.btn_guardar_aprobado)
        self.btn_exportar = QPushButton("Exportar Excel")
        self.btn_exportar.setEnabled(False)
        self.btn_exportar.setMinimumWidth(150)
        self.btn_exportar.clicked.connect(self._on_exportar)
        bottom.addWidget(self.btn_exportar)
        layout.addLayout(bottom)

    # ---------- Población ----------
    def _poblar_grupos(self):
        try:
            entradas = listar_keys_aprobado()
        except Exception as e:
            QMessageBox.critical(self, "Error al cargar grupos", str(e))
            return

        self._keys = [k[2] for k in entradas]

        self.tabla_aprobado.blockSignals(True)
        self.tabla_aprobado.setRowCount(len(entradas))
        for i, (grupo, subgrupo, key) in enumerate(entradas):
            item_g = QTableWidgetItem(key)
            item_g.setFlags(item_g.flags() & ~Qt.ItemIsEditable)
            if grupo in GRUPOS_DESAGREGADOS:
                font = item_g.font()
                font.setItalic(True)
                item_g.setFont(font)
            self.tabla_aprobado.setItem(i, COL_GRUPO, item_g)

            item_a = QTableWidgetItem("")
            item_a.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
            self.tabla_aprobado.setItem(i, COL_APROBADO, item_a)

            item_c = QTableWidgetItem("")
            item_c.setFlags(item_c.flags() & ~Qt.ItemIsEditable)
            item_c.setTextAlignment(int(Qt.AlignRight | Qt.AlignVCenter))
            item_c.setForeground(Qt.darkGray)
            self.tabla_aprobado.setItem(i, COL_CALCULADO, item_c)
        self.tabla_aprobado.blockSignals(False)

    # ---------- Persistencia ----------
    def _cargar_aprobado(self, anio: int):
        ruta = _ruta_aprobado(anio)
        self.tabla_aprobado.blockSignals(True)
        for i in range(self.tabla_aprobado.rowCount()):
            self.tabla_aprobado.item(i, COL_APROBADO).setText("")
        self.tabla_aprobado.blockSignals(False)

        if not ruta.exists():
            return
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
        except Exception:
            return
        self.tabla_aprobado.blockSignals(True)
        for i, key in enumerate(self._keys):
            valor = datos.get(key)
            if valor is None:
                continue
            self.tabla_aprobado.item(i, COL_APROBADO).setText(f"{float(valor):,.0f}")
        self.tabla_aprobado.blockSignals(False)

    def _leer_aprobado_millones(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for i, key in enumerate(self._keys):
            txt = self.tabla_aprobado.item(i, COL_APROBADO).text().strip().replace(",", "")
            if not txt:
                continue
            try:
                out[key] = float(txt)
            except ValueError:
                pass
        return out

    def _leer_aprobado_pesos(self) -> dict[str, float]:
        return {k: v * 1_000_000 for k, v in self._leer_aprobado_millones().items()}

    # ---------- Refresh ----------
    def _df_final(self) -> pd.DataFrame | None:
        if self._df_raw is None or self._df_raw.empty:
            return None
        return mensualizar_aprobado(self._df_raw, self._leer_aprobado_pesos())

    def _refrescar_pivot(self):
        df = self._df_final()
        if df is None:
            return
        pivot = (
            pivot_mensual_por_grupo(df, por_clave=True)
            if self.rb_mensual.isChecked()
            else pivot_acumulado_por_grupo(df, por_clave=True)
        )
        num_cols = set(MESES_NOMBRES) | {"Total"}
        self.tabla_pivot.setModel(PandasModel(pivot, columnas_numericas=num_cols))
        self.tabla_pivot.resizeColumnsToContents()
        self.tabla_pivot.setColumnWidth(0, max(self.tabla_pivot.columnWidth(0), 260))

    def _refrescar_calculado_column(self):
        self.tabla_aprobado.blockSignals(True)
        if self._df_raw is None or self._df_raw.empty:
            for i in range(self.tabla_aprobado.rowCount()):
                self.tabla_aprobado.item(i, COL_CALCULADO).setText("")
        else:
            df = _agregar_columna_clave(self._df_raw)
            totales = df.groupby("__clave")["movimiento"].sum()
            for i, key in enumerate(self._keys):
                total = float(totales.get(key, 0.0))
                self.tabla_aprobado.item(i, COL_CALCULADO).setText(
                    f"{abs(total) / 1e6:,.0f}"
                )
        self.tabla_aprobado.blockSignals(False)

    # ---------- Callbacks ----------
    def _on_anio_cambia(self, anio: int):
        self._cargar_aprobado(anio)
        if self._df_raw is not None:
            self._refrescar_pivot()

    def _on_aprobado_cambia(self, item: QTableWidgetItem):
        if item.column() != COL_APROBADO:
            return
        txt = item.text().strip().replace(",", "").replace(" ", "").replace("$", "")
        if not txt:
            if self._df_raw is not None:
                self._refrescar_pivot()
            return
        try:
            valor = float(txt)
        except ValueError:
            QMessageBox.warning(self, "Valor inválido",
                                f"'{item.text()}' no es un número.")
            self.tabla_aprobado.blockSignals(True)
            item.setText("")
            self.tabla_aprobado.blockSignals(False)
            return
        self.tabla_aprobado.blockSignals(True)
        item.setText(f"{valor:,.0f}")
        self.tabla_aprobado.blockSignals(False)
        if self._df_raw is not None:
            self._refrescar_pivot()

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

        self._refrescar_calculado_column()
        self._refrescar_pivot()
        self.btn_exportar.setEnabled(not self._df_raw.empty)
        self.btn_calcular.setEnabled(True)

        df_final = self._df_final()
        total = df_final["movimiento"].sum() if df_final is not None else 0
        n_aprobados = len(self._leer_aprobado_millones())
        self.lbl_estado.setText(
            f"Generado {len(self._df_raw):,} filas · "
            f"{n_aprobados} claves con aprobado digitado · "
            f"Total final: {total/1e6:,.0f} M"
        )

    def _on_vista_cambia(self):
        if self._df_raw is not None and not self._df_raw.empty:
            self._refrescar_pivot()

    def _on_guardar_aprobado(self):
        anio = self.spin_anio.value()
        ruta = _ruta_aprobado(anio)
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(
            json.dumps(self._leer_aprobado_millones(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        n = len(self._leer_aprobado_millones())
        self.lbl_estado.setText(f"Aprobado {anio} guardado ({n} claves) en {ruta.name}")
        QMessageBox.information(self, "Guardado",
                                f"Aprobado {anio} guardado ({n} claves).")

    def _on_exportar(self):
        df = self._df_final()
        if df is None or df.empty:
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
            ruta = exportar(df, Path(ruta_str))
        except Exception as e:
            QMessageBox.critical(self, "Error al exportar", str(e))
            return
        n_ap = len(self._leer_aprobado_millones())
        msg = f"Guardado: {ruta}\n\n{len(df):,} filas."
        if n_ap:
            msg += f"\n{n_ap} claves mensualizadas con aprobado digitado."
        QMessageBox.information(self, "Exportado", msg)
        self.lbl_estado.setText(f"Exportado: {ruta}")
