"""
ui/manager_dialogs.py - Data editing dialogs for modern DB management.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, 
    QDialogButtonBox, QFormLayout, QGroupBox
)
from PyQt5.QtCore import Qt


class NodeEditorDialog(QDialog):
    def __init__(self, node=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ECU (Node) Editor")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit(node.name if node else "")
        self.comment_edit = QTextEdit(node.comment if node else "")
        self.comment_edit.setMaximumHeight(100)
        
        form.addRow("Node Name:", self.name_edit)
        form.addRow("Comment:", self.comment_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "comment": self.comment_edit.toPlainText()
        }


class AttributeDefinitionDialog(QDialog):
    def __init__(self, adef=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attribute Definition Editor")
        self.setMinimumWidth(450)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit(adef.name if adef else "")
        self.obj_type_combo = QComboBox()
        self.obj_type_combo.addItems(["", "BU_", "BO_", "SG_", "EV_"])
        if adef: self.obj_type_combo.setCurrentText(adef.object_type or "")
        
        self.val_type_combo = QComboBox()
        self.val_type_combo.addItems(["INT", "HEX", "FLOAT", "STRING", "ENUM"])
        if adef: self.val_type_combo.setCurrentText(adef.value_type)
        
        self.min_edit = QDoubleSpinBox()
        self.min_edit.setRange(-1e9, 1e9)
        self.max_edit = QDoubleSpinBox()
        self.max_edit.setRange(-1e9, 1e9)
        if adef:
            self.min_edit.setValue(adef.minimum or 0)
            self.max_edit.setValue(adef.maximum or 0)

        self.enum_edit = QLineEdit(", ".join(adef.enum_values) if adef and adef.enum_values else "")
        self.enum_edit.setPlaceholderText("Val1, Val2, Val3...")
        
        form.addRow("Attribute Name:", self.name_edit)
        form.addRow("Object Scope:", self.obj_type_combo)
        form.addRow("Value Type:", self.val_type_combo)
        form.addRow("Min Value:", self.min_edit)
        form.addRow("Max Value:", self.max_edit)
        form.addRow("Enum Values:", self.enum_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "object_type": self.obj_type_combo.currentText(),
            "value_type": self.val_type_combo.currentText(),
            "minimum": self.min_edit.value(),
            "maximum": self.max_edit.value(),
            "enum_values": [s.strip() for s in self.enum_edit.text().split(",") if s.strip()]
        }


class EnvVarEditorDialog(QDialog):
    def __init__(self, ev=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Environment Variable Editor")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit(ev.name if ev else "")
        self.type_combo = QComboBox()
        self.type_combo.addItems(["0 (Integer)", "1 (Float)", "2 (String)"])
        if ev: self.type_combo.setCurrentIndex(ev.var_type)
        
        self.min_edit = QDoubleSpinBox()
        self.min_edit.setRange(-1e9, 1e9)
        self.max_edit = QDoubleSpinBox()
        self.max_edit.setRange(-1e9, 1e9)
        if ev:
            self.min_edit.setValue(ev.min)
            self.max_edit.setValue(ev.max)
            
        self.unit_edit = QLineEdit(ev.unit if ev else "")
        self.initial_edit = QDoubleSpinBox()
        self.initial_edit.setRange(-1e9, 1e9)
        if ev: self.initial_edit.setValue(ev.initial_value)

        form.addRow("Name:", self.name_edit)
        form.addRow("Variable Type:", self.type_combo)
        form.addRow("Min Range:", self.min_edit)
        form.addRow("Max Range:", self.max_edit)
        form.addRow("Unit:", self.unit_edit)
        form.addRow("Initial Value:", self.initial_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "var_type": self.type_combo.currentIndex(),
            "minimum": self.min_edit.value(),
            "maximum": self.max_edit.value(),
            "unit": self.unit_edit.text(),
            "initial_value": self.initial_edit.value()
        }
