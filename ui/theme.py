"""
theme.py - Modern 2026 UI Theme System
Light/Dark theme, clean typography, professional styling.
"""

# ────────────────────────────────────────────────────
# Color palette
# ────────────────────────────────────────────────────

COLORS_LIGHT = {
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F3F4F6", # Main app background
    "bg_tertiary": "#F9FAFB",
    "bg_panel": "#FFFFFF",     # Cards and SideNav
    "bg_input": "#FFFFFF",
    "bg_hover": "#F3F4F6",
    "bg_selected": "#DBEAFE",  # Tailwind Blue 100
    "bg_accent": "#2563EB",    # Tailwind Blue 600

    "text_primary": "#111827",
    "text_secondary": "#4B5563",
    "text_tertiary": "#9CA3AF",
    "text_on_accent": "#FFFFFF",
    "text_link": "#2563EB",

    "border": "#E5E7EB",
    "border_focus": "#3B82F6",
    "border_light": "#F3F4F6",

    "success": "#10B981",
    "warning": "#FBBC04",
    "error": "#EA4335",
    "info": "#4285F4",

    "bit_0": "#E8EAED",
    "bit_1": "#D2E3FC",
    "bit_selected": "#1A73E8",
    "bit_hover": "#BDC1C6",

    "graph_bg": "#FFFFFF",
    "graph_grid": "#E8EAED",
    "graph_lines": [
        "#1A73E8", "#EA4335", "#34A853", "#FBBC04",
        "#8E24AA", "#00ACC1", "#FF6D00", "#43A047"
    ],

    "scrollbar": "#BDC1C6",
    "scrollbar_hover": "#9AA0A6",

    "text_caption": "#80868B",
    "bg_preview": "#F8F9FA",
    "border_strong": "#DADCE0",

    "shadow": "rgba(60, 64, 67, 0.15)",
}

COLORS_DARK = {
    "bg_primary": "#1E1E1E",
    "bg_secondary": "#252526",
    "bg_tertiary": "#2D2D30",
    "bg_panel": "#252526",
    "bg_input": "#3C3C3C",
    "bg_hover": "#2A2D2E",
    "bg_selected": "#094771",
    "bg_accent": "#007ACC",

    "text_primary": "#CCCCCC",
    "text_secondary": "#9D9D9D",
    "text_tertiary": "#6D6D6D",
    "text_on_accent": "#FFFFFF",
    "text_link": "#3794FF",

    "border": "#3C3C3C",
    "border_focus": "#007ACC",
    "border_light": "#333333",

    "success": "#4EC9B0",
    "warning": "#CCA700",
    "error": "#F44747",
    "info": "#3794FF",

    "bit_0": "#3C3C3C",
    "bit_1": "#264F78",
    "bit_selected": "#007ACC",
    "bit_hover": "#505050",

    "graph_bg": "#1E1E1E",
    "graph_grid": "#333333",
    "graph_lines": [
        "#3794FF", "#F44747", "#4EC9B0", "#CCA700",
        "#C586C0", "#00B7C3", "#FF8C00", "#6A9955"
    ],

    "scrollbar": "#4A4A4A",
    "scrollbar_hover": "#6A6A6A",

    "text_caption": "#9AA0A6",
    "bg_preview": "#2D2D30",
    "border_strong": "#454545",

    "shadow": "rgba(0, 0, 0, 0.4)",
}


