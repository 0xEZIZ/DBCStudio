"""
ai_module.py - Smart Signal Detection & AI Assistance
Heuristic signal detection, AI signal suggestion, auto DBC generation.
CAN data-dan signal-lary awtomatiki tapmak we teklip etmek üçin ulanylýar.
"""

import math
import statistics
import json
import os
from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
from core.models import Signal, Message, DBCDatabase
from core.i18n import I18N


# ────────────────────────────────────────────────
# Signal pattern definitions (heuristic database)
# ────────────────────────────────────────────────

KNOWN_SIGNAL_PATTERNS = {
    "speed": {
        "keywords": ["speed", "velocity", "spd", "vss"],
        "typical_length": [16, 13],
        "typical_scale": [0.01, 0.05, 0.1, 1.0],
        "unit": "km/h",
        "range": (0, 300),
        "pattern": "smooth_increasing",
        "description": "Vehicle speed signal"
    },
    "rpm": {
        "keywords": ["rpm", "engine_speed", "engspd", "tach", "n_mot"],
        "typical_length": [16, 14],
        "typical_scale": [0.25, 1.0, 0.125],
        "unit": "rpm",
        "range": (0, 8000),
        "pattern": "periodic_oscillation",
        "description": "Engine RPM signal"
    },
    "temperature": {
        "keywords": ["temp", "temperature", "coolant", "oil_temp", "t_mot"],
        "typical_length": [8, 10],
        "typical_scale": [1.0, 0.5, 0.75],
        "typical_offset": [-40, -48],
        "unit": "degC",
        "range": (-40, 250),
        "pattern": "slow_change",
        "description": "Temperature signal"
    },
    "throttle": {
        "keywords": ["throttle", "accel", "pedal", "tps", "gas"],
        "typical_length": [8, 10],
        "typical_scale": [0.392157, 0.4, 1.0],
        "unit": "%",
        "range": (0, 100),
        "pattern": "variable",
        "description": "Throttle/pedal position"
    },
    "brake": {
        "keywords": ["brake", "brk", "brake_pressure"],
        "typical_length": [8, 16, 1],
        "typical_scale": [0.1, 1.0],
        "unit": "bar",
        "range": (0, 200),
        "pattern": "binary_or_pressure",
        "description": "Brake signal"
    },
    "steering": {
        "keywords": ["steer", "steering", "swa", "angle"],
        "typical_length": [16, 14],
        "typical_scale": [0.1, 0.04395],
        "unit": "deg",
        "range": (-800, 800),
        "pattern": "oscillation_centered",
        "description": "Steering angle signal"
    },
    "gear": {
        "keywords": ["gear", "transmission", "prndl"],
        "typical_length": [4, 3],
        "typical_scale": [1.0],
        "unit": "",
        "range": (0, 8),
        "pattern": "discrete_steps",
        "description": "Gear position signal"
    },
    "fuel": {
        "keywords": ["fuel", "fuel_level", "tank"],
        "typical_length": [8],
        "typical_scale": [0.392157, 1.0],
        "unit": "%",
        "range": (0, 100),
        "pattern": "very_slow_change",
        "description": "Fuel level signal"
    },
    "voltage": {
        "keywords": ["voltage", "batt", "battery", "vbat"],
        "typical_length": [8, 10],
        "typical_scale": [0.1, 0.05],
        "unit": "V",
        "range": (8, 16),
        "pattern": "stable_with_drift",
        "description": "Battery voltage signal"
    },
    "counter": {
        "keywords": ["counter", "cnt", "alive", "rolling"],
        "typical_length": [4, 8],
        "typical_scale": [1.0],
        "unit": "",
        "range": (0, 15),
        "pattern": "monotonic_wrapping",
        "description": "Rolling counter signal"
    },
    "checksum": {
        "keywords": ["checksum", "crc", "chk"],
        "typical_length": [8],
        "typical_scale": [1.0],
        "unit": "",
        "range": (0, 255),
        "pattern": "seemingly_random",
        "description": "Checksum/CRC signal"
    }
}


