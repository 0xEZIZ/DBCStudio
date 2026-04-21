"""Roundtrip verification test for all fixes."""
from core.models import Signal, Message, DBCDatabase, Node
from logic.parser import DBCParser
from logic.generator import DBCGenerator

# 1. Build a test database with edge cases
db = DBCDatabase(version='1.0', description='Test DB')
db.nodes = [Node(name='ECU1'), Node(name='ECU2')]

sig1 = Signal(name='Speed', start_bit=0, length=16, byte_order='little_endian',
              value_type='unsigned', scale=0.01, offset=-40.0, minimum=-40, maximum=215.35, unit='km/h')
sig2 = Signal(name='RPM', start_bit=16, length=12, byte_order='big_endian',
              value_type='unsigned', scale=1.0, offset=0.0, minimum=0, maximum=4095, unit='rpm')
msg1 = Message(message_id=0x100, name='EngineData', dlc=8, sender='ECU1', signals=[sig1, sig2])
db.add_message(msg1)

# 2. Generate DBC text
gen = DBCGenerator()
dbc_text = gen.generate(db)
print('=== Generated DBC ===')
print(dbc_text[:600])
print('...')

# 3. Parse it back
parser = DBCParser()
db2 = parser.parse_string(dbc_text)
print(f'\nParsed back: {len(db2.messages)} messages, {len(db2.nodes)} nodes')
for m in db2.messages:
    print(f'  MSG 0x{m.message_id:03X} {m.name}: {len(m.signals)} signals')
    for s in m.signals:
        print(f'    SG_ {s.name} [{s.start_bit}|{s.length}] '
              f'scale={s.scale} offset={s.offset} '
              f'min={s.minimum} max={s.maximum} unit={s.unit}')

# 4. Verify roundtrip
assert len(db2.messages) == 1, f'Expected 1 message, got {len(db2.messages)}'
assert db2.messages[0].signals[0].name == 'Speed'
assert db2.messages[0].signals[0].offset == -40.0, f'Offset was {db2.messages[0].signals[0].offset}'
assert db2.messages[0].signals[1].name == 'RPM'
assert db2.messages[0].signals[1].byte_order == 'big_endian'
print('\n[PASS] Roundtrip parse/generate')

# 5. Test encoder roundtrip
from logic.encoder import CANEncoder
enc = CANEncoder()
encoded = enc.encode_message(msg1, {'Speed': 100.0, 'RPM': 3000})
decoded = enc.decode_message(msg1, encoded)
speed_val = decoded['Speed']
rpm_val = decoded['RPM']
print(f'\nEncoder test: Speed={speed_val:.2f}, RPM={rpm_val:.2f}')
assert abs(speed_val - 100.0) < 0.02, f'Speed mismatch: {speed_val}'
assert abs(rpm_val - 3000.0) < 1.0, f'RPM mismatch: {rpm_val}'
print('[PASS] Encoder roundtrip')

# 6. Test _format_number edge cases
print(f'\nformat_number(-0.0) = {gen._format_number(-0.0)}')
print(f'format_number(1.5) = {gen._format_number(1.5)}')
print(f'format_number(10.0) = {gen._format_number(10.0)}')
print(f'format_number(0) = {gen._format_number(0)}')
assert gen._format_number(-0.0) == '0', f'Expected "0", got "{gen._format_number(-0.0)}"'
assert gen._format_number(10.0) == '10', f'Expected "10", got "{gen._format_number(10.0)}"'
assert gen._format_number(1.5) == '1.5'
print('[PASS] format_number')

# 7. Test CSV parser safety
from logic.analyzer import CANDumpParser
dump = CANDumpParser()
# Should not crash on bad CSV rows
frame = dump._parse_csv_row_auto(['', '', ''])
assert frame is None
frame = dump._parse_csv_row_auto(['abc', 'xyz', '8'])
assert frame is None
print('[PASS] CSV parser safety')

# 8. Test JSON roundtrip (with verbose=False)
import tempfile, os
tmpfile = os.path.join(tempfile.gettempdir(), 'test_dbc.json')
db.export_json(tmpfile, verbose=False)
db3 = DBCDatabase.import_json(tmpfile)
assert len(db3.messages) == 1
assert db3.messages[0].signals[0].name == 'Speed'
os.remove(tmpfile)
print('[PASS] JSON roundtrip (verbose=False)')

# 9. Test multiline comment parsing
multiline_dbc = '''
VERSION ""
NS_ :
BS_:
BU_:

CM_ "This is a
multiline comment
for the database";

BO_ 512 TestMsg: 8 Vector__XXX
 SG_ TestSig : 0|8@1+ (1,0) [0|255] "" Vector__XXX

'''
parser2 = DBCParser()
db4 = parser2.parse_string(multiline_dbc)
assert 'multiline comment' in db4.description, f'Failed: description was "{db4.description}"'
print('[PASS] Multiline comment parsing')

# 10. Test negative lookahead on BA_ (network vs node)
attr_test = '''
VERSION ""
NS_ :
BS_:
BU_: ECU1

BA_DEF_ "NetworkAttr" INT 0 100;
BA_ "NetworkAttr" 42;
BA_ "NetworkAttr" BU_ ECU1 99;

BO_ 256 TestMsg: 8 ECU1
 SG_ TestSig : 0|8@1+ (1,0) [0|255] "" Vector__XXX
'''
parser3 = DBCParser()
db5 = parser3.parse_string(attr_test)
net_val = db5.network_attributes.get('NetworkAttr')
assert net_val == 42, f'Network attr should be 42, got {net_val}'
print('[PASS] Network attribute lookahead')

print('\n=== ALL TESTS PASSED ===')
