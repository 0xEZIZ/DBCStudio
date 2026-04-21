"""
graph_panel.py - Signal Graph Visualization Panel
Signal bahalaryny grafik görnüşinde görkezýär.
Multiple signal overlay, zoom, pan goldawy bar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from i18n import I18N

# pyqtgraph import - eger ýok bolsa fallback
try:
    import pyqtgraph as pg
    HAS_PYQTGRAPH = True
except ImportError:
    HAS_PYQTGRAPH = False

from ui.theme import COLORS_LIGHT, COLORS_DARK


# Graph reňkleri
GRAPH_COLORS = [
    (66, 133, 244),    # Blue
    (234, 67, 53),     # Red
    (52, 168, 83),     # Green
    (251, 188, 4),     # Yellow
    (142, 36, 170),    # Purple
    (0, 172, 193),     # Cyan
    (255, 109, 0),     # Orange
    (67, 160, 71),     # Dark Green
]


class GraphPanel(QWidget):
    """Signal graph visualization panel."""

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.colors = COLORS_DARK if dark_mode else COLORS_LIGHT
        self.plot_items = {}  # signal_name -> PlotDataItem
        self.signal_data = {}  # signal_name -> (timestamps, values)
        self._signal_colors = {}  # signal_name -> color_index (persistent)
        self._next_color_idx = 0
        self.playback_line = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        self.title_lbl = QLabel(I18N.t("graph_title"))
        self.title_lbl.setProperty("subheading", True)
        header.addWidget(self.title_lbl)
        header.addStretch()

        self.btn_clear = QPushButton(I18N.t("console_clear"))
        self.btn_clear.setFixedWidth(80)
        self.btn_clear.clicked.connect(self.clear_all)
        header.addWidget(self.btn_clear)

        self.btn_auto_range = QPushButton(I18N.t("graph_auto_range"))
        self.btn_auto_range.setFixedWidth(100)
        header.addWidget(self.btn_auto_range)

        layout.addLayout(header)

        if HAS_PYQTGRAPH:
            self._setup_pyqtgraph(layout)
        else:
            self._setup_fallback(layout)

        # Legend
        self.legend_layout = QHBoxLayout()
        self.legend_layout.setSpacing(16)
        layout.addLayout(self.legend_layout)

    def _setup_pyqtgraph(self, layout):
        """pyqtgraph bilen graph setup."""
        # pyqtgraph konfigurasiýasy
        bg_color = self.colors["graph_bg"]
        pg.setConfigOptions(antialias=True)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(bg_color)
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel("bottom", I18N.t("graph_axis_x"), units="")
        self.plot_widget.setLabel("left", I18N.t("graph_axis_y"), units="")

        # Cross-hair
        self.vline = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#888", width=1))
        self.hline = pg.InfiniteLine(angle=0, movable=False, pen=pg.mkPen("#888", width=1))
        self.plot_widget.addItem(self.vline, ignoreBounds=True)
        self.plot_widget.addItem(self.hline, ignoreBounds=True)

        # Playback sync cursor (Distinct color)
        self.playback_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen("#FFD700", width=2, style=Qt.DashLine))
        self.plot_widget.addItem(self.playback_line, ignoreBounds=True)
        self.playback_line.hide()

        # Mouse move tracking
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_moved)

        self.btn_auto_range.clicked.connect(
            lambda: self.plot_widget.autoRange()
        )

        layout.addWidget(self.plot_widget)

    def _setup_fallback(self, layout):
        """pyqtgraph ýok bolsa fallback UI."""
        self.plot_widget = None
        self.fallback_lbl = QLabel(I18N.t("graph_fallback"))
        self.fallback_lbl.setAlignment(Qt.AlignCenter)
        self.fallback_lbl.setStyleSheet("color: #999; font-size: 14px; padding: 40px;")
        layout.addWidget(self.fallback_lbl)

    def _on_mouse_moved(self, pos):
        """Cross-hair mouse hereketinde ýerleşdirýär."""
        if not self.plot_widget:
            return
        mouse_point = self.plot_widget.plotItem.vb.mapSceneToView(pos)
        self.vline.setPos(mouse_point.x())
        self.hline.setPos(mouse_point.y())

    def add_signal(self, name: str, timestamps: list, values: list):
        """Grafa signal goşýar."""
        if not HAS_PYQTGRAPH or not self.plot_widget:
            return

        # Assign persistent color
        if name not in self._signal_colors:
            self._signal_colors[name] = self._next_color_idx
            self._next_color_idx += 1
        color_idx = self._signal_colors[name] % len(GRAPH_COLORS)
        color = GRAPH_COLORS[color_idx]
        pen = pg.mkPen(color=color, width=2)

        # X okuny döret (eger timestamp ýok bolsa index ulan)
        if timestamps and timestamps[0] != 0:
            x_data = timestamps
        else:
            x_data = list(range(len(values)))

        # Plot item döret
        plot_item = self.plot_widget.plot(
            x_data, values, pen=pen, name=name
        )
        self.plot_items[name] = plot_item
        self.signal_data[name] = (x_data, values)

        # Legend-e goş
        self._update_legend()

        # Auto range
        self.plot_widget.autoRange()

    def remove_signal(self, name: str):
        """Grafdan signal aýyrýar."""
        if name in self.plot_items:
            self.plot_widget.removeItem(self.plot_items[name])
            del self.plot_items[name]
            del self.signal_data[name]
            # Keep _signal_colors[name] so color stays stable if re-added
            self._update_legend()

    def clear_all(self):
        """Ähli signal-lary aýyrýar."""
        if self.plot_widget:
            for item in self.plot_items.values():
                self.plot_widget.removeItem(item)
        self.plot_items.clear()
        self.signal_data.clear()
        self._signal_colors.clear()
        self._next_color_idx = 0
        self._update_legend()

    def update_signal(self, name: str, timestamps: list, values: list):
        """Bar bolan signal-y täzeläýär."""
        if name in self.plot_items:
            if timestamps and timestamps[0] != 0:
                x_data = timestamps
            else:
                x_data = list(range(len(values)))
            self.plot_items[name].setData(x_data, values)
            self.signal_data[name] = (x_data, values)

    def set_playback_position(self, timestamp: float):
        """Playbak cursor-yny görkezilen wagtda ýerleşdirýär."""
        if self.playback_line:
            self.playback_line.setPos(timestamp)
            if self.playback_line.isHidden():
                self.playback_line.show()

    def _update_legend(self):
        """Legend-i täzeläýär."""
        # Köne legend-leri aýyr
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for name in self.plot_items.keys():
            color_idx = self._signal_colors.get(name, 0) % len(GRAPH_COLORS)
            color = GRAPH_COLORS[color_idx]
            color_hex = f"#{color[0]:02X}{color[1]:02X}{color[2]:02X}"

            legend_item = QLabel(f"  {name}")
            legend_item.setStyleSheet(
                f"background: {color_hex}; color: white; "
                f"padding: 2px 8px; border-radius: 4px; font-size: 11px;"
            )
            self.legend_layout.addWidget(legend_item)

        self.legend_layout.addStretch()

    def set_dark_mode(self, dark: bool):
        """Dark mode-y üýtgedýär."""
        self.dark_mode = dark
        self.colors = COLORS_DARK if dark else COLORS_LIGHT
        if self.plot_widget:
            self.plot_widget.setBackground(self.colors["graph_bg"])

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.title_lbl.setText(I18N.t("graph_title"))
        self.btn_clear.setText(I18N.t("console_clear"))
        self.btn_auto_range.setText(I18N.t("graph_auto_range"))
        
        if HAS_PYQTGRAPH and self.plot_widget:
            self.plot_widget.setLabel("bottom", I18N.t("graph_axis_x"))
            self.plot_widget.setLabel("left", I18N.t("graph_axis_y"))
        elif hasattr(self, 'fallback_lbl'):
            self.fallback_lbl.setText(I18N.t("graph_fallback"))
