"""
main_window.py - Main Application Window
Ähli panel-leri birleşdirýär: Data Table, Bit Editor, Graph, Signal Editor, DBC Preview.
Project save/load, export, AI features goldawy bar.
"""

import json
import os
import re
from collections import defaultdict

from PyQt5.QtWidgets import (
    QMainWindow, QDockWidget, QAction, QFileDialog, QMessageBox,
    QToolBar, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QInputDialog, QSplitter, QStatusBar, QApplication, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog,
    QDialogButtonBox, QTextEdit, QStackedWidget, QFrame, QTabWidget,
    QComboBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon, QKeySequence

from models import Signal, Message, DBCDatabase
from parser import DBCParser, print_database_summary
from generator import DBCGenerator
from analyzer import CANDumpParser, CANAnalyzer, CANFrame
from encoder import CANEncoder
from ai_module import SmartSignalDetector, AISignalSuggester, DifferentialAnalyzer, print_candidates
from async_loader import FileLoaderWorker, AsyncFileLoader
from i18n import I18N

from ui.theme import get_stylesheet, COLORS_LIGHT, COLORS_DARK
from ui.bit_editor import BitEditorPanel
from ui.graph_panel import GraphPanel
from ui.data_table import CANDataTable, SignalEditorPanel, DBCPreviewPanel, DatabaseExplorerPanel
from ui.db_manager_view import DBManagerView
from ui.manager_dialogs import NodeEditorDialog, AttributeDefinitionDialog, EnvVarEditorDialog
from ui.comparison_dialog import LogComparisonDialog
from ui.learning_center import DBCLearningCenter
from ui.smart_assistant_panel import SmartAssistantPanel
from ui.video_panel import VideoPlaybackPanel
from ui.log_console import LogConsole
from ui.hardware_dialog import HardwareSetupDialog
from ui.re_scout_panel import REScoutPanel
from hardware.ixxat_interface import IxxatInterface
from hardware.can_worker import CANReceiverWorker
from hardware.loggers import DualLogger


class NavButton(QPushButton):
    """Side navigation bar üçin ýöriteleşdirilen düwme."""
    def __init__(self, icon_text, label_text, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(64)
        self.setFixedHeight(64)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(2)

        icon_label = QLabel(icon_text)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet("font-size: 20px; background: transparent;")
        layout.addWidget(icon_label)

        text_label = QLabel(label_text)
        text_label.setObjectName("NavLabel")
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("font-size: 10px; font-weight: bold; background: transparent;")
        layout.addWidget(text_label)

    def set_active(self, active):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class SideNavBar(QFrame):
    """Çep tarapdaky workspace switcher bar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SideNav")
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 20, 0, 0)
        self.layout.setSpacing(10)
        self.layout.setAlignment(Qt.AlignTop)

        self.buttons = []

    def add_tab(self, icon, label, index):
        btn = NavButton(icon, label, index)
        self.layout.addWidget(btn)
        self.buttons.append(btn)
        return btn

    def set_active_tab(self, index):
        for btn in self.buttons:
            btn.set_active(btn.index == index)


class WorkspaceCard(QFrame):
    """Widgetleri card-style envelope-e salýar."""
    def __init__(self, title, widget, parent=None):
        super().__init__(parent)
        self.setObjectName("WorkspaceCard")
        self.setProperty("class", "Card")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setObjectName("CardHeader")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(16, 12, 16, 12)
        
        title_label = QLabel(title)
        title_label.setProperty("subheading", True)
        h_layout.addWidget(title_label)
        h_layout.addStretch()
        
        layout.addWidget(header)
        layout.addWidget(widget)


class MainWindow(QMainWindow):
    """
    Advanced CAN Bus Analyzer - Main Window.
    Ähli funksiýalary birleşdirýän esasy penjiräniň klasy.
    """

    APP_NAME = "CAN Bus Analyzer & DBC Generator"
    APP_VERSION = "3.0 Professional"

    def __init__(self, dark_mode=False):
        super().__init__()
        self.dark_mode = dark_mode
        self.colors = COLORS_DARK if dark_mode else COLORS_LIGHT

        # Data state
        self.database = DBCDatabase()
        self.can_frames = []  # [(timestamp, can_id, data), ...]
        self.frames_by_id = defaultdict(list)  # can_id -> [data, ...]
        self.current_can_id = -1
        self.defined_signals = {}  # can_id -> [Signal, ...]
        self.project_file = None
        self.ai_suggester = AISignalSuggester()
        self.encoder = CANEncoder()
        self.async_loader = AsyncFileLoader(self)
        
        # Hardware state
        self.can_worker = None
        self.active_interface = None

        self._setup_window()
        self._create_statusbar()
        self._create_panels()
        self._create_db_explorer() 
        self._setup_db_manager() # Add this
        self._create_menus()
        self._create_toolbar()
        self._connect_signals()
        self._connect_async_loader()
        self._apply_theme()
        
        # Initial retranslation
        I18N.language_changed.connect(self._retranslate_ui)
        self._retranslate_ui()

    # ── Data Sync Helper ──

    def _sync_frames_by_id(self):
        """can_frames-dan frames_by_id-ny sync edýär (single source of truth)."""
        self.frames_by_id.clear()
        for ts, cid, data in self.can_frames:
            self.frames_by_id[cid].append(data)

    # ── Setup ──

    def _setup_window(self):
        """Penjiräniň esasy sazlamalaryny edýär."""
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setMinimumSize(1280, 800)
        self.resize(1600, 950)
        
        # Set Application Icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            # Taskbar icon fix for Windows (AppUserModelID)
            try:
                import ctypes
                myappid = 'antigravity.candbc.tool.3'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

    def _create_panels(self):
        """Ähli panel-leri döredýär we Workspace-lere ýerleşdirýär."""
        # 1. Workspace Stack (Center)
        self.workspace_stack = QStackedWidget()
        self.workspace_stack.setObjectName("WorkspaceBody")

        # ── Workspace 1: Analyzer (📡 Analyze) ──
        analyzer_widget = QWidget()
        analyzer_layout = QVBoxLayout(analyzer_widget)
        analyzer_layout.setContentsMargins(0, 0, 0, 0)
        
        analyzer_splitter = QSplitter(Qt.Vertical)
        
        # Top half: Video & Table
        top_analyzer_box = QWidget()
        top_analyzer_layout = QHBoxLayout(top_analyzer_box)
        top_analyzer_layout.setContentsMargins(0, 0, 0, 0)
        
        inner_splitter = QSplitter(Qt.Horizontal)
        
        self.video_panel = VideoPlaybackPanel()
        self.video_panel.position_changed.connect(self._on_video_pos_changed)
        inner_splitter.addWidget(WorkspaceCard("Video Sync", self.video_panel))
        
        self.data_table = CANDataTable()
        inner_splitter.addWidget(WorkspaceCard("CAN Bus Traffic", self.data_table))
        
        inner_splitter.setSizes([400, 800])
        top_analyzer_layout.addWidget(inner_splitter)
        
        analyzer_splitter.addWidget(top_analyzer_box)
        
        # Bottom half: Graph
        self.graph_panel = GraphPanel(dark_mode=self.dark_mode)
        analyzer_splitter.addWidget(WorkspaceCard("Signal Graph", self.graph_panel))
        
        analyzer_splitter.setSizes([500, 300])
        
        # 🔗 System Console (Bottom)
        self.log_console = LogConsole()
        analyzer_splitter.addWidget(WorkspaceCard("System Logs & Diagnostic", self.log_console))
        
        analyzer_layout.addWidget(analyzer_splitter)

        # 🛡️ RE Scout (Reverse Engineering Wizard)
        self.diff_analyzer = DifferentialAnalyzer()
        self.re_scout = REScoutPanel()
        self.re_scout_dock = QDockWidget("🛡️ RE Scout - Signal Discovery", self)
        self.re_scout_dock.setWidget(self.re_scout)
        self.addDockWidget(Qt.RightDockWidgetArea, self.re_scout_dock)
        self.re_scout_dock.hide()

        # ── Workspace 2: Designer (🎨 Design) ──
        designer_widget = QWidget()
        designer_layout = QVBoxLayout(designer_widget)
        designer_layout.setContentsMargins(0, 0, 0, 0)

        design_splitter = QSplitter(Qt.Horizontal)
        
        # Left side: Bit Editor
        self.bit_editor = BitEditorPanel(dark_mode=self.dark_mode)
        design_splitter.addWidget(WorkspaceCard("Bit Layout Editor", self.bit_editor))
        
        # Right side: Signal Editor & List (Stacked)
        right_design_box = QWidget()
        right_design_layout = QVBoxLayout(right_design_box)
        right_design_layout.setContentsMargins(0, 0, 0, 0)
        
        self.signal_editor = SignalEditorPanel()
        self.signal_list = self._create_signal_list()
        
        sig_tabs = QTabWidget()
        sig_tabs.addTab(self.signal_editor, "Editor")
        sig_tabs.addTab(self.signal_list, "Defined Signals")
        
        right_design_layout.addWidget(WorkspaceCard("Signal Properties", sig_tabs))
        design_splitter.addWidget(right_design_box)
        
        design_splitter.setSizes([800, 400])
        designer_layout.addWidget(design_splitter)

        # ── Workspace 3: Preview (📄 Preview) ──
        self.dbc_preview = DBCPreviewPanel()
        preview_card = WorkspaceCard("DBC File Preview", self.dbc_preview)

        # Add to stack
        self.workspace_stack.addWidget(analyzer_widget)
        self.workspace_stack.addWidget(designer_widget)
        self.workspace_stack.addWidget(preview_card)

        # ── Workspace 4: Explorer (📂 Database) ──
        self.db_explorer = DatabaseExplorerPanel()
        explorer_card = WorkspaceCard("Database Explorer", self.db_explorer)
        self.workspace_stack.addWidget(explorer_card)

        # ── Workspace 5: Management (🛠️ Manage) ──
        self.db_manager = DBManagerView()
        manager_card = WorkspaceCard("DBC Database Management", self.db_manager)
        self.workspace_stack.addWidget(manager_card)

        # ── Workspace 6: Guide (📚 Help) ──
        self.learning_center = DBCLearningCenter()
        guide_card = WorkspaceCard("DBC Professional Guide", self.learning_center)
        self.workspace_stack.addWidget(guide_card)

        # ── Workspace 7: Smart AI (🚀 Smart Assistant) ──
        self.assistant_panel = SmartAssistantPanel()
        assistant_card = WorkspaceCard("Smart AI Reverse Assistant", self.assistant_panel)
        self.workspace_stack.addWidget(assistant_card)

        # 2. Side Navigation Bar (Left)
        self.sidebar = SideNavBar()
        btn_analyze = self.sidebar.add_tab("📡", "Analyze", 0)
        btn_design = self.sidebar.add_tab("🎨", "Design", 1)
        btn_preview = self.sidebar.add_tab("📄", "Preview", 2)
        btn_explorer = self.sidebar.add_tab("📂", "DBC Tree", 3)
        btn_manage = self.sidebar.add_tab("🛠️", "Manage", 4)
        btn_guide = self.sidebar.add_tab("📚", "Guide", 5)
        btn_smart = self.sidebar.add_tab("🚀", "Assistant", 6)

        btn_analyze.clicked.connect(lambda: self._switch_workspace(0))
        btn_design.clicked.connect(lambda: self._switch_workspace(1))
        btn_preview.clicked.connect(lambda: self._switch_workspace(2))
        btn_explorer.clicked.connect(lambda: self._switch_workspace(3))
        btn_manage.clicked.connect(lambda: self._switch_workspace(4))
        btn_guide.clicked.connect(lambda: self._switch_workspace(5))
        btn_smart.clicked.connect(lambda: self._switch_workspace(6))

        # 3. Final Layout
        main_container = QWidget()
        main_container_layout = QHBoxLayout(main_container)
        main_container_layout.setContentsMargins(0, 0, 0, 0)
        main_container_layout.setSpacing(0)
        
        main_container_layout.addWidget(self.sidebar)
        main_container_layout.addWidget(self.workspace_stack)
        
        self.setCentralWidget(main_container)
        self._switch_workspace(0)  # Default mode
        
        # Save button references for retranslation
        self.sidebar_buttons = {
            "analyze": btn_analyze,
            "design": btn_design,
            "preview": btn_preview,
            "explorer": btn_explorer,
            "manage": btn_manage,
            "guide": btn_guide,
            "smart": btn_smart
        }

    def _switch_workspace(self, index):
        """Workspace çalyşýar."""
        self.workspace_stack.setCurrentIndex(index)
        self.sidebar.set_active_tab(index)
        
        # Workspace-e görä status bar ýada beýleki zatlar güncellenip biler
        mode_keys = ["mode_analysis", "mode_design", "mode_preview", "mode_explorer", "mode_manage", "mode_guide", "mode_assistant"]
        self._status(I18N.t("status_switched").format(mode=I18N.t(mode_keys[index])))
        
        # Refresh management view if switched to it
        if index == 4:
            self.db_manager.refresh(self.database)

    def _create_signal_list(self) -> QWidget:
        """Defined signals list widget döredýär."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel(I18N.t("sig_defined"))
        title.setObjectName("SignalListTitle")
        title.setProperty("subheading", True)
        layout.addWidget(title)

        self.signal_table = QTableWidget()
        self.signal_table.setColumnCount(6)
        self.signal_table.setHorizontalHeaderLabels([
            I18N.t("col_msg"), I18N.t("col_sig"), I18N.t("col_bits"), I18N.t("sig_scale"), I18N.t("sig_unit"), ""
        ])
        header = self.signal_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Fixed)
        header.setSectionResizeMode(4, QHeaderView.Fixed)
        header.setSectionResizeMode(5, QHeaderView.Fixed)
        self.signal_table.setColumnWidth(2, 70)
        self.signal_table.setColumnWidth(3, 60)
        self.signal_table.setColumnWidth(4, 60)
        self.signal_table.setColumnWidth(5, 50)
        self.signal_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.signal_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.signal_table.verticalHeader().setVisible(False)
        self.signal_table.currentCellChanged.connect(self._on_signal_list_selected)
        layout.addWidget(self.signal_table)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_remove_signal = QPushButton(I18N.t("sig_remove"))
        self.btn_remove_signal.clicked.connect(self._remove_selected_signal)
        btn_layout.addWidget(self.btn_remove_signal)

        self.btn_graph_signal = QPushButton(I18N.t("sig_show_graph"))
        self.btn_graph_signal.clicked.connect(self._graph_selected_signal)
        btn_layout.addWidget(self.btn_graph_signal)
        layout.addLayout(btn_layout)

        return widget

    def _create_menus(self):
        """Menu bar döredýär."""
        menubar = self.menuBar()

        # File menu
        self.file_menu = menubar.addMenu(I18N.t("menu_file"))

        self.act_open_dbc = QAction(I18N.t("menu_open_dbc"), self)
        self.act_open_dbc.setShortcut(QKeySequence("Ctrl+O"))
        self.act_open_dbc.triggered.connect(self._open_dbc)
        self.file_menu.addAction(self.act_open_dbc)

        self.act_load_log = QAction(I18N.t("menu_load_log"), self)
        self.act_load_log.setShortcut("Ctrl+L")
        self.act_load_log.triggered.connect(self._load_can_log)
        self.file_menu.addAction(self.act_load_log)
        
        self.act_load_video = QAction(I18N.t("menu_load_video"), self)
        self.act_load_video.setShortcut("Ctrl+M")
        self.act_load_video.triggered.connect(self.video_panel._on_load_clicked)
        self.file_menu.addAction(self.act_load_video)

        self.file_menu.addSeparator()

        self.act_save_project = QAction(I18N.t("menu_save_project"), self)
        self.act_save_project.setShortcut(QKeySequence("Ctrl+S"))
        self.act_save_project.triggered.connect(self._save_project)
        self.file_menu.addAction(self.act_save_project)

        self.act_load_project = QAction(I18N.t("menu_load_project"), self)
        self.act_load_project.setShortcut(QKeySequence("Ctrl+Shift+O"))
        self.act_load_project.triggered.connect(self._load_project)
        self.file_menu.addAction(self.act_load_project)

        self.file_menu.addSeparator()

        # Export submenu
        self.export_menu = self.file_menu.addMenu(I18N.t("menu_export"))

        self.act_export_dbc = QAction(I18N.t("menu_export") + " DBC...", self)
        self.act_export_dbc.triggered.connect(self._export_dbc)
        self.export_menu.addAction(self.act_export_dbc)

        self.act_export_json = QAction(I18N.t("menu_export") + " JSON...", self)
        self.act_export_json.triggered.connect(self._export_json)
        self.export_menu.addAction(self.act_export_json)

        self.act_export_csv = QAction(I18N.t("menu_export") + " CSV...", self)
        self.act_export_csv.triggered.connect(self._export_csv)
        self.export_menu.addAction(self.act_export_csv)

        self.file_menu.addSeparator()

        self.act_exit = QAction(I18N.t("menu_exit"), self)
        self.act_exit.setShortcut(QKeySequence("Alt+F4"))
        self.act_exit.triggered.connect(self.close)
        self.file_menu.addAction(self.act_exit)

        # AI menu
        self.ai_menu = menubar.addMenu(I18N.t("menu_ai"))

        self.act_detect = QAction(I18N.t("menu_detect"), self)
        self.act_detect.setShortcut(QKeySequence("Ctrl+D"))
        self.act_detect.triggered.connect(self._ai_detect_signals)
        self.ai_menu.addAction(self.act_detect)

        self.act_suggest = QAction(I18N.t("menu_suggest"), self)
        self.act_suggest.setShortcut(QKeySequence("Ctrl+F"))
        self.act_suggest.triggered.connect(self._ai_find_signal)
        self.ai_menu.addAction(self.act_suggest)

        self.act_auto_dbc = QAction(I18N.t("menu_auto_dbc"), self)
        self.act_auto_dbc.triggered.connect(self._ai_auto_dbc)
        self.ai_menu.addAction(self.act_auto_dbc)
        
        self.ai_menu.addSeparator()

        self.act_smart = QAction("🚀 " + I18N.t("nav_assistant"), self)
        self.act_smart.triggered.connect(lambda: self._switch_workspace(6))
        self.ai_menu.addAction(self.act_smart)

        self.ai_menu.addSeparator()

        self.act_encode = QAction(I18N.t("menu_encode"), self)
        self.act_encode.setShortcut(QKeySequence("Ctrl+E"))
        self.act_encode.triggered.connect(self._encode_signal_values)
        self.ai_menu.addAction(self.act_encode)

        self.ai_menu.addSeparator()

        self.act_compare = QAction(I18N.t("menu_compare"), self)
        self.act_compare.triggered.connect(self._compare_logs)
        self.ai_menu.addAction(self.act_compare)

        # Hardware menu
        self.hw_menu = menubar.addMenu(I18N.t("menu_hw"))
        self.act_hw_connect = QAction("🔌 " + I18N.t("menu_connect"), self)
        self.act_hw_connect.triggered.connect(self._on_hw_connect_clicked)
        self.hw_menu.addAction(self.act_hw_connect)
        
        self.act_hw_stop = QAction("🛑 " + I18N.t("menu_stop"), self)
        self.act_hw_stop.setEnabled(False)
        self.act_hw_stop.triggered.connect(self._on_hw_stop_clicked)
        self.hw_menu.addAction(self.act_hw_stop)

        # View menu
        self.view_menu = menubar.addMenu(I18N.t("menu_view"))
        self.act_dark = QAction("🌓 " + I18N.t("menu_dark"), self)
        self.act_dark.setShortcut(QKeySequence("Ctrl+T"))
        self.act_dark.triggered.connect(self._toggle_theme)
        self.view_menu.addAction(self.act_dark)

        # Help menu
        self.help_menu = menubar.addMenu(I18N.t("menu_help"))
        
        self.act_help_guide = QAction(I18N.t("nav_guide"), self)
        self.act_help_guide.triggered.connect(lambda: self._switch_workspace(5))
        self.help_menu.addAction(self.act_help_guide)
        
        self.act_about = QAction(I18N.t("menu_about"), self)
        self.act_about.triggered.connect(self._show_about)
        self.help_menu.addAction(self.act_about)

    def _create_toolbar(self):
        """Toolbar döredýär."""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(20, 20))
        self.toolbar.addSeparator()

        self.act_live_btn = QAction("🔌 Live", self)
        self.act_live_btn.setToolTip("Connect to IXXAT Hardware")
        self.act_live_btn.triggered.connect(self._on_hw_connect_clicked)
        self.toolbar.addAction(self.act_live_btn)

        self.toolbar.addSeparator()

        ai_suggest_action = QAction("🚀 Explore", self)
        ai_suggest_action.setToolTip("AI Signal Exploration")
        ai_suggest_action.triggered.connect(self._on_ai_suggest_clicked)
        self.toolbar.addAction(ai_suggest_action)

        self.act_re_scout = QAction("🛡️ Scout", self)
        self.act_re_scout.setToolTip(I18N.t("scout_info"))
        self.act_re_scout.triggered.connect(lambda: self.re_scout_dock.show())
        self.toolbar.addAction(self.act_re_scout)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)

        # Language Toggle (Next to Dark/Light)
        lang_label = QLabel("🌐")
        lang_label.setStyleSheet("padding-left: 10px;")
        self.toolbar.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["TKM", "RUS", "ENG"])
        self.lang_combo.setFixedWidth(80)
        self.lang_combo.currentTextChanged.connect(I18N.set_language)
        self.toolbar.addWidget(self.lang_combo)

        self.addToolBar(Qt.TopToolBarArea, self.toolbar)

        # Buttons as actions
        btn_open_dbc = QAction("Open DBC", self)
        btn_open_dbc.triggered.connect(self._open_dbc)
        self.toolbar.addAction(btn_open_dbc)

        btn_load_log = QAction("Load Log", self)
        btn_load_log.triggered.connect(self._load_can_log)
        self.toolbar.addAction(btn_load_log)

        self.toolbar.addSeparator()

        btn_detect = QAction("AI Detect", self)
        btn_detect.triggered.connect(self._ai_detect_signals)
        self.toolbar.addAction(btn_detect)

        btn_gen_dbc = QAction("Generate DBC", self)
        btn_gen_dbc.triggered.connect(self._export_dbc)
        self.toolbar.addAction(btn_gen_dbc)

        self.toolbar.addSeparator()

        btn_theme = QAction(I18N.t("menu_dark"), self)
        btn_theme.triggered.connect(self._toggle_theme)
        self.toolbar.addAction(btn_theme)

    def _create_statusbar(self):
        """Status bar döredýär."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel(self._get_status_text())
        self.status_bar.addWidget(self.status_label)

    def _get_status_text(self):
        return f"  {self.APP_NAME} v{self.APP_VERSION} | {I18N.t('mode_ready')}"

    def _connect_signals(self):
        """Panel-leriň arasyndaky signal-lary birleşdirýär."""
        # Data table -> Bit editor (frame saýlananda)
        self.data_table.frame_selected.connect(self._on_frame_selected)
        self.data_table.id_filter_changed.connect(self._on_id_filter_changed)

        # Bit editor -> Signal editor (selection üýtgände)
        self.bit_editor.selection_changed.connect(
            self.signal_editor.set_from_selection
        )

        # Signal editor -> add signal
        self.signal_editor.signal_updated.connect(self._on_signal_added)

        # RE Scout interactions
        self.data_table.frame_selected.connect(self._sync_scout_focus)
        self.re_scout.analyze_requested.connect(self._on_scout_analyze_requested)
        self.re_scout.signal_added.connect(self._on_scout_signal_added)

    def _connect_async_loader(self):
        """Async loader signal-laryny birleşdirýär."""
        self.async_loader.load_finished.connect(self._on_async_load_finished)
        self.async_loader.load_error.connect(self._on_async_load_error)
        self.async_loader.load_progress.connect(self._on_async_progress)
        self.async_loader.load_status.connect(
            lambda s: self._status(s)
        )

    def _on_async_load_finished(self, result):
        """Async ýüklenme gutaranda."""
        if isinstance(result, DBCDatabase):
            self.database = result
            self._status(f"DBC loaded: {len(self.database.messages)} messages, "
                         f"{len(self.database.nodes)} nodes")
            self._update_dbc_preview()
            for msg in self.database.messages:
                if msg.signals:
                    self.defined_signals[msg.message_id] = msg.signals[:]
            self._refresh_signal_list()
            self.db_explorer.populate(self.database)
            self.data_table.update_from_database(self.database)
            self.db_manager.refresh(self.database) # Add this
            self._switch_workspace(3)  # Auto switch to Explorer
        elif isinstance(result, list):
            self.can_frames = result
            self._sync_frames_by_id()
            self.data_table.load_frames(result)
            self._status(f"Log loaded: {len(result)} frames, "
                         f"{len(self.frames_by_id)} unique IDs")
        elif isinstance(result, dict):
            # Project file
            self._apply_project_data(result)
        self.setEnabled(True)

    def _on_async_load_error(self, error_msg: str):
        """Async ýüklenme hata berende."""
        self.setEnabled(True)
        QMessageBox.critical(self, "Error", f"Loading failed:\n{error_msg}")

    def _on_async_progress(self, value: int):
        """Async progress bar update."""
        self._status(f"Loading... {value}%")

    def _apply_theme(self):
        """Temany ulanýar."""
        self.setStyleSheet(get_stylesheet(self.dark_mode))
        self.learning_center.set_dark_mode(self.dark_mode)
        # Refresh assistant if needed
        if hasattr(self, 'assistant_panel'):
            self.assistant_panel.setProperty("class", "WorkspaceBody")
            self.assistant_panel.style().unpolish(self.assistant_panel)
            self.assistant_panel.style().polish(self.assistant_panel)

    def _create_db_explorer(self):
        """Database explorer item selection handling."""
        self.db_explorer.item_selected.connect(self._on_explorer_item_selected)

    def _setup_db_manager(self):
        """Database manager signal-laryny birleşdirýär."""
        self.db_manager.node_added.connect(self._on_add_node)
        self.db_manager.node_edited.connect(self._on_edit_node)
        self.db_manager.node_deleted.connect(self._on_delete_node)
        
        self.db_manager.attr_added.connect(self._on_add_attr)
        self.db_manager.attr_edited.connect(self._on_edit_attr)
        self.db_manager.attr_deleted.connect(self._on_delete_attr)
        
        self.db_manager.env_added.connect(self._on_add_env)
        self.db_manager.env_edited.connect(self._on_edit_env)
        self.db_manager.env_deleted.connect(self._on_delete_env)

    def _on_video_pos_changed(self, pos_ms):
        """Video süýşende CAN logyny we grafikleri sync edýär."""
        if not self.can_frames:
            return
            
        # Get synchronized timestamp (s)
        ts = self.video_panel.get_sync_timestamp(pos_ms)
        
        # Update Table
        self.data_table.scroll_to_timestamp(ts)
        
        # Update Graph
        self.graph_panel.set_playback_position(ts)

    def _on_hw_connect_clicked(self):
        """Hardware birikdirme dialogyny açýar."""
        dialog = HardwareSetupDialog(self)
        if dialog.exec_():
            settings = dialog.get_settings()
            self._start_live_capture(settings)

    def _start_live_capture(self, settings):
        """CAN aragatnaşygyny başlaýar."""
        try:
            # 1. Interface-i döret
            if settings["interface"] == "ixxat":
                self.active_interface = IxxatInterface()
            
            # 2. Connect
            if not self.active_interface.connect(bitrate=settings["bitrate"], channel=settings["channel"]):
                QMessageBox.critical(self, "Connection Error", "IXXAT adapterine birigip bolmady. Driver-y we baglanyşygy barlaň.")
                return

            # 3. Logger (Auto-save)
            logger = None
            if settings["autosave"]:
                # Save to current project folder or default
                logger = DualLogger("live_capture")

            # 4. Worker başla
            self.can_worker = CANReceiverWorker(self.active_interface, logger)
            self.can_worker.frame_received.connect(self._on_live_data_received)
            self.can_worker.error_occurred.connect(self._on_hw_error)
            self.can_worker.start()

            # UI Update
            self.act_hw_stop.setEnabled(True)
            self.act_live_btn.setText("🛑 " + I18N.t("menu_stop"))
            self.act_live_btn.setStyleSheet("color: #ff4d4d; font-weight: bold;")
            self._status("📡 " + I18N.t("scout_live"))
            
        except Exception as e:
            QMessageBox.critical(self, "Hardware Error", f"Nätanyş ýalňyşlyk: {e}")

    def _on_hw_stop_clicked(self):
        """Capture-y duruzýar."""
        if self.can_worker:
            self.can_worker.stop()
            self.can_worker = None
        
        self.act_hw_stop.setEnabled(False)
        self.act_live_btn.setText("🔌 " + I18N.t("menu_connect"))
        self.act_live_btn.setStyleSheet("")
        self._status(I18N.t("ready"))

    def _on_live_data_received(self, frames):
        """Täze gelen batch maglumatlary UI-e goşýar."""
        if not frames:
            return
            
        # 1. Main Data Storage-e goş
        for f in frames:
            self.can_frames.append((f.timestamp, f.can_id, f.data))
        
        # 2. Sync by ID (Analysis üçin)
        self._sync_frames_by_id()
        
        # 3. Table Update (Batching)
        self.data_table.update_data(self.can_frames)
        
        # 4. Graph Update (Eger monitor edilýän bolsa)
        # Belli bir ID saýlanan bolsa, grafigi täzele
        if self.current_can_id != -1:
            self._update_graph()

        # 5. RE Scout Update
        for f in frames:
            self.re_scout.add_frame(f.can_id, f.data)

    def _on_hw_error(self, error_msg):
        QMessageBox.warning(self, "Hardware Error", f"Aragatnaşyk kesildi: {error_msg}")
        self._on_hw_stop_clicked()

    # ── Database Management Handlers ──

    def _on_add_node(self):
        dialog = NodeEditorDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            from models import Node
            data = dialog.get_data()
            self.database.nodes.append(Node(name=data['name'], comment=data['comment']))
            self.db_manager.refresh(self.database)
            self._status(f"Node '{data['name']}' added.")

    def _on_edit_node(self, node):
        dialog = NodeEditorDialog(node, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            node.name = data['name']
            node.comment = data['comment']
            self.db_manager.refresh(self.database)
            self._status(f"Node '{node.name}' updated.")

    def _on_delete_node(self, node):
        res = QMessageBox.warning(self, "Delete Node", f"Are you sure you want to delete node '{node.name}'?",
                                  QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.database.nodes.remove(node)
            self.db_manager.refresh(self.database)

    def _on_add_attr(self):
        dialog = AttributeDefinitionDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            from models import AttributeDefinition
            data = dialog.get_data()
            adef = AttributeDefinition(**data)
            self.database.attribute_definitions.append(adef)
            self.db_manager.refresh(self.database)

    def _on_edit_attr(self, adef):
        dialog = AttributeDefinitionDialog(adef, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            for k, v in data.items():
                setattr(adef, k, v)
            self.db_manager.refresh(self.database)

    def _on_delete_attr(self, adef):
        if QMessageBox.warning(self, "Delete", f"Delete attribute '{adef.name}'?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.database.attribute_definitions.remove(adef)
            self.db_manager.refresh(self.database)

    def _on_add_env(self):
        dialog = EnvVarEditorDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            from models import EnvironmentVariable
            data = dialog.get_data()
            ev = EnvironmentVariable(**data)
            self.database.environment_variables.append(ev)
            self.db_manager.refresh(self.database)

    def _on_edit_env(self, ev):
        dialog = EnvVarEditorDialog(ev, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            data = dialog.get_data()
            for k, v in data.items():
                setattr(ev, k, v)
            self.db_manager.refresh(self.database)

    def _on_delete_env(self, ev):
        if QMessageBox.warning(self, "Delete", f"Delete EnvVar '{ev.name}'?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.database.environment_variables.remove(ev)
            self.db_manager.refresh(self.database)

    def _on_explorer_item_selected(self, obj):
        """Explorer-de bir zat saýlananda degişli panel-e geçýär."""
        from models import Message, Signal, Node
        if isinstance(obj, Signal):
            # Find which message this signal belongs to
            for can_id, signals in self.defined_signals.items():
                if obj in signals:
                    self.current_can_id = can_id
                    self.signal_editor.set_from_signal(obj)
                    self._switch_workspace(1) # Go to Design mode
                    break
        elif isinstance(obj, Message):
            self.current_can_id = obj.message_id
            self._switch_workspace(1) # Go to Design mode
        elif isinstance(obj, Node):
            # TBD: Show Node details dialog?
            pass

    # ── File Operations ──

    def _open_dbc(self):
        """DBC faýly dialog bilen açýar."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Open DBC File", "",
            "DBC Files (*.dbc);;All Files (*)"
        )
        if filepath:
            self._open_dbc_file(filepath)

    def _open_dbc_file(self, filepath: str):
        """DBC faýly ýol boýunça açýar (async for large files)."""
        file_size = os.path.getsize(filepath)
        if file_size > 100_000:  # >100KB = async
            self._status(f"Loading {os.path.basename(filepath)}...")
            self.setEnabled(False)
            self.async_loader.load_file(filepath, FileLoaderWorker.LOAD_DBC)
        else:
            try:
                parser = DBCParser()
                self.database = parser.parse_file(filepath)
                self._status(f"DBC loaded: {os.path.basename(filepath)} "
                             f"({len(self.database.messages)} messages, "
                             f"{len(self.database.nodes)} nodes)")
                self._update_dbc_preview()
                for msg in self.database.messages:
                    if msg.signals:
                        self.defined_signals[msg.message_id] = msg.signals[:]
                self._refresh_signal_list()
                self.db_explorer.populate(self.database)
                self.data_table.update_from_database(self.database)
                self.db_manager.refresh(self.database) # Add this
                self._switch_workspace(3)  # Auto switch to Explorer
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load DBC:\n{e}")

    def _load_can_log(self):
        """CAN log faýly dialog bilen ýükleýär."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load CAN Log", "",
            "CAN Log Files (*.txt *.csv *.log *.asc);;All Files (*)"
        )
        if filepath:
            self._load_can_log_file(filepath)

    def _load_can_log_file(self, filepath: str):
        """CAN log faýly ýol boýunça ýükleýär (async for large files)."""
        file_size = os.path.getsize(filepath)
        if file_size > 500_000:  # >500KB = async
            self._status(f"Loading {os.path.basename(filepath)}...")
            self.setEnabled(False)
            self.async_loader.load_file(filepath, FileLoaderWorker.LOAD_CAN_LOG)
        else:
            try:
                dump_parser = CANDumpParser()
                frames = dump_parser.parse_file(filepath)

                if not frames:
                    QMessageBox.warning(self, "Warning", "No CAN frames found in file.")
                    return

                self.can_frames = [
                    (f.timestamp, f.can_id, f.data) for f in frames
                ]
                self._sync_frames_by_id()
                self.data_table.load_frames(self.can_frames)

                self._status(f"Log loaded: {os.path.basename(filepath)} "
                             f"({len(frames)} frames, "
                             f"{len(self.frames_by_id)} unique IDs)")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load log:\n{e}")

    def _save_project(self):
        """Proýekti JSON faýla saklaýar."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Project", "",
            "Project Files (*.canproj);;JSON Files (*.json)"
        )
        if not filepath:
            return

        project = {
            "version": self.APP_VERSION,
            "database": self.database.to_dict() if self.database.messages else None,
            "defined_signals": {},
            "current_can_id": self.current_can_id
        }

        for can_id, signals in self.defined_signals.items():
            project["defined_signals"][str(can_id)] = [
                s.to_dict() for s in signals
            ]

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(project, f, indent=2, ensure_ascii=False)

        self.project_file = filepath
        self._status(f"Project saved: {os.path.basename(filepath)}")

    def _load_project(self):
        """Proýekti dialog bilen ýükleýär."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Load Project", "",
            "Project Files (*.canproj);;JSON Files (*.json)"
        )
        if filepath:
            self._load_project_file(filepath)

    def _load_project_file(self, filepath: str):
        """Proýekti ýol boýunça ýükleýär."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                project = json.load(f)
            self._apply_project_data(project)
            self.project_file = filepath
            self._status(f"Project loaded: {os.path.basename(filepath)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load project:\n{e}")

    def _apply_project_data(self, project: dict):
        """Project dict-den data-ny ulanýar."""
        if project.get("database"):
            self.database = DBCDatabase.from_dict(project["database"])

        self.defined_signals.clear()
        for id_str, sigs_data in project.get("defined_signals", {}).items():
            can_id = int(id_str)
            self.defined_signals[can_id] = [
                Signal.from_dict(s) for s in sigs_data
            ]

        self._refresh_signal_list()
        self._update_dbc_preview()

    # ── Export ──

    def _export_dbc(self):
        """DBC faýla eksport edýär."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export DBC", "",
            "DBC Files (*.dbc)"
        )
        if not filepath:
            return

        db = self._build_database()
        generator = DBCGenerator()
        generator.generate_to_file(db, filepath)
        self._status(f"DBC exported: {os.path.basename(filepath)}")

    def _export_json(self):
        """JSON faýla eksport edýär."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "",
            "JSON Files (*.json)"
        )
        if not filepath:
            return

        db = self._build_database()
        db.export_json(filepath, verbose=False)
        self._status(f"JSON exported: {os.path.basename(filepath)}")

    def _export_csv(self):
        """Signal-lary CSV faýla eksport edýär."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "",
            "CSV Files (*.csv)"
        )
        if not filepath:
            return

        import csv
        db = self._build_database()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Message_ID", "Message_Name", "Signal_Name",
                "Start_Bit", "Length", "Byte_Order", "Value_Type",
                "Scale", "Offset", "Min", "Max", "Unit"
            ])
            for msg in db.messages:
                for sig in msg.signals:
                    writer.writerow([
                        f"0x{msg.message_id:03X}", msg.name, sig.name,
                        sig.start_bit, sig.length, sig.byte_order,
                        sig.value_type, sig.scale, sig.offset,
                        sig.minimum, sig.maximum, sig.unit
                    ])

        self._status(f"CSV exported: {os.path.basename(filepath)}")

    # ── AI Tools ──

    def _ai_detect_signals(self):
        """AI bilen signal-lary awtomatiki tapýar."""
        if not self.frames_by_id:
            QMessageBox.information(
                self, "Info", "Please load a CAN log first."
            )
            return

        can_id = self.current_can_id
        if can_id < 0:
            # Ähli ID-ler üçin detect et
            total_found = 0
            for cid, data_list in self.frames_by_id.items():
                detector = SmartSignalDetector()
                candidates = detector.detect_signals(cid, data_list, 0.4)
                if candidates:
                    signals = [c.to_signal() for c in candidates]
                    self.defined_signals[cid] = signals
                    total_found += len(signals)

            self._refresh_signal_list()
            self._update_dbc_preview()
            self._status(f"AI Detection complete: {total_found} signals found")
        else:
            # Diňe saýlanan ID üçin
            data_list = self.frames_by_id.get(can_id, [])
            if not data_list:
                return

            detector = SmartSignalDetector()
            candidates = detector.detect_signals(can_id, data_list, 0.3)

            if candidates:
                signals = [c.to_signal() for c in candidates]
                self.defined_signals[can_id] = signals
                self._refresh_signal_list()
                self._update_dbc_preview()

                # Bit editor-a signal-lary görkez
                self.bit_editor.set_signals(signals)

                self._status(
                    f"AI Detection for 0x{can_id:03X}: "
                    f"{len(candidates)} signals found"
                )
            else:
                self._status(f"No signals detected for 0x{can_id:03X}")

    def _ai_find_signal(self):
        """AI bilen signal gözleýär (keyword boýunça)."""
        keyword, ok = QInputDialog.getText(
            self, "Find Signal",
            "Enter signal type (e.g., speed, rpm, temperature):"
        )
        if not ok or not keyword:
            return

        if not self.frames_by_id:
            QMessageBox.information(
                self, "Info", "Please load a CAN log first."
            )
            return

        # Ähli ID-lerde gözle
        all_candidates = []
        detector = SmartSignalDetector()
        for cid, data_list in self.frames_by_id.items():
            candidates = detector.detect_signals(cid, data_list, 0.2)
            all_candidates.extend(candidates)

        matches = self.ai_suggester.suggest_by_keyword(keyword, all_candidates)

        if matches:
            # Netijäni dialog-da görkez
            msg = f"Found {len(matches)} candidates for '{keyword}':\n\n"
            for i, c in enumerate(matches[:10], 1):
                msg += (
                    f"{i}. 0x{c.can_id:03X} bit {c.start_bit}|{c.length} "
                    f"- {c.suggested_name} "
                    f"(confidence: {c.confidence:.0%})\n"
                    f"   {c.reason}\n\n"
                )

            dialog = QDialog(self)
            dialog.setWindowTitle(f"AI Signal Search: '{keyword}'")
            dialog.setMinimumSize(600, 400)
            dlayout = QVBoxLayout(dialog)
            text = QTextEdit()
            text.setPlainText(msg)
            text.setReadOnly(True)
            text.setFont(QFont("Cascadia Code", 10))
            dlayout.addWidget(text)

            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dialog.accept)
            dlayout.addWidget(btn_box)

            dialog.exec_()
        else:
            QMessageBox.information(
                self, "AI Search",
                f"No signals matching '{keyword}' were found."
            )

    def _ai_auto_dbc(self):
        """AI bilen awtomatiki DBC döredýär."""
        if not self.frames_by_id:
            QMessageBox.information(
                self, "Info", "Please load a CAN log first."
            )
            return

        db = self.ai_suggester.auto_generate_dbc(
            dict(self.frames_by_id), min_confidence=0.4
        )

        if db.messages:
            self.database = db
            # Signal-lary defined_signals-a goş
            for msg in db.messages:
                self.defined_signals[msg.message_id] = msg.signals[:]

            self._refresh_signal_list()
            self._update_dbc_preview()

            total_signals = sum(len(m.signals) for m in db.messages)
            self._status(
                f"AI Auto-DBC: {len(db.messages)} messages, "
                f"{total_signals} signals generated"
            )
        else:
            self._status("AI could not detect any signals.")

    def _encode_signal_values(self):
        """Encode Signal Values dialog — fiziki bahalary CAN frame-a öwürýär."""
        if not self.defined_signals:
            QMessageBox.information(
                self, "Info",
                "Please define signals first (load DBC or add signals manually)."
            )
            return

        # Build list of all messages with signals
        db = self._build_database()
        if not db.messages:
            return

        # Select message
        msg_names = [f"0x{m.message_id:03X} {m.name}" for m in db.messages]
        selected, ok = QInputDialog.getItem(
            self, "Encode", "Select message:", msg_names, 0, False
        )
        if not ok:
            return

        idx = msg_names.index(selected)
        msg = db.messages[idx]

        # Input signal values
        signal_values = {}
        input_lines = []
        for sig in msg.signals:
            input_lines.append(f"{sig.name} (scale={sig.scale}, offset={sig.offset}, unit={sig.unit})")

        values_text, ok = QInputDialog.getMultiLineText(
            self, "Encode Signal Values",
            f"Enter values for {msg.name} (one per line: SignalName=Value):\n\n"
            + "\n".join(f"{s.name} = " for s in msg.signals),
            "\n".join(f"{s.name} = 0" for s in msg.signals)
        )
        if not ok:
            return

        # Parse input
        for line in values_text.strip().split("\n"):
            line = line.strip()
            if "=" not in line:
                continue
            parts = line.split("=", 1)
            sig_name = parts[0].strip()
            try:
                value = float(parts[1].strip())
                signal_values[sig_name] = value
            except ValueError:
                continue

        if not signal_values:
            QMessageBox.warning(self, "Warning", "No valid signal values entered.")
            return

        try:
            encoded = self.encoder.encode_message(msg, signal_values)
            hex_str = " ".join(f"{b:02X}" for b in encoded)

            # Verify by decoding back
            decoded = self.encoder.decode_message(msg, encoded)
            verify_lines = []
            for sig_name, phys_val in decoded.items():
                sig = msg.get_signal(sig_name)
                unit = sig.unit if sig else ""
                verify_lines.append(f"  {sig_name} = {phys_val:.4f} {unit}")

            result_text = (
                f"Message: {msg.name} (0x{msg.message_id:03X})\n"
                f"DLC: {msg.dlc}\n\n"
                f"Encoded CAN Frame:\n"
                f"  HEX: {hex_str}\n"
                f"  RAW: {list(encoded)}\n\n"
                f"Verification (decode back):\n"
                + "\n".join(verify_lines)
            )

            dialog = QDialog(self)
            dialog.setWindowTitle("Encode Result")
            dialog.setMinimumSize(500, 350)
            dlayout = QVBoxLayout(dialog)
            text = QTextEdit()
            text.setPlainText(result_text)
            text.setReadOnly(True)
            text.setFont(QFont("Cascadia Code", 11))
            dlayout.addWidget(text)
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dialog.accept)
            dlayout.addWidget(btn_box)
            dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "Encode Error", f"Failed to encode:\n{e}")

    def _compare_logs(self):
        """Iki CAN log-y deňeşdirýär."""
        filepath1, _ = QFileDialog.getOpenFileName(
            self, "Select First Log", "",
            "CAN Log Files (*.txt *.csv *.log);;All Files (*)"
        )
        if not filepath1:
            return

        filepath2, _ = QFileDialog.getOpenFileName(
            self, "Select Second Log", "",
            "CAN Log Files (*.txt *.csv *.log);;All Files (*)"
        )
        if not filepath2:
            return

        dump_parser = CANDumpParser()
        frames1 = dump_parser.parse_file(filepath1)
        frames2 = dump_parser.parse_file(filepath2)

        fbi1 = defaultdict(list)
        for f in frames1:
            fbi1[f.can_id].append(f.data)

        fbi2 = defaultdict(list)
        for f in frames2:
            fbi2[f.can_id].append(f.data)

        result = self.ai_suggester.compare_logs(dict(fbi1), dict(fbi2))

        # Netijäni dialog-da görkez
        msg = "Log Comparison Results:\n\n"
        msg += f"Only in Log 1: {[f'0x{x:03X}' for x in result['only_in_log1']]}\n"
        msg += f"Only in Log 2: {[f'0x{x:03X}' for x in result['only_in_log2']]}\n"
        msg += f"Common IDs: {len(result['common'])}\n"
        msg += f"IDs with differences: {len(result['differences'])}\n\n"

        for cid, diff in result["differences"].items():
            msg += f"0x{cid:03X}: count {diff['count_log1']} vs {diff['count_log2']}"
            if diff["changed_bytes"]:
                msg += f", changed bytes: {[d['byte'] for d in diff['changed_bytes']]}"
            msg += "\n"

        dialog = QDialog(self)
        dialog.setWindowTitle("Log Comparison")
        dialog.setMinimumSize(600, 400)
        dlayout = QVBoxLayout(dialog)
        text = QTextEdit()
        text.setPlainText(msg)
        text.setReadOnly(True)
        text.setFont(QFont("Cascadia Code", 10))
        dlayout.addWidget(text)
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
        btn_box.accepted.connect(dialog.accept)
        dlayout.addWidget(btn_box)
        dialog.exec_()

    # ── Event Handlers ──

    def _on_frame_selected(self, can_id: int, data: bytes):
        """Data table-da frame saýlananda."""
        self.current_can_id = can_id
        self.bit_editor.set_frame_data(data, f"0x{can_id:03X}")

        # Eger bu ID üçin signal bar bolsa görkez
        signals = self.defined_signals.get(can_id, [])
        self.bit_editor.set_signals(signals)

    def _on_id_filter_changed(self, can_id: int):
        """ID filter üýtgände."""
        self.current_can_id = can_id

    def _on_signal_added(self, props: dict):
        """Signal editor-dan täze signal goşulanda."""
        if self.current_can_id < 0:
            QMessageBox.information(
                self, "Info",
                "Please select a CAN message first."
            )
            return

        # Validate signal name (DBC identifiers must be C-compatible)
        name = props["name"]
        if not name or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', name):
            QMessageBox.warning(
                self, "Invalid Name",
                "Signal name must start with a letter or underscore "
                "and contain only letters, digits, and underscores.\n"
                f"Got: '{name}'"
            )
            return

        signal = Signal(
            name=name,
            start_bit=props["start_bit"],
            length=props["length"],
            byte_order=props["byte_order"],
            value_type=props["value_type"],
            scale=props["scale"],
            offset=props["offset"],
            minimum=props["minimum"],
            maximum=props["maximum"],
            unit=props["unit"],
            multiplex_indicator=props.get("multiplex_indicator", ""),
            value_table=props.get("value_table", {})
        )

        if self.current_can_id not in self.defined_signals:
            self.defined_signals[self.current_can_id] = []
        self.defined_signals[self.current_can_id].append(signal)

        # UI-ni täzele
        self.bit_editor.set_signals(
            self.defined_signals[self.current_can_id]
        )
        self._refresh_signal_list()
        self._update_dbc_preview()

        # Live value görkez
        self._update_live_value(signal)

        self._status(f"Signal '{signal.name}' added to 0x{self.current_can_id:03X}")

    def _on_signal_list_selected(self, row, col, prev_row, prev_col):
        """Signal list-de signal saýlananda."""
        if row < 0:
            return

        # Table-dan can_id we signal name-i al
        msg_item = self.signal_table.item(row, 0)
        sig_item = self.signal_table.item(row, 1)
        if not msg_item or not sig_item:
            return

        can_id_str = msg_item.text()
        can_id = int(can_id_str.replace("0x", ""), 16)
        sig_name = sig_item.text()

        # Signal-y tap we editor-a doldur
        signals = self.defined_signals.get(can_id, [])
        for sig in signals:
            if sig.name == sig_name:
                self.signal_editor.set_from_signal(sig)
                break

    def _remove_selected_signal(self):
        """Saýlanan signal-y aýyrýar."""
        row = self.signal_table.currentRow()
        if row < 0:
            return

        msg_item = self.signal_table.item(row, 0)
        sig_item = self.signal_table.item(row, 1)
        if not msg_item or not sig_item:
            return

        can_id = int(msg_item.text().replace("0x", ""), 16)
        sig_name = sig_item.text()

        if can_id in self.defined_signals:
            self.defined_signals[can_id] = [
                s for s in self.defined_signals[can_id]
                if s.name != sig_name
            ]
            if not self.defined_signals[can_id]:
                del self.defined_signals[can_id]

        self._refresh_signal_list()
        self._update_dbc_preview()

        if can_id == self.current_can_id:
            self.bit_editor.set_signals(
                self.defined_signals.get(can_id, [])
            )

    def _graph_selected_signal(self):
        """Saýlanan signal-y grafda görkezýär."""
        row = self.signal_table.currentRow()
        if row < 0:
            return

        msg_item = self.signal_table.item(row, 0)
        sig_item = self.signal_table.item(row, 1)
        if not msg_item or not sig_item:
            return

        can_id = int(msg_item.text().replace("0x", ""), 16)
        sig_name = sig_item.text()

        signals = self.defined_signals.get(can_id, [])
        signal = None
        for s in signals:
            if s.name == sig_name:
                signal = s
                break

        if not signal or can_id not in self.frames_by_id:
            return

        # Build proper CANFrame objects with real timestamps from can_frames
        analyzer = CANAnalyzer()
        real_frames = []
        for ts, cid, data in self.can_frames:
            if cid == can_id:
                real_frames.append(CANFrame(ts, cid, data))
        analyzer.frames_by_id[can_id] = real_frames

        values = analyzer.extract_signal_values(
            can_id, signal.start_bit, signal.length,
            signal.byte_order,
            signal.value_type == "signed",
            signal.scale, signal.offset
        )

        if values:
            timestamps = [v[0] for v in values]
            vals = [v[1] for v in values]
            self.graph_panel.add_signal(sig_name, timestamps, vals)

    # ── Helpers ──

    def _build_database(self) -> DBCDatabase:
        """Häzirki defined_signals-dan DBCDatabase gurýar.
        Loaded DBC-den bar bolan properties-leri saklap galýar."""
        # Start from existing database to preserve nodes, attributes, etc.
        db = DBCDatabase(
            version=self.database.version or "1.0",
            description=self.database.description
        )
        # Preserve loaded properties
        db.nodes = self.database.nodes[:]
        db.attribute_definitions = self.database.attribute_definitions[:]
        db.value_tables = dict(self.database.value_tables)
        db.network_attributes = dict(self.database.network_attributes)
        db.environment_variables = self.database.environment_variables[:]

        for can_id, signals in self.defined_signals.items():
            # Check if a message with this ID already exists in loaded DB
            existing_msg = self.database.get_message(can_id)
            if existing_msg:
                msg = Message(
                    message_id=can_id,
                    name=existing_msg.name,
                    dlc=existing_msg.dlc,
                    sender=existing_msg.sender,
                    signals=signals[:],
                    comment=existing_msg.comment,
                    attributes=dict(existing_msg.attributes)
                )
            else:
                max_dlc = 8
                if can_id in self.frames_by_id:
                    max_dlc = max(
                        (len(d) for d in self.frames_by_id[can_id]),
                        default=8
                    )
                msg = Message(
                    message_id=can_id,
                    name=f"MSG_0x{can_id:03X}",
                    dlc=max_dlc,
                    signals=signals[:]
                )
            db.add_message(msg)

        return db

    def _refresh_signal_list(self):
        """Signal list tablisasyny täzelaýär."""
        self.signal_table.setRowCount(0)
        row = 0

        for can_id in sorted(self.defined_signals.keys()):
            for sig in self.defined_signals[can_id]:
                self.signal_table.insertRow(row)

                self.signal_table.setItem(
                    row, 0, QTableWidgetItem(f"0x{can_id:03X}")
                )
                self.signal_table.setItem(
                    row, 1, QTableWidgetItem(sig.name)
                )
                self.signal_table.setItem(
                    row, 2, QTableWidgetItem(f"{sig.start_bit}|{sig.length}")
                )
                self.signal_table.setItem(
                    row, 3, QTableWidgetItem(str(sig.scale))
                )
                self.signal_table.setItem(
                    row, 4, QTableWidgetItem(sig.unit)
                )

                # Delete button placeholder
                self.signal_table.setItem(row, 5, QTableWidgetItem(""))

                row += 1
        
        # Also update explorer if database changed
        self.db_explorer.populate(self._build_database())

    def _update_dbc_preview(self):
        """DBC preview panelini täzelaýär."""
        db = self._build_database()
        if db.messages:
            generator = DBCGenerator()
            dbc_text = generator.generate(db)
            self.dbc_preview.set_text(dbc_text)
        else:
            self.dbc_preview.set_text("")

    def _update_live_value(self, signal: Signal):
        """Signal-yň live value-sini hasaplaýar we görkezýär."""
        if self.current_can_id < 0:
            return

        data_list = self.frames_by_id.get(self.current_can_id, [])
        if not data_list:
            return

        from ai_module import PatternAnalyzer
        raw_values = PatternAnalyzer.extract_raw_values(
            data_list, signal.start_bit, signal.length, signal.byte_order
        )
        if raw_values:
            self.signal_editor.update_live_value(raw_values[-1])

    def _toggle_theme(self):
        """Dark/Light temany üýtgedýär."""
        self.dark_mode = not self.dark_mode
        self.colors = COLORS_DARK if self.dark_mode else COLORS_LIGHT
        self._apply_theme()
        self.graph_panel.set_dark_mode(self.dark_mode)

    def _status(self, text: str):
        """Status bar-y täzelaýär."""
        self.status_label.setText(f"  {text}")

    def _show_about(self):
        """About dialog-y görkezýär."""
        QMessageBox.about(
            self, "About",
            f"<h2>{self.APP_NAME}</h2>"
            f"<p>Version {self.APP_VERSION}</p>"
            f"<p>Industry-Level CAN Bus Analyzer & DBC Engine</p>"
            f"<p>Features:</p>"
            f"<ul>"
            f"<li>Full DBC Parse & Generate (all sections)</li>"
            f"<li>Signal Multiplexing (MUX) Support</li>"
            f"<li>Value Tables (ENUM) Support</li>"
            f"<li>Attribute Definitions & Values</li>"
            f"<li>Environment Variables</li>"
            f"<li>CAN Signal Encode & Decode</li>"
            f"<li>Full JSON Roundtrip (DBC↔JSON)</li>"
            f"<li>Async File Loading</li>"
            f"<li>CAN Log Analysis</li>"
            f"<li>Bit-Level Visual Editor</li>"
            f"<li>Signal Graph Visualization</li>"
            f"<li>AI-Powered Signal Detection</li>"
            f"<li>🚀 Smart AI Assistant (Reverse Assistant)</li>"
            f"<li>🎓 DBC Knowledge Learning (from personal DBCs)</li>"
            f"<li>Multi-Log Comparison</li>"
            f"<li>Project Save/Load</li>"
            f"</ul>"
        )

    def _on_ai_suggest_clicked(self):
        """Awtomatiki signal tapma (AI) funksiýasyny başlatýar."""
        if not self.can_frames:
            QMessageBox.information(self, "AI Suggest", "No CAN traffic loaded. Load a CAN log first to use AI detection.")
            return

        self._status("AI is analyzing traffic patterns...")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        
        try:
            suggested_db = self.ai_suggester.auto_generate_dbc(self.frames_by_id)
            QApplication.restoreOverrideCursor()

            total_sigs = sum(len(m.signals) for m in suggested_db.messages)
            if total_sigs == 0:
                QMessageBox.information(self, "AI Suggest", "AI couldn't detect any stable signal patterns.")
                return

            res = QMessageBox.question(
                self, "AI Suggest",
                f"AI detected {total_sigs} potential signals. Add them to project?",
                QMessageBox.Yes | QMessageBox.No
            )

            if res == QMessageBox.Yes:
                self.database.merge(suggested_db)
                for msg in suggested_db.messages:
                    if msg.message_id not in self.defined_signals:
                        self.defined_signals[msg.message_id] = msg.signals[:]
                    else:
                        existing_names = [s.name for s in self.defined_signals[msg.message_id]]
                        for s in msg.signals:
                            if s.name not in existing_names:
                                self.defined_signals[msg.message_id].append(s)

                self._refresh_signal_list()
                self.db_explorer.populate(self.database)
                self.db_manager.refresh(self.database)
                self.data_table.update_from_database(self.database)
                self._status(f"AI added {total_sigs} signals.")
                self._switch_workspace(3)
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "AI Error", f"AI detection failed: {e}")

    def _on_compare_logs(self):
        """Iki log-y deňeşdirmek üçin täze log saýlatdyrýar."""
        if not self.can_frames:
            QMessageBox.warning(self, "Compare Logs", "Please load the first log file normally before comparing.")
            return

        path, _ = QFileDialog.getOpenFileName(
            self, "Select Second Log for Comparison", "",
            "CAN Logs (*.log *.asc *.trc);;All Files (*)"
        )
        if not path:
            return

        self._status(f"Comparing with {os.path.basename(path)}...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        try:
            # 1. Parse second log
            from parser import LogParser
            parser = LogParser()
            frames2 = parser.parse(path)
            
            # Sync second log IDs
            frames_by_id2 = {}
            for _, cid, data in frames2:
                if cid not in frames_by_id2:
                    frames_by_id2[cid] = []
                frames_by_id2[cid].append(data)

            # 2. Run Comparison
            result = self.ai_suggester.compare_logs(self.frames_by_id, frames_by_id2)
            
            QApplication.restoreOverrideCursor()
            
            # 3. Show Results Dialog
            dialog = LogComparisonDialog(result, parent=self)
            dialog.exec_()
            
        except Exception as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.critical(self, "Comparison Error", f"Failed to compare logs:\n{e}")

    # ── RE Scout Handlers ──

    def _sync_scout_focus(self, can_id: int, data: bytes):
        """Data table-da ID saýlananda Scout-y şol ID-a fokuslaýar."""
        self.re_scout.set_active_id(can_id)

    def _on_scout_analyze_requested(self, baseline: dict, action: dict):
        """Differential analysis-i başladyar (Global mode)."""
        if not action:
            return
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            results = self.diff_analyzer.analyze(baseline, action)
            self.re_scout.show_results(results)
            self._status("Global RE analysis complete.")
        except Exception as e:
            QMessageBox.critical(self, "Analysis Error", f"Scout failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_scout_signal_added(self, can_id: int, start: int, length: int):
        """Scout-dan tapylan signal-y editor-a dolduryar."""
        self.current_can_id = can_id
        
        # 1. Designer tab-a geç
        self._switch_workspace(1)
        
        # 2. Editor-y doldur
        self.signal_editor.set_from_selection(start, length)
        
        # 3. Message name pre-fill
        self.signal_editor.name_edit.setText(f"SIG_DISC_{can_id:03X}_{start}")
        
        # 4. Scout dock-y optional ýap
        # self.re_scout_dock.hide() 
        
        self._status(f"Discovered signal [ID 0x{can_id:03X} | Bit {start}] loaded into Designer.")

    def _retranslate_ui(self):
        """Update all UI strings when language changes."""
        # Main Window
        self.setWindowTitle(I18N.t("app_name"))
        
        # Sidebar
        self.sidebar_buttons["analyze"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_analyze"))
        self.sidebar_buttons["design"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_design"))
        self.sidebar_buttons["preview"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_preview"))
        self.sidebar_buttons["explorer"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_explorer"))
        self.sidebar_buttons["manage"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_manage"))
        self.sidebar_buttons["guide"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_guide"))
        self.sidebar_buttons["smart"].findChild(QLabel, "NavLabel").setText(I18N.t("nav_assistant"))
        
        # Menus
        self.file_menu.setTitle(I18N.t("menu_file"))
        self.act_open_dbc.setText(I18N.t("menu_open_dbc"))
        self.act_load_log.setText(I18N.t("menu_load_log"))
        self.act_load_video.setText(I18N.t("menu_load_video"))
        self.act_save_project.setText(I18N.t("menu_save_project"))
        self.act_load_project.setText(I18N.t("menu_load_project"))
        self.export_menu.setTitle(I18N.t("menu_export"))
        self.act_export_dbc.setText(I18N.t("menu_export") + " DBC...")
        self.act_export_json.setText(I18N.t("menu_export") + " JSON...")
        self.act_export_csv.setText(I18N.t("menu_export") + " CSV...")
        self.act_exit.setText(I18N.t("menu_exit"))
        
        self.ai_menu.setTitle(I18N.t("menu_ai"))
        self.act_detect.setText(I18N.t("menu_detect"))
        self.act_suggest.setText(I18N.t("menu_suggest"))
        self.act_auto_dbc.setText(I18N.t("menu_auto_dbc"))
        self.act_smart.setText("🚀 " + I18N.t("nav_assistant"))
        self.act_encode.setText(I18N.t("menu_encode"))
        self.act_compare.setText(I18N.t("menu_compare"))
        
        self.hw_menu.setTitle(I18N.t("menu_hw"))
        self.act_hw_connect.setText("🔌 " + I18N.t("menu_connect"))
        self.act_hw_stop.setText("🛑 " + I18N.t("menu_stop"))
        
        self.view_menu.setTitle(I18N.t("menu_view"))
        self.act_dark.setText("🌓 " + I18N.t("menu_dark"))
        
        self.help_menu.setTitle(I18N.t("menu_help"))
        self.act_help_guide.setText(I18N.t("nav_guide"))
        self.act_about.setText(I18N.t("menu_about"))
        
        # Panels & Labels
        self.findChild(QLabel, "SignalListTitle").setText(I18N.t("sig_defined"))
        self.btn_remove_signal.setText(I18N.t("sig_remove"))
        self.btn_graph_signal.setText(I18N.t("sig_show_graph"))
        
        # Table Headers
        self.signal_table.setHorizontalHeaderLabels([
            I18N.t("col_msg"), I18N.t("col_sig"), I18N.t("col_bits"), I18N.t("sig_scale"), I18N.t("sig_unit"), ""
        ])

        self._status(I18N.t("ready"))
        
        # Propagate to sub-panels
        self.re_scout_dock.setWindowTitle(I18N.t("scout_title"))
        self.re_scout.retranslate_ui()
        
        # Workspace Panels
        self.data_table.retranslate_ui()
        self.signal_editor.retranslate_ui()
        self.dbc_preview.retranslate_ui()
        self.db_explorer.retranslate_ui()
        self.log_console.retranslate_ui()
        self.bit_editor.retranslate_ui()
        self.graph_panel.retranslate_ui()
        self.db_manager.retranslate_ui()
        self.learning_center.retranslate_ui()
        self.video_panel.retranslate_ui()
        
        # Assistant
        if hasattr(self, 'assistant_panel'):
            self.assistant_panel.retranslate_ui()

        # Update persistent status label
        self.status_label.setText(self._get_status_text())
