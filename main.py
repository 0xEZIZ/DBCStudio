"""
main.py - CAN DBC Parser & Generator Tool
GUI we CLI entry point.

Ulanylyşy:
    python main.py                          -> GUI açýar
    python main.py gui [--dark] [FILE]      -> GUI açýar (opsiýa: dark mode, faýl)
    python main.py parse <file.dbc> [--json output.json]
    python main.py generate <input.json> [--output output.dbc]
    python main.py analyze <dump.txt> [--output output.dbc]
    python main.py info <file.dbc>
    python main.py convert <file.dbc> --json output.json
    python main.py convert <input.json> --dbc output.dbc
"""

import argparse
import sys
import json
import os
import logging
from core.logger_config import setup_logging, get_logger

# Windows konsol encoding düzediş
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from ui.video_panel import VideoPlaybackPanel
from ui.log_console import LogConsole
from ui.hardware_dialog import HardwareSetupDialog
from core.models import DBCDatabase
from logic.parser import DBCParser, parse_dbc, print_database_summary
from logic.generator import DBCGenerator, generate_dbc, generate_dbc_from_json
from logic.analyzer import CANAnalyzer, analyze_dump


def cmd_parse(args):
    """DBC faýly parse edýär we maglumatlary görkezýär."""
    print(f"[*] DBC faýl parse edilýär: {args.file}")

    db = parse_dbc(args.file)
    print_database_summary(db)

    # JSON çykyş
    if args.json:
        db.export_json(args.json)
        print(f"[+] JSON faýla eksport edildi: {args.json}")


def cmd_generate(args):
    """JSON faýldan DBC faýl döredýär."""
    output = args.output or "output.dbc"
    print(f"[*] JSON-dan DBC döredilýär: {args.file} -> {output}")

    generate_dbc_from_json(args.file, output)


def cmd_analyze(args):
    """CAN dump faýly analiz edýär."""
    output = args.output or "analyzed_output.dbc"
    print(f"[*] CAN dump analiz edilýär: {args.file}")

    analyzer = CANAnalyzer()
    count = analyzer.load_dump(args.file)

    if count == 0:
        print("[!] Hiç bir CAN frame tapylmady. Faýl formatyny barlaň.")
        sys.exit(1)

    print(f"[+] {count} CAN frame ýüklendi.")

    if args.summary:
        # Diňe summary görkez
        analyzer.show_summary()
        return

    if args.id:
        # Belli bir ID üçin maglumat görkez
        can_id = int(args.id, 16)
        analyzer.show_id_data(can_id, max_rows=args.rows or 20)
        analyzer.show_changing_analysis(can_id)
        return

    # Interaktiw sessiýa
    analyzer.run_interactive_session(output)


def cmd_info(args):
    """DBC faýlynyň gysgaça maglumatlaryny görkezýär."""
    print(f"[*] DBC faýl maglumaty: {args.file}")

    db = parse_dbc(args.file)
    total_signals = sum(len(m.signals) for m in db.messages)

    print(f"\n  Version:    {db.version or '(not set)'}")
    print(f"  Messages:   {len(db.messages)}")
    print(f"  Signals:    {total_signals}")
    print(f"\n  Message list:")

    for msg in db.messages:
        print(f"    0x{msg.message_id:03X} {msg.name} "
              f"(DLC={msg.dlc}, signals={len(msg.signals)})")


def cmd_convert(args):
    """DBC <-> JSON arasyndaky konwersiýa."""
    if args.file.lower().endswith(".dbc") and args.json:
        # DBC -> JSON
        print(f"[*] DBC -> JSON: {args.file} -> {args.json}")
        db = parse_dbc(args.file)
        db.export_json(args.json)

    elif args.file.lower().endswith(".json") and args.dbc:
        # JSON -> DBC
        print(f"[*] JSON -> DBC: {args.file} -> {args.dbc}")
        generate_dbc_from_json(args.file, args.dbc)

    else:
        print("[!] Konwersiýa ugry kesgitlenip bilinmedi.")
        print("    DBC -> JSON: python main.py convert file.dbc --json out.json")
        print("    JSON -> DBC: python main.py convert file.json --dbc out.dbc")
        sys.exit(1)


