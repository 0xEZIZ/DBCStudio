"""
hardware/ixxat_interface.py - IXXAT VCI Implementation
python-can kitaphanasyny ulanyp IXXAT adapterleri bilen işleýär.
"""

import can
import time
from typing import Optional
from core.logger_config import get_logger
from hardware.bus_interface import BaseBusInterface
from logic.analyzer import CANFrame

logger = get_logger("IXXAT")

class IxxatInterface(BaseBusInterface):
    """
    IXXAT USB-to-CAN adapterleri üçin VCI backend.
    """

    def __init__(self):
        self.bus = None
        self._connected = False

    def connect(self, bitrate: int = 500000, channel: int = 0) -> bool:
        """
        IXXAT adapterine birikýär.
        Bitrate: 1000000, 500000, 250000, etc.
        """
        try:
            # python-can IXXAT backend
            self.bus = can.Bus(
                interface='ixxat',
                channel=channel,
                bitrate=bitrate
            )
            self._connected = True
            logger.info(f"Connected to IXXAT channel {channel} at {bitrate} bps")
            return True
        except Exception as e:
            logger.error(f"Connect error: {e}")
            self._connected = False
            return False

    def disconnect(self):
        if self.bus:
            self.bus.shutdown()
            self.bus = None
        self._connected = False

    def recv_frame(self, timeout: float = 0.1) -> Optional[CANFrame]:
        """Bus-dan maglumat okaýar we CANFrame-e öwürýär."""
        if not self.bus:
            return None
        
        try:
            msg = self.bus.recv(timeout)
            if msg:
                # can.Message -> analyzer.CANFrame
                return CANFrame(
                    timestamp=msg.timestamp,
                    can_id=msg.arbitration_id,
                    data=bytes(msg.data)
                )
        except Exception as e:
            # Diňe kritiki ýalňyşlyklary logla
            if "not found" not in str(e).lower():
                logger.error(f"Recv error: {e}")
        
        return None

    def send_frame(self, can_id: int, data: bytes) -> bool:
        if not self.bus:
            return False
        
        try:
            msg = can.Message(
                arbitration_id=can_id,
                data=data,
                is_extended_id=(can_id > 0x7FF)
            )
            self.bus.send(msg)
            return True
        except Exception as e:
            print(f"[!] IXXAT Send Error: {e}")
            return False

    def is_connected(self) -> bool:
        return self._connected
