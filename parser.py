"""
parser.py - DBC File Parser (Professional Edition)
*.dbc faýllaryny okaýar we analiz edýär.
Full DBC spec goldawy: BU_, VAL_TABLE_, VAL_, BA_DEF_, BA_DEF_DEF_,
BA_, EV_, SIG_VALTYPE_, SG_MUL_VAL_, multiplexed signals.
"""

import re
from typing import List, Optional, Dict, Any
from models import (
    Signal, Message, DBCDatabase,
    Node, AttributeDefinition, EnvironmentVariable
)


class DBCParser:
    """DBC faýllaryny parse edýän klas (Professional Edition)."""

    # ── Core regexes ──
    RE_VERSION = re.compile(r'^VERSION\s+"(.*)"', re.MULTILINE)
    RE_MESSAGE = re.compile(
        r'^BO_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s+(\w+)',
        re.MULTILINE
    )
    # Signal with optional mux indicator: SG_ name mux_indicator : ...
    # Proper float pattern for scale/offset/min/max (handles negatives, scientific notation)
    _FLOAT = r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
    RE_SIGNAL = re.compile(
        r'^\s+SG_\s+(\w+)\s+(M|m\d+)?\s*:\s*(\d+)\|(\d+)@([01])([+-])'
        r'\s*\(\s*(' + _FLOAT + r')\s*,\s*(' + _FLOAT + r')\s*\)'
        r'\s*\[\s*(' + _FLOAT + r')\s*\|\s*(' + _FLOAT + r')\s*\]'
        r'\s*"([^"]*)"'
        r'\s*(.*)',
        re.MULTILINE
    )

    # ── Nodes ──
    RE_NODES = re.compile(r'^BU_\s*:\s*(.*)', re.MULTILINE)

    # ── Comments (multi-line support via re.DOTALL) ──
    RE_COMMENT_GENERAL = re.compile(
        r'^CM_\s+"((?:[^"\\]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL
    )
    RE_COMMENT_NODE = re.compile(
        r'^CM_\s+BU_\s+(\w+)\s+"((?:[^"\\]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL
    )
    RE_COMMENT_MESSAGE = re.compile(
        r'^CM_\s+BO_\s+(\d+)\s+"((?:[^"\\]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL
    )
    RE_COMMENT_SIGNAL = re.compile(
        r'^CM_\s+SG_\s+(\d+)\s+(\w+)\s+"((?:[^"\\]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL
    )
    RE_COMMENT_ENV = re.compile(
        r'^CM_\s+EV_\s+(\w+)\s+"((?:[^"\\]|\\.)*)"\s*;', re.MULTILINE | re.DOTALL
    )

    # ── Value Tables ──
    RE_VAL_TABLE = re.compile(
        r'^VAL_TABLE_\s+(\w+)((?:\s+\d+\s+"[^"]*")*)\s*;', re.MULTILINE
    )
    RE_VAL_ENTRY = re.compile(r'(\d+)\s+"([^"]*)"')

    # ── Value Descriptions (signal-level enums) ──
    RE_VAL_DESC = re.compile(
        r'^VAL_\s+(\d+)\s+(\w+)((?:\s+\d+\s+"[^"]*")*)\s*;', re.MULTILINE
    )

    # ── Attribute Definitions ──
    # BA_DEF_ [object_type] "attr_name" value_type [params] ;
    RE_ATTR_DEF_INT = re.compile(
        r'^BA_DEF_\s*(BU_|BO_|SG_|EV_)?\s*"([^"]+)"\s+'
        r'(INT|HEX)\s+(-?\d+)\s+(-?\d+)\s*;', re.MULTILINE
    )
    RE_ATTR_DEF_FLOAT = re.compile(
        r'^BA_DEF_\s*(BU_|BO_|SG_|EV_)?\s*"([^"]+)"\s+'
        r'FLOAT\s+([eE\d.+-]+)\s+([eE\d.+-]+)\s*;', re.MULTILINE
    )
    RE_ATTR_DEF_STRING = re.compile(
        r'^BA_DEF_\s*(BU_|BO_|SG_|EV_)?\s*"([^"]+)"\s+STRING\s*;', re.MULTILINE
    )
    RE_ATTR_DEF_ENUM = re.compile(
        r'^BA_DEF_\s*(BU_|BO_|SG_|EV_)?\s*"([^"]+)"\s+'
        r'ENUM\s+((?:"[^"]*"\s*,?\s*)+);', re.MULTILINE
    )

    # ── Attribute Defaults ──
    RE_ATTR_DEF_DEF_NUM = re.compile(
        r'^BA_DEF_DEF_\s+"([^"]+)"\s+(-?[\d.eE+-]+)\s*;', re.MULTILINE
    )
    RE_ATTR_DEF_DEF_STR = re.compile(
        r'^BA_DEF_DEF_\s+"([^"]+)"\s+"([^"]*)"\s*;', re.MULTILINE
    )

    # ── Attribute Values ──
    # BA_ "name" value ;  (network) — negative lookahead prevents matching node/msg/sig lines
    RE_ATTR_VAL_NET_NUM = re.compile(
        r'^BA_\s+"([^"]+)"\s+(?!BU_|BO_|SG_|EV_)(-?[\d.eE+-]+)\s*;', re.MULTILINE
    )
    RE_ATTR_VAL_NET_STR = re.compile(
        r'^BA_\s+"([^"]+)"\s+(?!BU_|BO_|SG_|EV_)"([^"]*)"\s*;', re.MULTILINE
    )
    # BA_ "name" BU_ node_name value ;
    RE_ATTR_VAL_NODE = re.compile(
        r'^BA_\s+"([^"]+)"\s+BU_\s+(\w+)\s+(-?[\d.eE+-]+|"[^"]*")\s*;', re.MULTILINE
    )
    # BA_ "name" BO_ msg_id value ;
    RE_ATTR_VAL_MSG = re.compile(
        r'^BA_\s+"([^"]+)"\s+BO_\s+(\d+)\s+(-?[\d.eE+-]+|"[^"]*")\s*;', re.MULTILINE
    )
    # BA_ "name" SG_ msg_id signal_name value ;
    RE_ATTR_VAL_SIG = re.compile(
        r'^BA_\s+"([^"]+)"\s+SG_\s+(\d+)\s+(\w+)\s+(-?[\d.eE+-]+|"[^"]*")\s*;',
        re.MULTILINE
    )

    # ── Environment Variables ──
    RE_ENV_VAR = re.compile(
        r'^EV_\s+(\w+)\s*:\s*(\d+)\s*\[\s*([eE\d.+-]+)\s*\|\s*([eE\d.+-]+)\s*\]'
        r'\s*"([^"]*)"\s*([eE\d.+-]+)\s*(\d+)'
        r'\s*DUMMY_NODE_VECTOR\d*\s*(.*?)\s*;',
        re.MULTILINE
    )

    # ── Signal Value Type (float indicator) ──
    RE_SIG_VALTYPE = re.compile(
        r'^SIG_VALTYPE_\s+(\d+)\s+(\w+)\s*:\s*(\d+)\s*;', re.MULTILINE
    )

    # ── Signal Multiplexing (extended) ──
    RE_SG_MUL_VAL = re.compile(
        r'^SG_MUL_VAL_\s+(\d+)\s+(\w+)\s+(\w+)\s+'
        r'([\d-]+)\s*-\s*([\d-]+)\s*;', re.MULTILINE
    )

    # ── Bus Speed ──
    RE_BUS_SPEED = re.compile(r'^BS_\s*:\s*(\d+)?', re.MULTILINE)

    # ── New Symbols ──
    RE_NEW_SYMBOLS = re.compile(r'^NS_\s*:', re.MULTILINE)

    def __init__(self):
        self.database = DBCDatabase()

    def parse_file(self, filepath: str) -> DBCDatabase:
        """DBC faýly okaýar we DBCDatabase obýektini gaýtarýar."""
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return self.parse_string(content)

    def parse_string(self, content: str) -> DBCDatabase:
        """DBC string mazmunyny parse edýär (full professional)."""
        self.database = DBCDatabase()

        # 1. Version
        self._parse_version(content)

        # 2. New Symbols
        self._parse_new_symbols(content)

        # 3. Bus Speed
        self._parse_bus_speed(content)

        # 4. Nodes (BU_)
        self._parse_nodes(content)

        # 5. Global Value Tables (VAL_TABLE_)
        self._parse_value_tables(content)

        # 6. Messages and Signals (BO_ + SG_)
        self._parse_messages(content)

        # 7. Comments (CM_)
        self._parse_comments(content)

        # 8. Attribute Definitions (BA_DEF_)
        self._parse_attribute_definitions(content)

        # 9. Attribute Defaults (BA_DEF_DEF_)
        self._parse_attribute_defaults(content)

        # 10. Attribute Values (BA_)
        self._parse_attribute_values(content)

        # 11. Value Descriptions (VAL_)
        self._parse_value_descriptions(content)

        # 12. Signal Value Types (SIG_VALTYPE_)
        self._parse_signal_value_types(content)

        # 13. Environment Variables (EV_)
        self._parse_environment_variables(content)

        # 14. Extended Multiplexing (SG_MUL_VAL_)
        self._parse_extended_multiplexing(content)

        return self.database

    # ═══════════════════════════════════════════════════════════
    #  Parse Methods
    # ═══════════════════════════════════════════════════════════

    def _parse_version(self, content: str):
        """VERSION setirini parse edýär."""
        match = self.RE_VERSION.search(content)
        if match:
            self.database.version = match.group(1)

    def _parse_new_symbols(self, content: str):
        """NS_ bölümini parse edýär."""
        match = self.RE_NEW_SYMBOLS.search(content)
        if match:
            # NS_ soňundaky setirlerden symbols topla
            pos = match.end()
            symbols = []
            for line in content[pos:].split("\n"):
                stripped = line.strip()
                if not stripped:
                    break
                if stripped.isidentifier() or stripped.endswith("_"):
                    symbols.append(stripped)
            self.database.new_symbols = symbols

    def _parse_bus_speed(self, content: str):
        """BS_ setirini parse edýär."""
        match = self.RE_BUS_SPEED.search(content)
        if match and match.group(1):
            self.database.bus_speed = int(match.group(1))

    def _parse_nodes(self, content: str):
        """BU_ (nodes) setirini parse edýär."""
        match = self.RE_NODES.search(content)
        if match:
            names_str = match.group(1).strip()
            if names_str:
                names = names_str.split()
                for name in names:
                    name = name.strip()
                    if name:
                        self.database.nodes.append(Node(name=name))

    def _parse_value_tables(self, content: str):
        """VAL_TABLE_ (global value tables) parse edýär."""
        for match in self.RE_VAL_TABLE.finditer(content):
            table_name = match.group(1)
            entries_str = match.group(2)
            entries = {}
            for entry_match in self.RE_VAL_ENTRY.finditer(entries_str):
                val = int(entry_match.group(1))
                desc = entry_match.group(2)
                entries[val] = desc
            self.database.value_tables[table_name] = entries

    def _parse_messages(self, content: str):
        """BO_ (message) we SG_ (signal) setirlerini parse edýär."""
        lines = content.split("\n")
        current_message = None

        for line in lines:
            # Message setirini barla
            msg_match = self.RE_MESSAGE.match(line)
            if msg_match:
                msg_id = int(msg_match.group(1))
                msg_name = msg_match.group(2)
                dlc = int(msg_match.group(3))
                sender = msg_match.group(4)

                current_message = Message(
                    message_id=msg_id,
                    name=msg_name,
                    dlc=dlc,
                    sender=sender
                )
                self.database.add_message(current_message)
                continue

            # Signal setirini barla
            if current_message is not None:
                sig_match = self.RE_SIGNAL.match(line)
                if sig_match:
                    signal = self._build_signal(sig_match)
                    current_message.add_signal(signal)
                elif line.strip() == "" or (not line.startswith(" ") and not line.startswith("\t")):
                    if line.strip() != "" and not line.startswith(" "):
                        current_message = None

    def _build_signal(self, match: re.Match) -> Signal:
        """Regex match-den Signal obýektini gurýar (mux goldawy bilen)."""
        name = match.group(1)
        mux_indicator = match.group(2) or ""  # "M", "m0", "m5", etc.
        start_bit = int(match.group(3))
        length = int(match.group(4))

        byte_order_num = match.group(5)
        byte_order = "little_endian" if byte_order_num == "1" else "big_endian"

        value_type_char = match.group(6)
        value_type = "unsigned" if value_type_char == "+" else "signed"

        scale = float(match.group(7))
        offset = float(match.group(8))
        minimum = float(match.group(9))
        maximum = float(match.group(10))
        unit = match.group(11)

        receivers_str = match.group(12).strip()
        if receivers_str:
            receivers = [r.strip() for r in receivers_str.split(",") if r.strip()]
        else:
            receivers = ["Vector__XXX"]

        return Signal(
            name=name,
            start_bit=start_bit,
            length=length,
            byte_order=byte_order,
            value_type=value_type,
            scale=scale,
            offset=offset,
            minimum=minimum,
            maximum=maximum,
            unit=unit,
            receivers=receivers,
            multiplex_indicator=mux_indicator
        )

    def _parse_comments(self, content: str):
        """CM_ (comment) setirlerini parse edýär (all types)."""
        # General database comment
        for match in self.RE_COMMENT_GENERAL.finditer(content):
            # Check it's not a typed comment (BU_, BO_, SG_, EV_)
            # Extract the text between CM_ and the quote to check for type keywords
            full_match = match.group(0)
            # A general comment is: CM_ "..."; (no BU_/BO_/SG_/EV_ between CM_ and quote)
            preamble = full_match[:full_match.index('"')]
            if not any(t in preamble for t in ['BU_', 'BO_', 'SG_', 'EV_']):
                self.database.description = match.group(1)

        # Node comments
        for match in self.RE_COMMENT_NODE.finditer(content):
            node_name = match.group(1)
            comment = match.group(2)
            node = self.database.get_node(node_name)
            if node:
                node.comment = comment

        # Message comments
        for match in self.RE_COMMENT_MESSAGE.finditer(content):
            msg_id = int(match.group(1))
            comment = match.group(2)
            msg = self.database.get_message(msg_id)
            if msg:
                msg.comment = comment

        # Signal comments
        for match in self.RE_COMMENT_SIGNAL.finditer(content):
            msg_id = int(match.group(1))
            sig_name = match.group(2)
            comment = match.group(3)
            msg = self.database.get_message(msg_id)
            if msg:
                sig = msg.get_signal(sig_name)
                if sig:
                    sig.comment = comment

        # Environment variable comments
        for match in self.RE_COMMENT_ENV.finditer(content):
            ev_name = match.group(1)
            comment = match.group(2)
            for ev in self.database.environment_variables:
                if ev.name == ev_name:
                    ev.comment = comment
                    break

    def _parse_attribute_definitions(self, content: str):
        """BA_DEF_ attribute definitions parse edýär."""
        # INT / HEX
        for match in self.RE_ATTR_DEF_INT.finditer(content):
            obj_type = (match.group(1) or "").strip()
            attr_name = match.group(2)
            val_type = match.group(3)
            minimum = int(match.group(4))
            maximum = int(match.group(5))
            self.database.attribute_definitions.append(
                AttributeDefinition(
                    name=attr_name, object_type=obj_type,
                    value_type=val_type, minimum=minimum, maximum=maximum
                )
            )

        # FLOAT
        for match in self.RE_ATTR_DEF_FLOAT.finditer(content):
            obj_type = (match.group(1) or "").strip()
            attr_name = match.group(2)
            minimum = float(match.group(3))
            maximum = float(match.group(4))
            self.database.attribute_definitions.append(
                AttributeDefinition(
                    name=attr_name, object_type=obj_type,
                    value_type="FLOAT", minimum=minimum, maximum=maximum
                )
            )

        # STRING
        for match in self.RE_ATTR_DEF_STRING.finditer(content):
            obj_type = (match.group(1) or "").strip()
            attr_name = match.group(2)
            self.database.attribute_definitions.append(
                AttributeDefinition(
                    name=attr_name, object_type=obj_type,
                    value_type="STRING"
                )
            )

        # ENUM
        for match in self.RE_ATTR_DEF_ENUM.finditer(content):
            obj_type = (match.group(1) or "").strip()
            attr_name = match.group(2)
            enum_str = match.group(3)
            enum_values = re.findall(r'"([^"]*)"', enum_str)
            self.database.attribute_definitions.append(
                AttributeDefinition(
                    name=attr_name, object_type=obj_type,
                    value_type="ENUM", enum_values=enum_values
                )
            )

    def _parse_attribute_defaults(self, content: str):
        """BA_DEF_DEF_ attribute defaults parse edýär."""
        for match in self.RE_ATTR_DEF_DEF_NUM.finditer(content):
            attr_name = match.group(1)
            value_str = match.group(2)
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            self.database.attribute_defaults[attr_name] = value

            # Set the default on the definition too
            attr_def = self.database.get_attribute_definition(attr_name)
            if attr_def:
                attr_def.default = value

        for match in self.RE_ATTR_DEF_DEF_STR.finditer(content):
            attr_name = match.group(1)
            value = match.group(2)
            self.database.attribute_defaults[attr_name] = value

            attr_def = self.database.get_attribute_definition(attr_name)
            if attr_def:
                attr_def.default = value

    def _parse_attribute_values(self, content: str):
        """BA_ attribute values parse edýär (network, node, message, signal)."""
        # Network-level numeric (regex already excludes BU_/BO_/SG_/EV_ via lookahead)
        for match in self.RE_ATTR_VAL_NET_NUM.finditer(content):
            attr_name = match.group(1)
            value_str = match.group(2)
            try:
                value = int(value_str)
            except ValueError:
                value = float(value_str)
            self.database.network_attributes[attr_name] = value

        # Network-level string (regex already excludes BU_/BO_/SG_/EV_ via lookahead)
        for match in self.RE_ATTR_VAL_NET_STR.finditer(content):
            attr_name = match.group(1)
            value = match.group(2)
            self.database.network_attributes[attr_name] = value

        # Node-level
        for match in self.RE_ATTR_VAL_NODE.finditer(content):
            attr_name = match.group(1)
            node_name = match.group(2)
            value_str = match.group(3).strip('"')
            value = self._parse_value(value_str)
            node = self.database.get_node(node_name)
            if node:
                node.attributes[attr_name] = value

        # Message-level
        for match in self.RE_ATTR_VAL_MSG.finditer(content):
            attr_name = match.group(1)
            msg_id = int(match.group(2))
            value_str = match.group(3).strip('"')
            value = self._parse_value(value_str)
            msg = self.database.get_message(msg_id)
            if msg:
                msg.attributes[attr_name] = value

        # Signal-level
        for match in self.RE_ATTR_VAL_SIG.finditer(content):
            attr_name = match.group(1)
            msg_id = int(match.group(2))
            sig_name = match.group(3)
            value_str = match.group(4).strip('"')
            value = self._parse_value(value_str)
            msg = self.database.get_message(msg_id)
            if msg:
                sig = msg.get_signal(sig_name)
                if sig:
                    sig.attributes[attr_name] = value

    def _parse_value_descriptions(self, content: str):
        """VAL_ (signal-level value descriptions / enums) parse edýär."""
        for match in self.RE_VAL_DESC.finditer(content):
            msg_id = int(match.group(1))
            sig_name = match.group(2)
            entries_str = match.group(3)

            entries = {}
            for entry_match in self.RE_VAL_ENTRY.finditer(entries_str):
                val = int(entry_match.group(1))
                desc = entry_match.group(2)
                entries[val] = desc

            if entries:
                msg = self.database.get_message(msg_id)
                if msg:
                    sig = msg.get_signal(sig_name)
                    if sig:
                        sig.value_table = entries

    def _parse_signal_value_types(self, content: str):
        """SIG_VALTYPE_ (float signal indicator) parse edýär."""
        for match in self.RE_SIG_VALTYPE.finditer(content):
            msg_id = int(match.group(1))
            sig_name = match.group(2)
            val_type = int(match.group(3))
            # 1 = IEEE float, 2 = IEEE double
            if val_type in (1, 2):
                msg = self.database.get_message(msg_id)
                if msg:
                    sig = msg.get_signal(sig_name)
                    if sig:
                        sig.is_float = True

    def _parse_environment_variables(self, content: str):
        """EV_ environment variables parse edýär."""
        for match in self.RE_ENV_VAR.finditer(content):
            name = match.group(1)
            var_type = int(match.group(2))
            minimum = float(match.group(3))
            maximum = float(match.group(4))
            unit = match.group(5)
            initial = float(match.group(6))
            ev_id = int(match.group(7))
            access_str = match.group(8).strip()
            access_nodes = [n.strip() for n in access_str.split(",") if n.strip()] \
                if access_str else ["Vector__XXX"]

            self.database.environment_variables.append(
                EnvironmentVariable(
                    name=name, var_type=var_type,
                    minimum=minimum, maximum=maximum,
                    unit=unit, initial_value=initial,
                    ev_id=ev_id, access_nodes=access_nodes
                )
            )

    def _parse_extended_multiplexing(self, content: str):
        """SG_MUL_VAL_ extended multiplexing parse edýär."""
        for match in self.RE_SG_MUL_VAL.finditer(content):
            msg_id = int(match.group(1))
            sig_name = match.group(2)
            mux_sig = match.group(3)
            mux_from = int(match.group(4))
            mux_to = int(match.group(5))

            msg = self.database.get_message(msg_id)
            if msg:
                sig = msg.get_signal(sig_name)
                if sig and not sig.multiplex_indicator:
                    sig.multiplex_indicator = f"m{mux_from}"

    @staticmethod
    def _parse_value(value_str: str) -> Any:
        """String bahany dogry tipe öwürýär."""
        try:
            return int(value_str)
        except ValueError:
            try:
                return float(value_str)
            except ValueError:
                return value_str


