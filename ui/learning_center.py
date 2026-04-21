"""
ui/learning_center.py - Multi-lingual DBC Interactive Guide (Professional Edition)
DBC spesifikasiýasyny öwrenmek üçin gollanma (TM/RU/EN).
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QTextBrowser, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from core.i18n import I18N


class DBCLearningCenter(QWidget):
    """
    DBC spesifikasiýasyny we CAN protokolyny öwredýän interaktiw gollanma.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.is_dark = False
        self._setup_ui()
        self.retranslate_ui()

    def set_dark_mode(self, is_dark):
        """Ulgam temasyny düzedýär."""
        self.is_dark = is_dark
        self._update_content(self.lang_combo.currentText())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        self.title_lbl = QLabel(I18N.t("guide_header"))
        self.title_lbl.setProperty("class", "SectionHeader")
        header.addWidget(self.title_lbl)
        
        header.addStretch()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["TKM", "RUS", "ENG"])
        self.lang_combo.currentTextChanged.connect(self._on_combo_changed)
        self.lang_lbl = QLabel(I18N.t("lang_toggle"))
        header.addWidget(self.lang_lbl)
        header.addWidget(self.lang_combo)
        
        layout.addLayout(header)

        # Content Area
        self.content_browser = QTextBrowser()
        self.content_browser.setOpenExternalLinks(True)
        self.content_browser.setProperty("class", "ContentBrowser")
        
        layout.addWidget(self.content_browser)

    def _update_content(self, lang_text=None):
        lang = lang_text or I18N.current_language()
        if lang == "TKM":
            html = self._get_tm_content()
        elif lang == "RUS":
            html = self._get_ru_content()
        else:
            html = self._get_en_content()
            
        # Add dynamic styling to HTML based on theme
        bg_box = "#2D2D30" if self.is_dark else "#f6f8fa"
        border_box = "#454545" if self.is_dark else "#e1e4e8"
        text_color = "#CCCCCC" if self.is_dark else "#202124"
        accent_blue = "#3794FF" if self.is_dark else "#0366d6"
        
        styled_html = f"""
        <style>
            body, p, li {{ color: {text_color}; font-family: 'Segoe UI', sans-serif; line-height: 1.5; }}
            h1, h2, h3 {{ color: {accent_blue}; margin-top: 20px; }}
            code {{ background-color: {bg_box}; padding: 2px 4px; border-radius: 4px; color: {accent_blue}; }}
            .info-box {{ background-color: {bg_box}; padding: 15px; border-left: 5px solid {accent_blue}; border: 1px solid {border_box}; border-radius: 8px; margin: 10px 0; }}
            b {{ color: {accent_blue}; }}
        </style>
        {html}
        """
        self.content_browser.setHtml(styled_html)

    def _get_tm_content(self):
        return """
        <h1>DBC Masterklassy: Professional Gollanma</h1>
        <p>DBC (Database CAN) faýly - bu CAN torunda maglumatlaryň nähili alyş-çalyş edilýändigini düşündirýän standartdyr.</p>
        
        <h3>1. Umumy Struktura</h3>
        <ul>
            <li><b>VERSION</b>: Faýlyň wersiýasy.</li>
            <li><b>NS_ (New Symbols)</b>: Ulanylýan makrolar.</li>
            <li><b>BU_ (Nodes)</b>: Torda ýerleşýän elektron bloklar (ECU).</li>
            <li><b>BO_ (Messages)</b>: CAN frame-ler (ID we DLC).</li>
            <li><b>SG_ (Signals)</b>: Bit derejesindäki maglumatlar.</li>
        </ul>

        <h3>2. Signallaryň Kesgitlenişi (SG_)</h3>
        <p>Signal ýazylanda aşakdaky tertip ulanylýar:</p>
        <code>SG_ SignalName : StartBit|Length@ByteOrder ValueType (Scale,Offset) [Min|Max] "Unit" Receiver</code>
        
        <p><b>Mysallar:</b></p>
        <ul>
            <li><b>StartBit|Length</b>: Signalyň haýsy bitden başlap, näçe bit dowam edýändigi.</li>
            <li><b>@1+ (Intel)</b>: LSB (Least Significant Bit) ilki gelýär.</li>
            <li><b>@0+ (Motorola)</b>: MSB (Most Significant Bit) ilki gelýär.</li>
        </ul>

        <div class='info-box'>
        <b>Professional Mysal:</b><br>
        <code>BO_ 256 EngineData: 8 ECU_Motor</code><br>
        <code>  SG_ RPM : 0|16@1+ (0.25,0) [0|8000] "rpm" ECU_Dashboard</code>
        <br><br>
        <i>Bu ýerde 0x100 ID-li EngineData mesajy, 0-bitden başlaýan 16 bitlik RPM signalyny saklaýar. Scale 0.25 bolany üçin, hakyky baha = raw * 0.25.</i>
        </div>

        <h3>3. Atributlar (BA_)</h3>
        <p>Mesajlaryň döwürleýinligi (Cycle Time) ýa-da tizlik ýaly goşmaça maglumatlar üçin ulanylýar.</p>
        
        <div class='info-box'>
        <b>Professional Mux (Multiplexing) Mysal:</b><br>
        <code>BO_ 1500 Diagnostic_Msg: 8 ECU_A</code><br>
        <code>  SG_ Mux_Switch M : 0|8@1+ (1,0) [0|255] "" ECU_B</code><br>
        <code>  SG_ Temp_Signal m0 : 8|16@1+ (0.1,-40) [-40|215] "C" ECU_B</code><br>
        <code>  SG_ Press_Signal m1 : 8|16@1+ (1,0) [0|65535] "Pa" ECU_B</code><br>
        <br>
        <i>Düşündiriş: Mux_Switch 0 bolanda Temp_Signal okalýar, 1 bolanda bolsa Press_Signal okalýar. Bu bir ID-de köp maglumat ibermäge kömek edýär.</i>
        </div>
        """

    def _on_combo_changed(self, text):
        """Combo üýtgeçeginde I18N-i täzeleýär (öz gezeginde bu paneli hem täzelär)."""
        I18N.set_language(text)

    def retranslate_ui(self):
        """Dili täzeleýär."""
        self.lang_lbl.setText(I18N.t("lang_toggle"))
        self.title_lbl.setText(I18N.t("guide_header"))
        
        # Combo box-y sinhronla
        self.lang_combo.blockSignals(True)
        idx = self.lang_combo.findText(I18N.current_language())
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.blockSignals(False)
        
        self._update_content(I18N.current_language())

    def _get_ru_content(self):
        return """
        <h1>Мастер-класс DBC: Профессиональное руководство</h1>
        <p>DBC (Database CAN) — это стандартный формат файлов, описывающий структуру данных в сети CAN.</p>
        
        <h3>1. Общая структура</h3>
        <ul>
            <li><b>BU_ (Nodes)</b>: Электронные блоки управления (ECU) в сети.</li>
            <li><b>BO_ (Messages)</b>: Сообщения CAN (ID и DLC).</li>
            <li><b>SG_ (Signals)</b>: Данные на уровне бит внутри сообщения.</li>
        </ul>

        <h3>2. Определение сигналов (SG_)</h3>
        <p>Формат записи сигнала:</p>
        <code>SG_ ИмяСигнала : СтартБит|Длина@ПорядокБайт Тип (Множитель,Смещение) [Мин|Макс] "Ед.Изм" Получатель</code>
        
        <p><b>Пример:</b></p>
        <div class='info-box'>
        <code>BO_ 500 VehicleSpeedMessage: 8 ABS_Module</code><br>
        <code>  SG_ Speed : 0|16@1+ (0.01,0) [0|300] "km/h" Dashboard</code>
        <br><br>
        <i>Объяснение: Сообщение с ID 0x1F4 содержит сигнал скорости. Каждое значение из лога умножается на 0.01 для получения реальности в км/ч.</i>
        </div>

        <h3>3. Таблицы значений (VAL_)</h3>
        <p>Используются для перевода чисел в понятный текст (например, Состояние двери: 0 - Закрыто, 1 - Открыто).</p>
        <code>VAL_ 500 DoorStatus 1 "Open" 0 "Closed" ;</code>
        """

    def _get_en_content(self):
        return """
        <h1>DBC Masterclass: Professional Guide</h1>
        <p>A DBC (Database CAN) file defines how data is structured and exchanged on a CAN bus network.</p>
        
        <h3>1. Core Syntax</h3>
        <ul>
            <li><b>BU_ (Nodes)</b>: Network participants (ECUs).</li>
            <li><b>BO_ (Messages)</b>: The CAN frames including Hex ID and Length (DLC).</li>
            <li><b>SG_ (Signals)</b>: The individual data points within a message.</li>
        </ul>

        <h3>2. Signal Definition (SG_)</h3>
        <code>SG_ SignalName : StartBit|Length@Endianness Signedness (Factor,Offset) [Min|Max] "Unit" Receiver</code>
        
        <p><b>Common Layouts:</b></p>
        <ul>
            <li><b>Little Endian (@1)</b>: Also known as 'Intel' format. Bits grow upwards.</li>
            <li><b>Big Endian (@0)</b>: Also known as 'Motorola' format. Bits grow downwards across bytes.</li>
        </ul>

        <div class='info-box'>
        <b>Example (Engine RPM):</b><br>
        <code>BO_ 100 EngineStatus: 8 EMS</code><br>
        <code>  SG_ EngSpeed : 0|16@1+ (0.25,0) [0|8000] "rpm" DISP, TCU</code>
        </div>
        """
