"""
generator.py - DBC File Generator (Professional Edition)
Python obýektlerinden ýa-da JSON-dan dogry DBC faýl döredýär.
Full DBC spec goldawy: VAL_TABLE_, BA_DEF_, BA_DEF_DEF_, BA_,
VAL_, SIG_VALTYPE_, EV_, SG_MUL_VAL_, multiplexed signals.
"""

import json
from typing import List, Optional
from core.models import Signal, Message, DBCDatabase


class DBCGenerator:
    """DBC faýl döredýän klas (Professional Edition)."""

    # ── Correct DBC section order ──
    DEFAULT_NS_SYMBOLS = [
        "NS_DESC_", "CM_", "BA_DEF_", "BA_", "VAL_",
        "CAT_DEF_", "CAT_", "FILTER", "BA_DEF_DEF_",
        "EV_DATA_", "ENVVAR_DATA_", "SGTYPE_", "SGTYPE_VAL_",
        "BA_DEF_SGTYPE_", "BA_SGTYPE_", "SIG_TYPE_REF_",
        "VAL_TABLE_", "SIG_GROUP_", "SIG_VALTYPE_",
        "SIGTYPE_VALTYPE_", "BO_TX_BU_", "BA_REL_",
        "BA_SGTYPE_REL_", "SG_MUL_VAL_"
    ]

    def __init__(self):
        self.lines: List[str] = []

    def generate(self, database: DBCDatabase) -> str:
        """DBCDatabase obýektinden DBC string döredýär (full professional)."""
        self.lines = []

        # Correct DBC section order:
        # VERSION → NS_ → BS_ → BU_ → VAL_TABLE_ →
        # BO_/SG_ → CM_ → BA_DEF_ → BA_DEF_DEF_ → BA_ →
        # VAL_ → SIG_VALTYPE_ → SG_MUL_VAL_ → EV_

        self._write_version(database.version)
        self._write_new_symbols(database)
        self._write_bus_speed(database)
        self._write_nodes(database)
        self._write_value_tables(database)
        self._write_messages(database)
        self._write_comments(database)
        self._write_attribute_definitions(database)
        self._write_attribute_defaults(database)
        self._write_attribute_values(database)
        self._write_value_descriptions(database)
        self._write_signal_value_types(database)
        self._write_extended_multiplexing(database)
        self._write_environment_variables(database)

        return "\n".join(self.lines) + "\n"

    def generate_to_file(self, database: DBCDatabase, filepath: str):
        """DBCDatabase obýektinden DBC faýl döredýär we ýazýar."""
        content = self.generate(database)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[+] DBC faýl döredildi: {filepath}")

    def generate_from_json(self, json_filepath: str, output_filepath: str):
        """JSON faýldan DBC faýl döredýär."""
        database = DBCDatabase.import_json(json_filepath)
        self.generate_to_file(database, output_filepath)

    # ═══════════════════════════════════════════════════════════
    #  Section Writers
    # ═══════════════════════════════════════════════════════════

    def _write_version(self, version: str):
        """VERSION setirleri ýazýar."""
        self.lines.append(f'VERSION "{version}"')
        self.lines.append("")

    def _write_new_symbols(self, database: DBCDatabase):
        """NS_ bölümini ýazýar."""
        self.lines.append("NS_ :")
        symbols = database.new_symbols if database.new_symbols else self.DEFAULT_NS_SYMBOLS
        for sym in symbols:
            self.lines.append(f"\t{sym}")
        self.lines.append("")

    def _write_bus_speed(self, database: DBCDatabase):
        """BS_ (bus speed) bölümini ýazýar."""
        if database.bus_speed:
            self.lines.append(f"BS_: {database.bus_speed}")
        else:
            self.lines.append("BS_:")
        self.lines.append("")

    def _write_nodes(self, database: DBCDatabase):
        """BU_ (nodes) bölümini ýazýar."""
        if database.nodes:
            # Use explicit node list
            node_names = [n.name for n in database.nodes]
            self.lines.append(f"BU_: {' '.join(node_names)}")
        else:
            # Fallback: infer from senders/receivers
            nodes = set()
            for msg in database.messages:
                if msg.sender and msg.sender != "Vector__XXX":
                    nodes.add(msg.sender)
                for sig in msg.signals:
                    for recv in sig.receivers:
                        if recv and recv != "Vector__XXX":
                            nodes.add(recv)
            if nodes:
                self.lines.append(f"BU_: {' '.join(sorted(nodes))}")
            else:
                self.lines.append("BU_:")
        self.lines.append("")

    def _write_value_tables(self, database: DBCDatabase):
        """VAL_TABLE_ (global value tables) ýazýar."""
        if not database.value_tables:
            return
        for table_name, entries in database.value_tables.items():
            entries_str = " ".join(
                f'{val} "{desc}"' for val, desc in sorted(entries.items())
            )
            self.lines.append(f"VAL_TABLE_ {table_name} {entries_str} ;")
        self.lines.append("")

    def _write_messages(self, database: DBCDatabase):
        """BO_ we SG_ bölümlerini ýazýar."""
        for msg in database.messages:
            self.lines.append(
                f"BO_ {msg.message_id} {msg.name}: {msg.dlc} {msg.sender}"
            )
            for sig in msg.signals:
                self._write_signal(sig)
            self.lines.append("")

    def _write_signal(self, signal: Signal):
        """SG_ setirini ýazýar (mux goldawy bilen)."""
        byte_order = signal.byte_order_symbol
        value_type = signal.value_type_symbol
        receivers = ",".join(signal.receivers) if signal.receivers else "Vector__XXX"

        scale = self._format_number(signal.scale)
        offset = self._format_number(signal.offset)
        minimum = self._format_number(signal.minimum)
        maximum = self._format_number(signal.maximum)

        # Multiplex indicator
        mux_part = f" {signal.multiplex_indicator}" if signal.multiplex_indicator else ""

        line = (
            f" SG_ {signal.name}{mux_part} : {signal.start_bit}|{signal.length}"
            f"@{byte_order}{value_type}"
            f" ({scale},{offset})"
            f" [{minimum}|{maximum}]"
            f' "{signal.unit}"'
            f" {receivers}"
        )
        self.lines.append(line)

    def _write_comments(self, database: DBCDatabase):
        """CM_ (comment) bölümlerini ýazýar (all types)."""
        has_comments = False

        # Database description
        if database.description:
            self.lines.append(f'CM_ "{database.description}";')
            has_comments = True

        # Node comments
        for node in database.nodes:
            if node.comment:
                self.lines.append(f'CM_ BU_ {node.name} "{node.comment}";')
                has_comments = True

        # Message comments
        for msg in database.messages:
            if msg.comment:
                self.lines.append(f'CM_ BO_ {msg.message_id} "{msg.comment}";')
                has_comments = True

            # Signal comments
            for sig in msg.signals:
                if sig.comment:
                    self.lines.append(
                        f'CM_ SG_ {msg.message_id} {sig.name} "{sig.comment}";'
                    )
                    has_comments = True

        # Environment variable comments
        for ev in database.environment_variables:
            if ev.comment:
                self.lines.append(f'CM_ EV_ {ev.name} "{ev.comment}";')
                has_comments = True

        if has_comments:
            self.lines.append("")

    def _write_attribute_definitions(self, database: DBCDatabase):
        """BA_DEF_ attribute definitions ýazýar."""
        if not database.attribute_definitions:
            return

        for attr_def in database.attribute_definitions:
            obj = f"{attr_def.object_type} " if attr_def.object_type else ""

            if attr_def.value_type in ("INT", "HEX"):
                mn = int(attr_def.minimum) if attr_def.minimum is not None else 0
                mx = int(attr_def.maximum) if attr_def.maximum is not None else 0
                self.lines.append(
                    f'BA_DEF_ {obj}"{attr_def.name}" {attr_def.value_type} {mn} {mx};'
                )
            elif attr_def.value_type == "FLOAT":
                mn = attr_def.minimum if attr_def.minimum is not None else 0.0
                mx = attr_def.maximum if attr_def.maximum is not None else 0.0
                self.lines.append(
                    f'BA_DEF_ {obj}"{attr_def.name}" FLOAT '
                    f'{self._format_number(mn)} {self._format_number(mx)};'
                )
            elif attr_def.value_type == "STRING":
                self.lines.append(
                    f'BA_DEF_ {obj}"{attr_def.name}" STRING;'
                )
            elif attr_def.value_type == "ENUM":
                enum_str = ",".join(f'"{v}"' for v in attr_def.enum_values)
                self.lines.append(
                    f'BA_DEF_ {obj}"{attr_def.name}" ENUM {enum_str};'
                )

        self.lines.append("")

    def _write_attribute_defaults(self, database: DBCDatabase):
        """BA_DEF_DEF_ attribute defaults ýazýar."""
        if not database.attribute_defaults:
            return

        for attr_name, default_val in database.attribute_defaults.items():
            if isinstance(default_val, str):
                self.lines.append(f'BA_DEF_DEF_ "{attr_name}" "{default_val}";')
            else:
                self.lines.append(
                    f'BA_DEF_DEF_ "{attr_name}" {self._format_number(default_val)};'
                )

        self.lines.append("")

    def _write_attribute_values(self, database: DBCDatabase):
        """BA_ attribute values ýazýar (network, node, message, signal)."""
        has_attrs = False

        # Network-level
        for attr_name, value in database.network_attributes.items():
            if isinstance(value, str):
                self.lines.append(f'BA_ "{attr_name}" "{value}";')
            else:
                self.lines.append(
                    f'BA_ "{attr_name}" {self._format_number(value)};'
                )
            has_attrs = True

        # Node-level
        for node in database.nodes:
            for attr_name, value in node.attributes.items():
                val_str = f'"{value}"' if isinstance(value, str) else self._format_number(value)
                self.lines.append(f'BA_ "{attr_name}" BU_ {node.name} {val_str};')
                has_attrs = True

        # Message-level
        for msg in database.messages:
            for attr_name, value in msg.attributes.items():
                val_str = f'"{value}"' if isinstance(value, str) else self._format_number(value)
                self.lines.append(
                    f'BA_ "{attr_name}" BO_ {msg.message_id} {val_str};'
                )
                has_attrs = True

            # Signal-level
            for sig in msg.signals:
                for attr_name, value in sig.attributes.items():
                    val_str = f'"{value}"' if isinstance(value, str) else self._format_number(value)
                    self.lines.append(
                        f'BA_ "{attr_name}" SG_ {msg.message_id} {sig.name} {val_str};'
                    )
                    has_attrs = True

        if has_attrs:
            self.lines.append("")

    def _write_value_descriptions(self, database: DBCDatabase):
        """VAL_ (signal-level value descriptions) ýazýar."""
        has_vals = False

        for msg in database.messages:
            for sig in msg.signals:
                if sig.value_table:
                    entries = " ".join(
                        f'{val} "{desc}"'
                        for val, desc in sorted(sig.value_table.items())
                    )
                    self.lines.append(
                        f"VAL_ {msg.message_id} {sig.name} {entries} ;"
                    )
                    has_vals = True

        if has_vals:
            self.lines.append("")

    def _write_signal_value_types(self, database: DBCDatabase):
        """SIG_VALTYPE_ (float signals) ýazýar."""
        has_float = False

        for msg in database.messages:
            for sig in msg.signals:
                if sig.is_float:
                    val_type = 1  # IEEE float
                    if sig.length == 64:
                        val_type = 2  # IEEE double
                    self.lines.append(
                        f"SIG_VALTYPE_ {msg.message_id} {sig.name} : {val_type};"
                    )
                    has_float = True

        if has_float:
            self.lines.append("")

    def _write_extended_multiplexing(self, database: DBCDatabase):
        """SG_MUL_VAL_ extended multiplexing ýazýar."""
        has_mux = False

        for msg in database.messages:
            mux_sig = msg.get_multiplexer_signal()
            if not mux_sig:
                continue

            for sig in msg.signals:
                if sig.is_multiplexed and sig.mux_value is not None:
                    self.lines.append(
                        f"SG_MUL_VAL_ {msg.message_id} {sig.name} "
                        f"{mux_sig.name} {sig.mux_value}-{sig.mux_value};"
                    )
                    has_mux = True

        if has_mux:
            self.lines.append("")

    def _write_environment_variables(self, database: DBCDatabase):
        """EV_ environment variables ýazýar."""
        if not database.environment_variables:
            return

        for ev in database.environment_variables:
            access_nodes = ",".join(ev.access_nodes)
            self.lines.append(
                f'EV_ {ev.name} : {ev.var_type} '
                f'[{self._format_number(ev.minimum)}|{self._format_number(ev.maximum)}] '
                f'"{ev.unit}" {self._format_number(ev.initial_value)} {ev.ev_id} '
                f'DUMMY_NODE_VECTOR0 {access_nodes};'
            )

        self.lines.append("")

    # ═══════════════════════════════════════════════════════════

    @staticmethod
    def _format_number(value) -> str:
        """Sany DBC-e laýyk formatda ýazýar."""
        if isinstance(value, float):
            # Preserve negative zero as "0" (DBC convention)
            if value == 0.0:
                return "0"
            if value.is_integer():
                return str(int(value))
            return str(value)
        return str(value)


# ═══════════════════════════════════════════════════════════════
#  Convenience Functions
# ═══════════════════════════════════════════════════════════════

def generate_dbc(database: DBCDatabase, filepath: str):
    """DBC faýl döretmek üçin ýönekeý funksiýa."""
    generator = DBCGenerator()
    generator.generate_to_file(database, filepath)


def generate_dbc_from_json(json_filepath: str, output_filepath: str):
    """JSON faýldan DBC faýl döretmek üçin ýönekeý funksiýa."""
    generator = DBCGenerator()
    generator.generate_from_json(json_filepath, output_filepath)
