"""
logger_config.py - Professional Logging System
Programmanyň ähli logs-laryny bir ýere jemleýär.
"""

import logging
import sys
import os

def setup_logging():
    """Logging ulgamyny sazlaýar."""
    
    # Create logs directory
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "app.log")

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 1. File Handler (Ähli jikme-jiklikler)
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # 2. Console Handler (Diňe möhüm zatlar)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging system initialized.")

def get_logger(name):
    """Belli bir modul üçin logger gaýtarýar."""
    return logging.getLogger(name)