class SignalCandidate:
    """Bir potensial signal kandidatyny görkezýär."""

    def __init__(
        self,
        can_id: int,
        start_bit: int,
        length: int,
        byte_order: str = "little_endian",
        confidence: float = 0.0,
        suggested_name: str = "",
        suggested_type: str = "",
        suggested_scale: float = 1.0,
        suggested_offset: float = 0.0,
        suggested_unit: str = "",
        reason: str = ""
    ):
        self.can_id = can_id
        self.start_bit = start_bit
        self.length = length
        self.byte_order = byte_order
        self.confidence = confidence
        self.suggested_name = suggested_name
        self.suggested_type = suggested_type
        self.suggested_scale = suggested_scale
        self.suggested_offset = suggested_offset
        self.suggested_unit = suggested_unit
        self.reason = reason

    def to_signal(self) -> Signal:
        """Kandidaty Signal obýektine öwürýär."""
        return Signal(
            name=self.suggested_name or f"SIG_{self.start_bit}_{self.length}",
            start_bit=self.start_bit,
            length=self.length,
            byte_order=self.byte_order,
            value_type="unsigned",
            scale=self.suggested_scale,
            offset=self.suggested_offset,
            unit=self.suggested_unit
        )

    def __repr__(self) -> str:
        return (
            f"Candidate(bit={self.start_bit}|{self.length}, "
            f"type='{self.suggested_type}', "
            f"conf={self.confidence:.0%}, name='{self.suggested_name}')"
        )


class PatternAnalyzer:
    """Data pattern-lary analiz edýär (signal tapmak üçin)."""

    @staticmethod
    def extract_raw_values(
        frames_data: List[bytes],
        start_bit: int,
        length: int,
        byte_order: str = "little_endian"
    ) -> List[int]:
        """Frame listinden belli bir bit diapazonynda raw bahalary çykarýar."""
        values = []
        for data in frames_data:
            if byte_order == "little_endian":
                value = 0
                for i in range(length):
                    bit_idx = start_bit + i
                    byte_idx = bit_idx // 8
                    bit_pos = bit_idx % 8
                    if byte_idx < len(data):
                        if data[byte_idx] & (1 << bit_pos):
                            value |= (1 << i)
            else:
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
            values.append(value)
        return values

    @staticmethod
    def classify_pattern(values: List[int]) -> str:
        """Bahalaryň pattern-yny kesgitleýär."""
        if len(values) < 3:
            return "insufficient_data"

        unique = len(set(values))
        total = len(values)

        # Hemme bahalar birmeňzeş
        if unique == 1:
            return "constant"

        # Diňe 2 baha (binary)
        if unique == 2:
            return "binary"

        # Monoton artýan (wrapping bilen)
        diffs = [values[i + 1] - values[i] for i in range(len(values) - 1)]
        positive_diffs = sum(1 for d in diffs if d > 0)
        negative_diffs = sum(1 for d in diffs if d < 0)

        # Rolling counter (monoton artýan, az wrap-lar bilen)
        if positive_diffs > 0.8 * len(diffs) and negative_diffs <= 2:
            return "monotonic_wrapping"

        # Smooth artýan
        if positive_diffs > 0.7 * len(diffs):
            return "smooth_increasing"

        # Smooth azalýan
        if negative_diffs > 0.7 * len(diffs):
            return "smooth_decreasing"

        # Discrete steps (az unikal baha)
        if unique <= 0.1 * total and unique <= 10:
            return "discrete_steps"

        # Gaty haýal üýtgeýär
        try:
            std = statistics.stdev(values)
            mean = statistics.mean(values)
            cv = std / mean if mean != 0 else 0

            if cv < 0.02:
                return "stable_with_drift"
            if cv < 0.1:
                return "slow_change"
            if cv > 1.5:
                return "seemingly_random"
        except (statistics.StatisticsError, ZeroDivisionError):
            pass

        # Merkeze ýakyn yrgalanma
        try:
            mean = statistics.mean(values)
            max_val = max(values)
            min_val = min(values)
            mid = (max_val + min_val) / 2
            if abs(mean - mid) < 0.2 * (max_val - min_val):
                return "oscillation_centered"
        except (statistics.StatisticsError, ZeroDivisionError):
            pass

        return "variable"

    @staticmethod
    def calculate_entropy(values: List[int]) -> float:
        """Bahalaryň entropisyny hasaplaýar (bit)."""
        if not values:
            return 0.0
        total = len(values)
        freq = defaultdict(int)
        for v in values:
            freq[v] += 1
        entropy = 0.0
        for count in freq.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        return entropy

    @staticmethod
    def calculate_smoothness(values: List[int]) -> float:
        """Signal-yň näderejede ýumşakdygyny hasaplaýar (0-1, 1=gaty ýumşak)."""
        if len(values) < 3:
            return 0.5
        diffs = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
        max_possible = max(values) - min(values) if max(values) != min(values) else 1
        avg_diff = sum(diffs) / len(diffs)
        smoothness = 1.0 - min(avg_diff / max_possible, 1.0)
        return smoothness


