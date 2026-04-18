"""
hardware/loggers.py - Dual Format CAN Logger
Maglumatlary birwagtda .txt (candump) we .csv formatlara ýazýar.
"""

import csv
import time
import os
from datetime import datetime
from analyzer import CANFrame

class DualLogger:
    """
    CAN maglumatlaryny iki faýla ýazýan klas.
    Zero-lag üçin buffering (setirleýin) ulanýar.
    """

    def __init__(self, base_filename: str):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.txt_path = f"{base_filename}_{timestamp}.txt"
        self.csv_path = f"{base_filename}_{timestamp}.csv"
        
        self.txt_file = open(self.txt_path, "w", encoding="utf-8")
        self.csv_file = open(self.csv_path, "w", newline="", encoding="utf-8")
        
        self.csv_writer = csv.writer(self.csv_file)
        # CSV Header
        self.csv_writer.writerow(["Timestamp", "ID", "DLC", "Data_Hex"])
        
        # Write first metadata to txt
        self.txt_file.write(f"# CAN Log started at {datetime.now()}\n")
        self.txt_file.write(f"# Format: (timestamp) interface id#data\n")
        self.txt_file.flush()

    def log_frame(self, frame: CANFrame):
        """Frame-i iki faýla hem ýazýar."""
        if not frame:
            return

        ts = f"{frame.timestamp:.6f}"
        can_id = f"{frame.can_id:03X}"
        data_hex = frame.get_hex().replace(" ", "")

        # 1. TXT Format (Candump style)
        # (1620000000.000000) can0 123#DEADBEEF
        self.txt_file.write(f"({ts}) can0 {can_id}#{data_hex}\n")

        # 2. CSV Format
        self.csv_writer.writerow([ts, f"0x{can_id}", frame.dlc, data_hex])

    def flush(self):
        """Maglumatlary diske ýazýar (buffer-y boşadýar)."""
        self.txt_file.flush()
        self.csv_file.flush()

    def close(self):
        """Faýllary ýapýar."""
        self.txt_file.close()
        self.csv_file.close()
        print(f"[+] Logs saved: {self.txt_path}, {self.csv_path}")
