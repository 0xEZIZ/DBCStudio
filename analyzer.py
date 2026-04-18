"""
analyzer.py - CAN Dump Analyzer
CAN log (dump) faýllaryny analiz edýär we reverse engineering prosesine kömek edýär.
User interaktiw usulda signal-lary kesgitläp, DBC döredip bilýär.
"""

import re
import csv
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from models import Signal, Message, DBCDatabase
from generator import DBCGenerator
from encoder import CANEncoder


class CANFrame:
    """Bir CAN frame-ini görkezýär."""

    def __init__(self, timestamp: float, can_id: int, data: bytes):
        self.timestamp = timestamp
        self.can_id = can_id
        self.data = data

    @property
    def dlc(self) -> int:
        return len(self.data)

    def get_bits(self) -> str:
        """Data-ny bit string görnüşinde gaýtarýar."""
        return "".join(f"{byte:08b}" for byte in self.data)

    def get_hex(self) -> str:
        """Data-ny hex string görnüşinde gaýtarýar."""
        return " ".join(f"{byte:02X}" for byte in self.data)

    def __repr__(self) -> str:
        return f"CANFrame(id=0x{self.can_id:03X}, data={self.get_hex()})"


class CANDumpParser:
    """Dürli formatdaky CAN dump faýllaryny parse edýär."""

    # Goldanýan formatlar üçin regex patternler
    # Format 1: timestamp ID#DATA (candump format)
    # Mysal: (1620000000.000000) can0 123#DEADBEEF01020304
    RE_CANDUMP = re.compile(
        r'\((\d+\.\d+)\)\s+\w+\s+([0-9A-Fa-f]+)#([0-9A-Fa-f]*)'
    )

    # Format 2: timestamp,ID,DLC,D0,D1,...,D7 (CSV format)
    # Mysal: 0.000,0x123,8,DE,AD,BE,EF,01,02,03,04

    # Format 3: ýönekeý text format
    # Mysal: 123  [8]  DE AD BE EF 01 02 03 04
    RE_SIMPLE = re.compile(
        r'([0-9A-Fa-f]{3,8})\s+\[(\d)\]\s+((?:[0-9A-Fa-f]{2}\s*)+)'
    )

    # Format 4: timestamp + simple
    # Mysal: 0.000000 123  [8]  DE AD BE EF 01 02 03 04
    RE_TIMESTAMP_SIMPLE = re.compile(
        r'(\d+\.?\d*)\s+([0-9A-Fa-f]{3,8})\s+\[(\d)\]\s+((?:[0-9A-Fa-f]{2}\s*)+)'
    )

    def parse_file(self, filepath: str) -> List[CANFrame]:
        """CAN dump faýly okaýar we CANFrame listini gaýtarýar."""
        frames = []

        # CSV faýlmy barla
        if filepath.lower().endswith(".csv"):
            return self._parse_csv(filepath)

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        for line in lines:
            frame = self._parse_line(line.strip())
            if frame:
                frames.append(frame)

        if not frames:
            print("[!] Hiç bir CAN frame tapylmady. Faýl formatyny barlaň.")

        return frames

    def _parse_line(self, line: str) -> Optional[CANFrame]:
        """Bir setiri parse edýär we CANFrame gaýtarýar."""
        if not line or line.startswith("#") or line.startswith(";"):
            return None

        # candump formaty
        match = self.RE_CANDUMP.match(line)
        if match:
            timestamp = float(match.group(1))
            can_id = int(match.group(2), 16)
            data_hex = match.group(3)
            data = bytes.fromhex(data_hex) if data_hex else b""
            return CANFrame(timestamp, can_id, data)

        # Timestamp + simple format
        match = self.RE_TIMESTAMP_SIMPLE.match(line)
        if match:
            timestamp = float(match.group(1))
            can_id = int(match.group(2), 16)
            data_hex = match.group(4).replace(" ", "")
            data = bytes.fromhex(data_hex) if data_hex else b""
            return CANFrame(timestamp, can_id, data)

        # Simple format (timestamp-syz)
        match = self.RE_SIMPLE.match(line)
        if match:
            can_id = int(match.group(1), 16)
            data_hex = match.group(3).replace(" ", "")
            data = bytes.fromhex(data_hex) if data_hex else b""
            return CANFrame(0.0, can_id, data)

        return None

    def _parse_csv(self, filepath: str) -> List[CANFrame]:
        """CSV formatly CAN dump-y parse edýär."""
        frames = []
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            header = None
            for row in reader:
                if not row or row[0].startswith("#"):
                    continue

                # Header setirini anykla
                if header is None and any(
                    h.lower() in ["id", "can_id", "timestamp", "time"]
                    for h in row
                ):
                    header = [h.strip().lower() for h in row]
                    continue

                try:
                    if header:
                        frame = self._parse_csv_row_with_header(row, header)
                    else:
                        frame = self._parse_csv_row_auto(row)
                    if frame:
                        frames.append(frame)
                except (ValueError, IndexError):
                    continue

        return frames

    def _parse_csv_row_with_header(
        self, row: List[str], header: List[str]
    ) -> Optional[CANFrame]:
        """Header bolan CSV setirini parse edýär."""
        data_dict = dict(zip(header, [v.strip() for v in row]))

        timestamp = float(data_dict.get("timestamp", data_dict.get("time", "0")))

        id_str = data_dict.get("id", data_dict.get("can_id", "0"))
        can_id = int(id_str, 16) if id_str.startswith("0x") else int(id_str)

        # Data baýtlaryny topla
        data_bytes = []
        for key in ["d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7"]:
            if key in data_dict and data_dict[key]:
                data_bytes.append(int(data_dict[key], 16))

        # Eger data sütüni bar bolsa
        if not data_bytes and "data" in data_dict:
            hex_str = data_dict["data"].replace(" ", "")
            data_bytes = list(bytes.fromhex(hex_str))

        return CANFrame(timestamp, can_id, bytes(data_bytes))

    def _parse_csv_row_auto(self, row: List[str]) -> Optional[CANFrame]:
        """Header-siz CSV setirini awtomatiki parse edýär."""
        if len(row) < 3:
            return None

        # Safely parse timestamp — skip row if first cell is not numeric
        ts_str = row[0].strip()
        try:
            timestamp = float(ts_str) if ts_str else 0.0
        except ValueError:
            return None

        id_str = row[1].strip()
        if not id_str:
            return None
        try:
            can_id = int(id_str, 16) if id_str.startswith("0x") else int(id_str)
        except ValueError:
            return None

        # Galan sütünler data baýtlary bolup biler
        if len(row) > 3:
            # DLC + aýry baýtlar: timestamp, id, dlc, d0, d1, ...
            data_bytes = []
            dlc_str = row[2].strip()
            start_idx = 3 if (dlc_str.isdigit() and int(dlc_str) <= 8) else 2
            for i in range(start_idx, min(start_idx + 8, len(row))):
                cell = row[i].strip()
                if cell:
                    try:
                        data_bytes.append(int(cell, 16))
                    except ValueError:
                        continue
            return CANFrame(timestamp, can_id, bytes(data_bytes))

        return None


