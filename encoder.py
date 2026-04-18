"""
encoder.py - CAN Signal Encoder/Decoder (Professional Edition)
Signal bahalaryny CAN frame baýtlaryna encode edýär (we tersine decode).
Intel (little-endian) we Motorola (big-endian) byte order goldawy bar.
"""

from typing import Dict, List, Optional, Tuple
from models import Signal, Message


class CANEncoder:
    """
    CAN Signal Encoder — fiziki bahalary raw CAN frame-e öwürýär.

    Mysal:
        encoder = CANEncoder()
        data = encoder.encode_message(msg, {"VehicleSpeed": 100.0})
        # -> bytes: b'\\x10\\x27\\x00...'
    """

    def encode_message(
        self,
        message: Message,
        signal_values: Dict[str, float],
        base_data: Optional[bytes] = None
    ) -> bytes:
        """
        Message üçin signal bahalaryny encode edýär.

        Args:
            message: Target Message obýekti
            signal_values: {signal_name: physical_value} dict
            base_data: Esasy data (üstünde ýazmak üçin). None bolsa noldan başlaýar.

        Returns:
            Encoded CAN frame bytes (message.dlc uzynlykda)
        """
        data = bytearray(base_data) if base_data else bytearray(message.dlc)

        # Ensure data is at least DLC length
        while len(data) < message.dlc:
            data.append(0)

        for sig_name, physical_value in signal_values.items():
            signal = message.get_signal(sig_name)
            if signal is None:
                raise ValueError(
                    f"Signal '{sig_name}' not found in message '{message.name}'"
                )
            raw = self._physical_to_raw(signal, physical_value)
            self._pack_value(data, signal, raw)

        return bytes(data[:message.dlc])

    def encode_signal(
        self,
        signal: Signal,
        physical_value: float
    ) -> Tuple[int, int, int, str]:
        """
        Bir signal-y encode edýär we parametrleri gaýtarýar.

        Returns:
            (raw_value, start_bit, length, byte_order)
        """
        raw = self._physical_to_raw(signal, physical_value)
        return (raw, signal.start_bit, signal.length, signal.byte_order)

    def decode_message(
        self,
        message: Message,
        data: bytes,
        signal_names: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        CAN frame data-dan signal-lary decode edýär (MUX goldawy bilen).
        """
        results = {}
        
        # 1. Multiplexer signal-y tap we bahany al
        mux_val = None
        mux_sig = message.get_multiplexer_signal()
        if mux_sig:
            mux_val = int(self._extract_raw_value(data, mux_sig))
            results[mux_sig.name] = float(mux_val)

        # 2. Degişli signal-lary tap (static + matching mux)
        signals = message.get_signals_for_mux(mux_val)

        if signal_names:
            signals = [s for s in signals if s.name in signal_names]

        for signal in signals:
            if signal.is_multiplexer:
                continue # Eýýäm tapyldy
                
            raw = self._extract_raw_value(data, signal)

            # Handle signed values
            if signal.value_type == "signed":
                if raw >= (1 << (signal.length - 1)):
                    raw -= (1 << signal.length)

            physical = raw * signal.scale + signal.offset
            results[signal.name] = physical

        return results

    def decode_signal(
        self,
        signal: Signal,
        data: bytes
    ) -> float:
        """Bir signal-y decode edýär."""
        raw = self._extract_raw_value(data, signal)

        if signal.value_type == "signed":
            if raw >= (1 << (signal.length - 1)):
                raw -= (1 << signal.length)

        return raw * signal.scale + signal.offset

    # ═══════════════════════════════════════════════════════════
    #  Internal Methods
    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _physical_to_raw(signal: Signal, physical: float) -> int:
        """
        Fiziki bahany raw integer-e öwürýär.
        Formula: raw = round((physical - offset) / scale)
        """
        if signal.scale == 0:
            return 0

        raw = round((physical - signal.offset) / signal.scale)

        # Clamp to bit range
        max_val = (1 << signal.length) - 1
        if signal.value_type == "signed":
            min_val = -(1 << (signal.length - 1))
            max_val = (1 << (signal.length - 1)) - 1
            raw = max(min_val, min(max_val, raw))
            if raw < 0:
                raw += (1 << signal.length)  # Two's complement
        else:
            raw = max(0, min(max_val, raw))

        return raw

    def _pack_value(self, data: bytearray, signal: Signal, raw: int):
        """Raw bahany data bytearray-yna ýazýar."""
        if signal.byte_order == "little_endian":
            self._pack_value_intel(data, signal.start_bit, signal.length, raw)
        else:
            self._pack_value_motorola(data, signal.start_bit, signal.length, raw)

    @staticmethod
    def _pack_value_intel(
        data: bytearray,
        start_bit: int,
        length: int,
        raw: int
    ):
        """
        Intel (Little Endian) byte order encode.
        LSB bit = start_bit, bitler ýokary tarapa ösýär.
        """
        for i in range(length):
            bit_idx = start_bit + i
            byte_idx = bit_idx // 8
            bit_pos = bit_idx % 8

            if byte_idx < len(data):
                if raw & (1 << i):
                    data[byte_idx] |= (1 << bit_pos)
                else:
                    data[byte_idx] &= ~(1 << bit_pos)

    @staticmethod
    def _pack_value_motorola(
        data: bytearray,
        start_bit: int,
        length: int,
        raw: int
    ):
        """
        Motorola (Big Endian) byte order encode.
        MSB bit = start_bit, bitler aşak tarapa gidýär.
        """
        byte_idx = start_bit // 8
        bit_in_byte = start_bit % 8

        for i in range(length):
            if byte_idx < len(data):
                if raw & (1 << (length - 1 - i)):
                    data[byte_idx] |= (1 << bit_in_byte)
                else:
                    data[byte_idx] &= ~(1 << bit_in_byte)

            if bit_in_byte == 0:
                byte_idx += 1
                bit_in_byte = 7
            else:
                bit_in_byte -= 1

    def _extract_raw_value(self, data: bytes, signal: Signal) -> int:
        """Data-dan raw bit bahany çykaryp alýar."""
        if signal.byte_order == "little_endian":
            return self._unpack_value_intel(
                data, signal.start_bit, signal.length
            )
        else:
            return self._unpack_value_motorola(
                data, signal.start_bit, signal.length
            )

    @staticmethod
    def _unpack_value_intel(data: bytes, start_bit: int, length: int) -> int:
        """Intel byte order decode."""
        value = 0
        for i in range(length):
            bit_idx = start_bit + i
            byte_idx = bit_idx // 8
            bit_pos = bit_idx % 8
            if byte_idx < len(data):
                if data[byte_idx] & (1 << bit_pos):
                    value |= (1 << i)
        return value

    @staticmethod
    def _unpack_value_motorola(data: bytes, start_bit: int, length: int) -> int:
        """Motorola byte order decode."""
        value = 0
        byte_idx = start_bit // 8
        bit_in_byte = start_bit % 8

        for i in range(length):
            if byte_idx < len(data):
                if data[byte_idx] & (1 << bit_in_byte):
                    value |= (1 << (length - 1 - i))

            if bit_in_byte == 0:
                byte_idx += 1
                bit_in_byte = 7
            else:
                bit_in_byte -= 1

        return value


# ═══════════════════════════════════════════════════════════════
#  Convenience Functions
# ═══════════════════════════════════════════════════════════════

def encode_message(message: Message, signal_values: Dict[str, float]) -> bytes:
    """Message signal-laryny encode etmek üçin ýönekeý funksiýa."""
    encoder = CANEncoder()
    return encoder.encode_message(message, signal_values)


def decode_message(message: Message, data: bytes) -> Dict[str, float]:
    """Message signal-laryny decode etmek üçin ýönekeý funksiýa."""
    encoder = CANEncoder()
    return encoder.decode_message(message, data)