def get_stylesheet(dark: bool = False) -> str:
    """Temanyň QSS stylesheet-ini gaýtarýar."""
    c = COLORS_DARK if dark else COLORS_LIGHT

    return f"""
    /* ── Global ── */
    QWidget {{
        background-color: {c['bg_primary']};
        color: {c['text_primary']};
        font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
        font-size: 13px;
    }}

    /* ── Main Window ── */
    QMainWindow {{
        background-color: {c['bg_secondary']};
    }}

    QMainWindow::separator {{
        background: {c['border']};
        width: 1px;
        height: 1px;
    }}

    /* ── Menu Bar ── */
    QMenuBar {{
        background-color: {c['bg_panel']};
        border-bottom: 1px solid {c['border']};
        padding: 2px 0px;
    }}

    QMenuBar::item {{
        padding: 6px 12px;
        border-radius: 4px;
        margin: 2px;
    }}

    QMenuBar::item:selected {{
        background-color: {c['bg_hover']};
    }}

    QMenu {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 8px 32px 8px 16px;
        border-radius: 4px;
        margin: 1px 4px;
    }}

    QMenu::item:selected {{
        background-color: {c['bg_hover']};
    }}

    QMenu::separator {{
        height: 1px;
        background: {c['border_light']};
        margin: 4px 8px;
    }}

    /* ── Tool Bar ── */
    QToolBar {{
        background-color: {c['bg_panel']};
        border-bottom: 1px solid {c['border']};
        padding: 4px 8px;
        spacing: 4px;
    }}

    QToolButton {{
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 6px 12px;
        color: {c['text_primary']};
        font-weight: 500;
    }}

    QToolButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['border']};
    }}

    QToolButton:pressed {{
        background-color: {c['bg_selected']};
    }}

    /* ── Side Navigation ── */
    #SideNav {{
        background-color: {c['bg_panel']};
        border-right: 1px solid {c['border']};
        min-width: 110px;
        max-width: 110px;
    }}

    #SideNav QPushButton {{
        background-color: transparent;
        border: none;
        border-radius: 8px;
        margin: 4px 10px;
        padding: 8px 4px;
        color: {c['text_secondary']};
    }}

    #SideNav QPushButton:hover {{
        background-color: {c['bg_hover']};
        color: {c['text_primary']};
    }}

    #SideNav QPushButton[active="true"] {{
        background-color: {c['bg_selected']};
        color: {c['bg_accent']};
    }}

    #SideNav QLabel {{
        background: transparent;
        border: none;
        padding: 0px;
        margin: 0px;
    }}

    /* ── Workspace Card ── */
    #WorkspaceBody {{
        border: none;
    }}

    .Card {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
    }}

    #CardHeader {{
        padding: 12px 16px;
        border-bottom: 1px solid {c['border_light']};
        background-color: transparent;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }}

    #CardContent {{
        border: none;
        border-bottom-left-radius: 11px;
        border-bottom-right-radius: 11px;
        background: transparent;
    }}

    .CardTitle {{
        font-weight: 700;
        font-size: 14px;
        color: {c['text_primary']};
    }}

    .CardSubtitle {{
        color: {c['text_caption']};
        font-size: 11px;
    }}

    .SectionHeader {{
        font-size: 20px;
        font-weight: 700;
        color: {c['text_primary']};
        margin-bottom: 10px;
    }}

    .PlaceholderPlus {{
        font-size: 48px;
        color: {c['text_tertiary']};
    }}

    .PlaceholderText {{
        font-weight: 700;
        color: {c['text_caption']};
    }}

    .PreviewBox {{
        background-color: {c['bg_preview']};
        border: 1px dashed {c['border_strong']};
        border-radius: 8px;
        padding: 12px;
    }}

    .SectionBox {{
        background-color: {c['bg_tertiary']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        padding: 16px;
    }}

    .ContentBrowser {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 12px;
        padding: 20px;
        color: {c['text_primary']};
    }}

    /* ── Dock Widget ── */
    QDockWidget {{
        titlebar-close-icon: none;
        border: 1px solid {c['border']};
    }}

    QDockWidget::title {{
        background-color: {c['bg_tertiary']};
        padding: 8px 12px;
        border-bottom: 1px solid {c['border']};
        font-weight: 600;
        font-size: 12px;
        color: {c['text_secondary']};
        text-transform: uppercase;
    }}

    /* ── Tab Widget ── */
    QTabWidget::pane {{
        border: 1px solid {c['border']};
        border-top: none;
        background: {c['bg_panel']};
    }}

    QTabBar::tab {{
        background: {c['bg_secondary']};
        border: 1px solid {c['border']};
        border-bottom: none;
        padding: 8px 20px;
        margin-right: 2px;
        border-radius: 6px 6px 0px 0px;
        color: {c['text_secondary']};
    }}

    QTabBar::tab:selected {{
        background: {c['bg_panel']};
        color: {c['text_primary']};
        font-weight: 600;
        border-bottom: 2px solid {c['bg_accent']};
    }}

    QTabBar::tab:hover {{
        background: {c['bg_hover']};
    }}

    /* ── Table & Tree ── */
    QTableWidget, QTableView, QTreeWidget, QTreeView {{
        background-color: {c['bg_panel']};
        alternate-background-color: {c['bg_secondary']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        gridline-color: {c['border_light']};
        selection-background-color: {c['bg_selected']};
        selection-color: {c['text_primary']};
    }}

    QHeaderView::section {{
        background-color: {c['bg_tertiary']};
        padding: 8px 12px;
        border: none;
        border-bottom: 2px solid {c['border']};
        border-right: 1px solid {c['border_light']};
        font-weight: 600;
        font-size: 11px;
        color: {c['text_secondary']};
        text-transform: uppercase;
    }}

    /* ── Input Fields ── */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 12px;
        color: {c['text_primary']};
        font-size: 13px;
    }}

    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border-color: {c['border_focus']};
        border-width: 2px;
        padding: 7px 11px;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c['bg_panel']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        selection-background-color: {c['bg_selected']};
    }}

    /* ── Buttons ── */
    QPushButton {{
        background-color: {c['bg_tertiary']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        padding: 8px 20px;
        font-weight: 500;
        color: {c['text_primary']};
        min-height: 18px;
    }}

    QPushButton:hover {{
        background-color: {c['bg_hover']};
        border-color: {c['border_focus']};
    }}

    QPushButton:pressed {{
        background-color: {c['bg_selected']};
    }}

    QPushButton[primary="true"] {{
        background-color: {c['bg_accent']};
        color: {c['text_on_accent']};
        border: none;
        font-weight: 600;
    }}

    QPushButton[primary="true"]:hover {{
        background-color: {c['bg_accent']};
        opacity: 0.9;
    }}

    /* ── Group Box ── */
    QGroupBox {{
        font-weight: 600;
        font-size: 12px;
        color: {c['text_secondary']};
        border: 1px solid {c['border_light']};
        border-radius: 8px;
        margin-top: 16px;
        padding-top: 16px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px;
    }}

    /* ── Scroll Bar ── */
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0;
    }}

    QScrollBar::handle:vertical {{
        background: {c['scrollbar']};
        border-radius: 4px;
        min-height: 32px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c['scrollbar_hover']};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
        margin: 0;
    }}

    QScrollBar::handle:horizontal {{
        background: {c['scrollbar']};
        border-radius: 4px;
        min-width: 32px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {c['scrollbar_hover']};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}

    /* ── Text Edit ── */
    QTextEdit, QPlainTextEdit {{
        background-color: {c['bg_input']};
        border: 1px solid {c['border']};
        border-radius: 8px;
        padding: 8px;
        font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
        font-size: 12px;
    }}

    /* ── Status Bar ── */
    QStatusBar {{
        background-color: {c['bg_accent']};
        color: {c['text_on_accent']};
        border: none;
        font-size: 12px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* ── Splitter ── */
    QSplitter::handle {{
        background-color: transparent;
    }}

    QSplitter::handle:horizontal {{
        width: 12px;
    }}

    QSplitter::handle:vertical {{
        height: 12px;
    }}

    /* ── Label ── */
    QLabel {{
        background: transparent;
    }}

    QLabel[heading="true"] {{
        font-size: 18px;
        font-weight: 700;
        color: {c['text_primary']};
    }}

    QLabel[subheading="true"] {{
        font-size: 14px;
        font-weight: 600;
        color: {c['text_secondary']};
    }}

    QLabel[caption="true"] {{
        font-size: 11px;
        color: {c['text_tertiary']};
    }}

    /* ── Progress Bar ── */
    QProgressBar {{
        border: none;
        border-radius: 4px;
        background-color: {c['bg_tertiary']};
        text-align: center;
        height: 6px;
    }}

    QProgressBar::chunk {{
        background-color: {c['bg_accent']};
        border-radius: 4px;
    }}

    /* ── ToolTip ── */
    QToolTip {{
        background-color: {c['bg_tertiary']};
        color: {c['text_primary']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 12px;
    }}

    /* ── CheckBox ── */
    QCheckBox {{
        spacing: 8px;
        background: transparent;
    }}

    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border-radius: 4px;
        border: 2px solid {c['border']};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c['bg_accent']};
        border-color: {c['bg_accent']};
    }}

    QCheckBox::indicator:hover {{
        border-color: {c['border_focus']};
    }}
    """
