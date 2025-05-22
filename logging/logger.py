import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

class CustomFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt: str):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(
    name: str,
    level: int = logging.DEBUG,
    log_file: bool = True,
    console_output: bool = True
) -> logging.Logger:
    """
    Set up logger with socket handler and optionally file and console handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Whether to write to log file
        console_output: Whether to output to console
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers = []

    # Socket handler for remote logging
    socket_handler = logging.handlers.SocketHandler('localhost', 9020)
    logger.addHandler(socket_handler)

    # File handler
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"{name.replace('.', '_')}.log"
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(file_handler)

    # Console handler
    # if console_output:
    #     console_handler = logging.StreamHandler(sys.stdout)
    #     console_handler.setFormatter(
    #         CustomFormatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #     )
    #     logger.addHandler(console_handler)

    return logger

# Create a default logger for the application
app_logger = setup_logger("multi_agent_system")