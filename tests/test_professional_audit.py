"""
Professional Audit Test Suite - Comprehensive Validation
Tests all core modules: models, parser, generator, encoder, ai_module, analyzer
Edge cases: Multiplexing, signed signals, float signals, attributes, value tables
"""
import sys
import traceback

PASS_COUNT = 0
FAIL_COUNT = 0

def test(name, condition, detail=""):
    global PASS_COUNT, FAIL_COUNT
    if condition:
        PASS_COUNT += 1
        print(f"  [PASS] {name}")
    else:
        FAIL_COUNT += 1
        print(f"  [FAIL] {name} — {detail}")

def run_all():
    global PASS_COUNT, FAIL_COUNT
    
    # ═══════════════════════════════════════
    # 1. Models — Signal edge cases
    # ═══════════════════════════════════════
    print("\n═══ 1. Models: Signal Edge Cases ═══")
    from core.models import Signal, Message, DBCDatabase, Node, AttributeDefinition, EnvironmentVariable

    # Multiplexer signal
    mux_sig = Signal(name="MuxSwitch", start_bit=0, length=4, multiplex_indicator="M")
    test("MUX signal is_multiplexer", mux_sig.is_multiplexer)
    test("MUX signal NOT is_multiplexed", not mux_sig.is_multiplexed)
    test("MUX signal mux_value is None", mux_sig.mux_value is None)

    # Multiplexed signals
    m_sig = Signal(name="Speed_M0", start_bit=8, length=16, multiplex_indicator="m0")
    test("m0 signal is_multiplexed", m_sig.is_multiplexed)
    test("m0 signal mux_value == 0", m_sig.mux_value == 0)

    m_sig5 = Signal(name="Speed_M5", start_bit=8, length=16, multiplex_indicator="m5")
    test("m5 signal mux_value == 5", m_sig5.mux_value == 5)

    # Static signal (no mux)
    static_sig = Signal(name="Static", start_bit=24, length=8)
    test("Static signal NOT multiplexer", not static_sig.is_multiplexer)
    test("Static signal NOT multiplexed", not static_sig.is_multiplexed)
    test("Static mux_value is None", static_sig.mux_value is None)

    # Byte order and value type symbols
    intel_sig = Signal(name="A", start_bit=0, length=8, byte_order="little_endian", value_type="unsigned")
    moto_sig = Signal(name="B", start_bit=0, length=8, byte_order="big_endian", value_type="signed")
    test("Intel byte_order_symbol == '1'", intel_sig.byte_order_symbol == "1")
    test("Motorola byte_order_symbol == '0'", moto_sig.byte_order_symbol == "0")
    test("Unsigned value_type_symbol == '+'", intel_sig.value_type_symbol == "+")
    test("Signed value_type_symbol == '-'", moto_sig.value_type_symbol == "-")

    # Signal serialization with value_table
    vt_sig = Signal(name="Gear", start_bit=0, length=4, value_table={0: "Park", 1: "Reverse", 2: "Drive"})
    d = vt_sig.to_dict()
    test("value_table keys serialized as strings", all(isinstance(k, str) for k in d["value_table"].keys()))
    restored = Signal.from_dict(d)
    test("value_table restored with int keys", all(isinstance(k, int) for k in restored.value_table.keys()))
    test("Gear value_table round-trip", restored.value_table == {0: "Park", 1: "Reverse", 2: "Drive"})

    # Float signal
    float_sig = Signal(name="Temp", start_bit=0, length=32, is_float=True)
    fd = float_sig.to_dict()
    test("Float signal serialization", fd.get("is_float") is True)
    rf = Signal.from_dict(fd)
    test("Float signal deserialization", rf.is_float is True)

    # ═══════════════════════════════════════
    # 2. Models — Message with MUX
    # ═══════════════════════════════════════
    print("\n═══ 2. Models: Message MUX Operations ═══")
    msg = Message(message_id=0x300, name="MuxMsg", dlc=8, signals=[mux_sig, m_sig, m_sig5, static_sig])
    
    test("get_multiplexer_signal", msg.get_multiplexer_signal() == mux_sig)
    test("get_signal by name", msg.get_signal("Speed_M0") == m_sig)
    test("get_signal not found", msg.get_signal("NoExist") is None)
    
    # get_signals_for_mux
    mux0_sigs = msg.get_signals_for_mux(0)
    test("get_signals_for_mux(0) includes static", static_sig in mux0_sigs)
    test("get_signals_for_mux(0) includes mux sig", mux_sig in mux0_sigs)
    test("get_signals_for_mux(0) includes m0", m_sig in mux0_sigs)
    test("get_signals_for_mux(0) excludes m5", m_sig5 not in mux0_sigs)
    
    mux5_sigs = msg.get_signals_for_mux(5)
    test("get_signals_for_mux(5) includes m5", m_sig5 in mux5_sigs)
    test("get_signals_for_mux(5) excludes m0", m_sig not in mux5_sigs)

    # get_static_signals
    statics = msg.get_static_signals()
    test("Static signals include MuxSwitch", mux_sig in statics)
    test("Static signals include Static", static_sig in statics)
    test("Static signals exclude m0", m_sig not in statics)

    # ═══════════════════════════════════════
    # 3. Models — DBCDatabase merge
    # ═══════════════════════════════════════
    print("\n═══ 3. Models: DBCDatabase Merge ═══")
    db1 = DBCDatabase(version="1.0")
    db1.nodes.append(Node(name="ECU1"))
    db1.add_message(Message(message_id=0x100, name="Msg1", dlc=8))
    
    db2 = DBCDatabase(version="2.0")
    db2.nodes.append(Node(name="ECU1"))  # duplicate
    db2.nodes.append(Node(name="ECU2"))  # new
    db2.add_message(Message(message_id=0x100, name="Msg1", dlc=8))  # dup msg
    db2.add_message(Message(message_id=0x200, name="Msg2", dlc=8))  # new msg
    
    db1.merge(db2)
    test("Merge: no dup nodes", len(db1.nodes) == 2)
    test("Merge: no dup messages", len(db1.messages) == 2)
    test("Merge: new msg added", db1.get_message(0x200) is not None)

    # ═══════════════════════════════════════
    # 4. Encoder — Signed values
    # ═══════════════════════════════════════
    print("\n═══ 4. Encoder: Signed Values & Edge Cases ═══")
    from logic.encoder import CANEncoder
    enc = CANEncoder()
    
    # Signed signal encode/decode
    signed_sig = Signal(name="Temp", start_bit=0, length=8, byte_order="little_endian",
                        value_type="signed", scale=1.0, offset=-40.0)
    signed_msg = Message(message_id=0x400, name="TempMsg", dlc=8, signals=[signed_sig])
    
    # Encode -20°C: raw = (-20 - (-40)) / 1.0 = 20
    encoded = enc.encode_message(signed_msg, {"Temp": -20.0})
    decoded = enc.decode_message(signed_msg, encoded)
    test("Signed encode/decode -20°C", abs(decoded["Temp"] - (-20.0)) < 0.01,
         f"Got {decoded.get('Temp')}")
    
    # Encode 0°C: raw = (0 - (-40)) / 1.0 = 40
    encoded = enc.encode_message(signed_msg, {"Temp": 0.0})
    decoded = enc.decode_message(signed_msg, encoded)
    test("Signed encode/decode 0°C", abs(decoded["Temp"] - 0.0) < 0.01,
         f"Got {decoded.get('Temp')}")
    
    # Negative raw values (2's complement)
    neg_sig = Signal(name="Angle", start_bit=0, length=16, byte_order="little_endian",
                     value_type="signed", scale=0.1, offset=0.0)
    neg_msg = Message(message_id=0x500, name="AngleMsg", dlc=8, signals=[neg_sig])
    
    encoded = enc.encode_message(neg_msg, {"Angle": -100.0})
    decoded = enc.decode_message(neg_msg, encoded)
    test("Signed 16-bit encode/decode -100.0", abs(decoded["Angle"] - (-100.0)) < 0.1,
         f"Got {decoded.get('Angle')}")
    
    # Motorola byte order
    moto_encode_sig = Signal(name="MotorSig", start_bit=7, length=16,
                              byte_order="big_endian", value_type="unsigned",
                              scale=1.0, offset=0.0)
    moto_msg = Message(message_id=0x600, name="MotoMsg", dlc=8, signals=[moto_encode_sig])
    
    encoded = enc.encode_message(moto_msg, {"MotorSig": 1000})
    decoded = enc.decode_message(moto_msg, encoded)
    test("Motorola 16-bit encode/decode 1000", abs(decoded["MotorSig"] - 1000) < 0.1,
         f"Got {decoded.get('MotorSig')}")

    # Scale zero edge case
    zero_scale_sig = Signal(name="Zero", start_bit=0, length=8, scale=0.0)
    raw = enc._physical_to_raw(zero_scale_sig, 100.0)
    test("Scale=0 returns raw=0", raw == 0)

    # ═══════════════════════════════════════
    # 5. Parser/Generator — Complex DBC
    # ═══════════════════════════════════════
    print("\n═══ 5. Parser/Generator: Complex DBC Round-trip ═══")
    from logic.parser import DBCParser
    from logic.generator import DBCGenerator
    
    # Build complex database
    db = DBCDatabase(version="2.5", description="Full Professional Test")
    db.nodes = [Node(name="ECU_A", comment="Engine Control"), Node(name="TCU")]
    db.attribute_definitions.append(
        AttributeDefinition(name="BusType", object_type="", value_type="STRING")
    )
    db.attribute_defaults["BusType"] = "CAN"
    db.network_attributes["BusType"] = "CAN FD"
    db.value_tables["GearVT"] = {0: "Park", 1: "Reverse", 2: "Neutral", 3: "Drive"}
    
    msg1 = Message(message_id=0x100, name="EngineData", dlc=8, sender="ECU_A",
                   comment="Main engine message")
    sig1 = Signal(name="Speed", start_bit=0, length=16, byte_order="little_endian",
                  value_type="unsigned", scale=0.01, offset=0.0, minimum=0, maximum=655.35,
                  unit="km/h", comment="Vehicle speed")
    sig2 = Signal(name="RPM", start_bit=16, length=16, byte_order="little_endian",
                  value_type="unsigned", scale=0.25, offset=0.0, minimum=0, maximum=16383.75,
                  unit="rpm", comment="Engine RPM")
    sig3 = Signal(name="Gear", start_bit=32, length=4, value_table={0:"P", 1:"R", 2:"N", 3:"D"})
    msg1.signals = [sig1, sig2, sig3]
    msg1.attributes["GenMsgCycleTime"] = 100

    # MUX message
    msg2 = Message(message_id=0x200, name="MuxData", dlc=8, sender="TCU")
    mux_switch = Signal(name="MuxSelect", start_bit=0, length=4, multiplex_indicator="M")
    mux_s1 = Signal(name="Temp_M0", start_bit=8, length=16, multiplex_indicator="m0",
                    scale=0.1, offset=-40, unit="degC")
    mux_s2 = Signal(name="Press_M1", start_bit=8, length=16, multiplex_indicator="m1",
                    scale=0.5, offset=0, unit="bar")
    msg2.signals = [mux_switch, mux_s1, mux_s2]
    
    db.add_message(msg1)
    db.add_message(msg2)
    
    # Generate
    gen = DBCGenerator()
    dbc_text = gen.generate(db)
    
    test("DBC has VERSION", 'VERSION "2.5"' in dbc_text)
    test("DBC has NS_", "NS_ :" in dbc_text)
    test("DBC has BU_", "BU_: ECU_A TCU" in dbc_text)
    test("DBC has BO_ 256", "BO_ 256 EngineData" in dbc_text)
    test("DBC has CM_ database", 'CM_ "Full Professional Test"' in dbc_text)
    test("DBC has CM_ signal", 'CM_ SG_ 256 Speed "Vehicle speed"' in dbc_text)
    test("DBC has BA_DEF_", 'BA_DEF_ "BusType" STRING' in dbc_text)
    test("DBC has BA_DEF_DEF_", 'BA_DEF_DEF_ "BusType" "CAN"' in dbc_text)
    test("DBC has BA_ network", 'BA_ "BusType" "CAN FD"' in dbc_text)
    test("DBC has BA_ msg", 'BA_ "GenMsgCycleTime" BO_ 256 100' in dbc_text)
    test("DBC has VAL_TABLE_", "VAL_TABLE_ GearVT" in dbc_text)
    test("DBC has VAL_", "VAL_ 256 Gear" in dbc_text)
    test("DBC has MUX M indicator", "SG_ MuxSelect M" in dbc_text)
    test("DBC has MUX m0", "SG_ Temp_M0 m0" in dbc_text)
    test("DBC has SG_MUL_VAL_", "SG_MUL_VAL_" in dbc_text)
    
    # Parse back
    parser = DBCParser()
    db2 = parser.parse_string(dbc_text)
    
    test("Roundtrip: version", db2.version == "2.5")
    test("Roundtrip: 2 nodes", len(db2.nodes) == 2)
    test("Roundtrip: 2 messages", len(db2.messages) == 2)
    test("Roundtrip: description", "Full Professional Test" in db2.description)
    
    # Check signals
    eng = db2.get_message(0x100)
    test("Roundtrip: EngineData exists", eng is not None)
    if eng:
        spd = eng.get_signal("Speed")
        test("Roundtrip: Speed exists", spd is not None)
        if spd:
            test("Roundtrip: Speed scale", spd.scale == 0.01)
            test("Roundtrip: Speed unit", spd.unit == "km/h")
            test("Roundtrip: Speed comment", spd.comment == "Vehicle speed")
        
        gear = eng.get_signal("Gear")
        test("Roundtrip: Gear value_table", gear is not None and len(gear.value_table) == 4)
    
    mux = db2.get_message(0x200)
    test("Roundtrip: MuxData exists", mux is not None)
    if mux:
        test("Roundtrip: MUX signal count", len(mux.signals) == 3)
        ms = mux.get_signal("MuxSelect")
        test("Roundtrip: MuxSelect is_multiplexer", ms is not None and ms.is_multiplexer)
        t0 = mux.get_signal("Temp_M0")
        test("Roundtrip: Temp_M0 is_multiplexed", t0 is not None and t0.is_multiplexed)
    
    # Roundtrip: network attributes
    test("Roundtrip: network attr BusType", db2.network_attributes.get("BusType") == "CAN FD")
    test("Roundtrip: attr default BusType", db2.attribute_defaults.get("BusType") == "CAN")

    # Roundtrip: node comments
    ecu_a = db2.get_node("ECU_A")
    test("Roundtrip: ECU_A comment", ecu_a is not None and ecu_a.comment == "Engine Control")

    # ═══════════════════════════════════════
    # 6. Generator format_number edge cases
    # ═══════════════════════════════════════
    print("\n═══ 6. Generator: _format_number ═══")
    test("format_number(-0.0)", gen._format_number(-0.0) == "0")
    test("format_number(0.0)", gen._format_number(0.0) == "0")
    test("format_number(1.5)", gen._format_number(1.5) == "1.5")
    test("format_number(10.0)", gen._format_number(10.0) == "10")
    test("format_number(42)", gen._format_number(42) == "42")
    test("format_number(-3.14)", gen._format_number(-3.14) == "-3.14")

    # ═══════════════════════════════════════
    # 7. Analyzer — CSV parse safety
    # ═══════════════════════════════════════
    print("\n═══ 7. Analyzer: CSV Parse Safety ═══")
    from logic.analyzer import CANDumpParser, CANFrame
    dump = CANDumpParser()
    
    test("Empty row returns None", dump._parse_csv_row_auto([]) is None)
    test("Short row returns None", dump._parse_csv_row_auto(["a"]) is None)
    test("Bad ID row returns None", dump._parse_csv_row_auto(["0.0", "xyz", "8"]) is None)
    test("Bad timestamp returns None", dump._parse_csv_row_auto(["abc", "123", "8"]) is None)

    # Valid candump line
    frame = dump._parse_line("(1620000000.000000) can0 123#DEADBEEF01020304")
    test("candump parse", frame is not None and frame.can_id == 0x123)
    if frame:
        test("candump data length", len(frame.data) == 8)
        test("candump timestamp", frame.timestamp == 1620000000.0)

    # Simple format
    frame2 = dump._parse_line("123  [8]  DE AD BE EF 01 02 03 04")
    test("simple format parse", frame2 is not None and frame2.can_id == 0x123)

    # Comment/empty lines
    test("Comment line", dump._parse_line("# comment") is None)
    test("Empty line", dump._parse_line("") is None)

    # CANFrame methods
    frame3 = CANFrame(0.0, 0x456, bytes([0xAA, 0xBB]))
    test("CANFrame.get_hex()", frame3.get_hex() == "AA BB")
    test("CANFrame.get_bits()", frame3.get_bits() == "1010101010111011")
    test("CANFrame.dlc", frame3.dlc == 2)

    # ═══════════════════════════════════════
    # 8. AI Module — DifferentialAnalyzer
    # ═══════════════════════════════════════
    print("\n═══ 8. AI Module: DifferentialAnalyzer ═══")
    from logic.ai_module import DifferentialAnalyzer
    
    analyzer = DifferentialAnalyzer()
    baseline = {0x100: [b'\x00\x00'] * 10}
    action = {0x100: [b'\x00\x00', b'\x01\x00', b'\x00\x00', b'\x01\x00'] * 5}
    
    results = analyzer.analyze(baseline, action)
    test("DA found 0x100", 0x100 in results)
    if 0x100 in results:
        cands = results[0x100]["candidates"]
        test("DA found candidates", len(cands) > 0)
        found_bit0 = any(c["start_bit"] == 0 and c["type"] == "pure" for c in cands)
        test("DA bit 0 pure discovery", found_bit0)
    
    # Empty baseline with significant flipping (needs >5 flips to detect)
    flipping_data = [b'\x00\x00', b'\xFF\xFF'] * 10  # 20 frames, 9+ flips per bit
    results2 = analyzer.analyze({}, {0x100: flipping_data})
    test("DA empty baseline with flipping", 0x100 in results2)

    # ═══════════════════════════════════════
    # 9. JSON Roundtrip — Full
    # ═══════════════════════════════════════
    print("\n═══ 9. JSON Full Roundtrip ═══")
    import tempfile, os
    tmpfile = os.path.join(tempfile.gettempdir(), "test_full.json")
    db.export_json(tmpfile, verbose=False)
    db_from_json = DBCDatabase.import_json(tmpfile)
    
    test("JSON RT: version", db_from_json.version == "2.5")
    test("JSON RT: messages", len(db_from_json.messages) == 2)
    test("JSON RT: nodes", len(db_from_json.nodes) == 2)
    test("JSON RT: description", db_from_json.description == "Full Professional Test")
    test("JSON RT: value_tables", "GearVT" in db_from_json.value_tables)
    test("JSON RT: attr_defs", len(db_from_json.attribute_definitions) == 1)
    test("JSON RT: attr_defaults", db_from_json.attribute_defaults.get("BusType") == "CAN")
    test("JSON RT: network_attrs", db_from_json.network_attributes.get("BusType") == "CAN FD")
    
    os.remove(tmpfile)

    # ═══════════════════════════════════════
    # 10. I18N — Basic validation
    # ═══════════════════════════════════════
    print("\n═══ 10. I18N: Translation System ═══")
    from core.i18n import I18N
    
    for lang in ["TKM", "ENG", "RUS"]:
        I18N.set_language(lang)
        val = I18N.t("app_name")
        test(f"I18N '{lang}' app_name", val != "app_name", f"got '{val}'")
    
    # Fallback for missing key
    val = I18N.t("nonexistent_key_12345")
    test("I18N missing key fallback", val == "nonexistent_key_12345")

    # ═══════════════════════════════════════
    # Summary
    # ═══════════════════════════════════════
    print(f"\n{'='*60}")
    total = PASS_COUNT + FAIL_COUNT
    print(f"AUDIT RESULTS: {PASS_COUNT}/{total} passed, {FAIL_COUNT} failed")
    if FAIL_COUNT == 0:
        print("✅ ALL TESTS PASSED — PRODUCTION READY")
    else:
        print("❌ SOME TESTS FAILED — FIX REQUIRED")
    print(f"{'='*60}")
    
    return FAIL_COUNT == 0

if __name__ == "__main__":
    try:
        success = run_all()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL] Unhandled exception: {e}")
        traceback.print_exc()
        sys.exit(2)