class CANAnalyzer:
    """CAN dump-y analiz edýär we reverse engineering kömegi berýär."""

    def __init__(self):
        self.frames: List[CANFrame] = []
        self.frames_by_id: Dict[int, List[CANFrame]] = defaultdict(list)

    def load_dump(self, filepath: str) -> int:
        """CAN dump faýly ýükleýär. Tapylan frame sanyny gaýtarýar."""
        parser = CANDumpParser()
        self.frames = parser.parse_file(filepath)

        self.frames_by_id.clear()
        for frame in self.frames:
            self.frames_by_id[frame.can_id].append(frame)

        return len(self.frames)

    # ── Encode / Decode convenience ──

    def encode_frame(
        self,
        message: Message,
        signal_values: dict
    ) -> bytes:
        """
        Signal bahalaryny CAN frame-a encode edýär.
        Args:
            message: Message obýekti (DBC-den)
            signal_values: {signal_name: physical_value}
        Returns:
            Encoded CAN frame bytes
        """
        encoder = CANEncoder()
        return encoder.encode_message(message, signal_values)

    def decode_frame(
        self,
        message: Message,
        data: bytes,
        signal_names: list = None
    ) -> dict:
        """
        CAN frame data-dan signal bahalaryny decode edýär.
        Args:
            message: Message obýekti (DBC-den)
            data: CAN frame bytes
            signal_names: Diňe şu signal-lary decode et (None=hemmesi)
        Returns:
            {signal_name: physical_value}
        """
        encoder = CANEncoder()
        return encoder.decode_message(message, data, signal_names)

    def decode_all_frames(
        self,
        database: DBCDatabase,
        can_id: int
    ) -> list:
        """
        Belli bir CAN ID üçin ähli frame-leri decode edýär.
        Returns:
            [(timestamp, {signal_name: value}), ...]
        """
        if can_id not in self.frames_by_id:
            return []

        msg = database.get_message(can_id)
        if not msg:
            return []

        encoder = CANEncoder()
        results = []
        for frame in self.frames_by_id[can_id]:
            values = encoder.decode_message(msg, frame.data)
            results.append((frame.timestamp, values))
        return results

    def get_unique_ids(self) -> List[int]:
        """Ähli unikal CAN ID-leri gaýtarýar (sorted)."""
        return sorted(self.frames_by_id.keys())

    def get_id_statistics(self) -> Dict[int, dict]:
        """Her bir CAN ID üçin statistikany gaýtarýar."""
        stats = {}
        for can_id, id_frames in self.frames_by_id.items():
            dlcs = [f.dlc for f in id_frames]
            stats[can_id] = {
                "count": len(id_frames),
                "dlc": max(dlcs) if dlcs else 0,
                "min_dlc": min(dlcs) if dlcs else 0,
                "max_dlc": max(dlcs) if dlcs else 0,
            }
        return stats

    def show_summary(self):
        """CAN dump-yň gysgaça mazmunyny görkezýär."""
        print(f"\n{'='*60}")
        print(f"CAN Dump Summary")
        print(f"{'='*60}")
        print(f"Total frames: {len(self.frames)}")
        print(f"Unique CAN IDs: {len(self.frames_by_id)}")
        print(f"{'='*60}")

        stats = self.get_id_statistics()
        print(f"\n{'ID':>10} | {'Count':>8} | {'DLC':>4} | {'Sample Data'}")
        print(f"{'-'*10}-+-{'-'*8}-+-{'-'*4}-+-{'-'*30}")

        for can_id in sorted(stats.keys()):
            s = stats[can_id]
            sample = self.frames_by_id[can_id][0].get_hex()
            print(f"  0x{can_id:03X}   | {s['count']:>8} | {s['dlc']:>4} | {sample}")

        print()

    def show_id_data(self, can_id: int, max_rows: int = 20):
        """Belli bir CAN ID üçin data-ny görkezýär."""
        if can_id not in self.frames_by_id:
            print(f"[!] CAN ID 0x{can_id:03X} tapylmady.")
            return

        id_frames = self.frames_by_id[can_id]
        print(f"\n--- CAN ID: 0x{can_id:03X} ({len(id_frames)} frames) ---")
        print(f"{'#':>5} | {'Timestamp':>12} | {'Hex Data':>24} | Binary Data")
        print(f"{'-'*5}-+-{'-'*12}-+-{'-'*24}-+-{'-'*64}")

        for i, frame in enumerate(id_frames[:max_rows]):
            print(
                f"{i:>5} | {frame.timestamp:>12.4f} | {frame.get_hex():>24} | "
                f"{frame.get_bits()}"
            )

        if len(id_frames) > max_rows:
            print(f"  ... ({len(id_frames) - max_rows} more frames)")
        print()

    def detect_changing_bytes(self, can_id: int) -> List[int]:
        """Belli bir CAN ID-de üýtgeýän baýtlary anyklaýar."""
        if can_id not in self.frames_by_id:
            return []

        id_frames = self.frames_by_id[can_id]
        if len(id_frames) < 2:
            return []

        first = id_frames[0].data
        changing = []

        for byte_idx in range(len(first)):
            values = set()
            for frame in id_frames:
                if byte_idx < len(frame.data):
                    values.add(frame.data[byte_idx])
            if len(values) > 1:
                changing.append(byte_idx)

        return changing

    def detect_changing_bits(self, can_id: int) -> List[int]:
        """Belli bir CAN ID-de üýtgeýän bitleri anyklaýar."""
        if can_id not in self.frames_by_id:
            return []

        id_frames = self.frames_by_id[can_id]
        if len(id_frames) < 2:
            return []

        max_len = max(len(f.data) for f in id_frames)
        changing_bits = []

        for bit_idx in range(max_len * 8):
            byte_idx = bit_idx // 8
            bit_pos = 7 - (bit_idx % 8)
            values = set()

            for frame in id_frames:
                if byte_idx < len(frame.data):
                    bit_val = (frame.data[byte_idx] >> bit_pos) & 1
                    values.add(bit_val)

            if len(values) > 1:
                changing_bits.append(bit_idx)

        return changing_bits

    def show_changing_analysis(self, can_id: int):
        """Üýtgeýän baýtlary we bitleri görkezýär."""
        changing_bytes = self.detect_changing_bytes(can_id)
        changing_bits = self.detect_changing_bits(can_id)

        print(f"\n--- Change Analysis for 0x{can_id:03X} ---")
        print(f"Changing bytes: {changing_bytes}")
        print(f"Changing bits:  {changing_bits}")

        if changing_bytes:
            print(f"\nByte values range:")
            id_frames = self.frames_by_id[can_id]
            for byte_idx in changing_bytes:
                values = [
                    f.data[byte_idx]
                    for f in id_frames
                    if byte_idx < len(f.data)
                ]
                print(
                    f"  Byte {byte_idx}: min=0x{min(values):02X} "
                    f"max=0x{max(values):02X} "
                    f"unique={len(set(values))}"
                )
        print()

    def extract_signal_values(
        self,
        can_id: int,
        start_bit: int,
        length: int,
        byte_order: str = "little_endian",
        signed: bool = False,
        scale: float = 1.0,
        offset: float = 0.0
    ) -> List[Tuple[float, float]]:
        """
        Kesgitlenen signal parametrlerinden signal bahalaryny çykaryp alýar.
        (timestamp, value) jübütleriniň listini gaýtarýar.
        """
        if can_id not in self.frames_by_id:
            return []

        results = []
        for frame in self.frames_by_id[can_id]:
            raw = self._extract_raw_value(
                frame.data, start_bit, length, byte_order
            )
            if signed and raw >= (1 << (length - 1)):
                raw -= (1 << length)
            physical = raw * scale + offset
            results.append((frame.timestamp, physical))

        return results

    def _extract_raw_value(
        self,
        data: bytes,
        start_bit: int,
        length: int,
        byte_order: str
    ) -> int:
        """Data-dan raw bit bahany çykaryp alýar."""
        if byte_order == "little_endian":
            # Intel byte order
            value = 0
            for i in range(length):
                bit_idx = start_bit + i
                byte_idx = bit_idx // 8
                bit_pos = bit_idx % 8
                if byte_idx < len(data):
                    if data[byte_idx] & (1 << bit_pos):
                        value |= (1 << i)
            return value
        else:
            # Motorola byte order
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

    def interactive_define_signals(self, can_id: int) -> List[Signal]:
        """
        Interaktiw usulda signal-lary kesgitlemäge mümkinçilik berýär.
        User start_bit, length, scale, offset girizýär.
        """
        if can_id not in self.frames_by_id:
            print(f"[!] CAN ID 0x{can_id:03X} tapylmady.")
            return []

        # Ilki data-ny görkez
        self.show_id_data(can_id, max_rows=10)
        self.show_changing_analysis(can_id)

        signals = []
        print("\nSignal-lary kesgitläň (gutarmak üçin boş name giriziň):\n")

        while True:
            name = input("  Signal name (ýa-da Enter gutarmak üçin): ").strip()
            if not name:
                break

            try:
                start_bit = int(input("  Start bit: "))
                length = int(input("  Length (bits): "))

                order_input = input("  Byte order (1=Intel/LE, 0=Motorola/BE) [1]: ").strip()
                byte_order = "big_endian" if order_input == "0" else "little_endian"

                signed_input = input("  Signed? (y/n) [n]: ").strip().lower()
                value_type = "signed" if signed_input == "y" else "unsigned"

                scale = float(input("  Scale [1.0]: ").strip() or "1.0")
                offset = float(input("  Offset [0.0]: ").strip() or "0.0")
                unit = input("  Unit []: ").strip()

                minimum = float(input("  Min value [0]: ").strip() or "0")
                maximum = float(input("  Max value [0]: ").strip() or "0")

                signal = Signal(
                    name=name,
                    start_bit=start_bit,
                    length=length,
                    byte_order=byte_order,
                    value_type=value_type,
                    scale=scale,
                    offset=offset,
                    minimum=minimum,
                    maximum=maximum,
                    unit=unit
                )
                signals.append(signal)

                # Mysal signal bahalaryny görkez
                values = self.extract_signal_values(
                    can_id, start_bit, length, byte_order,
                    value_type == "signed", scale, offset
                )
                if values:
                    sample = values[:5]
                    print(f"\n  Sample values: {[f'{v[1]:.2f}' for v in sample]}")

                print(f"  [+] Signal '{name}' goşuldy.\n")

            except (ValueError, KeyboardInterrupt):
                print("  [!] Nädogry giriş. Gaýtadan synanyşyň.\n")
                continue

        return signals

    def create_dbc_from_analysis(
        self,
        signals_by_id: Dict[int, List[Signal]],
        output_filepath: str,
        version: str = ""
    ):
        """
        Analiz netijelerinden DBC faýl döredýär.

        Args:
            signals_by_id: {CAN_ID: [Signal, ...]} görnüşinde
            output_filepath: Çykyş DBC faýlynyň ýoly
            version: DBC wersiýasy
        """
        database = DBCDatabase(version=version)

        for can_id, signals in signals_by_id.items():
            stats = self.get_id_statistics()
            dlc = stats.get(can_id, {}).get("dlc", 8)

            msg = Message(
                message_id=can_id,
                name=f"MSG_0x{can_id:03X}",
                dlc=dlc,
                signals=signals
            )
            database.add_message(msg)

        generator = DBCGenerator()
        generator.generate_to_file(database, output_filepath)
        return database

    def run_interactive_session(self, output_filepath: str = "output.dbc"):
        """Interaktiw reverse engineering sessiýasyny başlaýar."""
        self.show_summary()

        signals_by_id: Dict[int, List[Signal]] = {}

        while True:
            try:
                id_input = input(
                    "\nCAN ID giriziň (hex, mysal: 123) "
                    "ýa-da 'done' gutarmak üçin: "
                ).strip()

                if id_input.lower() in ("done", "exit", "quit", "q"):
                    break

                can_id = int(id_input, 16)
                signals = self.interactive_define_signals(can_id)

                if signals:
                    signals_by_id[can_id] = signals

            except (ValueError, KeyboardInterrupt):
                print("\n[!] Nädogry giriş.")
                continue

        if signals_by_id:
            db = self.create_dbc_from_analysis(signals_by_id, output_filepath)
            print(f"\n[+] DBC faýl döredildi: {output_filepath}")
            print(f"    Messages: {len(db.messages)}")
            total_signals = sum(len(m.signals) for m in db.messages)
            print(f"    Signals:  {total_signals}")
        else:
            print("\n[!] Hiç bir signal kesgitlenmedi. DBC döredilmedi.")


def analyze_dump(filepath: str, output: str = "output.dbc"):
    """CAN dump faýly analiz etmek üçin ýönekeý funksiýa."""
    analyzer = CANAnalyzer()
    count = analyzer.load_dump(filepath)

    if count == 0:
        print("[!] Hiç bir frame tapylmady.")
        return

    print(f"[+] {count} frame ýüklendi.")
    analyzer.run_interactive_session(output)
