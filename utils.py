import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
from dotenv import load_dotenv

def load_config(config_path: Path = Path(".env")) -> dict:
    """
    Loads configuration from a .env file.
    """
    load_dotenv(config_path)

    log_folder = os.getenv("LOG_FOLDER")
    if log_folder is not None:
        log_folder = Path(log_folder)

    config = {
        "serial_port": os.getenv("SERIAL_PORT"),
        "baud_rate": int(os.getenv("BAUD_RATE", 57600)),
        "log_folder": log_folder,
        "blink_spike_threshold": int(os.getenv("BLINK_SPIKE_THRESHOLD", 500)),
        "blink_dip_threshold": int(os.getenv("BLINK_DIP_THRESHOLD", -400)),
        "blink_baseline_threshold": int(os.getenv("BLINK_BASELINE_THRESHOLD", 150)),
        "blink_max_dip_delay": int(os.getenv("BLINK_MAX_DIP_DELAY", 500)),
        "blink_max_baseline_delay": int(os.getenv("BLINK_MAX_BASELINE_DELAY", 200)),
    }

    return config


def setup_logger(log_filename: Path | None = None) -> logging.Logger:
    """
    Sets up a logger that writes to both stdout and a log file.
    """
    logger = logging.getLogger("EEGAssistiveComm")
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    if log_filename is not None:
        # TODO: backup count not working as expected, need to investigate
        # File handler with rotation (1 MB per file, keep 3 backups)
        file_handler = RotatingFileHandler(log_filename, maxBytes=1_000_000, backupCount=10)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger