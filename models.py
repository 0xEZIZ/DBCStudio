"""
models.py - CAN DBC Data Models (Professional Edition)
Signal, Message, Node, Attribute, ValueTable, EnvironmentVariable classlary.
JSON serialization/deserialization goldawy bar (backward compatible).
"""

import json
from typing import List, Dict, Optional, Tuple, Any


# ═══════════════════════════════════════════════════════════════
#  Node (ECU)
# ═══════════════════════════════════════════════════════════════

class Node:
    """CAN Network Node (ECU) modelini görkezýär."""

    def __init__(
        self,
        name: str,
        comment: str = "",
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.comment = comment
        self.attributes = attributes or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "comment": self.comment,
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Node":
        return cls(
            name=data["name"],
            comment=data.get("comment", ""),
            attributes=data.get("attributes", {})
        )

    def __repr__(self) -> str:
        return f"Node(name='{self.name}')"


# ═══════════════════════════════════════════════════════════════
#  AttributeDefinition
# ═══════════════════════════════════════════════════════════════

class AttributeDefinition:
    """
    DBC BA_DEF_ attribute definition.
    object_type: "" (network), "BU_" (node), "BO_" (message), "SG_" (signal)
    value_type:  "INT", "FLOAT", "STRING", "ENUM", "HEX"
    """

    def __init__(
        self,
        name: str,
        object_type: str = "",
        value_type: str = "STRING",
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
        enum_values: Optional[List[str]] = None,
        default: Any = None
    ):
        self.name = name
        self.object_type = object_type  # "", "BU_", "BO_", "SG_"
        self.value_type = value_type    # "INT", "FLOAT", "STRING", "ENUM", "HEX"
        self.minimum = minimum
        self.maximum = maximum
        self.enum_values = enum_values or []
        self.default = default

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "object_type": self.object_type,
            "value_type": self.value_type,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "enum_values": self.enum_values,
            "default": self.default
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AttributeDefinition":
        return cls(
            name=data["name"],
            object_type=data.get("object_type", ""),
            value_type=data.get("value_type", "STRING"),
            minimum=data.get("minimum"),
            maximum=data.get("maximum"),
            enum_values=data.get("enum_values", []),
            default=data.get("default")
        )

    def __repr__(self) -> str:
        return (
            f"AttributeDefinition(name='{self.name}', "
            f"type='{self.object_type}', value='{self.value_type}')"
        )


# ═══════════════════════════════════════════════════════════════
#  EnvironmentVariable
# ═══════════════════════════════════════════════════════════════

class EnvironmentVariable:
    """DBC EV_ environment variable."""

    VAR_TYPES = {0: "INTEGER", 1: "FLOAT", 2: "STRING"}
    ACCESS_TYPES = {0: "UNRESTRICTED", 1: "READ", 2: "WRITE", 3: "READWRITE"}

    def __init__(
        self,
        name: str,
        var_type: int = 0,
        minimum: float = 0.0,
        maximum: float = 0.0,
        unit: str = "",
        initial_value: float = 0.0,
        ev_id: int = 0,
        access_type: int = 0,
        access_nodes: Optional[List[str]] = None,
        comment: str = "",
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.var_type = var_type
        self.minimum = minimum
        self.maximum = maximum
        self.unit = unit
        self.initial_value = initial_value
        self.ev_id = ev_id
        self.access_type = access_type
        self.access_nodes = access_nodes or ["Vector__XXX"]
        self.comment = comment
        self.attributes = attributes or {}

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "var_type": self.var_type,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "unit": self.unit,
            "initial_value": self.initial_value,
            "ev_id": self.ev_id,
            "access_type": self.access_type,
            "access_nodes": self.access_nodes,
            "comment": self.comment,
            "attributes": self.attributes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EnvironmentVariable":
        return cls(
            name=data["name"],
            var_type=data.get("var_type", 0),
            minimum=data.get("minimum", 0.0),
            maximum=data.get("maximum", 0.0),
            unit=data.get("unit", ""),
            initial_value=data.get("initial_value", 0.0),
            ev_id=data.get("ev_id", 0),
            access_type=data.get("access_type", 0),
            access_nodes=data.get("access_nodes", ["Vector__XXX"]),
            comment=data.get("comment", ""),
            attributes=data.get("attributes", {})
        )

    def __repr__(self) -> str:
        return f"EnvironmentVariable(name='{self.name}', type={self.var_type})"


# ═══════════════════════════════════════════════════════════════
#  Signal
# ═══════════════════════════════════════════════════════════════

class Signal:
    """CAN Signal modelini görkezýär (Professional Edition)."""

    def __init__(
        self,
        name: str,
        start_bit: int,
        length: int,
        byte_order: str = "little_endian",
        value_type: str = "unsigned",
        scale: float = 1.0,
        offset: float = 0.0,
        minimum: float = 0.0,
        maximum: float = 0.0,
        unit: str = "",
        receivers: Optional[List[str]] = None,
        comment: str = "",
        # ── New Professional fields ──
        multiplex_indicator: str = "",
        value_table: Optional[Dict[int, str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        is_float: bool = False
    ):
        self.name = name
        self.start_bit = start_bit
        self.length = length
        self.byte_order = byte_order
        self.value_type = value_type
        self.scale = scale
        self.offset = offset
        self.minimum = minimum
        self.maximum = maximum
        self.unit = unit
        self.receivers = receivers or ["Vector__XXX"]
        self.comment = comment
        # Professional fields
        self.multiplex_indicator = multiplex_indicator  # "", "M", "m0"-"m255"
        self.value_table = value_table or {}            # {int: str}
        self.attributes = attributes or {}              # {name: value}
        self.is_float = is_float

    @property
    def is_multiplexer(self) -> bool:
        return self.multiplex_indicator == "M"

    @property
    def is_multiplexed(self) -> bool:
        return self.multiplex_indicator.startswith("m") and self.multiplex_indicator != "M"

    @property
    def mux_value(self) -> Optional[int]:
        if self.is_multiplexed:
            try:
                return int(self.multiplex_indicator[1:])
            except ValueError:
                return None
        return None

    def to_dict(self) -> dict:
        """Signal-y dictionary görnüşine öwürýär."""
        d = {
            "name": self.name,
            "start_bit": self.start_bit,
            "length": self.length,
            "byte_order": self.byte_order,
            "value_type": self.value_type,
            "scale": self.scale,
            "offset": self.offset,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "unit": self.unit,
            "receivers": self.receivers,
            "comment": self.comment
        }
        # Only include professional fields if non-default
        if self.multiplex_indicator:
            d["multiplex_indicator"] = self.multiplex_indicator
        if self.value_table:
            # JSON keys must be strings
            d["value_table"] = {str(k): v for k, v in self.value_table.items()}
        if self.attributes:
            d["attributes"] = self.attributes
        if self.is_float:
            d["is_float"] = self.is_float
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Signal":
        """Dictionary-den Signal obýektini döredýär."""
        # Parse value_table keys back to int
        vt_raw = data.get("value_table", {})
        value_table = {int(k): v for k, v in vt_raw.items()} if vt_raw else {}

        return cls(
            name=data["name"],
            start_bit=data["start_bit"],
            length=data["length"],
            byte_order=data.get("byte_order", "little_endian"),
            value_type=data.get("value_type", "unsigned"),
            scale=data.get("scale", 1.0),
            offset=data.get("offset", 0.0),
            minimum=data.get("minimum", 0.0),
            maximum=data.get("maximum", 0.0),
            unit=data.get("unit", ""),
            receivers=data.get("receivers"),
            comment=data.get("comment", ""),
            multiplex_indicator=data.get("multiplex_indicator", ""),
            value_table=value_table,
            attributes=data.get("attributes", {}),
            is_float=data.get("is_float", False)
        )

    @property
    def byte_order_symbol(self) -> str:
        """DBC formatynda byte order belgisi: 1=Intel(LE), 0=Motorola(BE)."""
        return "1" if self.byte_order == "little_endian" else "0"

    @property
    def value_type_symbol(self) -> str:
        """DBC formatynda value type belgisi: +=unsigned, -=signed."""
        return "+" if self.value_type == "unsigned" else "-"

    @property
    def is_multiplexer(self) -> bool:
        return self.multiplex_indicator == "M"

    @property
    def is_multiplexed(self) -> bool:
        return self.multiplex_indicator.startswith("m") and self.multiplex_indicator != "M"

    @property
    def mux_value(self) -> Optional[int]:
        """Multiplexed signal-yň mux bahasy (m0=0, m5=5, ...)."""
        if self.is_multiplexed:
            try:
                return int(self.multiplex_indicator[1:])
            except ValueError:
                return None
        return None

    def __repr__(self) -> str:
        mux = f", mux='{self.multiplex_indicator}'" if self.multiplex_indicator else ""
        return (
            f"Signal(name='{self.name}', start_bit={self.start_bit}, "
            f"length={self.length}, scale={self.scale}, offset={self.offset}, "
            f"unit='{self.unit}'{mux})"
        )


# ═══════════════════════════════════════════════════════════════
#  Message
# ═══════════════════════════════════════════════════════════════

class Message:
    """CAN Message modelini görkezýär (Professional Edition)."""

    def __init__(
        self,
        message_id: int,
        name: str,
        dlc: int = 8,
        sender: str = "Vector__XXX",
        signals: Optional[List[Signal]] = None,
        comment: str = "",
        # ── New Professional fields ──
        attributes: Optional[Dict[str, Any]] = None,
        signal_groups: Optional[List[dict]] = None,
        transmitters: Optional[List[str]] = None
    ):
        self.message_id = message_id
        self.name = name
        self.dlc = dlc
        self.sender = sender
        self.signals = signals or []
        self.comment = comment
        # Professional fields
        self.attributes = attributes or {}
        self.signal_groups = signal_groups or []
        self.transmitters = transmitters or []

    def add_signal(self, signal: Signal):
        """Message-e täze signal goşýar."""
        self.signals.append(signal)

    def remove_signal(self, signal_name: str):
        """Ady boýunça signal aýyrýar."""
        self.signals = [s for s in self.signals if s.name != signal_name]

    def get_signal(self, signal_name: str) -> Optional[Signal]:
        """Ady boýunça signal tapýar."""
        for signal in self.signals:
            if signal.name == signal_name:
                return signal
        return None

    def get_multiplexer_signal(self) -> Optional[Signal]:
        """Bu message-daky Multiplexor signal-y tapýar."""
        for sig in self.signals:
            if sig.is_multiplexer:
                return sig
        return None

    def get_signals_for_mux(self, mux_value: Optional[int] = None) -> List[Signal]:
        """
        Belli bir multiplexer bahasy üçin degişli signal-lary gaýtarýar.
        mux_value: None bolsa diňe multiplexed bolmadyk signal-lar.
        """
        results = []
        for sig in self.signals:
            if not sig.multiplex_indicator:
                results.append(sig)
            elif sig.is_multiplexer:
                results.append(sig)
            elif sig.is_multiplexed and sig.mux_value == mux_value:
                results.append(sig)
        return results

    def get_multiplexed_signals(self, mux_value: int) -> List[Signal]:
        """Belli bir mux bahasy üçin signal-lary gaýtarýar."""
        return [s for s in self.signals if s.mux_value == mux_value]

    def get_static_signals(self) -> List[Signal]:
        """Mux-syz (static) signal-lary gaýtarýar."""
        return [s for s in self.signals
                if not s.multiplex_indicator or s.is_multiplexer]

    def to_dict(self) -> dict:
        """Message-i dictionary görnüşine öwürýär."""
        d = {
            "message_id": self.message_id,
            "name": self.name,
            "dlc": self.dlc,
            "sender": self.sender,
            "signals": [s.to_dict() for s in self.signals],
            "comment": self.comment
        }
        if self.attributes:
            d["attributes"] = self.attributes
        if self.signal_groups:
            d["signal_groups"] = self.signal_groups
        if self.transmitters:
            d["transmitters"] = self.transmitters
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Dictionary-den Message obýektini döredýär."""
        signals = [Signal.from_dict(s) for s in data.get("signals", [])]
        return cls(
            message_id=data["message_id"],
            name=data["name"],
            dlc=data.get("dlc", 8),
            sender=data.get("sender", "Vector__XXX"),
            signals=signals,
            comment=data.get("comment", ""),
            attributes=data.get("attributes", {}),
            signal_groups=data.get("signal_groups", []),
            transmitters=data.get("transmitters", [])
        )

    def __repr__(self) -> str:
        return (
            f"Message(id=0x{self.message_id:03X}, name='{self.name}', "
            f"dlc={self.dlc}, signals={len(self.signals)})"
        )


# ═══════════════════════════════════════════════════════════════
#  DBCDatabase
# ═══════════════════════════════════════════════════════════════

class DBCDatabase:
    """Tutuş DBC bazasyny görkezýär (Professional Edition)."""

    def __init__(
        self,
        version: str = "",
        messages: Optional[List[Message]] = None,
        description: str = "",
        # ── New Professional fields ──
        nodes: Optional[List[Node]] = None,
        attribute_definitions: Optional[List[AttributeDefinition]] = None,
        attribute_defaults: Optional[Dict[str, Any]] = None,
        network_attributes: Optional[Dict[str, Any]] = None,
        value_tables: Optional[Dict[str, Dict[int, str]]] = None,
        environment_variables: Optional[List[EnvironmentVariable]] = None,
        new_symbols: Optional[List[str]] = None,
        bus_speed: int = 0
    ):
        self.version = version
        self.messages = messages or []
        self.description = description
        # Professional fields
        self.nodes = nodes or []
        self.attribute_definitions = attribute_definitions or []
        self.attribute_defaults = attribute_defaults or {}
        self.network_attributes = network_attributes or {}
        self.value_tables = value_tables or {}       # global VAL_TABLE_
        self.environment_variables = environment_variables or []
        self.new_symbols = new_symbols or []
        self.bus_speed = bus_speed

    # ── Message CRUD ──

    def add_message(self, message: Message):
        """Baza täze message goşýar."""
        self.messages.append(message)

    def remove_message(self, message_id: int):
        """ID boýunça message aýyrýar."""
        self.messages = [m for m in self.messages if m.message_id != message_id]

    def get_message(self, message_id: int) -> Optional[Message]:
        """ID boýunça message tapýar."""
        for message in self.messages:
            if message.message_id == message_id:
                return message
        return None

    def get_message_by_name(self, name: str) -> Optional[Message]:
        """Ady boýunça message tapýar."""
        for message in self.messages:
            if message.name == name:
                return message
        return None

    # ── Utility Methods (NEW) ──

    def get_signal_by_name(self, name: str) -> Optional[Tuple["Message", "Signal"]]:
        """
        Signal adyna görä gözleýär.
        Tapylsa (Message, Signal) jübütini gaýtarýar, ýogsam None.
        """
        for msg in self.messages:
            for sig in msg.signals:
                if sig.name == name:
                    return (msg, sig)
        return None

    def get_signals_by_message(self, message_id: int) -> List[Signal]:
        """Belli bir message ID üçin ähli signal-lary gaýtarýar."""
        msg = self.get_message(message_id)
        return msg.signals[:] if msg else []

    def get_node(self, name: str) -> Optional[Node]:
        """Node ady boýunça tapýar."""
        for node in self.nodes:
            if node.name == name:
                return node
        return None

    def get_multiplexed_signals(self, message_id: int, mux_value: int) -> List[Signal]:
        """Belli bir message we mux bahasy üçin signal-lary tapýar."""
        msg = self.get_message(message_id)
        if msg:
            return msg.get_multiplexed_signals(mux_value)
        return []

    def get_attribute_definition(self, name: str) -> Optional[AttributeDefinition]:
        """Attribute definition ady boýunça tapýar."""
        for ad in self.attribute_definitions:
            if ad.name == name:
                return ad
        return None

    def merge(self, other_db: 'DBCDatabase'):
        """Başga bir database-i häzirki bilen birleşdirýär (duplicate ID-leri barlaýar)."""
        for node in other_db.nodes:
            if not self.get_node(node.name):
                self.nodes.append(node)
                
        for msg in other_db.messages:
            existing = self.get_message(msg.message_id)
            if not existing:
                self.add_message(msg)
            else:
                # Signallary birleşdir
                for sig in msg.signals:
                    if not existing.get_signal(sig.name):
                        existing.add_signal(sig)
        
        # Merge global value tables
        self.value_tables.update(other_db.value_tables)
        # Merge attributes
        for adef in other_db.attribute_definitions:
            if not self.get_attribute_definition(adef.name):
                self.attribute_definitions.append(adef)

    # ── Serialization ──

    def to_dict(self) -> dict:
        """Bazany dictionary görnüşine öwürýär."""
        d = {
            "version": self.version,
            "description": self.description,
            "messages": [m.to_dict() for m in self.messages]
        }
        if self.nodes:
            d["nodes"] = [n.to_dict() for n in self.nodes]
        if self.attribute_definitions:
            d["attribute_definitions"] = [a.to_dict() for a in self.attribute_definitions]
        if self.attribute_defaults:
            d["attribute_defaults"] = self.attribute_defaults
        if self.network_attributes:
            d["network_attributes"] = self.network_attributes
        if self.value_tables:
            # Convert int keys to string for JSON
            d["value_tables"] = {
                name: {str(k): v for k, v in entries.items()}
                for name, entries in self.value_tables.items()
            }
        if self.environment_variables:
            d["environment_variables"] = [e.to_dict() for e in self.environment_variables]
        if self.new_symbols:
            d["new_symbols"] = self.new_symbols
        if self.bus_speed:
            d["bus_speed"] = self.bus_speed
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "DBCDatabase":
        """Dictionary-den DBCDatabase obýektini döredýär (backward compatible)."""
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        nodes = [Node.from_dict(n) for n in data.get("nodes", [])]
        attr_defs = [
            AttributeDefinition.from_dict(a)
            for a in data.get("attribute_definitions", [])
        ]
        env_vars = [
            EnvironmentVariable.from_dict(e)
            for e in data.get("environment_variables", [])
        ]
        # Parse value_tables int keys
        vt_raw = data.get("value_tables", {})
        value_tables = {}
        for name, entries in vt_raw.items():
            value_tables[name] = {int(k): v for k, v in entries.items()}

        return cls(
            version=data.get("version", ""),
            messages=messages,
            description=data.get("description", ""),
            nodes=nodes,
            attribute_definitions=attr_defs,
            attribute_defaults=data.get("attribute_defaults", {}),
            network_attributes=data.get("network_attributes", {}),
            value_tables=value_tables,
            environment_variables=env_vars,
            new_symbols=data.get("new_symbols", []),
            bus_speed=data.get("bus_speed", 0)
        )

    def to_json(self, indent: int = 2) -> str:
        """Bazany JSON string görnüşine öwürýär."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> "DBCDatabase":
        """JSON string-den DBCDatabase obýektini döredýär."""
        data = json.loads(json_str)
        return cls.from_dict(data)

    def export_json(self, filepath: str, verbose: bool = True):
        """Bazany JSON faýla ýazýar."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.to_json())
        if verbose:
            print(f"[+] JSON faýla eksport edildi: {filepath}")

    @classmethod
    def import_json(cls, filepath: str) -> "DBCDatabase":
        """JSON faýldan DBCDatabase obýektini döredýär."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def __repr__(self) -> str:
        return (
            f"DBCDatabase(version='{self.version}', "
            f"messages={len(self.messages)}, "
            f"nodes={len(self.nodes)})"
        )
