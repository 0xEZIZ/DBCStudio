"""
ui/log_console.py - Application Log Console Widget
Programmanyň logs-laryny UI-da görkezýär.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QLabel, QHBoxLayout, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor
from core.i18n import I18N
import logging

class LogSignalEmitter(QObject):
    """Log-lary Qt signal-y görnüşinde emit edýär."""
    new_log = pyqtSignal(str, int) # message, level

class QtLogHandler(logging.Handler):
    """Logging handler that emits signals."""
    def __init__(self, emitter):
        super().__init__()
        self.emitter = emitter

    def emit(self, record):
        msg = self.format(record)
        self.emitter.new_log.emit(msg, record.levelno)

class LogConsole(QWidget):
    """
    Programmanyň consolesy - Error we maglumatlary görkezýär.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.emitter = LogSignalEmitter()
        self.emitter.new_log.connect(self._add_log)
        
        # Sazlamalar
        handler = QtLogHandler(self.emitter)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header = QHBoxLayout()
        self.title_lbl = QLabel(I18N.t("console_title"))
        header.addWidget(self.title_lbl)
        header.addStretch()
        
        self.btn_clear = QPushButton(I18N.t("console_clear"))
        self.btn_clear.setFixedWidth(80)
        self.btn_clear.clicked.connect(lambda: self.log_view.clear() if hasattr(self, 'log_view') else None)
        header.addWidget(self.btn_clear)
        layout.addLayout(header)

        # Log Text Area
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Cascadia Code", 9))
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #333;")
        layout.addWidget(self.log_view)

    def _add_log(self, message, level):
        """Täze log goşýar."""
        color = "#d4d4d4" # default info
        if level >= logging.ERROR:
            color = "#f44336" # Red
        elif level >= logging.WARNING:
            color = "#ffeb3b" # Yellow
        
        html = f'<span style="color: {color};">{message}</span>'
        self.log_view.appendHtml(html)
        
        # Auto-scroll
        self.log_view.verticalScrollBar().setValue(
            self.log_view.verticalScrollBar().maximum()
        )

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.title_lbl.setText(I18N.t("console_title"))
        self.btn_clear.setText(I18N.t("console_clear"))
