"""
ui/smart_assistant_panel.py - Professional Smart AI Selection & Training Workspace
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QFileDialog, QFrame, QScrollArea,
    QComboBox, QLineEdit, QTextEdit, QListWidget,
    QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from i18n import I18N
from ai_module import DBCKnowledgeManager, SmartAssistantEngine
from parser import DBCParser


class RecommendationCard(QFrame):
    """AI tarapyndan berilýän her bir maslahat üçin card."""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("RecommendationCard")
        self.setProperty("class", "Card")
        # Custom sub-styles that still need CSS for specific components
        self.setStyleSheet("""
            #StatusBadge {
                background-color: #0076FF;
                color: white;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        
        # Header: ID + Badge
        header = QHBoxLayout()
        can_id = self.data["can_id"]
        id_label = QLabel(f"<b>CAN ID: 0x{can_id:03X}</b>")
        header.addWidget(id_label)
        
        header.addStretch()
        
        self.badge = QLabel(I18N.t("ai_rec_badge"))
        self.badge.setObjectName("StatusBadge")
        header.addWidget(self.badge)
        layout.addLayout(header)

        # Advice Text
        advice = QLabel(self.data["advice"])
        advice.setWordWrap(True)
        advice.setProperty("class", "PlaceholderText")
        advice.setStyleSheet("margin-top: 5px;")
        layout.addWidget(advice)

        # Technical Details
        cand = self.data["candidate"]
        details = QLabel(
            f"{I18N.t('nav_assistant')}: {cand.suggested_name} ({cand.suggested_type})\n"
            f"{I18N.t('sig_start')}: {cand.start_bit} | {I18N.t('sig_length')}: {cand.length} | "
            f"Conf: {cand.confidence:.0%}"
        )
        details.setProperty("class", "PreviewBox")
        details.setStyleSheet("font-size: 11px;")
        layout.addWidget(details)


