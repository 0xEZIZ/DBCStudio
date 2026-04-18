"""
i18n.py - Internationalization System (TKM, RUS, ENG)
Multilingual support for the CAN DBC Tool.
Professional engineering terminology.
"""

from PyQt5.QtCore import QObject, pyqtSignal

class Translator(QObject):
    """Singleton-based translation manager."""
    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._current_lang = "TKM"
        self._translations = {
            "TKM": {
                # General
                "app_name": "CAN Awtobus Analizatory & DBC Dörediji",
                "app_version": "3.0 Professional",
                "ready": "Taýýar",
                "error": "Ýalňyşlyk",
                "warning": "Duýduryş",
                "info": "Maglumat",
                "success": "Üstünlikli",
                "loading": "Ýüklenýär...",
                "no": "Ýok",
                "yes": "Hawa",

                # Navigation (Sidebar)
                "nav_analyze": "Analiz",
                "nav_design": "Taslama",
                "nav_preview": "Gözden geçirme",
                "nav_explorer": "Agaç (DBC)",
                "nav_manage": "Dolandyrmak",
                "nav_guide": "Gollanma",
                "nav_assistant": "AI Kömekçi",

                # Menus
                "menu_file": "&Faýl",
                "menu_open_dbc": "DBC açmak...",
                "menu_load_log": "CAN Log ýüklemek...",
                "menu_load_video": "Wideo Sync ýüklemek...",
                "menu_save_project": "Taslamany ýazdyrmak",
                "menu_load_project": "Taslamany ýüklemek",
                "menu_export": "Eksport",
                "menu_exit": "Çykmak",
                "menu_ai": "&AI Gurallary",
                "menu_detect": "Signallary awtomatiki tapmak",
                "menu_suggest": "Signal gözlemek...",
                "menu_auto_dbc": "Awtomatiki DBC döretmek",
                "menu_encode": "Signal bahalaryny kodlamak...",
                "menu_compare": "Log-lary deňeşdirmek...",
                "menu_hw": "&Hardware",
                "menu_connect": "CAN Bus-a birikmek...",
                "menu_stop": "Ýazgy duruzmak",
                "menu_view": "&Görünüş",
                "menu_dark": "Garaňky/Ýagty tema",
                "menu_help": "&Kömek",
                "menu_about": "Programma barada",

                # Workspace Cards
                "card_video": "Wideo Sinkronizasiýa",
                "card_traffic": "CAN Awtobus Trafıgi",
                "card_graph": "Signal Grafigi",
                "card_console": "Ulgam Konsoly we Diagnostika",
                "card_bit_editor": "Bitleriň Ýerleşiş Redaktory",
                "card_signal_props": "Signal Häsiýetnamasy",
                "card_dbc_preview": "DBC Faýlynyň Görnüşi",
                "card_db_explorer": "Database Agajy",
                "card_db_manage": "DBC Maglumatlar Binýadyny Dolandyrmak",
                "card_guide": "DBC Professional Gollanmasy",
                "card_ai_wizard": "Akylly AI Analiz Kömekçisi",

                # RE Scout
                "scout_title": "🛡️ RE Gözlegçi (Scout)",
                "scout_info": "Hereket esasly signal gözlegi: Kadaly ýagdaý we Hereket ýagdaýyny deňeşdiriň.",
                "scout_status": "Ýagdaý: ",
                "scout_idle": "🔘 TAÝÝAR",
                "scout_rec_baseline": "🟦 BASELINE ÝAZGYSY (IDLE)",
                "scout_rec_action": "🔥 HEREKET ÝAZGYSY (EVENT)",
                "scout_analyzing": "⌛ ANALIZ EDILÝÄR...",
                "scout_complete": "✨ ANALIZ TAMAMLANDY",
                "scout_btn_baseline": "1. Baseline Başlat",
                "scout_btn_action": "2. Hereket Başlat",
                "scout_btn_reset": "Ähli maglumatlary nol et",
                "scout_candidates": "🎯 TAPYLAN SIGNAL KANDIDATLARY",
                "scout_heatmap": "Bitleriň gyzgynlyk kartasy",
                "scout_detail": "Analiz etmek üçin signal saýlaň.",
                "scout_score": "Tapawut Score",
                "scout_load_signal_tip": "Bu signaly Designer-a ýüklemek üçin iki gezek basyň.",

                # Signal Editor
                "sig_name": "Signal ady:",
                "sig_start": "Başlangyç bit:",
                "sig_length": "Uzynlygy:",
                "sig_byte_order": "Byte tertibi:",
                "sig_type": "Baha görnüşi:",
                "sig_scale": "Koeffisient:",
                "sig_offset": "Süýşme (Offset):",
                "sig_unit": "Birligi:",
                "sig_min": "Min:",
                "sig_max": "Max:",
                "sig_add": "Signal goş",
                "sig_clear": "Arassala",

                # Column Headers
                "col_id": "ID",
                "col_dlc": "DLC",
                "col_data": "Maglumat (Hex)",
                "col_timestamp": "Wagt",
                "col_msg": "Habar (Message)",
                "col_sig": "Signal",
                "col_bits": "Bitler",

                # Theme
                "theme_toggle": "Tema çalyşmak",
                "lang_toggle": "Dili seçmek",

                # Hardware Dialog
                "hw_title": "CAN Enjamyna Birikmek",
                "hw_settings": "Apparatura Sazlamalary",
                "hw_interface": "Interfeýs:",
                "hw_channel": "Kanal:",
                "hw_bitrate": "Bitrate (Tizlik):",
                "hw_logging": "Log ýazgy we Saklamak",
                "hw_autosave": "Awtomatik sakla (.txt + .csv)",
                "hw_listen_only": "Diňe diňlemek (Passive)",

                # Console
                "console_title": "Ulgam Loglary we Konsol",
                "console_clear": "Arassala",

                # Additional RE Scout
                "scout_stop_baseline": "⏹️ BASELINE DURUZ",
                "scout_stop_action": "⏹️ HEREKETI DURUZ",
                "scout_no_diff": "Hiç hili tapawut tapylmady.",
                "scout_disc_signal": "Tapylan signal [ID 0x{id:X} | Bit {bit}] Designer-a ýüklendi.",

                # Main Window Messages & Status
                "msg_open_dbc": "DBC Faýl Açmak",
                "msg_load_log": "CAN Log Ýüklemek",
                "msg_save_proj": "Taslamany Saklamak",
                "msg_load_proj": "Taslamany Ýüklemek",
                "msg_export_dbc": "DBC Eksport Etmek",
                "msg_export_json": "JSON Eksport Etmek",
                "msg_export_csv": "CSV Eksport Etmek",
                "msg_about_title": "Programma Barada",
                "msg_ai_suggest_title": "AI Maslahaty",
                "msg_ai_explore": "AI Signal Gözlegi",
                "msg_compare_logs": "Log-lary Deňeşdirme",
                "msg_invalid_name": "Nädogry At",
                "msg_invalid_name_info": "Signal ady harp ýa-da aşaky çyzyk bilen başlamaly we diňe harplardan, sanlardan ybarat bolmaly.",
                "msg_no_can_traffic": "CAN trafik ýüklenmedi. AI ulanmak üçin ilki log ýükläň.",
                "msg_select_msg": "Ilki CAN habaryny saýlaň.",
                "status_capture_started": "📡 Real-wagt ýazgy başlandy...",
                "status_capture_stopped": "Ýazgy duruzyldy.",
                "status_switched": "{mode} režimine geçildi.",
                "mode_analysis": "Analiz Režimi",
                "mode_design": "Taslama Režimi",
                "mode_preview": "Eksport Gözden Geçirme",
                "mode_explorer": "Maglumat Binýady Explorer",
                "mode_manage": "Maglumat Binýady Dolandyryş",
                "mode_guide": "Öwreniş Merkezi",
                "mode_assistant": "Smart AI Kömekçi",

                # Defined Signals Table
                "sig_defined": "Kesgitlenen Signallar",
                "sig_remove": "Aýyr",
                "sig_show_graph": "Grafik Görkez",

                # Data Table
                "dt_title": "CAN Maglumatlary (Ýokary Öndürijilikli)",
                "dt_filter_id": "ID Filtrle:",
                "dt_all_ids": "Ähli ID-ler",
                "dt_unique": "Diňe üýtgeýänler (Unique)",
                "dt_frames_count": "{count} san",
                "dt_frames_filtered": "{count} san (Filtrlendi)",

                # Signal Editor Expanded
                "sig_search_placeholder": "meselem: Tizlik, RPM...",
                "sig_byte_order_intel": "Intel (LE)",
                "sig_byte_order_moto": "Motorola (BE)",
                "sig_type_unsigned": "Belgisiz (Unsigned)",
                "sig_type_signed": "Belgili (Signed)",
                "sig_mux": "Multiplex:",
                "sig_mux_none": "Ýok",
                "sig_val_desc": "Baha Düşündirişleri (Enum):",
                "sig_formula": "Formula: baha = raw * {scale} + {offset}",
                "sig_live_value": "Live Baha: {raw} -> Fiziki: {phys} {unit}",
                "sig_placeholder_unit": "km/s, rpm...",

                # DBC Preview
                "dbc_preview_title": "DBC Gözden Geçirme",
                "dbc_copy": "Kopiýala",
                "dbc_preview_placeholder": "DBC çykyşy şu ýerde peýda bolar...",

                # Explorer
                "db_explorer_title": "Maglumat Binýady Explorer",
                "db_explorer_search": "Gözle...",
                "db_explorer_nodes": "Dügünler (Nodes)",
                "db_explorer_msgs": "Habarlar we Signallar",
                "db_explorer_attrs": "Atributlar",
                "db_explorer_envs": "Gurşaw Üýtgeýänleri (EnvVars)",

                # Graph
                "graph_title": "Signal Grafigi",
                "graph_auto_range": "Awtomatik Ölçeg",
                "graph_axis_x": "Wagt / San",
                "graph_axis_y": "Baha",
                "graph_fallback": "Grafik görmek üçin 'pyqtgraph' gerek.\nGurmak üçin: pip install pyqtgraph",

                # Management
                # Guide
                "guide_header": "📚 DBC Professional Öwreniş Merkezi",

                "manage_nodes": "Dügünler (ECUs)",
                "manage_attrs": "Atribut Kesgitlemeleri",
                "manage_envs": "Gurşaw Üýtgeýänleri",
                "manage_add_new": "Täze {type} goş",

                # Smart Assistant
                "ai_assistant_title": "Smart AI Kömekçi",
                "ai_teach_title": "🎓 AI-a Öwret (DBC-den)",
                "ai_teach_desc": "AI-a markalara mahsus maglumatlary öwretmek üçin bar bolan DBC faýllaryňyzy ýükläň.",
                "ai_brand_placeholder": "Marka (mysal: Toyota, VW)",
                "ai_btn_train": "DBC-ni Ýükle we Öwret",
                "ai_scan_title": "🚀 Smart Reverse Scan",
                "ai_log_main": "Esasy Trafik Logy:",
                "ai_log_ref": "Bellik (Reference) Logy:",
                "ai_brand_context": "Marka Konteksti:",
                "ai_btn_run": "Smart AI Analizini Başlat",
                "ai_expert_title": "Ekspert Maslahatlary",
                "ai_select_dbc": "Öwretmek üçin DBC faýllaryny saýlaň...",
                "ai_expert_desc": "Siziň maglumat binýadyňyza we trafik analiziňize esaslanan AI maslahatlary.",
                "ai_rec_badge": "MASLAHAT BERILÝÄR",
                "ai_no_results": "Ýokary ynamly signallar tapylmady.",
                "ai_msg_train_ok": "AI '{brand}' markasy üçin {count} DBC faýlyndan üstünlikli öwrendi.",
                "ai_advice_known": "Siziň '{brand}' bilimleriňize esaslanyp, bu ID {id} ähtimal şulary saklaýar: {names}.",
                "ai_advice_detected": "AI {type} pattern-yny tapdy. ",
                "ai_advice_recommend": "Men {start}-bitden başlap {len}-bitlik signal kesgitlemegi maslahat berýärin. ",
                "ai_advice_reason": "Sebäp: {reason}.",
                "ai_advice_pattern": "'{name}' üçin '{brand}' maglumat binýadynda güýçli meňzeşlik tapyldy. Bitleriň ýerleşişi laýyk gelýär.",

                # Video panel
                "video_offset": "Süýşme (ms):",
                "video_load": "Wideo ýükle",
                "video_open_title": "Wideo faýlyny aç...",
                "video_files": "Wideo faýllary",

                # Bit Editor
                "bit_header": "Bit {n}",
                "byte_header": "Byte {n}",
                "bit_selection_info": "Saýlanan: bit {start} | uzynlygy {len}",
                "bit_editor_info": "Bitleri görmek üçin habar saýlaň",
                "bit_data_hex": "DATA HEX:",
                "bit_tip": "💡 Maslahat: Täze signal üçin bitleri mouse bilen saýlaň."
            },
            "RUS": {
                # General
                "app_name": "Анализатор CAN-шины и Генератор DBC",
                "app_version": "3.0 Professional",
                "ready": "Готов",
                "error": "Ошибка",
                "warning": "Предупреждение",
                "info": "Информация",
                "success": "Успешно",
                "loading": "Загрузка...",
                "no": "Нет",
                "yes": "Да",

                # Navigation
                "nav_analyze": "Анализ",
                "nav_design": "Дизайн",
                "nav_preview": "Просмотр",
                "nav_explorer": "Дерево DBC",
                "nav_manage": "Управление",
                "nav_guide": "Справка",
                "nav_assistant": "AI Ассистент",

                # Menus
                "menu_file": "&Файл",
                "menu_open_dbc": "Открыть DBC...",
                "menu_load_log": "Загрузить CAN лог...",
                "menu_load_video": "Синхр. видео...",
                "menu_save_project": "Сохранить проект",
                "menu_load_project": "Загрузить проект",
                "menu_export": "Экспорт",
                "menu_exit": "Выход",
                "menu_ai": "&AI Инструменты",
                "menu_detect": "Авто-детект сигналов",
                "menu_suggest": "Найти сигнал...",
                "menu_auto_dbc": "Генерация DBC через AI",
                "menu_encode": "Кодировать значения...",
                "menu_compare": "Сравнить логи...",
                "menu_hw": "&Оборудование",
                "menu_connect": "Подключиться к CAN...",
                "menu_stop": "Остановить захват",
                "menu_view": "&Вид",
                "menu_dark": "Темная/Светлая тема",
                "menu_help": "&Помощь",
                "menu_about": "О программе",

                # Cards
                "card_video": "Синхронизация видео",
                "card_traffic": "Трафик CAN-шины",
                "card_graph": "График сигналов",
                "card_console": "Системная консоль",
                "card_bit_editor": "Редактор бит",
                "card_signal_props": "Свойства сигнала",
                "card_dbc_preview": "Просмотр DBC файла",
                "card_db_explorer": "Проводник базы данных",
                "card_db_manage": "Управление базой данных DBC",
                "card_guide": "Профессиональный гид по DBC",
                "card_ai_wizard": "Помощник реверс-инжиниринга",

                # RE Scout
                "scout_title": "🛡️ RE Скаут (Поиск сигналов)",
                "scout_info": "Детекция по событиям: Сравните базовую линию (Idle) с активным действием.",
                "scout_status": "Статус: ",
                "scout_idle": "🔘 ГОТОВ",
                "scout_rec_baseline": "🟦 ЗАПИСЬ БАЗОВОЙ ЛИНИИ",
                "scout_rec_action": "🔥 ЗАПИСЬ СОБЫТИЯ (ACTION)",
                "scout_analyzing": "⌛ АНАЛИЗ...",
                "scout_complete": "✨ АНАЛИЗ ЗАВЕРШЕН",
                "scout_btn_baseline": "1. Старт Baseline",
                "scout_btn_action": "2. Старт Action",
                "scout_btn_reset": "Сбросить сессию",
                "scout_candidates": "🎯 НАЙДЕННЫЕ КАНДИДАТЫ",
                "scout_heatmap": "Тепловая карта активности бит",
                "scout_detail": "Выберите кандидата для анализа поведения бит.",
                "scout_score": "Оценка дельты",
                "scout_load_signal_tip": "Дважды щелкните, чтобы загрузить этот сигнал в Дизайнер.",

                # Signal Editor
                "sig_name": "Имя сигнала:",
                "sig_start": "Стартовый бит:",
                "sig_length": "Длина (бит):",
                "sig_byte_order": "Порядок байт:",
                "sig_type": "Тип данных:",
                "sig_scale": "Коэффициент:",
                "sig_offset": "Смещение:",
                "sig_unit": "Единица:",
                "sig_min": "Мин:",
                "sig_max": "Макс:",
                "sig_add": "Добавить сигнал",
                "sig_clear": "Очистить",

                # Column Headers
                "col_id": "ID",
                "col_dlc": "DLC",
                "col_data": "Данные (Hex)",
                "col_timestamp": "Время",
                "col_msg": "Сообщение",
                "col_sig": "Сигнал",
                "col_bits": "Биты",

                # Theme
                "theme_toggle": "Переключить тему",
                "lang_toggle": "Выбрать язык",

                # Hardware Dialog
                "hw_title": "Подключение к оборудования CAN",
                "hw_settings": "Настройки оборудования",
                "hw_interface": "Интерфейс:",
                "hw_channel": "Канал:",
                "hw_bitrate": "Скорость (Bitrate):",
                "hw_logging": "Логирование и сохранение",
                "hw_autosave": "Авто-сохранение (.txt + .csv)",
                "hw_listen_only": "Только прослушивание (Passive)",

                # Console
                "console_title": "Системные логи и консоль",
                "console_clear": "Очистить",

                # Additional RE Scout
                "scout_stop_baseline": "⏹️ СТОП BASELINE",
                "scout_stop_action": "⏹️ СТОП ACTION",
                "scout_no_diff": "Значимых различий не обнаружено.",
                "scout_disc_signal": "Обнаруженный сигнал [ID 0x{id:X} | Бит {bit}] загружен в Дизайнер.",

                # Main Window Messages & Status
                "msg_open_dbc": "Открыть DBC файл",
                "msg_load_log": "Загрузить CAN лог",
                "msg_save_proj": "Сохранить проект",
                "msg_load_proj": "Загрузить проект",
                "msg_export_dbc": "Экспорт DBC",
                "msg_export_json": "Экспорт JSON",
                "msg_export_csv": "Экспорт CSV",
                "msg_about_title": "О программе",
                "msg_ai_suggest_title": "AI Предложение",
                "msg_ai_explore": "AI Поиск сигналов",
                "msg_compare_logs": "Сравнение логов",
                "msg_invalid_name": "Недопустимое имя",
                "msg_invalid_name_info": "Имя сигнала должно начинаться с буквы или подчеркивания и содержать только буквы и цифры.",
                "msg_no_can_traffic": "CAN трафик не загружен. Сначала загрузите лог.",
                "msg_select_msg": "Сначала выберите CAN сообщение.",
                "status_capture_started": "📡 Захват в реальном времени запущен...",
                "status_capture_stopped": "Захват остановлен.",
                "status_switched": "Переключено в {mode}",
                "mode_analysis": "Режим Анализа",
                "mode_design": "Режим Проектирования",
                "mode_preview": "Предпросмотр Экспорта",
                "mode_explorer": "Проводник Базы Данных",
                "mode_manage": "Управление Базой Данных",
                "mode_guide": "Центр Обучения",
                "mode_assistant": "Smart AI Ассистент",

                # Defined Signals Table
                "sig_defined": "Определенные сигналы",
                "sig_remove": "Удалить",
                "sig_show_graph": "Показать график",

                # Data Table
                "dt_title": "CAN Данные (Высокая производительность)",
                "dt_filter_id": "Фильтр ID:",
                "dt_all_ids": "Все ID",
                "dt_unique": "Только уникальные",
                "dt_frames_count": "{count} кадров",
                "dt_frames_filtered": "{count} кадров (Фильтр)",

                # Signal Editor Expanded
                "sig_search_placeholder": "напр. Скорость, Обороты...",
                "sig_byte_order_intel": "Intel (LE)",
                "sig_byte_order_moto": "Motorola (BE)",
                "sig_type_unsigned": "Беззнаковый",
                "sig_type_signed": "Знаковый",
                "sig_mux": "Мультиплекс:",
                "sig_mux_none": "Нет",
                "sig_val_desc": "Описания значений (Enum):",
                "sig_formula": "Формула: знач-е = raw * {scale} + {offset}",
                "sig_live_value": "Тек. значение: {raw} -> Физ: {phys} {unit}",
                "sig_placeholder_unit": "км/ч, об/мин...",

                # DBC Preview
                "dbc_preview_title": "Просмотр DBC",
                "dbc_copy": "Копировать",
                "dbc_preview_placeholder": "Здесь появится DBC код...",

                # Explorer
                "db_explorer_title": "Проводник БД",
                "db_explorer_search": "Поиск по базе...",
                "db_explorer_nodes": "Узлы (Nodes)",
                "db_explorer_msgs": "Сообщения и Сигналы",
                "db_explorer_attrs": "Атрибуты",
                "db_explorer_envs": "Переменные окружения",

                # Graph
                "graph_title": "График сигналов",
                "graph_auto_range": "Авто-масштаб",
                "graph_axis_x": "Время / Отсчеты",
                "graph_axis_y": "Значение",
                "graph_fallback": "Для графиков требуется 'pyqtgraph'.\nУстановка: pip install pyqtgraph",

                # Management
                # Guide
                "guide_header": "📚 Профессиональный центр обучения DBC",

                "manage_nodes": "Узлы (ECUs)",
                "manage_attrs": "Определения атрибутов",
                "manage_envs": "Переменные окружения",
                "manage_add_new": "Добавить {type}",

                # Smart Assistant
                "ai_assistant_title": "Smart AI Ассистент",
                "ai_teach_title": "🎓 Обучить AI (из DBC)",
                "ai_teach_desc": "Загрузите существующие DBC для обучения AI паттернам конкретных брендов.",
                "ai_brand_placeholder": "Бренд (напр., Toyota, VW)",
                "ai_btn_train": "Загрузить и обучить DBC",
                "ai_scan_title": "🚀 Умное обратное сканирование",
                "ai_log_main": "Основной лог трафика:",
                "ai_log_ref": "Эталонный лог (Reference):",
                "ai_brand_context": "Контекст бренда:",
                "ai_btn_run": "Запустить Smart AI анализ",
                "ai_expert_title": "Экспертные рекомендации",
                "ai_select_dbc": "Выберите DBC файлы для обучения...",
                "ai_expert_desc": "Профессиональные выводы AI на основе базы знаний и анализа трафика.",
                "ai_rec_badge": "РЕКОМЕНДОВАНО",
                "ai_no_results": "Высокоточных сигналов не найдено.",
                "ai_msg_train_ok": "AI успешно обучен на {count} DBC файлах для бренда '{brand}'.",
                "ai_advice_known": "На основе ваших знаний о '{brand}', этот ID {id}, вероятно, содержит: {names}.",
                "ai_advice_detected": "AI обнаружил паттерн {type}. ",
                "ai_advice_recommend": "Я рекомендую определить {len}-битный сигнал, начиная с бита {start}. ",
                "ai_advice_reason": "Причина: {reason}.",
                "ai_advice_pattern": "Найдено сильное совпадение для '{name}' в базе знаний '{brand}'. Сетка бит совпадает.",

                # Video panel
                "video_offset": "Смещение (мс):",
                "video_load": "Загрузить видео",
                "video_open_title": "Открыть видео...",
                "video_files": "Видео файлы",

                # Bit Editor
                "bit_header": "Бит {n}",
                "byte_header": "Байт {n}",
                "bit_selection_info": "Выбрано: бит {start} | длина {len}",
                "bit_editor_info": "Выберите сообщение для просмотра бит",
                "bit_data_hex": "HEX ДАННЫЕ:",
                "bit_tip": "💡 Подсказка: Выделите биты мышкой для создания сигнала."
            },
            "ENG": {
                # General
                "app_name": "CAN Bus Analyzer & DBC Generator",
                "app_version": "3.0 Professional",
                "ready": "Ready",
                "error": "Error",
                "warning": "Warning",
                "info": "Information",
                "success": "Success",
                "loading": "Loading...",
                "no": "No",
                "yes": "Yes",

                # Navigation
                "nav_analyze": "Analyze",
                "nav_design": "Design",
                "nav_preview": "Preview",
                "nav_explorer": "DBC Tree",
                "nav_manage": "Manage",
                "nav_guide": "Guide",
                "nav_assistant": "Assistant",

                # Menus
                "menu_file": "&File",
                "menu_open_dbc": "Open DBC...",
                "menu_load_log": "Load CAN Log...",
                "menu_load_video": "Load Video Sync...",
                "menu_save_project": "Save Project",
                "menu_load_project": "Load Project",
                "menu_export": "Export",
                "menu_exit": "Exit",
                "menu_ai": "&AI Tools",
                "menu_detect": "Auto Detect Signals",
                "menu_suggest": "Find Signal...",
                "menu_auto_dbc": "Auto Generate DBC",
                "menu_encode": "Encode Signal Values...",
                "menu_compare": "Compare Logs...",
                "menu_hw": "&Hardware",
                "menu_connect": "Connect to CAN...",
                "menu_stop": "Stop Live Capture",
                "menu_view": "&View",
                "menu_dark": "Dark/Light Mode",
                "menu_help": "&Help",
                "menu_about": "About",

                # Cards
                "card_video": "Video Sync",
                "card_traffic": "CAN Bus Traffic",
                "card_graph": "Signal Graph",
                "card_console": "System Console",
                "card_bit_editor": "Bit Layout Editor",
                "card_signal_props": "Signal Properties",
                "card_dbc_preview": "DBC File Preview",
                "card_db_explorer": "Database Explorer",
                "card_db_manage": "Database Management",
                "card_guide": "DBC Professional Guide",
                "card_ai_wizard": "RE Smart Assistant",

                # RE Scout
                "scout_title": "🛡️ RE Scout",
                "scout_info": "Event-based discovery: Compare Baseline (Idle) with Action recording.",
                "scout_status": "Status: ",
                "scout_idle": "🔘 READY",
                "scout_rec_baseline": "🟦 RECORDING BASELINE",
                "scout_rec_action": "🔥 RECORDING ACTION",
                "scout_analyzing": "⌛ ANALYZING...",
                "scout_complete": "✨ ANALYSIS COMPLETE",
                "scout_btn_baseline": "1. Start Baseline",
                "scout_btn_action": "2. Start Action",
                "scout_btn_reset": "Reset Session",
                "scout_candidates": "🎯 DISCOVERED CANDIDATES",
                "scout_heatmap": "Bit activity heatmap",
                "scout_detail": "Select a candidate to analyze bit behavior.",
                "scout_score": "Delta Score",
                "scout_load_signal_tip": "Double-click to load this signal into the Designer.",

                # Signal Editor
                "sig_name": "Signal Name:",
                "sig_start": "Start Bit:",
                "sig_length": "Length:",
                "sig_byte_order": "Byte Order:",
                "sig_type": "Value Type:",
                "sig_scale": "Scale:",
                "sig_offset": "Offset:",
                "sig_unit": "Unit:",
                "sig_min": "Min:",
                "sig_max": "Max:",
                "sig_add": "Add Signal",
                "sig_clear": "Clear",

                # Column Headers
                "col_id": "ID",
                "col_dlc": "DLC",
                "col_data": "Data (Hex)",
                "col_timestamp": "Timestamp",
                "col_msg": "Message",
                "col_sig": "Signal",
                "col_bits": "Bits",

                # Theme
                "theme_toggle": "Toggle Theme",
                "lang_toggle": "Select Language",

                # Hardware Dialog
                "hw_title": "Connect to CAN Hardware",
                "hw_settings": "Hardware Settings",
                "hw_interface": "Interface:",
                "hw_channel": "Channel:",
                "hw_bitrate": "Bitrate:",
                "hw_logging": "Logging & Persistence",
                "hw_autosave": "Auto-save to file (.txt + .csv)",
                "hw_listen_only": "Listen Only Mode (Passive)",

                # Console
                "console_title": "System Logs & Console",
                "console_clear": "Clear",

                # Additional RE Scout
                "scout_stop_baseline": "⏹️ STOP BASELINE",
                "scout_stop_action": "⏹️ STOP ACTION",
                "scout_no_diff": "No significant differences found.",
                "scout_disc_signal": "Discovered signal [ID 0x{id:X} | Bit {bit}] loaded into Designer.",

                # Main Window Messages & Status
                "msg_open_dbc": "Open DBC File",
                "msg_load_log": "Load CAN Log",
                "msg_save_proj": "Save Project",
                "msg_load_proj": "Load Project",
                "msg_export_dbc": "Export DBC",
                "msg_export_json": "Export JSON",
                "msg_export_csv": "Export CSV",
                "msg_about_title": "About",
                "msg_ai_suggest_title": "AI Suggest",
                "msg_ai_explore": "AI Signal Exploration",
                "msg_compare_logs": "Compare Logs",
                "msg_invalid_name": "Invalid Name",
                "msg_invalid_name_info": "Signal name must start with a letter or underscore and contain only letters, digits, and underscores.",
                "msg_no_can_traffic": "No CAN traffic loaded. Load a CAN log first.",
                "msg_select_msg": "Please select a CAN message first.",
                "status_capture_started": "📡 Real-time capture started...",
                "status_capture_stopped": "Capture stopped.",
                "status_switched": "Switched to {mode}",
                "mode_analysis": "Analysis Mode",
                "mode_design": "Design Mode",
                "mode_preview": "Export Preview",
                "mode_explorer": "Database Explorer",
                "mode_manage": "Database Management",
                "mode_guide": "Learning Center",
                "mode_assistant": "Smart Assistant",

                # Defined Signals Table
                "sig_defined": "Defined Signals",
                "sig_remove": "Remove",
                "sig_show_graph": "Show Graph",

                # Data Table
                "dt_title": "CAN Data (High Performance)",
                "dt_filter_id": "Filter ID:",
                "dt_all_ids": "All IDs",
                "dt_unique": "Unique only",
                "dt_frames_count": "{count} frames",
                "dt_frames_filtered": "{count} frames (Filtered)",

                # Signal Editor Expanded
                "sig_search_placeholder": "e.g. EngineRPM, BatteryVoltage...",
                "sig_byte_order_intel": "Intel (LE)",
                "sig_byte_order_moto": "Motorola (BE)",
                "sig_type_unsigned": "Unsigned",
                "sig_type_signed": "Signed",
                "sig_mux": "Multiplex:",
                "sig_mux_none": "None",
                "sig_val_desc": "Value Descriptions (Enum):",
                "sig_formula": "Formula: value = raw * {scale} + {offset}",
                "sig_live_value": "Live Value: {raw} -> Physical: {phys} {unit}",
                "sig_placeholder_unit": "km/h, rpm...",

                # DBC Preview
                "dbc_preview_title": "DBC Preview",
                "dbc_copy": "Copy",
                "dbc_preview_placeholder": "DBC output will appear here...",

                # Explorer
                "db_explorer_title": "Database Explorer",
                "db_explorer_search": "Search database...",
                "db_explorer_nodes": "Nodes",
                "db_explorer_msgs": "Messages & Signals",
                "db_explorer_attrs": "Attributes",
                "db_explorer_envs": "Environment Variables",

                # Graph
                "graph_title": "Signal Graph",
                "graph_auto_range": "Auto Range",
                "graph_axis_x": "Time / Samples",
                "graph_axis_y": "Value",
                "graph_fallback": "Graph visualization requires 'pyqtgraph'.\nInstall: pip install pyqtgraph",

                # Management
                # Guide
                "guide_header": "📚 DBC Professional Learning Center",

                "manage_nodes": "Nodes (ECUs)",
                "manage_attrs": "Attribute Definitions",
                "manage_envs": "Environment Variables",
                "manage_add_new": "Add New {type}",

                # Smart Assistant
                "ai_assistant_title": "Smart AI Assistant",
                "ai_teach_title": "🎓 Teach AI (Train from DBC)",
                "ai_teach_desc": "Upload your existing DBCs to teach the AI brand-specific patterns.",
                "ai_brand_placeholder": "Brand (e.g., Toyota, VW)",
                "ai_btn_train": "Load & Train DBC",
                "ai_scan_title": "🚀 Smart Reverse Scan",
                "ai_log_main": "Main Traffic Log:",
                "ai_log_ref": "Reference Log:",
                "ai_brand_context": "Target Brand Context:",
                "ai_btn_run": "Run Smart AI Analysis",
                "ai_expert_title": "Expert Recommendations",
                "ai_select_dbc": "Select DBC files to learn from...",
                "ai_expert_desc": "AI insights based on your knowledge base and traffic analysis.",
                "ai_rec_badge": "RECOMMENDED",
                "ai_no_results": "No high-confidence signals found.",
                "ai_msg_train_ok": "AI successfully learned from {count} DBC files for brand '{brand}'.",
                "ai_advice_known": "Based on your '{brand}' knowledge, this ID {id} likely contains: {names}. ",
                "ai_advice_detected": "AI detected a {type} pattern. ",
                "ai_advice_recommend": "I recommend defining a {len}-bit signal starting at bit {start}. ",
                "ai_advice_reason": "Reason: {reason}.",
                "ai_advice_pattern": "Strong pattern match for '{name}' from {brand} knowledge base. Bit alignment found.",

                # Video panel
                "video_offset": "Offset (ms):",
                "video_load": "Load Video",
                "video_open_title": "Open Video...",
                "video_files": "Video Files",

                # Bit Editor
                "bit_header": "Bit {n}",
                "byte_header": "Byte {n}",
                "bit_selection_info": "Selected: bit {start} | length {len}",
                "bit_editor_info": "Select a message to view bit layout",
                "bit_data_hex": "DATA HEX:",
                "bit_tip": "💡 Tip: Click and drag to select bits for a new signal."
            }
        }

    def set_language(self, lang: str):
        if lang in self._translations:
            self._current_lang = lang
            self.language_changed.emit(lang)

    def t(self, key: str) -> str:
        """Translates a key based on current language."""
        return self._translations[self._current_lang].get(key, key)

    def current_language(self) -> str:
        return self._current_lang

# Global singleton instance
I18N = Translator()
