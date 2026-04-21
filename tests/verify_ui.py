"""
Verification script for Database Explorer & UI Enhancements
"""
from PyQt5.QtWidgets import QApplication
import sys

# Create app to test PyQt widgets
app = QApplication(sys.argv)

try:
    from ui.data_table import DatabaseExplorerPanel, CANDataTable
    from core.models import DBCDatabase, Node, Message, Signal
    from ui.main_window import MainWindow

    # 1. Test Explorer Populate
    db = DBCDatabase(version="1.0")
    node = Node(name="ECU_TEST", comment="Test Node")
    db.nodes.append(node)
    
    msg = Message(message_id=0x123, name="Msg_Test", dlc=8)
    sig = Signal(name="Sig_Test", start_bit=0, length=8)
    msg.add_signal(sig)
    db.add_message(msg)
    
    explorer = DatabaseExplorerPanel()
    explorer.populate(db)
    print("OK: DatabaseExplorerPanel populate")

    # 2. Test CANDataTable update_from_database
    table = CANDataTable()
    table.update_from_database(db)
    # Check if 0x123 is in id_filter (we can't easily check internals without running events, but let's check item count)
    # 1 "All IDs" + 1 "0x123"
    assert table.id_filter.count() == 2
    assert "0x123" in table.id_filter.itemText(1)
    print("OK: CANDataTable update_from_database")

    # 3. Test MainWindow creation
    win = MainWindow()
    assert hasattr(win, 'db_explorer')
    assert win.workspace_stack.count() >= 4
    print("OK: MainWindow workspace stack")

    print("\n[+] UI ENHANCEMENTS VERIFIED!")

except Exception as e:
    print(f"FAILED: Verification failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

sys.exit(0)