class SmartSignalDetector:
    """Heuristic usulda signal-lary awtomatiki tapýar."""

    def __init__(self):
        self.pattern_analyzer = PatternAnalyzer()

    def detect_signals(
        self,
        can_id: int,
        frames_data: List[bytes],
        min_confidence: float = 0.3
    ) -> List[SignalCandidate]:
        """
        Berlen CAN ID üçin signal kandidatlaryny tapýar.
        """
        if len(frames_data) < 5:
            return []

        candidates = []
        max_bits = max(len(d) for d in frames_data) * 8

        # 1. Bit-level üýtgeşme analizi
        changing_regions = self._find_changing_regions(frames_data, max_bits)

        # 2. Her region üçin signal candidate döret
        for start, end in changing_regions:
            length = end - start + 1
            if length < 1 or length > 32:
                continue

            raw_values = PatternAnalyzer.extract_raw_values(
                frames_data, start, length
            )
            pattern = PatternAnalyzer.classify_pattern(raw_values)

            if pattern == "constant":
                continue

            candidate = self._classify_candidate(
                can_id, start, length, raw_values, pattern
            )
            if candidate and candidate.confidence >= min_confidence:
                candidates.append(candidate)

        # 3. Standart signal uzunlyklaryny synap gör (8, 16 bit)
        for bit_len in [1, 4, 8, 16]:
            for start in range(0, max_bits - bit_len + 1, bit_len):
                # Eýýäm tapylan regionlarda bar bolsa skip et
                if any(
                    c.start_bit <= start < c.start_bit + c.length
                    for c in candidates
                ):
                    continue

                raw_values = PatternAnalyzer.extract_raw_values(
                    frames_data, start, bit_len
                )
                pattern = PatternAnalyzer.classify_pattern(raw_values)

                if pattern == "constant":
                    continue

                candidate = self._classify_candidate(
                    can_id, start, bit_len, raw_values, pattern
                )
                if candidate and candidate.confidence >= min_confidence:
                    # Overlap barla
                    overlap = False
                    for existing in candidates:
                        if (start < existing.start_bit + existing.length and
                                start + bit_len > existing.start_bit):
                            if candidate.confidence <= existing.confidence:
                                overlap = True
                                break
                    if not overlap:
                        candidates.append(candidate)

        # Confidence boýunça tertiple
        candidates.sort(key=lambda c: c.confidence, reverse=True)

        # Overlap-lary aýyr (iň ýokary confidence sakla)
        return self._remove_overlaps(candidates)

    def _find_changing_regions(
        self, frames_data: List[bytes], max_bits: int
    ) -> List[Tuple[int, int]]:
        """Üýtgeýän bit regionlaryny tapýar."""
        changing = [False] * max_bits

        for bit_idx in range(max_bits):
            byte_idx = bit_idx // 8
            bit_pos = bit_idx % 8
            values = set()
            for data in frames_data:
                if byte_idx < len(data):
                    values.add((data[byte_idx] >> bit_pos) & 1)
            if len(values) > 1:
                changing[bit_idx] = True

        # Yzygiderli regionlary topla
        regions = []
        start = None
        for i, is_changing in enumerate(changing):
            if is_changing and start is None:
                start = i
            elif not is_changing and start is not None:
                regions.append((start, i - 1))
                start = None
        if start is not None:
            regions.append((start, max_bits - 1))

        return regions

    def _classify_candidate(
        self,
        can_id: int,
        start_bit: int,
        length: int,
        raw_values: List[int],
        pattern: str
    ) -> Optional[SignalCandidate]:
        """Pattern-a görä kandidaty klassifisirlýär we atylandyrýar."""
        confidence = 0.3
        suggested_type = "unknown"
        suggested_name = f"SIG_0x{can_id:03X}_{start_bit}"
        suggested_scale = 1.0
        suggested_offset = 0.0
        suggested_unit = ""
        reason = f"Pattern: {pattern}"

        unique = len(set(raw_values))
        max_val = max(raw_values) if raw_values else 0

        # Pattern-a esaslanan klassifikasiýa
        if pattern == "monotonic_wrapping" and length <= 8:
            suggested_type = "counter"
            suggested_name = f"Counter_0x{can_id:03X}_{start_bit}"
            confidence = 0.85
            reason = "Monotonically increasing with wrapping - likely rolling counter"

        elif pattern == "binary" and length == 1:
            suggested_type = "flag"
            suggested_name = f"Flag_0x{can_id:03X}_{start_bit}"
            confidence = 0.7
            reason = "Single bit toggling - likely a boolean flag"

        elif pattern == "seemingly_random" and length == 8:
            suggested_type = "checksum"
            suggested_name = f"Checksum_0x{can_id:03X}_{start_bit}"
            confidence = 0.5
            reason = "High entropy byte - possibly checksum/CRC"

        elif pattern == "smooth_increasing" and length >= 12:
            suggested_type = "speed"
            suggested_name = f"Speed_0x{can_id:03X}_{start_bit}"
            suggested_scale = 0.01
            suggested_unit = "km/h"
            confidence = 0.6
            reason = "Smooth increasing 16-bit value - possibly vehicle speed"

        elif pattern == "oscillation_centered" and length >= 12:
            suggested_type = "steering"
            suggested_name = f"SteerAngle_0x{can_id:03X}_{start_bit}"
            suggested_scale = 0.1
            suggested_unit = "deg"
            confidence = 0.5
            reason = "Centered oscillation - possibly steering angle"

        elif pattern == "slow_change" and length == 8:
            suggested_type = "temperature"
            suggested_name = f"Temp_0x{can_id:03X}_{start_bit}"
            suggested_offset = -40.0
            suggested_unit = "degC"
            confidence = 0.55
            reason = "Slowly changing 8-bit value - possibly temperature"

        elif pattern == "discrete_steps" and length <= 4:
            suggested_type = "gear"
            suggested_name = f"State_0x{can_id:03X}_{start_bit}"
            confidence = 0.5
            reason = "Discrete steps - possibly gear/mode selector"

        elif pattern == "variable" and length >= 8:
            # Umumy üýtgeýän signal
            smoothness = PatternAnalyzer.calculate_smoothness(raw_values)
            if smoothness > 0.7:
                suggested_type = "analog"
                confidence = 0.4
                reason = f"Smooth variable signal (smoothness={smoothness:.2f})"
            else:
                suggested_type = "digital"
                confidence = 0.3
                reason = f"Variable signal (smoothness={smoothness:.2f})"
            suggested_name = f"Signal_0x{can_id:03X}_{start_bit}"

        elif pattern == "stable_with_drift" and length >= 8:
            suggested_type = "voltage"
            suggested_name = f"Voltage_0x{can_id:03X}_{start_bit}"
            suggested_scale = 0.1
            suggested_unit = "V"
            confidence = 0.45
            reason = "Stable with small drift - possibly voltage"

        else:
            suggested_name = f"Signal_0x{can_id:03X}_{start_bit}"
            confidence = 0.2
            reason = f"Unclassified pattern: {pattern}"

        return SignalCandidate(
            can_id=can_id,
            start_bit=start_bit,
            length=length,
            confidence=confidence,
            suggested_name=suggested_name,
            suggested_type=suggested_type,
            suggested_scale=suggested_scale,
            suggested_offset=suggested_offset,
            suggested_unit=suggested_unit,
            reason=reason
        )

    def _remove_overlaps(
        self, candidates: List[SignalCandidate]
    ) -> List[SignalCandidate]:
        """Overlap edýän kandidatlaryň arasynda iň gowusyny saýlaýar."""
        result = []
        used_bits = set()

        for c in candidates:
            bits = set(range(c.start_bit, c.start_bit + c.length))
            if not bits & used_bits:
                result.append(c)
                used_bits |= bits

        return result


