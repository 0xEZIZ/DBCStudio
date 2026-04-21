"""
hardware/can_worker.py - Real-time CAN Receiver Thread
IXXAT-dan maglumatlary okaýar we UI/Logger-e iberýär.
"""

from PyQt5.QtCore import QThread, pyqtSignal
from hardware.bus_interface import BaseBusInterface
from hardware.loggers import DualLogger
from core.logger_config import get_logger

logger = get_logger("CANWorker")

class CANReceiverWorker(QThread):
    """
    CAN maglumatlaryny okaýan background sütün.
    UI-yň doňmazlygy üçin batching ulanýar.
    """
    frame_received = pyqtSignal(list) # List of CANFrame for batching
    error_occurred = pyqtSignal(str)

    def __init__(self, interface: BaseBusInterface, logger_ui: DualLogger = None):
        super().__init__()
        self.interface = interface
        self.logger_ui = logger_ui # This is the file logger (DualLogger)
        self.running = True
        self.batch_size = 50
        self.refresh_rate = 0.04 # 40ms (~25 FPS)

    def run(self):
        """Esasy diňleýiş düwnügi."""
        logger.info("CAN Receiver thread started.")
        buffer = []
        last_ui_update = time.time()

        while self.running:
            try:
                # 1. Hardware-den oka
                frame = self.interface.recv_frame(timeout=0.01)
                
                if frame:
                    # 2. File-a ýaz (Zero lag)
                    if self.logger_ui:
                        self.logger_ui.log_frame(frame)
                    
                    # 3. UI buffer-e goş
                    buffer.append(frame)

                # 4. UI-y täzelemek (Batching)
                now = time.time()
                if (len(buffer) >= self.batch_size) or (now - last_ui_update >= self.refresh_rate):
                    if buffer:
                        self.frame_received.emit(buffer)
                        buffer = []
                        last_ui_update = now
                        # Logger buffer-laryny hem diske ýaz
                        if self.logger_ui:
                            self.logger_ui.flush()

            except Exception as e:
                logger.error(f"Worker critical error: {e}")
                self.error_occurred.emit(str(e))
                self.running = False

        # Cleanup
        if self.logger_ui:
            self.logger_ui.close()
        self.interface.disconnect()
        logger.info("CAN Receiver thread stopped.")

    def stop(self):
        self.running = False
        self.wait()
