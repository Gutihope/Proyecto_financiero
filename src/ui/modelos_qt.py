"""Adaptadores Qt para mostrar DataFrames en QTableView."""
import pandas as pd
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class PandasModel(QAbstractTableModel):
    def __init__(
        self,
        df: pd.DataFrame,
        columnas_numericas: set[str] | None = None,
        columnas_porcentaje: set[str] | None = None,
        columnas_delta: set[str] | None = None,
    ):
        super().__init__()
        self._df = df
        self._num_cols = columnas_numericas or set()
        self._pct_cols = columnas_porcentaje or set()
        self._delta_cols = columnas_delta or set()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None

        col_name = self._df.columns[index.column()]
        val = self._df.iloc[index.row(), index.column()]

        if role == Qt.DisplayRole:
            if col_name in self._pct_cols:
                if pd.isna(val):
                    return ""
                try:
                    return f"{float(val):+,.1f}%"
                except (TypeError, ValueError):
                    return str(val)
            if col_name in self._delta_cols:
                if pd.isna(val):
                    return ""
                try:
                    return f"{float(val):+,.0f}"
                except (TypeError, ValueError):
                    return str(val)
            if col_name in self._num_cols:
                if pd.isna(val):
                    return ""
                try:
                    return f"{float(val):,.0f}"
                except (TypeError, ValueError):
                    return str(val)
            return "" if pd.isna(val) else str(val)

        if role == Qt.TextAlignmentRole:
            if (col_name in self._num_cols or col_name in self._pct_cols
                    or col_name in self._delta_cols):
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        if role == Qt.ForegroundRole and (col_name in self._pct_cols
                                          or col_name in self._delta_cols):
            try:
                v = float(val)
                if v > 0:
                    return Qt.darkGreen
                if v < 0:
                    return Qt.darkRed
            except (TypeError, ValueError):
                return None
            return None

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section + 1)
        return None