def cmd_gui(args):
    """GUI interfeýsi açýar."""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtGui import QIcon
        from PyQt5.QtCore import Qt
        from ui.main_window import MainWindow
    except ImportError as e:
        import traceback
        traceback.print_exc()
        print(f"\n[!] Import ýalňyşlygy: {e}")
        print("    Eger PyQt5 ýok bolsa: pip install PyQt5")
        sys.exit(1)

    # Setup Logging
    setup_logging()
    logging.info("Application starting...")

    # High DPI goldawy
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("CAN Bus Analyzer & DBC Generator")
    app.setApplicationVersion("2.0")
    
    # Set global icon
    if os.path.exists("logo.png"):
        app.setWindowIcon(QIcon("logo.png"))

    dark_mode = getattr(args, "dark", False)
    window = MainWindow(dark_mode=dark_mode)

    # Eger faýl berlen bolsa, açylanda ýükle
    filepath = getattr(args, "file", None)
    if filepath and os.path.isfile(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".dbc":
            window._open_dbc_file(filepath)
        elif ext in (".txt", ".csv", ".log", ".asc"):
            window._load_can_log_file(filepath)
        elif ext in (".canproj", ".json"):
            window._load_project_file(filepath)

    window.show()
    sys.exit(app.exec_())


def main():
    """CLI we GUI esasy funksiýasy."""
    parser = argparse.ArgumentParser(
        prog="CAN DBC Tool",
        description="CAN DBC Parser & Generator Tool - "
                    "DBC faýllaryny parse etmek, döretmek, CAN dump analiz etmek we GUI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Mysallar:
  python main.py                              (GUI açýar)
  python main.py gui                          (GUI açýar)
  python main.py gui --dark                   (GUI dark mode bilen)
  python main.py gui example.dbc              (GUI + faýl açýar)
  python main.py parse example.dbc
  python main.py parse example.dbc --json output.json
  python main.py generate input.json --output output.dbc
  python main.py analyze candump.txt
  python main.py analyze candump.txt --summary
  python main.py analyze candump.txt --id 123
  python main.py info example.dbc
  python main.py convert example.dbc --json output.json
  python main.py convert input.json --dbc output.dbc
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Komanda")

    # gui koманdasы
    gui_parser = subparsers.add_parser(
        "gui", help="GUI interfeýsi açýar (esasy režim)"
    )
    gui_parser.add_argument(
        "file", nargs="?", default=None,
        help="Açylanda ýüklenýän faýl (DBC, CAN log, ýa-da project)"
    )
    gui_parser.add_argument(
        "--dark", "-d", action="store_true",
        help="Dark mode bilen başla"
    )

    # parse koманdasы
    parse_parser = subparsers.add_parser(
        "parse", help="DBC faýly parse edýär we mazmunyny görkezýär"
    )
    parse_parser.add_argument("file", help="DBC faýlynyň ýoly")
    parse_parser.add_argument(
        "--json", "-j", help="JSON faýla eksport (filepath)"
    )

    # generate koманdasы
    gen_parser = subparsers.add_parser(
        "generate", help="JSON faýldan DBC faýl döredýär"
    )
    gen_parser.add_argument("file", help="JSON giriş faýlynyň ýoly")
    gen_parser.add_argument(
        "--output", "-o", help="Çykyş DBC faýlynyň ýoly", default="output.dbc"
    )

    # analyze koманdasы
    analyze_parser = subparsers.add_parser(
        "analyze", help="CAN dump faýly analiz edýär (reverse engineering)"
    )
    analyze_parser.add_argument("file", help="CAN dump faýlynyň ýoly (txt/csv)")
    analyze_parser.add_argument(
        "--output", "-o", help="Çykyş DBC faýlynyň ýoly",
        default="analyzed_output.dbc"
    )
    analyze_parser.add_argument(
        "--summary", "-s", action="store_true",
        help="Diňe gysgaça mazmuny görkez"
    )
    analyze_parser.add_argument(
        "--id", help="Belli bir CAN ID üçin maglumat (hex)"
    )
    analyze_parser.add_argument(
        "--rows", "-r", type=int, default=20,
        help="Görkezilýän frame sany"
    )

    # info koманdasы
    info_parser = subparsers.add_parser(
        "info", help="DBC faýlynyň gysgaça maglumatlaryny görkezýär"
    )
    info_parser.add_argument("file", help="DBC faýlynyň ýoly")

    # convert koманdasы
    convert_parser = subparsers.add_parser(
        "convert", help="DBC <-> JSON konwersiýa"
    )
    convert_parser.add_argument("file", help="Giriş faýly (DBC ýa-da JSON)")
    convert_parser.add_argument("--json", help="JSON çykyş faýly")
    convert_parser.add_argument("--dbc", help="DBC çykyş faýly")

    # Argument-lary parse et
    args = parser.parse_args()

    # Hiç bir komanda berilmese -> GUI açýar
    if not args.command:
        cmd_gui(argparse.Namespace(dark=False, file=None))
        return

    # Koмандany ýerine ýetir
    commands = {
        "gui": cmd_gui,
        "parse": cmd_parse,
        "generate": cmd_generate,
        "analyze": cmd_analyze,
        "info": cmd_info,
        "convert": cmd_convert,
    }

    try:
        commands[args.command](args)
    except FileNotFoundError as e:
        print(f"[!] Faýl tapylmady: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"[!] JSON parse hatasy: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[*] Programma togtadyldy.")
        sys.exit(0)


if __name__ == "__main__":
    main()
