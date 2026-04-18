"""
hardware/bus_interface.py - Base Abstract Class for CAN Interfaces
Hardware-den garaşsyz CAN aragatnaşygyny dolandyrýar.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from analyzer import CANFrame

class BaseBusInterface(ABC):
    """
    Hemme CAN interfeýsleri (IXXAT, Virtual, SocketCAN) üçin esasy klas.
    """

    @abstractmethod
    def connect(self, bitrate: int, channel: int) -> bool:
        """Hardware-e birleşýär."""
        pass

    @abstractmethod
    def disconnect(self):
        """Hardware baglanyşygyny kesýär."""
        pass

    @abstractmethod
    def recv_frame(self, timeout: float = 0.1) -> Optional[CANFrame]:
        """Bus-dan bir frame okaýar."""
        pass

    @abstractmethod
    def send_frame(self, can_id: int, data: bytes) -> bool:
        """Bus-a bir frame iberýär."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Baglanyşygyň barlygyny barlaýar."""
        pass
