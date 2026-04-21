"""
ui/hardware_dialog.py - CAN Hardware Connection Dialog
IXXAT we beýleki interfeýsler üçin sazlamalar penjiresi.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QPushButton, QCheckBox, QGroupBox,
    QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt
from core.i18n import I18N

class HardwareSetupDialog(QDialog):
    """
    CAN Adapterini birikdirmek we sazlamak üçin dialog.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(I18N.t("hw_title"))
        self.setFixedWidth(400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # 1. Interface Selection
        group_hw = QGroupBox(I18N.t("hw_settings"))
        form = QFormLayout(group_hw)
        
        self.interface_combo = QComboBox()
        self.interface_combo.addItems(["IXXAT (VCI 4)"])
        form.addRow(I18N.t("hw_interface"), self.interface_combo)

        self.channel_combo = QComboBox()
        self.channel_combo.addItems(["Channel 0", "Channel 1", "Channel 2"])
        form.addRow(I18N.t("hw_channel"), self.channel_combo)

        self.bitrate_combo = QComboBox()
        # Common bitrates
        bitrates = ["1000 kbps (1M)", "500 kbps", "250 kbps", "125 kbps", "100 kbps", "50 kbps"]
        self.bitrate_combo.addItems(bitrates)
        self.bitrate_combo.setCurrentIndex(1) # Default 500k
        form.addRow(I18N.t("hw_bitrate"), self.bitrate_combo)
        
        layout.addWidget(group_hw)

        # 2. Logging Settings
        group_log = QGroupBox(I18N.t("hw_logging"))
        l_layout = QVBoxLayout(group_log)
        
        self.chk_autosave = QCheckBox(I18N.t("hw_autosave"))
        self.chk_autosave.setChecked(True)
        self.chk_autosave.setProperty("class", "PlaceholderText")
        l_layout.addWidget(self.chk_autosave)
        
        self.chk_listen_only = QCheckBox(I18N.t("hw_listen_only"))
        self.chk_listen_only.setChecked(False)
        l_layout.addWidget(self.chk_listen_only)
        
        layout.addWidget(group_log)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_settings(self) -> dict:
        """User tarapyndan saýlanan sazlamalary gaýtarýar."""
        # Bitrate parse (ex: "500 kbps" -> 500000)
        bitrate_str = self.bitrate_combo.currentText().split(" ")[0]
        bitrate = int(bitrate_str) * 1000

        return {
            "interface": "ixxat",
            "channel": self.channel_combo.currentIndex(),
            "bitrate": bitrate,
            "autosave": self.chk_autosave.isChecked(),
            "listen_only": self.chk_listen_only.isChecked()
        }
