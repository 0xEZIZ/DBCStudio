"""
ui/comparison_dialog.py - High-level visualization of differences between two CAN logs.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QTableWidget, QTableWidgetItem, QHeaderView, 
    QFrame, QAbstractItemView, QLineEdit
)
from PyQt5.QtCore import Qt


class LogComparisonDialog(QDialog):
    def __init__(self, comparison_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Multi-Log Comparison Results")
        self.resize(1000, 700)
        
        self.data = comparison_data
        self._setup_ui()
        self._populate()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Summary Header
        header = QFrame()
        header.setStyleSheet("background-color: #f8f9fa; border-radius: 8px; padding: 10px;")
        h_layout = QHBoxLayout(header)
        
        info = (
            f"<b>Unique IDs Log 1:</b> {len(self.data['only_in_log1'])} | "
            f"<b>Unique IDs Log 2:</b> {len(self.data['only_in_log2'])} | "
            f"<b>Common IDs:</b> {len(self.data['common'])}"
        )
        h_layout.addWidget(QLabel(info))
        layout.addWidget(header)

        # Search / Filter
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Filter by CAN ID (HEX)...")
        self.search_edit.textChanged.connect(self._filter_table)
        layout.addWidget(self.search_edit)

        # Main Difference Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "CAN ID", "Log 1 Count", "Log 2 Count", "Status / Changed Bytes"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        
        layout.addWidget(self.table)

        # Legend / Info Footer
        footer = QLabel(
            "<span style='color: #d9534f;'>● Red: Only in Log 1</span> | "
            "<span style='color: #5cb85c;'>● Green: Only in Log 2</span> | "
            "<span style='color: #f0ad4e;'>● Yellow: Content Change</span>"
        )
        footer.setAlignment(Qt.AlignCenter)
        layout.addWidget(footer)

    def _populate(self):
        self.table.setRowCount(0)
        all_ids = sorted(list(set(self.data['only_in_log1'] + self.data['only_in_log2'] + self.data['common'])))
        
        for can_id in all_ids:
            row = self.table.rowCount()
            self.table.insertRow(row)

            id_str = f"0x{can_id:03X}"
            self.table.setItem(row, 0, QTableWidgetItem(id_str))

            # Status and Styling
            status_text = ""
            color = None

            if can_id in self.data['only_in_log1']:
                self.table.setItem(row, 1, QTableWidgetItem("Yes"))
                self.table.setItem(row, 2, QTableWidgetItem("No"))
                status_text = "Missing in Log 2"
                color = "#f2dede" # Light Red
            elif can_id in self.data['only_in_log2']:
                self.table.setItem(row, 1, QTableWidgetItem("No"))
                self.table.setItem(row, 2, QTableWidgetItem("Yes"))
                status_text = "New in Log 2"
                color = "#dff0d8" # Light Green
            else:
                # Common ID, check message content
                diff_info = self.data['differences'].get(can_id)
                cnt1 = diff_info['count_log1'] if diff_info else "N/A"
                cnt2 = diff_info['count_log2'] if diff_info else "N/A"
                self.table.setItem(row, 1, QTableWidgetItem(str(cnt1)))
                self.table.setItem(row, 2, QTableWidgetItem(str(cnt2)))

                if diff_info and diff_info['changed_bytes']:
                    changed = [f"B{b['byte']}" for b in diff_info['changed_bytes']]
                    status_text = f"Data change in: {', '.join(changed)}"
                    color = "#fcf8e3" # Light Yellow
                else:
                    status_text = "Identical behavior"

            # Apply background color to entire row if needed
            if color:
                from PyQt5.QtGui import QColor as QC
                bg = QC(color)
                for col in range(4):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(bg)
            
            self.table.setItem(row, 3, QTableWidgetItem(status_text))

    def _filter_table(self, text):
        for i in range(self.table.rowCount()):
            match = text.lower() in self.table.item(i, 0).text().lower()
            self.table.setRowHidden(i, not match)