# ═══════════════════════════════════════════════════════════════
#  Convenience Functions
# ═══════════════════════════════════════════════════════════════

def parse_dbc(filepath: str) -> DBCDatabase:
    """DBC faýly parse etmek üçin ýönekeý funksiýa."""
    parser = DBCParser()
    return parser.parse_file(filepath)


def print_database_summary(db: DBCDatabase):
    """DBC database-niň gysgaça mazmunyny çap edýär."""
    print(f"{'='*60}")
    print(f"DBC Database Summary")
    print(f"{'='*60}")
    print(f"Version: {db.version or '(not specified)'}")
    print(f"Nodes: {', '.join(n.name for n in db.nodes) or '(none)'}")
    print(f"Total messages: {len(db.messages)}")
    total_sigs = sum(len(m.signals) for m in db.messages)
    print(f"Total signals:  {total_sigs}")
    if db.attribute_definitions:
        print(f"Attribute defs: {len(db.attribute_definitions)}")
    if db.value_tables:
        print(f"Value tables:   {len(db.value_tables)}")
    if db.environment_variables:
        print(f"Env variables:  {len(db.environment_variables)}")
    print(f"{'='*60}")

    for msg in db.messages:
        print(f"\n  Message: {msg.name}")
        print(f"    ID: 0x{msg.message_id:03X} ({msg.message_id})")
        print(f"    DLC: {msg.dlc}")
        print(f"    Sender: {msg.sender}")
        if msg.comment:
            print(f"    Comment: {msg.comment}")
        if msg.attributes:
            print(f"    Attributes: {msg.attributes}")
        print(f"    Signals ({len(msg.signals)}):")

        for sig in msg.signals:
            order = "Intel" if sig.byte_order == "little_endian" else "Motorola"
            vtype = "Unsigned" if sig.value_type == "unsigned" else "Signed"
            mux = f" [{sig.multiplex_indicator}]" if sig.multiplex_indicator else ""
            print(f"      - {sig.name}{mux}")
            print(f"        Bit: {sig.start_bit}|{sig.length} [{order}, {vtype}]")
            print(f"        Scale: {sig.scale}, Offset: {sig.offset}")
            print(f"        Range: [{sig.minimum} .. {sig.maximum}]")
            print(f"        Unit: '{sig.unit}'")
            if sig.comment:
                print(f"        Comment: {sig.comment}")
            if sig.value_table:
                print(f"        Values: {sig.value_table}")
            if sig.attributes:
                print(f"        Attrs: {sig.attributes}")

    print(f"\n{'='*60}")