class SmartAssistantPanel(QWidget):
    """
    Smart AI Assistant Workspace.
    DBC-den öwrenýär we loglary professional analiz edýär.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.km = DBCKnowledgeManager()
        self.engine = SmartAssistantEngine(self.km)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # ── Left Side: Controls ──
        controls = QFrame()
        controls.setFixedWidth(350)
        c_layout = QVBoxLayout(controls)
        c_layout.setSpacing(15)

        # 1. Training Section
        train_box = QFrame()
        train_box.setProperty("class", "SectionBox")
        t_layout = QVBoxLayout(train_box)
        
        self.train_title = QLabel(I18N.t("ai_teach_title"))
        self.train_title.setProperty("subheading", True)
        t_layout.addWidget(self.train_title)
        
        self.train_desc = QLabel(I18N.t("ai_teach_desc"))
        t_layout.addWidget(self.train_desc)
        
        self.brand_input = QLineEdit()
        self.brand_input.setPlaceholderText(I18N.t("ai_brand_placeholder"))
        t_layout.addWidget(self.brand_input)
        
        self.btn_train = QPushButton(I18N.t("ai_btn_train"))
        self.btn_train.setProperty("primary", True)
        self.btn_train.clicked.connect(self._on_train_clicked)
        t_layout.addWidget(self.btn_train)
        c_layout.addWidget(train_box)

        # 2. Smart Scan Section
        scan_box = QFrame()
        scan_box.setProperty("class", "SectionBox")
        s_layout = QVBoxLayout(scan_box)
        
        self.scan_title = QLabel(I18N.t("ai_scan_title"))
        self.scan_title.setProperty("subheading", True)
        s_layout.addWidget(self.scan_title)
        
        self.main_log_lbl = QLabel(I18N.t("ai_log_main"))
        s_layout.addWidget(self.main_log_lbl)
        self.main_log_path = QLineEdit()
        self.main_log_path.setReadOnly(True)
        h_log1 = QHBoxLayout()
        h_log1.addWidget(self.main_log_path)
        btn_log1 = QPushButton("...")
        btn_log1.setFixedWidth(30)
        btn_log1.clicked.connect(self._pick_main_log)
        h_log1.addWidget(btn_log1)
        s_layout.addLayout(h_log1)
        
        self.ref_log_lbl = QLabel(I18N.t("ai_log_ref"))
        s_layout.addWidget(self.ref_log_lbl)
        self.ref_log_path = QLineEdit()
        self.ref_log_path.setReadOnly(True)
        h_log2 = QHBoxLayout()
        h_log2.addWidget(self.ref_log_path)
        btn_log2 = QPushButton("...")
        btn_log2.setFixedWidth(30)
        btn_log2.clicked.connect(self._pick_ref_log)
        h_log2.addWidget(btn_log2)
        s_layout.addLayout(h_log2)
        
        self.brand_select = QComboBox()
        self.brand_select.addItems(["Generic", "Toyota", "Volkswagen", "Honda", "Nissan", "Ford"])
        self.brand_ctx_lbl = QLabel(I18N.t("ai_brand_context"))
        s_layout.addWidget(self.brand_ctx_lbl)
        s_layout.addWidget(self.brand_select)
        
        self.btn_run = QPushButton(I18N.t("ai_btn_run"))
        self.btn_run.setFixedHeight(40)
        self.btn_run.setProperty("primary", True)
        self.btn_run.clicked.connect(self._on_run_analysis)
        s_layout.addWidget(self.btn_run)
        
        c_layout.addWidget(scan_box)
        c_layout.addStretch()
        
        main_layout.addWidget(controls)

        # ── Right Side: Expert Recommendations ──
        results_area = QFrame()
        results_area.setProperty("class", "SectionBox")
        r_layout = QVBoxLayout(results_area)
        
        self.res_title = QLabel(I18N.t("ai_expert_title"))
        self.res_title.setProperty("heading", True)
        r_layout.addWidget(self.res_title)
        
        self.res_desc = QLabel(I18N.t("ai_expert_desc"))
        r_layout.addWidget(self.res_desc)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: transparent; border: none;")
        self.scroll_content = QWidget()
        self.cards_layout = QVBoxLayout(self.scroll_content)
        self.cards_layout.setAlignment(Qt.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        
        r_layout.addWidget(self.scroll)
        
        main_layout.addWidget(results_area)

    def _pick_main_log(self):
        path, _ = QFileDialog.getOpenFileName(self, I18N.t("msg_load_log"))
        if path: self.main_log_path.setText(path)

    def _pick_ref_log(self):
        path, _ = QFileDialog.getOpenFileName(self, I18N.t("msg_compare_logs"))
        if path: self.ref_log_path.setText(path)

    def _on_train_clicked(self):
        brand = self.brand_input.text() or "Generic"
        paths, _ = QFileDialog.getOpenFileNames(self, I18N.t("ai_select_dbc"), "", "DBC Files (*.dbc)")
        if not paths: return

        parser = DBCParser()
        count = 0
        for p in paths:
            try:
                db = parser.parse(p)
                self.km.learn_from_dbc(db, brand)
                count += 1
            except: continue
        
        self.km.save_knowledge()
        QMessageBox.information(self, I18N.t("menu_help"), I18N.t("ai_msg_train_ok").format(count=count, brand=brand))

    def _on_run_analysis(self):
        main_path = self.main_log_path.text()
        if not main_path:
            QMessageBox.warning(self, I18N.t("msg_invalid_name"), I18N.t("msg_no_can_traffic"))
            return

        # Clear old cards
        for i in reversed(range(self.cards_layout.count())): 
            self.cards_layout.itemAt(i).widget().setParent(None)

        # Run Analysis (Simulated for this script, normally uses real engine)
        # Note: In the final app, we'll parse the logs here
        try:
            from parser import LogParser
            lp = LogParser()
            frames1 = lp.parse(main_path)
            f_id1 = {}
            for _, cid, data in frames1:
                if cid not in f_id1: f_id1[cid] = []
                f_id1[cid].append(data)
            
            f_id2 = None
            if self.ref_log_path.text():
                frames2 = lp.parse(self.ref_log_path.text())
                f_id2 = {}
                for _, cid, data in frames2:
                    if cid not in f_id2: f_id2[cid] = []
                    f_id2[cid].append(data)

            results = self.engine.smart_analyze(f_id1, self.brand_select.currentText(), f_id2)
            
            if not results:
                self.cards_layout.addWidget(QLabel(I18N.t("ai_no_results")))
            else:
                for res in sorted(results, key=lambda x: x['candidate'].confidence, reverse=True):
                    # Show top IDs only to avoid clutter
                    if res['candidate'].confidence > 0.4:
                        card = RecommendationCard(res)
                        self.cards_layout.addWidget(card)
                        
        except Exception as e:
            QMessageBox.critical(self, I18N.t("msg_invalid_name"), str(e))

    def retranslate_ui(self):
        """Update strings when language changes."""
        self.train_title.setText(I18N.t("ai_teach_title"))
        self.train_desc.setText(I18N.t("ai_teach_desc"))
        self.brand_input.setPlaceholderText(I18N.t("ai_brand_placeholder"))
        self.btn_train.setText(I18N.t("ai_btn_train"))
        
        self.scan_title.setText(I18N.t("ai_scan_title"))
        self.main_log_lbl.setText(I18N.t("ai_log_main"))
        self.ref_log_lbl.setText(I18N.t("ai_log_ref"))
        self.brand_ctx_lbl.setText(I18N.t("ai_brand_context"))
        self.btn_run.setText(I18N.t("ai_btn_run"))
        
        self.res_title.setText(I18N.t("ai_expert_title"))
        self.res_desc.setText(I18N.t("ai_expert_desc"))
        
        # Note: Recommendations cards themselves are temporary and will be recreated on next run.
        # But we can try to re-run or just update existing ones if needed.