class AISignalSuggester:
    """User soragyna görä signal teklip edýär."""

    def __init__(self):
        self.detector = SmartSignalDetector()

    def suggest_by_keyword(
        self,
        keyword: str,
        candidates: List[SignalCandidate]
    ) -> List[SignalCandidate]:
        """
        User-iň ýazan keyword-yna (mysal: 'speed', 'temperature')
        laýyk signal-lary tapýar.
        """
        keyword = keyword.lower().strip()
        matches = []

        for candidate in candidates:
            score = 0.0

            # Gönüden-göni type gabat gelme
            if candidate.suggested_type == keyword:
                score = 1.0
            elif keyword in candidate.suggested_type:
                score = 0.8

            # Known pattern keyword-laryna garşy barla
            for sig_type, pattern in KNOWN_SIGNAL_PATTERNS.items():
                if any(kw in keyword or keyword in kw
                       for kw in pattern["keywords"]):
                    if candidate.suggested_type == sig_type:
                        score = max(score, 0.9)
                    elif candidate.length in pattern.get("typical_length", []):
                        score = max(score, 0.4)

            # Signal adynda keyword barla
            if keyword in candidate.suggested_name.lower():
                score = max(score, 0.7)

            if score > 0.2:
                candidate.confidence = min(candidate.confidence + score * 0.3, 1.0)
                matches.append(candidate)

        matches.sort(key=lambda c: c.confidence, reverse=True)
        return matches

    def auto_generate_dbc(
        self,
        frames_by_id: Dict[int, List[bytes]],
        min_confidence: float = 0.4
    ) -> DBCDatabase:
        """
        CAN dump-dan awtomatiki DBC database döredýär.
        AI heuristic signal detection ulanýar.
        """
        db = DBCDatabase(version="1.0")

        for can_id, frames_data in frames_by_id.items():
            candidates = self.detector.detect_signals(
                can_id, frames_data, min_confidence
            )

            if not candidates:
                continue

            max_dlc = max(len(d) for d in frames_data)
            msg = Message(
                message_id=can_id,
                name=f"MSG_0x{can_id:03X}",
                dlc=max_dlc
            )

            for c in candidates:
                signal = c.to_signal()
                msg.add_signal(signal)

            if msg.signals:
                db.add_message(msg)

        return db

    def compare_logs(
        self,
        frames_by_id_1: Dict[int, List[bytes]],
        frames_by_id_2: Dict[int, List[bytes]]
    ) -> Dict[str, any]:
        """
        Iki CAN log-y deňeşdirýär we tapawutlary görkezýär.
        """
        ids_1 = set(frames_by_id_1.keys())
        ids_2 = set(frames_by_id_2.keys())

        result = {
            "only_in_log1": sorted(ids_1 - ids_2),
            "only_in_log2": sorted(ids_2 - ids_1),
            "common": sorted(ids_1 & ids_2),
            "differences": {}
        }

        for can_id in result["common"]:
            data1 = frames_by_id_1[can_id]
            data2 = frames_by_id_2[can_id]

            diff = {
                "count_log1": len(data1),
                "count_log2": len(data2),
                "changed_bytes": []
            }

            # Baýt-level tapawudy barla
            max_dlc = max(
                max((len(d) for d in data1), default=0),
                max((len(d) for d in data2), default=0)
            )

            for byte_idx in range(max_dlc):
                vals1 = set(
                    d[byte_idx] for d in data1 if byte_idx < len(d)
                )
                vals2 = set(
                    d[byte_idx] for d in data2 if byte_idx < len(d)
                )
                if vals1 != vals2:
                    diff["changed_bytes"].append({
                        "byte": byte_idx,
                        "range_log1": (min(vals1), max(vals1)) if vals1 else None,
                        "range_log2": (min(vals2), max(vals2)) if vals2 else None
                    })

            if diff["changed_bytes"] or diff["count_log1"] != diff["count_log2"]:
                result["differences"][can_id] = diff

        return result


