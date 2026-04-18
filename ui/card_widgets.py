"""
ui/card_widgets.py - Modern Card-based UI Components (Professional Edition)
DBC obýektlerini (Node, Attribute, EnvVar) modern we premium dizaýnda görkezýär.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFrame, QLayout, QSizePolicy, QStyle
)
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PyQt5.QtGui import QIcon, QFont


class FlowLayout(QLayout):
    """
    Kand kartoçkalaryny awtomatiki ýerleşdirýän responsive layout.
    """
    def __init__(self, parent=None, margin=-1, hspacing=-1, vspacing=-1):
        super().__init__(parent)
        self._hspacing = hspacing
        self._vspacing = vspacing
        self._items = []
        self.setContentsMargins(margin, margin, margin, margin)

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self._items.append(item)

    def smartSpacing(self, pm):
        parent = self.parent()
        if not parent:
            return -1
        elif parent.isWidgetType():
            return parent.style().pixelMetric(pm, None, parent)
        else:
            return parent.spacing()

    def horizontalSpacing(self):
        if self._hspacing >= 0:
            return self._hspacing
        else:
            return self.smartSpacing(QStyle.PM_LayoutHorizontalSpacing)

    def verticalSpacing(self):
        if self._vspacing >= 0:
            return self._vspacing
        else:
            return self.smartSpacing(QStyle.PM_LayoutVerticalSpacing)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def _do_layout(self, rect, test_only):
        left, top, right, bottom = self.getContentsMargins()
        effective_rect = rect.adjusted(+left, +top, -right, -bottom)
        x = effective_rect.x()
        y = effective_rect.y()
        line_height = 0

        for item in self._items:
            wid = item.widget()
            space_x = self.horizontalSpacing()
            if space_x == -1:
                space_x = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            space_y = self.verticalSpacing()
            if space_y == -1:
                space_y = wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > effective_rect.right() and line_height > 0:
                x = effective_rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y() + bottom


class ModernCard(QFrame):
    """
    Base class for all management cards. 
    Premium styling: Rounded corners, border, hover animations (via CSS).
    """
    def __init__(self, title, subtitle="", icon_text="📦", parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        self.setFixedWidth(280)
        self.setFixedHeight(180)
        
        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(16, 16, 16, 16)
        self.layout.setSpacing(10)

        # Header (Icon + Title)
        header_layout = QHBoxLayout()
        self.icon_label = QLabel(icon_text)
        self.icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(self.icon_label)
        
        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "CardTitle")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label, 1)
        
        self.layout.addLayout(header_layout)

        # Subtitle / Description
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("class", "CardSubtitle")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.layout.addWidget(self.subtitle_label, 1)

        # Footer (Actions)
        self.footer_layout = QHBoxLayout()
        self.footer_layout.setSpacing(8)
        self.layout.addLayout(self.footer_layout)

    def add_action(self, text, callback, primary=False):
        btn = QPushButton(text)
        if primary:
            btn.setProperty("class", "PrimaryButton")
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(callback)
        self.footer_layout.addWidget(btn)
        return btn


class NodeCard(ModernCard):
    def __init__(self, node_obj, on_edit, on_delete, parent=None):
        subtitle = f"Comment: {node_obj.comment or 'No comment'}"
        super().__init__(node_obj.name, subtitle, "🖥️", parent)
        self.node = node_obj
        self.add_action("Edit", lambda: on_edit(self.node))
        self.add_action("Delete", lambda: on_delete(self.node))


class AttributeCard(ModernCard):
    def __init__(self, attr_obj, on_edit, on_delete, parent=None):
        subtitle = f"Type: {attr_obj.value_type}\nScope: {attr_obj.object_type or 'Network'}"
        super().__init__(attr_obj.name, subtitle, "⚙️", parent)
        self.attribute = attr_obj
        self.add_action("Edit", lambda: on_edit(self.attribute))
        self.add_action("Delete", lambda: on_delete(self.attribute))


class EnvVarCard(ModernCard):
    def __init__(self, ev_obj, on_edit, on_delete, parent=None):
        subtitle = f"Type: {ev_obj.var_type}\nRange: [{ev_obj.min}|{ev_obj.max}]"
        super().__init__(ev_obj.name, subtitle, "🌍", parent)
        self.env_var = ev_obj
        self.add_action("Edit", lambda: on_edit(self.env_var))
        self.add_action("Delete", lambda: on_delete(self.env_var))


class AddActionCard(QFrame):
    """
    The 'Add New' placeholder card.
    """
    def __init__(self, label_text, callback, parent=None):
        super().__init__(parent)
        self.setObjectName("AddActionCard")
        self.setFixedWidth(280)
        self.setFixedHeight(180)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        plus_label = QLabel("+")
        plus_label.setProperty("class", "PlaceholderPlus")
        plus_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(plus_label)
        
        self.text_label = QLabel(label_text)
        self.text_label.setProperty("class", "PlaceholderText")
        self.text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.text_label)
        
        # Click handling (overlay or events)
        self.callback = callback

    def set_text(self, text):
        self.text_label.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.callback()
