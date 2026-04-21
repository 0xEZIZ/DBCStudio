"""
ui/re_scout_panel.py - Professional Reverse Engineering Scout
Interactive tool for global event-based signal discovery.
"""

from collections import defaultdict
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QListWidget, QListWidgetItem, QProgressBar,
    QFrame, QGroupBox, QSplitter, QScrollArea
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPainter, QBrush, QPen
from core.i18n import I18N

class BitHeatmapWidget(QWidget):
    """
    CAN message bit heatmap (8x8 grid).
    Visualizes activity levels.
    """
    def __init__(self):
        super().__init__()
        self.setFixedSize(220, 220)
        self.heatmap_data = [0] * 64
        self.highlight_bits = [] # List of (bit, color)

    def set_data(self, heatmap_data: list, highlight_bits: list = None):
        self.heatmap_data = heatmap_data[:64] if heatmap_data else [0] * 64
        self.highlight_bits = highlight_bits or []
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        padding = 10
        available_size = self.width() - 2 * padding
        cell_size = available_size // 8
        max_flips = max(self.heatmap_data) if any(self.heatmap_data) else 1

        for i in range(64):
            # Row-major ordering for bit layout
            # Byte 0 (bits 0-7), Byte 1 (bits 8-15)... 
            # In UI: Rows = Bytes, Cols = Bits
            byte_idx = i // 8
            bit_pos = i % 8
            
            x = padding + bit_pos * cell_size
            y = padding + byte_idx * cell_size
            
            # Base color based on flip count (Heatmap)
            # Use logarithmic-ish scale for color to show small changes
            if self.heatmap_data[i] > 0:
                intensity = min(200, 40 + int((self.heatmap_data[i] / max_flips) * 160))
                color = QColor(40 + (intensity // 2), 20, intensity) # Deep blue to bright purple/pink
            else:
                color = QColor(35, 35, 35) # Dark gray for static bits
            
            # Highlight specific bits if requested (Selection)
            for hb, h_color in self.highlight_bits:
                if i == hb:
                    color = h_color
                    break
            
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(120, 120, 120, 40)))
            painter.drawRect(x, y, cell_size, cell_size)
            
            # Draw tiny bit number if space allows
            if cell_size > 15:
                painter.setPen(QPen(QColor(200, 200, 200, 100)))
                painter.setFont(QFont("Segoe UI", 6))
                painter.drawText(x+2, y+cell_size-2, str(i))

