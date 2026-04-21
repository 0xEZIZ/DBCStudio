"""
bit_editor.py - Bit-Level Visual Editor
CAN message data-ny bit derejesinde görkezýär we signal-lary wizual saýlamaga
mümkinçilik berýär. Drag & select funksiýasy bar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolTip, QSizePolicy, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import (
    QPainter, QColor, QFont, QPen, QBrush, QFontMetrics, QCursor
)
from ui.theme import COLORS_LIGHT, COLORS_DARK
from core.i18n import I18N


# Signal-lar üçin reňkler (8 dürli reňk)
SIGNAL_COLORS = [
    "#4285F4", "#EA4335", "#34A853", "#FBBC04",
    "#8E24AA", "#00ACC1", "#FF6D00", "#43A047",
    "#E91E63", "#00BCD4", "#FF5722", "#607D8B"
]


class BitGridWidget(QWidget):
    """
    CAN message data-ny bit grid görnüşinde görkezýän widget.
    8 byte x 8 bit = 64 bit grid.

    User mouse bilen bitleri saýlap signal kesgitläp bilýär.
    """

    # Signals
    selection_changed = pyqtSignal(int, int)  # start_bit, length
    bit_hovered = pyqtSignal(int)  # bit index

    # Ölçegler
    CELL_SIZE = 44
    CELL_PADDING = 2
    HEADER_HEIGHT = 28
    ROW_HEADER_WIDTH = 56
    LABEL_HEIGHT = 20

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.colors = COLORS_DARK if dark_mode else COLORS_LIGHT

        # Data
        self.data = bytes(8)  # 8 byte default
        self.dlc = 8

        # Signal mapping: bit_index -> (signal_index, signal_name)
        self.signal_map = {}
        self.signal_names = []

        # Selection state
        self.selecting = False
        self.select_start = -1
        self.select_end = -1
        self.hover_bit = -1

        # Widget settings
        total_w = self.ROW_HEADER_WIDTH + 8 * (self.CELL_SIZE + self.CELL_PADDING) + 16
        total_h = self.HEADER_HEIGHT + 8 * (self.CELL_SIZE + self.CELL_PADDING) + self.LABEL_HEIGHT + 16
        self.setMinimumSize(total_w, total_h)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)

    def set_data(self, data: bytes):
        """CAN frame data-ny set edýär."""
        self.data = data
        self.dlc = len(data)
        self.update()

    def set_signals(self, signals: list):
        """Signal-lary set edýär (signal map döretmek üçin)."""
        self.signal_map.clear()
        self.signal_names.clear()

        for i, sig in enumerate(signals):
            self.signal_names.append(sig.name)
            if sig.byte_order == "little_endian":
                # Intel: bits are sequential from start_bit
                for bit_offset in range(sig.length):
                    bit_idx = sig.start_bit + bit_offset
                    if 0 <= bit_idx < self.dlc * 8:
                        self.signal_map[bit_idx] = (i, sig.name)
            else:
                # Motorola (big-endian): MSB is at start_bit,
                # bits proceed within byte then wrap to next byte
                byte_idx = sig.start_bit // 8
                bit_in_byte = sig.start_bit % 8
                for bit_offset in range(sig.length):
                    bit_idx = byte_idx * 8 + bit_in_byte
                    if 0 <= bit_idx < self.dlc * 8:
                        self.signal_map[bit_idx] = (i, sig.name)
                    if bit_in_byte == 0:
                        byte_idx += 1
                        bit_in_byte = 7
                    else:
                        bit_in_byte -= 1

        self.update()

    def clear_selection(self):
        """Saýlanyny arassalaýar."""
        self.select_start = -1
        self.select_end = -1
        self.selecting = False
        self.update()

    def get_selection(self):
        """Häzirki saýlany gaýtarýar: (start_bit, length) ýa-da None."""
        if self.select_start >= 0 and self.select_end >= 0:
            s = min(self.select_start, self.select_end)
            e = max(self.select_start, self.select_end)
            return (s, e - s + 1)
        return None

    # ── Drawing ──

    def paintEvent(self, event):
        """Widget-i çyzýar."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        self._draw_headers(painter)
        self._draw_grid(painter)
        self._draw_selection_info(painter)

        painter.end()

    def _draw_headers(self, painter: QPainter):
        """Sütün we setir header-lary çyzýar."""
        header_font = QFont("Segoe UI", 9, QFont.Bold)
        painter.setFont(header_font)
        painter.setPen(QColor(self.colors["text_secondary"]))

        # Sütün header-lary (bit 7 -> bit 0)
        for col in range(8):
            x = self.ROW_HEADER_WIDTH + col * (self.CELL_SIZE + self.CELL_PADDING)
            bit_label = I18N.t("bit_header").format(n=7 - col)
            rect = QRect(x, 0, self.CELL_SIZE, self.HEADER_HEIGHT)
            painter.drawText(rect, Qt.AlignCenter, bit_label)

        # Setir header-lary (Byte 0 -> Byte 7)
        for row in range(min(self.dlc, 8)):
            y = self.HEADER_HEIGHT + row * (self.CELL_SIZE + self.CELL_PADDING)
            byte_label = I18N.t("byte_header").format(n=row)
            rect = QRect(0, y, self.ROW_HEADER_WIDTH - 4, self.CELL_SIZE)
            painter.drawText(rect, Qt.AlignVCenter | Qt.AlignRight, byte_label)

    def _draw_grid(self, painter: QPainter):
        """Bit grid-ini çyzýar."""
        cell_font = QFont("Cascadia Code", 11, QFont.Bold)
        painter.setFont(cell_font)

        for row in range(min(self.dlc, 8)):
            byte_val = self.data[row] if row < len(self.data) else 0

            for col in range(8):
                bit_pos = 7 - col  # MSB first
                bit_idx = row * 8 + bit_pos
                bit_val = (byte_val >> bit_pos) & 1

                x = self.ROW_HEADER_WIDTH + col * (self.CELL_SIZE + self.CELL_PADDING)
                y = self.HEADER_HEIGHT + row * (self.CELL_SIZE + self.CELL_PADDING)
                rect = QRect(x, y, self.CELL_SIZE, self.CELL_SIZE)

                # Reňk kesgitle
                bg_color, text_color, border_color = self._get_cell_colors(
                    bit_idx, bit_val
                )

                # Fon çyz
                painter.setPen(QPen(QColor(border_color), 1))
                painter.setBrush(QBrush(QColor(bg_color)))
                painter.drawRoundedRect(rect, 4, 4)

                # Bit bahasy ýaz
                painter.setPen(QColor(text_color))
                painter.drawText(rect, Qt.AlignCenter, str(bit_val))

                # Bit index kiçi ýaz
                idx_font = QFont("Segoe UI", 7)
                painter.setFont(idx_font)
                painter.setPen(QColor(self.colors["text_tertiary"]))
                idx_rect = QRect(x + 2, y + 2, self.CELL_SIZE - 4, 12)
                painter.drawText(idx_rect, Qt.AlignLeft | Qt.AlignTop, str(bit_idx))
                painter.setFont(cell_font)

    def _get_cell_colors(self, bit_idx, bit_val):
        """Öýjük üçin reňkleri gaýtarýar."""
        # Saýlanan
        sel = self.get_selection()
        if sel and sel[0] <= bit_idx < sel[0] + sel[1]:
            return (
                self.colors["bit_selected"],
                "#FFFFFF",
                self.colors["border_focus"]
            )

        # Signal-a degişli
        if bit_idx in self.signal_map:
            sig_idx = self.signal_map[bit_idx][0]
            color = SIGNAL_COLORS[sig_idx % len(SIGNAL_COLORS)]
            return color, "#FFFFFF", color

        # Hover
        if bit_idx == self.hover_bit:
            return (
                self.colors["bit_hover"],
                self.colors["text_primary"],
                self.colors["border"]
            )

        # Normal
        if bit_val:
            return (
                self.colors["bit_1"],
                self.colors["text_primary"],
                self.colors["border"]
            )
        return (
            self.colors["bit_0"],
            self.colors["text_secondary"],
            self.colors["border_light"]
        )

    def _draw_selection_info(self, painter: QPainter):
        """Saýlanan diapazon barada maglumat ýazýar."""
        sel = self.get_selection()
        if not sel:
            return

        y = self.HEADER_HEIGHT + self.dlc * (self.CELL_SIZE + self.CELL_PADDING) + 4
        info_font = QFont("Segoe UI", 10, QFont.Bold)
        painter.setFont(info_font)
        painter.setPen(QColor(self.colors["bg_accent"]))

        text = I18N.t("bit_selection_info").format(start=sel[0], len=sel[1])
        painter.drawText(self.ROW_HEADER_WIDTH, y + 14, text)

    # ── Mouse Events ──

    def _bit_at_pos(self, pos: QPoint) -> int:
        """Mouse pozisiýasyndan bit index-i tapýar."""
        col = (pos.x() - self.ROW_HEADER_WIDTH) // (self.CELL_SIZE + self.CELL_PADDING)
        row = (pos.y() - self.HEADER_HEIGHT) // (self.CELL_SIZE + self.CELL_PADDING)

        if 0 <= col < 8 and 0 <= row < self.dlc:
            bit_pos = 7 - col
            return row * 8 + bit_pos
        return -1

    def mousePressEvent(self, event):
        """Mouse basma - selection başla."""
        if event.button() == Qt.LeftButton:
            bit = self._bit_at_pos(event.pos())
            if bit >= 0:
                self.selecting = True
                self.select_start = bit
                self.select_end = bit
                self.update()

    def mouseMoveEvent(self, event):
        """Mouse hereketde - selection giňelt ýa-da hover görkez."""
        bit = self._bit_at_pos(event.pos())

        if self.selecting and bit >= 0:
            self.select_end = bit
            self.update()
        elif bit != self.hover_bit:
            self.hover_bit = bit
            self.bit_hovered.emit(bit)
            self.update()

            # Tooltip
            if bit >= 0:
                byte_idx = bit // 8
                bit_in_byte = bit % 8
                bit_text = I18N.t("bit_header").format(n=bit)
                byte_text = I18N.t("byte_header").format(n=byte_idx)
                tip = f"{bit_text} ({byte_text}, Bit {bit_in_byte})"
                if bit in self.signal_map:
                    tip += f"\nSignal: {self.signal_map[bit][1]}"
                QToolTip.showText(QCursor.pos(), tip)

    def mouseReleaseEvent(self, event):
        """Mouse goýberme - selection gutardy."""
        if event.button() == Qt.LeftButton and self.selecting:
            self.selecting = False
            sel = self.get_selection()
            if sel:
                self.selection_changed.emit(sel[0], sel[1])
            self.update()

    def leaveEvent(self, event):
        """Mouse widget-den çykanda."""
        self.hover_bit = -1
        self.update()


