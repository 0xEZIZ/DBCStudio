"""
async_loader.py - Async File Loading System
QThread-based file loader, UI freeze-siz uly faýllary ýüklemek üçin.
Progress bar we error handling goldawy bar.
"""

from PyQt5.QtCore import QThread, pyqtSignal, QObject


class FileLoaderWorker(QThread):
    """
    Background thread-de faýl ýükleýän worker.
    DBC, CAN log, JSON faýllar üçin ulanylýar.

    Signals:
        progress(int): 0-100 aralygynda progress
        finished(object): Netije obýekti (DBCDatabase, list, dict, ...)
        error(str): Hata habary
        status(str): Status teksti
    """

    progress = pyqtSignal(int)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    status = pyqtSignal(str)

    # Load types
    LOAD_DBC = "dbc"
    LOAD_CAN_LOG = "can_log"
    LOAD_JSON = "json"
    LOAD_PROJECT = "project"

    def __init__(self, filepath: str, load_type: str, parent=None):
        super().__init__(parent)
        self.filepath = filepath
        self.load_type = load_type
        self._cancelled = False

    def cancel(self):
        """Ýüklemäni ýatyrýar."""
        self._cancelled = True

    def run(self):
        """Background thread-de ýüklemäni ýerine ýetirýär."""
        try:
            if self.load_type == self.LOAD_DBC:
                self._load_dbc()
            elif self.load_type == self.LOAD_CAN_LOG:
                self._load_can_log()
            elif self.load_type == self.LOAD_JSON:
                self._load_json()
            elif self.load_type == self.LOAD_PROJECT:
                self._load_project()
            else:
                self.error.emit(f"Unknown load type: {self.load_type}")
        except Exception as e:
            self.error.emit(f"Loading error: {str(e)}")

    def _load_dbc(self):
        """DBC faýly ýükleýär."""
        self.status.emit("Parsing DBC file...")
        self.progress.emit(10)

        from parser import DBCParser
        parser = DBCParser()

        self.progress.emit(30)
        if self._cancelled:
            return

        database = parser.parse_file(self.filepath)
        self.progress.emit(90)

        if self._cancelled:
            return

        self.progress.emit(100)
        self.finished.emit(database)

    def _load_can_log(self):
        """CAN log faýly ýükleýär."""
        self.status.emit("Loading CAN log...")
        self.progress.emit(5)

        from analyzer import CANDumpParser
        dump_parser = CANDumpParser()

        self.progress.emit(10)
        if self._cancelled:
            return

        # Parse file with progress tracking
        frames = dump_parser.parse_file(self.filepath)

        self.progress.emit(80)
        if self._cancelled:
            return

        # Convert to tuples
        result = [(f.timestamp, f.can_id, f.data) for f in frames]

        self.progress.emit(100)
        self.finished.emit(result)

    def _load_json(self):
        """JSON faýly ýükleýär."""
        self.status.emit("Loading JSON...")
        self.progress.emit(20)

        from models import DBCDatabase
        database = DBCDatabase.import_json(self.filepath)

        self.progress.emit(100)
        self.finished.emit(database)

    def _load_project(self):
        """Project faýly ýükleýär."""
        import json
        self.status.emit("Loading project...")
        self.progress.emit(20)

        with open(self.filepath, "r", encoding="utf-8") as f:
            project = json.load(f)

        self.progress.emit(100)
        self.finished.emit(project)


class AsyncFileLoader(QObject):
    """
    Async file loader manager.
    Worker-lary dolandyrýar we UI bilen baglanyşdyrýar.

    Mysal:
        loader = AsyncFileLoader()
        loader.load_started.connect(lambda: statusbar.setText("Loading..."))
        loader.load_finished.connect(on_loaded)
        loader.load_error.connect(on_error)
        loader.load_progress.connect(progressbar.setValue)

        loader.load_file("data.dbc", FileLoaderWorker.LOAD_DBC)
    """

    load_started = pyqtSignal()
    load_finished = pyqtSignal(object)
    load_error = pyqtSignal(str)
    load_progress = pyqtSignal(int)
    load_status = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: FileLoaderWorker = None

    def load_file(self, filepath: str, load_type: str):
        """Faýly async ýüklemäni başlaýar."""
        # Öňki worker-y ýatyr
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
            self._worker.wait(2000)

        self._worker = FileLoaderWorker(filepath, load_type)
        self._worker.progress.connect(self.load_progress.emit)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.status.connect(self.load_status.emit)

        self.load_started.emit()
        self._worker.start()

    def cancel(self):
        """Häzirki ýüklemäni ýatyrýar."""
        if self._worker and self._worker.isRunning():
            self._worker.cancel()

    def is_loading(self) -> bool:
        """Ýüklenýärmi barlaýar."""
        return self._worker is not None and self._worker.isRunning()

    def _on_finished(self, result):
        """Worker gutaranda."""
        self.load_finished.emit(result)

    def _on_error(self, error_msg: str):
        """Worker hata berende."""
        self.load_error.emit(error_msg)