def print_candidates(candidates: List[SignalCandidate]):
    """Signal kandidatlaryny oňat formatda çap edýär."""
    if not candidates:
        print(f"  ({I18N.t('ai_no_results')})")
        return

    print(f"\n  {'#':>3}  {'Name':<30} {'Bits':>8} {'Type':<15} "
          f"{'Conf':>6} {'Reason'}")
    print(f"  {'─'*3}  {'─'*30} {'─'*8} {'─'*15} {'─'*6} {'─'*40}")

    for i, c in enumerate(candidates, 1):
        print(
            f"  {i:>3}  {c.suggested_name:<30} "
            f"{c.start_bit:>2}|{c.length:<4} "
            f"{c.suggested_type:<15} "
            f"{c.confidence:>5.0%} "
            f"{c.reason}"
        )


class DBCKnowledgeManager:
    """
    DBC faýllaryndan 'bilim' alýar we ýatda saklaýar.
    Ulanyjynyň ozalky işlerini täze awtomatiki tapyşlar üçin ulanýar.
    """
    def __init__(self, storage_path="knowledge_base.json"):
        self.storage_path = storage_path
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> Dict:
        if os.path.exists(self.storage_path):
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"patterns": {}, "brands": {}}

    def save_knowledge(self):
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge, f, indent=4)

    def learn_from_dbc(self, db: DBCDatabase, brand: str = "Generic"):
        """DBC-den signallaryň 'fingerprint'-lerini çykaryp alýar."""
        if brand not in self.knowledge["brands"]:
            self.knowledge["brands"][brand] = {}

        for msg in db.messages:
            for sig in msg.signals:
                # Fingerprint döretmek
                fp = {
                    "id": msg.message_id,
                    "start": sig.start_bit,
                    "length": sig.length,
                    "byte_order": sig.byte_order,
                    "value_type": sig.value_type,
                    "factor": sig.scale,
                    "offset": sig.offset
                }
                # At boýunça ýatda sakla (mysal: "Speed" -> [fp1, fp2])
                name_key = sig.name.lower()
                if name_key not in self.knowledge["patterns"]:
                    self.knowledge["patterns"][name_key] = []
                
                # Diňe täze bolsa goş
                if fp not in self.knowledge["patterns"][name_key]:
                    self.knowledge["patterns"][name_key].append(fp)
                
                # Marka boýunça ID-leri ýatda sakla
                id_hex = f"0x{msg.message_id:03X}"
                if id_hex not in self.knowledge["brands"][brand]:
                    self.knowledge["brands"][brand][id_hex] = []
                if sig.name not in self.knowledge["brands"][brand][id_hex]:
                    self.knowledge["brands"][brand][id_hex].append(sig.name)

    def find_matches(self, can_id: int, brand: str = "Generic") -> List[str]:
        """Belli bir ID üçin marka degişli bolan signallary tapýar."""
        id_hex = f"0x{can_id:03X}"
        return self.knowledge["brands"].get(brand, {}).get(id_hex, [])