class BitEditorPanel(QWidget):
    """
    Bit Editor panel - BitGridWidget + maglumat paneli.
    """

    selection_changed = pyqtSignal(int, int)

    def __init__(self, parent=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Info & Hex area (Styled container)
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: palette(alternate-base);
                border: 1px solid palette(midlight);
                border-radius: 8px;
            }
            QLabel { border: none; background: transparent; }
        """)
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.setSpacing(4)

        self.info_label = QLabel(I18N.t("bit_editor_info"))
        self.info_label.setProperty("subheading", True)
        self.info_label.setStyleSheet("font-size: 13px;")
        header_layout.addWidget(self.info_label)

        hex_row = QHBoxLayout()
        self.hex_title = QLabel(I18N.t("bit_data_hex"))
        self.hex_title.setProperty("caption", True)
        self.hex_display = QLabel("00 00 00 00 00 00 00 00")
        self.hex_display.setStyleSheet(
            "font-family: 'Cascadia Code', monospace; font-size: 14px; font-weight: bold; color: palette(link);"
        )
        hex_row.addWidget(self.hex_title)
        hex_row.addWidget(self.hex_display)
        hex_row.addStretch()
        header_layout.addLayout(hex_row)

        layout.addWidget(header_frame)

        # Bit grid
        self.grid = BitGridWidget(dark_mode=self.dark_mode)
        self.grid.selection_changed.connect(self._on_selection_changed)
        layout.addWidget(self.grid, 1)

        # Instructions
        self.help_label = QLabel(I18N.t("bit_tip"))
        self.help_label.setProperty("caption", True)
        self.help_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.help_label)

    def set_frame_data(self, data: bytes, msg_name: str = ""):
        """Frame data-ny set edýär."""
        self.grid.set_data(data)
        self.hex_display.setText(" ".join(f"{b:02X}" for b in data))
        if msg_name:
            self.info_label.setText(f"{I18N.t('nav_explorer')}: {msg_name} (DLC={len(data)})")

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.info_label.setText(I18N.t("bit_editor_info"))
        self.hex_title.setText(I18N.t("bit_data_hex"))
        self.help_label.setText(I18N.t("bit_tip"))
        self.grid.update()

    def set_signals(self, signals: list):
        """Signal-lary set edýär."""
        self.grid.set_signals(signals)

    def _on_selection_changed(self, start_bit, length):
        self.selection_changed.emit(start_bit, length)
