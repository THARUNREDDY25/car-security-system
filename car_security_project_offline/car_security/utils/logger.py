"""
utils/logger.py — Centralized logging setup
Logs to both console and rotating file in logs/system.log
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    if log_file is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        log_file = os.path.join(base, "logs", "system.log")

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    logger    = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fmt       = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler (max 5MB × 3 backups)
    fh = RotatingFileHandler(log_file, maxBytes=5*1024*1024, backupCount=3)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    return logger