class SmartAssistantEngine:
    """
    Iň ýokary derejeli AI kömekçisi.
    Heuristics + Knowledge Base + Cross-Log Analysis-y birleşdirýär.
    """
    def __init__(self, knowledge_manager: DBCKnowledgeManager):
        self.km = knowledge_manager
        self.detector = SmartSignalDetector()

    def smart_analyze(
        self, 
        frames_by_id: Dict[int, List[bytes]], 
        brand: str = "Generic",
        reference_frames_by_id: Optional[Dict[int, List[bytes]]] = None
    ) -> List[Dict]:
        """
        Doly analiz we maslahat berýär.
        """
        results = []
        
        for can_id, data_list in frames_by_id.items():
            # 1. Knowledge Base-den barla
            known_names = self.km.find_matches(can_id, brand)
            
            # 2. Heuristic analiz
            candidates = self.detector.detect_signals(can_id, data_list)
            
            # 3. Cross-Log Analiz (hereket barmy?)
            is_motion_signal = False
            if reference_frames_by_id and can_id in reference_frames_by_id:
                # Reference log (mysal: idling) bilen deňeşdir
                # Bu ýerde has çuňňur logika bolup biler
                pass

            for cand in candidates:
                advice = self._generate_advice(cand, known_names, brand)
                results.append({
                    "can_id": can_id,
                    "candidate": cand,
                    "known_names": known_names,
                    "advice": advice
                })
        
        return results

    def _generate_advice(self, cand: SignalCandidate, known_names: List[str], brand: str) -> str:
        """Professional maslahat tekstini döredýär."""
        id_hex = f"0x{cand.can_id:03X}"
        
        if known_names:
            names_str = ", ".join(known_names)
            advice = I18N.t("ai_advice_known").format(brand=brand, id=id_hex, names=names_str)
        else:
            advice = I18N.t("ai_advice_detected").format(type=cand.suggested_type)

        advice += I18N.t("ai_advice_recommend").format(len=cand.length, start=cand.start_bit)
        advice += I18N.t("ai_advice_reason").format(reason=cand.reason)
        return advice