class REScoutPanel(QWidget):
    """
    Professional Reverse Engineering Scout.
    Supports multi-ID global discovery and bit-level visualization.
    """
    analyze_requested = pyqtSignal(dict, dict) # baseline_dict, action_dict
    signal_added = pyqtSignal(int, int, int) # id, start, length

    def __init__(self):
        super().__init__()
        self.baseline_data = defaultdict(list) # can_id -> [bytes]
        self.action_data = defaultdict(list)
        self.recording_mode = "idle"
        self.active_id = None
        self._status_state = "idle"  # idle, baseline, action, analyzing, complete
        
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_box = QFrame()
        header_box.setObjectName("ScoutHeader")
        header_layout = QVBoxLayout(header_box)
        
        self.title_lbl = QLabel(I18N.t("scout_title"))
        self.title_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(self.title_lbl)
        
        self.info_lbl = QLabel(I18N.t("scout_info"))
        self.info_lbl.setWordWrap(True)
        self.info_lbl.setStyleSheet("color: #888; font-size: 11px;")
        header_layout.addWidget(self.info_lbl)
        layout.addWidget(header_box)

        # Controls
        self.ctrl_group = QGroupBox(I18N.t("nav_analyze"))
        ctrl_layout = QVBoxLayout(self.ctrl_group)
        
        self.status_lbl = QLabel(f"{I18N.t('scout_status')} {I18N.t('scout_idle')}")
        self.status_lbl.setStyleSheet("font-weight: bold; background: #222; padding: 10px; border-radius: 6px; border: 1px solid #444;")
        self.status_lbl.setAlignment(Qt.AlignCenter)
        ctrl_layout.addWidget(self.status_lbl)

        btn_layout = QHBoxLayout()
        self.btn_baseline = QPushButton(I18N.t("scout_btn_baseline"))
        self.btn_baseline.clicked.connect(self._toggle_baseline)
        self.btn_baseline.setFixedHeight(45)
        self.btn_baseline.setCursor(Qt.PointingHandCursor)
        
        self.btn_action = QPushButton(I18N.t("scout_btn_action"))
        self.btn_action.clicked.connect(self._toggle_action)
        self.btn_action.setEnabled(False)
        self.btn_action.setFixedHeight(45)
        self.btn_action.setCursor(Qt.PointingHandCursor)
        
        btn_layout.addWidget(self.btn_baseline)
        btn_layout.addWidget(self.btn_action)
        ctrl_layout.addLayout(btn_layout)

        self.btn_reset = QPushButton(I18N.t("scout_btn_reset"))
        self.btn_reset.clicked.connect(self.reset)
        ctrl_layout.addWidget(self.btn_reset)
        
        layout.addWidget(self.ctrl_group)

        # Main Splitter
        self.splitter = QSplitter(Qt.Vertical)
        
        # Results List
        res_container = QFrame()
        res_container.setObjectName("ResultBox")
        res_layout = QVBoxLayout(res_container)
        self.res_label = QLabel(I18N.t("scout_candidates"))
        res_layout.addWidget(self.res_label)
        
        self.res_list = QListWidget()
        self.res_list.itemClicked.connect(self._on_item_clicked)
        self.res_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.res_list.setStyleSheet("QListWidget { background: #1a1a1a; border-radius: 4px; }")
        res_layout.addWidget(self.res_list)
        self.splitter.addWidget(res_container)
        
        # Details & Heatmap
        detail_container = QFrame()
        detail_container.setStyleSheet("background: #252525; border-radius: 8px;")
        detail_layout = QHBoxLayout(detail_container)
        
        self.heatmap = BitHeatmapWidget()
        detail_layout.addWidget(self.heatmap)
        
        self.detail_lbl = QLabel(I18N.t("scout_detail"))
        self.detail_lbl.setWordWrap(True)
        self.detail_lbl.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.detail_lbl.setStyleSheet("font-family: 'Segoe UI'; font-size: 12px; color: #ccc; padding: 10px;")
        detail_layout.addWidget(self.detail_lbl, 1)
        
        self.splitter.addWidget(detail_container)
        layout.addWidget(self.splitter)

        self.stats_lbl = QLabel(I18N.t("scout_info"))
        self.stats_lbl.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.stats_lbl)
        
        # Initial retranslation
        self.retranslate_ui()

    def retranslate_ui(self):
        """Update all strings in the panel."""
        self.title_lbl.setText(I18N.t("scout_title"))
        self.info_lbl.setText(I18N.t("scout_info"))
        self.ctrl_group.setTitle(I18N.t("nav_analyze"))
        self.res_label.setText(I18N.t("scout_candidates"))
        
        self.btn_baseline.setText(I18N.t("scout_btn_baseline") if self.recording_mode != "baseline" else "⏹️ STOP")
        self.btn_action.setText(I18N.t("scout_btn_action") if self.recording_mode != "action" else "⏹️ STOP")
        self.btn_reset.setText(I18N.t("scout_btn_reset"))
        
        self._update_status_lbl()
        self._update_stats_lbl()

    def _update_status_lbl(self):
        prefix = I18N.t("scout_status")
        if self.recording_mode == "baseline":
            self._status_state = "baseline"
            text = f"{prefix} {I18N.t('scout_rec_baseline')}"
        elif self.recording_mode == "action":
            self._status_state = "action"
            text = f"{prefix} {I18N.t('scout_rec_action')}"
        elif self._status_state == "analyzing":
            text = f"{prefix} ⌛ {I18N.t('scout_analyzing')}"
        elif self._status_state == "complete":
            text = f"{prefix} ✨ {I18N.t('scout_complete')}"
        else:
            self._status_state = "idle"
            text = f"{prefix} {I18N.t('scout_idle')}"
        self.status_lbl.setText(text)

    def _update_stats_lbl(self):
        ids = len(set(self.baseline_data.keys()) | set(self.action_data.keys()))
        b_count = sum(len(v) for v in self.baseline_data.values())
        a_count = sum(len(v) for v in self.action_data.values())
        monitoring_text = f"ID: {ids} | B:{b_count} | A:{a_count}"
        self.stats_lbl.setText(monitoring_text)

    def add_frame(self, can_id: int, data: bytes):
        if self.recording_mode == "baseline":
            self.baseline_data[can_id].append(data)
        elif self.recording_mode == "action":
            self.action_data[can_id].append(data)
        
        ids = len(set(self.baseline_data.keys()) | set(self.action_data.keys()))
        b_count = sum(len(v) for v in self.baseline_data.values())
        a_count = sum(len(v) for v in self.action_data.values())
        self.stats_lbl.setText(f"Active Channels: {ids} | Baseline Frames: {b_count} | Event Frames: {a_count}")

    def _toggle_baseline(self):
        if self.recording_mode == "idle":
            self.recording_mode = "baseline"
            self.btn_baseline.setText(I18N.t("scout_stop_baseline"))
            self.btn_baseline.setStyleSheet("background-color: #d32f2f; color: white; border: 2px solid white;")
            self._update_status_lbl()
            self.btn_action.setEnabled(False)
        else:
            self.recording_mode = "idle"
            self.btn_baseline.setText(I18N.t("scout_btn_baseline"))
            self.btn_baseline.setStyleSheet("")
            self._update_status_lbl()
            self.btn_action.setEnabled(True)

    def _toggle_action(self):
        if self.recording_mode == "idle":
            self.recording_mode = "action"
            self.btn_action.setText(I18N.t("scout_stop_action"))
            self.btn_action.setStyleSheet("background-color: #f57c00; color: white; border: 2px solid white;")
            self._update_status_lbl()
        else:
            self.recording_mode = "idle"
            self.btn_action.setText(I18N.t("scout_btn_action"))
            self.btn_action.setStyleSheet("")
            self._status_state = "analyzing"
            self._update_status_lbl()
            self.analyze_requested.emit(dict(self.baseline_data), dict(self.action_data))

    def show_results(self, all_results: dict):
        self.res_list.clear()
        self._status_state = "complete"
        self._update_status_lbl()
        
        if not all_results:
            self.res_list.addItem(I18N.t("scout_no_diff"))
            return

        # Sort IDs by total score
        sorted_ids = sorted(all_results.keys(), key=lambda x: all_results[x]["total_score"], reverse=True)

        for can_id in sorted_ids:
            res = all_results[can_id]
            # ID Header
            header = QListWidgetItem(f"ID 0x{can_id:03X} (Delta Score: {res['total_score']:.1f})")
            header.setFlags(Qt.NoItemFlags)
            header.setBackground(QColor(40, 40, 40))
            header.setForeground(QColor(200, 200, 200))
            header.setFont(QFont("Segoe UI", 9, QFont.Bold))
            self.res_list.addItem(header)

            for c in res["candidates"]:
                icon = "✨" if c["type"] == "pure" else "🔄"
                bit_text = I18N.t("col_bits")
                len_text = I18N.t("sig_length")
                item_text = f"   {icon} {bit_text} {c['start_bit']} | {len_text} {c['length']} ({c['type']}) » {c['confidence']:.0%}"
                item = QListWidgetItem(item_text)
                
                # Metadata
                c_data = dict(c)
                c_data["can_id"] = can_id
                c_data["heatmap"] = res["heatmap"]
                item.setData(Qt.UserRole, c_data)
                
                if c["type"] == "pure":
                    item.setForeground(QColor("#81c784")) # Greenish
                elif c["type"] == "transitioned":
                    item.setForeground(QColor("#64b5f6")) # Blueish
                
                self.res_list.addItem(item)

    def _on_item_clicked(self, item):
        data = item.data(Qt.UserRole)
        if not data: return
        
        can_id = data["can_id"]
        heatmap = data["heatmap"]
        
        # Highlight bits in heatmap (Neon Orange)
        highlight = []
        for i in range(data["length"]):
            highlight.append((data["start_bit"] + i, QColor(255, 145, 0)))

        self.heatmap.set_data(heatmap, highlight)
        
        # Detailed HTML-style text
        detail_text = (
            f"<h3 style='color: #ffa500;'>ID: 0x{can_id:03X}</h3>"
            f"<b>{I18N.t('nav_analyze')}:</b> {data['type'].upper()}<br>"
            f"<b>{I18N.t('sig_start')}:</b> {data['start_bit']}, <b>{I18N.t('sig_length')}:</b> {data['length']}<br>"
            f"<b>Probability:</b> {data['confidence']:.1%}<br><br>"
            f"<span style='color: #888;'>{I18N.t('scout_load_signal_tip') if I18N.t('scout_load_signal_tip') != 'scout_load_signal_tip' else 'Double-click to load into Designer.'}</span>"
        )
        self.detail_lbl.setText(detail_text)

    def _on_item_double_clicked(self, item):
        data = item.data(Qt.UserRole)
        if data:
            self.signal_added.emit(data['can_id'], data['start_bit'], data['length'])

    def reset(self):
        self.baseline_data.clear()
        self.action_data.clear()
        self.recording_mode = "idle"
        self._status_state = "idle"
        self.res_list.clear()
        self.detail_lbl.setText(I18N.t("scout_detail"))
        self.heatmap.set_data([0]*64)
        self.btn_baseline.setText(I18N.t("scout_btn_baseline"))
        self.btn_action.setText(I18N.t("scout_btn_action"))
        self.btn_action.setEnabled(False)
        self._update_status_lbl()
        self._update_stats_lbl()
