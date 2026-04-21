"""
data_table.py - CAN Data Table Widget
CAN frame data-ny tablisa görnüşinde görkezýär.
ID boýunça filter, sort, duplicate detection goldawy bar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableView,
    QLabel, QLineEdit, QPushButton, QComboBox, QHeaderView, QCheckBox,
    QAbstractItemView, QFrame, QGridLayout, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import Qt, pyqtSignal, QAbstractTableModel, QModelIndex, QSortFilterProxyModel
from PyQt5.QtGui import QColor, QFont, QIcon
from core.i18n import I18N


class CANTableModel(QAbstractTableModel):
    """
    Professional Model for CAN frames.
    Data-ga birikdirilen (binding) arhitektura ulanýar.
    """
    def __init__(self, frames=None):
        super().__init__()
        self._frames = frames or []
        self._headers = ["#", I18N.t("col_timestamp"), I18N.t("col_id"), I18N.t("col_dlc"), I18N.t("col_data")]
        self._mono_font = QFont("Cascadia Code", 10)

    def rowCount(self, parent=QModelIndex()):
        return len(self._frames)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._frames)):
            return None

        row_data = self._frames[index.row()] # (ts, id, data)
        col = index.column()

        if role == Qt.DisplayRole:
            if col == 0: return str(index.row() + 1)
            if col == 1: return f"{row_data[0]:.6f}"
            if col == 2: return f"0x{row_data[1]:03X}"
            if col == 3: return str(len(row_data[2]))
            if col == 4: return " ".join(f"{b:02X}" for b in row_data[2])

        if role == Qt.FontRole:
            if col in [1, 2, 4]: return self._mono_font

        if role == Qt.TextAlignmentRole:
            if col in [0, 2, 3]: return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.BackgroundRole and col == 2:
            # ID-e häsiýetli reňk ber
            can_id = row_data[1]
            hue = (can_id * 47) % 360
            return QColor.fromHsv(hue, 40, 240) # Soft colored background

        if role == Qt.UserRole:
            # Arka tarapdaky hakyky maglumatlary gaýtarmak üçin
            return row_data

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def update_data(self, frames):
        self.beginResetModel()
        self._frames = frames
        self.endResetModel()


class CANDataTable(QWidget):
    """CAN frame data tablisasy (Professional Model/View)."""

    # Signals
    frame_selected = pyqtSignal(int, bytes)  # can_id, data
    id_filter_changed = pyqtSignal(int)  # filtered CAN ID (-1 = all)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.frames = []  # Single source of truth
        self.unique_ids = set()
        
        # Setup Models
        self.model = CANTableModel(self.frames)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterKeyColumn(2) # Filter by ID column
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        self.title = QLabel(I18N.t("dt_title"))
        self.title.setProperty("subheading", True)
        layout.addWidget(self.title)

        # Filter bar
        filter_layout = QHBoxLayout()
        self.filter_lbl = QLabel(I18N.t("dt_filter_id"))
        filter_layout.addWidget(self.filter_lbl)
        self.id_filter = QComboBox()
        self.id_filter.addItem(I18N.t("dt_all_ids"), -1)
        self.id_filter.currentIndexChanged.connect(self._on_filter_changed)
        self.id_filter.setMinimumWidth(150)
        filter_layout.addWidget(self.id_filter)

        self.chk_unique = QCheckBox(I18N.t("dt_unique"))
        self.chk_unique.toggled.connect(self._apply_filter)
        filter_layout.addWidget(self.chk_unique)

        filter_layout.addStretch()

        self.count_label = QLabel(I18N.t("dt_frames_count").format(count=0))
        self.count_label.setProperty("caption", True)
        filter_layout.addWidget(self.count_label)
        layout.addLayout(filter_layout)

        # Table View
        self.table = QTableView()
        self.table.setModel(self.proxy_model)
        
        # Table settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)

        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 50)

        # Selection signal
        self.table.selectionModel().selectionChanged.connect(self._on_selection_changed)

        layout.addWidget(self.table)

    def load_frames(self, frames: list):
        """Frame listini ýükleýär."""
        self.frames = frames
        self.unique_ids = set(f[1] for f in frames)
        self.model.update_data(self.frames)

        # ID filter-i täzele
        self.id_filter.blockSignals(True)
        self.id_filter.clear()
        self.id_filter.addItem("All IDs", -1)
        for cid in sorted(self.unique_ids):
            count = sum(1 for f in frames if f[1] == cid)
            self.id_filter.addItem(f"0x{cid:03X} ({count})", cid)
        self.id_filter.blockSignals(False)
        
        self.count_label.setText(I18N.t("dt_frames_count").format(count=len(self.frames)))

    def update_data(self, frames: list):
        """Real-time update üçin."""
        self.frames = frames
        self.model.layoutChanged.emit() # Notify view of change
        self.count_label.setText(I18N.t("dt_frames_count").format(count=len(self.frames)))

    def update_from_database(self, database):
        """DBC-den ID-leri filtere goşýar."""
        if not database: return
        dbc_ids = set(m.message_id for m in database.messages)
        all_ids = self.unique_ids.union(dbc_ids)

        self.id_filter.blockSignals(True)
        current_id = self.id_filter.currentData()
        self.id_filter.clear()
        self.id_filter.addItem(I18N.t("dt_all_ids"), -1)
        for cid in sorted(all_ids):
            count = sum(1 for f in self.frames if f[1] == cid)
            name = f" - {database.get_message(cid).name}" if database.get_message(cid) else ""
            self.id_filter.addItem(f"0x{cid:03X}{name} ({count})", cid)
        
        idx = self.id_filter.findData(current_id)
        if idx >= 0: self.id_filter.setCurrentIndex(idx)
        self.id_filter.blockSignals(False)

    def _on_filter_changed(self, index):
        can_id = self.id_filter.currentData()
        if can_id == -1:
            self.proxy_model.setFilterFixedString("")
        else:
            self.proxy_model.setFilterFixedString(f"0x{can_id:03X}")
        
        self.count_label.setText(I18N.t("dt_frames_filtered").format(count=self.proxy_model.rowCount()))
        self.id_filter_changed.emit(can_id or -1)

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.title.setText(I18N.t("dt_title"))
        self.filter_lbl.setText(I18N.t("dt_filter_id"))
        self.chk_unique.setText(I18N.t("dt_unique"))
        
        # Update combo box "All IDs" item
        self.id_filter.blockSignals(True)
        self.id_filter.setItemText(0, I18N.t("dt_all_ids"))
        self.id_filter.blockSignals(False)
        
        # Update model headers
        self.model._headers = ["#", I18N.t("col_timestamp"), I18N.t("col_id"), I18N.t("col_dlc"), I18N.t("col_data")]
        self.model.headerDataChanged.emit(Qt.Horizontal, 0, 4)
        
        # Update count label
        if self.id_filter.currentData() == -1:
            self.count_label.setText(I18N.t("dt_frames_count").format(count=len(self.frames)))
        else:
            self.count_label.setText(I18N.t("dt_frames_filtered").format(count=self.proxy_model.rowCount()))

    def _apply_filter(self):
        # TBD: Multiplexer or complex filters
        pass

    def _on_selection_changed(self, selected, deselected):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes: return
        
        # Get data from source model via proxy index
        index = self.proxy_model.mapToSource(indexes[0])
        row_data = self.model.data(index, Qt.UserRole)
        if row_data:
            self.frame_selected.emit(row_data[1], row_data[2])

    def get_selected_frame(self):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes: return None
        index = self.proxy_model.mapToSource(indexes[0])
        return self.model.data(index, Qt.UserRole)

    def scroll_to_timestamp(self, target_ts: float):
        """Timestamp-e görä iň golaý setiri tapýar (Optimized)."""
        if not self.frames: return
        
        import bisect
        all_ts = [f[0] for f in self.frames]
        idx = bisect.bisect_left(all_ts, target_ts)
        
        # Clamp index
        idx = max(0, min(idx, len(self.frames)-1))
        
        # Select row in source model
        source_index = self.model.index(idx, 0)
        # Map to proxy
        proxy_index = self.proxy_model.mapFromSource(source_index)
        
        if proxy_index.isValid():
            self.table.selectRow(proxy_index.row())
            self.table.scrollTo(proxy_index, QAbstractItemView.PositionAtCenter)


class SignalEditorPanel(QWidget):
    """Signal property editor - signal parametrlerini redaktirlemek üçin (Professional)."""

    signal_updated = pyqtSignal(dict)  # signal properties dict

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Group 1: General Info ──
        gen_group = QWidget()
        gen_layout = QVBoxLayout(gen_group)
        gen_layout.setContentsMargins(0, 0, 0, 0)
        
        self.name_lbl = QLabel(I18N.t("sig_name"))
        gen_layout.addWidget(self.name_lbl)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(I18N.t("sig_search_placeholder"))
        gen_layout.addWidget(self.name_edit)
        main_layout.addWidget(gen_group)

        # ── Group 2: Layout & Encoding (Grid) ──
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)

        # Start bit
        self.start_bit_lbl = QLabel(I18N.t("sig_start"))
        grid_layout.addWidget(self.start_bit_lbl, 0, 0)
        self.start_bit_edit = QLineEdit("0")
        grid_layout.addWidget(self.start_bit_edit, 0, 1)

        # Length
        self.length_lbl = QLabel(I18N.t("sig_length"))
        grid_layout.addWidget(self.length_lbl, 0, 2)
        self.length_edit = QLineEdit("8")
        grid_layout.addWidget(self.length_edit, 0, 3)

        # Byte Order
        self.byte_order_lbl = QLabel(I18N.t("sig_byte_order"))
        grid_layout.addWidget(self.byte_order_lbl, 1, 0)
        self.byte_order_combo = QComboBox()
        self.byte_order_combo.addItems([I18N.t("sig_byte_order_intel"), I18N.t("sig_byte_order_moto")])
        grid_layout.addWidget(self.byte_order_combo, 1, 1, 1, 3)

        # Value Type
        self.value_type_lbl = QLabel(I18N.t("sig_type"))
        grid_layout.addWidget(self.value_type_lbl, 2, 0)
        self.value_type_combo = QComboBox()
        self.value_type_combo.addItems([I18N.t("sig_type_unsigned"), I18N.t("sig_type_signed")])
        grid_layout.addWidget(self.value_type_combo, 2, 1)

        # Multiplex
        self.mux_lbl = QLabel(I18N.t("sig_mux"))
        grid_layout.addWidget(self.mux_lbl, 2, 2)
        self.mux_combo = QComboBox()
        self.mux_combo.addItem(I18N.t("sig_mux_none"), "")
        self.mux_combo.addItem("M (Muxer)", "M")
        for i in range(16):
            self.mux_combo.addItem(f"m{i}", f"m{i}")
        grid_layout.addWidget(self.mux_combo, 2, 3)

        main_layout.addLayout(grid_layout)

        # ── Group 3: Scaling & Range ──
        scaling_group = QFrame()
        scaling_group.setProperty("class", "Card")
        scaling_layout = QGridLayout(scaling_group)
        scaling_layout.setContentsMargins(12, 12, 12, 12)

        self.scale_lbl = QLabel(I18N.t("sig_scale"))
        scaling_layout.addWidget(self.scale_lbl, 0, 0)
        self.scale_edit = QLineEdit("1.0")
        scaling_layout.addWidget(self.scale_edit, 0, 1)

        self.offset_lbl = QLabel(I18N.t("sig_offset"))
        scaling_layout.addWidget(self.offset_lbl, 0, 2)
        self.offset_edit = QLineEdit("0.0")
        scaling_layout.addWidget(self.offset_edit, 0, 3)

        self.min_lbl = QLabel(I18N.t("sig_min"))
        scaling_layout.addWidget(self.min_lbl, 1, 0)
        self.min_edit = QLineEdit("0")
        scaling_layout.addWidget(self.min_edit, 1, 1)

        self.max_lbl = QLabel(I18N.t("sig_max"))
        scaling_layout.addWidget(self.max_lbl, 1, 2)
        self.max_edit = QLineEdit("0")
        scaling_layout.addWidget(self.max_edit, 1, 3)

        self.unit_lbl = QLabel(I18N.t("sig_unit"))
        scaling_layout.addWidget(self.unit_lbl, 2, 0)
        self.unit_edit = QLineEdit()
        self.unit_edit.setPlaceholderText(I18N.t("sig_placeholder_unit"))
        scaling_layout.addWidget(self.unit_edit, 2, 1, 1, 3)

        main_layout.addWidget(scaling_group)

        # ── Group 4: Value Table (Enum) ──
        vt_header = QHBoxLayout()
        self.vt_lbl = QLabel(I18N.t("sig_val_desc"))
        vt_header.addWidget(self.vt_lbl)
        vt_header.addStretch()
        
        btn_vt_add = QPushButton("+")
        btn_vt_add.setFixedSize(24, 24)
        btn_vt_add.clicked.connect(self._add_vt_entry)
        vt_header.addWidget(btn_vt_add)
        
        btn_vt_remove = QPushButton("−")
        btn_vt_remove.setFixedSize(24, 24)
        btn_vt_remove.clicked.connect(self._remove_vt_entry)
        vt_header.addWidget(btn_vt_remove)
        
        main_layout.addLayout(vt_header)

        self.vt_table = QTableWidget()
        self.vt_table.setColumnCount(2)
        self.vt_table.setHorizontalHeaderLabels([I18N.t("col_data"), I18N.t("col_msg")])
        self.vt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.vt_table.setColumnWidth(0, 40)
        self.vt_table.setMaximumHeight(80)
        self.vt_table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.vt_table)

        # Preview Labels
        preview_box = QFrame()
        preview_box.setProperty("class", "PreviewBox")
        preview_layout = QVBoxLayout(preview_box)
        
        self.formula_label = QLabel(I18N.t("sig_formula").format(scale="1.0", offset="0.0"))
        self.formula_label.setStyleSheet("font-style: italic; border: none;")
        preview_layout.addWidget(self.formula_label)

        self.live_value_label = QLabel(I18N.t("sig_live_value").format(raw="-", phys="-", unit=""))
        self.live_value_label.setStyleSheet("font-weight: bold; border: none; font-size: 14px;")
        preview_layout.addWidget(self.live_value_label)
        
        main_layout.addWidget(preview_box)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton(I18N.t("sig_add"))
        self.btn_add.setProperty("primary", True)
        self.btn_add.clicked.connect(self._on_add_clicked)
        btn_layout.addWidget(self.btn_add)

        self.btn_clear = QPushButton(I18N.t("sig_clear"))
        self.btn_clear.clicked.connect(self._clear_fields)
        btn_layout.addWidget(self.btn_clear)
        main_layout.addLayout(btn_layout)

        main_layout.addStretch()

        # Connect formula updates
        self.scale_edit.textChanged.connect(self._update_formula)
        self.offset_edit.textChanged.connect(self._update_formula)

    # ── Value Table helpers ──

    def _add_vt_entry(self):
        """Value table-a täze entry goşýar."""
        row = self.vt_table.rowCount()
        self.vt_table.insertRow(row)
        self.vt_table.setItem(row, 0, QTableWidgetItem(str(row)))
        self.vt_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_vt_entry(self):
        """Saýlanan value table entry-ni aýyrýar."""
        row = self.vt_table.currentRow()
        if row >= 0:
            self.vt_table.removeRow(row)

    def _get_value_table(self) -> dict:
        """Value table-dan dict {int: str} gaýtarýar."""
        vt = {}
        for row in range(self.vt_table.rowCount()):
            val_item = self.vt_table.item(row, 0)
            desc_item = self.vt_table.item(row, 1)
            if val_item and desc_item:
                try:
                    vt[int(val_item.text())] = desc_item.text()
                except ValueError:
                    continue
        return vt

    def _set_value_table(self, vt: dict):
        """Value table-ny widget-e ýükleýär."""
        self.vt_table.setRowCount(0)
        for val, desc in sorted(vt.items()):
            row = self.vt_table.rowCount()
            self.vt_table.insertRow(row)
            self.vt_table.setItem(row, 0, QTableWidgetItem(str(val)))
            self.vt_table.setItem(row, 1, QTableWidgetItem(desc))

    # ── Original methods (updated) ──

    def set_from_selection(self, start_bit: int, length: int):
        """Bit editor-dan saýlanan diapazon bilen dolduryar."""
        self.start_bit_edit.setText(str(start_bit))
        self.length_edit.setText(str(length))

    def set_from_signal(self, signal):
        """Bar bolan signal obýektinden doldurýar."""
        self.name_edit.setText(signal.name)
        self.start_bit_edit.setText(str(signal.start_bit))
        self.length_edit.setText(str(signal.length))
        self.byte_order_combo.setCurrentIndex(
            0 if signal.byte_order == "little_endian" else 1
        )
        self.value_type_combo.setCurrentIndex(
            0 if signal.value_type == "unsigned" else 1
        )
        self.scale_edit.setText(str(signal.scale))
        self.offset_edit.setText(str(signal.offset))
        self.min_edit.setText(str(signal.minimum))
        self.max_edit.setText(str(signal.maximum))
        self.unit_edit.setText(signal.unit)

        # Multiplex indicator
        mux = getattr(signal, 'multiplex_indicator', '')
        idx = self.mux_combo.findData(mux)
        self.mux_combo.setCurrentIndex(idx if idx >= 0 else 0)

        # Value table
        vt = getattr(signal, 'value_table', {})
        self._set_value_table(vt if vt else {})

        self._update_formula()

    def update_live_value(self, raw_value: int):
        """Live formula netijäni görkezýär."""
        try:
            scale = float(self.scale_edit.text() or "1")
            offset = float(self.offset_edit.text() or "0")
            physical = raw_value * scale + offset
            unit = self.unit_edit.text()

            # Show enum label if value table has this value
            vt = self._get_value_table()
            enum_label = ""
            if vt and raw_value in vt:
                enum_label = f" ({vt[raw_value]})"

            self.live_value_label.setText(
                I18N.t("sig_live_value").format(raw=raw_value, phys=physical, unit=unit) + enum_label
            )
        except ValueError:
            self.live_value_label.setText(f"Raw: {raw_value}")

    def _update_formula(self):
        """Formula label-i täzelaýär."""
        try:
            scale = self.scale_edit.text() or "1"
            offset = self.offset_edit.text() or "0"
            self.formula_label.setText(
                I18N.t("sig_formula").format(scale=scale, offset=offset)
            )
        except Exception:
            pass

    def _clear_fields(self):
        """Ähli meýdançalary arassalaýar."""
        self.name_edit.clear()
        self.start_bit_edit.setText("0")
        self.length_edit.setText("8")
        self.byte_order_combo.setCurrentIndex(0)
        self.value_type_combo.setCurrentIndex(0)
        self.mux_combo.setCurrentIndex(0)
        self.scale_edit.setText("1.0")
        self.offset_edit.setText("0.0")
        self.min_edit.setText("0")
        self.max_edit.setText("0")
        self.unit_edit.clear()
        self.vt_table.setRowCount(0)
        self.live_value_label.setText("Current: -")

    def _on_add_clicked(self):
        """Add Signal basylanda."""
        props = self.get_signal_properties()
        if props and props["name"]:
            self.signal_updated.emit(props)

    def get_signal_properties(self) -> dict:
        """Häzirki signal parametrlerini dict görnüşinde gaýtarýar."""
        try:
            return {
                "name": self.name_edit.text().strip(),
                "start_bit": int(self.start_bit_edit.text() or "0"),
                "length": int(self.length_edit.text() or "8"),
                "byte_order": "little_endian" if self.byte_order_combo.currentIndex() == 0 else "big_endian",
                "value_type": "unsigned" if self.value_type_combo.currentIndex() == 0 else "signed",
                "scale": float(self.scale_edit.text() or "1"),
                "offset": float(self.offset_edit.text() or "0"),
                "minimum": float(self.min_edit.text() or "0"),
                "maximum": float(self.max_edit.text() or "0"),
                "unit": self.unit_edit.text().strip(),
                "multiplex_indicator": self.mux_combo.currentData() or "",
                "value_table": self._get_value_table(),
            }
        except ValueError:
            return None

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.name_lbl.setText(I18N.t("sig_name"))
        self.name_edit.setPlaceholderText(I18N.t("sig_search_placeholder"))
        self.start_bit_lbl.setText(I18N.t("sig_start"))
        self.length_lbl.setText(I18N.t("sig_length"))
        self.byte_order_lbl.setText(I18N.t("sig_byte_order"))
        
        self.byte_order_combo.blockSignals(True)
        self.byte_order_combo.setItemText(0, I18N.t("sig_byte_order_intel"))
        self.byte_order_combo.setItemText(1, I18N.t("sig_byte_order_moto"))
        self.byte_order_combo.blockSignals(False)
        
        self.value_type_lbl.setText(I18N.t("sig_type"))
        self.value_type_combo.blockSignals(True)
        self.value_type_combo.setItemText(0, I18N.t("sig_type_unsigned"))
        self.value_type_combo.setItemText(1, I18N.t("sig_type_signed"))
        self.value_type_combo.blockSignals(False)
        
        self.mux_lbl.setText(I18N.t("sig_mux"))
        self.mux_combo.blockSignals(True)
        self.mux_combo.setItemText(0, I18N.t("sig_mux_none"))
        self.mux_combo.blockSignals(False)
        
        self.scale_lbl.setText(I18N.t("sig_scale"))
        self.offset_lbl.setText(I18N.t("sig_offset"))
        self.min_lbl.setText(I18N.t("sig_min"))
        self.max_lbl.setText(I18N.t("sig_max"))
        self.unit_lbl.setText(I18N.t("sig_unit"))
        self.unit_edit.setPlaceholderText(I18N.t("sig_placeholder_unit"))
        
        self.vt_lbl.setText(I18N.t("sig_val_desc"))
        self.vt_table.setHorizontalHeaderLabels([I18N.t("col_data"), I18N.t("col_msg")])
        
        self._update_formula()
        self.btn_add.setText(I18N.t("sig_add"))
        self.btn_clear.setText(I18N.t("sig_clear"))



class DBCPreviewPanel(QWidget):
    """DBC output preview panel - döredilýän DBC-niň görnüşini görkezýär."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        self.title = QLabel(I18N.t("dbc_preview_title"))
        self.title.setProperty("subheading", True)
        header.addWidget(self.title)
        header.addStretch()

        self.btn_copy = QPushButton(I18N.t("dbc_copy"))
        self.btn_copy.setFixedWidth(70)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        header.addWidget(self.btn_copy)

        layout.addLayout(header)

        # Text preview
        from PyQt5.QtWidgets import QTextEdit
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Cascadia Code", 11))
        self.text_edit.setPlaceholderText(I18N.t("dbc_preview_placeholder"))
        layout.addWidget(self.text_edit)

    def set_text(self, text: str):
        """DBC text-ini set edýär."""
        self.text_edit.setPlainText(text)

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.title.setText(I18N.t("dbc_preview_title"))
        self.btn_copy.setText(I18N.t("dbc_copy"))
        self.text_edit.setPlaceholderText(I18N.t("dbc_preview_placeholder"))

    def _copy_to_clipboard(self):
        """Text-i clipboard-a kopyalaýar."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())

class DatabaseExplorerPanel(QWidget):
    """
    DBC Database Explorer - Ähli struktura professional Tree View görnüşinde (Professional).
    Nodes, Messages, Signals, Attributes we EnvVars görkezýär.
    """
    
    # Signals
    item_selected = pyqtSignal(object)  # Selected model object (Node, Message, or Signal)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with search
        header_layout = QHBoxLayout()
        self.title = QLabel(I18N.t("db_explorer_title"))
        self.title.setProperty("subheading", True)
        header_layout.addWidget(self.title)
        
        header_layout.addStretch()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(I18N.t("db_explorer_search"))
        self.search_edit.setClearButtonEnabled(True)
        self.search_edit.setFixedWidth(250)
        self.search_edit.textChanged.connect(self._on_search_changed)
        header_layout.addWidget(self.search_edit)
        
        layout.addLayout(header_layout)

        # Tree Widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([I18N.t("nav_explorer"), I18N.t("info")])
        self.tree.setColumnWidth(0, 300)
        self.tree.setAlternatingRowColors(True)
        self.tree.setAnimated(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        
        layout.addWidget(self.tree)

    def clear(self):
        """Agaçdaky ähli elementleri arassalaýar."""
        self.tree.clear()

    def populate(self, database):
        """DBC Database maglumatlary bilen doldurýar."""
        self.clear()
        if not database:
            return

        mono_font = QFont("Cascadia Code", 10)

        # 1. Nodes
        nodes_root = QTreeWidgetItem(self.tree, [I18N.t("db_explorer_nodes"), f"({len(database.nodes)})"])
        nodes_root.setFont(0, QFont("", 10, QFont.Bold))
        for node in database.nodes:
            item = QTreeWidgetItem(nodes_root, [node.name, node.comment or ""])
            item.setData(0, Qt.UserRole, node)
            item.setIcon(0, QIcon()) # TBD: Add icons if needed

        # 2. Messages & Signals
        msgs_root = QTreeWidgetItem(self.tree, [I18N.t("db_explorer_msgs"), f"({len(database.messages)})"])
        msgs_root.setFont(0, QFont("", 10, QFont.Bold))
        for msg in database.messages:
            msg_id_str = f"0x{msg.message_id:03X}"
            msg_item = QTreeWidgetItem(msgs_root, [f"{msg.name} ({msg_id_str})", f"DLC: {msg.dlc}, Sender: {msg.sender}"])
            msg_item.setFont(0, mono_font)
            msg_item.setData(0, Qt.UserRole, msg)
            
            for sig in msg.signals:
                mux_str = f" [{sig.multiplex_indicator}]" if sig.multiplex_indicator else ""
                sig_details = f"{sig.start_bit}|{sig.length} ({sig.scale}, {sig.offset}) {sig.unit}"
                sig_item = QTreeWidgetItem(msg_item, [f"SG_ {sig.name}{mux_str}", sig_details])
                sig_item.setData(0, Qt.UserRole, sig)

        # 3. Attributes
        if database.attribute_definitions:
            attr_root = QTreeWidgetItem(self.tree, [I18N.t("db_explorer_attrs"), f"({len(database.attribute_definitions)})"])
            attr_root.setFont(0, QFont("", 10, QFont.Bold))
            for adef in database.attribute_definitions:
                item = QTreeWidgetItem(attr_root, [adef.name, f"{adef.object_type} {adef.value_type}"])
                item.setData(0, Qt.UserRole, adef)

        # 4. Environment Variables
        if database.environment_variables:
            env_root = QTreeWidgetItem(self.tree, [I18N.t("db_explorer_envs"), f"({len(database.environment_variables)})"])
            env_root.setFont(0, QFont("", 10, QFont.Bold))
            for ev in database.environment_variables:
                item = QTreeWidgetItem(env_root, [ev.name, f"{ev.var_type} [{ev.min}|{ev.max}] {ev.unit}"])
                item.setData(0, Qt.UserRole, ev)

        # Expand top-level items
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setExpanded(True)

    def _on_item_clicked(self, item, column):
        """Element basylanda model obýektini emit edýär."""
        obj = item.data(0, Qt.UserRole)
        if obj:
            self.item_selected.emit(obj)

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.title.setText(I18N.t("db_explorer_title"))
        self.search_edit.setPlaceholderText(I18N.t("db_explorer_search"))
        self.tree.setHeaderLabels([I18N.t("nav_explorer"), I18N.t("info")])

    def _on_search_changed(self, text):
        """Agaçda gözleg amala aşyrýar."""
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            root = self.tree.topLevelItem(i)
            self._filter_item(root, text)

    def _filter_item(self, item, text):
        """Recursive filter for tree items."""
        match = text in item.text(0).lower() or text in item.text(1).lower()
        child_match = False
        
        for i in range(item.childCount()):
            if self._filter_item(item.child(i), text):
                child_match = True
        
        visible = match or child_match
        item.setHidden(not visible)
        if visible and text:
            item.setExpanded(True)
        return visible
