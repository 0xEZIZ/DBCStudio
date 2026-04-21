"""
ui/db_manager_view.py - Database Management Interface (Professional Edition)
DBC obýektlerini (Nodes, Attributes, EnvVars) card-style we modern görnüşde dolandyrýar.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QScrollArea, QFrame, QMessageBox, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.card_widgets import FlowLayout, NodeCard, AttributeCard, EnvVarCard, AddActionCard
from core.i18n import I18N


class ManagementSection(QWidget):
    """
    DBC obýektleriniň bir kategoriýasyny (meselem, Nodes) görkezýär.
    """
    def __init__(self, key, title, icon, add_callback, parent=None):
        super().__init__(parent)
        self.key = key
        self.title_text = title
        self.icon = icon
        self.add_callback = add_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # Title
        self.title_label = QLabel(f"{icon} {title}")
        self.title_label.setProperty("class", "SectionHeader")
        layout.addWidget(self.title_label)

        # Flow Layout Container
        self.container = QWidget()
        self.flow_layout = FlowLayout(self.container)
        self.flow_layout.setSpacing(20)
        layout.addWidget(self.container)
        
        # Add Initial Placeholder
        self.placeholder = AddActionCard(I18N.t("manage_add_new").format(type=title), add_callback)
        self.flow_layout.addWidget(self.placeholder)

    def clear_cards(self):
        """Kartoçkalary arassalaýar (placeholder-den başga)."""
        while self.flow_layout.count() > 1:
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def add_card(self, card_widget):
        """Täze kartoçka goşýar (placeholder-den öň)."""
        # Placeholder elmydama soňunda bolmaly
        self.flow_layout.removeItem(self.flow_layout.itemAt(self.flow_layout.count() - 1))
        self.flow_layout.addWidget(card_widget)
        self.flow_layout.addWidget(self.placeholder)

    def retranslate_ui(self):
        """Update strings."""
        translated_title = I18N.t(self.key)
        self.title_label.setText(f"{self.icon} {translated_title}")
        self.placeholder.set_text(I18N.t("manage_add_new").format(type=translated_title))


class DBManagerView(QWidget):
    """
    Database dolandyryş paneli.
    """
    # Signals for logic layer
    node_added = pyqtSignal()
    node_edited = pyqtSignal(object)
    node_deleted = pyqtSignal(object)
    
    attr_added = pyqtSignal()
    attr_edited = pyqtSignal(object)
    attr_deleted = pyqtSignal(object)
    
    env_added = pyqtSignal()
    env_edited = pyqtSignal(object)
    env_deleted = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tab Widget for better organization
        self.tabs = QTabWidget()
        self.tabs.setObjectName("ManagerTabs")
        
        # 1. Nodes Section
        self.nodes_section = ManagementSection("manage_nodes", "Nodes (ECUs)", "🖥️", lambda: self.node_added.emit())
        self.tabs.addTab(self._wrap_in_scroll(self.nodes_section), I18N.t("db_explorer_nodes"))
        
        # 2. Attributes Section
        self.attrs_section = ManagementSection("manage_attrs", "Attribute Definitions", "⚙️", lambda: self.attr_added.emit())
        self.tabs.addTab(self._wrap_in_scroll(self.attrs_section), I18N.t("db_explorer_attrs"))
        
        # 3. Environment Variables Section
        self.envs_section = ManagementSection("manage_envs", "Environment Variables", "🌍", lambda: self.env_added.emit())
        self.tabs.addTab(self._wrap_in_scroll(self.envs_section), "Env Vars")
        
        layout.addWidget(self.tabs)

    def _wrap_in_scroll(self, widget):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(widget)
        scroll.setStyleSheet("background: transparent;")
        return scroll

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.nodes_section.retranslate_ui()
        self.attrs_section.retranslate_ui()
        self.envs_section.retranslate_ui()
        
        self.tabs.setTabText(0, I18N.t("db_explorer_nodes"))
        self.tabs.setTabText(1, I18N.t("db_explorer_attrs"))
        self.tabs.setTabText(2, "Env Vars") # Short enough for tab

    def refresh(self, database):
        """Database maglumatlary bilen ähli bölümleri täzeleýär."""
        if not database:
            return

        # Nodes
        self.nodes_section.clear_cards()
        for node in database.nodes:
            card = NodeCard(node, self.node_edited.emit, self.node_deleted.emit)
            self.nodes_section.add_card(card)

        # Attributes
        self.attrs_section.clear_cards()
        for adef in database.attribute_definitions:
            card = AttributeCard(adef, self.attr_edited.emit, self.attr_deleted.emit)
            self.attrs_section.add_card(card)

        # Environment Variables
        self.envs_section.clear_cards()
        for ev in database.environment_variables:
            card = EnvVarCard(ev, self.env_edited.emit, self.env_deleted.emit)
            self.envs_section.add_card(card)
