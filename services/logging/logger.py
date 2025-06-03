"""
Logging Service for Oprina

This module provides a centralized logging service for the Oprina voice assistant.
It configures logging with proper formatting and handlers.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Do NOT import settings at the top level to avoid circular import
# from config.settings import settings

# Custom StreamHandler to force UTF-8 encoding if possible
class Utf8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        super().__init__(stream)
        # Try to set encoding to UTF-8
        if hasattr(self.stream, 'reconfigure'):
            try:
                self.stream.reconfigure(encoding='utf-8')
            except Exception:
                pass
        elif hasattr(self.stream, 'encoding'):
            try:
                self.stream.encoding = 'utf-8'
            except Exception:
                pass

    def emit(self, record):
        try:
            super().emit(record)
        except UnicodeEncodeError:
            # Fallback: remove non-ASCII characters and try again
            record.msg = str(record.msg).encode('ascii', errors='replace').decode('ascii')
            super().emit(record)

def setup_logger(name, console_output=True, log_level=None):
    """
    Set up a logger with proper formatting and handlers.
    
    Args:
        name: Logger name
        console_output: Whether to output to console
        log_level: Logging level (defaults to settings.LOG_LEVEL)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Get log level from settings if not specified
    if log_level is None:
        try:
            from config.settings import settings
            log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        except Exception:
            log_level = logging.INFO
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler if requested
    if console_output:
        # Use custom UTF-8 handler
        console_handler = Utf8StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        # Warn if encoding is not UTF-8
        encoding = getattr(sys.stdout, 'encoding', None)
        if encoding and encoding.lower() != 'utf-8':
            logger.warning(f"Console encoding is {encoding}. Unicode/emoji may not display correctly. Run 'chcp 65001' in your terminal for UTF-8 support.")
    
    # Create file handler
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Fix for Windows encoding issues with emoji
    if sys.platform == 'win32':
        # Set console encoding to UTF-8 if possible
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8')
            except Exception:
                pass
        if hasattr(sys.stderr, 'reconfigure'):
            try:
                sys.stderr.reconfigure(encoding='utf-8')
            except Exception:
                pass
    
    return logger

# Remove the default logger creation at the module level to avoid circular import
# app_logger = setup_logger("multi_agent_system")