class DifferentialAnalyzer:
    """
    Two-phase differential analysis for Reverse Engineering.
    Compares 'Baseline' (Idle) vs 'Action' (Active) packets.
    """

    def analyze(
        self,
        baseline_frames: Dict[int, List[bytes]],
        action_frames: Dict[int, List[bytes]]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Baseline we Action maglumatlaryny ähli ID-ler üçin deňeşdirýär.
        Returns: { can_id: { "candidates": [...], "score": total_id_score } }
        """
        results = {}
        all_ids = set(baseline_frames.keys()) | set(action_frames.keys())

        for can_id in all_ids:
            b_frames = baseline_frames.get(can_id, [])
            a_frames = action_frames.get(can_id, [])

            if not a_frames:
                continue

            # Calculate bit-level stats
            max_len = max(
                max((len(f) for f in b_frames), default=0),
                max((len(f) for f in a_frames), default=0)
            )
            max_bits = max_len * 8

            b_activity = self._get_bit_activity(b_frames, max_bits)
            a_activity = self._get_bit_activity(a_frames, max_bits)
            
            # Value transition analysis (Stable in Baseline -> Active in Action)
            b_stable_vals = self._get_stable_bits(b_frames, max_bits)
            a_varied_bits = [i for i, flips in enumerate(a_activity) if flips > 0]

            delta_bits = []
            for i in range(max_bits):
                b_act = b_activity[i]
                a_act = a_activity[i]
                
                # Logic 1: Bit was DEAD in baseline, but started flipping in action (PURE)
                if a_act > 0 and b_act == 0:
                    delta_bits.append({"bit": i, "score": 1.0, "type": "pure"})
                
                # Logic 2: Bit was stable (0 or 1) in baseline, but changed in action (LATCH/TOGGLE)
                elif i in a_varied_bits and i in b_stable_vals:
                    delta_bits.append({"bit": i, "score": 0.8, "type": "transitioned"})
                
                # Logic 3: Bit was already flipping, but frequency increased significantly
                elif a_act > b_act * 3 and a_act > 5:
                    delta_bits.append({"bit": i, "score": 0.6, "type": "increased"})

            if delta_bits:
                candidates = self._group_trending_bits(delta_bits)
                if candidates:
                    results[can_id] = {
                        "candidates": candidates,
                        "heatmap": a_activity,
                        "total_score": sum(c["confidence"] for c in candidates)
                    }

        return results

    def _get_stable_bits(self, frames: List[bytes], max_bits: int) -> Dict[int, int]:
        """Haýsy bitleriň baseline-da hemişe şol bir baha (0 ýa 1) eýedigini tapýar."""
        if not frames: return {}
        
        stable_vals = {}
        for bit_idx in range(max_bits):
            byte_idx = bit_idx // 8
            bit_pos = bit_idx % 8
            
            values = set()
            for f in frames:
                if byte_idx < len(f):
                    values.add((f[byte_idx] >> bit_pos) & 1)
                else:
                    values.add(0)
            
            if len(values) == 1:
                stable_vals[bit_idx] = list(values)[0]
        return stable_vals

    def _get_bit_activity(self, frames: List[bytes], max_bits: int) -> List[int]:
        """Her bir bit-iň näçeräk gezek üýtgänini (flip) hasaplaýar."""
        flips = [0] * max_bits
        if not frames:
            return flips

        prev_bits = None
        for data in frames:
            # Convert bytes to bit array
            current_bits = []
            for b in data:
                for j in range(8):
                    current_bits.append((b >> j) & 1)
            
            # Fill remaining bits with 0
            while len(current_bits) < max_bits:
                current_bits.append(0)

            if prev_bits is not None:
                for i in range(max_bits):
                    if current_bits[i] != prev_bits[i]:
                        flips[i] += 1
            
            prev_bits = current_bits
            
        return flips

    def _group_trending_bits(self, delta_bits: List[Dict]) -> List[Dict]:
        """Yzygiderli deltalary signal hökmünde toplaýar."""
        if not delta_bits:
            return []

        # Sort by bit index
        delta_bits.sort(key=lambda x: x["bit"])
        
        groups = []
        if not delta_bits: return []
        
        current_group = [delta_bits[0]]
        
        for i in range(1, len(delta_bits)):
            if delta_bits[i]["bit"] == delta_bits[i-1]["bit"] + 1:
                current_group.append(delta_bits[i])
            else:
                groups.append(current_group)
                current_group = [delta_bits[i]]
        groups.append(current_group)

        # Merge groups into candidate dicts
        candidates = []
        for g in groups:
            start = g[0]["bit"]
            length = len(g)
            avg_score = sum(i["score"] for i in g) / length
            
            # Identify most likely byte order (Simple heuristic: if it crosses byte boundary)
            byte_order = "little_endian"
            
            candidates.append({
                "start_bit": start,
                "length": length,
                "confidence": avg_score,
                "type": g[0]["type"]
            })
            
        return sorted(candidates, key=lambda x: x["confidence"], reverse=True)
